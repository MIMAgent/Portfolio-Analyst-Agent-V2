# Fund Alignment Multisignal Patch - 2026-04-09

## Purpose

This note documents the join-logic patch that preserves both algo perspectives in fund-level rolled exposure alignment and enforces `acid_type` to algo-dimension mapping.

## Why This Patch Was Needed

The earlier rolled exposure alignment keyed algo joins by `acid` only.

That created two problems:

1. multiple algo perspectives such as `local_real` and `usd_unhedged` could collapse into one surviving row per ACID
2. the join did not enforce that:
   - `acid_country` should attach only to `Countries`
   - `acid_region_sector` should attach only to `RegionalSectors`
   - `acid_bond` should not attach to the current equity algo dimensions

## What Changed

New files:

- `src/portfolio_analyst_agent/rolled_exposure_alignment_multisignal.py`
- `src/portfolio_analyst_agent/fund_weights_vir_algo_multisignal.py`
- `scripts/build_fund_weights_vir_algo_multisignal.py`

## New Join Behavior

### Acid-type to dimension mapping

- `acid_country` -> `countries`
- `acid_region_sector` -> `regional_sectors`
- `acid_bond` -> no current algo dimension

### Perspective preservation

For eligible ACID types, the alignment now emits one row per expected algo perspective for the mapped dimension.

Current practical result with the two monthly algo workbooks:

- one `local_real` row
- one `usd_unhedged` row

for each matched:

- country ACID
- region-sector ACID

### Missing behavior

If an ACID is eligible for algo matching but missing from the latest algo signal set, the output still preserves one row per expected perspective with:

- `algo_join_status = missing_in_algo`

### Non-applicable behavior

If an ACID type has no valid algo dimension under the current workflow, the output emits one row with:

- `algo_join_status = not_applicable_for_acid_type`

This is the expected result today for:

- `acid_bond`

## Validation Summary

Local fixture validation confirmed:

- country rows fan out into two algo rows
- region-sector rows fan out into two algo rows
- bond rows remain outside the algo join
- missing eligible ACIDs still preserve both expected algo perspectives with `missing_in_algo`

## Recommended Use

Use `scripts/build_fund_weights_vir_algo_multisignal.py` when the goal is to produce a combined fund-level weights + VIR + algo file without collapsing multiple algo perspectives into one row.
