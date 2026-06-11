# Frontend Data Handoff for Claude

This document explains the current data structure, where each file lives, how the files relate to each other, what keys are important, and how a new frontend should consume them.

This is meant for rebuilding the PM / portfolio dashboard cleanly from the data, without inheriting the current UI decisions.

## 1. Big Picture

There are **four main data layers** feeding the frontend:

1. `monthlyReviewBundle.json`
   - legacy structured review bundle
   - one object per fund
   - contains markdown review text, artifact paths, and some run metadata

2. `fundWeightsVirAlgo.json`
   - the main **exposure table**
   - one row per `(fund, acid)`
   - this is the core table for active weights, benchmark weights, VIR values, algo values, and join status

3. `exposureLineage.json`
   - the **look-through / drilldown table**
   - keyed by `fund`, then `acid`
   - explains which underlying securities and sleeves create each exposure

4. `agent2` artifacts
   - the new Bedrock-backed review layer
   - includes:
     - `manifest` = metadata, cost, token usage, artifact paths
     - `review` = human-readable structured output from the model
     - `packet` = structured pre-LLM evidence payload that is the best source for UI data

## 2. Canonical File Locations

### Frontend-facing static copies

These are the files currently copied into the frontend app:

- [frontend/Example_frontendV1/src/data/monthlyReviewBundle.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/monthlyReviewBundle.json)
- [frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/fundWeightsVirAlgo.json)
- [frontend/Example_frontendV1/src/data/exposureLineage.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/exposureLineage.json)
- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-manifest.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-manifest.json)
- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-review.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-review.json)
- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json)

### Canonical `agent2` originals

These are the originals produced by the new agent pipeline:

- [agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/run_manifest.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/run_manifest.json)
- [agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/bedrock_review.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/bedrock_review.json)
- [agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/agent2_review_packet.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/agent2_review_packet.json)
- [agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/evidence_pack.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/data/bedrock_runs/2026-05-31/mstar-us-equity-live/evidence_pack.json)

## 3. The Primary Join Keys

This is the most important thing to understand.

### Main joins

The main frontend joins are:

- `fund`
- `acid`

For most UI work:

- use `fund` to select the fund-level subset
- use `acid` to join:
  - exposure row
  - look-through lineage row
  - signal row
  - agent2 material position row (when possible)

### Important note on labels vs ACIDs

The `agent2` review packet often uses human labels like:

- `Industrials`
- `Information Technology`
- `United States Lrg Growth`

while the exposure table uses `acid` values that may be abbreviated or slightly different.

So there are **two join modes**:

1. exact join by `acid` when possible
2. normalized join by label when the packet uses human-readable labels

If rebuilding the UI, it is worth creating an explicit `display_label` mapping layer instead of relying on fuzzy matching in the component code.

## 4. File-by-File Schema

## 4.1 `fundWeightsVirAlgo.json`

This is the most important table in the whole app.

### Grain

One row per:

- `fund`
- `acid`

### Example fields

- `row_id`
- `snapshot_date`
- `exposure_source`
- `source_file`
- `fund`
- `acid_type`
- `acid`
- `fund_target_rolled_exposure`
- `fund_benchmark_rolled_exposure`
- `active_rolled_exposure`
- `matched_target_weight`
- `target_match_pct`
- `matched_benchmark_weight`
- `benchmark_match_pct`
- `benchmark_coverage_ok`
- `source_security_count`
- `sample_source_securities`
- `vir_snapshot_date`
- `vir_workbook_type`
- `vir_stf`
- `vir_delta_stf`
- `vir_rank_in_category_by_stf`
- `vir_rank_change_by_stf`
- `algo_snapshot_date`
- `algo_perspective`
- `algo_sheet_dimension`
- `algo_absolute_weight`
- `algo_active_weight`
- `algo_benchmark_weight`
- `algo_absolute_weight_mom`
- `algo_active_weight_mom`
- `vir_join_status`
- `algo_join_status`

### Semantic meaning of the core fields

- `fund_target_rolled_exposure`
  - portfolio / target weight for the exposure

- `fund_benchmark_rolled_exposure`
  - benchmark weight for the same exposure

- `active_rolled_exposure`
  - portfolio minus benchmark
  - this is the main field for overweights / underweights

- `vir_stf`
  - current VIR / STF signal level for the exposure

- `vir_delta_stf`
  - month-over-month VIR / STF change

- `algo_active_weight`
  - model / algo suggested active weight

- `algo_active_weight_mom`
  - month-over-month change in algo active weight

- `source_security_count`
  - number of underlying security rows contributing to this exposure

- `sample_source_securities`
  - quick string preview of underlying names

- `vir_join_status`
  - whether the exposure matched to VIR data

- `algo_join_status`
  - whether the exposure matched to algo data

### How to use this file in UI

Use it for:

- all top overweights / underweights
- active exposure tables
- benchmark vs portfolio comparisons
- signal alignment / disagreement
- category aggregation
- sorting / filtering by category, sign, size, signal status

## 4.2 `exposureLineage.json`

This is the drilldown dataset.

### Grain

Nested shape:

- top level key = `fund`
- next level key = `acid`

Then each `(fund, acid)` object contains:

- `securityCount`
- `totalActiveContribution`
- `securities`
- `byPath`

### `securities[]`

Each security object contains:

- `securityName`
- `identifier`
- `activeContribution`
- `targetContribution`
- `benchmarkContribution`
- `sourceCount`
- `sources`

### `sources[]` inside each security

Each source object contains:

- `sourceName`
- `portcode`
- `path`
- `activeContribution`
- `targetContribution`
- `benchmarkContribution`

### `byPath[]`

Aggregated contribution by sleeve / source path:

- `path`
- `activeContribution`
- `targetContribution`
- `benchmarkContribution`
- `rows`

### How to use this file in UI

This should power the **exposure drilldown**.

Best practice:

1. user selects an exposure row from the top table
2. app loads the `(fund, acid)` lineage object
3. show:
   - total active contribution
   - aggregated security list
   - per-security active contribution
   - per-security source list
   - by-path / by-sleeve summary

Very important:

You specifically asked that drilldown should **not** show active weight repeated blindly.
Instead it should aggregate security contributions across multiple sleeves.

For example:

- `NVIDIA total contribution = 10`
- then underneath:
  - `Fund A = 5`
  - `Fund B = 3`
  - `Fund C = 2`

This file has the right structure for that.

## 4.3 `monthlyReviewBundle.json`

This is the older review bundle.

### Top-level structure

- `bundle_generated_at`
- `snapshot_date`
- `as_of_date`
- `fund_count`
- `funds[]`

### Each `funds[]` item contains

- `slug`
- `fund`
- `snapshot_date`
- `review_run_id`
- `run_summary_markdown`
- `detailed_review_markdown`
- `detailed_review_html`
- `artifact_paths`
- `run_payload`
- `index_entry`

### `artifact_paths`

Contains repo paths such as:

- `pm_review_markdown`
- `pm_review_html`
- `change_brief_json`
- `change_brief_markdown`
- `agent_trace_json`

### `run_payload.review_run_metadata`

Contains run metadata:

- `fund`
- `snapshot_date`
- `as_of_date`
- `review_run_id`
- `parser_version`
- `mapping_version`
- `governance_version`
- `algo_version`
- `run_mode`

### `run_payload.change_brief`

Contains:

- `evidence_index`
- `executive_summary`
- `material_movers`
- `memory_updates_summary`
- `sizing_artifact_summary`
- `triggers_fired_summary`
- `header`

### Use of `monthlyReviewBundle.json`

This should be treated as:

- legacy review narrative
- legacy evidence / review metadata
- fallback source when no `agent2` review exists yet

It is **not** the best source for modern structured UI.

For a new site, use this mostly for:

- backward compatibility
- markdown review rendering
- artifact links
- memory / review history metadata

## 4.4 `agent2` manifest

Current example:

- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-manifest.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-manifest.json)

### Fields

- `fund`
- `logical_snapshot_date`
- `review_date`
- `model`
- `region_name`
- `generated_at`
- `artifacts`
- `usage`
- `approx_cost_usd`
- `parsed_json_ok`

### `usage`

- `inputTokens`
- `outputTokens`
- `totalTokens`
- `cacheReadInputTokens`
- `cacheWriteInputTokens`

### Use in UI

This file should power:

- run metadata
- model name
- generation timestamp
- token usage
- estimated cost
- links to raw artifacts

## 4.5 `agent2` review

Current example:

- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-review.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-review.json)

This is the **LLM output** in structured JSON form.

### Top-level keys

- `executive_summary`
- `current_positioning`
- `what_changed`
- `bull_case`
- `bear_case`
- `devils_advocate`
- `pm_questions`
- `follow_up`
- `dashboard_highlights`

### Shapes

#### `current_positioning[]`

- `label`
- `view`
- `evidence`

#### `what_changed[]`

- `label`
- `change`
- `why_it_matters`

#### `bull_case[]`, `bear_case[]`, `devils_advocate[]`

- `label`
- `statement`

#### `pm_questions[]`

- `label`
- `question`
- `why_now`

#### `follow_up[]`

- `label`
- `action`

#### `dashboard_highlights[]`

- `label`
- `highlight`

### Use in UI

This file should drive the **narrative layer** of the dashboard:

- executive summary hero
- PM review tab
- bull / bear / devil's advocate cards
- PM questions panel
- follow-up tracker
- highlights rail

Important:

This file is excellent for narrative display, but not ideal for granular numeric UI because it contains text summaries, not normalized row-level records.

## 4.6 `agent2` packet

Current example:

- [frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/data/agent2/mstar-us-equity-packet.json)

This is the most important structured file for the next frontend.

Think of it as the **pre-LLM analytical data model**.

### Top-level keys

- `header`
- `fund_snapshot`
- `material_positions`
- `signal_summary`
- `top_movers`
- `decomposition_summary`
- `challenge_book`
- `pm_questions`
- `portfolio_implications`
- `roadmap`
- `data_quality_flags`
- `source_index`
- `run_metadata`

### `header`

- `fund`
- `fund_slug`
- `fund_type`
- `benchmark`
- `pm_names`
- `snapshot_date`
- `as_of_date`
- `review_date`
- `review_run_id`
- `source_snapshot_date`

### `fund_snapshot`

Contains:

- `largest_overweights[]`
- `largest_underweights[]`
- `category_exposures[]`
- `style_posture[]`
- `headline_summary[]`

This is great for:

- overview page
- top tilts
- category posture
- style posture

### `material_positions[]`

This is the best table for a redesigned detail page.

Fields include:

- `position_id`
- `acid`
- `category`
- `label`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`
- `vir_now`
- `vir_delta_mom`
- `vir_rank_in_category_by_stf`
- `vir_rank_change_by_stf`
- `algo_view`
- `algo_active_weight`
- `algo_absolute_weight`
- `algo_benchmark_weight`
- `algo_active_weight_mom`
- `signal_alignment`
- `signal_quality`
- `decomposition_assessment`
- `decomposition_driver`
- `decomposition_driver_value`
- `decomposition_values`
- `internal_history_status`
- `internal_history_excerpt`
- `internal_history_related_themes`
- `external_context_status`
- `importance_score`
- `positioning_direction`
- `vir_direction`
- `algo_direction`
- `vir_snapshot_date`
- `algo_snapshot_date`
- `sample_source_securities`
- `source_security_count`
- `source_breakdown`

### `source_breakdown`

This is very useful.

It contains:

- `security_count`
- `securities[]`

Each security contains:

- `security_name`
- `identifier`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`
- `sources[]`
- `source_count`

Each `sources[]` item contains:

- `source_name`
- `portfolio_weight`
- `benchmark_weight`
- `active_weight`

This structure is what should power the improved drilldown you wanted.

### `signal_summary`

Use for:

- signal posture by category
- now vs prior comparisons
- aligned vs diverging counts

### `top_movers`

Use for:

- changes over time
- what moved most in VIR / signal terms
- trend cards / ranked movement lists

### `decomposition_summary`

Use for:

- “why is this signal doing this?”
- factor decomposition
- growth / yield / inflation / valuation adjustment reads

### `challenge_book`

Use for:

- highest-priority position / signal disagreements
- committee challenge queue

### `pm_questions`

Use for:

- PM review tab
- structured discussion prep

### `portfolio_implications`

Use for:

- “what does this mean for the book?”
- downstream consequences of the current positioning

### `roadmap`

Use for:

- next steps
- follow-up actions
- work queue

### `data_quality_flags`

Each item contains:

- `severity`
- `flag`
- `message`

Current examples include:

- missing VIR rows
- missing algo rows
- logical vs source snapshot mismatch
- stale VIR snapshot
- algo scaled to percentage points

### `source_index`

Each item contains:

- `source_type`
- `artifact_path`
- `purpose`

This is very important for traceability.

### `run_metadata`

- `builder_version`
- `fund`
- `logical_snapshot_date`
- `source_snapshot_date`
- `review_date`
- `material_position_count`
- `history_fund_name`

## 5. Recommended Source of Truth by UI Need

If Claude is rebuilding the site, tell it to use this hierarchy:

### For numeric portfolio tables

Use:

- `fundWeightsVirAlgo.json`

### For look-through / drilldown

Use:

- `exposureLineage.json`
- then prefer `agent2 packet material_positions[].source_breakdown` when building a richer single-position detail panel

### For fund-level overview cards

Use:

- `agent2 packet -> fund_snapshot`

### For detailed position cards

Use:

- `agent2 packet -> material_positions`

### For PM narrative / committee text

Use:

- `agent2 review`

### For run metadata / cost / freshness / traceability

Use:

- `agent2 manifest`
- `agent2 packet -> data_quality_flags`
- `agent2 packet -> source_index`

### For fallback or historical review text

Use:

- `monthlyReviewBundle.json`

## 6. Practical Data Model Claude Should Build

The cleanest frontend architecture would normalize the data into these layers:

### `fund`

- `fund`
- `slug`
- `snapshot_date`
- `benchmark`
- `pm_names`
- `review_run_id`

### `exposure`

From `fundWeightsVirAlgo.json`

- one row per `(fund, acid)`
- core numeric position / VIR / algo table

### `exposure_detail`

From:

- `exposureLineage.json`
- enriched by `agent2 packet material_positions.source_breakdown`

### `fund_overview`

From `agent2 packet.fund_snapshot`

### `material_position`

From `agent2 packet.material_positions`

### `review_narrative`

From `agent2 review`

### `run_meta`

From `agent2 manifest`

### `traceability`

From:

- `agent2 packet.data_quality_flags`
- `agent2 packet.source_index`
- `monthlyReviewBundle.run_payload.change_brief.evidence_index`

## 7. Recommended Screen Mapping

If Claude is redesigning the product, this is the cleanest mapping:

### Overview

Use:

- `agent2 packet.fund_snapshot`
- `agent2 review.executive_summary`
- `agent2 review.dashboard_highlights`
- `manifest` cost / freshness metadata

### Positioning

Use:

- `fundWeightsVirAlgo` filtered by fund
- category aggregations built from `acid_type` / category mapping
- top overweights / underweights from `fund_snapshot`
- drilldown from `exposureLineage`

### Signals

Use:

- `fundWeightsVirAlgo`
- `agent2 packet.material_positions`
- `agent2 review.what_changed`
- `agent2 packet.top_movers`
- `challenge_book`

### PM Review

Use:

- `agent2 review.current_positioning`
- `bull_case`
- `bear_case`
- `devils_advocate`
- `pm_questions`
- `follow_up`

### Evidence / Trust / Audit

Use:

- `manifest`
- `data_quality_flags`
- `source_index`
- `monthlyReviewBundle.run_payload.change_brief.evidence_index`

## 8. Current Code That Builds the View Model

If Claude wants to inspect the current transformation logic, the existing frontend view-model code is here:

- [frontend/Example_frontendV1/src/App.jsx](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/frontend/Example_frontendV1/src/App.jsx)

Most relevant functions:

- `buildFundDirectory`
- `buildFundModel`
- `buildAgentReview`
- `filterModelByCategory`
- `parseReviewMarkdown`

These are useful as reference only. Claude does **not** need to preserve this UI architecture.

## 9. Current `agent2` Generation Code

If Claude or a developer wants to understand how the new agent data is produced, look here:

### Core builders

- [agent2/src/agent2/review_packet_builder.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/review_packet_builder.py)
- [agent2/src/agent2/evidence_pack_builder.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/evidence_pack_builder.py)
- [agent2/src/agent2/review_prompt.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/review_prompt.py)
- [agent2/src/agent2/bedrock_review_runner.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/bedrock_review_runner.py)
- [agent2/src/agent2/internal_history_retrieval.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/internal_history_retrieval.py)
- [agent2/src/agent2/ic_checklist_ingest.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/src/agent2/ic_checklist_ingest.py)

### Scripts

- [agent2/scripts/build_review_packet.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/scripts/build_review_packet.py)
- [agent2/scripts/run_bedrock_review.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/scripts/run_bedrock_review.py)
- [agent2/scripts/ingest_ic_checklists.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/scripts/ingest_ic_checklists.py)
- [agent2/scripts/query_internal_history.py](C:/Users/schuri2/OneDrive%20-%20MORNINGSTAR%20INC/Documents/GitHub/Portfolio-Analyst-Agent-V2/agent2/scripts/query_internal_history.py)

## 10. What Claude Should Be Told Explicitly

Tell Claude these points very clearly:

1. The frontend should be redesigned from the data model up, not from the current UI.
2. `fundWeightsVirAlgo.json` is the core numeric exposure table.
3. `exposureLineage.json` is the canonical drilldown source.
4. `agent2_review_packet.json` is the best structured source for overview, position detail, signals, decomposition, and data quality.
5. `bedrock_review.json` is the narrative source for PM-facing text.
6. `run_manifest.json` is the source for cost, model, timestamp, and traceability metadata.
7. The main join keys are `fund` and `acid`, but some `agent2` packet labels need a label-normalization layer.
8. The UI should prioritize:
   - portfolio positioning
   - VIR / algo evolution
   - source drilldown
   - structured PM review
   - trust / evidence / data freshness

## 11. Current Limitations / Gotchas

These matter for frontend design:

1. Not every row has VIR data.
2. Not every row has algo data.
3. Bond rows may legitimately have no VIR / no algo.
4. The current live US Equity run has a stale VIR snapshot (`2026-02-28`) relative to the review month (`2026-05-31`).
5. The `monthlyReviewBundle` is not rich enough alone for the desired product.
6. The current frontend copied only one live `agent2` run (`MStar US Equity`), so a scalable design should expect multiple per-fund `agent2` artifacts later.

## 12. Best Short Instruction to Give Claude

If you want a compact prompt to hand Claude, use this:

> Build a new PM analyst dashboard from the repo data model, not from the current UI. Use `fundWeightsVirAlgo.json` as the core exposure table, `exposureLineage.json` for drilldown, `agent2_review_packet.json` for structured overview / signal / decomposition / challenge data, `bedrock_review.json` for narrative PM review text, and `run_manifest.json` for cost / timestamp / model metadata. Join mainly on `fund` and `acid`, but add a label normalization layer for packet labels like `Industrials` and `United States Lrg Growth`. The product should centralize portfolio data and also show the agent’s reasoning clearly, with strong drilldowns, signal movement, PM questions, and evidence / trust surfaces.
