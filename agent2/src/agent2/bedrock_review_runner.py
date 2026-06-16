"""Run one agent2 review through Bedrock and save all artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

from .evidence_pack_builder import build_evidence_pack, write_evidence_pack
from .review_packet_builder import build_review_packet, write_review_packet
from .review_prompt import build_review_system_prompt, build_review_user_prompt


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_analyst_agent.agent_runtime.llm_client import BedrockClaudeClient  # noqa: E402

# Validation, parsing, and markdown rendering live in a dependency-free module
# so lightweight tooling can reuse them. Re-exported here for back-compat with
# existing imports (tests and callers import these from this module).
from .review_validation import (  # noqa: E402,F401
    ALLOWED_RECOMMENDED_ACTIONS,
    GENERIC_PM_QUESTION_PATTERNS,
    _approx_cost_usd,
    _collect_text,
    _parse_json_response,
    _render_markdown_review,
    _validate_review_payload,
)


def run_bedrock_review(
    *,
    fund: str,
    logical_snapshot_date: str,
    review_date: str,
    output_root: str | Path,
    model: str = "us.anthropic.claude-sonnet-4-6",
    region_name: str = "us-east-2",
    profile_name: str | None = None,
    output_style: str = "deep_challenge_memo",
    challenge_count_target: int = 4,
    max_output_tokens: int = 5000,
    read_timeout: int = 180,
) -> dict[str, Any]:
    _load_repo_env(REPO_ROOT / ".env")
    review_packet = build_review_packet(
        fund=fund,
        logical_snapshot_date=logical_snapshot_date,
        review_date=review_date,
    )
    evidence_pack = build_evidence_pack(
        review_packet,
        refresh_market_context=True,
        output_style=output_style,
        challenge_count_target=challenge_count_target,
    )
    system_prompt = build_review_system_prompt(output_style=output_style)
    user_prompt = build_review_user_prompt(evidence_pack, output_style=output_style)

    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_path = write_review_packet(review_packet, output_dir / "agent2_review_packet.json")
    evidence_path = write_evidence_pack(evidence_pack, output_dir / "evidence_pack.json")
    (output_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    (output_dir / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")

    client = BedrockClaudeClient(
        model=model,
        region_name=region_name,
        profile_name=profile_name,
        max_tokens=max_output_tokens,
        read_timeout=read_timeout,
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
        validation_error = "Bedrock response was not valid JSON, likely because the response was truncated or malformed."
    if parsed_json is not None:
        try:
            parsed_json = _validate_review_payload(parsed_json, output_style=output_style)
        except ValueError as exc:
            validation_error = str(exc)
            parsed_json = None

    raw_response_path = output_dir / "bedrock_raw_response.json"
    raw_response_path.write_text(json.dumps(response.raw, indent=2, default=str), encoding="utf-8")
    (output_dir / "bedrock_response.txt").write_text(response_text, encoding="utf-8")
    if parsed_json is not None:
        (output_dir / "bedrock_review.json").write_text(json.dumps(parsed_json, indent=2), encoding="utf-8")
        (output_dir / "bedrock_review.md").write_text(
            _render_markdown_review(parsed_json, review_packet, output_style=output_style),
            encoding="utf-8",
        )
    elif validation_error:
        (output_dir / "bedrock_validation_error.txt").write_text(validation_error, encoding="utf-8")

    run_manifest = {
        "fund": fund,
        "logical_snapshot_date": logical_snapshot_date,
        "review_date": review_date,
        "model": model,
        "output_style": output_style,
        "challenge_count_target": evidence_pack.get("run_goal", {}).get("challenge_count_target"),
        "region_name": region_name,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "artifacts": {
            "review_packet": packet_path.as_posix(),
            "evidence_pack": evidence_path.as_posix(),
            "system_prompt": (output_dir / "system_prompt.txt").as_posix(),
            "user_prompt": (output_dir / "user_prompt.txt").as_posix(),
            "bedrock_raw_response": raw_response_path.as_posix(),
            "bedrock_response_text": (output_dir / "bedrock_response.txt").as_posix(),
            "bedrock_review_json": (output_dir / "bedrock_review.json").as_posix() if parsed_json is not None else "",
            "bedrock_review_markdown": (output_dir / "bedrock_review.md").as_posix() if parsed_json is not None else "",
            "bedrock_validation_error": (output_dir / "bedrock_validation_error.txt").as_posix() if validation_error else "",
        },
        "usage": response.usage,
        "approx_cost_usd": _approx_cost_usd(response.usage),
        "parsed_json_ok": parsed_json is not None,
        "validation_error": validation_error,
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    return run_manifest


def _load_repo_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value
    os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
