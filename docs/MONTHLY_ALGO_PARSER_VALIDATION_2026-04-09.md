# Monthly Algo Parser Validation - 2026-04-09

## Scope

Validated the initial local algo parser scaffold against the two real monthly algo workbooks:

- `Algo LR.xlsx`
- `Algo USD Unhedged.xlsx`

The generated CSV artifact was kept local and not committed.

## Local Run

Command used locally:

```bash
python scripts/parse_monthly_algo.py "Algo LR.xlsx" "Algo USD Unhedged.xlsx" --output artifacts/monthly_algo_records.csv
```

## Validation Outcome

### Algo LR

- perspective: `local_real`
- snapshot date detected: `2026-02-28`
- normalized record count: `58,500`
- counts by sheet:
  - `countries`: `29,835`
  - `regional_sectors`: `28,665`
- counts by metric:
  - `absolute_weight`: `11,700`
  - `active_weight`: `11,700`
  - `benchmark_weight`: `11,700`
  - `absolute_weight_mom`: `11,700`
  - `active_weight_mom`: `11,700`

### Algo USD Unhedged

- perspective: `usd_unhedged`
- snapshot date detected: `2026-02-28`
- normalized record count: `58,500`
- counts by sheet:
  - `countries`: `29,835`
  - `regional_sectors`: `28,665`
- counts by metric:
  - `absolute_weight`: `11,700`
  - `active_weight`: `11,700`
  - `benchmark_weight`: `11,700`
  - `absolute_weight_mom`: `11,700`
  - `active_weight_mom`: `11,700`

### Combined local artifact

- total normalized rows written locally: `117,000`
- local output path: `artifacts/monthly_algo_records.csv`

## Interpretation

This confirms:

- the algo parser scaffold can read both workbooks using the standard-library XLSX reader
- the `Countries` and `RegionalSectors` sheet contracts are implemented correctly enough to parse the real files end to end
- the output is ready to serve as the basis for the separate sizing artifact in the monthly workflow

## Repo Impact

The repo now contains:

- parser scaffold code under `src/portfolio_analyst_agent/`
- CLI entrypoint under `scripts/parse_monthly_algo.py`
- parser contract in `docs/MONTHLY_ALGO_PARSER_SPEC_V1.md`

The generated CSV remains a local artifact and is intentionally excluded from source control.
