# Agent2 Frontend Data Contract v2

Last updated: 2026-07-21

## Purpose

This is the clean frontend handoff for `agent2`.

It is written for whoever rebuilds the dashboard next so they do not have to reverse-engineer:

- which JSON file is canonical for which purpose
- how `packet`, `evidence`, `review`, and `manifest` relate to each other
- which fields are safe for numeric UI
- which fields are narrative-only
- how to join challenge rows to holdings, risk, and research without fuzzy guessing

This document is intentionally practical.

---

## 1. Recommended frontend source files

The only production frontend is `frontend/web`, as configured by the repository-root
`netlify.toml`. Its fund registry is:

- `frontend/web/src/data/funds/index.js`

Each supported fund has one directory containing `manifest.json`, `review.json`,
`packet.json`, `evidence.json`, and `factorRisk.json`:

- `frontend/web/src/data/funds/us-equity/`
- `frontend/web/src/data/funds/international-equity/`
- `frontend/web/src/data/funds/goe/`

Shared signal history is stored at:

- `frontend/web/src/data/signalHistory.json`

For UI work, use these production copies. Do not create a parallel frontend.

---

## 2. What each file is for

### A. `manifest.json`

Use this for:

- run metadata
- model used
- token usage
- approximate cost
- artifact paths
- validation state

Do not use this for:

- holdings
- risk
- positioning
- PM narrative

Top-level fields:

- `fund`
- `logical_snapshot_date`
- `review_date`
- `model`
- `output_style`
- `challenge_count_target`
- `region_name`
- `generated_at`
- `artifacts`
- `usage`
- `approx_cost_usd`
- `parsed_json_ok`
- `validation_error`

### B. `review.json`

Use this for:

- top-level narrative shown to humans
- executive summary
- key insights
- deep challenge memo text
- PM questions
- follow-up actions
- dashboard highlights

Do not use this for:

- numeric source of truth
- holdings drilldown
- risk tables
- exact signal values

Top-level fields:

- `executive_summary`
- `key_insights`
- `challenge_brief`
- `pm_questions`
- `follow_up`
- `dashboard_highlights`

Important:

`review.json` is display-oriented narrative.
It is not the right place to source the exact numbers for UI components.

### C. `packet.json`

This is the canonical structured fact model.

Use this for:

- normalized position rows
- normalized challenge rows
- normalized risk context
- normalized signal summary
- normalized decomposition
- source-aware evidence metadata

Top-level fields:

- `header`
- `fund_snapshot`
- `material_positions`
- `risk_context`
- `signal_summary`
- `top_movers`
- `decomposition_summary`
- `challenge_book`
- `pm_questions`
- `portfolio_implications`
- `roadmap`
- `sharepoint_research_summary`
- `data_quality_flags`
- `source_index`
- `run_metadata`

If a frontend engineer wants one file to understand the whole model, this is the one.

### D. `evidence.json`

This is the best frontend-ready file.

Use this for:

- challenge queue
- challenge cards
- selected challenge drilldown
- exact holdings causing a challenge
- exact VIR / algo / decomp explanation
- exact risk contribution
- SharePoint research focus
- market context excerpts

Top-level fields:

- `header`
- `run_goal`
- `fund_shape`
- `top_challenges`
- `challenge_market_context`
- `challenge_support_packets`
- `supporting_positions`
- `risk_and_attribution`
- `sharepoint_research_focus`
- `internal_history_focus`
- `source_drilldowns`
- `data_quality_flags`
- `cost_guardrails`

Practical rule:

- `packet.json` = canonical structured model
- `evidence.json` = easiest dashboard data surface
- `review.json` = human narrative layer
- `manifest.json` = run metadata layer

---

## 3. Canonical join keys

## Primary keys

Use these in this order:

1. `challenge_id`
2. `acid`
3. `fund_slug`
4. normalized `label` only as fallback

## Key meanings

### `challenge_id`

Best key for challenge surfaces.

Exists in:

- `evidence.top_challenges[]`
- `evidence.challenge_support_packets[]`
- `packet.challenge_book[]`

Use this whenever building:

- challenge list
- selected challenge state
- compact card to drilldown linkage

### `acid`

Best key for position / exposure / research / holdings mapping.

Exists in:

- `packet.material_positions[]`
- `packet.challenge_book[]`
- `evidence.top_challenges[]`
- `evidence.challenge_support_packets[]`
- `evidence.sharepoint_research_focus[]`
- `evidence.source_drilldowns[]`

Use this whenever building:

- exposure-level views
- holdings drilldown
- research lookup
- risk mapping to exposure

### `fund_slug`

Best key for selecting the fund run.

Exists in:

- `packet.header.fund_slug`
- `evidence.header.fund_slug`

### normalized `label`

Use only when forced to join the Bedrock deep narrative back to structured rows.

Current reason:

`review.challenge_brief[]` currently contains `label`, but not a stable `acid` or `challenge_id`.

That means:

- compact challenge rows should be selected from `evidence.top_challenges[]`
- deep memo rows should be linked back to compact rows by normalized `label`

This is a temporary compromise, not ideal schema design.

---

## 4. Current join strategy by surface

## A. Challenge queue

Use:

- `evidence.top_challenges[]`

Why:

- already ranked
- has `challenge_id`
- has `acid`
- has short UI-friendly fields

Primary fields:

- `challenge_id`
- `acid`
- `label`
- `category`
- `priority`
- `challenge_score`
- `challenge_type`
- `challenge_headline`
- `primary_pm_question`
- `pm_decision_fork`
- `source_quality`
- `research_status`
- `top_holding_lineage`

## B. Selected challenge drilldown

Start from:

- selected `challenge_id`

Then join to:

- `evidence.challenge_support_packets[]` on `challenge_id`

Use that for:

- `exact_holdings_causing_it`
- `exact_vir_algo_decomp_explanation`
- `exact_risk_contribution`
- `exact_internal_research_excerpt`
- `exact_external_market_context`

This is the canonical drilldown surface.

## C. Deep memo view

Start from:

- selected compact challenge row in `evidence.top_challenges[]`

Then match to:

- `review.challenge_brief[]`

Join rule:

- normalize compact `label`
- normalize deep memo `label`
- match those

Because the deep memo currently does not carry `acid` or `challenge_id`, this join should be isolated in one mapping helper, not repeated ad hoc in components.

## D. Fund-level dashboard highlights

Use:

- `review.dashboard_highlights[]`
- `review.key_insights[]`
- `review.follow_up[]`
- `packet.fund_snapshot`
- `evidence.fund_shape`

Use review fields for text and packet/evidence fields for numbers.

## E. Holdings drilldown

Preferred source:

- `evidence.challenge_support_packets[].exact_holdings_causing_it`

Fallback source:

- `packet.material_positions[].source_breakdown.securities`

The frontend should not recompute these if the evidence packet already contains them.

## F. Risk monitor

Preferred source:

- `evidence.risk_and_attribution`

Fallback source:

- `packet.risk_context`

Why prefer `evidence`:

- the names are already shaped for presentation
- challenge-linked fields are easier to consume

## G. Research / SharePoint view

Use:

- `evidence.sharepoint_research_focus[]`
- `packet.material_positions[].sharepoint_research`
- `evidence.challenge_support_packets[].exact_internal_research_excerpt`

## H. Run / audit view

Use:

- `manifest.json`
- `packet.source_index[]`
- `packet.run_metadata`
- `packet.data_quality_flags[]`

---

## 5. Field map by UI need

## A. Metric strip at top of dashboard

Recommended source fields:

- active risk:
  - `evidence.risk_and_attribution.summary.active_predicted_risk_pct`
- active share:
  - `evidence.risk_and_attribution.summary.active_share_pct`
- active return:
  - `evidence.risk_and_attribution.return_attribution_mtd.active_period_return`
- top style driver:
  - `evidence.risk_and_attribution.top_style_risk_drivers[0].label`
- top industry driver:
  - `evidence.risk_and_attribution.top_industry_risk_drivers[0].label`

## B. Selected exposure signal block

Recommended source:

- `evidence.challenge_support_packets[].exact_vir_algo_decomp_explanation`

Fields:

- `active_weight`
- `portfolio_weight`
- `benchmark_weight`
- `positioning_direction`
- `vir_now`
- `vir_delta_mom`
- `vir_direction`
- `algo_active_weight`
- `algo_active_weight_mom`
- `algo_direction`
- `signal_alignment`
- `decomposition_driver`
- `decomposition_assessment`
- `decomposition_values`

## C. Compact challenge card

Recommended source:

- `evidence.top_challenges[]`

Fields:

- `challenge_headline`
- `thesis_under_pressure`
- `positioning_tension`
- `model_signal_tension`
- `vir_decomposition_readthrough`
- `market_context_readthrough`
- `measured_risk_readthrough`
- `return_attribution_readthrough`
- `pm_decision_fork`
- `primary_pm_question`
- `evidence_needed_next`
- `source_quality`

## D. Deep challenge memo card

Recommended source:

- `review.challenge_brief[]`

Fields:

- `challenge_headline`
- `thesis_under_pressure`
- `positioning_tension`
- `model_signal_tension`
- `vir_decomposition_readthrough`
- `market_context_readthrough`
- `measured_risk_readthrough`
- `exact_holdings_causing_it`
- `exact_vir_algo_decomp_explanation`
- `exact_risk_contribution`
- `exact_internal_research_excerpt`
- `exact_external_market_context`
- `bull_case`
- `bear_case`
- `devils_advocate`
- `what_would_change_my_mind`
- `pm_decision_fork`
- `primary_pm_question`
- `evidence_needed_next`
- `confidence`
- `source_quality`

Important:

Some of those fields are duplicated in richer structured form inside `evidence.challenge_support_packets[]`.
When building tables, use the structured evidence version.
When building prose blocks, use the deep memo version.

## E. Security-level drilldown

Recommended source:

- `evidence.challenge_support_packets[].exact_holdings_causing_it[]`

Fields per holding:

- `security_name`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`
- `sources[]`

Fields per source:

- `source_name`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`

Frontend rendering rule:

Aggregate by security first.
Then display the sleeve/source breakdown under the security.

Do not flatten these back into duplicated exposure rows.

## F. Risk contribution table

Recommended source:

- `evidence.risk_and_attribution`

Key sections:

- `summary`
- `top_style_risk_drivers`
- `top_industry_risk_drivers`
- `return_attribution_mtd`
- `likely_holdings_contributors`
- `specific_risk_watchlist`
- `narrative_observations`

## G. SharePoint research panel

Recommended source:

- `evidence.sharepoint_research_focus[]`

Fields:

- `acid`
- `label`
- `category`
- `research_path`
- `research_summary`

## H. Raw position table

Recommended source:

- `packet.material_positions[]`

Use when a frontend needs a sortable exposure grid.

Important fields:

- `position_id`
- `acid`
- `category`
- `label`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`
- `vir_now`
- `vir_delta_mom`
- `algo_active_weight`
- `algo_active_weight_mom`
- `signal_alignment`
- `signal_quality`
- `decomposition_assessment`
- `decomposition_driver`
- `importance_score`
- `positioning_direction`
- `vir_direction`
- `algo_direction`
- `source_security_count`
- `sample_source_securities`
- `vir_join_status`
- `algo_join_status`

---

## 6. Canonical source preference order

If two files both appear to contain the same idea, use this order.

## A. Exact numbers

1. `packet.json`
2. `evidence.json`
3. `review.json`

## B. Challenge ranking and challenge selection

1. `evidence.top_challenges[]`
2. `packet.challenge_book[]`
3. `review.challenge_brief[]`

## C. Holdings drilldown

1. `evidence.challenge_support_packets[].exact_holdings_causing_it`
2. `packet.material_positions[].source_breakdown.securities`

## D. Risk attribution

1. `evidence.risk_and_attribution`
2. `packet.risk_context`

## E. Narrative text

1. `review.json`
2. `packet.challenge_book[]`
3. `evidence.top_challenges[]`

---

## 7. Known schema gaps

These are the current rough edges a frontend builder should know up front.

## Gap 1: deep review rows do not carry stable join keys

Current issue:

- `review.challenge_brief[]` has `label`
- it does not reliably carry `challenge_id`
- it does not reliably carry `acid`

Impact:

- deep memo join requires normalized label matching

Recommended future fix:

Add these fields to every `review.challenge_brief[]` item:

- `challenge_id`
- `acid`
- `fund_slug`

## Gap 2: `review.json` should not be treated as a numeric source

The same concept may appear in prose there, but the numeric truth belongs in `packet` or `evidence`.

## Gap 3: some research matching metadata is richer in `packet.material_positions[]`

If the frontend needs:

- match confidence
- primary vs secondary match
- extracted slide text

it should read:

- `packet.material_positions[].sharepoint_research`

not just:

- `evidence.sharepoint_research_focus[]`

## Gap 4: packet and evidence overlap by design

That overlap is intentional:

- `packet` is the structured analytical superset
- `evidence` is the frontend-oriented subset around top challenges

Do not try to deduplicate those files in the UI layer.

---

## 8. Recommended frontend helper layer

Any rebuild should create one small normalization layer before rendering.

Recommended selectors / helpers:

1. `getRunManifest(fundSlug)`
2. `getReviewNarrative(fundSlug)`
3. `getPacket(fundSlug)`
4. `getEvidence(fundSlug)`
5. `getChallengeQueue(fundSlug)` from `evidence.top_challenges`
6. `getChallengeSupportById(fundSlug, challengeId)` from `evidence.challenge_support_packets`
7. `getDeepMemoByChallengeId(fundSlug, challengeId)` using label normalization bridge
8. `getMaterialPositionByAcid(fundSlug, acid)` from `packet.material_positions`
9. `getResearchByAcid(fundSlug, acid)` from `evidence.sharepoint_research_focus`

The important thing is that the label-normalization hack should live in one place only.

---

## 9. Minimum UI mapping that should work immediately

If someone wants the shortest path to a good dashboard, this is the safe build:

### Dashboard tab

- KPI strip from `evidence.risk_and_attribution.summary`
- challenge queue from `evidence.top_challenges`
- selected challenge monitor from `evidence.top_challenges + challenge_support_packets`
- security drilldown from `challenge_support_packets.exact_holdings_causing_it`
- research summary from `evidence.sharepoint_research_focus`
- market context from `challenge_support_packets.exact_external_market_context`

### Risk tab

- all from `evidence.risk_and_attribution`

### Holdings tab

- exposure grid from `packet.material_positions`
- challenge-linked security drilldown from `challenge_support_packets`

### Research tab

- SharePoint list from `evidence.sharepoint_research_focus`
- PM questions from `review.pm_questions`
- deeper internal/external excerpt blocks from `review.challenge_brief` plus `challenge_support_packets`

### Run tab

- `manifest.json`
- `packet.run_metadata`
- `packet.data_quality_flags`

---

## 10. Summary

For the next frontend builder:

- use `evidence.json` first for dashboard screens
- use `packet.json` for exact structured facts and sortable tables
- use `review.json` for human-readable memo text only
- use `manifest.json` for run metadata only
- use `challenge_id` first, `acid` second, normalized `label` only as fallback
- do not rebuild holdings drilldown from scratch if `challenge_support_packets` already contains it

If this contract is followed, the next UI build should not need to guess.
