"""CLI entrypoint for building the first agent2 review packet."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "agent2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent2.review_packet_builder import build_review_packet, write_review_packet  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a structured agent2 review packet for one fund.")
    parser.add_argument("--fund", required=True, help="Fund name, for example 'MStar US Equity'.")
    parser.add_argument(
        "--logical-snapshot-date",
        default="2026-05-31",
        help="Business snapshot month to label the packet with, even if source artifacts carry later processing dates.",
    )
    parser.add_argument(
        "--review-date",
        default="",
        help="Optional review date override. Defaults to today's date.",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Output path for the structured review packet JSON.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    packet = build_review_packet(
        fund=args.fund,
        logical_snapshot_date=args.logical_snapshot_date,
        review_date=args.review_date or None,
    )
    output_path = write_review_packet(packet, args.output_json)
    print(f"fund={packet['header']['fund']}")
    print(f"logical_snapshot_date={packet['header']['snapshot_date']}")
    print(f"source_snapshot_date={packet['header']['source_snapshot_date']}")
    print(f"material_position_count={len(packet['material_positions'])}")
    print(f"output_json={output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
