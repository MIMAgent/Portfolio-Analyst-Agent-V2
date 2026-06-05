"""Print the Model 1 fund snapshot payload as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.agent_tools import get_fund_snapshot  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read a fund snapshot from the combined alignment CSV.")
    parser.add_argument("fund", help="Fund name to load.")
    parser.add_argument("--snapshot-date", help="Snapshot date to load. Defaults to latest on or before as-of date.")
    parser.add_argument("--as-of-date", required=True, help="As-of date used for replay-safe retrieval.")
    parser.add_argument(
        "--alignment-csv",
        default="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
        help="Combined fund/VIR/algo alignment CSV.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = get_fund_snapshot(
        fund=args.fund,
        snapshot_date=args.snapshot_date,
        as_of_date=args.as_of_date,
        alignment_csv=args.alignment_csv,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
