"""Re-run a Bedrock review from an already-built evidence pack.

This is the cheap prompt-iteration loop. The expensive, data-heavy work
(building the review packet and evidence pack from raw exposures / VIR / risk
files) is skipped entirely -- we reuse a previously saved ``evidence_pack.json``
and only re-send it to Bedrock with the current prompt. That isolates the
prompt as the single variable when tuning challenge-brief output quality.

It is deliberately dependency-light: it loads ``review_prompt``,
``review_validation``, and ``llm_client`` by file path, bypassing every package
``__init__`` so it needs only the standard library plus ``boto3`` (already
present in AWS CloudShell). No pandas / openpyxl / repo install required.

It runs in two layouts:
  * inside the repo checkout (finds the modules in their normal locations), or
  * as a flat bundle (all the .py files and evidence_pack.json sit next to it).

Use ``--dry-run`` to assemble and write the prompts without calling Bedrock
(no AWS, no spend) -- handy for sanity-checking before a real run.

Example (AWS CloudShell, SSO creds already present):

    python3 rerun_review_from_evidence.py --output-root ./out --max-output-tokens 12000
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


SCRIPT_DIR = Path(__file__).resolve().parent
# Repo root when running from agent2/scripts/ ; harmless if it doesn't exist.
REPO_ROOT = SCRIPT_DIR.parents[1]


def _load_module_by_path(name: str, *candidates: Path) -> ModuleType:
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    searched = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(f"Could not locate {name}.py. Looked in:\n  {searched}")


def _first_existing(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


# review_prompt and review_validation: flat bundle (next to script) or in-repo.
_AGENT2 = REPO_ROOT / "agent2" / "src" / "agent2"
review_prompt = _load_module_by_path(
    "review_prompt",
    SCRIPT_DIR / "review_prompt.py",
    _AGENT2 / "review_prompt.py",
)
review_validation = _load_module_by_path(
    "review_validation",
    SCRIPT_DIR / "review_validation.py",
    _AGENT2 / "review_validation.py",
)

build_review_system_prompt = review_prompt.build_review_system_prompt
build_review_user_prompt = review_prompt.build_review_user_prompt
_collect_text = review_validation._collect_text
_parse_json_response = review_validation._parse_json_response
_validate_review_payload = review_validation._validate_review_payload
_render_markdown_review = review_validation._render_markdown_review
_approx_cost_usd = review_validation._approx_cost_usd

DEFAULT_EVIDENCE_PACK = _first_existing(
    SCRIPT_DIR / "evidence_pack.json",
    REPO_ROOT
    / "agent2"
    / "data"
    / "bedrock_runs"
    / "2026-05-31"
    / "mstar-us-equity-live-2026-06-15-deepmemo-12k-top4"
    / "evidence_pack.json",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Re-run an agent2 review from a saved evidence pack.")
    parser.add_argument(
        "--evidence-pack",
        default=str(DEFAULT_EVIDENCE_PACK) if DEFAULT_EVIDENCE_PACK else None,
        required=DEFAULT_EVIDENCE_PACK is None,
        help="Path to a previously saved evidence_pack.json.",
    )
    parser.add_argument("--output-root", required=True, help="Directory to save the rerun artifacts.")
    parser.add_argument(
        "--output-style",
        default="deep_challenge_memo",
        choices=("deep_challenge_memo", "challenge_cards"),
        help="Review output mode. Deep memo is the default.",
    )
    parser.add_argument("--model", default="us.anthropic.claude-sonnet-4-6", help="Bedrock model or inference profile id.")
    parser.add_argument("--aws-region", default="us-east-2", help="AWS region.")
    parser.add_argument("--aws-profile", default=None, help="Optional AWS profile.")
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=12000,
        help="Max model output tokens. Deep memos need headroom; the prior live run used ~7.2k.",
    )
    parser.add_argument("--bedrock-read-timeout", type=int, default=180, help="Bedrock read timeout.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Assemble and write the prompts but do not call Bedrock (no AWS, no spend).",
    )
    return parser


def _load_bedrock_client_class():
    """Load BedrockClaudeClient by path so we skip the heavy package __init__."""
    module = _load_module_by_path(
        "paa_llm_client",
        SCRIPT_DIR / "llm_client.py",
        REPO_ROOT / "src" / "portfolio_analyst_agent" / "agent_runtime" / "llm_client.py",
    )
    return module.BedrockClaudeClient


def main() -> int:
    args = build_parser().parse_args()

    evidence_path = Path(args.evidence_pack)
    if not evidence_path.exists():
        print(f"ERROR: evidence pack not found: {evidence_path}", file=sys.stderr)
        return 2
    evidence_pack = json.loads(evidence_path.read_text(encoding="utf-8"))

    output_dir = Path(args.output_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = build_review_system_prompt(output_style=args.output_style)
    user_prompt = build_review_user_prompt(evidence_pack, output_style=args.output_style)
    (output_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    (output_dir / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")

    if args.dry_run:
        print("dry_run=True (no Bedrock call)")
        print(f"evidence_pack={evidence_path.as_posix()}")
        print(f"output_style={args.output_style}")
        print(f"system_prompt_chars={len(system_prompt)}")
        print(f"user_prompt_chars={len(user_prompt)}")
        print(f"prompts_written_to={output_dir.as_posix()}")
        return 0

    BedrockClaudeClient = _load_bedrock_client_class()
    client = BedrockClaudeClient(
        model=args.model,
        region_name=args.aws_region,
        profile_name=args.aws_profile,
        max_tokens=args.max_output_tokens,
        read_timeout=args.bedrock_read_timeout,
    )
    response = client.send(
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[],
    )

    response_text = _collect_text(response.content)
    parsed_json = _parse_json_response(response_text)
    validation_error = ""
    if parsed_json is None:
        validation_error = "Bedrock response was not valid JSON (likely truncated -- raise --max-output-tokens)."
    else:
        try:
            parsed_json = _validate_review_payload(parsed_json, output_style=args.output_style)
        except ValueError as exc:
            validation_error = str(exc)
            parsed_json = None

    (output_dir / "bedrock_raw_response.json").write_text(json.dumps(response.raw, indent=2, default=str), encoding="utf-8")
    (output_dir / "bedrock_response.txt").write_text(response_text, encoding="utf-8")
    if parsed_json is not None:
        (output_dir / "bedrock_review.json").write_text(json.dumps(parsed_json, indent=2), encoding="utf-8")
        review_packet = {"header": evidence_pack.get("header", {})}
        (output_dir / "bedrock_review.md").write_text(
            _render_markdown_review(parsed_json, review_packet, output_style=args.output_style),
            encoding="utf-8",
        )
    elif validation_error:
        (output_dir / "bedrock_validation_error.txt").write_text(validation_error, encoding="utf-8")

    manifest = {
        "rerun_from_evidence_pack": evidence_path.as_posix(),
        "output_style": args.output_style,
        "model": args.model,
        "region_name": args.aws_region,
        "max_output_tokens": args.max_output_tokens,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "usage": response.usage,
        "approx_cost_usd": _approx_cost_usd(response.usage),
        "parsed_json_ok": parsed_json is not None,
        "validation_error": validation_error,
    }
    (output_dir / "rerun_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"evidence_pack={evidence_path.as_posix()}")
    print(f"output_style={args.output_style}")
    print(f"parsed_json_ok={parsed_json is not None}")
    print(f"approx_cost_usd={manifest['approx_cost_usd']}")
    if validation_error:
        print(f"validation_error={validation_error}")
    print(f"output_dir={output_dir.as_posix()}")
    return 0 if parsed_json is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
