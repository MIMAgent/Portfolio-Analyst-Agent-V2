"""Build one fund-level CSV that combines rolled weights, VIR, and algo signals."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.fund_weights_vir_algo import build_fund_weights_vir_algo  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build one fund-level CSV that combines rolled exposures, VIR fields, and latest algo signals."
    )
    parser.add_argument(
        "workbook",
        nargs="?",
        default="data/RMv2_PCT_Mstar_funds_2026-04-06.xlsm",
        help="Path to the RMv2 .xlsm workbook.",
    )
    parser.add_argument(
        "--vir-csv",
        default="artifacts/equity_vir_history.csv",
        help="Normalized VIR CSV used to attach STF and rank fields.",
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
        default="artifacts/rolled_exposures/fund_weights_vir_algo.csv",
        help="Output CSV for the combined fund-level rows.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    outputs = build_fund_weights_vir_algo(
        workbook_path=args.workbook,
        output_dir=args.output_dir,
        vir_csv=args.vir_csv,
        algo_workbooks=args.algo_workbooks,
        combined_output=args.fund_output,
    )

    print(f"fund_summary_csv={outputs['fund_summary']}")
    print(f"fund_weights_vir_algo_csv={outputs['fund_weights_vir_algo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
