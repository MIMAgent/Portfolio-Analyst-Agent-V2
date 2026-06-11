"""Build a compact model-ready evidence pack from the larger agent2 review packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_evidence_pack(review_packet: dict[str, Any]) -> dict[str, Any]:
    material_positions = list(review_packet.get("material_positions", []))
    signal_summary = review_packet.get("signal_summary", {})
    fund_snapshot = review_packet.get("fund_snapshot", {})

    evidence_pack = {
        "header": review_packet.get("header", {}),
        "headline_summary": fund_snapshot.get("headline_summary", []),
        "largest_overweights": fund_snapshot.get("largest_overweights", [])[:4],
        "largest_underweights": fund_snapshot.get("largest_underweights", [])[:4],
        "style_posture": fund_snapshot.get("style_posture", [])[:5],
        "top_divergences": _compact_positions(
            [
                row
                for row in material_positions
                if row.get("signal_alignment") in {"diverging", "partially_aligned"}
            ][:5]
        ),
        "top_aligned_positions": _compact_positions(
            [row for row in material_positions if row.get("signal_alignment") == "aligned"][:4]
        ),
        "top_movers": review_packet.get("top_movers", [])[:5],
        "decomposition_focus": _compact_decomposition_rows(review_packet.get("decomposition_summary", [])[:5]),
        "challenge_candidates": review_packet.get("challenge_book", [])[:5],
        "pm_questions_seed": review_packet.get("pm_questions", [])[:6],
        "portfolio_implications_seed": review_packet.get("portfolio_implications", [])[:4],
        "recurring_internal_themes": _recurring_internal_themes(material_positions),
        "key_internal_history": _key_internal_history(material_positions),
        "key_sharepoint_research": _key_sharepoint_research(material_positions),
        "source_drilldowns": _source_drilldowns(material_positions),
        "sharepoint_research_summary": review_packet.get("sharepoint_research_summary", [])[:6],
        "data_quality_flags": review_packet.get("data_quality_flags", []),
        "signal_summary": {
            "fund_level_observations": signal_summary.get("fund_level_observations", []),
            "mechanical_signals": signal_summary.get("mechanical_signals", [])[:4],
        },
        "cost_guardrails": {
            "instruction": "Use only the evidence below. Do not restate every row. Focus on the 5-8 most decision-relevant tensions.",
            "target_output_tokens": 3500,
        },
    }
    return evidence_pack


def write_evidence_pack(evidence_pack: dict[str, Any], output_json: str | Path) -> Path:
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence_pack, indent=2), encoding="utf-8")
    return output_path


def _compact_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for row in rows:
        compacted.append(
            {
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "portfolio_weight": row.get("portfolio_weight"),
                "benchmark_weight": row.get("benchmark_weight"),
                "active_weight": row.get("active_weight"),
                "vir_now": row.get("vir_now"),
                "vir_delta_mom": row.get("vir_delta_mom"),
                "algo_active_weight": row.get("algo_active_weight"),
                "signal_alignment": row.get("signal_alignment", ""),
                "signal_quality": row.get("signal_quality", ""),
                "decomposition_driver": row.get("decomposition_driver", ""),
                "decomposition_assessment": row.get("decomposition_assessment", ""),
                "internal_history_status": row.get("internal_history_status", ""),
                "internal_history_excerpt": row.get("internal_history_excerpt", "")[:180],
                "sharepoint_research_path": row.get("sharepoint_research_path", ""),
                "sharepoint_research_summary": row.get("sharepoint_research_summary", "")[:220],
                "sample_source_securities": row.get("sample_source_securities", ""),
                "source_breakdown": _compact_source_breakdown(row.get("source_breakdown", {})),
            }
        )
    return compacted


def _recurring_internal_themes(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    themes = []
    for row in material_positions:
        for theme_id in row.get("internal_history_related_themes", []):
            if theme_id in seen:
                continue
            seen.add(theme_id)
            themes.append(
                {
                    "theme_id": theme_id,
                    "example_acid": row.get("acid", ""),
                    "example_label": row.get("label", ""),
                }
            )
    return themes[:10]


def _key_internal_history(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in material_positions:
        excerpt = row.get("internal_history_excerpt", "").strip()
        if not excerpt:
            continue
        rows.append(
            {
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "excerpt": excerpt[:220],
                "themes": row.get("internal_history_related_themes", []),
            }
        )
    return rows[:5]


def _key_sharepoint_research(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in material_positions:
        if row.get("sharepoint_research", {}).get("match_status") != "matched":
            continue
        rows.append(
            {
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "research_path": row.get("sharepoint_research_path", ""),
                "research_summary": row.get("sharepoint_research_summary", "")[:260],
            }
        )
    return rows[:5]


def _source_drilldowns(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drilldowns = []
    for row in material_positions:
        source_breakdown = row.get("source_breakdown", {})
        securities = source_breakdown.get("securities", [])
        if not securities:
            continue
        drilldowns.append(
            {
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "top_securities": _compact_drilldown_securities(securities[:3]),
            }
        )
    return drilldowns[:5]


def _compact_source_breakdown(source_breakdown: dict[str, Any]) -> dict[str, Any]:
    securities = source_breakdown.get("securities", [])
    return {
        "security_count": source_breakdown.get("security_count", 0),
        "securities": _compact_drilldown_securities(securities[:3]),
    }


def _compact_drilldown_securities(securities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for security in securities:
        compacted.append(
            {
                "security_name": security.get("security_name", ""),
                "portfolio_weight": round(float(security.get("portfolio_weight", 0.0)), 4),
                "benchmark_weight": round(float(security.get("benchmark_weight", 0.0)), 4),
                "active_weight": round(float(security.get("active_weight", 0.0)), 4),
                "sources": [
                    {
                        "source_name": source.get("source_name", ""),
                        "portfolio_weight": round(float(source.get("portfolio_weight", 0.0)), 4),
                        "benchmark_weight": round(float(source.get("benchmark_weight", 0.0)), 4),
                        "active_weight": round(float(source.get("active_weight", 0.0)), 4),
                    }
                    for source in security.get("sources", [])[:2]
                ],
            }
        )
    return compacted


def _compact_decomposition_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for row in rows:
        compacted.append(
            {
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "dominant_driver": row.get("dominant_driver", ""),
                "dominant_driver_value": row.get("dominant_driver_value"),
                "assessment": row.get("assessment", ""),
                "vir_now": row.get("vir_now"),
                "vir_delta_mom": row.get("vir_delta_mom"),
                "active_weight": row.get("active_weight"),
                "values": {
                    key: value
                    for key, value in row.get("values", {}).items()
                    if key in {"growth", "yield", "inflation", "currency_usd", "valuation_adjustment_top_down", "valuation_adjustment_combined"}
                },
            }
        )
    return compacted
