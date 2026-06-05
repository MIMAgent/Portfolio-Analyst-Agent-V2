# Rolled Exposure And Fund Alignment Workflow

Date: 2026-04-09

## Purpose

This document captures the workbook-specific holdings parser replacement and the combined fund-level alignment workflow now in the repository.

The goal is to make it easy to answer:

- what each fund owns at the ACID level
- which account-level holdings are driving a fund's ACID exposure
- how those rolled exposures compare to VIR
- how those rolled exposures compare to the latest algo sizing signals

## Why The Earlier Holdings Approach Was Replaced

The earlier holdings workflow was designed around an exposure-matrix parser and a separate holdings-to-VIR cross-reference layer.

That approach was too abstract for the Morningstar workbook now in use because the real source of truth is security-level lookthrough data paired with account weights in the `Portfolio` tab.

The replacement workflow is built directly around the actual workbook structure:

- `Portfolio` defines account membership and fund weights
- `Full_lookthrough` defines the underlying security exposures and ACID tags

This lets the parser preserve lineage from fund -> account -> security -> ACID instead of only producing a higher-level mapped exposure table.

## Source Workbook Logic

Source workbook:

- `data/RMv2_PCT_Mstar_funds_2026-04-06.xlsm`

Tabs used:

- `Portfolio`
- `Full_lookthrough`

### Portfolio Tab

The parser uses the `Portfolio` tab as the account-to-fund weight map.

Rules:

- column `A`: account name
- column `B`: account `secid`
- rows `5:82`: account rows
- fund blocks begin at columns `G`, `M`, `S`, `Y`, `AE`, `AK`, `AQ`, `AW`
- each block is six columns wide
- row `1` of each block contains the fund name
- the second column in each block is the account target weight for that fund
- the third column in each block is the benchmark weight when present

This produces one account-level weight vector per fund.

### Full_lookthrough Tab

The parser uses the `Full_lookthrough` tab as the security-level source for ACID exposures.

Rules:

- column `B`: `portcode`
- `Portfolio!B` secid is matched to `Full_lookthrough!B` portcode
- column `E`: security name
- column `F`: common identifier
- column `D`: hierarchy path
- column `I`: security weight
- column `J`: broad asset class

Only these ACID columns are used:

- column `V`: `acid_country`
- column `W`: `acid_region_sector`
- column `X`: `acid_bond`

Explicitly not used:

- column `AZ`
- column `BA`

The user requested that bond matching use bond ACID only, and that equity exposures use only columns `V` and `W`.

## Rolled Exposure Parser

Primary files:

- `scripts/build_rolled_exposures.py`
- `src/portfolio_analyst_agent/rolled_exposures.py`

## What The Parser Builds

The parser creates a traceable rolled exposure dataset at both the account and fund level.

### Account-Level Detail

Each eligible security row in `Full_lookthrough` becomes one or more ACID-linked exposure rows:

- one row for `acid_country` when column `V` is populated
- one row for `acid_region_sector` when column `W` is populated
- one row for `acid_bond` when column `X` is populated

Each row preserves:

- `portcode`
- `account_name`
- `security_name`
- `common_identifier`
- `h_path`
- `asset_class_broad`
- `security_weight`
- `acid_type`
- `acid`

This is the core lineage layer used to answer where a country, region, sector, or bond exposure came from.

### Account-Level Summary

The account summary rolls the detailed security rows up to:

- account
- ACID type
- ACID

For each row it stores:

- `account_rolled_exposure`
- source security counts
- sample source security names
- all fund target and benchmark weights from the `Portfolio` tab

This gives a compact view of each account's exposure before fund-level multiplication.

### Fund-Level Detail

The fund detail layer multiplies account-level security contribution by the account weight inside each fund.

For each security-linked ACID row:

- `fund_target_security_contribution = account_target_weight * account_security_contribution`
- `fund_benchmark_security_contribution = account_benchmark_weight * account_security_contribution`

This is the key rolled lookthrough logic.

It keeps the full traceability fields so a user can see which securities inside which accounts are driving a given fund exposure.

### Fund-Level Summary

The fund summary rolls the fund detail rows up to:

- fund
- ACID type
- ACID

For each row it stores:

- `fund_target_rolled_exposure`
- `fund_benchmark_rolled_exposure`
- `active_rolled_exposure`
- matched target and benchmark coverage fields
- source security counts
- sample source securities

This is the main summary layer used for downstream comparison to VIR and algo.

## Rolled Exposure Outputs

The parser writes:

- `artifacts/rolled_exposures/account_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/account_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/fund_rollthrough_coverage.csv`
- `artifacts/rolled_exposures/fund_rollthrough_definitions.csv`

## VIR And Algo Cross-Reference

Primary files:

- `scripts/build_rolled_exposure_alignment.py`
- `src/portfolio_analyst_agent/rolled_exposure_alignment.py`

This layer takes the rolled exposure summaries and attaches analytical fields from the rest of the repo.

### VIR Join Logic

Input:

- normalized VIR CSV, currently `artifacts/equity_vir_history.csv`

Join key:

- `acid`

Behavior:

- uses the latest VIR row by ACID
- only counts as a true VIR match when analytical signal fields are present
- exposes:
  - `vir_snapshot_date`
  - `vir_workbook_type`
  - `vir_stf`
  - `vir_delta_stf`
  - `vir_rank_in_category_by_stf`
  - `vir_rank_change_by_stf`

Status field:

- `vir_join_status`

Important note:

- equity ACIDs can match against the current normalized VIR history CSV
- bond ACIDs will remain `missing_in_vir` until a fixed-income normalized VIR source is added

### Algo Join Logic

Inputs:

- monthly algo workbooks such as `Algo LR.xlsx`
- monthly algo workbooks such as `Algo USD Unhedged.xlsx`

Join key:

- `acid`

Behavior:

- parses the algo workbooks
- collapses them to the latest signal set by ACID
- attaches:
  - `algo_snapshot_date`
  - `algo_perspective`
  - `algo_sheet_dimension`
  - `algo_absolute_weight`
  - `algo_active_weight`
  - `algo_benchmark_weight`
  - `algo_absolute_weight_mom`
  - `algo_active_weight_mom`

Status field:

- `algo_join_status`

## Combined Fund-Level Weights + VIR + Algo Script

Primary files:

- `scripts/build_fund_weights_vir_algo.py`
- `src/portfolio_analyst_agent/fund_weights_vir_algo.py`

This is the orchestration layer that connects all three:

- fund rolled weights
- VIR
- algo

### Logic

Step 1:

- run the rolled exposure parser on the Morningstar workbook

Step 2:

- take the generated `fund_rolled_exposure_summary.csv`

Step 3:

- join those fund-level ACID rows to VIR by `acid`

Step 4:

- join those same fund-level ACID rows to the latest algo signals by `acid`

Step 5:

- write one combined CSV for all funds

Output:

- `artifacts/rolled_exposures/fund_weights_vir_algo.csv`

## What The Combined Fund CSV Contains

Core rolled exposure fields:

- `fund`
- `acid_type`
- `acid`
- `fund_target_rolled_exposure`
- `fund_benchmark_rolled_exposure`
- `active_rolled_exposure`

Traceability fields:

- `source_security_count`
- `sample_source_securities`

Coverage fields:

- `matched_target_weight`
- `target_match_pct`
- `matched_benchmark_weight`
- `benchmark_match_pct`

VIR fields:

- `vir_snapshot_date`
- `vir_workbook_type`
- `vir_stf`
- `vir_delta_stf`
- `vir_rank_in_category_by_stf`
- `vir_rank_change_by_stf`

Algo fields:

- `algo_snapshot_date`
- `algo_perspective`
- `algo_sheet_dimension`
- `algo_absolute_weight`
- `algo_active_weight`
- `algo_benchmark_weight`
- `algo_absolute_weight_mom`
- `algo_active_weight_mom`

Join flags:

- `vir_join_status`
- `algo_join_status`

## Why This Structure Matters

This workflow is designed to support both analysis and explanation.

It does not only say that a fund has exposure to an ACID. It also preserves enough detail to answer:

- which accounts created that exposure
- which securities inside those accounts created that exposure
- whether the exposure lines up with the current VIR view
- whether the exposure lines up with the latest algo sizing view

That makes it useful both for machine-readable downstream prompts and for analyst QA.

## Current Limitations

- The current VIR source is equity-only, so many bond ACIDs will not yet match to VIR.
- Algo fields remain blank unless algo workbook paths are provided at runtime.
- The combined fund-level CSV is summary-level; detailed security trace still lives in the fund detail and account detail CSVs.

## Main Commands

Build rolled exposures:

```powershell
& "C:\Users\schuri2\AppData\Local\Programs\Python\Python311\python.exe" scripts\build_rolled_exposures.py "data\RMv2_PCT_Mstar_funds_2026-04-06.xlsm"
```

Build rolled exposure alignment:

```powershell
& "C:\Users\schuri2\AppData\Local\Programs\Python\Python311\python.exe" scripts\build_rolled_exposure_alignment.py --vir-csv artifacts\equity_vir_history.csv --algo-workbooks "C:\path\to\Algo LR.xlsx" "C:\path\to\Algo USD Unhedged.xlsx"
```

Build one combined fund-level weights + VIR + algo CSV:

```powershell
& "C:\Users\schuri2\AppData\Local\Programs\Python\Python311\python.exe" scripts\build_fund_weights_vir_algo.py --algo-workbooks "C:\path\to\Algo LR.xlsx" "C:\path\to\Algo USD Unhedged.xlsx"
```
