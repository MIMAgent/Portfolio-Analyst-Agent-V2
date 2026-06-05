# Equity VIR Parser Spec v1

## Purpose

This document defines the concrete v1 parser contract for the equity model workbook based on the sample file `202602-Equity Model.xlsx` and PM-confirmed signal definitions.

The parser is responsible for reading the workbook, extracting the required equity VIR fields by ACID, computing derived metrics, persisting canonical rows, and preparing monthly deltas for the analyst agent.

The same canonical field contract should also be used by the separate historical workbook `vir_history.xlsx` so that trend generation can run on a consistent schema.

## Workbook Contract

### Source workbook

- File type: Excel workbook (`.xlsx`)
- Primary sheet: `General Model`
- Row grain: one row per equity ACID
- Canonical join key: `ACID`

### Historical trend workbook

- File type: Excel workbook (`.xlsx`)
- Primary sheet: `Sheet1`
- Header row: `1`
- Row grain: one row per `(acid, valdate)`
- Canonical join key: `(acid, snapshot_date)`

The history workbook is not the main monthly ingestion source. It is the backfilled time series source used to create trend-ready normalized rows using the same canonical output fields as the equity parser.

### Header layout

- Row `3`: canonical machine-readable field IDs
- Row `5`: human-readable business labels
- First data row: `6`
- Stop condition: first blank ACID row after data begins

The parser should use row `3` for field matching and retain row `5` labels for documentation, debug output, and future lineage metadata.

## Required Field Extraction

### Identity fields

- `asset_class_name`: column `B`
- `acid`: column `C`

### Primary analytical fields

- `local_real_vir`: `LR10_Combined` from column `RJ`
- `local_nominal_vir`: `N10USD_Combined` from column `RM`
- `usd_hedged_vir`: `N10USDH` from column `ALH`
- `unconditional_vir`: `LRUC_Combined` from column `RL`
- `price_to_fair_value`: `PFV_t` from column `QQ`

### Confirmed v1 STF definition

For the equity model, the primary attractiveness signal is:

`stf = LR10_Combined - LRUC_Combined`

This definition supersedes the earlier generic handoff formula. The parser must not compute equity STF as `Unconditional - 20Y`.

### Decomposition fields

Store the following decomposition inputs in canonical form:

- `inflation`: `Infl_RD10` from column `PU`
- `currency_usd`: `USD_RD10` from column `PV`
- `yield`: `Yld_RD10` from column `PW`
- `growth`: `Growth_RD10` from column `PX`
- `valuation_adjustment_top_down`: `ValAdj_RD10` from column `PY`
- `valuation_adjustment_combined`: `ValAdj_RD10_Combined` from column `RG`

### Derived decomposition field

Compute and store:

`valuation_adjustment_bottom_up = 2 * ValAdj_RD10_Combined - ValAdj_RD10`

## Historical Header Aliases

When ingesting `vir_history.xlsx`, map the workbook headers below into the same canonical fields used by the equity parser:

- `acid` -> `acid`
- `valdate` -> `snapshot_date`
- `lr10_combined` -> `local_real_vir`
- `usdn_uh10_combined` -> `local_nominal_vir`
- `usdn_h10` -> `usd_hedged_vir`
- `lruc` -> `unconditional_vir`
- `infl_rd` -> `inflation`
- `usd_rduh10` -> `currency_usd`
- `yield_rd10` -> `yield`
- `growth_rd` -> `growth`
- `valadj_rd10` -> `valuation_adjustment_top_down`
- `valadj_rd10_combined` -> `valuation_adjustment_combined`
- `PFV_agg` -> `price_to_fair_value`

Notes:

- `asset_class_name` is not present in the history file and should remain null unless joined from a reference source.
- Header matching for the history workbook should be case-insensitive.
- The output column names should still follow the canonical parser names, not the raw history-file aliases.

## Parser Behavior

### 1. Read and validate

- Open sheet `General Model`
- Read machine headers from row `3`
- Validate required headers are present for all required fields above
- Validate each data row has a non-empty ACID
- Preserve the full raw row as structured payload for audit and replay

### 2. Normalize row output

For each ACID row, emit a canonical normalized record containing:

- `snapshot_date`
- `workbook_type = equity_model`
- `acid`
- `asset_class_name`
- extracted raw numeric fields
- derived STF
- decomposition fields
- derived bottom-up valuation adjustment
- raw row payload

If a numeric field is blank, preserve it as null and record the missing field in validation output. Do not infer missing values.

### 3. Persist snapshot

Persist one normalized row per `(snapshot_date, acid)`.

The parser should also store:

- header row `3` mapping used for this parse
- row `5` business labels used for lineage
- ingestion timestamp
- parser version

## Delta Logic

After loading the current month, compare each ACID against the most recent prior snapshot.

### Required monthly comparisons

- `delta_stf = current_stf - prior_stf`
- `delta_local_real_vir`
- `delta_local_nominal_vir`
- `delta_usd_hedged_vir`
- `delta_unconditional_vir`
- `delta_price_to_fair_value`

For the historical workbook, compute these same deltas row by row within each ACID time series, using the immediately prior `valdate` for that ACID.

### STF driver decomposition

Because `stf = LR10_Combined - LRUC_Combined`, decompose the STF change as:

`delta_stf = delta_LR10_Combined - delta_LRUC_Combined`

Store both components explicitly so the agent can explain whether STF moved because:

- the 10-year local real VIR improved,
- the unconditional VIR changed,
- or both moved in offsetting/reinforcing directions.

### Ranking

For the equity model, rank attractiveness and movers using `stf`.

Store:

- `rank_in_category_by_stf`
- `prior_rank_in_category_by_stf`
- `rank_change_by_stf`

Top movers should be defined by absolute `delta_stf`.

If category metadata is not available in the historical workbook, the implementation may temporarily rank across the full equity history universe for each snapshot date until category enrichment is added.

## Validation Rules

Reject the ingestion if any of the following are true:

- `General Model` sheet is missing
- row `3` cannot be read as the canonical header row
- `ACID` column is missing
- any of `LR10_Combined`, `LRUC_Combined`, `N10USD_Combined`, `N10USDH`, `PFV_t`, `Infl_RD10`, `USD_RD10`, `Yld_RD10`, `Growth_RD10`, `ValAdj_RD10`, `ValAdj_RD10_Combined` are missing

Warn but do not fail if:

- some required fields are blank for a subset of ACIDs
- business labels in row `5` drift while row `3` machine headers remain stable
- some ACIDs are new or absent versus the prior month

## Canonical Storage Shape

Recommended normalized fields for the v1 equity snapshot table:

- `snapshot_date`
- `ingested_at`
- `parser_version`
- `workbook_type`
- `acid`
- `asset_class_name`
- `local_real_vir`
- `local_nominal_vir`
- `usd_hedged_vir`
- `unconditional_vir`
- `stf`
- `price_to_fair_value`
- `inflation`
- `currency_usd`
- `yield`
- `growth`
- `valuation_adjustment_top_down`
- `valuation_adjustment_combined`
- `valuation_adjustment_bottom_up`
- `prior_stf`
- `delta_stf`
- `prior_rank_in_category_by_stf`
- `rank_in_category_by_stf`
- `rank_change_by_stf`
- `raw_row`
- `raw_headers`

## Agent-Facing Output Contract

The parser should return a structured ingestion summary with:

- snapshot date processed
- row count ingested
- matched ACIDs vs prior month
- new ACIDs
- missing ACIDs vs prior month
- top movers by absolute STF delta
- STF driver decomposition for those movers
- validation warnings

The parser should not decide what the investment conclusion is. It should expose structured evidence so the LLM agent can determine:

- what changed,
- whether the move is meaningful,
- whether decomposition is supportive or misleading,
- and how the signal maps to portfolio positioning.

## Implementation Notes

- Match fields by row `3` machine headers, not by Excel column letters alone.
- Keep column letters in test fixtures and docs as a convenience check, not as the primary production dependency.
- Treat this as a model-specific parser profile named `equity_model_v1`.
- Design the parser framework so fixed income and future models can register different primary-signal formulas without changing the surrounding ingestion pipeline.

## Open Follow-Ups

- Confirm whether category mapping for each ACID is present in this workbook or will come from a separate reference source.
- Add a sample sanitized holdings file next so ACID-based cross-reference logic can be specified against real portfolio data.
