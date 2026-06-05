# Monthly Review Viewer

React viewer for the tracked monthly review output pack.

## Data source

The viewer uses:

- `src/data/monthlyReviewBundle.json`

That bundle is generated from:

- `artifacts/monthly_review/<snapshot_date>/batch_index.json`
- each fund's `run_payload.json`
- each fund's `run_summary.md`

## Refresh the bundle

```powershell
python scripts\build_monthly_review_frontend_bundle.py
```

## Run

```powershell
cd frontend\Example_frontendV1
npm run dev
```

## Build

```powershell
cd frontend\Example_frontendV1
npm run build
```

## What it shows

- fund selector
- Change Brief material movers
- Sizing agreement and disagreement lists
- Challenge Brief items
- run summary markdown
- evidence pointer and source-hash context
