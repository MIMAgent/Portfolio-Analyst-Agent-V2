from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build frontend review JSON from a structured review packet.")
    parser.add_argument("--packet", required=True, help="Path to the structured agent2 review packet JSON.")
    parser.add_argument("--output", required=True, help="Path to write the frontend review JSON.")
    return parser.parse_args()


def _format_weight(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:+.2f}%"


def _format_signal(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:+.1%}"


def _humanize_driver(value: str) -> str:
    return value.replace("_", " ").strip().title() if value else "Unknown Driver"


def build_review(packet: dict) -> dict:
    signal_summary = packet.get("signal_summary", {})
    fund_snapshot = packet.get("fund_snapshot", {})
    challenge_book = packet.get("challenge_book", [])
    top_movers = packet.get("top_movers", [])
    portfolio_implications = packet.get("portfolio_implications", [])
    roadmap = packet.get("roadmap", [])
    pm_questions = packet.get("pm_questions", [])
    quality_flags = packet.get("data_quality_flags", [])
    sharepoint_rows = packet.get("sharepoint_research_summary", [])

    aligned = signal_summary.get("aligned_positions", [])
    diverging = signal_summary.get("diverging_positions", [])
    headline_summary = [item for item in fund_snapshot.get("headline_summary", []) if item]
    observations = [item for item in signal_summary.get("fund_level_observations", []) if item]
    largest_overweights = fund_snapshot.get("largest_overweights", [])
    largest_underweights = fund_snapshot.get("largest_underweights", [])

    improving_movers = [item for item in top_movers if (item.get("vir_delta_mom") or 0) > 0][:3]
    weakening_movers = [item for item in top_movers if (item.get("vir_delta_mom") or 0) < 0][:3]
    high_priority = [item for item in challenge_book if item.get("priority") == "high"][:4]
    medium_priority = [item for item in challenge_book if item.get("priority") != "high"][:2]

    current_positioning = []
    for item in largest_underweights[:2] + largest_overweights[:2]:
        current_positioning.append(
            {
                "label": item.get("label", "Position"),
                "view": f"{item.get('label', 'Position')} is currently {_format_weight(item.get('active_weight'))} active versus the benchmark.",
                "evidence": (
                    f"{item.get('category', 'Exposure')} | benchmark {_format_weight(item.get('benchmark_weight'))} | "
                    f"portfolio {_format_weight(item.get('portfolio_weight'))}"
                ),
            }
        )

    bull_case = []
    for item in aligned[:3]:
        bull_case.append(
            {
                "label": f"{item.get('label', 'Position')} aligned",
                "statement": (
                    f"{item.get('label', 'Position')} is {_format_weight(item.get('active_weight'))} active and currently aligned "
                    f"with the signal direction."
                ),
            }
        )
    for item in improving_movers:
        bull_case.append(
            {
                "label": f"{item.get('label', 'Position')} improving",
                "statement": (
                    f"{item.get('label', 'Position')} improved by {_format_signal(item.get('vir_delta_mom'))} month over month, "
                    f"with {_humanize_driver(item.get('decomposition_driver', ''))} as the main driver."
                ),
            }
        )

    bear_case = []
    for item in high_priority:
        bear_case.append(
            {
                "label": item.get("label", "Challenge"),
                "statement": item.get("reason", ""),
            }
        )
    for item in weakening_movers:
        bear_case.append(
            {
                "label": f"{item.get('label', 'Position')} weakening",
                "statement": (
                    f"{item.get('label', 'Position')} moved by {_format_signal(item.get('vir_delta_mom'))} month over month, "
                    "which weakens the current signal backdrop."
                ),
            }
        )

    devils_advocate = []
    for item in portfolio_implications[:3]:
        devils_advocate.append(
            {
                "label": item.get("type", "Counterpoint").replace("_", " ").title(),
                "statement": item.get("statement", ""),
            }
        )
    for item in medium_priority:
        devils_advocate.append(
            {
                "label": f"{item.get('label', 'Position')} follow-through",
                "statement": item.get("reason", ""),
            }
        )

    follow_up = []
    for item in roadmap[:5]:
        follow_up.append(
            {
                "label": item.get("acid") or "Next step",
                "action": item.get("step", ""),
            }
        )
    for item in quality_flags[:2]:
        follow_up.append(
            {
                "label": item.get("flag", "data_quality").replace("_", " ").title(),
                "action": item.get("message", ""),
            }
        )

    dashboard_highlights = []
    for index, highlight in enumerate(headline_summary):
        dashboard_highlights.append(
            {
                "label": f"Packet highlight {index + 1}",
                "highlight": highlight,
            }
        )
    for item in sharepoint_rows[:2]:
        dashboard_highlights.append(
            {
                "label": item.get("label") or item.get("acid") or "Research match",
                "highlight": f"{item.get('file_name', 'Research deck')} matched to {item.get('acid', '-')}.",
            }
        )

    return {
        "executive_summary": " ".join(headline_summary + observations)
        or "The latest structured packet is loaded, but no current live narrative is available yet.",
        "current_positioning": current_positioning,
        "what_changed": [
            {
                "label": f"{item.get('label', 'Position')} mover",
                "change": f"VIR moved {_format_signal(item.get('vir_delta_mom'))} month over month.",
                "why_it_matters": (
                    f"{item.get('category', 'Exposure')} | VIR now {_format_signal(item.get('vir_now'))} | "
                    f"active {_format_weight(item.get('active_weight'))}"
                ),
            }
            for item in top_movers[:5]
        ],
        "bull_case": bull_case[:5],
        "bear_case": bear_case[:5],
        "devils_advocate": devils_advocate[:5],
        "pm_questions": pm_questions[:7],
        "follow_up": follow_up[:7],
        "dashboard_highlights": dashboard_highlights[:8],
    }


def build_current_review(packet: dict) -> dict:
    """Build the v2 frontend narrative shape from structured packet facts only.

    This is the safe fallback when the optional Bedrock narrative run is not
    available. It deliberately reuses packet prose and never invents market
    evidence, holdings, signals, or risk observations.
    """

    snapshot = packet.get("fund_snapshot", {})
    signal_summary = packet.get("signal_summary", {})
    quality_flags = packet.get("data_quality_flags", [])
    challenges = sorted(
        packet.get("challenge_book", []),
        key=lambda row: float(row.get("challenge_score") or 0),
        reverse=True,
    )[:4]

    headlines = [str(item) for item in snapshot.get("headline_summary", []) if item]
    observations = [
        str(item) for item in signal_summary.get("fund_level_observations", []) if item
    ]
    stale_notes = [
        str(item.get("message", ""))
        for item in quality_flags
        if item.get("flag") == "risk_context_pre_month_end" and item.get("message")
    ]

    key_insights = []
    challenge_brief = []
    for item in challenges:
        label = item.get("label", "Position")
        priority = item.get("priority", "medium")
        key_insights.append(
            {
                "label": label,
                "insight": item.get("challenge_headline")
                or item.get("observation")
                or item.get("reason", ""),
                "why_it_matters": item.get("interpretation")
                or item.get("positioning_tension")
                or item.get("reason", ""),
            }
        )
        challenge_brief.append(
            {
                "label": label,
                "challenge_headline": item.get("challenge_headline", ""),
                "descriptor": " | ".join(
                    value
                    for value in (
                        item.get("category", ""),
                        str(item.get("challenge_type", "")).replace("_", " "),
                        f"{priority} priority",
                    )
                    if value
                ),
                "thesis_under_pressure": item.get("thesis_under_pressure", ""),
                "positioning_tension": item.get("positioning_tension", ""),
                "model_signal_tension": item.get("model_signal_tension", ""),
                "relative_signal_readthrough": item.get("relative_signal_readthrough", ""),
                "vir_decomposition_readthrough": item.get("vir_decomposition_readthrough", ""),
                "market_context_readthrough": item.get("market_context_readthrough", ""),
                "measured_risk_readthrough": item.get("measured_risk_readthrough", ""),
                "exact_holdings_causing_it": item.get("top_holding_lineage", ""),
                "exact_vir_algo_decomp_explanation": item.get("model_signal_tension", ""),
                "exact_risk_contribution": item.get("measured_risk_readthrough", ""),
                "exact_internal_research_excerpt": item.get("internal_context_summary", ""),
                "exact_external_market_context": item.get("external_context_summary", ""),
                "bull_case": item.get("interpretation", ""),
                "bear_case": item.get("reason", ""),
                "devils_advocate": item.get("devils_advocate_statement", ""),
                "what_would_change_my_mind": item.get("what_would_change_view", ""),
                "pm_decision_fork": item.get("pm_decision_fork", ""),
                "recommended_action": "REVIEW AT IC" if priority == "high" else "DEFEND OR RESIZE",
                "primary_pm_question": item.get("primary_pm_question")
                or item.get("question", ""),
                "evidence_needed_next": item.get("evidence_needed_next", ""),
                "confidence": "Structured packet summary; optional model narrative was not run.",
                "source_quality": item.get("source_quality", ""),
            }
        )

    question_by_acid = {
        str(row.get("acid", "")): row for row in packet.get("pm_questions", [])
    }
    roadmap_by_acid = {
        str(row.get("acid", "")): row for row in packet.get("roadmap", [])
    }
    pm_questions = []
    follow_up = []
    for item in challenges:
        acid = str(item.get("acid", ""))
        question = question_by_acid.get(acid, {})
        roadmap = roadmap_by_acid.get(acid, {})
        pm_questions.append(
            {
                "label": item.get("label", "Position"),
                "question": question.get("question")
                or item.get("primary_pm_question")
                or item.get("question", ""),
                "why_now": question.get("why_now")
                or item.get("challenge_headline")
                or item.get("reason", ""),
            }
        )
        follow_up.append(
            {
                "label": item.get("label", "Position"),
                "action": roadmap.get("step") or item.get("evidence_needed_next", ""),
                "why_it_matters": item.get("what_would_change_view")
                or item.get("interpretation", ""),
            }
        )

    dashboard_highlights = [
        {"label": f"Packet highlight {index + 1}", "highlight": text}
        for index, text in enumerate(headlines[:4])
    ]
    dashboard_highlights.extend(
        {
            "label": str(flag.get("flag", "data quality")).replace("_", " ").title(),
            "highlight": flag.get("message", ""),
        }
        for flag in quality_flags[:4]
        if flag.get("message")
    )

    executive_parts = headlines[:3] + observations[:3] + stale_notes[:1]
    return {
        "executive_summary": " ".join(executive_parts)
        or "The structured packet is available, but no summary rows were produced.",
        "key_insights": key_insights,
        "challenge_brief": challenge_brief,
        "pm_questions": pm_questions,
        "follow_up": follow_up,
        "dashboard_highlights": dashboard_highlights[:8],
    }


def main() -> int:
    args = parse_args()
    packet_path = Path(args.packet)
    output_path = Path(args.output)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    review = build_current_review(packet)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
    print(f"packet={packet_path.as_posix()}")
    print(f"output={output_path.as_posix()}")
    print(f"pm_questions={len(review['pm_questions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
