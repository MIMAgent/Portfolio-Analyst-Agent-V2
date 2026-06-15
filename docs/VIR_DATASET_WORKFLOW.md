# Equity VIR Dataset Workflow

This repo now has one canonical equity VIR dataset:

- `artifacts/vir/equity_vir_dataset.csv`

That file exists so the backend, agent, and frontend do not have to guess which VIR source is latest.

## Source logic

The dataset is built in two layers:

1. Base history through February 28, 2026
   - source:
     - `artifacts/equity_vir_history.csv`
   - this is the historical normalized dataset that already existed in the repo

2. Monthly append from separate Equity Model workbooks
   - sources:
     - `data/2026-03-31/202603-Equity Model.xlsx`
     - `data/2026-04-30/202604-Equity Model.xlsx`
     - `data/2026-05-31/202605-Equity Model.xlsx`
   - future months should follow the same pattern:
     - `data/<snapshot-date>/<yyyymm>-Equity Model.xlsx`

## Canonical rule

Use:

- `artifacts/vir/equity_vir_dataset.csv`

Do not use:

- `artifacts/equity_vir_history.csv`

except as the historical base input for dataset construction.

## Build command

To rebuild the canonical dataset:

```powershell
python scripts\build_equity_vir_dataset.py
```

What that does:

- loads the base history CSV
- discovers all monthly Equity Model workbooks under `data/*/*Equity Model.xlsx`
- parses them with the equity parser
- merges and deduplicates by `(snapshot_date, acid)`
- writes:
  - `artifacts/vir/equity_vir_dataset.csv`
  - `artifacts/vir/equity_vir_dataset.csv.zip`

## Monthly operating procedure

When a new monthly Equity Model workbook arrives:

1. Save it under a new dated folder in `data/`
2. Keep the workbook name in the same style:
   - `YYYYMM-Equity Model.xlsx`
3. Run:

```powershell
python scripts\build_equity_vir_dataset.py
```

That appends the new month into the canonical consolidated VIR dataset.

## Backend usage

The main repo defaults were updated so the backend reads from the canonical dataset path:

- `artifacts/vir/equity_vir_dataset.csv`

This includes:

- monthly review runtime
- challenge trigger logic
- agent2 packet builder
- frontend signal-history build path
- multisignal rolled exposure build path

## Important downstream note

Rebuilding the VIR dataset updates the source of truth for VIR history.

If you also want refreshed joined exposure outputs for the app, rerun the downstream build that joins holdings, benchmark, VIR, and algo together. The main canonical path is:

```powershell
python scripts\build_fund_weights_vir_algo_multisignal.py "data\2026-05-31\RMv2_PCT_Mstar_funds_2026-06-08.xlsm" --algo-workbooks "data\2026-05-31\Algo LR (3).xlsx"
```

That builder refreshes from the canonical VIR dataset path by default.
