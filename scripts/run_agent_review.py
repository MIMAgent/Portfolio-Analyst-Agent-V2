"""Run the LLM-backed Portfolio Analyst Agent review loop."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.agent_runtime import run_fund  # noqa: E402
from portfolio_analyst_agent.agent_runtime.llm_client import AnthropicMessagesClient, BedrockClaudeClient  # noqa: E402
from portfolio_analyst_agent.fund_review import DEFAULT_FUND_ORDER  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Model 1 LLM agent review loop.")
    parser.add_argument("--fund", action="append", help="Fund(s) to review. Repeat for multiple funds.")
    parser.add_argument("--snapshot-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    parser.add_argument("--as-of-date", required=True, help="As-of date in YYYY-MM-DD format.")
    parser.add_argument("--output-root", default="artifacts/monthly_review", help="Output root for artifacts.")
    parser.add_argument("--run-mode", default="ad_hoc", choices=["ad_hoc", "live_monthly", "historical_replay"])
    parser.add_argument("--provider", default="bedrock", choices=["bedrock", "anthropic"], help="LLM provider.")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region for Bedrock.")
    parser.add_argument("--aws-profile", default=None, help="Optional AWS profile for Bedrock credentials.")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Anthropic model name.")
    parser.add_argument("--bedrock-read-timeout", type=int, default=180, help="Bedrock read timeout in seconds.")
    parser.add_argument("--max-output-tokens", type=int, default=8192, help="Maximum output tokens per LLM turn.")
    parser.add_argument("--include-sizing", action="store_true", help="Require write_sizing_considerations.")
    parser.add_argument("--include-challenge", action="store_true", help="Require write_challenge_brief.")
    parser.add_argument(
        "--include-proposed-memory",
        action="store_true",
        help="Shadow/test mode: allow recall_memory to return proposed memory rows alongside approved/applied rows.",
    )
    parser.add_argument("--max-turns", type=int, default=20)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.provider == "bedrock":
        model = args.model if args.model != "claude-sonnet-4-5" else "anthropic.claude-sonnet-4-6"
        client = BedrockClaudeClient(
            model=model,
            region_name=args.aws_region,
            profile_name=args.aws_profile,
            read_timeout=args.bedrock_read_timeout,
            max_tokens=args.max_output_tokens,
        )
    else:
        client = AnthropicMessagesClient(model=args.model, max_tokens=args.max_output_tokens)
    required_writes = {"write_change_brief"}
    if args.include_sizing:
        required_writes.add("write_sizing_considerations")
    if args.include_challenge:
        required_writes.add("write_challenge_brief")
    funds = args.fund or list(DEFAULT_FUND_ORDER)
    for fund in funds:
        result = run_fund(
            fund=fund,
            snapshot_date=args.snapshot_date,
            as_of_date=args.as_of_date,
            llm_client=client,
            output_root=args.output_root,
            run_mode=args.run_mode,
            max_turns=args.max_turns,
            required_writes=required_writes,
            include_proposed_memory=args.include_proposed_memory,
        )
        print(f"fund={result.fund}")
        print(f"review_run_id={result.review_run_id}")
        print(f"trace_path={result.trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
