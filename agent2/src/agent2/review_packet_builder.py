"""Build the first structured agent2 review packet from current monthly data."""

from __future__ import annotations

import csv
from datetime import date
import io
import json
from pathlib import Path
import re
from typing import Any
from zipfile import ZipFile

from .internal_history_retrieval import load_internal_history, retrieve_relevant_history, summarize_recurring_themes
from .sharepoint_research import DEFAULT_SHAREPOINT_RESEARCH_ROOT, build_research_index, match_research_for_position


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ALIGNMENT_CSV = REPO_ROOT / "artifacts" / "rolled_exposures" / "fund_weights_vir_algo_multisignal.csv"
DEFAULT_DETAIL_CSV = REPO_ROOT / "artifacts" / "rolled_exposures" / "fund_rolled_exposure_detail.csv"
DEFAULT_MAPPING_CSV = REPO_ROOT / "data" / "acid_mapping_bootstrap_v1.csv"
DEFAULT_VIR_HISTORY_CSV = REPO_ROOT / "artifacts" / "equity_vir_history.csv"
DEFAULT_INTERNAL_HISTORY_JSON = REPO_ROOT / "agent2" / "data" / "internal_history" / "us_equity_checklists_q2_2026.json"
DEFAULT_MEMORY_JSON = REPO_ROOT / "artifacts" / "agent_memory" / "memory_records.json"
DEFAULT_SHAREPOINT_RESEARCH_DIR = DEFAULT_SHAREPOINT_RESEARCH_ROOT

EQUITY_DECOMPOSITION_FIELDS = (
    "growth",
    "yield",
    "inflation",
    "currency_usd",
    "valuation_adjustment_top_down",
    "valuation_adjustment_combined",
    "valuation_adjustment_bottom_up",
)


def build_review_packet(
    *,
    fund: str,
    logical_snapshot_date: str | None = None,
    review_date: str | None = None,
    alignment_csv: str | Path = DEFAULT_ALIGNMENT_CSV,
    detail_csv: str | Path = DEFAULT_DETAIL_CSV,
    mapping_csv: str | Path = DEFAULT_MAPPING_CSV,
    vir_history_csv: str | Path = DEFAULT_VIR_HISTORY_CSV,
    internal_history_json: str | Path | None = DEFAULT_INTERNAL_HISTORY_JSON,
    memory_json: str | Path | None = DEFAULT_MEMORY_JSON,
    sharepoint_research_dir: str | Path | None = DEFAULT_SHAREPOINT_RESEARCH_DIR,
) -> dict[str, Any]:
    alignment_rows = _load_csv_rows(Path(alignment_csv))
    fund_rows = [row for row in alignment_rows if row.get("fund", "").strip() == fund]
    if not fund_rows:
        raise ValueError(f"No alignment rows found for fund {fund!r}.")

    selected_snapshot_date = _latest_snapshot_date(fund_rows)
    current_rows = [row for row in fund_rows if row.get("snapshot_date", "").strip() == selected_snapshot_date]
    current_rows.sort(key=lambda row: abs(_to_float(row.get("active_rolled_exposure"))), reverse=True)

    mapping_index = _load_mapping_index(Path(mapping_csv))
    detail_rows = _load_csv_rows(Path(detail_csv))
    lineage_by_acid = _build_lineage_by_acid(
        detail_rows=detail_rows,
        fund=fund,
        snapshot_date=selected_snapshot_date,
    )
    decomp_by_key = _load_decomposition_index(
        Path(vir_history_csv),
        keys={
            (row.get("vir_snapshot_date", "").strip(), row.get("acid", "").strip())
            for row in current_rows
            if row.get("vir_snapshot_date", "").strip() and row.get("acid", "").strip()
        },
    )

    logical_date = logical_snapshot_date or selected_snapshot_date
    history_payload = _load_optional_internal_history(internal_history_json)
    history_fund = _resolve_history_fund_name(history_payload, fund)
    recurring_themes = (
        summarize_recurring_themes(history_payload, fund=history_fund, before_date=logical_date)
        if history_payload and history_fund
        else []
    )
    active_thesis_by_acid = _load_active_thesis_by_acid(memory_json, fund=fund)
    research_index = build_research_index(sharepoint_research_dir)

    material_positions: list[dict[str, Any]] = []
    for row in current_rows:
        acid = row.get("acid", "").strip()
        mapping = mapping_index.get(acid, {})
        decomposition = decomp_by_key.get((row.get("vir_snapshot_date", "").strip(), acid), {})
        history_context = _build_history_context(
            history_payload=history_payload,
            history_fund=history_fund,
            logical_date=logical_date,
            row=row,
            mapping=mapping,
        )
        lineage = lineage_by_acid.get(acid, _empty_lineage())
        category, label = _derive_category_and_label(row=row, mapping=mapping)
        sharepoint_research = match_research_for_position(
            acid=acid,
            label=label,
            research_index=research_index,
        )
        material_positions.append(
            _build_material_position(
                row=row,
                mapping=mapping,
                category=category,
                label=label,
                decomposition=decomposition,
                history_context=history_context,
                lineage=lineage,
                active_thesis=active_thesis_by_acid.get(acid),
                sharepoint_research=sharepoint_research,
            )
        )

    material_positions.sort(key=lambda item: item["importance_score"], reverse=True)
    matched_research_positions = [item for item in material_positions if item.get("sharepoint_research", {}).get("match_status") == "matched"]

    output_review_date = review_date or date.today().isoformat()
    packet = {
        "header": _build_header(
            fund=fund,
            logical_snapshot_date=logical_date,
            review_date=output_review_date,
            source_snapshot_date=selected_snapshot_date,
            material_positions=material_positions,
            history_payload=history_payload,
            history_fund=history_fund,
            logical_date=logical_date,
        ),
        "fund_snapshot": _build_fund_snapshot(material_positions),
        "material_positions": material_positions,
        "signal_summary": _build_signal_summary(material_positions, recurring_themes),
        "top_movers": _build_top_movers(material_positions),
        "decomposition_summary": _build_decomposition_summary(material_positions),
        "challenge_book": _build_challenge_book(material_positions),
        "pm_questions": _build_pm_questions(material_positions, recurring_themes),
        "portfolio_implications": _build_portfolio_implications(material_positions, recurring_themes),
        "roadmap": _build_roadmap(material_positions),
        "sharepoint_research_summary": _build_sharepoint_research_summary(material_positions),
        "data_quality_flags": _build_data_quality_flags(
            material_positions=material_positions,
            selected_snapshot_date=selected_snapshot_date,
            logical_snapshot_date=logical_date,
        ),
        "source_index": _build_source_index(
            alignment_csv=Path(alignment_csv),
            detail_csv=Path(detail_csv),
            mapping_csv=Path(mapping_csv),
            vir_history_csv=Path(vir_history_csv),
            internal_history_json=Path(internal_history_json) if internal_history_json else None,
            memory_json=Path(memory_json) if memory_json else None,
            sharepoint_research_dir=Path(sharepoint_research_dir) if sharepoint_research_dir else None,
        ),
        "run_metadata": {
            "builder_version": "agent2_review_packet_v1",
            "fund": fund,
            "logical_snapshot_date": logical_date,
            "source_snapshot_date": selected_snapshot_date,
            "review_date": output_review_date,
            "material_position_count": len(material_positions),
            "history_fund_name": history_fund or "",
            "matched_sharepoint_research_count": len(matched_research_positions),
        },
    }
    return packet


def write_review_packet(packet: dict[str, Any], output_json: str | Path) -> Path:
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return output_path


def _build_header(
    *,
    fund: str,
    logical_snapshot_date: str,
    review_date: str,
    source_snapshot_date: str,
    material_positions: list[dict[str, Any]],
    history_payload: dict[str, Any] | None,
    history_fund: str,
    logical_date: str,
) -> dict[str, Any]:
    fund_type = next(
        (item["mapping"].get("model_family", "") for item in material_positions if item["mapping"].get("model_family", "")),
        "",
    )
    pm_names = _pm_names_from_history(history_payload, fund=history_fund, before_date=logical_date)
    return {
        "fund": fund,
        "fund_slug": _slugify(fund),
        "fund_type": fund_type or "unknown",
        "benchmark": _guess_benchmark(fund),
        "pm_names": pm_names,
        "snapshot_date": logical_snapshot_date,
        "as_of_date": logical_snapshot_date,
        "review_date": review_date,
        "review_run_id": f"agent2_{_slugify(fund)}_{logical_snapshot_date}",
        "source_snapshot_date": source_snapshot_date,
    }


def _build_fund_snapshot(material_positions: list[dict[str, Any]]) -> dict[str, Any]:
    overweights = [item for item in material_positions if item["active_weight"] > 0][:5]
    underweights = [item for item in material_positions if item["active_weight"] < 0][:5]
    category_exposures = []
    seen_categories: set[tuple[str, str]] = set()
    for item in material_positions:
        key = (item["category"], item["label"])
        if key in seen_categories:
            continue
        seen_categories.add(key)
        category_exposures.append(
            {
                "group": item["category"],
                "label": item["label"],
                "active_weight": item["active_weight"],
                "portfolio_weight": item["portfolio_weight"],
                "benchmark_weight": item["benchmark_weight"],
                "signal_direction": item["signal_alignment"],
                "source_refs": item["source_refs"],
            }
        )
        if len(category_exposures) >= 10:
            break

    style_posture = []
    for item in material_positions:
        mapping = item["mapping"]
        if item["category"] == "Eq Size / Style" and abs(item["active_weight"]) >= 2.0:
            style_posture.append(
                {
                    "label": item["label"],
                    "active_weight": item["active_weight"],
                    "interpretation": _style_posture_text(item, mapping),
                }
            )

    headline_summary = _build_headline_summary(material_positions)
    return {
        "largest_overweights": [_snapshot_row(item) for item in overweights],
        "largest_underweights": [_snapshot_row(item) for item in underweights],
        "category_exposures": category_exposures,
        "style_posture": style_posture[:6],
        "headline_summary": headline_summary,
    }


def _snapshot_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": item["category"],
        "label": item["label"],
        "active_weight": item["active_weight"],
        "benchmark_weight": item["benchmark_weight"],
        "portfolio_weight": item["portfolio_weight"],
        "source_refs": item["source_refs"],
    }


def _build_material_position(
    *,
    row: dict[str, str],
    mapping: dict[str, str],
    category: str,
    label: str,
    decomposition: dict[str, float],
    history_context: dict[str, Any],
    lineage: dict[str, Any],
    active_thesis: dict[str, Any] | None,
    sharepoint_research: dict[str, Any],
) -> dict[str, Any]:
    active_weight = _to_float(row.get("active_rolled_exposure"))
    portfolio_weight = _to_float(row.get("fund_target_rolled_exposure"))
    benchmark_weight = _to_float(row.get("fund_benchmark_rolled_exposure"))
    vir_now = _to_float_or_none(row.get("vir_stf"))
    vir_delta_mom = _to_float_or_none(row.get("vir_delta_stf"))
    algo_active_weight_pct = _to_float(row.get("algo_active_weight")) * 100.0 if row.get("algo_active_weight", "") else None
    algo_absolute_weight_pct = _to_float(row.get("algo_absolute_weight")) * 100.0 if row.get("algo_absolute_weight", "") else None
    algo_benchmark_weight_pct = _to_float(row.get("algo_benchmark_weight")) * 100.0 if row.get("algo_benchmark_weight", "") else None
    algo_active_weight_mom_pct = _to_float(row.get("algo_active_weight_mom")) * 100.0 if row.get("algo_active_weight_mom", "") else None
    vir_direction = _signal_direction(vir_now)
    algo_direction = _signal_direction(algo_active_weight_pct)
    positioning_direction = _signal_direction(active_weight)
    signal_alignment = _alignment_label(
        positioning_direction=positioning_direction,
        vir_direction=vir_direction,
        algo_direction=algo_direction,
    )
    decomp_meta = _decomposition_meta(decomposition)
    importance_score = _importance_score(
        active_weight=active_weight,
        vir_delta_mom=vir_delta_mom,
        positioning_direction=positioning_direction,
        vir_direction=vir_direction,
        algo_direction=algo_direction,
        decomp_meta=decomp_meta,
    )
    history_matches = history_context.get("matches", [])
    internal_history_status = "matched_prior_rationale" if history_matches else "no_recent_rationale_found"
    external_context_status = "pending_external_research"
    source_refs = [
        {
            "artifact_path": "artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
            "row_id": row.get("row_id", ""),
        }
    ]
    if history_matches:
        source_refs.append(
            {
                "artifact_path": "agent2/data/internal_history/us_equity_checklists_q2_2026.json",
                "row_id": history_matches[0].get("source_filename", ""),
            }
        )
    primary_research_match = sharepoint_research.get("primary_match")
    if primary_research_match:
        source_refs.append(
            {
                "artifact_path": primary_research_match.get("full_path", ""),
                "row_id": primary_research_match.get("file_name", ""),
            }
        )

    return {
        "position_id": f"{_slugify(row.get('fund', ''))}__{_slugify(row.get('acid', ''))}",
        "acid": row.get("acid", ""),
        "category": category,
        "label": label,
        "portfolio_weight": portfolio_weight,
        "benchmark_weight": benchmark_weight,
        "active_weight": active_weight,
        "vir_now": vir_now,
        "vir_delta_mom": vir_delta_mom,
        "vir_rank_in_category_by_stf": _to_float_or_none(row.get("vir_rank_in_category_by_stf")),
        "vir_rank_change_by_stf": _to_float_or_none(row.get("vir_rank_change_by_stf")),
        "algo_view": algo_direction,
        "algo_active_weight": algo_active_weight_pct,
        "algo_absolute_weight": algo_absolute_weight_pct,
        "algo_benchmark_weight": algo_benchmark_weight_pct,
        "algo_active_weight_mom": algo_active_weight_mom_pct,
        "signal_alignment": signal_alignment,
        "signal_quality": _signal_quality(vir_delta_mom),
        "decomposition_assessment": decomp_meta["assessment"],
        "decomposition_driver": decomp_meta["dominant_driver"],
        "decomposition_driver_value": decomp_meta["dominant_value"],
        "decomposition_values": decomposition,
        "internal_history_status": internal_history_status,
        "internal_history_excerpt": history_matches[0].get("body_text", "")[:400] if history_matches else "",
        "internal_history_related_themes": history_matches[0].get("related_themes", []) if history_matches else [],
        "external_context_status": external_context_status,
        "importance_score": round(importance_score, 3),
        "positioning_direction": positioning_direction,
        "vir_direction": vir_direction,
        "algo_direction": algo_direction,
        "vir_snapshot_date": row.get("vir_snapshot_date", ""),
        "algo_snapshot_date": row.get("algo_snapshot_date", ""),
        "sample_source_securities": row.get("sample_source_securities", ""),
        "source_security_count": _to_int(row.get("source_security_count")),
        "source_breakdown": lineage,
        "sharepoint_research": sharepoint_research,
        "sharepoint_research_summary": sharepoint_research.get("extracted_context", {}).get("summary_text", "")[:1000],
        "sharepoint_research_path": primary_research_match.get("full_path", "") if primary_research_match else "",
        "mapping": mapping,
        "vir_join_status": row.get("vir_join_status", ""),
        "algo_join_status": row.get("algo_join_status", ""),
        "active_thesis": active_thesis or {},
        "source_refs": source_refs,
    }


def _build_signal_summary(material_positions: list[dict[str, Any]], recurring_themes: list[dict[str, Any]]) -> dict[str, Any]:
    aligned_positions = [
        {
            "acid": item["acid"],
            "label": item["label"],
            "category": item["category"],
            "active_weight": item["active_weight"],
            "signal_alignment": item["signal_alignment"],
        }
        for item in material_positions
        if item["signal_alignment"] == "aligned"
    ][:5]
    diverging_positions = [
        {
            "acid": item["acid"],
            "label": item["label"],
            "category": item["category"],
            "active_weight": item["active_weight"],
            "positioning_direction": item["positioning_direction"],
            "vir_direction": item["vir_direction"],
            "algo_direction": item["algo_direction"],
        }
        for item in material_positions
        if item["signal_alignment"] in {"diverging", "partially_aligned"}
    ][:6]
    mechanical_signals = [
        {
            "acid": item["acid"],
            "label": item["label"],
            "driver": item["decomposition_driver"],
            "assessment": item["decomposition_assessment"],
        }
        for item in material_positions
        if item["decomposition_assessment"] in {"valuation_led", "currency_led"}
    ][:6]

    observations = []
    if material_positions:
        largest = material_positions[0]
        observations.append(
            f"The largest current active expression is {largest['label']} at {largest['active_weight']:.2f} percentage points, with {largest['signal_alignment']} signal support."
        )
    if recurring_themes:
        theme = recurring_themes[0]
        observations.append(
            f"Internal history most often references {theme['label']} ({theme['occurrence_count']} prior mentions), so that posture deserves continuity checks."
        )
    if diverging_positions:
        item = diverging_positions[0]
        observations.append(
            f"The clearest position-versus-signal tension is {item['label']}, where positioning is {item['positioning_direction']} while VIR is {item['vir_direction']} and algo is {item['algo_direction']}."
        )
    return {
        "aligned_positions": aligned_positions,
        "diverging_positions": diverging_positions,
        "mechanical_signals": mechanical_signals,
        "fund_level_observations": observations,
    }


def _build_top_movers(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    movers = sorted(
        [item for item in material_positions if item["vir_delta_mom"] is not None],
        key=lambda item: abs(item["vir_delta_mom"]),
        reverse=True,
    )
    return [
        {
            "acid": item["acid"],
            "label": item["label"],
            "category": item["category"],
            "vir_now": item["vir_now"],
            "vir_delta_mom": item["vir_delta_mom"],
            "decomposition_driver": item["decomposition_driver"],
            "decomposition_assessment": item["decomposition_assessment"],
            "active_weight": item["active_weight"],
        }
        for item in movers[:8]
    ]


def _build_decomposition_summary(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in material_positions:
        if not item["decomposition_values"]:
            continue
        rows.append(
            {
                "acid": item["acid"],
                "label": item["label"],
                "dominant_driver": item["decomposition_driver"],
                "dominant_driver_value": item["decomposition_driver_value"],
                "assessment": item["decomposition_assessment"],
                "vir_now": item["vir_now"],
                "vir_delta_mom": item["vir_delta_mom"],
                "active_weight": item["active_weight"],
                "values": item["decomposition_values"],
            }
        )
    rows.sort(key=lambda item: abs(item["dominant_driver_value"] or 0.0), reverse=True)
    return rows[:10]


def _build_challenge_book(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    challenge_items = []
    for item in material_positions:
        if item["signal_alignment"] == "aligned":
            continue
        if abs(item["active_weight"]) < 1.5:
            continue
        challenge_items.append(
            {
                "acid": item["acid"],
                "label": item["label"],
                "category": item["category"],
                "priority": "high" if abs(item["active_weight"]) >= 3.0 else "medium",
                "reason": _challenge_reason(item),
                "question": _challenge_question(item),
                "source_refs": item["source_refs"],
            }
        )
    return challenge_items[:8]


def _build_pm_questions(material_positions: list[dict[str, Any]], recurring_themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions = []
    ranked = sorted(
        material_positions,
        key=lambda item: (
            0 if item["signal_alignment"] in {"diverging", "partially_aligned"} else 1,
            -abs(item["active_weight"]),
        ),
    )
    for item in ranked:
        if len(questions) >= 6:
            break
        if item["signal_alignment"] == "aligned":
            if abs(item["active_weight"]) < 3.0:
                continue
            if item["decomposition_assessment"] == "broad_based" and item["internal_history_status"] == "matched_prior_rationale":
                continue
        if item["signal_alignment"] == "insufficient_signal" and abs(item["active_weight"]) < 2.0:
            continue
        questions.append(
            {
                "acid": item["acid"],
                "label": item["label"],
                "question": _challenge_question(item),
                "why_now": _challenge_reason(item),
            }
        )
    if recurring_themes:
        theme = recurring_themes[0]
        questions.append(
            {
                "acid": "",
                "label": theme["label"],
                "question": f"Do we still agree with the historical {theme['label'].lower()} posture, or has the evidence base changed enough that the old rationale should be rewritten?",
                "why_now": "This theme appears repeatedly in prior internal checklists and should be explicitly re-underwritten rather than assumed.",
            }
        )
    return questions[:7]


def _build_portfolio_implications(material_positions: list[dict[str, Any]], recurring_themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    implications = []
    largest_underweight = next((item for item in material_positions if item["active_weight"] < 0), None)
    largest_overweight = next((item for item in material_positions if item["active_weight"] > 0), None)
    if largest_underweight:
        implications.append(
            {
                "type": "risk_concentration",
                "statement": f"The biggest underweight is {largest_underweight['label']}, which means the fund's relative return path will still be highly sensitive to whether that area broadens or mean-reverts.",
            }
        )
    if largest_overweight:
        implications.append(
            {
                "type": "conviction_expression",
                "statement": f"The biggest overweight is {largest_overweight['label']}, so stock selection and implementation quality inside that bucket matter more than the headline active weight alone suggests.",
            }
        )
    if recurring_themes:
        implications.append(
            {
                "type": "continuity_check",
                "statement": f"Prior internal rationale repeatedly emphasized {recurring_themes[0]['label'].lower()}, so the June review should explicitly confirm whether that story still holds with current sizing and signal evidence.",
            }
        )
    return implications


def _build_roadmap(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    next_steps = []
    for item in material_positions:
        if len(next_steps) >= 5:
            break
        if item["signal_alignment"] == "aligned" and item["decomposition_assessment"] == "broad_based":
            continue
        next_steps.append(
            {
                "acid": item["acid"],
                "step": f"Review the security-level construction underneath {item['label']} and decide whether the current expression is still the cleanest way to hold the view.",
            }
        )
    return next_steps


def _build_data_quality_flags(
    *,
    material_positions: list[dict[str, Any]],
    selected_snapshot_date: str,
    logical_snapshot_date: str,
) -> list[dict[str, Any]]:
    flags = []
    missing_vir = [item for item in material_positions if item["vir_join_status"] != "matched_to_vir"]
    missing_algo = [item for item in material_positions if item["algo_join_status"] != "matched_to_algo"]
    if missing_vir:
        flags.append(
            {
                "severity": "medium",
                "flag": "missing_vir_rows",
                "message": f"{len(missing_vir)} exposure rows do not have matched VIR context.",
            }
        )
    if missing_algo:
        flags.append(
            {
                "severity": "medium",
                "flag": "missing_algo_rows",
                "message": f"{len(missing_algo)} exposure rows do not have matched algo context.",
            }
        )
    if selected_snapshot_date != logical_snapshot_date:
        flags.append(
            {
                "severity": "low",
                "flag": "logical_vs_source_snapshot_date",
                "message": f"The review month is {logical_snapshot_date}, while the source holdings snapshot embedded in the rolled artifact is {selected_snapshot_date}.",
            }
        )
    vir_snapshot_dates = sorted({item.get("vir_snapshot_date", "") for item in material_positions if item.get("vir_snapshot_date", "")})
    if vir_snapshot_dates:
        latest_vir_snapshot = vir_snapshot_dates[-1]
        if latest_vir_snapshot < logical_snapshot_date:
            flags.append(
                {
                    "severity": "medium",
                    "flag": "stale_vir_snapshot",
                    "message": f"The latest matched VIR snapshot in this packet is {latest_vir_snapshot}, older than the labeled review month {logical_snapshot_date}.",
                }
            )
        flags.append(
            {
                "severity": "low",
                "flag": "algo_scaled_to_percentage_points",
                "message": "Algo weights are stored as decimals in the source workbook and are converted to percentage points in this packet for readability.",
            }
        )
    return flags


def _build_sharepoint_research_summary(material_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary_rows = []
    for item in material_positions:
        research = item.get("sharepoint_research", {})
        if research.get("match_status") != "matched":
            continue
        primary_match = research.get("primary_match", {})
        extracted_context = research.get("extracted_context", {})
        summary_rows.append(
            {
                "acid": item.get("acid", ""),
                "label": item.get("label", ""),
                "matched_via": research.get("matched_via", ""),
                "confidence": research.get("confidence", 0.0),
                "folder_month": primary_match.get("folder_month", ""),
                "file_name": primary_match.get("file_name", ""),
                "full_path": primary_match.get("full_path", ""),
                "slide_titles": extracted_context.get("slide_titles", [])[:4],
                "summary_text": extracted_context.get("summary_text", "")[:800],
            }
        )
    return summary_rows[:10]


def _build_source_index(
    *,
    alignment_csv: Path,
    detail_csv: Path,
    mapping_csv: Path,
    vir_history_csv: Path,
    internal_history_json: Path | None,
    memory_json: Path | None,
    sharepoint_research_dir: Path | None,
) -> list[dict[str, Any]]:
    sources = [
        {
            "source_type": "structured_current",
            "artifact_path": alignment_csv.relative_to(REPO_ROOT).as_posix(),
            "purpose": "ACID-level fund positioning with VIR and algo joins",
        },
        {
            "source_type": "structured_lineage",
            "artifact_path": detail_csv.relative_to(REPO_ROOT).as_posix(),
            "purpose": "Security and sleeve contributions underneath each ACID exposure",
        },
        {
            "source_type": "mapping",
            "artifact_path": mapping_csv.relative_to(REPO_ROOT).as_posix(),
            "purpose": "Category, region, country, sector, style, and interpretation labels",
        },
        {
            "source_type": "vir_history",
            "artifact_path": f"{vir_history_csv.relative_to(REPO_ROOT).as_posix()}.zip",
            "purpose": "VIR history and decomposition fields",
        },
    ]
    if internal_history_json and internal_history_json.exists():
        sources.append(
            {
                "source_type": "internal_history",
                "artifact_path": internal_history_json.relative_to(REPO_ROOT).as_posix(),
                "purpose": "Prior mutual fund checklist context",
            }
        )
    if memory_json and memory_json.exists():
        sources.append(
            {
                "source_type": "memory",
                "artifact_path": memory_json.relative_to(REPO_ROOT).as_posix(),
                "purpose": "Existing thesis and exception context",
            }
        )
    if sharepoint_research_dir and sharepoint_research_dir.exists():
        sources.append(
            {
                "source_type": "sharepoint_research",
                "artifact_path": sharepoint_research_dir.as_posix(),
                "purpose": "Synced SharePoint research decks matched to individual ACIDs",
            }
        )
    return sources


def _build_headline_summary(material_positions: list[dict[str, Any]]) -> list[str]:
    summary = []
    if not material_positions:
        return summary
    biggest_underweight = next((item for item in material_positions if item["active_weight"] < 0), None)
    biggest_overweight = next((item for item in material_positions if item["active_weight"] > 0), None)
    if biggest_underweight:
        summary.append(
            f"Largest underweight: {biggest_underweight['label']} ({biggest_underweight['active_weight']:.2f} pts), with VIR {biggest_underweight['vir_direction']} and algo {biggest_underweight['algo_direction']}."
        )
    if biggest_overweight:
        summary.append(
            f"Largest overweight: {biggest_overweight['label']} ({biggest_overweight['active_weight']:.2f} pts), with decomposition reading {biggest_overweight['decomposition_assessment']}."
        )
    diverging = [item for item in material_positions if item["signal_alignment"] == "diverging"]
    if diverging:
        summary.append(f"{len(diverging)} material positions are directionally fighting the current VIR/algo read.")
    return summary


def _load_optional_internal_history(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    source = Path(path)
    if not source.exists():
        return None
    return load_internal_history(source)


def _resolve_history_fund_name(payload: dict[str, Any] | None, fund: str) -> str:
    if not payload:
        return ""
    available = {document.get("fund", "") for document in payload.get("documents", [])}
    candidates = [fund, re.sub(r"^MStar\s+", "", fund).strip()]
    for candidate in candidates:
        if candidate in available:
            return candidate
    return ""


def _pm_names_from_history(payload: dict[str, Any] | None, *, fund: str, before_date: str) -> list[str]:
    if not payload or not fund:
        return []
    candidates = []
    for document in payload.get("documents", []):
        if document.get("fund") != fund:
            continue
        document_date = document.get("document_date", "")
        if before_date and _normalize_dateish(document_date) >= _normalize_dateish(before_date):
            continue
        candidates.append(document)
    if not candidates:
        return []
    candidates.sort(key=lambda item: _normalize_dateish(item.get("document_date", "")), reverse=True)
    return candidates[0].get("pm_names", [])


def _build_history_context(
    *,
    history_payload: dict[str, Any] | None,
    history_fund: str,
    logical_date: str,
    row: dict[str, str],
    mapping: dict[str, str],
) -> dict[str, Any]:
    if not history_payload or not history_fund:
        return {"matches": []}
    theme_ids = _theme_ids_for_row(row=row, mapping=mapping)
    query_terms = [
        row.get("acid", ""),
        mapping.get("sector", ""),
        mapping.get("style", ""),
        mapping.get("country", ""),
        mapping.get("region", ""),
        mapping.get("asset_class_name", ""),
    ]
    query = " ".join(term for term in query_terms if term)
    return retrieve_relevant_history(
        history_payload,
        fund=history_fund,
        query=query,
        theme_ids=theme_ids,
        before_date=logical_date,
        max_sections=2,
    )


def _theme_ids_for_row(*, row: dict[str, str], mapping: dict[str, str]) -> list[str]:
    theme_ids = []
    sector = mapping.get("sector", "")
    style = mapping.get("style", "")
    label = mapping.get("asset_class_name", "")
    if sector == "Information Technology":
        theme_ids.extend(["information_technology_underweight", "ai_leadership_risk"])
    if sector == "Industrials":
        theme_ids.append("industrials_overweight")
    if sector == "Financials":
        theme_ids.append("financials_overweight")
    if any(token in label for token in ("Small", "Mid", "SMID")) or any(token in row.get("acid", "") for token in ("MID", "SML")):
        theme_ids.append("smid_overweight")
    if style == "Value":
        theme_ids.append("value_tilt")
    deduped = []
    seen = set()
    for theme_id in theme_ids:
        if theme_id not in seen:
            seen.add(theme_id)
            deduped.append(theme_id)
    return deduped


def _load_active_thesis_by_acid(path: str | Path | None, *, fund: str) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8"))
    tables = payload.get("tables", {})
    thesis_rows = tables.get("thesis_ledger", [])
    return {
        row.get("acid", ""): row
        for row in thesis_rows
        if row.get("fund") == fund and row.get("status") == "active"
    }


def _load_mapping_index(path: Path) -> dict[str, dict[str, str]]:
    rows = _load_csv_rows(path)
    return {row.get("acid", "").strip(): row for row in rows if row.get("acid", "").strip()}


def _build_lineage_by_acid(*, detail_rows: list[dict[str, str]], fund: str, snapshot_date: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in detail_rows:
        if row.get("fund", "").strip() != fund:
            continue
        if row.get("snapshot_date", "").strip() != snapshot_date:
            continue
        acid = row.get("acid", "").strip()
        if not acid:
            continue
        bucket = grouped.setdefault(acid, {"_security_map": {}})
        security_name = row.get("security_name", "").strip() or row.get("common_identifier", "").strip() or "Unknown"
        identifier = row.get("common_identifier", "").strip() or security_name
        security_bucket = bucket["_security_map"].setdefault(
            identifier,
            {
                "security_name": security_name,
                "identifier": identifier,
                "portfolio_weight": 0.0,
                "benchmark_weight": 0.0,
                "active_weight": 0.0,
                "_source_map": {},
            },
        )
        target = _to_float(row.get("fund_target_security_contribution"))
        benchmark = _to_float(row.get("fund_benchmark_security_contribution"))
        active = target - benchmark
        security_bucket["portfolio_weight"] += target
        security_bucket["benchmark_weight"] += benchmark
        security_bucket["active_weight"] += active

        source_name = row.get("account_name", "").strip() or row.get("portcode", "").strip() or "Unknown Source"
        source_bucket = security_bucket["_source_map"].setdefault(
            source_name,
            {
                "source_name": source_name,
                "portfolio_weight": 0.0,
                "benchmark_weight": 0.0,
                "active_weight": 0.0,
            },
        )
        source_bucket["portfolio_weight"] += target
        source_bucket["benchmark_weight"] += benchmark
        source_bucket["active_weight"] += active

    finalized: dict[str, dict[str, Any]] = {}
    for acid, bucket in grouped.items():
        securities = []
        for security in bucket["_security_map"].values():
            sources = sorted(
                security.pop("_source_map").values(),
                key=lambda item: abs(item["portfolio_weight"]),
                reverse=True,
            )
            security["sources"] = sources
            security["source_count"] = len(sources)
            securities.append(security)
        securities.sort(key=lambda item: abs(item["portfolio_weight"]), reverse=True)
        finalized[acid] = {
            "security_count": len(securities),
            "securities": securities[:20],
        }
    return finalized


def _empty_lineage() -> dict[str, Any]:
    return {"security_count": 0, "securities": []}


def _load_decomposition_index(path: Path, *, keys: set[tuple[str, str]]) -> dict[tuple[str, str], dict[str, float]]:
    if not keys:
        return {}
    indexed: dict[tuple[str, str], dict[str, float]] = {}
    with _open_csv_text(path) as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (row.get("snapshot_date", "").strip(), row.get("acid", "").strip())
            if key not in keys:
                continue
            values = {}
            for field in EQUITY_DECOMPOSITION_FIELDS:
                value = _to_float_or_none(row.get(field))
                if value is not None:
                    values[field] = value
            if values:
                indexed[key] = values
    return indexed


def _derive_category_and_label(*, row: dict[str, str], mapping: dict[str, str]) -> tuple[str, str]:
    asset_name = mapping.get("asset_class_name", "").replace(" Equity", "").strip() or row.get("acid", "")
    sector = mapping.get("sector", "").strip()
    style = mapping.get("style", "").strip()
    family = mapping.get("family", "").strip()
    country = mapping.get("country", "").strip()
    region = mapping.get("region", "").strip()

    if sector:
        return "Eq Sector", sector
    if style or "Size" in family or "Style" in family or any(token in row.get("acid", "") for token in ("LRG", "MID", "SML")):
        return "Eq Size / Style", asset_name
    if country and region and country != region:
        return "Country", country
    if region:
        return "Region", region
    if row.get("acid_type", "") == "acid_bond":
        return "Cash / Other", asset_name
    return "Exposure", asset_name


def _decomposition_meta(values: dict[str, float]) -> dict[str, Any]:
    if not values:
        return {
            "dominant_driver": "",
            "dominant_value": None,
            "assessment": "missing",
        }
    ranked = sorted(values.items(), key=lambda item: abs(item[1]), reverse=True)
    dominant_driver, dominant_value = ranked[0]
    total_abs = sum(abs(value) for value in values.values())
    share = abs(dominant_value) / total_abs if total_abs else 0.0
    if share < 0.45 and len(ranked) >= 2:
        assessment = "broad_based"
    elif dominant_driver.startswith("valuation_adjustment"):
        assessment = "valuation_led"
    elif dominant_driver == "currency_usd":
        assessment = "currency_led"
    else:
        assessment = "fundamental_led"
    return {
        "dominant_driver": dominant_driver,
        "dominant_value": dominant_value,
        "assessment": assessment,
    }


def _importance_score(
    *,
    active_weight: float,
    vir_delta_mom: float | None,
    positioning_direction: str,
    vir_direction: str,
    algo_direction: str,
    decomp_meta: dict[str, Any],
) -> float:
    score = abs(active_weight)
    if vir_delta_mom is not None:
        score += abs(vir_delta_mom) * 40.0
    if positioning_direction != "neutral" and vir_direction not in {"neutral", "missing"} and positioning_direction != vir_direction:
        score += 1.5
    if positioning_direction != "neutral" and algo_direction not in {"neutral", "missing"} and positioning_direction != algo_direction:
        score += 1.0
    if decomp_meta["assessment"] in {"valuation_led", "currency_led"}:
        score += 0.5
    return score


def _signal_quality(vir_delta_mom: float | None) -> str:
    if vir_delta_mom is None:
        return "unknown"
    if vir_delta_mom > 0.003:
        return "improving"
    if vir_delta_mom < -0.003:
        return "weakening"
    return "stable"


def _signal_direction(value: float | None) -> str:
    if value is None:
        return "missing"
    if value > 0:
        return "overweight"
    if value < 0:
        return "underweight"
    return "neutral"


def _alignment_label(*, positioning_direction: str, vir_direction: str, algo_direction: str) -> str:
    comparable = [direction for direction in (vir_direction, algo_direction) if direction not in {"missing", "neutral"}]
    if not comparable or positioning_direction == "neutral":
        return "insufficient_signal"
    same_count = sum(1 for direction in comparable if direction == positioning_direction)
    if same_count == len(comparable):
        return "aligned"
    if same_count == 0:
        return "diverging"
    return "partially_aligned"


def _style_posture_text(item: dict[str, Any], mapping: dict[str, str]) -> str:
    direction = "overweight" if item["active_weight"] > 0 else "underweight"
    if mapping.get("style") == "Value":
        return f"{direction.title()} value exposure remains a meaningful part of the fund shape."
    if mapping.get("style") == "Growth":
        return f"{direction.title()} growth exposure remains a meaningful part of the fund shape."
    return f"{direction.title()} exposure in this size bucket is material enough to shape the portfolio's style posture."


def _challenge_reason(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return (
            f"Positioning is {item['positioning_direction']}, but VIR is {item['vir_direction']} and algo is {item['algo_direction']}."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"The signal is being driven mainly by {item['decomposition_driver']}, which makes the headline move look more mechanical than broad-based."
        )
    return "This is a material active position that still needs an explicit current-month rationale."


def _challenge_question(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return (
            f"Why is the fund still {item['positioning_direction']} {item['label']} when both current signals lean {item['vir_direction']}/{item['algo_direction']}?"
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"Does the team still trust the {item['label']} signal if the move is mostly {item['decomposition_driver']} driven rather than broad-based?"
        )
    return f"What is the current underwriting case for keeping {item['label']} at this size?"


def _guess_benchmark(fund: str) -> str:
    if fund == "MStar US Equity":
        return "Russell 3000"
    return ""


def _normalize_dateish(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        return value
    parts = re.split(r"[/-]", value or "")
    if len(parts) == 3:
        month, day, year = parts
        if len(year) == 2:
            year = f"20{year}"
        return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
    return ""


def _latest_snapshot_date(rows: list[dict[str, str]]) -> str:
    return max(row.get("snapshot_date", "") for row in rows)


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with _open_csv_text(path) as handle:
        return list(csv.DictReader(handle))


def _open_csv_text(path: Path):
    if path.exists():
        return path.open("r", newline="", encoding="utf-8-sig")
    zip_path = path.with_name(f"{path.name}.zip")
    if not zip_path.exists():
        raise FileNotFoundError(f"CSV source not found: {path} or {zip_path}")
    archive = ZipFile(zip_path)
    member_name = next(name for name in archive.namelist() if Path(name).name == path.name or name.endswith(".csv"))
    binary_handle = archive.open(member_name)
    text_handle = io.TextIOWrapper(binary_handle, encoding="utf-8-sig", newline="")

    class _ZipTextContext:
        def __enter__(self):
            return text_handle

        def __exit__(self, exc_type, exc, tb):
            text_handle.detach()
            binary_handle.close()
            archive.close()
            return False

    return _ZipTextContext()


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _to_float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _to_float_or_none(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: str | None) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
