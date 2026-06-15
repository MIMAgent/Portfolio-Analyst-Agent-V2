"""Build the canonical consolidated equity VIR dataset used by the repo."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.equity_history import (  # noqa: E402
    DEFAULT_EQUITY_VIR_BASE_HISTORY_CSV,
    DEFAULT_EQUITY_VIR_DATASET_CSV,
    build_equity_vir_dataset,
    discover_equity_model_workbooks,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the canonical consolidated equity VIR dataset from base history plus monthly Equity Model workbooks."
    )
    parser.add_argument(
        "--base-history-csv",
        default=str(DEFAULT_EQUITY_VIR_BASE_HISTORY_CSV),
        help="Base normalized equity VIR history CSV, typically the pre-March history source.",
    )
    parser.add_argument(
        "--monthly-workbooks",
        nargs="*",
        default=None,
        help="Monthly Equity Model workbooks to merge in. Defaults to all data/*/*Equity Model.xlsx files.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_EQUITY_VIR_DATASET_CSV),
        help="Output path for the canonical consolidated equity VIR dataset.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    monthly_workbooks = (
        [Path(path).resolve() for path in args.monthly_workbooks]
        if args.monthly_workbooks
        else discover_equity_model_workbooks(ROOT / "data")
    )

    output_path, records = build_equity_vir_dataset(
        base_history_csv=args.base_history_csv,
        monthly_workbooks=monthly_workbooks,
        output_csv=args.output,
        include_existing_output=True,
    )

    snapshot_dates = sorted({record.snapshot_date for record in records})
    latest_snapshot = snapshot_dates[-1].isoformat() if snapshot_dates else ""
    earliest_snapshot = snapshot_dates[0].isoformat() if snapshot_dates else ""

    print(f"base_history_csv={Path(args.base_history_csv).resolve()}")
    print(f"monthly_workbook_count={len(monthly_workbooks)}")
    print(f"monthly_workbooks={','.join(str(path) for path in monthly_workbooks)}")
    print(f"row_count={len(records)}")
    print(f"snapshot_count={len(snapshot_dates)}")
    print(f"earliest_snapshot_date={earliest_snapshot}")
    print(f"latest_snapshot_date={latest_snapshot}")
    print(f"output_csv={output_path}")
    print(f"output_zip={output_path}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
