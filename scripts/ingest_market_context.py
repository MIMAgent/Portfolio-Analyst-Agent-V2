"""Ingest approved Markdown/text notes into monthly market-context CSV."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.market_context_ingest import IngestDefaults, ingest_market_context_documents  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build citable market context from approved source notes.")
    parser.add_argument("--input-dir", default="artifacts/market_context/source_docs")
    parser.add_argument("--output-csv", default="artifacts/market_context/monthly_market_context.csv")
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--source-label", default="Approved market context note")
    parser.add_argument("--source-date", default="")
    parser.add_argument("--scope-type", default="global")
    parser.add_argument("--scope-value", default="")
    parser.add_argument("--priority", default="3")
    parser.add_argument("--append", action="store_true", help="Append to existing CSV and dedupe by row_id.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = ingest_market_context_documents(
        input_dir=args.input_dir,
        output_csv=args.output_csv,
        defaults=IngestDefaults(
            snapshot_date=args.snapshot_date,
            as_of_date=args.as_of_date,
            source_label=args.source_label,
            source_date=args.source_date,
            scope_type=args.scope_type,
            scope_value=args.scope_value,
            priority=args.priority,
        ),
        append=args.append,
    )
    print(f"market_context_csv={result['output_csv']}")
    print(f"row_count={result['row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
