"""Build an analyst-facing markdown summary from the combined fund weights/VIR/algo CSV."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.fund_weights_summary import (  # noqa: E402
    load_fund_combined_rows,
    write_fund_weights_summary_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an analyst-facing markdown summary from the combined fund weights/VIR/algo CSV."
    )
    parser.add_argument(
        "--input-csv",
        default="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
        help="Combined fund weights/VIR/algo CSV (canonical multisignal output).",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/rolled_exposures/fund_weights_vir_algo_summary.md",
        help="Markdown output path.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    rows = load_fund_combined_rows(args.input_csv)
    output_path = write_fund_weights_summary_markdown(rows, args.output_md)

    print(f"summary_row_count={len(rows)}")
    print(f"summary_markdown={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
