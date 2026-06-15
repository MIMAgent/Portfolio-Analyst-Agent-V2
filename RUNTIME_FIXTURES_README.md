# Runtime Fixtures Upload Set

This folder contains the curated runtime/demo fixtures for `Portfolio-Analyst-Agent-V2`.

Include these files in GitHub:

- `data/acid_mapping_bootstrap_v1.csv`
- `artifacts/agent_memory/memory_records.json`
- `artifacts/equity_vir_history.csv.zip`
- `artifacts/vir/equity_vir_dataset.csv.zip`
- `artifacts/rolled_exposures/*`

Notes:

- `artifacts/equity_vir_history.csv.zip` is the legacy/base pre-March history mirror.
- `artifacts/vir/equity_vir_dataset.csv.zip` is the canonical consolidated VIR dataset the app/backend should use.

Do not upload the broader generated artifact directory, raw workbooks, raw `equity_vir_history.csv`, raw `artifacts/vir/equity_vir_dataset.csv`, `.env`, `__pycache__`, `.pyc`, `.pytest_cache`, monthly review traces, or patch ZIPs.
