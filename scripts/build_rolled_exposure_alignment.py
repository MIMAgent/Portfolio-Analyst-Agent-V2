"""Cross-reference rolled exposure outputs to VIR rows and latest algo signals."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.rolled_exposure_alignment import (  # noqa: E402
    build_account_exposure_alignment,
    build_fund_exposure_alignment,
    write_alignment_csv,
)
from portfolio_analyst_agent.equity_history import DEFAULT_EQUITY_VIR_DATASET_CSV  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-reference rolled exposure summaries to VIR rows and latest algo signals."
    )
    parser.add_argument(
        "--account-summary-csv",
        default="artifacts/rolled_exposures/account_rolled_exposure_summary.csv",
        help="Account rolled exposure summary CSV.",
    )
    parser.add_argument(
        "--fund-summary-csv",
        default="artifacts/rolled_exposures/fund_rolled_exposure_summary.csv",
        help="Fund rolled exposure summary CSV.",
    )
    parser.add_argument(
        "--vir-csv",
        default=str(DEFAULT_EQUITY_VIR_DATASET_CSV),
        help="Normalized VIR CSV to attach STF and rank fields.",
    )
    parser.add_argument(
        "--algo-workbooks",
        nargs="*",
        help="Monthly algo workbook paths used to attach latest algo signals.",
    )
    parser.add_argument(
        "--account-output",
        default="artifacts/rolled_exposures/account_vir_algo_alignment.csv",
        help="Output CSV for account-level alignment rows.",
    )
    parser.add_argument(
        "--fund-output",
        default="artifacts/rolled_exposures/fund_vir_algo_alignment.csv",
        help="Output CSV for fund-level alignment rows.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    account_rows = build_account_exposure_alignment(
        account_summary_csv=args.account_summary_csv,
        vir_csv=args.vir_csv,
        algo_workbooks=args.algo_workbooks,
    )
    fund_rows = build_fund_exposure_alignment(
        fund_summary_csv=args.fund_summary_csv,
        vir_csv=args.vir_csv,
        algo_workbooks=args.algo_workbooks,
    )

    account_path = write_alignment_csv(account_rows, args.account_output)
    fund_path = write_alignment_csv(fund_rows, args.fund_output)

    print(f"account_alignment_count={len(account_rows)}")
    print(f"account_alignment_csv={account_path}")
    print(f"fund_alignment_count={len(fund_rows)}")
    print(f"fund_alignment_csv={fund_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
