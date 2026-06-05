"""Search approved web sources and cache citable market-context rows."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio_analyst_agent.market_context_search import SearchDefaults, search_market_context_web  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--fund", default="")
    parser.add_argument("--acid", default="")
    parser.add_argument("--comparison-group", default="")
    parser.add_argument("--output-csv", default="artifacts/market_context/monthly_market_context.csv")
    parser.add_argument("--max-results", type=int, default=6)
    parser.add_argument("--max-sources", type=int, default=4)
    parser.add_argument("--replace", action="store_true", help="Replace output CSV instead of appending.")
    args = parser.parse_args()

    result = search_market_context_web(
        query=args.query,
        defaults=SearchDefaults(
            snapshot_date=args.snapshot_date,
            as_of_date=args.as_of_date,
            fund=args.fund,
            acid=args.acid,
            comparison_group=args.comparison_group,
        ),
        output_csv=args.output_csv,
        max_results=args.max_results,
        max_sources=args.max_sources,
        append=not args.replace,
    )
    print(f"context_status={result['context_status']}")
    print(f"new_row_count={result['new_row_count']}")
    print(f"total_row_count={result['total_row_count']}")
    print(f"output_csv={result['output_csv']}")
    print(f"searched_domains={','.join(result['searched_domains'])}")
    for diagnostic in result.get("run_metadata", {}).get("source_diagnostics", []):
        print(
            "source_diagnostic="
            f"source_id={diagnostic.get('source_id', '')},"
            f"domain={diagnostic.get('domain', '')},"
            f"search_result_count={diagnostic.get('search_result_count', 0)},"
            f"accepted_search_result_count={diagnostic.get('accepted_search_result_count', 0)},"
            f"fallback_row_count={diagnostic.get('fallback_row_count', 0)},"
            f"fallback_status={diagnostic.get('fallback_status', '')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
