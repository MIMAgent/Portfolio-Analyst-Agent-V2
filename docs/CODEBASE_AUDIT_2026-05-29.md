# Codebase Audit - Portfolio Analyst Agent V2

**Date:** 2026-05-29
**Scope:** Full repository (`src/`, `scripts/`, `docs/`, `frontend/`, `pyproject.toml`) — ~7,600 LOC Python + React/Vite prototype.
**Focus (per request, in priority order):** Architecture & scope → Data/financial correctness → Code quality & bugs.
**Method:** Three independent read-only passes; financial findings additionally executed against the real workbooks in `data/`. The three headline Critical items were re-verified by hand against source.

---

## Executive summary

The **specs and design thinking are strong, the deterministic data plumbing is competently built, but three things undercut it today:**

1. **The "agent" does not exist in code.** The whole product premise — *"LLM-led agent, not a deterministic pipeline disguised as an agent"* — is currently unmet. There is no LLM call, no reasoning loop, no tool-calling, no write/memory tools anywhere. What ships is a deterministic pipeline emitting templated JSON drafts with blank judgment fields. This is precisely the anti-pattern the project's own risk register warns against.

2. **There are real financial-correctness bugs that reach the IC-facing output.** A double-counting bug prints ~199% exposure for equity funds; bond funds show phantom 100% "active" bets because benchmark coverage is empty; and a hardcoded row range silently drops an entire account. These are numbers a human committee would act on.

3. **Zero tests** for a tool whose entire value proposition is *auditable, evidence-cited* analysis.

None of this is architecturally broken. The foundations (frozen dataclasses, deterministic row-IDs, replay-safe `as_of_date` gating, a dependency-free XLSX reader, Windows-correct CSV handling) are genuinely good mid-to-senior work. The gap is **velocity debt and an unbuilt core**, not incompetence.

---

## 1. Architecture & scope

### 1.1 Stated goal vs. reality — there is no agent
- Repo-wide search for `anthropic|openai|llm|claude|gpt|tool_call|messages.create` returns **zero hits** in source. No LLM SDK is even a declared dependency.
- The harness is explicitly deterministic by its own docstrings: `monthly_review.py:1` — *"Deterministic monthly review harness for Model 1."*
- "Agent output" is hardcoded templates/f-strings:
  - `monthly_review.py:81-95` — `memory_updates_summary` counts are literal `0`; `proposed_memory_ops: []`.
  - `monthly_review.py:347-370` — `_challenge_items` emits `challenge_id: ""`, `cleaner_expression: ""`, `falsification_framing: ""` — exactly the judgment fields the agent is supposed to produce.
- The spec defines a **10-tool surface**; only **3 read tools** exist (`get_fund_snapshot`, `recall_memory`, `evaluate_challenge_triggers` — `agent_tools.py:224`). **All 4 write tools and the remaining read tools are missing.**
- **Memory is read-only and hand-seeded.** Every record in `artifacts/agent_memory/memory_records.json` is stamped `manual_thesis_seed_*` / `manual_fund_review_*`. The 15 memory operations and the 4-state review lifecycle (`proposed/approved/applied/rejected`) are schema-only — nothing ever writes them.

> The internal docs are honest about this (`AGENT_REASONING_LOOP_AND_MEMORY_V1.md:9` calls itself "not an implementation"; the dashboard marks the agent "Not started"). The **README overstates readiness** ("IC prep") relative to running code.

### 1.2 The ACID model — key vs. behavioral layer
- **As a join key, ACID is applied consistently** across equity VIR, fixed income, holdings, and algo. Good.
- **As the behavioral interpretation layer, it is never consumed at runtime.** The mapping file (`data/acid_mapping_bootstrap_v1.csv`) carrying `interpretation_type`, `comparison_group`, `relative_value_group`, etc. is only ever *written* (by `build_bootstrap_acid_mapping.py`) — **no runtime module loads it.** This is why `MAPPING_VERSION = "mapping_layer_pending_review"` and why challenge Trigger 5 is deferred (`challenge_triggers.py:26`). The product's stated differentiator ("mapping tells the agent how to think") is disconnected.

### 1.3 Module structure
- The `src/` (library) vs `scripts/` (thin CLI) split is **coherent and the better part of the codebase.**
- But there's notable drift below the agent: duplicated single-signal vs. `*_multisignal.py` stacks, a 784-line dual-format renderer, a 589-line mapping bootstrap, and a React frontend — all built around output whose narrative content is still placeholder. This contradicts the project's own "start narrow" operating principle.

### 1.4 What's missing for the PM/IC workflow
- The **agent runtime** (loop + LLM + tool dispatch + write/memory tools) — the core product.
- The **fixed-income VIR parser** — fully spec'd, not implemented.
- The **equity *monthly* model parser** — only the *history* sheet parser exists; the monthly `General Model` sheet parser is doc-only, and the sample workbook isn't even in `data/`.
- A **governance/config layer** — thresholds/versions are scattered code constants; the spec'd `config/agent_governance.yaml` doesn't exist.
- **Tests** — none.

---

## 2. Data & financial correctness

> This section is the highest-stakes. Several findings were confirmed by running the pipeline on the real workbooks, not just reading code.

### CRITICAL

**C1 — Cross-ACID-type double-counting in the IC-facing fund summary**
`fund_weights_summary.py:87-88`. `fund_rows` spans all three `acid_type`s (`acid_country`, `acid_region_sector`, `acid_bond`). Country and region-sector are two taxonomies over the *same* securities, so summing across them double-counts. **Confirmed live:** the summary prints "summed target rolled exposure: **199.14**" for MStar US Equity and **198.13** for International Equity — ~199% of a 100% fund, rendered straight into the markdown an IC reads.
*Fix:* sum within a single `acid_type`, break the total out per type, or drop the aggregate.

**C2 — Empty benchmark coverage produces phantom 100% "active" bets**
`rolled_exposures.py:344` (`active = target − benchmark`), root cause at `:419-423`. For the bond funds, benchmark account weights sum to **0.0** despite `benchmark_available=True`, so `active = target − 0 = target` — the *entire* position is reported as an active overweight (e.g. Defensive Bond `US Secu` active = 26.70 = full target). `challenge_triggers` then fires spurious sign-disagreement triggers on what is really "no benchmark data."
*Fix:* when benchmark coverage ≈ 0 but target is populated, null out `active_rolled_exposure` or carry a `benchmark_coverage_ok` flag that triggers must honor.

**C3 — Hardcoded account row range silently drops a real account**
`rolled_exposures.py:409` — `range(5, 83)` stops at row 82, but the workbook has a populated account in **row 83** (`secid XIUSA000MC`). Lookthrough rows mapping only to that account are dropped at the join with no warning.
*Fix:* detect the account block extent dynamically (read until first blank secid) and assert the observed last row.

### HIGH
- **H1 — Unmatched lookthrough rows silently discarded.** `rolled_exposures.py:92-94` does `if account is None: continue` with no count/log. With 32k lookthrough rows, a join-key drift silently zeroes exposures. *Fix:* count and report dropped portcodes; warn if the dropped fraction exceeds a threshold.
- **H2 — `usd_unhedged` algo perspective collapsed in trigger eval.** `challenge_triggers.py:402-411` always prefers `local_real` with an order-dependent `group_rows[0]` fallback — undoing the multisignal patch's intent and being non-deterministic. *Fix:* make the fallback deterministic; evaluate per perspective if algo signals matter to triggers.
- **H3 — Non-numeric cells crash the whole parse.** Every `_to_float` does a naked `float()` (`rolled_exposures.py:636`, `algo_parser.py:146`, `equity_history.py:284`, `alignment.py:227`). A single `"NA"`/`"#N/A"`/Excel error cell aborts the monthly run. *Fix:* route non-numerics to a warnings channel with row/col/file context.
- **H4 — Cached formula values trusted blindly; error cells leak.** `workbook_xml.py:161-162` returns cached `<v>` text without checking `t="e"`. `#REF!`/`#DIV/0!` strings flow into `_to_float` (→ crash) or string fields (unnoticed). *Fix:* treat `t="e"` as null/missing and record it.

### MEDIUM
- **M1 — Composite algo signals sum metrics with no completeness check.** `signal_aliases.py:91-131` synthesizes e.g. `US MID EQ = US MID G EQ + US MID V EQ` by plain addition; `_sum_metric` returns a partial sum when only one component is present, silently reporting a half-composite. Summing MoM *change* metrics is also only valid if components are additive+complete. *Fix:* require all components present (else `None`); tag synthesized rows.
- **M2 — Single-signal path still overwrites same-ACID rows.** `rolled_exposure_alignment.py:205-213` keys latest-algo by `acid` only — the exact bug the multisignal patch fixed, still shipping via `fund_weights_vir_algo.py`. *Fix:* deprecate the single-signal path.
- **M3 — Equity history date parse assumes ISO.** `equity_history.py:120` `date.fromisoformat(...)` works today but dies on Excel serials (which the algo spec uses). *Fix:* detect serial vs ISO.
- **M4 — VIR alias overwrites real ACID without provenance.** `signal_aliases.py:49-57,84-88` back-fills e.g. `AU RE EQ` from `AU EQ` (REITs ≠ broad equity) and marks it `matched_to_vir` indistinguishably from a true match. *Fix:* add `vir_match_kind` (`direct` / `aliased_from:<acid>`).
- **M5 — Rank-in-category computed over the whole universe.** `equity_history.py:251-263` + `challenge_triggers.py:414-429` convert universe-wide rank into quartiles that drive directional triggers — miscalibrated vs. true peer category. *Fix:* gate sign-disagreement firing on true category membership; surface the limitation meanwhile.

### Verified CORRECT (no action)
`excel_serial_to_date` epoch (1899-12-30); `snapshot_date = max(periods)`; `stf = local_real_vir − unconditional_vir` matches spec; the per-security rolled-exposure multiply is unit-consistent (~99–100% for fully-invested funds); within-type grouping does not double-count (only the cross-type sum in C1 does); decomposition-rotation weakening math is internally consistent.

---

## 3. Code quality & bugs

**Overall read:** solid, careful, mid-to-senior code being rushed at the edges. Strong points: frozen dataclasses, modern type hints, `from __future__ import annotations`, deterministic row-IDs, replay-safe gating, `newline="" encoding="utf-8"` on every CSV, dependency-free XLSX reader. **No bare/broad excepts, no mutable default args, every file opened in a `with` block** — genuinely clean on those axes.

### Bugs
- **HIGH — `watch_item_count` key typo → always renders 0.** `render_monthly_review_report.py:127` reads `watch_item_count`; emitter writes `watch_items_count` (`memory_store.py:74`). Confirmed mismatch. *Fix:* one-character correction.
- **MED — Deprecated `datetime.utcnow()` (3 sites)** at `rolled_exposures.py:77`, `equity_history.py:92`, `monthly_review.py:53` — naive datetime labeled `"Z"`. *Fix:* `datetime.now(timezone.utc)` (already done correctly in the bundle builder).
- **MED — `algo_parser.parse_algo_workbook` double-builds records.** `:149` sets `snapshot_date` from a partially-populated `all_periods` inside the loop, then `:167-184` rebuilds the entire list to overwrite it. *Fix:* compute `max(all_periods)` once after the loop, construct once.

### Duplication (highest-impact cleanup)
- **HIGH — `rolled_exposure_alignment.py` vs `_multisignal.py` are ~90% identical** (~150 duplicated lines incl. byte-identical dataclasses), same for the two `fund_weights_vir_algo*.py` wrappers. Any schema change needs lockstep edits to both. *Fix:* one module, parameterize the algo-join strategy.
- **HIGH — XLSX parser copy-pasted into `rolled_exposures.py:502-589`**, duplicating `XlsxWorkbook` methods in `workbook_xml.py`. *Fix:* add a sheet-filtered loader to `XlsxWorkbook`, delete the copy.
- **MED — `_to_float/_to_int/_fmt/_shorten/_top_rows/_dedupe` copied across 6+ modules** (~120 lines). *Fix:* shared `_csvutil`/`_fmt` module.
- **MED — 11-line `sys.path` bootstrap repeated in all 16 scripts.** *Fix:* make the package installable (`pip install -e .`) and import normally.

### Reproducibility / config
- **HIGH — Dated input filename baked into argparse defaults.** `build_fund_weights_vir_algo*.py` default to `data/RMv2_PCT_Mstar_funds_2026-04-06.xlsm`. Next month silently parses last month's file. *Fix:* make required, or glob newest `data/RMv2_*.xlsm`.
- **HIGH — `pyproject.toml` declares no dependencies and no `[build-system]`.** Good news: code is genuinely **stdlib-only** (verified), so runtime risk is low. But it isn't installable (hence the 16× path hack) and pytest isn't declared. *Fix:* add `[build-system]`, a `dev`/`test` extra.
- **MED — `artifacts/...` paths hardcoded as CWD-relative module constants** (`agent_tools.py:15`, `challenge_triggers.py:17`, `memory_store.py:13`, `monthly_review.py:18-19`). Tools only work from repo root. *Fix:* centralize `ARTIFACTS_ROOT` resolved from `__file__` or env.

### Testing
- **No `tests/` directory, zero tests** despite pytest being configured. Highest-value targets: row-id stability, `equity_history._apply_trend_fields` (rank/delta), `challenge_triggers` state machine, `signal_aliases` composite/alias, `agent_tools` as-of replay guards, a tiny round-trip XLSX parse, and a regression for the `watch_items_count` key.

### Dead code (low)
`workbook_xml.py:55` `Worksheet.row()`, `XlsxWorkbook.sheet_names`, `row_ids.py:89` `fund_multisignal_row_id` — defined, never called.

---

## 4. Prioritized fix roadmap

### Tier 0 — Correctness (do first; these produce wrong IC numbers)
1. **C1** double-counting in `fund_weights_summary.py` (199% exposure)
2. **C2** phantom 100% active bets on bond funds (empty benchmark coverage)
3. **C3** hardcoded `range(5, 83)` dropping account row 83
4. **H1** silent discard of unmatched lookthrough rows (add counts/warnings)
5. `watch_items_count` key typo

### Tier 1 — Robustness & trust
6. **H3/H4** non-numeric & error-cell handling (stop crashing / silent leaks)
7. Add a `tests/` suite covering the analytic heart (row-ids, trend fields, triggers, replay guards)
8. **H2/M2** make perspective dedupe deterministic; deprecate single-signal path
9. Remove dated argparse default; glob newest workbook

### Tier 2 — Maintainability & packaging
10. Make package installable; add `[build-system]` + dev extra; delete 16× `sys.path` hack
11. Merge the duplicated single/multisignal modules; reuse `XlsxWorkbook` in `rolled_exposures`; consolidate shared helpers
12. Centralize `ARTIFACTS_ROOT`; replace `datetime.utcnow()`; fix `algo_parser` double-build
13. **M1/M4/M5** composite completeness flag, VIR alias provenance, category-aware quartiles

### Tier 3 — The actual product (largest effort, the core bet)
14. Build the LLM tool-calling loop + the 4 write tools + memory-mutation path
15. Wire the behavioral ACID mapping file into `get_fund_snapshot`/triggers (unlock Trigger 5)
16. Implement the fixed-income VIR parser and the equity monthly-model parser
17. Externalize governance config (`config/agent_governance.yaml`)
18. Re-point the frontend at live outputs (after the above produces real content)

---

## Bottom line

You have an excellent **specification and a clean deterministic core**, but the product's defining feature (the agent) is unbuilt, the behavioral mapping is disconnected, and there are **financial-correctness bugs reaching the IC-facing output**. The single highest-leverage sequence: **fix the Tier 0 number bugs now**, add a test net (Tier 1), then commit to building the actual agent loop (Tier 3). Avoid further investment in the renderer/frontend until they have real content to show.
