"""Run the deterministic Model 1 monthly review harness."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.monthly_review import run_monthly_review, run_monthly_review_batch  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deterministic monthly review harness.")
    parser.add_argument(
        "--fund",
        action="append",
        help="Fund(s) to review. Repeat the flag for multiple funds. Defaults to the full DEFAULT_FUND_ORDER batch.",
    )
    parser.add_argument(
        "--snapshot-date",
        default=None,
        help="Optional snapshot date override in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--as-of-date",
        required=True,
        help="As-of date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--output-root",
        default="artifacts/monthly_review",
        help="Output directory root.",
    )
    parser.add_argument(
        "--run-mode",
        default="ad_hoc",
        choices=["ad_hoc", "live_monthly", "historical_replay"],
        help="Run mode recorded in the output metadata.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.fund and len(args.fund) == 1:
        result = run_monthly_review(
            fund=args.fund[0],
            snapshot_date=args.snapshot_date,
            as_of_date=args.as_of_date,
            output_root=args.output_root,
            run_mode=args.run_mode,
        )
        for key, value in result.items():
            print(f"{key}={value}")
        return 0

    batch = run_monthly_review_batch(
        funds=args.fund,
        snapshot_date=args.snapshot_date,
        as_of_date=args.as_of_date,
        output_root=args.output_root,
        run_mode=args.run_mode,
    )
    print(f"fund_count={batch['fund_count']}")
    print(f"batch_index={Path(args.output_root) / (args.snapshot_date or batch['results'][0]['snapshot_date']) / 'batch_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
