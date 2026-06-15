# Session Log

## Date

- 2026-04-01
- 2026-04-02
- 2026-04-09
- 2026-04-13
- 2026-05-30

## What We Accomplished

### Foundation and architecture

- Confirmed the project should be a true LLM-led agent, not a deterministic Python pipeline disguised as an agent.
- Confirmed the implementation repo is the private GitHub repository `MIMAgent/Portfolio-Analyst-Agent`.
- Bootstrapped the repository with an initial `README.md`.
- Read and incorporated the local planning documents:
  - `PM_ANALYST_AGENT_SCHEMA_V1.md`
  - `PM_ANALYST_CRITICAL_REASONING_UPDATE.md`
  - `VIR_Parser_Requirements_Handoff.md`
- Read `PM_Analyst_Agent_Deployment_Architecture.md` and used it to anchor the end-state deployment plan across Model 1, Model 2, and Model 3.
- Confirmed the repo should use an agent-first architecture where Python provides tools, persistence, validation, and auditability, while the LLM performs the actual analytical reasoning.

### Equity parser and mapping work

- Inspected the sample workbook `202602-Equity Model.xlsx` and verified the workbook structure.
- Identified the primary equity parser sheet and header layout:
  - sheet: `General Model`
  - machine-readable header row: `3`
  - business label row: `5`
  - first data row: `6`
  - canonical join key: `ACID`
- Confirmed the v1 equity signal definitions from the PM and treated them as superseding earlier generic assumptions.
- Published the initial equity parser specification to the repo.
- Confirmed the exact `Growth_RD10` field location in the equity workbook: column `PX`.
- Updated the equity parser spec to require `Growth_RD10` explicitly.
- Added and validated the equity mapping seed file and confirmed it is a complete 1:1 ACID coverage match versus the equity model workbook.
- Added deterministic normalization rules for the current thin equity mapping file.
- Logged one likely source anomaly for later review: `EM UT EQ` is currently labeled `Industry`.

### Fixed income parser and mapping work

- Inspected the sample fixed income model export `202602- Fixed Income Model.csv`.
- Confirmed the fixed income export is already structurally normalized as CSV with machine-friendly headers.
- Published the initial fixed income parser specification to the repo.
- Refined the fixed income USD-hedged-YTM helper rule to apply only to treasury ACIDs for the PM-specified developed-markets allowlist.
- Incorporated PM guidance that treasury and corporate maturity buckets are part of the thesis, not just metadata.

### Shared mapping and holdings design work

- Added a shared ACID mapping schema that treats mappings as behavioral metadata, not just category labels.
- Locked the decision to use separate equity and fixed income mapping files, both governed by the same shared ACID schema.
- Locked the decision to govern the treasury hedged-YTM allowlist in the fixed income mapping file rather than parser config.
- Created a holdings-to-ACID crosswalk guide for cases where holdings do not carry ACID directly.
- Clarified the current holdings design: the expected holdings file is exposure-based rather than security-based.
- Locked the v1 holdings join approach: use an approved exposure-label-to-ACID crosswalk for `sector`, `country`, and `style` rows.
- Captured the need to use benchmark or universe context for potentially ambiguous labels such as `Large Cap Value`.
- Reviewed the sample holdings workbook `RMv2_PCT_Mstar_funds_2026-03-05.xlsm` based on PM-provided structural details.
- Confirmed the holdings input is an equity exposure matrix on the `Equity exposure` tab rather than a security-level holdings export.
- Confirmed the portfolio name is sourced from cell `A4`.
- Confirmed the holdings snapshot date should be parsed from the workbook filename.
- Confirmed the workbook layout is consistent across the initial portfolio set.
- Reviewed the companion holdings mapping file and confirmed it is sufficient to drive cell-level ACID attachment.
- Published the initial holdings parser specification to the repo.
- Published the initial holdings-to-VIR cross-reference specification to the repo.

### Monthly output package and workflow

- Reviewed the minimum monthly output-package question.
- Recommended that the monthly algo file should appear as a separate artifact rather than being buried inside another report.
- Kept the broader monthly output-package decision open pending review of the actual algo file.
- Captured that the algo file may affect whether the monthly package needs a separate sizing-aware implementation artifact.

### Dashboard and planning work

- Created project dashboard docs based on the deployment architecture and current parser and mapping decisions.
- Created a compressed Q2 2026 execution dashboard instead of using an overly long sprint board.
- Created a one-page Q2 meeting dashboard for live discussion use.
- Reviewed the Q2 dashboard immediate questions one by one.
- Updated the Q2 dashboard so questions 1, 2, 3, and 5 are now reflected as completed decisions, with only question 4 left open.

### Stakeholder decision

- Initially documented the broader stakeholder set that would eventually matter for a shared Model 2 deployment.
- Then refined the current-phase decision based on user guidance:
  - for the present Q2 planning and design phase, the key stakeholders are PM lead and Shivika
  - broader IT, InfoSec, IAM, compliance, and data-owner approvals are future implementation dependencies, not current planning blockers

## Equity Parser Decisions Locked In

### Workbook structure

- Source workbook type: Excel `.xlsx`
- Primary sheet: `General Model`
- One row per equity ACID
- Use row `3` machine headers for extraction
- Use row `5` business labels for lineage/debugging
- Stop parsing when ACID becomes blank after data starts

### Canonical join key

- `ACID`

### Required identity fields

- `asset_class_name` from column `B`
- `acid` from column `C`

### Confirmed primary equity fields

- `local_real_vir` = `LR10_Combined` (`RJ`)
- `local_nominal_vir` = `N10USD_Combined` (`RM`)
- `usd_hedged_vir` = `N10USDH` (`ALH`)
- `unconditional_vir` = `LRUC_Combined` (`RL`)
- `price_to_fair_value` = `PFV_t` (`QQ`)

### Confirmed equity STF definition

- `stf = LR10_Combined - LRUC_Combined`

This supersedes the earlier incorrect generic STF definition.

### Confirmed decomposition fields

- `inflation` = `Infl_RD10` (`PU`)
- `currency_usd` = `USD_RD10` (`PV`)
- `yield` = `Yld_RD10` (`PW`)
- `growth` = `Growth_RD10` (`PX`)
- `valuation_adjustment_top_down` = `ValAdj_RD10` (`PY`)
- `valuation_adjustment_combined` = `ValAdj_RD10_Combined` (`RG`)

### Derived decomposition field

- `valuation_adjustment_bottom_up = 2 * ValAdj_RD10_Combined - ValAdj_RD10`

## Fixed Income Parser Decisions Locked In

### File structure

- Source file type: CSV
- One row per fixed income ACID
- Header row is already machine-friendly
- Canonical join key: `acid`

### Confirmed primary fixed income fields

- `acid`
- `currency`
- `curve_type`
- `yield_tomaturity`
- `duration`
- `oas`
- `convexity`
- `oas_fv`
- `termspread`
- `termspread_fv`
- `yield_tomaturity_fv`
- `fx_usd_hedged_1`
- `local_nominal_10`
- `local_real_10`
- `usd_hedged_10`
- `real_vir_fair`

### Confirmed fixed income STF definition

- `stf = local_real_10 - real_vir_fair`

### Confirmed 10-year decomposition fields

- `income_contrib_10`
- `rollyield_contrib_10`
- `creditloss_contrib_10`
- `price_contrib_10`
- `inflation_contrib_10`
- fair-value reference: `inflation_contrib_fair`

### Derived helper field

- `usd_hedged_yield_to_maturity_1 = yield_tomaturity + fx_usd_hedged_1`
- Apply only to treasury ACIDs in the current developed-markets allowlist:
  `AU T`, `CA T`, `EU T`, `EU T: DEU`, `EU T: ESP`, `EU T: FRA`, `EU T: ITA`, `JP T`, `UK T`
- Governance decision: the helper eligibility should live in the fixed income mapping file, not parser config

## Mapping and Holdings Decisions Locked In

- ACID mappings are not just taxonomy.
- They must also define analytical interpretation rules for the agent.
- This rule applies across both equities and fixed income.
- Shared mapping contract is documented in `docs/ACID_MAPPING_SCHEMA_V1.md`.
- The current equity mapping file is accepted as a seed taxonomy file and can be normalized into the shared schema with deterministic defaults.
- Equity and fixed income mappings should live in separate files using the same shared schema.
- Holdings for the current workflow should be treated as exposure-based rows rather than security-level rows.
- The v1 holdings join should use an exact governed exposure-label-to-ACID crosswalk for benchmark and portfolio labels in `sector`, `country`, and `style`.

## Output Package Status

- The monthly algo file should be treated as a separate artifact in the Model 1 monthly package.
- The final definition of the minimum acceptable monthly output package remains open until the algo file is reviewed.

## Holdings Parser Decisions Locked In

### Workbook structure

- Source workbook type: Excel `.xlsm`
- Primary sheet: `Equity exposure`
- One workbook per portfolio
- Portfolio name source: cell `A4`
- Snapshot date source: parse from the workbook filename

### Exposure matrix layout

- Row labels live in column `A`
- Sector headers are in row `8`
- Data rows begin at row `9`
- Portfolio weights are in columns `B:N`
- Benchmark weights are in columns `Q:AC`
- Active weights are in columns `AF:AR`
- Risk contribution is in columns `AU:BG`
- Label columns `A`, `P`, `AE`, and `AT` are not data columns

### Holdings mapping dependency

- The workbook does not contain `ACID` directly
- `holdings_mapping.csv` is the canonical bridge between workbook cells and ACIDs
- Mapping is cell-aware and section-aware, not just row-label aware
- `Total` columns often map to row-level region or country ACIDs and should be retained

### Confirmed holdings parsing rules

- `column_header = N/A` should be skipped
- `Total` columns should be ingested
- Region rows and country rows should both be ingested
- Double counting across region and country rows is acceptable because they represent different aggregation levels
- Blank workbook cells should remain `null`
- Numeric zero should remain `0`

## Holdings Cross-Reference Decisions Locked In

- v1 cross-reference should use `ACID` only
- Only holdings rows with a usable `ACID` should be joined to VIR
- Do not perform fuzzy matching for unmapped holdings rows
- Do not infer substitute identifiers when `ACID` is missing
- Unmapped holdings rows should remain visible for QA and reporting but should be excluded from alignment logic
- Cross-reference should preserve section granularity across:
  - `portfolio_weight`
  - `benchmark_weight`
  - `active_weight`
  - `risk_contribution`
- `Total` rows should participate in the join when they have an `ACID`
- Region rows and country rows should both remain in the raw joined output without de-duplication
- Preferred snapshot matching rule is to use the most recent VIR snapshot on or before the holdings snapshot date

## Repo Files Added Today

- `README.md`
- `docs/EQUITY_VIR_PARSER_SPEC_V1.md`
- `docs/FIXED_INCOME_VIR_PARSER_SPEC_V1.md`
- `docs/ACID_MAPPING_SCHEMA_V1.md`
- `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`
- `session_log.md`

## 2026-04-09 Update

### Equity VIR history and trends

- Added a new equity VIR history parser module at `src/portfolio_analyst_agent/equity_history.py`.
- Added a CLI wrapper at `scripts/parse_equity_vir_history.py`.
- Updated `docs/EQUITY_VIR_PARSER_SPEC_V1.md` so the separate `vir_history.xlsx` workbook now maps into the same canonical equity field contract as the monthly equity parser.
- Confirmed the history-file mappings:
  - `usdn_uh10_combined` -> `local_nominal_vir`
  - `pfv_agg` -> `price_to_fair_value`
- Implemented trend-ready normalization fields for the history series:
  - `stf`
  - prior STF
  - month-over-month deltas
  - STF rank
  - prior rank
  - rank change

### Workbook ingestion support

- Fixed an XLSX relationship-path issue in `src/portfolio_analyst_agent/workbook_xml.py` so workbook sheet targets with leading `/xl/...` paths parse correctly.
- Added the source workbook into the repo at `data/vir_history.xlsx`.

### Python setup and parser validation

- Installed Python 3.11 locally and validated the interpreter path:
  - `C:\Users\schuri2\AppData\Local\Programs\Python\Python311\python.exe`
- Ran the history parser end to end against the real workbook.
- Successful parse results:
  - `source_file=vir_history.xlsx`
  - `row_count=326830`
  - `snapshot_count=675`
  - `acid_count=1469`
  - `latest_snapshot_date=2026-02-28`
- Generated normalized output:
  - `artifacts/equity_vir_history.csv`

### Rolled exposure workflow replacement

- Replaced the earlier holdings-parser / holdings-to-VIR-cross-reference approach with a workbook-specific rolled exposure workflow built from the `Portfolio` and `Full_lookthrough` tabs.
- Added the Morningstar workbook to the repo at `data/RMv2_PCT_Mstar_funds_2026-04-06.xlsm` so collaborators can run the parser locally after pulling.
- Added `scripts/build_rolled_exposures.py` and `src/portfolio_analyst_agent/rolled_exposures.py`.
- The new rolled exposure parser:
  - matches `Portfolio!B` secid to `Full_lookthrough!B` portcode
  - uses only:
    - `Full_lookthrough!V` for `acid_country`
    - `Full_lookthrough!W` for `acid_region_sector`
    - `Full_lookthrough!X` for `acid_bond`
  - preserves `security_name`, `common_identifier`, and `h_path` so ACID exposures can be traced back to the source holdings rows
  - builds both account-level and fund-level rolled exposures
  - carries benchmark exposure rollups alongside target exposure rollups
- Added `scripts/build_rolled_exposure_alignment.py` and `src/portfolio_analyst_agent/rolled_exposure_alignment.py`.
- The new alignment layer cross-references rolled account and fund ACID exposures to:
  - normalized VIR rows
  - latest algo signals when monthly algo workbooks are provided
- Added `scripts/build_fund_weights_vir_algo.py` and `src/portfolio_analyst_agent/fund_weights_vir_algo.py`.
- The new fund-level orchestration script runs the rolled exposure parser and then writes a single combined CSV that carries:
  - fund target rolled exposure
  - fund benchmark rolled exposure
  - active rolled exposure
  - VIR STF and rank fields
  - latest algo weights and month-over-month fields
- Added a technical workflow reference doc at `docs/ROLLED_EXPOSURE_AND_FUND_ALIGNMENT_WORKFLOW_2026-04-09.md` covering:
  - the rolled exposure parser logic
  - the `Portfolio` and `Full_lookthrough` workbook structure
  - the VIR join logic
  - the algo join logic
  - the combined fund weights + VIR + algo workflow
- Generated rolled exposure outputs locally under `artifacts/rolled_exposures/`, including:
  - account detail and summary
  - fund detail and summary
  - fund coverage
  - fund definitions
  - account-to-VIR/algo alignment
  - fund-to-VIR/algo alignment
- Removed the superseded docs:
  - `docs/HOLDINGS_PARSER_SPEC_V1.md`
  - `docs/HOLDINGS_VIR_CROSS_REFERENCE_SPEC_V1.md`

## Current Repository References

- Repo: `MIMAgent/Portfolio-Analyst-Agent`
- Equity parser spec: `docs/EQUITY_VIR_PARSER_SPEC_V1.md`
- Fixed income parser spec: `docs/FIXED_INCOME_VIR_PARSER_SPEC_V1.md`
- Shared mapping schema: `docs/ACID_MAPPING_SCHEMA_V1.md`
- Equity mapping normalization: `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`
- Q2 execution dashboard: `docs/PROJECT_DASHBOARD_Q2_2026.md`
- Q2 one-pager: `docs/PROJECT_DASHBOARD_Q2_2026_ONE_PAGER.md`
- Rolled exposure parser: `scripts/build_rolled_exposures.py`
- Rolled exposure alignment: `scripts/build_rolled_exposure_alignment.py`

## Agreed Next Steps

1. Review the monthly algo file.
2. Finalize the minimum acceptable monthly output package.
3. Scaffold the holdings parser implementation and supporting folder structure in the repo.
4. Implement the mapping-driven holdings workbook normalization flow.
5. Implement the ACID-only holdings-to-VIR join layer.
6. Resolve whether `EM UT EQ` should remain `Industry` or be corrected to `Sector`.
7. Continue building toward the Q2 Model 1 operating workflow.

## Open Items

- Review the monthly algo file and decide how the separate sizing artifact should be framed.
- Gather the initial portfolio workbooks to use for parser smoke tests.
- Decide whether the first code pass should include only holdings parsing or also the cross-reference join implementation.
- Resolve the `EM UT EQ` category anomaly.
- Define the final Model 1 output pack once the algo file is reviewed.

## Working Principle

- Keep the system agent-first.
- Python should provide ingestion, storage, validation, audit logging, and tool wrappers.
- The LLM should remain responsible for hypothesis formation, decomposition interpretation, position challenge, memory updates, and PM-facing output.

## 2026-04-13 Update

### Today

- Ran a real practice round from the saved repo checkout at `Desktop/Portfolio Agent _Repo` using repo code and repo data rather than ad hoc local files.
- Rebuilt normalized equity VIR history from `data/vir_history.xlsx` and confirmed the latest snapshot date remains `2026-02-28`.
- Ran the new multisignal fund-alignment workflow against the real algo workbooks `data/Algo LR.xlsx` and `data/Algo USD Unhedged.xlsx`.

### Done

- Validated the additive multisignal workflow path that preserves both algo perspectives instead of collapsing to one row per ACID.
- Confirmed dimension-aware algo joins now behave as intended:
  - `acid_country` joins only to `Countries`
  - `acid_region_sector` joins only to `RegionalSectors`
  - `acid_bond` remains out of the current equity algo join
- Generated a real combined output at `artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv`.
- Practice-round output summary:
  - `941` total rows
  - `810` rows matched to VIR
  - `131` rows missing in VIR
  - `680` rows matched to algo
  - `144` rows missing in algo
  - `117` rows marked `not_applicable_for_acid_type`
- Split benchmark diagnostics into two cleaner artifacts:
  - `artifacts/rolled_exposures/funds_with_no_usable_benchmark.csv`
  - `artifacts/rolled_exposures/acid_rows_with_zero_benchmark_exposure_in_benchmarked_funds.csv`
- Confirmed the benchmark nuance for funds like `MStar US Equity`: benchmark is present at the fund level, but some individual ACIDs legitimately have zero benchmark exposure.
- Confirmed the true current fund-level benchmark exceptions in this practice round are:
  - `MStar Total Return Bond`
  - `MStar Defensive Bond`
  - `MStar Multisector Bond`
  - `MStar Alternatives`

### Next

- Decide whether the `*_multisignal` workflow should replace the older default alignment path in the repo.
- Define the PM-facing artifact layer that should sit on top of the normalized CSV outputs.
- Continue practice-round review on benchmark handling before locking any behavior change for benchmarkless funds.
- Start shaping the backend outputs into UI-friendly summary, detail, and diagnostics datasets.

### Current Readout

- The backend foundation is now real and runnable.
- The project has moved from parser and mapping design into workflow hardening, interpretation decisions, and UI-shaping.
- The main open questions are no longer whether the data can be parsed, but how the outputs should be presented and governed.
- This update supersedes the older holdings-parser next steps listed above; the active path is the rolled exposure and fund-alignment workflow documented in `docs/ROLLED_EXPOSURE_AND_FUND_ALIGNMENT_WORKFLOW_2026-04-09.md`.

## 2026-04-27 Update

### Today

- Reviewed fund-level rolled exposure outputs fund by fund rather than only looking at aggregate workflow outputs.
- Added ACID alias and fallback logic so known parent-bucket and cross-taxonomy mismatches can connect more cleanly to VIR and algo without changing the source workbook.
- Added a reusable review-pack generator and pushed the resulting checklist into the repo.

### Done

- Added `src/portfolio_analyst_agent/signal_aliases.py` to centralize:
  - VIR fallback aliases such as:
    - `EM EQ -> EM Comp EQ`
    - `AU RE EQ -> AU EQ`
  - algo aliases such as:
    - `US RE EQ -> US REIT`
    - `AU RE EQ -> AU REIT`
    - `EM RE EQ -> EM REIT`
    - `EU RE EQ -> EU REIT`
    - `JP * EQ sector rows -> JP EQ`
  - composite algo rollups such as:
    - `US MID EQ = US MID G EQ + US MID V EQ`
    - `US SML EQ = US SML G EQ + US SML V EQ`
    - `US LRG EQ = US LRG G EQ + US LRG V EQ`
- Updated the rolled exposure parser to reclassify specific `US EQ` parent-bucket residues into more useful size buckets where explicitly reviewed and approved:
  - small-cap ETF and systematic-SMID residues into `US SML EQ`
  - selected benchmark and security-specific rows into `US MID EQ` / `US LRG EQ`
- Added:
  - `scripts/build_fund_review_pack.py`
  - `src/portfolio_analyst_agent/fund_review.py`
  - `artifacts/fund_review/fund_review_checklist.csv`
- Pushed the work to `main` in commit `2e0ba48` with the message:
  - `Add fund review checklist and ACID alias rules`

### Fund Review Readout

- `MStar US Equity`
  - Mostly clean after alias and residual reclassification work.
  - Remaining items are acceptable exceptions such as `USD Cash`, tiny `EM EQ`, and benchmark-only residuals.
- `MStar International Equity`
  - Mostly clean after:
    - `AU RE EQ -> AU EQ` for VIR
    - `AU/EM/EU RE EQ -> REIT` for algo
    - `JP` sector rows mapped to `JP EQ` for algo
  - Remaining `USD Cash`, `EM EQ`, and `US EQ` exceptions were accepted as reviewable but not blocking.
- `MStar Global Opportunistic Equity`
  - Mostly clean.
  - Accepted exceptions:
    - `USD Cash`
    - `EM EQ` under `EM Comp EQ` for VIR and ignored in algo
    - `US EQ` kept in VIR and ignored in algo
    - tiny `EM LC T: Gbl Div. (JPM)` residual
- `MStar Global Income`
  - Mostly clean.
  - Accepted exceptions:
    - `USD Cash`
    - benchmark-only `EM EQ`
    - small `US EQ` parent bucket
- `MStar Municipal Bond`
  - Initial review started.
  - Current behavior still reflects the absence of a normalized fixed-income VIR source in the repo.

### Current Readout

- The review process is no longer blocked on generic parser plumbing for equity-style joins.
- The project now has a usable mechanism for:
  - documenting fund-by-fund review decisions
  - encoding reviewed alias logic into the repo
  - rerunning the full workflow after business-rule decisions are made
- The largest remaining gap is not the equity workflow anymore.
- The largest remaining structural gap is fixed-income VIR ingestion and connection.

### Recommended Next Direction

1. Finish the remaining fund reviews in order:
   - `MStar Municipal Bond`
   - `MStar Total Return Bond`
   - `MStar Defensive Bond`
   - `MStar Multisector Bond`
   - `MStar Alternatives`
2. Decide whether accepted review exceptions should remain checklist-only decisions or be encoded as permanent parser/alias rules.
3. Bring fixed-income VIR into the repo as a normalized source and connect bond ACIDs to it.
4. After all 9 funds are reviewed, collapse the checklist findings into a stable PM-facing artifact layer.

## 2026-04-28 Update

### What Changed

- Pulled and reviewed the new agent-layer work added by others:
  - `576a015` `Add agent reasoning loop and memory schema`
  - `3a79c01` `Add fund snapshot read tool and stable row IDs`
- Confirmed the project direction is now shifting from raw artifact generation toward a fund-by-fund agent operating contract built around:
  - one fund at a time
  - explicit `as_of_date`
  - evidence-backed claims
  - governed memory
  - replay-safe tool outputs
- Chose a hybrid deterministic row ID format for the first durable evidence layer:
  - readable type prefix plus compact stable hash
  - examples:
    - `fsum_<hash>`
    - `fdet_<hash>`
    - `falg_<hash>`
    - `frvw_<hash>`

### Row ID Contract

- Added `src/portfolio_analyst_agent/row_ids.py` as the shared row ID utility module.
- Implemented row IDs from stable business keys rather than random UUIDs.
- Row IDs are now created at row-build time inside the generators, not as a post-processing step.
- The current contract is:
  - fund summary row:
    - `snapshot_date + fund + acid_type + acid`
  - fund multisignal alignment row:
    - `snapshot_date + fund + acid_type + acid + algo_perspective`
  - fund detail row:
    - `snapshot_date + fund + account_name + security_name + acid_type + acid`
  - account summary row:
    - `snapshot_date + account_name + acid_type + acid`
  - account detail row:
    - `snapshot_date + account_name + security_name + acid_type + acid`
- The canonical key is hashed into a short deterministic ID with a row-type prefix.

### Where Row IDs Were Added

- Added deterministic `row_id` fields to the generated artifacts that the agent will need to cite:
  - `fund_weights_vir_algo.csv`
  - `fund_weights_vir_algo_multisignal.csv`
  - `fund_rolled_exposure_summary.csv`
  - `fund_rolled_exposure_detail.csv`
  - `account_rolled_exposure_summary.csv`
  - `account_rolled_exposure_detail.csv`
  - `fund_rollthrough_coverage.csv`
  - `fund_rollthrough_definitions.csv`
  - `artifacts/fund_review/fund_review_checklist.csv`
- Updated `src/portfolio_analyst_agent/evidence.py` so generic fallback evidence IDs also use the same compact deterministic style.

### Compatibility Check

- Confirmed the new row IDs fit the incoming agent tool design.
- `scripts/get_fund_snapshot.py` and `src/portfolio_analyst_agent/agent_tools.py` can now read aligned fund data that already contains stable row IDs instead of depending on ad hoc fallback hashing at read time.
- This gives the evidence layer a cleaner contract for:
  - citation
  - memory attachment
  - challenge triggering
  - replay-safe monthly review runs

### Verification

- Rebuilt the rolled exposure and alignment artifacts after wiring the new row ID helpers into the generators.
- Verified the core outputs now include `row_id` as a first-class field.
- Verified same-input reruns produce the same row IDs.
- Verified changing the logical identity of a row changes the row ID.
- Verified `get_fund_snapshot` can read a reviewed fund snapshot and surface row IDs in the returned payload.

### Current Readout

- The project now has the first real durable evidence handle the analyst agent can cite and remember.
- We are no longer limited to asking the LLM to read loose CSV rows by position or content alone.
- The next agent-building steps should now be:
  1. add stable row IDs anywhere else evidence may be cited from detail or lineage outputs
  2. implement `recall_memory`
  3. implement `evaluate_challenge_triggers`
  4. build `run_monthly_review` for one reviewed pilot fund

### Memory Layer Progress

- Added a first JSON-backed memory store at:
  - `artifacts/agent_memory/memory_records.json`
- Added `src/portfolio_analyst_agent/memory_store.py` to:
  - load the v1 memory payload
  - enforce supported memory scopes
  - filter records by `fund`, `snapshot_date`, and `as_of_date`
  - separate valid thesis, challenge, exception, and watch-item rows
- Added `recall_memory` to `src/portfolio_analyst_agent/agent_tools.py` as the first read-only memory tool.
- The current memory file uses one payload with four required v1 tables:
  - `thesis_ledger`
  - `open_challenges`
  - `exceptions`
  - `watch_items`
- The initial seed is intentionally narrow:
  - approved accepted-exception entries only
  - no thesis ledger items yet
  - no open challenges yet
  - no watch items yet
- Seeded approved exceptions reflect the reviewed fund decisions already made in session, including:
  - `USD Cash` for `MStar US Equity`
  - `EM EQ` for `MStar US Equity`
  - `EM EQ` and `US EQ` for `MStar International Equity`
  - `USD Cash` and `EM LC T: Gbl Div. (JPM)` for `MStar Global Opportunistic Equity`
  - `USD Cash` for `MStar Global Income`
- Each seeded exception points back to a stable evidence row in:
  - `artifacts/rolled_exposures/fund_weights_vir_algo.csv`

### Updated Readout

- The project now has both sides of the first analyst memory loop:
  - stable evidence row IDs
  - a replay-safe memory recall tool
- The next implementation step should be `evaluate_challenge_triggers`, because it will be able to consult both:
  - current fund snapshot rows
  - active accepted exceptions from memory

### Trigger Evaluation Progress

- Added `src/portfolio_analyst_agent/challenge_triggers.py` as the first deterministic trigger engine.
- Added `evaluate_challenge_triggers` to `src/portfolio_analyst_agent/agent_tools.py`.
- The first implemented trigger is intentionally narrow:
  - `sign_disagreement`
- The currently deferred triggers remain:
  - `decomposition_rotation`
  - `better_expression_available`
- The current implementation:
  - loads one fund snapshot through `get_fund_snapshot`
  - loads active exceptions through `recall_memory`
  - deduplicates multisignal rows down to one analytical row per `(acid_type, acid)`
  - evaluates only material rows using `materiality_threshold_active = 1.0`
  - derives equity VIR quartile context from `artifacts/equity_vir_history.csv`
  - suppresses fired candidates when an accepted exception covers the `(fund, acid, trigger_type)`
- The current implementation does not pretend unsupported rows are clean:
  - non-matched VIR rows are returned as `not_evaluable`
  - fixed-income VIR trigger logic is not yet implemented and is returned as `not_evaluable`
- Initial pilot verification:
  - `MStar US Equity`
    - 13 material sign-disagreement candidates evaluated
    - 1 fired candidate:
      - `US ID EQ`
    - 12 rows returned as `not_triggered`
  - `MStar International Equity`
    - 30 material sign-disagreement candidates evaluated
    - 3 fired candidates:
      - `NL EQ`
      - `EU ID EQ`
      - `JP IT EQ`
    - 26 rows returned as `not_triggered`
    - 1 row returned as `not_evaluable`

### Updated Next Step

- The next step after this trigger baseline should be to decide whether to:
  - tune the sign-disagreement governance thresholds first
  - or add `decomposition_rotation` next
- A practical sequence is:
  1. validate the current sign-disagreement outputs against reviewed PM expectations
  2. encode any low-noise suppression refinements needed
  3. then add `decomposition_rotation`

### Important Trigger Calibration Decision

- Added a dedicated governance note:
  - `docs/CHALLENGE_TRIGGER_CALIBRATION_2026-04-29.md`
- Decision taken:
  - keep the current base materiality threshold at `1.0`
  - do not raise the whole threshold globally yet
  - do not collapse everything to fire/no-fire
  - add a `borderline` state for weaker quartile disagreements
- Current `sign_disagreement` operating rule:
  - base materiality gate:
    - `abs(active_rolled_exposure) >= 1.0`
  - quartile directional gate:
    - top quartile = overweight VIR view
    - bottom quartile = underweight VIR view
  - full `fired` trigger only when the disagreement is stronger:
    - `abs(active_rolled_exposure) >= 1.5`
    - or VIR percentile is stronger than the quartile edge:
      - `<= 0.20`
      - or `>= 0.80`
  - otherwise classify as `borderline`
- Why this was done:
  - the earlier simpler rule was directionally good but slightly too blunt
  - `NL EQ` in `MStar International Equity` looked more like a borderline disagreement than a full challenge
- Important note:
  - this is the current rule
  - it does not have to remain the permanent rule
  - it should be revisited if PM review shows:
    - too many fired rows that should be borderline
    - too many borderline rows that should be fired

### Decomposition Rotation Progress

- Added the first `decomposition_rotation` implementation inside:
  - `src/portfolio_analyst_agent/challenge_triggers.py`
- Updated the trigger surface so the repo now formally supports:
  - `sign_disagreement`
  - `decomposition_rotation`
- Added a dedicated decision note:
  - `docs/DECOMPOSITION_ROTATION_CALIBRATION_2026-04-29.md`

### Current Decomposition Rotation Decision Rules

- Current scope is intentionally narrow:
  - equity VIR rows only
  - matched VIR required
  - active thesis memory required
  - thesis must include a usable `last_affirmed_decomp`
- Current base materiality gate:
  - `abs(active_rolled_exposure) >= 1.0`
- Current dominant-driver rule:
  - use the decomposition field with the largest absolute value
- Current equity decomposition field set:
  - `growth`
  - `yield`
  - `inflation`
  - `currency_usd`
  - `valuation_adjustment_top_down`
  - `valuation_adjustment_combined`
  - `valuation_adjustment_bottom_up`
- Current rotation rule:
  - fire when the dominant driver changes
  - and the prior dominant driver weakens enough
- Current weakening rule:
  - prior dominant driver changes sign
  - or its absolute magnitude declines by at least `0.01`

### Current Practical Readout

- The engine is implemented, but there are currently no live decomposition-rotation candidates.
- This is expected right now because:
  - `artifacts/agent_memory/memory_records.json` still has an empty `thesis_ledger`
- Pilot verification on:
  - `MStar US Equity`
  - `MStar International Equity`
- Result:
  - `thesis_backed_row_count = 0`
  - `decomposition_rotation` candidates returned = `0`

### Important Note

- This is the current operating rule.
- It does not have to remain the permanent rule.
- It should be revisited once the repo has real thesis entries and once PM review gives feedback on how sensitive the weakening rule should be.

### What We Need To Think About To Add Layers Later

1. Seed and maintain real thesis memory entries with `last_affirmed_decomp`.
2. Decide whether the `0.01` weakening rule is the right global threshold.
3. Decide whether decomposition rotation should also support a `borderline` state.
4. Add fixed-income decomposition support once fixed-income VIR normalization exists.
5. Decide whether dominant-driver logic should stay simple or become model-family-specific.
6. Future decision:
   - decide whether `decomposition_rotation` should remain thesis-only
   - or broaden later into a history-based trigger that can evaluate all ACIDs even without thesis memory
   - current decision is to keep it thesis-only

### Thesis Seeding Progress

- Seeded the first baseline thesis ledger entries in:
  - `artifacts/agent_memory/memory_records.json`
- The initial seed is intentionally narrow and cautious:
  - `review_state = proposed`
  - `status = active`
  - `visibility_scope = personal`
- Current seeded baseline theses:
  - `MStar US Equity` / `US ID EQ`
  - `MStar International Equity` / `EU ID EQ`
  - `MStar International Equity` / `JP IT EQ`
- Each seeded thesis includes:
  - `thesis_text`
  - `thesis_drivers`
  - `last_affirmed_snapshot_date`
  - `last_affirmed_stf`
  - `last_affirmed_decomp`
  - `falsification_conditions`
  - stable `evidence_pointers`

### Current Thesis Seeding Decision

- These are baseline thesis entries so future decomposition changes can be evaluated.
- They are not yet being treated as fully approved PM or house-view theses.
- Current dominant driver stored in the seeded records:
  - `valuation_adjustment_top_down`
- Important note:
  - this is the current seeding approach
  - it can be changed later if we decide thesis seeding should:
    - use `approved` instead of `proposed`
    - cover more ACIDs
    - use a richer thesis template
    - store additional decomposition context

### Practical Verification

- `recall_memory` now returns thesis rows for the seeded funds.
- `evaluate_challenge_triggers` now sees thesis-backed rows:
  - `MStar US Equity`
    - `thesis_backed_row_count = 1`
  - `MStar International Equity`
    - `thesis_backed_row_count = 2`
- `decomposition_rotation` correctly does not fire on the same affirmed snapshot.
- Current result for seeded rows:
  - `US ID EQ` -> `not_triggered`
  - `EU ID EQ` -> `not_triggered`
  - `JP IT EQ` -> `not_triggered`
- Reason:
  - dominant decomposition driver has not changed since the baseline affirmation point

### Bootstrap Mapping Progress

- Created a draft bootstrap ACID mapping layer:
  - `data/acid_mapping_bootstrap_v1.csv`
- Added the generator:
  - `scripts/build_bootstrap_acid_mapping.py`
- Added the review note:
  - `docs/BOOTSTRAP_ACID_MAPPING_2026-04-29.md`
- Important note:
  - this mapping is a bootstrap draft only
  - it has not yet been reviewed and should not be treated as part of the trusted operating process yet
  - it exists to speed up review and future `better_expression_available` work, but still needs human validation before it is relied on in production logic

### Monthly Review Harness Progress

- Since the bootstrap mapping is still unreviewed, the current path is to hold that draft aside and build the first `run_monthly_review` harness using only the trusted tools already in the repo:
  - `get_fund_snapshot`
  - `recall_memory`
  - `evaluate_challenge_triggers`
- Added the deterministic monthly review harness:
  - `src/portfolio_analyst_agent/monthly_review.py`
- Added the CLI entry point:
  - `scripts/run_monthly_review.py`
- Exported the harness from:
  - `src/portfolio_analyst_agent/__init__.py`

### Current Monthly Review Output Contract

- The harness runs one fund at a time or the full reviewed fund batch.
- It writes draft, structured monthly review artifacts under:
  - `artifacts/monthly_review/<snapshot_date>/<fund-slug>/`
- Current outputs:
  - `run_payload.json`
  - `change_brief_draft.json`
  - `sizing_considerations_draft.json`
  - `challenge_brief_draft.json` only when fired triggers exist
  - `run_summary.md`
- Batch runs also write:
  - `artifacts/monthly_review/<snapshot_date>/batch_index.json`

### Current Monthly Review Decision

- This harness is intentionally deterministic and evidence-first.
- It is currently using only trusted inputs and current trigger/memory governance.
- It is not yet using the bootstrap ACID mapping draft.
- It is not yet trying to generate final PM-ready narrative prose.
- Important note:
  - this is the current operating decision
  - it can change later once the mapping layer is reviewed and once we decide how much narrative generation should live inside the monthly review step

### Monthly Review Verification

- Verified single-fund run:
  - `python scripts/run_monthly_review.py --fund "MStar US Equity" --as-of-date 2026-04-29`
- Verified full-batch run:
  - `python scripts/run_monthly_review.py --as-of-date 2026-04-29`
- The first pilot run for `MStar US Equity` produced:
  - deterministic `review_run_id`
  - `Change Brief` draft payload
  - `Sizing Considerations` draft payload
  - `Challenge Brief` draft payload because fired triggers exist
  - markdown summary output

### What We Need To Think About Next For Monthly Review

1. Decide whether the current deterministic JSON drafts should remain the stable intermediate contract or evolve into richer PM-facing outputs.
2. Decide when to layer LLM-authored interpretation on top of the structured review payload.
3. Decide whether `run_monthly_review` should stay limited to trusted tools until the ACID mapping layer is reviewed.
4. Decide whether the monthly review step should later write proposed memory operations back into the memory layer or remain read-only for longer.

### Repo Sync Status

- The current monthly review harness work has been pushed to the online repo.
- Latest pushed commit at this point:
  - `08cf9e6` `Add deterministic monthly review harness`
- This means the current online repo now includes:
  - stable evidence row IDs
  - replay-safe memory recall
  - sign-disagreement trigger logic
  - thesis-only decomposition rotation
  - bootstrap ACID mapping draft
  - deterministic `run_monthly_review` harness

### Monthly Review Output Tracking Decision

- The generated `artifacts/monthly_review/` output set is now being tracked in git so it can be reviewed directly in the online repo.
- Other `artifacts/` outputs remain ignored for now.
- Important note:
  - this is the current tracking decision
  - it can be changed later if the monthly review outputs become too large or if we decide they should be published another way

### Artifact Tracking Decision Update

- Tracking scope has now been broadened from `artifacts/monthly_review/` to the full project `artifacts/` tree so the current local project outputs are online in the repo.
- Current intent:
  - keep project artifacts online
  - keep only obvious runtime/cache directories ignored
- Current ignored local-only paths are now limited to:
  - `__pycache__/`
  - `.pytest_cache/`
  - `node_modules/`
  - `.tmp_vir_history/`
- GitHub size-limit exception:
  - raw `artifacts/equity_vir_history.csv` exceeds GitHub's normal file limit
  - current approach is to keep the raw CSV local and track `artifacts/equity_vir_history.csv.zip` online as the mirror artifact
- Important note:
  - this is the current tracking decision
  - it can be changed later if we want a smaller published artifact surface or a different artifact publishing strategy

### Monthly Review Frontend Progress

- Replaced the prior demo view in `frontend/Example_frontendV1` with a monthly review viewer designed around the current output pack.
- Added a bundle generator:
  - `scripts/build_monthly_review_frontend_bundle.py`
- Added the generated frontend data bundle:
  - `frontend/Example_frontendV1/src/data/monthlyReviewBundle.json`
- The React viewer now pulls the monthly review artifacts together in one place for each fund:
  - Change Brief material movers
  - sizing agreement and disagreement lists
  - Challenge Brief items
  - run summary markdown
  - evidence pointer and source hash context

### Current Frontend Decision

- The frontend is currently bundle-driven, not live file-system driven.
- Current flow:
  - run monthly review
  - rebuild the frontend bundle
  - open the React viewer
- Important note:
  - this is the current operating decision
  - it can be changed later if we want the frontend to read the monthly review artifacts more directly or support snapshot switching inside the app

### What We Need To Think About Next For The Frontend

1. Decide whether the viewer should stay focused on the tracked monthly review snapshot bundle or support multiple snapshots directly.
2. Decide whether the React app should stay review-only or later support memory approvals / reviewer actions.
3. Decide whether we want the monthly review bundle regenerated manually with a script or automatically as part of the monthly review run.

---

## 2026-05-30 — Tier 0 correctness fixes + Tier 1 robustness

Worked from `docs/CODEBASE_AUDIT_2026-05-29.md` and `docs/AGENT_BUILD_PLAN_V1.md`. Scope agreed up front: Phase 0 (correct numbers + installable package) through Tier 1 robustness. The deterministic parsing/plumbing was the focus; the LLM agent (Tier 3) was explicitly not started this session.

### Baseline and packaging (Stage 1)

- Froze the pre-change IC-facing outputs in `tests/baseline_2026-05-30/` (summary markdown, fund rolled-exposure summary, coverage) before touching any code.
- Confirmed the headline bugs reproduce from source: US Equity summed exposure 199.14%, bond funds with empty benchmark coverage.
- Found a reproducibility issue worth noting: the committed `fund_weights_vir_algo_summary.md` did not regenerate from the committed intermediate CSV (different VIR/algo match counts), i.e. the committed artifacts had drifted from their own inputs. The rolled-exposures layer, however, is fully reproducible from the workbook (matches to float ULP + timestamp).
- Made the package installable: added `[build-system]` (hatchling), `dependencies = []` (core stays stdlib-only), `agent` extra (`anthropic`, `pydantic>=2`) and `dev` extra (`pytest`). `pip install -e .` now works.
- Stood up `tests/` (none existed). 31 tests by end of session.

### Tier 0 — IC-facing correctness

- **C3 (root cause of three findings).** `rolled_exposures._account_rows` hardcoded `range(5, 83)`, truncating the account block at row 82 and silently dropping rows 83–88 — which are exactly the bond benchmark indices (Bloomberg US Agg / US Corp / US Corp HY, JPM EMBI / GBI-EM). Replaced with dynamic detection (read to first blank `secid`) plus a hard assertion that the block reaches at least row 83. Fixing this alone:
  - restored benchmark coverage for Total Return / Defensive / Multisector Bond (0.00 → ~100), which removed the phantom 100% "active" bets (the C2 symptom), and
  - eliminated all unmatched lookthrough rows (the H1 symptom): 84 accounts now match all 32,221 lookthrough rows, 0 dropped.
- **C2.** In `_fund_summary_rows`, compute a fund-level `benchmark_coverage_ok` flag; when a fund has no benchmark coverage at all, `active_rolled_exposure` is set to null instead of `target − 0`. Deliberately fund-level: a single ACID with a zero benchmark weight inside a benchmarked fund is a real active bet and is preserved. Only MStar Alternatives now legitimately has no benchmark, and it is flagged. The flag is threaded through `rolled_exposure_alignment_multisignal` and explicitly honored in `challenge_triggers` (sign-disagreement no longer fires against a non-existent benchmark — Alternatives returns 0 candidates).
- **C1.** `fund_weights_summary` summed `fund_target_rolled_exposure` across all `acid_type`s; country and region-sector are alternate taxonomies over the same securities, so the total double-counted (~199%). Now broken out per `acid_type`, deduped by `acid` (so per-perspective rows in the multisignal CSV can't inflate it either). US Equity now reads country 99.17 + bond 0.83 = 100%, region-sector 99.14% — no 199% anywhere.
- **H1.** Unmatched lookthrough rows are now counted and a warning is emitted (escalated above a 1% threshold) instead of silent `continue`. Currently fires on nothing after C3.
- **watch_items_count typo.** `render_monthly_review_report.py` read `watch_item_count`; emitter writes `watch_items_count`. One-character fix.

### Tier 1 — robustness

- **H4.** `workbook_xml._cell_value` now treats error cells (`t="e"`: `#REF!`, `#DIV/0!`, `#N/A`, …) as missing, so the error literal can no longer leak into a numeric parse or a string field.
- **H3.** New `parse_utils.safe_float`: blanks and non-numeric text (`"NA"`, `"#N/A"`, stray text) become `None` with a warning rather than aborting the whole monthly parse on a single bad cell. Routed through the four workbook-parse paths (`rolled_exposures`, `equity_history`, `alignment` `_to_float`; `algo_parser` inline coercion, with row/col context in the warning).
- **H2.** `challenge_triggers._dedupe_trigger_rows` fallback was `group_rows[0]` (CSV-row-order dependent). Now picks deterministically by a stable key (perspective name, then row_id) when no `local_real` perspective exists.
- **M2.** Deprecated the single-signal path: `DeprecationWarning` on `build_fund_weights_vir_algo`, `build_fund_exposure_alignment`, `build_account_exposure_alignment`; repointed `build_fund_weights_summary` default input to the multisignal CSV; removed the three now-stale single-signal artifacts (`fund_weights_vir_algo.csv`, `account_vir_algo_alignment.csv`, `fund_vir_algo_alignment.csv`). Canonical path is multisignal.
- **Dated-filename default.** `build_fund_weights_vir_algo_multisignal` no longer defaults to a hardcoded dated workbook; it globs the newest `data/RMv2_*.xlsm` (filenames embed an ISO date, so lexical max = newest). Prevents silently re-parsing last month's file.
- **utcnow().** Replaced the deprecated naive `datetime.utcnow() + "Z"` at three sites with `datetime.now(timezone.utc)…replace("+00:00","Z")` (format-preserving), matching the bundle builder.

### Verification and artifact promotion

- Ran the full chain from source (`vir_history.xlsx` → `equity_vir_history.csv`; `RMv2_*.xlsm` + `Algo LR.xlsx` → rolled exposures + multisignal CSV → summary). Before/after deltas vs the frozen baseline are exactly the intended ones: `+4` recovered account-block rows, one new `benchmark_coverage_ok` column, bond benchmark totals 0 → ~100, Alternatives null-active; equity per-row data byte-identical (C1 was a presentation bug, not a data bug).
- Promoted the corrected artifacts into `artifacts/rolled_exposures/` (8 canonical files). Left `equity_vir_history.csv.zip` untouched — the rebuilt VIR matched the committed zip line-for-line (326,831 rows) and the unzipped CSV is gitignored.
- Re-ran the rolled layer with all Tier 1 parse changes in place: clean (no warnings, no crash, deprecation gone) and byte-identical to the promoted numbers. The robustness changes are inert on good data and only engage on malformed input.

### Tests added (`tests/`)

- `test_row_ids.py` — determinism / field-sensitivity / prefix isolation of the row-id backbone.
- `test_rolled_exposures.py` — C3 block detection (row 83+ recovered, stop-at-blank, truncation raises) and C2 fund-level null-active vs preserved-active.
- `test_fund_summary.py` — C1 per-type summation, dedupe-by-acid, no double-counted total in the markdown.
- `test_challenge_triggers.py` — C2 coverage honoring (explicit flag + fallback); H2 dedupe determinism.
- `test_parse_robustness.py` — H3 tolerant coercion; H4 error-cell handling.

### Not done this session (next candidates)

- **Tier 2 maintainability:** consolidate the remaining `_to_float` duplication (9 copies) behind the shared helper; merge the duplicated single/multisignal modules; reuse `XlsxWorkbook` in `rolled_exposures`; centralize `ARTIFACTS_ROOT`.
- **Tier 3 — the actual agent (`AGENT_BUILD_PLAN_V1` Phases 1–5):** read tools + ACID mapping wiring → governance config + memory write path → citation enforcer + write tools → the LLM loop → orchestrator. The build plan's Phase-0 prerequisite (correct numbers + installable package) is now satisfied.

Note: this repo is not a git checkout on this machine; nothing above is committed. All changes are in the working tree only.

---

## 2026-06-01 — ZIP VIR fallback + exception suppression governance

Reviewed the updated codebase from `Updated Code/session_log.md` forward, then patched the two highest-risk handoff issues from the review.

### Changes made

- Added `csv_sources.py` as the shared CSV source resolver:
  - reads the raw CSV when present locally
  - falls back to the tracked `<csv>.zip` mirror when the raw CSV is absent
  - selects the ZIP member that matches the requested CSV name, or the only CSV in the archive
- Routed normalized VIR history readers through the shared fallback:
  - `alignment.load_vir_rows_from_csv`
  - `challenge_triggers._vir_quartile_lookup`
  - `challenge_triggers._vir_decomposition_lookup`
- Updated source-file hashing in monthly review / challenge-trigger metadata to hash the actual source used:
  - raw `artifacts/equity_vir_history.csv` if present
  - otherwise `artifacts/equity_vir_history.csv.zip`
- Tightened challenge suppression governance:
  - proposed memory exceptions remain visible in memory recall
  - only `approved` and `applied` exceptions can suppress fired trigger candidates
- Updated collaborator-facing docs:
  - README now marks the multisignal fund/VIR/algo path as canonical
  - README documents the ZIP mirror fallback
  - multisignal CLI help now calls out ZIP fallback behavior

### Tests / verification

- Added `tests/test_csv_sources.py` for ZIP mirror fallback.
- Extended `tests/test_challenge_triggers.py` to pin that proposed exceptions do not suppress triggers.
- Verified Python AST parsing without bytecode writes: 44 Python files parse successfully.
- Verified the ZIP fallback path directly with a temporary `equity_vir_history.csv.zip`.
- Verified exception suppression directly: proposed exceptions are ignored; approved exceptions suppress.
- Full `pytest` still could not run in this environment because `pytest` is not installed.

### Git status

- The shell cannot find `git` on PATH, and this `Updated Code` folder still does not appear to contain a local `.git` checkout. Code changes are present in the working folder but were not committed from this environment.

---

## 2026-06-01 — Agent Build Plan Phase 1 read tools

Implemented the next build step from `docs/AGENT_BUILD_PLAN_V1.md`: make ACID mapping live in the agent read-tool layer and expose the missing deterministic read tools.

### Changes made

- Added `acid_mapping.py`:
  - loads `data/acid_mapping_bootstrap_v1.csv`
  - indexes mappings by ACID
  - exposes peer discovery through `comparison_group`, `relative_value_group`, and `parent_family`
  - provides mapping enrichment fields for tool outputs
- Updated `get_fund_snapshot`:
  - enriches each ACID row with `mapping_*` fields
  - emits `mapping_status`
  - includes the mapping file in source hashes
- Added read tools in `agent_tools.py`:
  - `get_acid_history`
  - `get_exposure_lineage`
  - `get_peer_context`
- Tightened memory recall authority:
  - authoritative prior context now returns only `approved` / `applied` rows
  - proposed rows are still counted in `summary.proposed_count`
  - summary now records `authority_rule = approved_applied_only`
- Moved Trigger 5 into the supported trigger set:
  - `better_expression_available` is no longer deferred
  - deterministic implementation checks mapped investable peers for a material STF advantage
  - fixed income rows still degrade safely where VIR trigger evaluation is not yet supported
- Updated README to document the agent read tools.

### Tests / verification

- Added `tests/test_agent_tools_phase1.py`.
- Extended `tests/test_challenge_triggers.py` with better-expression trigger coverage.
- Verified Python AST parsing without bytecode writes: 46 Python files parse successfully.
- Direct checks passed:
  - `get_fund_snapshot` returns mapping-enriched ACID rows
  - `get_acid_history` returns replay-gated VIR history
  - `get_exposure_lineage` returns largest source contributors first
  - `get_peer_context` returns mapped peer context
  - `recall_memory_store` excludes proposed rows from authoritative context but counts them
  - `evaluate_challenge_triggers` now reports supported triggers: sign disagreement, decomposition rotation, better expression available
- Full `pytest` still could not run in this environment because `pytest` is not installed.

### Current next build step

- Phase 2 from the build plan is next: governance config plus the proposed-only memory write path.
- The major design decision is now locked: proposed memory is visible for review but not authoritative until approved/applied.

---

## 2026-06-01 — Agent Build Plan Phase 2 governance + memory writes

Implemented the deterministic Phase 2 guardrails from `docs/AGENT_BUILD_PLAN_V1.md`.

### Changes made

- Added `config/agent_governance.json`:
  - versioned governance events with `effective_from`
  - threshold parameters externalized from trigger code
  - `auto_apply_memory_ops = false`
- Added `governance.py`:
  - `load_governance(as_of_date)` selects the latest effective governance event
  - exposes typed parameter accessors and source hashes
- Wired `challenge_triggers.py` to governance:
  - materiality thresholds now come from governance
  - decomposition weakening threshold now comes from governance
  - peer advantage threshold now comes from governance
  - trigger summary includes `governance_version`
- Updated `monthly_review.py`:
  - run metadata now uses the loaded governance version instead of a hardcoded string
  - governance file is included in source hashes
- Added `memory_ops.py`:
  - validates and appends proposed-only memory operations
  - rejects `auto_apply_memory_ops=true`
  - rejects conflicting ops in one call
  - supports thesis, challenge, watch-item, and exception operation families
  - writes atomically via temp-file replace
- Updated `memory_store.py`:
  - append-only memory rows now collapse to latest row per logical ID for recall
  - this lets close/update operations append replacement rows without leaving stale open records active
- Updated README to document governance and memory write modules.

### Tests / verification

- Added `tests/test_governance.py`.
- Added `tests/test_memory_ops.py`.
- Full test suite passed:
  - `44 passed in 0.19s`

### Current next build step

- Phase 3 is next: citation enforcement, output payload schemas, and write tools for Change Brief / Sizing Considerations / Challenge Brief.
- LLM API key still not needed yet. The next phase is still deterministic validation infrastructure.

---

## 2026-06-01 — Agent Build Plan Phase 3 citation enforcement + write tools

Implemented the deterministic write boundary from `docs/AGENT_BUILD_PLAN_V1.md`.

### Changes made

- Added `citations.py`:
  - parses citation tokens
  - resolves `csv:<path>#row_id=<id>`
  - resolves `mem:<table>#<record_id>`
  - resolves `deriv:<formula>?inputs=<refs>`
  - enforces citations on narrative fields before writes are accepted
- Added `schemas.py`:
  - stdlib validators for Change Brief, Sizing Considerations, and Challenge Brief payloads
  - validates required headers and artifact sections
  - rejects prescriptive sizing language
  - validates Challenge Brief trigger references when fired trigger IDs are supplied
- Added `write_tools.py`:
  - `write_change_brief`
  - `write_sizing_considerations`
  - `write_challenge_brief`
  - `update_memory` wrapper around `memory_ops.apply_ops`
  - persists JSON and Markdown only after schema + citation checks pass
- Updated README to document citation enforcement and write tools.

### Tests / verification

- Added `tests/test_citations.py`.
- Added `tests/test_write_tools.py`.
- Full test suite passed:
  - `53 passed in 0.27s`

### Current next build step

- Phase 4 is next: the actual LLM tool-use loop.
- The deterministic read tools, governance, memory writes, citation enforcement, schemas, and write tools now exist.
- This is the point where the Anthropic / Claude API key becomes useful for the first real agent runtime implementation.

---

## 2026-06-01 — Agent Build Plan Phase 4 LLM runtime skeleton

Implemented the first LLM agent runtime layer without making a live API call.

### Changes made

- Added `run_metadata.py`:
  - builds review run metadata
  - stamps parser, mapping, governance, and algo versions
  - captures source hashes
- Added `agent_runtime/`:
  - `llm_client.py`: mockable client protocol, scripted test client, and Anthropic Messages API wrapper
  - `prompts.py`: system prompt and per-fund user prompt
  - `tool_registry.py`: Anthropic-compatible tool definitions plus callable dispatch wrappers
  - `loop.py`: one-fund tool-use loop with tool dispatch, required write enforcement, and trace logging
- Added `scripts/run_agent_review.py`:
  - CLI for real LLM-backed runs
  - expects `ANTHROPIC_API_KEY`
  - supports one fund or the default fund batch
- Updated README with runtime files and the command for a live Claude run.

### Tests / verification

- Added `tests/test_agent_loop.py`.
- Mocked LLM test proves:
  - model `tool_use` blocks are dispatched
  - `tool_result` blocks are returned to the conversation
  - `write_change_brief` is actually called through the registry
  - the loop rejects completion before required writes
  - `agent_trace.json` is written
- Full test suite passed:
  - `55 passed in 0.33s`

### API status

- No live Anthropic API call was made in this phase.
- The runtime is now ready for a first controlled API smoke test once `ANTHROPIC_API_KEY` is set.

### Environment update

- Confirmed local `.env` contains `ANTHROPIC_API_KEY` without printing the secret.
- Added `.env` to `.gitignore`.
- Added lightweight stdlib `.env` loading in `agent_runtime/llm_client.py` so local runs can pick up `ANTHROPIC_API_KEY` automatically.
- Full test suite passed after the update:
  - `56 passed in 0.31s`

### Bedrock direction update

- Direct Anthropic API calls are not allowed in the corporate environment.
- AWS Bedrock is available through the user's AWS environment, region `us-east-1`.
- Target model identified from Bedrock console: `anthropic.claude-sonnet-4-6`.
- Added Bedrock support:
  - optional `bedrock` extra with `boto3`
  - `BedrockClaudeClient` using the AWS Bedrock Converse API
  - provider selection in `scripts/run_agent_review.py`
  - CLI defaults now prefer `--provider bedrock`
  - internal tool-use / tool-result conversion is covered by tests
- `.env` can carry short-term AWS credentials:
  - preferred Bedrock API-key path:
    - `AWS_BEARER_TOKEN_BEDROCK`
    - `AWS_DEFAULT_REGION=us-east-1`
- standard AWS temporary credential fallback:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN`
- Full test suite passed after Bedrock runtime support:
  - `57 passed in 0.30s`

---

## 2026-06-10 — May 2026 data refresh, single-fund review artifact, and frontend redesign checkpoint

This is the current handoff checkpoint for Al. The repo now contains the latest May 2026 data snapshot, a tracked single-fund review artifact, and a non-final frontend redesign tied to the refreshed structured data.

### Data snapshot and source files

- Saved the latest monthly source files under `data/2026-05-31/` as the repo convention for the May 2026 snapshot:
  - `Algo LR (3).xlsx`
  - `RMv2_PCT_Mstar_funds_2026-06-08.xlsm`
  - `202605-Equity Model.xlsx`
  - `202605- Fixed Income Model.csv`
- Per user instruction, the folder keeps the `2026-05-31` snapshot convention even though one source filename carries a `2026-06-08` date. Treat these as the May 2026 source pack.

### Structured exposure refresh

- Rebuilt the rolled exposure artifacts for the latest data pack.
- Updated tracked CSV outputs in `artifacts/rolled_exposures/`, including:
  - `fund_weights_vir_algo_multisignal.csv`
  - `fund_rolled_exposure_detail.csv`
  - `fund_rolled_exposure_summary.csv`
  - account-level rollup outputs
  - `fund_rollthrough_definitions.csv`
- The frontend now consumes refreshed structured rows instead of the earlier stale bundle.

### Monthly review artifact saved to repo

- Added a tracked monthly review artifact for:
  - `artifacts/monthly_review/2026-05-31/mstar-us-equity/`
- Saved files include:
  - `pm_review.md`
  - `pm_review.html`
  - `change_brief.json`
  - `change_brief.md`
  - `agent_trace.json`
- This is currently a single-fund checkpoint, useful both as review output and as frontend content.

### Frontend data bundling changes

- Updated `scripts/build_monthly_review_frontend_bundle.py` so the frontend bundle is rebuilt from tracked repo artifacts.
- The script now regenerates:
  - `frontend/Example_frontendV1/src/data/monthlyReviewBundle.json`
  - `frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json`
  - `frontend/Example_frontendV1/src/data/exposureLineage.json`
- Important behavior:
  - saved PM review content comes from `artifacts/monthly_review/...`
  - structured exposure and lineage views come from `artifacts/rolled_exposures/...`
  - the app surfaces snapshot mismatch when review narrative and structured tables are not from the exact same file date

### Frontend redesign checkpoint

- Refactored the React shell in `frontend/Example_frontendV1/src/App.jsx`.
- Restyled the app in `frontend/Example_frontendV1/src/styles.css` toward the new PM dashboard reference.
- Current navigation / sections:
  - `Overview`
  - `Challenge Brief`
  - `VIR Decomp`
  - `Fund of Funds`
  - `IC Prep`
  - `Agent Memory`
- Added:
  - top shell with fund selector and snapshot chips
  - portfolio view switcher for `New Portfolio`, `Target Portfolio`, and `Benchmark`
  - fund directory derived from real structured exposure data
  - badge counts for challenge / IC-prep tabs
  - IC-prep panel synthesized from top tensions plus saved review text
- The redesign is explicitly **not final UI**. It is a checkpoint aligned to the latest design direction and real data wiring.

### Notes for Al

- The current preview build was verified locally after a successful `vite build`.
- The main repo files to inspect for the latest frontend checkpoint are:
  - `frontend/Example_frontendV1/src/App.jsx`
  - `frontend/Example_frontendV1/src/styles.css`
  - `frontend/Example_frontendV1/src/data/monthlyReviewBundle.json`
  - `frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json`
  - `frontend/Example_frontendV1/src/data/exposureLineage.json`
  - `scripts/build_monthly_review_frontend_bundle.py`
- The branch used for this checkpoint is `codex/non-final-ui-checkpoint`.

---

## 2026-06-11 - Agent2 buildout, Bedrock live run, SharePoint research wiring, and frontend handoff

This is the latest checkpoint for Al. The repo now contains a separate `agent2/` workstream that builds a richer PM review packet, runs a live Bedrock review, pulls in prior internal checklist context, and matches synced SharePoint research decks by ACID.

### What was added

- Created a new isolated `agent2/` folder so the original agent flow stays intact.
- Added Agent2 architecture and operating docs:
  - `agent2/README.md`
  - `agent2/AGENT2_INPUT_REGISTRY_V1.md`
  - `agent2/AGENT2_OUTPUT_SCHEMA_V1.md`
  - `agent2/AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`
  - `agent2/IC_DOC_INGESTION_SPEC_V1.md`
- Added a frontend/data handoff doc for a future UI rebuild:
  - `docs/CLAUDE_FRONTEND_DATA_HANDOFF.md`
- Added a repo-level philosophy copy:
  - `docs/AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`

### Core Agent2 code

- Review packet builder:
  - `agent2/src/agent2/review_packet_builder.py`
- Evidence pack builder:
  - `agent2/src/agent2/evidence_pack_builder.py`
- Prompt assembly:
  - `agent2/src/agent2/review_prompt.py`
- Bedrock execution:
  - `agent2/src/agent2/bedrock_review_runner.py`
- Internal checklist ingestion:
  - `agent2/src/agent2/ic_checklist_ingest.py`
- Internal history retrieval:
  - `agent2/src/agent2/internal_history_retrieval.py`
- SharePoint research matching and slide-text extraction:
  - `agent2/src/agent2/sharepoint_research.py`

### Supporting scripts

- Build structured packet:
  - `agent2/scripts/build_review_packet.py`
- Run live Bedrock review:
  - `agent2/scripts/run_bedrock_review.py`
- Ingest old IC / checklist docs:
  - `agent2/scripts/ingest_ic_checklists.py`
- Query prior internal rationale:
  - `agent2/scripts/query_internal_history.py`

### Internal-history and checklist work

- Old US Equity checklist docs were ingested into structured JSON for retrieval.
- Saved internal-history artifacts under:
  - `agent2/data/internal_history/`
- Purpose of this layer:
  - turn prior monthly PM writeups into structured memory
  - retrieve relevant historical commentary for current exposures
  - let the new review compare "what we hold now" vs "what we said before"

### SharePoint research integration

- Agent2 now scans the synced research folder:
  - `C:\Users\schuri2\MORNINGSTAR INC\MIM Global Research - Final Research (yyyymm-AC-ACID-project title)`
- Matching logic uses ACIDs from the current exposure / position records.
- For matched ACIDs, the agent stores:
  - deck file path
  - deck metadata from the filename
  - compact slide-text summary when extractable from `.pptx`
- This is now wired into:
  - review packet generation
  - evidence pack generation
  - prompt context for Bedrock
- Latest packet check for `MStar US Equity` showed many matched research files, including examples like:
  - `US IT EQ`
  - `US ID EQ`
  - `US FN EQ`
  - `US SML EQ`

### Live Bedrock test

- Ran one live Bedrock review for:
  - `MStar US Equity`
- Output folder:
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/`
- Key artifacts there:
  - `agent2_review_packet.json`
  - `evidence_pack.json`
  - `system_prompt.txt`
  - `user_prompt.txt`
  - `bedrock_raw_response.json`
  - `bedrock_response.txt`
  - `bedrock_review.json`
  - `bedrock_review.md`
  - `run_manifest.json`
- `run_manifest.json` currently shows:
  - model: `us.anthropic.claude-sonnet-4-6`
  - region: `us-east-2`
  - input tokens: `20535`
  - output tokens: `4822`
  - total tokens: `25357`
  - approx cost: `$0.1339`
  - parsed JSON: `true`

### Structured packet / evidence outputs

- Curated packet path:
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet.json`
- Curated evidence path:
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/evidence_pack.json`
- These are the cleanest files to inspect if someone wants to see the assembled data model without digging through the raw Bedrock run folder.

### Runtime fix in the original agent code

- Updated:
  - `src/portfolio_analyst_agent/agent_runtime/llm_client.py`
- Fix made:
  - do not send empty `toolConfig` to Bedrock when `tools=[]`
- Reason:
  - Bedrock Converse was rejecting requests when the runtime included an empty tool block

### Frontend checkpoint

- The frontend was partially rewired to read live Agent2 review data and use a lighter, warmer visual treatment:
  - `frontend/Example_frontendV1/index.html`
  - `frontend/Example_frontendV1/src/App.jsx`
  - `frontend/Example_frontendV1/src/styles.css`
  - `frontend/Example_frontendV1/src/data/agent2/`
- The current UI is not final. It is a checkpoint only.
- The better long-form data/UI handoff for future redesign work is:
  - `docs/CLAUDE_FRONTEND_DATA_HANDOFF.md`

### What Al should open first

- For the overall concept:
  - `agent2/README.md`
  - `docs/AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`
- For the actual packet structure:
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet.json`
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/evidence_pack.json`
- For the live model run:
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/run_manifest.json`
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/bedrock_review.md`
- For SharePoint research logic:
  - `agent2/src/agent2/sharepoint_research.py`
- For history / retrieval logic:
  - `agent2/src/agent2/ic_checklist_ingest.py`
  - `agent2/src/agent2/internal_history_retrieval.py`
- For future frontend rebuild:
  - `docs/CLAUDE_FRONTEND_DATA_HANDOFF.md`

### Current status

- The repo now has:
  - a separate Agent2 framework
  - one successful live Bedrock run
  - tracked structured outputs for one fund
  - SharePoint research matching by ACID
  - a non-final frontend checkpoint wired to the new review data
- The next sensible step after this checkpoint is either:
  - improve the review schema / prompt quality for more funds, or
  - rebuild the frontend against the structured Agent2 packet and evidence model

## 2026-06-12 Follow-up: March/April VIR backfill and stale-review cleanup

### What changed today

- Added the missing 2026 US Equity model months into the repo data chain:
  - `data/2026-03-31/202603-Equity Model.xlsx`
  - `data/2026-04-30/202604-Equity Model.xlsx`
- Updated the VIR refresh pipeline so it no longer relies on only the newest workbook:
  - `scripts/build_fund_weights_vir_algo_multisignal.py`
  - `--vir-workbook` now accepts multiple files
  - when no explicit list is passed, it auto-discovers all `data/*/*Equity Model.xlsx` files and refreshes the history in sorted month order
- Confirmed the parser handles the newer `General Model` workbook layout and continues to merge decomposition fields into:
  - `artifacts/equity_vir_history.csv`
  - implementation lives in `src/portfolio_analyst_agent/equity_history.py`

### Why this matters

- The May 2026 VIR month-over-month changes were previously incomplete because the March and April workbooks were missing from the refresh chain.
- After the fix, the structured artifact and frontend bundle now use the correct May-over-April VIR move.
- Example checked explicitly:
  - `US IT EQ`
  - `2026-03-31`: `-0.027103275954997424`
  - `2026-04-30`: `-0.04396241690279659`
  - `2026-05-31`: `-0.05675254928131926`
  - correct `vir_delta_stf`: `-0.012790132378522667`

### Rebuilt artifacts after the backfill

- Rebuilt rolled exposure alignment with full March-April-May VIR chain.
- Rebuilt frontend data files:
  - `frontend/Example_frontendV1/src/data/monthlyReviewBundle.json`
  - `frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json`
  - `frontend/Example_frontendV1/src/data/signalHistory.json`
- Rebuilt latest structured packet:
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet_2026-06-12.json`
- Copied latest packet into frontend:
  - `frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json`

### Frontend stale-review protection

- `frontend/Example_frontendV1/src/App.jsx`
  - now detects when the structured packet is newer than the last live Bedrock narrative
  - if the narrative is stale, the UI no longer presents the old Bedrock prose as current
  - instead it derives the visible review sections from the current structured packet
- Added helper script:
  - `scripts/build_frontend_agent_review.py`
  - purpose: regenerate `frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-review.json` from the structured packet so the repo itself does not keep obviously stale frontend review text

### Verification notes

- Production build succeeded:
  - `frontend/Example_frontendV1`
  - `npm run build`
- Local data spot checks confirmed:
  - `frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json` carries `US IT EQ` with `vir_snapshot_date=2026-05-31` and `vir_delta_stf=-0.012790132378522667`
  - `frontend/Example_frontendV1/src/data/signalHistory.json` includes March, April, and May 2026 VIR points for `US IT EQ`
  - `frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json` now matches the corrected May 2026 values
- The Codex in-app browser returned a blank root both on the existing Vite dev server and a clean preview server even though:
  - the HTTP endpoints responded normally
  - Vite served transformed modules
  - the production build completed successfully
- Treat that browser blank-state as a local verification-surface issue unless reproduced in a normal browser outside Codex.

### What Al should look at first for this specific fix

- Pipeline / parser:
  - `scripts/build_fund_weights_vir_algo_multisignal.py`
  - `src/portfolio_analyst_agent/equity_history.py`
- Corrected structured outputs:
  - `artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv`
  - `frontend/Example_frontendV1/src/data/signalHistory.json`
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet_2026-06-12.json`
- Frontend stale-review handling:
  - `frontend/Example_frontendV1/src/App.jsx`
  - `scripts/build_frontend_agent_review.py`

## 2026-06-12 Follow-up: Risk-integrated dashboard handoff for Al

### What changed today

- Added the new risk workbook into the repo and agent flow:
  - `data/2026-05-31/weekly_US_EQ_Time Series Risk Report - Sortable_2026-03-31_2026-06-05.xlsx`
- Added a dedicated risk parser:
  - `src/portfolio_analyst_agent/risk_report.py`
- Added tests for the new risk parsing:
  - `tests/test_risk_report.py`
- Updated Agent2 packet/evidence construction so the saved review packet now includes:
  - portfolio risk summary
  - return attribution
  - top style risk drivers
  - top industry risk drivers
  - likely holdings contributors
  - specific risk watchlist
- Agent2 files touched:
  - `agent2/src/agent2/review_packet_builder.py`
  - `agent2/src/agent2/evidence_pack_builder.py`
  - `agent2/src/agent2/review_prompt.py`
- Saved the latest risk-aware live Bedrock run for May 2026:
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live-2026-06-12-riskcontext/`
- Updated tracked review artifacts:
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet.json`
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/agent2_review_packet_2026-06-12.json`
  - `agent2/data/review_packets/2026-05-31/mstar-us-equity/evidence_pack.json`

### Frontend handoff

- Main source files:
  - `frontend/Example_frontendV1/src/App.jsx`
  - `frontend/Example_frontendV1/src/styles.css`
  - `frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-manifest.json`
  - `frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json`
- The dashboard now has a clearer tab split:
  - `Overview`
    - lighter summary / positioning surface
    - active weights vs benchmark
    - VIR vs positioning scatter
    - rank movers
  - `Risk`
    - measured risk snapshot
    - return attribution MTD
    - measured risk sources
    - where risk is coming from
  - `VIR / Algo`
    - selected exposure time series
    - signal comparison
    - position-level risk context
  - `IC Prep`
    - actual agent brief
    - PM questions
    - devil's advocate
    - next actions
    - focused risk lens
- In plain English:
  - `Risk` = the risk workbook numbers and decomposition
  - `IC Prep` = what the agent thinks those numbers mean
  - `VIR / Algo` = how that applies to the selected position

### Where the agent output is shown

- The saved live narrative / packet-backed brief is surfaced in:
  - `frontend/Example_frontendV1/src/App.jsx`
  - tab: `IC Prep`
- The key rendered sections are:
  - `Agent brief`
  - `Focused call`
  - `Focused risk lens`
  - `Questions for PM`
  - `Devil's advocate`
  - `Next actions`
  - `Current positioning`
  - `What the agent is flagging`

### Access / run instructions for Al

- Local frontend source to edit:
  - `frontend/Example_frontendV1/src/`
- Run locally:
  - `cd frontend/Example_frontendV1`
  - `npm install`
  - `npm run preview -- --host 127.0.0.1 --port 4177`
- Then open:
  - `http://127.0.0.1:4177`

### Temporary quick-share package

- For a fast static upload to Netlify / drag-and-drop hosting:
  - `frontend/Example_frontendV1/netlify-quickshare/`
- This is a generated static bundle for quick sharing, not the long-term editable source of truth.
- If Al wants to make changes, he should edit:
  - `frontend/Example_frontendV1/src/App.jsx`
  - `frontend/Example_frontendV1/src/styles.css`
  - then rebuild from source rather than editing `netlify-quickshare`.

### Notes for Al

- The UI is still not final.
- The current branch is a checkpoint branch, not a final merge-ready UI branch.
- The most important code/data to inspect first:
  - `src/portfolio_analyst_agent/risk_report.py`
  - `agent2/src/agent2/review_packet_builder.py`
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live-2026-06-12-riskcontext/run_manifest.json`
  - `frontend/Example_frontendV1/src/App.jsx`

## 2026-06-15 Follow-up: PM challenge card updates merged to main

- Al opened draft PR `#1` (`Add PM challenge card contract`).
- On June 15, 2026, that work was merged into local `main` and pushed to `origin/main`.
- The PR adds:
  - `docs/PM_CHALLENGE_CARD_CONTRACT_V1.md`
  - richer PM-facing challenge fields in `src/portfolio_analyst_agent/agent_runtime/prompts.py`
  - schema support in `src/portfolio_analyst_agent/schemas.py`
  - rendering / validation support in `src/portfolio_analyst_agent/write_tools.py`
- Practical impact:
  - `Challenge Brief` output can now carry more decision-useful PM fields such as thesis pressure, positioning tension, model signal tension, decision fork, primary PM question, and next evidence needed.
- Current default branch:
  - `main`
# 2026-06-15 - Agent2 Canonical Path Reset

- `agent2` was switched to a single canonical methodology: the deep PM challenge memo path.
- The old compact / challenge-card branching was removed from `agent2` code paths.
- Default `agent2` behavior is now:
  - deep memo review shape
  - 4 challenge briefs
  - deep evidence pack with exact holdings, VIR / algo / decomp, risk, research, market context, bull / bear, devil's advocate, and PM decision fork
- Canonical successful Bedrock run path:
  - `agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live-2026-06-15-deepmemo-12k-top4/`
- Main code files updated:
  - `agent2/src/agent2/review_prompt.py`
  - `agent2/src/agent2/evidence_pack_builder.py`
  - `agent2/src/agent2/bedrock_review_runner.py`
  - `agent2/scripts/run_bedrock_review.py`
  - `agent2/README.md`
  - `agent2/AGENT2_OUTPUT_SCHEMA_V1.md`
- The old `agent` folder / legacy runtime was left unchanged.
- Some historical `agent2/data/bedrock_runs/...` prototype folders could not be deleted because Windows / OneDrive returned access denied on those artifacts, but they are no longer part of the active code path.

# 2026-06-15 - Agent2 Dual Output Restore

- Restored both `agent2` output surfaces on top of the same shared evidence path:
  - `deep_challenge_memo`
  - `challenge_cards`
- Kept `deep_challenge_memo` as the default run mode.
- This means `agent2` no longer reverts to the old prototype methodology, but it does preserve the earlier compact presentation surface the user wanted to keep.

# 2026-06-15 - Agent2 Frontend Data Contract Cleanup

- Added a new canonical frontend mapping document:
  - `docs/AGENT2_FRONTEND_DATA_CONTRACT_V2.md`
- Purpose:
  - tell the next UI builder exactly which JSON file is authoritative for each surface
  - define join order across `manifest`, `review`, `packet`, and `evidence`
  - clarify that `evidence.json` is the preferred dashboard surface
  - clarify that `packet.json` is the canonical structured fact model
  - clarify that `review.json` is narrative-only and should not be used as numeric source of truth
- Important current schema gap called out in the doc:
  - `review.challenge_brief[]` does not yet carry stable `challenge_id` / `acid`, so deep-memo joins currently require normalized-label fallback
- Also updated:
  - `docs/CLAUDE_FRONTEND_DATA_HANDOFF.md`
    - now points to the new contract as the canonical `agent2` frontend reference

# 2026-06-15 - Canonical Consolidated Equity VIR Dataset

- Added a canonical consolidated equity VIR dataset path:
  - `artifacts/vir/equity_vir_dataset.csv`
  - `artifacts/vir/equity_vir_dataset.csv.zip`
- Dataset construction rule is now explicit:
  - use legacy/base VIR history through `2026-02-28`
  - append monthly Equity Model workbook data for March 2026 onward
- Added:
  - `scripts/build_equity_vir_dataset.py`
  - `docs/VIR_DATASET_WORKFLOW.md`
- Updated backend defaults so repo consumers read the canonical dataset path instead of the legacy base-history path, including:
  - monthly review runtime
  - challenge trigger runtime
  - agent2 review packet builder
  - frontend signal-history build path
  - multisignal rolled exposure build path
- Rebuilt and verified the consolidated dataset:
  - latest snapshot date now reaches `2026-05-31`
  - downstream `fund_weights_vir_algo_multisignal.csv` rows for US Equity now show `vir_snapshot_date=2026-05-31`

# 2026-06-15 - Frontend Reference Reset And Navigation Notes

- Reworked `frontend/Example_frontendV1/src/App.jsx` and `frontend/Example_frontendV1/src/styles.css` toward the editorial PM dashboard reference layout the user provided.
- The current frontend uses the saved `agent2` data copies under:
  - `frontend/Example_frontendV1/src/data/agent2/`
    - `mstar-us-equity-manifest.json`
    - `mstar-us-equity-review.json`
    - `mstar-us-equity-packet.json`
    - `mstar-us-equity-evidence.json`
- Important navigation guidance for Al / the next UI pass:
  - start with `docs/AGENT2_FRONTEND_DATA_CONTRACT_V2.md`
  - then read `docs/CLAUDE_FRONTEND_DATA_HANDOFF.md`
  - then inspect `frontend/Example_frontendV1/src/App.jsx`
  - treat `evidence.json` as the preferred dashboard-facing surface
  - treat `packet.json` as the structured numeric/source-of-truth layer
  - do not use `review.json` as the numeric source of truth; it is narrative-first
- Fixed a runtime crash in the Risk tab where holding objects were being rendered directly instead of mapping to `security_name`.
- Verified the local preview after the fix by clicking through:
  - Overview
  - Challenge Cards
  - Deep Memo
  - Risk
  - Holdings
  - Research
  - Run Detail
