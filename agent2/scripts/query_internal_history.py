"""CLI for querying structured internal-history records produced by agent2 ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "agent2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent2.internal_history_retrieval import load_internal_history, retrieve_relevant_history  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query agent2 internal-history records.")
    parser.add_argument("--input-json", required=True, help="Structured internal-history JSON path.")
    parser.add_argument("--fund", required=True, help="Fund name.")
    parser.add_argument("--query", default="", help="Free-text query.")
    parser.add_argument("--theme-id", action="append", default=[], help="Theme id filter. Repeat for multiple.")
    parser.add_argument("--section-key", action="append", default=[], help="Section key filter. Repeat for multiple.")
    parser.add_argument("--before-date", default="", help="Only search documents before this date.")
    parser.add_argument("--max-sections", type=int, default=8, help="Maximum matched sections to return.")
    parser.add_argument("--output-json", default="", help="Optional output JSON path.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = load_internal_history(args.input_json)
    result = retrieve_relevant_history(
        payload,
        fund=args.fund,
        query=args.query,
        theme_ids=args.theme_id,
        section_keys=args.section_key,
        before_date=args.before_date or None,
        max_sections=args.max_sections,
    )
    text = json.dumps(result, indent=2)
    if args.output_json:
        Path(args.output_json).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
