"""Normalize the equity VIR history workbook into trend-ready rows."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.equity_history import (  # noqa: E402
    parse_equity_history_workbook,
    write_equity_history_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse the equity VIR history workbook into canonical trend rows.")
    parser.add_argument("workbook", help="Path to the VIR history workbook.")
    parser.add_argument(
        "--output",
        default="artifacts/equity_vir_history.csv",
        help="CSV output path for normalized history rows.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = parse_equity_history_workbook(args.workbook)
    summary = result.summary()
    output_path = write_equity_history_csv(result.records, args.output)

    print(f"source_file={summary['source_file']}")
    print(f"row_count={summary['row_count']}")
    print(f"snapshot_count={summary['snapshot_count']}")
    print(f"acid_count={summary['acid_count']}")
    print(f"latest_snapshot_date={summary['latest_snapshot_date']}")
    print(f"output_csv={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
