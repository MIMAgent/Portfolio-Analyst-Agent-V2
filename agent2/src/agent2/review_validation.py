"""Validation and rendering helpers for agent2 Bedrock reviews.

This module is intentionally dependency-free (standard library only) and has no
relative imports, so it can be reused by the data-heavy pipeline AND loaded
standalone by lightweight tooling (e.g. the prompt-iteration rerun script that
runs in environments without pandas/openpyxl). Keep it that way: do not import
the evidence/packet builders or the LLM client here.
"""

from __future__ import annotations

import json
from typing import Any


GENERIC_PM_QUESTION_PATTERNS = (
    "is this still intentional",
    "why is this still overweight",
    "why is the fund still overweight",
    "why is this still underweight",
    "why is the fund still underweight",
)

# Closed vocabulary of process-level review actions. Keeps the agent within the
# documented non-prescriptive line: it may frame a review fork, but must not
# recommend a trade, direction, or target weight. See
# agent2/AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md and
# docs/PM_CHALLENGE_CARD_CONTRACT_V1.md.
ALLOWED_RECOMMENDED_ACTIONS = frozenset(
    {
        "REVIEW AT IC",
        "DOCUMENT",
        "DOCUMENT OR RESIZE",
        "DEFEND OR RESIZE",
        "OFFSET",
        "WATCH",
    }
)


def _collect_text(blocks: list[dict[str, Any]]) -> str:
    parts = []
    for block in blocks:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(part for part in parts if part).strip()


def _parse_json_response(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _validate_review_payload(payload: dict[str, Any], output_style: str = "deep_challenge_memo") -> dict[str, Any]:
    required_list_sections = (
        "key_insights",
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
    key_insights = payload.get("key_insights", [])
    if len(key_insights) < 3:
        raise ValueError("key_insights must contain at least 3 concise PM-useful insights.")
    for index, item in enumerate(key_insights):
        if not isinstance(item, dict):
            raise ValueError(f"key_insights[{index}] must be an object.")
        for field in ("label", "insight", "why_it_matters"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"key_insights[{index}].{field} must be a non-empty string.")
    for index, item in enumerate(challenge_brief):
        if not isinstance(item, dict):
            raise ValueError(f"challenge_brief[{index}] must be an object.")
        required_fields = [
            "label",
            "challenge_headline",
            "thesis_under_pressure",
            "positioning_tension",
            "model_signal_tension",
            "vir_decomposition_readthrough",
            "market_context_readthrough",
            "measured_risk_readthrough",
            "pm_decision_fork",
            "primary_pm_question",
            "evidence_needed_next",
            "source_quality",
        ]
        if output_style == "deep_challenge_memo":
            required_fields[8:8] = [
                "descriptor",
                "exact_holdings_causing_it",
                "exact_vir_algo_decomp_explanation",
                "exact_risk_contribution",
                "exact_internal_research_excerpt",
                "exact_external_market_context",
                "bull_case",
                "bear_case",
                "devils_advocate",
                "what_would_change_my_mind",
                "recommended_action",
                "confidence",
            ]
        for field in required_fields:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"challenge_brief[{index}].{field} must be a non-empty string.")
        question = item.get("primary_pm_question", "").lower()
        if any(pattern in question for pattern in GENERIC_PM_QUESTION_PATTERNS):
            raise ValueError("challenge_brief contains an overly generic PM question.")
        if output_style == "deep_challenge_memo":
            action = item.get("recommended_action", "").strip().upper()
            if action not in ALLOWED_RECOMMENDED_ACTIONS:
                raise ValueError(
                    "challenge_brief recommended_action must be one of "
                    f"{sorted(ALLOWED_RECOMMENDED_ACTIONS)} to stay within the non-prescriptive policy."
                )
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


def _render_markdown_review(
    review: dict[str, Any],
    review_packet: dict[str, Any],
    output_style: str = "deep_challenge_memo",
) -> str:
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
    lines.extend(_section_lines("Key Insights", review.get("key_insights", []), ("label", "insight", "why_it_matters")))
    lines.extend(_challenge_brief_lines(review.get("challenge_brief", []), output_style=output_style))
    lines.extend(_section_lines("PM Questions", review.get("pm_questions", []), ("label", "question", "why_now")))
    lines.extend(_section_lines("Follow Up", review.get("follow_up", []), ("label", "action", "why_it_matters")))
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


def _challenge_brief_lines(rows: list[dict[str, Any]], output_style: str = "deep_challenge_memo") -> list[str]:
    lines = ["## Challenge Brief", ""]
    for row in rows:
        label = row.get("label", "")
        lines.extend([f"### {label}", ""])
        challenge_fields = [
            ("challenge_headline", "Headline"),
            ("descriptor", "Descriptor"),
            ("thesis_under_pressure", "Thesis Under Pressure"),
            ("positioning_tension", "Positioning Tension"),
            ("model_signal_tension", "Model Signal Tension"),
            ("vir_decomposition_readthrough", "VIR Decomposition Readthrough"),
            ("market_context_readthrough", "Market Context Readthrough"),
            ("measured_risk_readthrough", "Measured Risk Readthrough"),
            ("pm_decision_fork", "PM Decision Fork"),
            ("recommended_action", "Recommended Action"),
            ("primary_pm_question", "Primary PM Question"),
            ("evidence_needed_next", "Evidence Needed Next"),
            ("source_quality", "Source Quality"),
        ]
        if output_style == "deep_challenge_memo":
            challenge_fields[8:8] = [
                ("exact_holdings_causing_it", "Exact Holdings Causing It"),
                ("exact_vir_algo_decomp_explanation", "Exact VIR / Algo / Decomp Explanation"),
                ("exact_risk_contribution", "Exact Risk Contribution"),
                ("exact_internal_research_excerpt", "Exact Internal Research Excerpt"),
                ("exact_external_market_context", "Exact External Market Context"),
                ("bull_case", "Bull Case"),
                ("bear_case", "Bear Case"),
                ("devils_advocate", "Devil's Advocate"),
                ("what_would_change_my_mind", "What Would Change My Mind"),
                ("confidence", "Confidence"),
            ]
        for field, title in challenge_fields:
            value = row.get(field, "")
            if value:
                lines.append(f"- **{title}:** {value}")
        lines.append("")
    return lines
