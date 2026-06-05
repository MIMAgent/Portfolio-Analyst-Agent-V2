# Fixed Income VIR Parser Spec v1

## Purpose

This document defines the concrete v1 parser contract for the fixed income model export based on the sample file `202602- Fixed Income Model.csv` and PM-confirmed signal definitions.

The parser is responsible for reading the fixed income model export, extracting the required fields by ACID, computing derived metrics, persisting canonical rows, and preparing monthly deltas for the analyst agent.

## File Contract

### Source file

- File type: CSV
- Row grain: one row per fixed income ACID
- Canonical join key: `acid`
- Header row: first row of the file
- Headers are already machine-friendly and normalized

### Core identity and market fields

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

## Required Field Extraction

### Primary analytical fields

- `local_nominal_10`: 10-year local nominal VIR
- `local_real_10`: 10-year local real VIR
- `usd_hedged_10`: 10-year USD-hedged VIR
- `real_vir_fair`: fair-value real VIR

### Confirmed v1 fixed income STF definition

For the fixed income model, the primary attractiveness signal is:

`stf = local_real_10 - real_vir_fair`

This is the fixed income parser's primary signal for ranking and monthly delta analysis.

### VIR decomposition fields

Store the 10-year decomposition inputs in canonical form:

- `income_contrib_10`
- `rollyield_contrib_10`
- `creditloss_contrib_10`
- `price_contrib_10`
- `inflation_contrib_10`

### Fair-value reference field

- `inflation_contrib_fair`

## Derived Fields

### 1. Spread to Fair

Compute and store:

`stf = local_real_10 - real_vir_fair`

### 2. USD-investor hedged yield helper

Compute and store the PM-requested helper field:

`usd_hedged_yield_to_maturity_1 = yield_tomaturity + fx_usd_hedged_1`

In v1, this helper should be treated as a treasury-focused developed-markets helper, not a generic non-USD bond rule.

Apply it to treasury ACIDs for the following markets:

- Australia: `AU T`
- Canada: `CA T`
- Europe aggregate: `EU T`
- Germany: `EU T: DEU`
- Spain: `EU T: ESP`
- France: `EU T: FRA`
- Italy: `EU T: ITA`
- Japan: `JP T`
- UK: `UK T`

If the parser cannot match an ACID to this allowlist, it should leave `usd_hedged_yield_to_maturity_1` null unless a later mapping/config expands the rule.

## Parser Behavior

### 1. Read and validate

- Read the CSV header row directly
- Validate required headers are present
- Validate each data row has a non-empty `acid`
- Preserve the full raw row as structured payload for audit and replay

### 2. Normalize row output

For each ACID row, emit a canonical normalized record containing:

- `snapshot_date`
- `workbook_type = fixed_income_model`
- `acid`
- `currency`
- `curve_type`
- core market fields
- primary VIR fields
- fair-value fields
- decomposition fields
- derived STF
- derived USD-investor hedged-YTM helper
- raw row payload

If a numeric field is blank, preserve it as null and record the missing field in validation output. Do not infer missing values.

### 3. Persist snapshot

Persist one normalized row per `(snapshot_date, acid)`.

The parser should also store:

- ingestion timestamp
- parser version
- raw headers used for this parse

## Delta Logic

After loading the current month, compare each ACID against the most recent prior snapshot.

### Required monthly comparisons

- `delta_stf = current_stf - prior_stf`
- `delta_local_nominal_10`
- `delta_local_real_10`
- `delta_usd_hedged_10`
- `delta_real_vir_fair`
- `delta_yield_tomaturity`
- `delta_duration`
- `delta_oas`
- `delta_oas_fv`
- `delta_termspread`
- `delta_termspread_fv`

### STF driver decomposition

Because `stf = local_real_10 - real_vir_fair`, decompose the STF change as:

`delta_stf = delta_local_real_10 - delta_real_vir_fair`

Store both components explicitly so the agent can explain whether STF moved because:

- the 10-year local real VIR changed,
- the fair-value real VIR changed,
- or both moved in offsetting/reinforcing directions.

### Ranking

For the fixed income model, rank attractiveness and movers using `stf`.

Store:

- `rank_in_category_by_stf`
- `prior_rank_in_category_by_stf`
- `rank_change_by_stf`

Top movers should be defined by absolute `delta_stf`.

## Validation Rules

Reject the ingestion if any of the following are true:

- `acid` header is missing
- any of `currency`, `curve_type`, `yield_tomaturity`, `duration`, `oas`, `convexity`, `oas_fv`, `termspread`, `termspread_fv`, `yield_tomaturity_fv`, `fx_usd_hedged_1`, `local_nominal_10`, `local_real_10`, `usd_hedged_10`, `income_contrib_10`, `rollyield_contrib_10`, `creditloss_contrib_10`, `price_contrib_10`, `inflation_contrib_10`, `real_vir_fair`, `inflation_contrib_fair` are missing

Warn but do not fail if:

- some required fields are blank for a subset of ACIDs
- some ACIDs are new or absent versus the prior month
- convexity is blank for instruments where the model export leaves it empty

## Canonical Storage Shape

Recommended normalized fields for the v1 fixed income snapshot table:

- `snapshot_date`
- `ingested_at`
- `parser_version`
- `workbook_type`
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
- `usd_hedged_yield_to_maturity_1`
- `local_nominal_10`
- `local_real_10`
- `usd_hedged_10`
- `real_vir_fair`
- `stf`
- `income_contrib_10`
- `rollyield_contrib_10`
- `creditloss_contrib_10`
- `price_contrib_10`
- `inflation_contrib_10`
- `inflation_contrib_fair`
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
- whether the fixed income signal is driven by carry, price, inflation, or fair-value shifts,
- and how the signal maps to portfolio positioning.

## Implementation Notes

- Match fields by CSV header names only; there is no Excel-column dependency in production parsing.
- Treat this as a model-specific parser profile named `fixed_income_model_v1`.
- Keep the parser framework flexible so each model family can define its own primary signal and decomposition logic.
- The fixed income model is already structurally normalized, so the parser should remain thin and avoid unnecessary reshaping.

## Open Follow-Ups

- Decide whether the treasury ACID allowlist for the hedged-YTM helper should live in parser config or in the future ACID mapping file.
- Provide the future ACID mapping file for category enrichment.
- Add a sample holdings file after both model specs are complete so cross-reference logic can be specified against real portfolio data.
