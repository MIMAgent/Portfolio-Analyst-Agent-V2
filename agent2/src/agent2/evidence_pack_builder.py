"""Build the canonical deep-memo evidence pack from the larger agent2 review packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_context_bridge import build_challenge_market_context


def build_evidence_pack(
    review_packet: dict[str, Any],
    *,
    refresh_market_context: bool = True,
    challenge_count_target: int = 4,
) -> dict[str, Any]:
    material_positions = list(review_packet.get("material_positions", []))
    fund_snapshot = review_packet.get("fund_snapshot", {})
    risk_context = review_packet.get("risk_context", {})
    challenge_candidates = list(review_packet.get("challenge_book", []))[:challenge_count_target]
    positions_by_acid = {
        str(row.get("acid", "")).strip(): row
        for row in material_positions
        if str(row.get("acid", "")).strip()
    }
    challenge_market_context = build_challenge_market_context(
        header=review_packet.get("header", {}),
        challenge_candidates=challenge_candidates,
        refresh_missing=refresh_market_context,
        max_challenges=challenge_count_target,
        max_rows_per_challenge=3,
    )
    market_context_by_acid = {
        str(row.get("acid", "")).strip(): row
        for row in challenge_market_context
        if str(row.get("acid", "")).strip()
    }
    challenge_support_packets = _build_challenge_support_packets(
        challenge_candidates,
        positions_by_acid=positions_by_acid,
        market_context_by_acid=market_context_by_acid,
        risk_context=risk_context,
    )

    evidence_pack = {
        "header": review_packet.get("header", {}),
        "run_goal": {
            "instruction": "Write the canonical deep PM challenge memo. Prioritize the top 4 decisions the PM actually needs to defend, resize, monitor, or explain.",
            "challenge_count_target": challenge_count_target,
            "output_style": "deep_challenge_memo",
        },
        "fund_shape": {
            "headline_summary": fund_snapshot.get("headline_summary", [])[:4],
            "largest_overweights": fund_snapshot.get("largest_overweights", [])[:3],
            "largest_underweights": fund_snapshot.get("largest_underweights", [])[:3],
            "style_posture": fund_snapshot.get("style_posture", [])[:4],
        },
        "top_challenges": _compact_challenge_candidates(challenge_candidates),
        "challenge_market_context": challenge_market_context,
        "challenge_support_packets": challenge_support_packets,
        "supporting_positions": {
            "top_divergences": _compact_positions(
                [
                    row
                    for row in material_positions
                    if row.get("signal_alignment") in {"diverging", "partially_aligned"}
                ][:4]
            ),
            "top_aligned_positions": _compact_positions(
                [row for row in material_positions if row.get("signal_alignment") == "aligned"][:3]
            ),
            "top_movers": review_packet.get("top_movers", [])[:4],
            "decomposition_focus": _compact_decomposition_rows(review_packet.get("decomposition_summary", [])[:4]),
        },
        "risk_and_attribution": {
            "summary": risk_context.get("summary", {}),
            "top_style_risk_drivers": risk_context.get("top_style_risk_drivers", [])[:3],
            "top_industry_risk_drivers": risk_context.get("top_industry_risk_drivers", [])[:4],
            "return_attribution_mtd": risk_context.get("return_attribution_mtd", {}),
            "likely_holdings_contributors": risk_context.get("likely_holdings_contributors", [])[:4],
            "specific_risk_watchlist": risk_context.get("specific_risk_watchlist", [])[:3],
            "narrative_observations": risk_context.get("narrative_observations", [])[:4],
        },
        "sharepoint_research_focus": _key_sharepoint_research(material_positions),
        "internal_history_focus": _key_internal_history(material_positions),
        "source_drilldowns": _source_drilldowns(material_positions),
        "data_quality_flags": review_packet.get("data_quality_flags", []),
        "cost_guardrails": {
            "instruction": "Use only the evidence below. Do not produce a broad monthly review. Focus on the top 4 PM decisions and keep every section concise.",
            "target_output_tokens": 4200,
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
                "active_thesis": row.get("active_thesis", {}),
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
                "research_status": row.get("sharepoint_research", {}).get("primary_match", {}).get("folder_month", ""),
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


def _compact_challenge_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted = []
    for row in rows:
        compacted.append(
            {
                "challenge_id": row.get("challenge_id", ""),
                "acid": row.get("acid", ""),
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "priority": row.get("priority", ""),
                "challenge_score": row.get("challenge_score"),
                "challenge_type": row.get("challenge_type", ""),
                "challenge_headline": row.get("challenge_headline", ""),
                "thesis_under_pressure": row.get("thesis_under_pressure", ""),
                "positioning_tension": row.get("positioning_tension", ""),
                "model_signal_tension": row.get("model_signal_tension", ""),
                "vir_decomposition_readthrough": row.get("vir_decomposition_readthrough", ""),
                "market_context_readthrough": row.get("market_context_readthrough", ""),
                "measured_risk_readthrough": row.get("measured_risk_readthrough", ""),
                "return_attribution_readthrough": row.get("return_attribution_readthrough", ""),
                "pm_decision_fork": row.get("pm_decision_fork", ""),
                "primary_pm_question": row.get("primary_pm_question", ""),
                "evidence_needed_next": row.get("evidence_needed_next", ""),
                "source_quality": row.get("source_quality", ""),
                "research_status": row.get("research_status", {}),
                "top_holding_lineage": row.get("top_holding_lineage", ""),
            }
        )
    return compacted


def _build_challenge_support_packets(
    rows: list[dict[str, Any]],
    *,
    positions_by_acid: dict[str, dict[str, Any]],
    market_context_by_acid: dict[str, dict[str, Any]],
    risk_context: dict[str, Any],
) -> list[dict[str, Any]]:
    packets = []
    for row in rows:
        acid = str(row.get("acid", "")).strip()
        position = positions_by_acid.get(acid, {})
        market_context = market_context_by_acid.get(acid, {})
        packets.append(
            {
                "challenge_id": row.get("challenge_id", ""),
                "acid": acid,
                "label": row.get("label", ""),
                "category": row.get("category", ""),
                "exact_holdings_causing_it": _support_holdings(position),
                "exact_vir_algo_decomp_explanation": _support_signal_stack(position),
                "exact_risk_contribution": _support_risk_contribution(position, risk_context=risk_context),
                "exact_internal_research_excerpt": _support_internal_research(position),
                "exact_external_market_context": _support_external_market_context(market_context),
                "internal_history_excerpt": str(position.get("internal_history_excerpt", "")).strip()[:320],
                "top_holding_lineage": row.get("top_holding_lineage", ""),
                "research_status": row.get("research_status", {}),
                "source_quality": row.get("source_quality", ""),
            }
        )
    return packets


def _support_holdings(position: dict[str, Any]) -> list[dict[str, Any]]:
    securities = position.get("source_breakdown", {}).get("securities", [])
    rows = []
    for security in securities[:4]:
        rows.append(
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
                    for source in security.get("sources", [])[:3]
                ],
            }
        )
    return rows


def _support_signal_stack(position: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_weight": position.get("active_weight"),
        "portfolio_weight": position.get("portfolio_weight"),
        "benchmark_weight": position.get("benchmark_weight"),
        "positioning_direction": position.get("positioning_direction", ""),
        "vir_now": position.get("vir_now"),
        "vir_delta_mom": position.get("vir_delta_mom"),
        "vir_direction": position.get("vir_direction", ""),
        "algo_active_weight": position.get("algo_active_weight"),
        "algo_active_weight_mom": position.get("algo_active_weight_mom"),
        "algo_direction": position.get("algo_direction", ""),
        "signal_alignment": position.get("signal_alignment", ""),
        "decomposition_driver": position.get("decomposition_driver", ""),
        "decomposition_assessment": position.get("decomposition_assessment", ""),
        "decomposition_values": position.get("decomposition_values", {}),
    }


def _support_risk_contribution(position: dict[str, Any], *, risk_context: dict[str, Any]) -> dict[str, Any]:
    label = str(position.get("label", "")).strip()
    category = str(position.get("category", "")).strip()
    sector_match = next(
        (
            row
            for row in risk_context.get("likely_holdings_contributors", [])
            if str(row.get("mapped_sector", "")).strip() == label
        ),
        None,
    )
    watch_match = next(
        (
            row
            for row in risk_context.get("specific_risk_watchlist", [])
            if str(row.get("label", "")).strip() == label and str(row.get("category", "")).strip() == category
        ),
        None,
    )
    style_rows = risk_context.get("top_style_risk_drivers", [])
    style_match = None
    if category == "Eq Size / Style":
        lowered = label.lower()
        if any(token in lowered for token in ("small", "mid", "large")):
            style_match = next((row for row in style_rows if row.get("label") == "Size"), None)
        elif "growth" in lowered or "value" in lowered:
            style_match = next((row for row in style_rows if row.get("label") in {"Medium-Term Momentum", "Market Sensitivity"}), None)
    return {
        "sector_or_industry_match": sector_match or {},
        "style_match": style_match or {},
        "specific_risk_watch_match": watch_match or {},
        "return_attribution_mtd": risk_context.get("return_attribution_mtd", {}),
    }


def _support_internal_research(position: dict[str, Any]) -> dict[str, Any]:
    sharepoint_research = position.get("sharepoint_research", {})
    primary_match = {}
    if isinstance(sharepoint_research, dict):
        candidate = sharepoint_research.get("primary_match")
        if isinstance(candidate, dict):
            primary_match = candidate
    return {
        "active_thesis_text": str((position.get("active_thesis") or {}).get("thesis_text", "")).strip(),
        "active_thesis_falsification_conditions": str((position.get("active_thesis") or {}).get("falsification_conditions", "")).strip(),
        "internal_history_excerpt": str(position.get("internal_history_excerpt", "")).strip()[:400],
        "sharepoint_research_summary": str(position.get("sharepoint_research_summary", "")).strip()[:420],
        "sharepoint_research_path": position.get("sharepoint_research_path", ""),
        "sharepoint_research_month": primary_match.get("folder_month", ""),
        "sharepoint_match_status": sharepoint_research.get("match_status", ""),
    }


def _support_external_market_context(market_context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in market_context.get("rows", [])[:3]:
        rows.append(
            {
                "headline": item.get("headline", ""),
                "narrative": item.get("narrative", ""),
                "fundamental_readthrough": item.get("fundamental_readthrough", ""),
                "pm_question": item.get("pm_question", ""),
                "source": item.get("source_label", ""),
                "published_at": item.get("source_date", ""),
                "citation": item.get("citation_ref", ""),
                "url": item.get("source_url", ""),
            }
        )
    return rows
