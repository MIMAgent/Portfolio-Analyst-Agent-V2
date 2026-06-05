# Portfolio Analyst Agent

Institutional PM analyst agent for monthly VIR review, portfolio cross-reference, and IC prep.

## Current focus

- Define the agent-first architecture
- Specify the v1 equity VIR parser against a real sample workbook
- Specify the v1 fixed income VIR parser against a real sample export
- Keep the repo aligned with the PM workflow and ACID-based cross-referencing model
- Define a shared ACID mapping schema that captures both taxonomy and agent interpretation rules
- Normalize the initial equity mapping file into the shared mapping contract

## Source inputs

This repository is being bootstrapped from:

- PM analyst agent product schema
- Critical reasoning addendum
- VIR parser requirements handoff
- Sample workbook: `202602-Equity Model.xlsx`
- Sample file: `202602- Fixed Income Model.csv`
- Seed taxonomy file: `Equity_mapping_file.csv`

## Initial docs

- `docs/EQUITY_VIR_PARSER_SPEC_V1.md`: concrete parser spec for the equity model export
- `docs/FIXED_INCOME_VIR_PARSER_SPEC_V1.md`: concrete parser spec for the fixed income model export
- `docs/ACID_MAPPING_SCHEMA_V1.md`: shared enrichment schema for behavior-aware ACID mapping
- `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`: deterministic normalization rules for the current thin equity mapping file

## Current tooling

- `scripts/parse_monthly_algo.py`: normalize monthly algo workbooks
- `scripts/build_sizing_snapshot.py`: build PM-facing sizing snapshot artifacts
- `scripts/build_algo_alignment.py`: align latest algo signals to VIR and holdings rows
- `scripts/parse_equity_vir_history.py`: normalize `vir_history.xlsx` into trend-ready equity VIR rows
- `scripts/build_rolled_exposures.py`: roll account and fund exposures to country, region-sector, and bond ACIDs from `Portfolio` and `Full_lookthrough`
- `scripts/build_rolled_exposure_alignment.py`: attach VIR fields and latest algo signals to rolled account and fund exposure summaries
- `scripts/build_fund_weights_vir_algo_multisignal.py`: canonical rolled exposure parser and fund-level VIR/algo join; preserves both local-real and USD-unhedged algo perspectives when available
- `scripts/build_fund_weights_vir_algo.py`: legacy single-signal fund-level combined weights/VIR/algo CSV path
- `scripts/build_fund_weights_summary.py`: build an analyst-facing markdown summary from the combined fund weights/VIR/algo CSV

## Agent read tools

- `get_fund_snapshot`: returns replay-safe fund ACID rows enriched with the live ACID mapping metadata.
- `get_acid_history`: returns row-stamped VIR history for one ACID, gated by `snapshot_date` / `as_of_date`.
- `get_exposure_lineage`: returns the account/security rows that roll into one fund/ACID exposure.
- `get_peer_context`: returns mapping-driven peer ACIDs and current snapshot rows for relative-value context.
- `recall_memory`: returns approved/applied prior memory as authoritative context while still reporting proposed counts.
- `evaluate_challenge_triggers`: evaluates sign disagreement, decomposition rotation, and better-expression-available trigger candidates.

## Agent governance and memory writes

- `config/agent_governance.json`: versioned governance parameters with `effective_from` semantics.
- `governance.load_governance`: resolves the governance event valid for a run's `as_of_date`.
- `memory_ops.apply_ops`: validates and appends proposed-only memory operations. Model 1 rejects auto-apply and keeps human approval as a separate lifecycle step.

## Agent write tools

- `citations.resolve_token` / `citations.enforce_payload_citations`: resolve CSV, memory, and derivation citation tokens and reject uncited narrative fields.
- `schemas.py`: lightweight stdlib validators for Change Brief, Sizing Considerations, and Challenge Brief payloads.
- `write_tools.py`: validated persistence boundary for `write_change_brief`, `write_sizing_considerations`, `write_challenge_brief`, and `update_memory`.

## LLM agent runtime

- `agent_runtime/tool_registry.py`: exposes the deterministic read/write tools to the LLM with Anthropic-compatible `input_schema` definitions.
- `agent_runtime/loop.py`: runs one fund through the tool-use loop and writes `agent_trace.json`.
- `agent_runtime/llm_client.py`: provides a mockable client interface plus the Anthropic Messages API wrapper.
- `scripts/run_agent_review.py`: CLI entry point for the real LLM-backed run.

To run with Claude through AWS Bedrock:

```powershell
python -m pip install -e ".[bedrock]"
python scripts\run_agent_review.py --provider bedrock --aws-region us-east-1 --model anthropic.claude-sonnet-4-6 --fund "MStar US Equity" --snapshot-date 2026-04-06 --as-of-date 2026-04-06
```

For a Bedrock API key from the AWS console, set this in `.env` or the shell:

```text
AWS_BEARER_TOKEN_BEDROCK=...
AWS_DEFAULT_REGION=us-east-1
```

If you are using standard AWS temporary credentials instead of a Bedrock API key, then use `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.

Direct Anthropic API support remains available only as an explicit alternate provider.

## Current data files

- `data/vir_history.xlsx`: historical equity VIR input used for trend normalization
- `artifacts/equity_vir_history.csv.zip`: tracked mirror for the large normalized equity VIR history CSV; readers use `artifacts/equity_vir_history.csv` when present locally and fall back to this ZIP mirror otherwise
- `data/RMv2_PCT_Mstar_funds_2026-04-06.xlsm`: Morningstar portfolio workbook used for rolled exposure parsing and VIR/algo cross-reference

## Design principles

- LLM-led agent, not a deterministic pipeline disguised as an agent
- Python provides tools, persistence, validation, and auditability
- ACID is the canonical join key across VIR, holdings, and future risk data
- Parser preserves raw workbook fidelity while normalizing into canonical storage
- Mapping files define how the agent should interpret an exposure, not just what bucket it belongs to
