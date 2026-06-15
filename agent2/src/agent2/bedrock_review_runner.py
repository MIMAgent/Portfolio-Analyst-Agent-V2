"""Run one compact agent2 review through Bedrock and save all artifacts."""

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

GENERIC_PM_QUESTION_PATTERNS = (
    "is this still intentional",
    "why is this still overweight",
    "why is the fund still overweight",
    "why is this still underweight",
    "why is the fund still underweight",
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
    max_output_tokens: int = 5000,
    read_timeout: int = 180,
) -> dict[str, Any]:
    _load_repo_env(REPO_ROOT / ".env")
    review_packet = build_review_packet(
        fund=fund,
        logical_snapshot_date=logical_snapshot_date,
        review_date=review_date,
    )
    evidence_pack = build_evidence_pack(review_packet)
    system_prompt = build_review_system_prompt()
    user_prompt = build_review_user_prompt(evidence_pack)

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
    if parsed_json is not None:
        try:
            parsed_json = _validate_review_payload(parsed_json)
        except ValueError as exc:
            validation_error = str(exc)
            parsed_json = None

    raw_response_path = output_dir / "bedrock_raw_response.json"
    raw_response_path.write_text(json.dumps(response.raw, indent=2, default=str), encoding="utf-8")
    (output_dir / "bedrock_response.txt").write_text(response_text, encoding="utf-8")
    if parsed_json is not None:
        (output_dir / "bedrock_review.json").write_text(json.dumps(parsed_json, indent=2), encoding="utf-8")
        (output_dir / "bedrock_review.md").write_text(_render_markdown_review(parsed_json, review_packet), encoding="utf-8")
    elif validation_error:
        (output_dir / "bedrock_validation_error.txt").write_text(validation_error, encoding="utf-8")

    run_manifest = {
        "fund": fund,
        "logical_snapshot_date": logical_snapshot_date,
        "review_date": review_date,
        "model": model,
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


def _collect_text(blocks: list[dict[str, Any]]) -> str:
    parts = []
    for block in blocks:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(part for part in parts if part).strip()


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


def _parse_json_response(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _validate_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required_list_sections = (
        "current_positioning",
        "what_changed",
        "bull_case",
        "bear_case",
        "devils_advocate",
        "challenge_brief",
        "pm_questions",
        "follow_up",
        "dashboard_highlights",
    )
    if not isinstance(payload, dict):
        raise ValueError("Bedrock review payload must be a JSON object.")
    executive_summary = payload.get("executive_summary")
    if not isinstance(executive_summary, str) or not executive_summary.strip():
        raise ValueError("Missing executive_summary in Bedrock review payload.")
    for section in required_list_sections:
        rows = payload.get(section)
        if not isinstance(rows, list):
            raise ValueError(f"Section {section!r} must be a list.")
    challenge_brief = payload.get("challenge_brief", [])
    if not challenge_brief:
        raise ValueError("challenge_brief must contain at least one PM decision-card item.")
    for index, item in enumerate(challenge_brief):
        if not isinstance(item, dict):
            raise ValueError(f"challenge_brief[{index}] must be an object.")
        for field in (
            "label",
            "challenge_headline",
            "thesis_under_pressure",
            "positioning_tension",
            "model_signal_tension",
            "vir_decomposition_readthrough",
            "market_context_readthrough",
            "pm_decision_fork",
            "primary_pm_question",
            "evidence_needed_next",
            "source_quality",
        ):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"challenge_brief[{index}].{field} must be a non-empty string.")
        question = item.get("primary_pm_question", "").lower()
        if any(pattern in question for pattern in GENERIC_PM_QUESTION_PATTERNS):
            raise ValueError("challenge_brief contains an overly generic PM question.")
    return payload


def _approx_cost_usd(usage: dict[str, Any]) -> float | None:
    if not usage:
        return None
    input_tokens = _usage_int(usage, "inputTokens", "input_tokens")
    output_tokens = _usage_int(usage, "outputTokens", "output_tokens")
    if input_tokens is None and output_tokens is None:
        return None
    return round(((input_tokens or 0) / 1_000_000) * 3 + ((output_tokens or 0) / 1_000_000) * 15, 4)


def _usage_int(usage: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = usage.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _render_markdown_review(review: dict[str, Any], review_packet: dict[str, Any]) -> str:
    header = review_packet.get("header", {})
    lines = [
        f"# Agent2 Review - {header.get('fund', '')}",
        "",
        f"- Review month: {header.get('snapshot_date', '')}",
        f"- Review date: {header.get('review_date', '')}",
        f"- Source snapshot date: {header.get('source_snapshot_date', '')}",
        "",
        "## Executive Summary",
        "",
        review.get("executive_summary", ""),
        "",
    ]
    lines.extend(_section_lines("Current Positioning", review.get("current_positioning", []), ("label", "view", "evidence")))
    lines.extend(_section_lines("What Changed", review.get("what_changed", []), ("label", "change", "why_it_matters")))
    lines.extend(_section_lines("Bull Case", review.get("bull_case", []), ("label", "statement")))
    lines.extend(_section_lines("Bear Case", review.get("bear_case", []), ("label", "statement")))
    lines.extend(_section_lines("Devil's Advocate", review.get("devils_advocate", []), ("label", "statement")))
    lines.extend(_challenge_brief_lines(review.get("challenge_brief", [])))
    lines.extend(_section_lines("PM Questions", review.get("pm_questions", []), ("label", "question", "why_now")))
    lines.extend(_section_lines("Follow Up", review.get("follow_up", []), ("label", "action")))
    lines.extend(_section_lines("Dashboard Highlights", review.get("dashboard_highlights", []), ("label", "highlight")))
    return "\n".join(lines).rstrip() + "\n"


def _section_lines(title: str, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[str]:
    lines = [f"## {title}", ""]
    for row in rows:
        first = row.get(fields[0], "")
        rest = [row.get(field, "") for field in fields[1:]]
        detail = " | ".join(value for value in rest if value)
        if detail:
            lines.append(f"- **{first}**: {detail}")
        else:
            lines.append(f"- **{first}**")
    lines.append("")
    return lines


def _challenge_brief_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Challenge Brief", ""]
    for row in rows:
        label = row.get("label", "")
        lines.extend([f"### {label}", ""])
        for field, title in (
            ("challenge_headline", "Headline"),
            ("thesis_under_pressure", "Thesis Under Pressure"),
            ("positioning_tension", "Positioning Tension"),
            ("model_signal_tension", "Model Signal Tension"),
            ("vir_decomposition_readthrough", "VIR Decomposition Readthrough"),
            ("market_context_readthrough", "Market Context Readthrough"),
            ("pm_decision_fork", "PM Decision Fork"),
            ("primary_pm_question", "Primary PM Question"),
            ("evidence_needed_next", "Evidence Needed Next"),
            ("source_quality", "Source Quality"),
        ):
            value = row.get(field, "")
            if value:
                lines.append(f"- **{title}:** {value}")
        lines.append("")
    return lines
