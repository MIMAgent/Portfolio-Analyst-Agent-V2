"""Build a one-by-one fund review checklist and workbook from current artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.fund_review import build_fund_review_pack  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a checklist and markdown workbook for reviewing the 9 funds one by one."
    )
    parser.add_argument(
        "--combined-csv",
        default="artifacts/rolled_exposures/fund_weights_vir_algo.csv",
        help="Combined fund/VIR/algo CSV to review.",
    )
    parser.add_argument(
        "--coverage-csv",
        default="artifacts/rolled_exposures/fund_rollthrough_coverage.csv",
        help="Fund coverage CSV used to prefill match metrics.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/fund_review",
        help="Directory where the review checklist and workbook should be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    outputs = build_fund_review_pack(
        combined_csv=args.combined_csv,
        coverage_csv=args.coverage_csv,
        output_dir=args.output_dir,
    )

    print(f"checklist_csv={outputs['checklist_csv']}")
    print(f"workbook_md={outputs['workbook_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
