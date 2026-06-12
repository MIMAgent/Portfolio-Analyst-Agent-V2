"""Build one fund-level CSV that preserves both algo perspectives per eligible ACID."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.fund_weights_vir_algo_multisignal import (  # noqa: E402
    build_fund_weights_vir_algo_multisignal,
)
from portfolio_analyst_agent.equity_history import (  # noqa: E402
    load_equity_history_records_from_csv,
    merge_equity_history_records,
    parse_equity_history_workbook,
    write_equity_history_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build one fund-level CSV that preserves both algo perspectives per eligible ACID."
    )
    parser.add_argument(
        "workbook",
        nargs="?",
        default=None,
        help="Path to the RMv2 .xlsm workbook. If omitted, the newest data/RMv2_*.xlsm is used.",
    )
    parser.add_argument(
        "--vir-csv",
        default="artifacts/equity_vir_history.csv",
        help="Normalized VIR CSV used to attach STF and rank fields. Falls back to <name>.zip if the raw CSV is absent.",
    )
    parser.add_argument(
        "--vir-workbook",
        nargs="*",
        default=None,
        help="One or more Equity Model workbooks used to refresh the normalized VIR history before joining exposures.",
    )
    parser.add_argument(
        "--algo-workbooks",
        nargs="*",
        help="Monthly algo workbook paths used to attach latest algo signals.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/rolled_exposures",
        help="Directory where rolled exposure artifacts should be written.",
    )
    parser.add_argument(
        "--fund-output",
        default="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
        help="Output CSV for the combined fund-level rows.",
    )
    return parser


def _resolve_workbook(explicit: str | None) -> str:
    """Return the workbook path, defaulting to the newest data/RMv2_*.xlsm.

    Avoids silently re-parsing a stale dated file baked into the defaults (audit:
    reproducibility/config). Filenames embed an ISO date, so lexical max == newest.
    """
    if explicit:
        return explicit
    candidates = sorted(p for p in (ROOT / "data").glob("RMv2_*.xlsm") if not p.name.startswith("~$"))
    if not candidates:
        raise SystemExit("No workbook given and no data/RMv2_*.xlsm found.")
    return str(candidates[-1])


def _resolve_equity_model_workbooks(explicit: list[str] | None) -> list[str]:
    if explicit:
        return explicit
    candidates = sorted(
        p
        for p in (ROOT / "data").glob("*/*Equity Model.xlsx")
        if not p.name.startswith("~$")
    )
    return [str(path) for path in candidates]


def _refresh_vir_history(vir_csv: str, vir_workbooks: list[str] | None) -> Path | None:
    if not vir_workbooks:
        return None

    existing_records = []
    try:
        existing_records = load_equity_history_records_from_csv(vir_csv)
    except FileNotFoundError:
        existing_records = []

    merged_records = existing_records
    refreshed_row_count = 0
    resolved_workbooks = [Path(path).resolve() for path in vir_workbooks]
    for workbook_path in resolved_workbooks:
        result = parse_equity_history_workbook(workbook_path)
        refreshed_row_count += len(result.records)
        merged_records = merge_equity_history_records(merged_records, result.records)

    output_path = write_equity_history_csv(merged_records, vir_csv)

    latest_dates = sorted({record.snapshot_date for record in merged_records})
    latest_snapshot = latest_dates[-1].isoformat() if latest_dates else ""
    print(f"vir_source_workbooks={','.join(str(path) for path in resolved_workbooks)}")
    print(f"vir_refreshed_rows={refreshed_row_count}")
    print(f"vir_latest_snapshot_date={latest_snapshot}")
    print(f"vir_history_csv={output_path}")
    return output_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    workbook = _resolve_workbook(args.workbook)
    vir_workbooks = _resolve_equity_model_workbooks(args.vir_workbook)
    print(f"workbook={workbook}")
    _refresh_vir_history(args.vir_csv, vir_workbooks)

    outputs = build_fund_weights_vir_algo_multisignal(
        workbook_path=workbook,
        output_dir=args.output_dir,
        vir_csv=args.vir_csv,
        algo_workbooks=args.algo_workbooks,
        combined_output=args.fund_output,
    )

    print(f"fund_summary_csv={outputs['fund_summary']}")
    print(f"fund_weights_vir_algo_multisignal_csv={outputs['fund_weights_vir_algo_multisignal']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
