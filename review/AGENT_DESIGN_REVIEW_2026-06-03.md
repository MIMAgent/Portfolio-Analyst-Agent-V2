# Agent Design & Schema Review — Portfolio Analyst Agent

**Date:** 2026-06-03
**Scope:** `codex_bedrock_runtime_patch_v15` — the LLM agent runtime (`src/portfolio_analyst_agent/agent_runtime/`), write/validation layer (`schemas.py`, `write_tools.py`, `citations.py`), memory layer (`memory_ops.py`, `memory_store.py`), governance, and the Bedrock provider.
**Reference contract:** `docs/AGENT_REASONING_LOOP_AND_MEMORY_V1.md`
**Relationship to prior work:** This patch is the **Tier 3 "actual product"** from `docs/CODEBASE_AUDIT_2026-05-29.md` — it implements the LLM tool-use loop, the 4 write tools, the memory-mutation path, `get_market_context`, externalized governance, and a Bedrock Converse provider that the audit said did not yet exist.

---

## Executive summary

The implementation finally realizes the "LLM-led agent, not a deterministic pipeline" goal, and the foundations are strong: a clean LLM-vs-Python boundary, citation-at-the-write-boundary enforcement, a testable provider abstraction, context compaction, and versioned governance.

Three things hold it back from matching the spec's ambition:

1. **The loop terminates too early**, so a default run produces only the Change Brief — Sizing Considerations and the Challenge Brief are nearly unreachable.
2. **The schema is defined twice (and already drifts)**, key enums/cross-checks aren't enforced, and the citation contract has a real hole that lets PM-facing narrative fields go uncited.
3. **The memory loop is inert in autonomous operation** — nothing the agent writes can ever be recalled, which also disables the decomposition-rotation trigger.

None of this is architecturally broken. The fixes are surgical and high-leverage.

---

## What's genuinely strong

- **Clean LLM-vs-Python boundary.** Python owns ingestion, replay gating, stable row-IDs, atomic writes, and source-file hashing; the LLM owns judgment. This is exactly the "agent, not a pipeline" goal.
- **Citation-at-the-write-boundary** (`citations.enforce_payload_citations`) is the right enforcement point, and resolving `csv:`/`mem:`/`deriv:`/`trigger:` tokens against real rows is a strong auditability primitive.
- **Testability.** The `LLMClient` Protocol plus `ScriptedLLMClient` double makes the loop unit-testable with no network.
- **Context compaction.** `loop._llm_visible_result` keeps evidence handles while shrinking model-visible payloads — a thoughtful way to control context growth.
- **Governance** externalized with `effective_from` versioning; memory is append-only with latest-collapse and a 4-state `review_state` lifecycle.

---

## A. Agent loop (`agent_runtime/loop.py`)

### A1 — The early-break makes optional artifacts nearly unreachable *(highest impact)*
Lines 159–169 break the loop the moment `completed_writes ⊇ required_writes`. With the default `required_writes = {write_change_brief}` (`loop.py:208`), the loop closes the instant the Change Brief lands — so Sizing Considerations and the Challenge Brief can only be produced if the model emits them as **additional `tool_use` blocks in the same assistant turn** as the Change Brief. But the system prompt actively discourages that ("Write the Change Brief before any optional write tool"; "Write Sizing Considerations only after Change Brief succeeds").

**Net effect:** a default run almost always yields only the Change Brief, contradicting the spec ("Sizing… always when algo coverage is available").

**Fix:** delete the line-159 early break and let the model terminate naturally via the no-tool-use path (lines 108–112), which *already* checks required writes as a post-condition. `max_turns` remains the backstop.

### A2 — Required-writes is the wrong mechanism for *conditional* artifacts
`run_agent_review.py --include-challenge` adds `write_challenge_brief` to `required_writes`. If no trigger fires, the model cannot satisfy it (the validator rejects empty/non-fired briefs), so the loop burns all 20 turns and **fails the whole fund**. Challenge production is conditional on fired triggers by design — it should never be a hard "required write."

**Fix:** introduce an `expected_if(condition)` notion, or gate the requirement on `context.fired_trigger_ids` being non-empty.

### A3 — Model can silently review the wrong fund
Every read tool does `args.get("fund", context.fund)` (`tool_registry.py:60`, etc.), so a hallucinated `fund` arg overrides the harness-queued fund — bypassing the spec's "fund not in `DEFAULT_FUND_ORDER` → reject" rule.

**Fix:** pin `fund`/`snapshot_date`/`as_of_date` from context and ignore model overrides for these (or validate the supplied fund against the queue).

### A4 — `acid` not marked required
`get_acid_history`/`get_exposure_lineage`/`get_peer_context` use `_object_schema(..., required=())`, but the callables do `args["acid"]` → `KeyError` → caught as a tool error → wasted turn.

**Fix:** mark `acid` required in the input schema so API-level validation nudges the model.

### A5 — `stop_reason` / `max_tokens` ignored
`max_tokens=4096` is fixed (`llm_client.py:63,109`). A large Change Brief can truncate mid-JSON; the loop then runs a malformed `tool_use` block and errors.

**Fix:** detect `stop_reason == "max_tokens"` and either raise `max_tokens` for write turns or continue/repair. (Minor: `turn_count` at `loop.py:203` returns `len(trace)` — event count, not turns — which is misleading.)

---

## B. Schema & validation (`tool_registry.py` schemas, `schemas.py`, `citations.py`)

### B1 — Two hand-written schema representations that already drift
The Anthropic `input_schema` (`_change_brief_schema`) and the runtime validator (`validate_change_brief`) are independent. The input schema requires `executive_summary` + `material_movers`; the validator *additionally* requires `header`, `sizing_artifact_summary`, `memory_updates_summary`, `triggers_fired_summary`, `evidence_index` (papered over by `_prepare_change_brief_content` defaults).

**Result:** the schema shown to the model ≠ the schema enforced.

**Fix:** define each artifact contract once (a JSON Schema dict) and derive *both* the tool `input_schema` and validation from it. Adding `jsonschema` is a cheap dependency (the audit already flags that `pyproject` declares none), and it lets you enforce `maxItems`, types, and **enums** in one place.

### B2 — Enums unenforced; `trigger_type` can be mislabeled
`trigger_type` should be `enum {sign_disagreement, decomposition_rotation, better_expression_available}`, but `_hydrate_challenge_item` (`tool_registry.py:281`) **defaults a missing `trigger_type` to `"sign_disagreement"`**, and the validator only checks it's non-empty. Critically, `validate_challenge_brief` verifies `trigger_candidate_id ∈ fired_trigger_ids` but **never checks the declared `trigger_type` matches the fired candidate's actual type** — because `_record_triggers` (`tool_registry.py:204`) discards the type, keeping only IDs.

**Fix:** store `{id → type}` from the trigger evaluation and cross-check the declared type against the fired candidate.

### B3 — Citation enforcement has a real hole
`enforce_payload_citations` only inspects a fixed allowlist, `NARRATIVE_FIELD_NAMES` (`citations.py:18`). The Change Brief's own schema fields **`pm_takeaway`, `review_question`, `what_would_change_view`** — plus `headline`, `fundamental_readthrough`, `pm_question` — are *not* in that set, so they are accepted as **uncited free text**, directly contradicting "Every narrative claim must include resolvable citation tokens."

**Fix:** add these fields to the allowlist, or invert the rule (require citations on all string leaves except a known-safe metadata allowlist).

### B4 — Structured `evidence_pointers` are decorative
Enforcement only checks inline narrative tokens; `evidence_pointers: [{artifact_path, row_id}]` are never resolved. A mover can cite a real row in prose while its `evidence_pointers` point nowhere (or at a different row).

**Fix:** validate that pointers resolve, and ideally that the narrative's tokens ⊆ `evidence_pointers`.

### B5 — `reject_prescriptive_sizing_language` is a naive substring blocklist
`schemas.py:87` bans `"buy "`, `"sell "`, `"increase to"`, etc. This false-positives ("sell-side estimates", "buy-rated peers") and false-negatives ("trim", "add exposure", "a larger position is warranted"), and it is applied **only to Sizing**, though the prompt forbids prescription everywhere.

**Fix:** at minimum use word-boundary regex and apply across all three artifacts; better, treat it as a soft signal, not a guarantee.

### B6 — Dead validation rules
- `validate_challenge_brief`'s "cannot dismiss every item" check (`schemas.py:82`) counts items with a `challenge_id` as accepted, but hydration always assigns one — so it can never trip.
- `next_review_checkpoint` is "required" but always defaulted to `"Next monthly review"`.

**Fix:** make them meaningful or remove them, so the validator's guarantees are real.

### B7 — `additionalProperties: True` everywhere
Fine for read-tool inputs, but on the artifact leaves it lets the model dump hallucinated fields silently.

**Fix:** set `false` on leaf objects (e.g., `evidence_pointers` items) to catch drift.

---

## C. Memory model — the machinery is largely inert in an autonomous loop

### C1 — The recall/propose loop is broken in practice *(high impact)*
`apply_ops` always writes `review_state="proposed"` (`memory_ops.py:282`), and there is **no approval tool/CLI in this patch.** But `recall_memory_store` only returns `AUTHORITATIVE_REVIEW_STATES = {approved, applied}` (`memory_store.py:21,45`). So **nothing the agent writes is ever recallable.**

Consequences:
- The agent reviews each month "in isolation" despite the elaborate memory design.
- **`decomposition_rotation` can essentially never fire**, since it requires an existing *active thesis* that recall will never surface.

**Fix:** add an approval step (even a manual `approve_memory.py`) **or** a governance "shadow mode" that treats `proposed` as recallable. Otherwise the entire thesis/challenge tier is write-only.

### C2 — Replay as-of gate uses wall-clock `created_at`, not a business availability date
`_is_record_available` (`memory_store.py:317`) gates on `created_at` (ingestion time). The spec wants `record_available_date <= as_of_date`. For seeded/backfilled memory, `created_at` can wrongly exclude legitimately-old records that were physically written recently.

**Fix:** prefer business dates (`opened_at_snapshot_date`, `last_affirmed_snapshot_date`, etc.) for replay gating, which the selectors already apply; keep `created_at` for audit only.

### C3 — Spec invariant not enforced
"`last_affirmed_snapshot_date` may not move backward" is never checked in `affirm_thesis` (`memory_ops.py:140`). `_find_thesis` also returns the first dict-iteration match, which is non-deterministic if duplicates exist. Low severity for v1, but these are the invariants the design leans on.

---

## D. Provider robustness (`llm_client.py`, `run_agent_review.py`)

### D1 — Bedrock bearer-token path drops retries/timeout config
The boto path sets `retries={max_attempts:2}` and a configurable `read_timeout` (`llm_client.py:129`); the bearer path uses raw `urllib` with a hardcoded `timeout=120` and **no retry/backoff** (`llm_client.py:224`). Throttling (`ThrottlingException` / HTTP 429) on a multi-fund loop will hard-fail.

**Fix:** unify timeout config and add backoff to the bearer path.

### D2 — Model-id resolution is fragile
`run_agent_review.py:41` only swaps the literal default `claude-sonnet-4-5` to `anthropic.claude-sonnet-4-6`; any other Anthropic-style id is passed verbatim to Bedrock, which generally needs an `anthropic.`-prefixed id or (increasingly) a regional **inference-profile** id like `us.anthropic.claude-...`.

**Fix:** resolve `--model` per-provider with a mapping table and validation, and document the inference-profile requirement.

### D3 — Governance thresholds aren't given to the model
Materiality lives in `agent_governance.json`, but the static `SYSTEM_PROMPT` talks about "material movers" with no numbers, so the model's notion of "material" is unanchored from the deterministic triggers.

**Fix:** inject the resolved governance thresholds into the prompt so model judgment and `evaluate_challenge_triggers` agree.

---

## Prioritized sequence

| # | Item | Why first |
|---|------|-----------|
| 1 | **A1 + A2** — loop early-break + conditional-artifact handling | Without these the agent only ever writes one of three artifacts. |
| 2 | **C1** — approval path / shadow recall | Unlocks the entire memory + decomposition-rotation design. |
| 3 | **B1–B4** — single-source schema, enum/trigger-type cross-check, citation-allowlist hole, evidence-pointer resolution | These are the auditability guarantees the product sells. |
| 4 | **D1–D2** — Bedrock retry/throttling + model-id resolution | Operational reliability for monthly batch runs. |

### Quick-win cluster (small, isolated)
A3 (pin fund), A4 (`acid` required), B6 (dead rules), B7 (`additionalProperties: false` on leaves), C3 (monotonic affirm date) — each is a few lines and individually low-risk.

---

## Bottom line

The agent loop is real, the boundaries are clean, and the auditability primitives are the right ones. The gap is that **the loop stops before the full output package is produced, the schema contract is enforced in two places that disagree, and the memory tier is write-only in autonomous operation.** Fix the loop termination (A1/A2) and the memory recall path (C1) first — those unlock the design as specified — then consolidate the schema (B1–B4) so the evidence guarantees are airtight.
