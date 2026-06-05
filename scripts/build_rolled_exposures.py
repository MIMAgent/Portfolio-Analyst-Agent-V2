"""Build account-level and fund-level rolled ACID exposure CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.rolled_exposures import build_rolled_exposures  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build rolled account and fund ACID exposures from the Portfolio and Full_lookthrough tabs."
    )
    parser.add_argument("workbook", help="Path to the RMv2 .xlsm workbook.")
    parser.add_argument(
        "--output-dir",
        default="artifacts/rolled_exposures",
        help="Directory where the output CSV files should be written.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    outputs = build_rolled_exposures(args.workbook, args.output_dir)
    for name, path in outputs.items():
        print(f"{name}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
