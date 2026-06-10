# Agent Build Plan v1 - Portfolio Analyst Agent V2

**Date:** 2026-05-29
**Status:** Design/plan only. No code written. This is the implementation plan for the LLM reasoning loop specified in `AGENT_REASONING_LOOP_AND_MEMORY_V1.md`.

## Decisions locked for this plan
- **Provider:** Claude / Anthropic Messages API tool-use loop. Needs `ANTHROPIC_API_KEY`.
- **Memory writes:** **proposed-only.** Every memory op persists with `review_state = "proposed"`. The lifecycle (`approved/applied/rejected`) is built but no op auto-applies in v1. `auto_apply_memory_ops = false` in governance.
- **Harness owns the loop**, the LLM owns judgment. Validation is deterministic Python at the tool boundary, never prompt-enforced.
- **Prerequisite:** the Tier-0 correctness fixes (C2, C3, H1 from `CODEBASE_AUDIT_2026-05-29.md`) land *before or with* the agent, because `get_fund_snapshot` / `evaluate_challenge_triggers` feed the LLM those numbers.

---

## 1. The one real dependency decision

The codebase is currently **stdlib-only**, which is a genuine virtue. Building the agent introduces dependencies. Recommendation — add exactly two runtime deps and isolate them:

| Dep | Why | Scope of blast radius |
|---|---|---|
| `anthropic` | The LLM client. Unavoidable for a Claude loop. | Only `agent_runtime/` imports it. The parsers/tools stay clean. |
| `pydantic` (v2) | Payload + memory-op schema validation **and** auto-generates the JSON `input_schema` for each Anthropic tool. Doing this by hand in stdlib is error-prone and is exactly the validation the spec demands at the write boundary. | Only `schemas.py`, `write_tools.py`, `tool_registry.py`. |

**Governance config:** the spec says "a file *such as* `config/agent_governance.yaml`." To preserve zero-dependency in the core, use **`config/agent_governance.json`** (stdlib `json`) rather than YAML — same versioned/`effective_from` semantics, no PyYAML. Flagged as a deliberate substitution.

The existing parser/tool layer keeps importing nothing new. Only the new `agent_runtime/` package and the write/validation layer take on `anthropic`+`pydantic`. If you ever want provider-agnostic later, the `llm_client.py` seam is where it goes.

---

## 2. File-by-file plan

Grouped by build phase. **[NEW]** = create, **[MOD]** = modify existing.

### Phase 0 — Unblock: fix the numbers + packaging
*Small, must precede a trustworthy agent.*

- **[MOD] `src/portfolio_analyst_agent/rolled_exposures.py`**
  - C3: replace `range(5, 83)` (`:409`) with dynamic account-block detection (read until first blank `secid`); assert observed last row ≥ expected.
  - C2: when benchmark coverage ≈ 0 but target is populated, set `active_rolled_exposure = None` (not `target − 0`) and emit a `benchmark_coverage_ok` flag.
  - H1: count + log dropped `portcode`s at the join (`:92-94`); warn if dropped fraction exceeds a threshold.
- **[MOD] `src/portfolio_analyst_agent/challenge_triggers.py`** — honor `benchmark_coverage_ok`; do not fire sign-disagreement on coverage-empty rows.
- **[MOD] `pyproject.toml`** — add `[build-system]` (hatchling/setuptools), `dependencies = ["anthropic", "pydantic>=2"]`, `[project.optional-dependencies] dev = ["pytest"]`, and `[project.scripts]` entry points. Makes `pip install -e .` work → kills the 16× `sys.path` hack over time.

**Acceptance:** re-run the pipeline; the `fund_weights_summary` "summed exposure" is no longer ~199%, bond funds no longer show full-position active bets, dropped-account count is logged.

### Phase 1 — Finish the read tools + wire the mapping

- **[NEW] `src/portfolio_analyst_agent/acid_mapping.py`**
  - Loads `data/acid_mapping_bootstrap_v1.csv` into an indexed lookup keyed by `acid`.
  - `load_mapping(as_of_date) -> MappingIndex` with `.get(acid)` exposing `interpretation_type`, `comparison_group`, `relative_value_group`, `parent_family`, `investable_flag`, `curve_aware`, `stf_favorable_direction`.
  - This is the layer the audit found "written but never read." Wiring it here is what makes the mapping *live*.
- **[MOD] `src/portfolio_analyst_agent/agent_tools.py`** — add the three missing read tools, same replay-gated style as the existing three:
  - `get_acid_history(acid, snapshot_date, as_of_date, lookback_months=12, model_family=None)` → reads `equity_vir_history` (STF, delta STF, rank, decomposition time series; stable `row_id` per row; enforce `<= as_of_date`).
  - `get_exposure_lineage(fund, acid, snapshot_date, as_of_date)` → reads `fund_rolled_exposure_detail.csv` (account + security-level rows, `h_path`, weights, contributions; stable `row_id`).
  - `get_peer_context(acid, snapshot_date, as_of_date)` → joins `acid_mapping` + current snapshot: peer ACIDs in `comparison_group` / `relative_value_group`, parent-family signal, `stf_favorable_direction`. Powers Trigger 5.
  - Wire mapping into `get_fund_snapshot` so `acid_rows` carry mapping fields (the agent reasons with behavior, not just buckets).
- **[MOD] `src/portfolio_analyst_agent/challenge_triggers.py`** — un-defer Trigger 5 (`better_expression_available`) now that `relative_value_group`/`investable_flag` are loadable; remove from `DEFERRED_TRIGGER_TYPES`.

**Acceptance:** all 6 read tools callable, replay-gated, return `row_id`-stamped rows; `get_peer_context` returns real peers; Trigger 5 can fire on a crafted case.

### Phase 2 — Governance config + memory write path

- **[NEW] `config/agent_governance.json`** — all thresholds from the spec's Governance Parameters section (`materiality_threshold_active`, `decomposition_weakening_threshold`, `peer_advantage_threshold`, `stale_*_threshold_months`, `vir_quartile_universe`, `auto_apply_memory_ops=false`, …), each with `effective_from`. Versioned (`governance_version`).
- **[NEW] `src/portfolio_analyst_agent/governance.py`** — `load_governance(as_of_date)` returns the params valid as of the date (respects `effective_from`). Triggers + materiality read from here instead of module constants.
- **[NEW] `src/portfolio_analyst_agent/memory_ops.py`** — the write side of memory (read side stays in `memory_store.py`):
  - The 15 typed ops as pydantic models (`affirm_thesis`, `create_thesis`, `update_thesis`, `mark_thesis_weakening/contradicted`, `supersede_thesis`, `open_challenge`, `update_challenge`, `close_challenge`, `escalate_challenge_to_ic`, `dismiss_challenge`, `create_watch_item`, `close_watch_item`, `log_exception`, `expire_exception`).
  - `apply_ops(fund, ops, run_metadata) -> list[AppliedOp]` that: schema-validates each op; enforces Tier-1 invariants (one `active` thesis per `(fund,acid)`; `last_affirmed_snapshot_date` monotonic; supersede only by same `(fund,acid)`); rejects conflicting ops in one call; stamps `review_run_id/snapshot_date/as_of_date/timestamp`; sets `review_state="proposed"`; returns generated `challenge_id`s.
  - **Atomic append** to `artifacts/agent_memory/memory_records.json` (write-temp-then-rename). Records are append-only with `review_state`, so nothing is mutated in place — preserves audit + replay.
- **[MOD] `src/portfolio_analyst_agent/memory_store.py`** — ensure `recall_memory_store` filters to `review_state in {"approved","applied"}` for *prior-context* recall (proposed ops from a current run are not yet "real"), while still surfacing proposed counts where the spec asks.

**Acceptance:** unit tests prove invariants reject bad ops; ops land as `proposed`; recall still works and excludes future-dated/proposed entries per replay rules.

### Phase 3 — Citation enforcement + write tools

- **[NEW] `src/portfolio_analyst_agent/citations.py`** — the boundary enforcer:
  - Parse the three token forms: `csv:<path>#row_id=<id>`, `mem:<table>#<record_id>`, `deriv:<formula>?inputs=<refs>`.
  - `resolve(token) -> bool` checks the referenced row/record/derivation actually exists (CSV row_id present, memory record present, derivation inputs resolvable).
  - `enforce(payload)` walks every narrative field, finds claims, and rejects if any lacks a resolvable token. **This is the spec's "write tools reject uncited narrative."**
- **[NEW] `src/portfolio_analyst_agent/schemas.py`** — pydantic models for `ChangeBriefPayload`, `SizingConsiderationsPayload`, `ChallengeBriefPayload` (mirroring the Output Package schemas verbatim).
- **[NEW] `src/portfolio_analyst_agent/write_tools.py`** — the 4 write tools:
  - `write_change_brief(fund, content)` — validate schema → `citations.enforce` → persist MD+JSON under `artifacts/monthly_review/<snapshot_date>/<fund>/`.
  - `write_sizing_considerations(fund, content)` — same; non-prescriptive (reject any trade/target-weight recommendation language via a lightweight check).
  - `write_challenge_brief(fund, content)` — validate each item references a fired `trigger_candidate_id` and has a `challenge_id`; reject if every item dismissed.
  - `update_memory(fund, ops)` — delegate to `memory_ops.apply_ops`.
  - These supersede the template f-strings in `monthly_review.py` (which becomes a deterministic *fallback*, not the brief author).

**Acceptance:** a payload with a fabricated/uncited claim is rejected with a clear error; a valid payload persists MD+JSON; challenge-brief validation rejects an item with no fired trigger.

### Phase 4 — The LLM loop (the thin part)

- **[NEW] `src/portfolio_analyst_agent/agent_runtime/__init__.py`**
- **[NEW] `src/portfolio_analyst_agent/agent_runtime/tool_registry.py`** — maps each of the 10 tools → `{callable, pydantic-derived input_schema}` for the Anthropic `tools` param. Single source of truth for what the model can call.
- **[NEW] `src/portfolio_analyst_agent/agent_runtime/llm_client.py`** — wraps `anthropic.Anthropic`. Messages API, **prompt caching** on the system prompt + tool definitions (stable across funds), retries/backoff, token/latency logging. The only file that imports `anthropic`.
- **[NEW] `src/portfolio_analyst_agent/agent_runtime/prompts.py`** — system prompt encoding the playbook (Steps 1–12), the universal behavior rule, the citation contract, and the "factual, non-prescriptive" constraint. Per-fund user message seeds `fund/snapshot_date/as_of_date/run_metadata`.
- **[NEW] `src/portfolio_analyst_agent/agent_runtime/loop.py`** — `run_fund(fund, run_metadata) -> FundRunResult`:
  - Conversation loop: model emits tool_use blocks → harness dispatches via `tool_registry` → returns tool_result → repeat until the write tools have all fired (change brief always; sizing when algo coverage; challenge brief conditional; memory ops).
  - Records the **analytical trace** (ordered tool-call sequence + args + result hashes) to `artifacts/monthly_review/<snapshot_date>/<fund>/agent_trace.json`.
  - Enforces run-level validation rules (spec §Validation): reject run if a brief is emitted without a fired trigger, a citation can't resolve, the fund isn't in `DEFAULT_FUND_ORDER`, or a read tool returned future-dated data.
- **[NEW] `src/portfolio_analyst_agent/run_metadata.py`** — builds `ReviewRunMetadata` (`review_run_id`, versions, `source_file_hashes`, `run_mode`), reusing `evidence.file_sha256`.

### Phase 5 — Orchestrator + trace + docs

- **[NEW] `scripts/run_agent_review.py`** — CLI: takes `--as-of-date`, `--snapshot-date`, optional `--funds`, `--run-mode {live_monthly|historical_replay|ad_hoc}`. Builds run metadata, iterates `DEFAULT_FUND_ORDER`, calls `loop.run_fund` per fund, writes `batch_index.json`. The Python harness manages the queue; the LLM never aggregates across funds.
- **[MOD] `scripts/render_monthly_review_report.py`** — resolve citation tokens to human-readable refs (and fix the `watch_items_count` key typo while here).
- **[MOD] `README.md`** — correct the "IC prep" overclaim; document the agent entry point and the `ANTHROPIC_API_KEY` requirement.

---

## 3. How one fund flows (the loop in motion)

```
run_agent_review.py
  └─ build ReviewRunMetadata (run_id, versions, source hashes, as_of_date)
  └─ for fund in DEFAULT_FUND_ORDER:
       loop.run_fund(fund, meta):
         system prompt (playbook + citation contract)  ── cached
         tools = tool_registry (10 schemas)            ── cached
         model → recall_memory                → harness returns prior context
         model → get_fund_snapshot            → corrected exposures + mapping fields
         model → get_exposure_lineage / get_acid_history / get_peer_context (selective)
         model → evaluate_challenge_triggers  → deterministic candidates
         model → write_change_brief(content)  → schema+citation validated → persisted
         model → write_sizing_considerations  → (if algo coverage)
         model → update_memory(ops)           → proposed-only, invariants enforced
         model → write_challenge_brief        → (only if a candidate accepted)
         harness records analytical trace, closes run
```

Replay safety is already enforced in the read tools (`_enforce_as_of`); the loop just must not hand the model anything outside the tool surface.

---

## 4. Testing plan (built alongside, Phase 0 onward)

- **`tests/test_row_ids.py`** — stability of the audit backbone.
- **`tests/test_rolled_exposures.py`** — C1/C2/C3 regressions (no double-count, no phantom active, account row detected); dropped-portcode counting.
- **`tests/test_memory_ops.py`** — every Tier-1 invariant; conflicting-ops rejection; proposed-only stamping.
- **`tests/test_citations.py`** — token parse/resolve; uncited-claim rejection.
- **`tests/test_write_tools.py`** — schema rejection, challenge-brief validation, MD+JSON persistence.
- **`tests/test_challenge_triggers.py`** — Trigger 1/3/5 fired/borderline/suppressed states; coverage-empty suppression.
- **`tests/test_agent_loop.py`** — loop with a **mocked** LLM client (scripted tool_use sequence) → end-to-end without spending tokens.

---

## 5. Milestones & rough effort

| Phase | Deliverable | Relative effort |
|---|---|---|
| 0 | Numbers correct + package installable | S |
| 1 | All 6 read tools + mapping live + Trigger 5 | M |
| 2 | Governance config + memory write path | M–L |
| 3 | Citation enforcer + 4 write tools | L |
| 4 | LLM loop runs one fund end-to-end | M |
| 5 | Batch orchestrator + trace + render/docs | S–M |

The center of gravity is Phases 2–3 (deterministic validation infra), exactly per the design principle. Phase 4 (the "agent") is comparatively thin.

---

## 6. Risks & open follow-ups (from the spec, still live)
- **Threshold calibration** — governance defaults are placeholders; calibrate against shadow months before trusting fired triggers.
- **FI VIR parser still missing** — bond ACIDs stay `not_evaluable_for_vir_triggers` until it lands; the agent must degrade gracefully, not crash, on bond funds.
- **Citation "claim detection"** — deciding which fields count as "narrative claims" needs a precise rule so the enforcer isn't over/under-strict. Pin this down in Phase 3.
- **Near-miss → watch item** policy — open governance choice.
- **Memory on-disk layout** — append-only JSON for v1; DB deferred to Model 2.

---

## Bottom line
The spec is implementable largely as written. The work is mostly the deterministic write/validation/memory infrastructure (Phases 2–3) — which is the right place for the effort. The LLM loop itself is small once the tools exist. Build order: **correct the numbers → finish read tools + wire mapping → governance + memory writes → citation enforcement + write tools → the loop → orchestrator.**
