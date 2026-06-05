# Runtime Fixtures Policy V1

Purpose: keep `Portfolio-Analyst-Agent-V2` runnable for demo and test review flows without turning GitHub into a dump for generated outputs or raw local workbooks.

## Tracked Runtime Fixtures

The repo may track the following curated runtime fixtures:

- `data/acid_mapping_bootstrap_v1.csv`
- `artifacts/agent_memory/memory_records.json`
- `artifacts/equity_vir_history.csv.zip`
- `artifacts/rolled_exposures/account_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/account_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/fund_rollthrough_coverage.csv`
- `artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv`
- `artifacts/rolled_exposures/fund_weights_vir_algo_summary.md`

## Excluded Files

Do not track:

- `.env` or any API credentials
- raw workbook inputs unless explicitly approved
- raw `artifacts/equity_vir_history.csv`
- monthly review traces and generated run outputs
- generated HTML viewers
- `__pycache__`, `.pyc`, `.pytest_cache`, or local logs
- Codex patch ZIPs or CloudShell transport bundles

## Rationale

The curated fixtures let a fresh clone run the current review harness against a known April 2026 sample. Generated monthly outputs should be recreated by scripts, not preserved as source.
