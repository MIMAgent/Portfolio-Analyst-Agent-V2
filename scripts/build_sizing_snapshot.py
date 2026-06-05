"""Build the monthly sizing artifact from the algo workbooks."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.algo_parser import parse_multiple_algo_workbooks  # noqa: E402
from portfolio_analyst_agent.sizing_snapshot import (  # noqa: E402
    build_sizing_snapshot,
    latest_signals_from_results,
    write_latest_signals_csv,
    write_snapshot_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the monthly sizing considerations snapshot.")
    parser.add_argument("workbooks", nargs="+", help="Path(s) to algo workbook files.")
    parser.add_argument(
        "--signals-output",
        default="artifacts/latest_algo_signals.csv",
        help="CSV output path for the latest algo signals.",
    )
    parser.add_argument(
        "--markdown-output",
        default="artifacts/sizing_considerations_snapshot.md",
        help="Markdown output path for the sizing snapshot.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of rows to show per ranking section.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    results = parse_multiple_algo_workbooks(args.workbooks)
    latest_signals = latest_signals_from_results(results)
    snapshot = build_sizing_snapshot(latest_signals, top_n=args.top_n)

    signals_path = write_latest_signals_csv(latest_signals, args.signals_output)
    markdown_path = write_snapshot_markdown(snapshot, args.markdown_output)

    print(f"snapshot_date={snapshot.snapshot_date.isoformat()}")
    print(f"latest_signal_count={len(latest_signals)}")
    print(f"signals_csv={signals_path}")
    print(f"markdown_snapshot={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
