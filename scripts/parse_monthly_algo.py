"""CLI entrypoint for normalizing the monthly algo workbooks."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.algo_parser import (  # noqa: E402
    parse_multiple_algo_workbooks,
    write_records_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse monthly algo workbooks into normalized ACID-level rows.")
    parser.add_argument("workbooks", nargs="+", help="Path(s) to algo workbook files.")
    parser.add_argument(
        "--output",
        help="Optional CSV output path for the combined normalized records.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    results = parse_multiple_algo_workbooks(args.workbooks)

    for result in results:
        summary = result.summary()
        print(f"{summary['source_file']} :: perspective={summary['algo_perspective']} :: snapshot_date={summary['snapshot_date']}")
        print(f"  record_count={summary['record_count']}")
        print(f"  counts_by_sheet={summary['counts_by_sheet']}")
        print(f"  counts_by_metric={summary['counts_by_metric']}")

    if args.output:
        combined_records = [record for result in results for record in result.records]
        output_path = write_records_csv(combined_records, args.output)
        print(f"wrote {len(combined_records)} records to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
