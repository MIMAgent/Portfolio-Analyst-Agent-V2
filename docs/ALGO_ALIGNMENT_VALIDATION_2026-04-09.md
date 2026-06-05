# Algo Alignment Validation - 2026-04-09

## Scope

Validated the first command-line wrapper that joins the latest algo signal set to normalized VIR and holdings CSV inputs.

New script:

- `scripts/build_algo_alignment.py`

This script builds the latest algo signal set from:

- `Algo LR.xlsx`
- `Algo USD Unhedged.xlsx`

and then optionally joins those latest signals to:

- normalized VIR CSV rows
- normalized holdings CSV rows

## Local Validation Run

Command used locally:

```bash
python scripts/build_algo_alignment.py "Algo LR.xlsx" "Algo USD Unhedged.xlsx" --vir-csv artifacts/test_vir_rows.csv --holdings-csv artifacts/test_holdings_rows.csv --algo-vir-output artifacts/test_algo_vir_alignment.csv --algo-holdings-output artifacts/test_algo_holdings_alignment.csv
```

Observed output:

- `latest_signal_count=200`
- `algo_vir_alignment_count=200`
- `algo_holdings_alignment_count=200`

## Smoke-Test Join Status Counts

Using small local fixture CSVs:

- algo-to-VIR:
  - `matched_to_vir=6`
  - `missing_in_vir=194`
- algo-to-holdings:
  - `matched_to_holdings=6`
  - `missing_in_holdings=194`

Interpretation:

- the script preserves one output row per latest algo signal
- matched and missing join states remain explicit in the output
- this is the right behavior for auditability and downstream PM review

## What Is Now Ready

The repo now contains working CLI entry points for:

- parsing the raw monthly algo workbooks
- building the PM-facing sizing snapshot artifact
- joining the latest algo signals to normalized VIR rows
- joining the latest algo signals to normalized holdings rows

## What Still Depends On Upstream Inputs

Real production alignment output still requires normalized source CSVs for:

- VIR snapshots
- holdings exposures

So this closes the algo-to-alignment CLI scaffold, but not the final real-data alignment run.
