"""CLI for running one compact agent2 review through Bedrock."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "agent2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent2.bedrock_review_runner import run_bedrock_review  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical agent2 deep monthly review through Bedrock.")
    parser.add_argument("--fund", required=True, help="Fund name.")
    parser.add_argument("--logical-snapshot-date", default="2026-05-31", help="Business month to label the run.")
    parser.add_argument("--review-date", default="", help="Optional review date override.")
    parser.add_argument("--output-root", required=True, help="Directory to save all run artifacts.")
    parser.add_argument("--model", default="us.anthropic.claude-sonnet-4-6", help="Bedrock model or inference profile id.")
    parser.add_argument("--aws-region", default="us-east-2", help="AWS region.")
    parser.add_argument("--aws-profile", default=None, help="Optional AWS profile.")
    parser.add_argument(
        "--challenge-count-target",
        type=int,
        default=4,
        help="Number of top challenges to include in the deep memo.",
    )
    parser.add_argument("--max-output-tokens", type=int, default=5000, help="Max model output tokens.")
    parser.add_argument("--bedrock-read-timeout", type=int, default=180, help="Bedrock read timeout.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    manifest = run_bedrock_review(
        fund=args.fund,
        logical_snapshot_date=args.logical_snapshot_date,
        review_date=args.review_date or args.logical_snapshot_date,
        output_root=args.output_root,
        model=args.model,
        region_name=args.aws_region,
        profile_name=args.aws_profile,
        challenge_count_target=args.challenge_count_target,
        max_output_tokens=args.max_output_tokens,
        read_timeout=args.bedrock_read_timeout,
    )
    print(f"fund={manifest['fund']}")
    print(f"logical_snapshot_date={manifest['logical_snapshot_date']}")
    print(f"model={manifest['model']}")
    print(f"output_style={manifest['output_style']}")
    print(f"challenge_count_target={manifest['challenge_count_target']}")
    print(f"parsed_json_ok={manifest['parsed_json_ok']}")
    print(f"approx_cost_usd={manifest['approx_cost_usd']}")
    print(f"run_manifest={Path(args.output_root, 'run_manifest.json').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
