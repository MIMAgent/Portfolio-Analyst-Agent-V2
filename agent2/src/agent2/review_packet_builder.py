"""Build the first structured agent2 review packet from current monthly data."""

from __future__ import annotations

import csv
from datetime import date
import io
import json
from pathlib import Path
import re
import sys
from typing import Any
from zipfile import ZipFile

from .internal_history_retrieval import load_internal_history, retrieve_relevant_history, summarize_recurring_themes
from .path_redaction import redact_paths
from .sharepoint_research import DEFAULT_SHAREPOINT_RESEARCH_ROOT, build_research_index, match_research_for_position


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ALIGNMENT_CSV = REPO_ROOT / "artifacts" / "rolled_exposures" / "fund_weights_vir_algo_multisignal.csv"
DEFAULT_DETAIL_CSV = REPO_ROOT / "artifacts" / "rolled_exposures" / "fund_rolled_exposure_detail.csv"
DEFAULT_MAPPING_CSV = REPO_ROOT / "data" / "acid_mapping_bootstrap_v1.csv"
DEFAULT_VIR_HISTORY_CSV = REPO_ROOT / "artifacts" / "vir" / "equity_vir_dataset.csv"


RISK_REPORT_GLOB_BY_FUND = {
    "MStar US Equity": "weekly_US_EQ*Risk Report*.xlsx",
    "MStar International Equity": "weekly_INTL_EQ*Risk Report*.xlsx",
    "MStar Global Opportunistic Equity": "weekly_GOE*Risk Report*.xlsx",
}


def _latest_risk_report_for_fund(fund: str) -> Path | None:
    pattern = RISK_REPORT_GLOB_BY_FUND.get(fund)
    if not pattern:
        return None
    candidates = sorted(REPO_ROOT.glob(f"data/*/{pattern}"))
    return candidates[-1] if candidates else None
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

GENERIC_PM_QUESTION_PATTERNS = (
    "is this still intentional",
    "why is this still overweight",
    "why is the fund still overweight",
    "why is this still underweight",
    "why is the fund still underweight",
)


# --- STF relative-ranking universe -------------------------------------------
# STF is a valuation/attractiveness signal, not a sizing call. To let the agent
# reason about *relative* attractiveness, we rank each exposure's STF against its
# peers in the fund's mandate universe (not the whole model): US funds rank
# within US, international within ex-US (DM+EM), global funds globally. Universe
# is then split by category group (sectors / styles / countries / regions).
# NOTE: this should eventually live in a proper per-fund config.
FUND_STF_UNIVERSE_SCOPE = {
    "MStar US Equity": "us",
    "MStar International Equity": "ex_us",
    "MStar Global Opportunities": "global",
    "MStar Global Opp": "global",
}
DEFAULT_STF_UNIVERSE_SCOPE = "global"
STF_HISTORY_WINDOW = 12  # trailing months for the historical STF percentile

_STF_CATEGORY_GROUP = {
    "Eq Sector": "sectors",
    "Eq Size / Style": "styles",
    "Country": "countries",
    "Region": "regions",
}
_STF_SCOPE_LABEL = {"us": "US", "ex_us": "ex-US", "global": "global"}


def _fund_universe_scope(fund: str) -> str:
    return FUND_STF_UNIVERSE_SCOPE.get(fund, DEFAULT_STF_UNIVERSE_SCOPE)


def _acid_region(acid: str) -> str:
    return str(acid or "").strip().split(" ")[0]


def _acid_in_scope(acid: str, scope: str) -> bool:
    region = _acid_region(acid)
    if scope == "us":
        return region == "US"
    if scope == "ex_us":
        return region != "US"
    return True  # global


def _stf_median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def _universe_dominant_driver(members: list[dict[str, Any]]) -> str:
    # The regime story is "what is dragging this universe negative", so take the
    # most-negative decomposition component per member and report the mode --
    # not the largest-absolute driver, which can be a positive tailwind.
    counts: dict[str, int] = {}
    for member in members:
        values = member.get("decomposition_values") or {}
        negatives = {k: v for k, v in values.items() if v < 0}
        if not negatives:
            continue
        drag_key = min(negatives, key=lambda k: negatives[k])
        counts[drag_key] = counts.get(drag_key, 0) + 1
    if not counts:
        return ""
    driver, count = max(counts.items(), key=lambda kv: kv[1])
    # Only report a shared driver if it actually dominates the universe.
    return driver if count >= max(2, len(members) * 0.4) else ""


def _attach_stf_relative_context(material_positions: list[dict[str, Any]], *, scope: str) -> None:
    """Rank each position's STF within its (fund-scope x category-group) universe.

    Mutates each position in place, adding a `stf_relative_context` dict, or None
    when the position is out of mandate scope / has no rankable category / lacks
    an STF value. Rank 1 = most attractive (highest STF).
    """
    scope_label = _STF_SCOPE_LABEL.get(scope, scope)
    universes: dict[str, list[dict[str, Any]]] = {}
    for position in material_positions:
        position["stf_relative_context"] = None
        group = _STF_CATEGORY_GROUP.get(position.get("category", ""))
        if group is None or position.get("vir_now") is None:
            continue
        if not _acid_in_scope(position.get("acid", ""), scope):
            continue
        universes.setdefault(f"{scope_label} {group}", []).append(position)

    for label, members in universes.items():
        members.sort(key=lambda p: p["vir_now"], reverse=True)
        size = len(members)
        stf_values = [m["vir_now"] for m in members]
        median = _stf_median(stf_values)
        all_negative = all(value < 0 for value in stf_values)
        dominant_driver = _universe_dominant_driver(members)
        best, worst = members[0], members[-1]
        for index, position in enumerate(members):
            rank = index + 1
            more_attractive = [m["label"] for m in members[:index]]
            position["stf_relative_context"] = {
                "universe": label,
                "universe_size": size,
                "rank": rank,
                "percentile": round((size - rank) / (size - 1), 2) if size > 1 else 1.0,
                "stf": round(position["vir_now"], 4),
                "universe_median_stf": round(median, 4),
                "vs_median": round(position["vir_now"] - median, 4),
                "more_attractive_peers": more_attractive[:3],
                "more_attractive_count": len(more_attractive),
                "universe_best": {"label": best["label"], "stf": round(best["vir_now"], 4)},
                "universe_worst": {"label": worst["label"], "stf": round(worst["vir_now"], 4)},
                "universe_all_negative": all_negative,
                "universe_dominant_driver": dominant_driver,
            }


def _ordinal(n: int) -> str:
    v = n % 100
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(v % 10, "th") if not 11 <= v <= 13 else "th"
    return f"{n}{suffix}"


def _load_stf_history_by_acid(vir_history_csv: str | Path, *, acids: list[str], window: int) -> dict[str, list[float]]:
    """Per-ACID trailing STF series from the VIR history workbook (for the
    historical percentile). Returns {} if the file is absent or unparseable."""
    path = Path(vir_history_csv)
    if not path.exists():
        return {}
    wanted = set(acids)
    rows_by_acid: dict[str, list[tuple[str, float]]] = {}
    try:
        with _open_csv_text(path) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                acid = (row.get("acid") or "").strip()
                if acid not in wanted:
                    continue
                stf = _to_float_or_none(row.get("stf"))
                if stf is None:
                    lr = _to_float_or_none(row.get("local_real_vir") or row.get("lr10_combined"))
                    uc = _to_float_or_none(row.get("unconditional_vir") or row.get("lruc"))
                    if lr is not None and uc is not None:
                        stf = lr - uc
                if stf is None:
                    continue
                rows_by_acid.setdefault(acid, []).append(((row.get("snapshot_date") or "").strip(), stf))
    except Exception:
        return {}
    out: dict[str, list[float]] = {}
    for acid, pairs in rows_by_acid.items():
        pairs.sort(key=lambda pair: pair[0])
        series = [value for _, value in pairs][-window:]
        if len(series) >= 2:
            out[acid] = series
    return out


def _attach_stf_history_percentile(
    material_positions: list[dict[str, Any]],
    *,
    history_by_acid: dict[str, list[float]],
    window: int,
) -> None:
    """Augment each position's stf_relative_context with where its CURRENT STF
    sits in its OWN trailing range (time-series, orthogonal to the peer rank)."""
    for position in material_positions:
        ctx = position.get("stf_relative_context")
        if not ctx:
            continue
        series = history_by_acid.get(position.get("acid", ""))
        if not series or len(series) < 2:
            continue
        # The series' last point is the current snapshot; rank it against its prior
        # history (excludes the current point -- no self-counting, no rounding skew).
        current = series[-1]
        prior = series[:-1]
        below = sum(1 for value in prior if value < current)
        ctx["historical_percentile"] = round(below / len(prior), 2)
        ctx["history_window_months"] = window
        ctx["history_low"] = round(min(series), 4)
        ctx["history_high"] = round(max(series), 4)


def build_review_packet(
    *,
    fund: str,
    logical_snapshot_date: str | None = None,
    review_date: str | None = None,
    alignment_csv: str | Path = DEFAULT_ALIGNMENT_CSV,
    detail_csv: str | Path = DEFAULT_DETAIL_CSV,
    mapping_csv: str | Path = DEFAULT_MAPPING_CSV,
    vir_history_csv: str | Path = DEFAULT_VIR_HISTORY_CSV,
    risk_report_xlsx: str | Path | None = None,
    internal_history_json: str | Path | None = DEFAULT_INTERNAL_HISTORY_JSON,
    memory_json: str | Path | None = DEFAULT_MEMORY_JSON,
    sharepoint_research_dir: str | Path | None = DEFAULT_SHAREPOINT_RESEARCH_DIR,
) -> dict[str, Any]:
    alignment_rows = _load_csv_rows(Path(alignment_csv))
    fund_rows = [row for row in alignment_rows if row.get("fund", "").strip() == fund]
    if not fund_rows:
        raise ValueError(f"No alignment rows found for fund {fund!r}.")
    risk_report_xlsx = risk_report_xlsx or _latest_risk_report_for_fund(fund)

    selected_snapshot_date = _latest_snapshot_date(fund_rows)
    current_rows = [row for row in fund_rows if row.get("snapshot_date", "").strip() == selected_snapshot_date]
    current_rows.sort(key=lambda row: abs(_to_float(row.get("active_rolled_exposure"))), reverse=True)

    mapping_index = _load_mapping_index(Path(mapping_csv))
    detail_rows = _load_csv_rows(Path(detail_csv))
    benchmark = _benchmark_name_from_detail_rows(
        detail_rows,
        fund=fund,
        snapshot_date=selected_snapshot_date,
    )
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
    _attach_stf_relative_context(material_positions, scope=_fund_universe_scope(fund))
    _attach_stf_history_percentile(
        material_positions,
        history_by_acid=_load_stf_history_by_acid(
            vir_history_csv,
            acids=[item.get("acid", "") for item in material_positions],
            window=STF_HISTORY_WINDOW,
        ),
        window=STF_HISTORY_WINDOW,
    )
    matched_research_positions = [item for item in material_positions if item.get("sharepoint_research", {}).get("match_status") == "matched"]
    output_review_date = review_date or date.today().isoformat()
    risk_context = _load_risk_context(
        fund=fund,
        risk_as_of_date=output_review_date,
        material_positions=material_positions,
        risk_report_xlsx=risk_report_xlsx,
    )

    challenge_book = _build_challenge_book(
        material_positions,
        risk_context=risk_context,
        logical_snapshot_date=logical_date,
    )
    packet = {
        "header": _build_header(
            fund=fund,
            logical_snapshot_date=logical_date,
            review_date=output_review_date,
            source_snapshot_date=selected_snapshot_date,
            benchmark=benchmark,
            material_positions=material_positions,
            history_payload=history_payload,
            history_fund=history_fund,
            logical_date=logical_date,
        ),
        "fund_snapshot": _build_fund_snapshot(material_positions, risk_context=risk_context),
        "material_positions": material_positions,
        "risk_context": risk_context,
        "signal_summary": _build_signal_summary(material_positions, recurring_themes, risk_context=risk_context),
        "top_movers": _build_top_movers(material_positions),
        "decomposition_summary": _build_decomposition_summary(material_positions),
        "challenge_book": challenge_book,
        "pm_questions": _build_pm_questions(material_positions, challenge_book, recurring_themes, risk_context=risk_context),
        "portfolio_implications": _build_portfolio_implications(material_positions, recurring_themes, risk_context=risk_context),
        "roadmap": _build_roadmap(material_positions),
        "sharepoint_research_summary": _build_sharepoint_research_summary(material_positions),
        "data_quality_flags": _build_data_quality_flags(
            material_positions=material_positions,
            selected_snapshot_date=selected_snapshot_date,
            logical_snapshot_date=logical_date,
            risk_context=risk_context,
        ),
        "source_index": _build_source_index(
            alignment_csv=Path(alignment_csv),
            detail_csv=Path(detail_csv),
            mapping_csv=Path(mapping_csv),
            vir_history_csv=Path(vir_history_csv),
            risk_report_xlsx=Path(risk_report_xlsx) if risk_report_xlsx else None,
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
            "risk_context_available": bool(risk_context.get("available")),
            "risk_date_used": risk_context.get("summary", {}).get("risk_date_used", ""),
        },
    }
    return packet


def write_review_packet(packet: dict[str, Any], output_json: str | Path) -> Path:
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(redact_paths(packet), indent=2), encoding="utf-8")
    return output_path


def _build_header(
    *,
    fund: str,
    logical_snapshot_date: str,
    review_date: str,
    source_snapshot_date: str,
    benchmark: str,
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
        "benchmark": benchmark,
        "pm_names": pm_names,
        "snapshot_date": logical_snapshot_date,
        "as_of_date": logical_snapshot_date,
        "review_date": review_date,
        "review_run_id": f"agent2_{_slugify(fund)}_{logical_snapshot_date}",
        "source_snapshot_date": source_snapshot_date,
    }


def _build_fund_snapshot(material_positions: list[dict[str, Any]], *, risk_context: dict[str, Any]) -> dict[str, Any]:
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
    if risk_context.get("available"):
        risk_summary = risk_context.get("summary", {})
        headline_summary.append(
            "US_EQ risk context: "
            f"active predicted risk {risk_summary.get('active_predicted_risk_pct', 0.0):.2f}%, "
            f"active share {risk_summary.get('active_share_pct', 0.0):.1f}%, "
            f"risk date used {risk_summary.get('risk_date_used', '')}."
        )
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


def _build_signal_summary(
    material_positions: list[dict[str, Any]],
    recurring_themes: list[dict[str, Any]],
    *,
    risk_context: dict[str, Any],
) -> dict[str, Any]:
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
            f"The clearest position-versus-signal tension is {item['label']}, where positioning is {item['positioning_direction']} while the STF is {item['vir_direction']} and the algo active weight (relative to benchmark) is {item['algo_direction']}."
        )
    observations.extend(risk_context.get("narrative_observations", [])[:3])
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


def _build_challenge_book(
    material_positions: list[dict[str, Any]],
    *,
    risk_context: dict[str, Any],
    logical_snapshot_date: str,
) -> list[dict[str, Any]]:
    challenge_items = []
    for item in material_positions:
        if item["signal_alignment"] == "aligned":
            continue
        if abs(item["active_weight"]) < 1.5:
            continue
        primary_pm_question = _challenge_primary_pm_question(item)
        evidence_needed_next = _challenge_evidence_needed_next(item)
        research_status = _challenge_research_status(item, logical_snapshot_date=logical_snapshot_date)
        challenge_score = _challenge_priority_score(
            item,
            risk_context=risk_context,
            research_status=research_status,
        )
        challenge_items.append(
            {
                "challenge_id": f"ch_{_slugify(item['acid'])}_{item.get('vir_snapshot_date') or 'current'}",
                "acid": item["acid"],
                "label": item["label"],
                "category": item["category"],
                "priority": "high" if abs(item["active_weight"]) >= 3.0 else "medium",
                "challenge_type": _challenge_type(item),
                "challenge_score": round(challenge_score, 3),
                "reason": _challenge_reason(item),
                "question": primary_pm_question,
                "observation": _challenge_reason(item),
                "interpretation": _challenge_interpretation(item),
                "challenge_headline": _challenge_headline(item),
                "thesis_under_pressure": _challenge_thesis_under_pressure(item),
                "positioning_tension": _challenge_positioning_tension(item),
                "model_signal_tension": _challenge_model_signal_tension(item),
                "relative_signal_readthrough": _challenge_relative_signal_readthrough(item),
                "stf_relative_context": item.get("stf_relative_context"),
                "vir_decomposition_readthrough": _challenge_vir_decomposition_readthrough(item),
                "market_context_readthrough": _challenge_market_context_readthrough(item),
                "measured_risk_readthrough": _challenge_measured_risk_readthrough(item, risk_context=risk_context),
                "return_attribution_readthrough": _challenge_return_attribution_readthrough(item, risk_context=risk_context),
                "pm_decision_fork": _challenge_pm_decision_fork(item),
                "primary_pm_question": primary_pm_question,
                "evidence_needed_next": evidence_needed_next,
                "source_quality": _challenge_source_quality(item),
                "devils_advocate_statement": _challenge_devils_advocate_statement(item),
                "what_would_change_view": evidence_needed_next,
                "internal_context_summary": _challenge_internal_context_summary(item),
                "external_context_summary": _challenge_market_context_readthrough(item),
                "research_status": research_status,
                "top_holding_lineage": _challenge_top_holding_lineage(item),
                "source_refs": item["source_refs"],
            }
        )
    challenge_items.sort(
        key=lambda row: (
            row.get("challenge_score", 0.0),
            abs(float(row.get("priority") == "high")),
            abs(next((item["active_weight"] for item in material_positions if item["acid"] == row["acid"]), 0.0)),
        ),
        reverse=True,
    )
    return challenge_items[:6]


def _build_pm_questions(
    material_positions: list[dict[str, Any]],
    challenge_book: list[dict[str, Any]],
    recurring_themes: list[dict[str, Any]],
    *,
    risk_context: dict[str, Any],
) -> list[dict[str, Any]]:
    questions = []
    for challenge in challenge_book:
        if len(questions) >= 6:
            break
        questions.append(
            {
                "acid": challenge.get("acid", ""),
                "label": challenge.get("label", ""),
                "question": challenge.get("primary_pm_question", ""),
                "why_now": challenge.get("challenge_headline", "") or challenge.get("observation", ""),
            }
        )

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
        question = _challenge_primary_pm_question(item)
        if any(pattern in question.lower() for pattern in GENERIC_PM_QUESTION_PATTERNS):
            continue
        questions.append(
            {
                "acid": item["acid"],
                "label": item["label"],
                "question": question,
                "why_now": _challenge_headline(item),
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
    if risk_context.get("available"):
        top_driver = next(iter(risk_context.get("top_industry_risk_drivers", [])), None)
        if top_driver:
            questions.append(
                {
                    "acid": "",
                    "label": top_driver["label"],
                    "question": f"What is the underwriting case for keeping {top_driver['label']} as a leading source of active risk right now?",
                    "why_now": f"It is the largest modeled industry risk driver at {top_driver['share_of_variance_pct']:.1f}% of active variance.",
                }
            )
    return questions[:7]


def _build_portfolio_implications(
    material_positions: list[dict[str, Any]],
    recurring_themes: list[dict[str, Any]],
    *,
    risk_context: dict[str, Any],
) -> list[dict[str, Any]]:
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
    if risk_context.get("available"):
        risk_summary = risk_context.get("summary", {})
        implications.append(
            {
                "type": "measured_risk_context",
                "statement": "Measured active risk is "
                f"{risk_summary.get('active_predicted_risk_pct', 0.0):.2f}% with "
                f"{risk_summary.get('active_share_pct', 0.0):.1f}% active share, so PM debate should separate conviction from raw risk budget use.",
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
    risk_context: dict[str, Any],
) -> list[dict[str, Any]]:
    flags = []
    missing_vir = [item for item in material_positions if item["vir_join_status"] != "matched_to_vir"]
    missing_algo = [item for item in material_positions if item["algo_join_status"] != "matched_to_algo"]
    if missing_vir:
        flags.append(
            {
                "severity": "medium",
                "flag": "missing_vir_rows",
                "message": f"{len(missing_vir)} exposure rows do not have matched STF context.",
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
                    "message": f"The latest matched STF snapshot in this packet is {latest_vir_snapshot}, older than the labeled review month {logical_snapshot_date}.",
                }
            )
        flags.append(
            {
                "severity": "low",
                "flag": "algo_scaled_to_percentage_points",
                "message": "Algo weights are stored as decimals in the source workbook and are converted to percentage points in this packet for readability.",
            }
        )
    if not risk_context.get("available"):
        flags.append(
            {
                "severity": "medium",
                "flag": "missing_risk_report_context",
                "message": "No parsed risk report context was available for this packet.",
            }
        )
    elif risk_context.get("summary", {}).get("risk_date_used", "") < logical_snapshot_date:
        flags.append(
            {
                "severity": "low",
                "flag": "risk_context_pre_month_end",
                "message": f"Risk context uses the latest business-day row on or before {logical_snapshot_date}: {risk_context.get('summary', {}).get('risk_date_used', '')}.",
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
    risk_report_xlsx: Path | None,
    internal_history_json: Path | None,
    memory_json: Path | None,
    sharepoint_research_dir: Path | None,
) -> list[dict[str, Any]]:
    sources = [
        {
            "source_type": "structured_current",
            "artifact_path": alignment_csv.relative_to(REPO_ROOT).as_posix(),
            "purpose": "ACID-level fund positioning with STF and algo joins",
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
            "purpose": "STF history and decomposition fields",
        },
    ]
    if risk_report_xlsx and risk_report_xlsx.exists():
        sources.append(
            {
                "source_type": "risk_report",
                "artifact_path": risk_report_xlsx.relative_to(REPO_ROOT).as_posix(),
                "purpose": "Time-series risk, factor-risk, and return-attribution context",
            }
        )
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
            f"Largest underweight: {biggest_underweight['label']} ({biggest_underweight['active_weight']:.2f} pts), with STF {biggest_underweight['vir_direction']} and the algo active weight {biggest_underweight['algo_direction']} (relative to benchmark)."
        )
    if biggest_overweight:
        summary.append(
            f"Largest overweight: {biggest_overweight['label']} ({biggest_overweight['active_weight']:.2f} pts), with decomposition reading {biggest_overweight['decomposition_assessment']}."
        )
    diverging = [item for item in material_positions if item["signal_alignment"] == "diverging"]
    if diverging:
        summary.append(f"{len(diverging)} material positions are directionally fighting the current STF/algo read.")
    return summary


def _load_optional_internal_history(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    source = Path(path)
    if not source.exists():
        return None
    return load_internal_history(source)


def _load_risk_context(
    *,
    fund: str,
    risk_as_of_date: str,
    material_positions: list[dict[str, Any]],
    risk_report_xlsx: str | Path | None,
) -> dict[str, Any]:
    if fund not in RISK_REPORT_GLOB_BY_FUND or not risk_report_xlsx:
        return {"available": False}
    source = Path(risk_report_xlsx)
    if not source.exists():
        return {"available": False, "source_file": source.name}
    src_root = REPO_ROOT / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from portfolio_analyst_agent.risk_report import build_risk_context

    return build_risk_context(
        source,
        review_date=risk_as_of_date,
        material_positions=material_positions,
    )


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
            f"Positioning is {item['positioning_direction']}, but the STF is {item['vir_direction']} and the algo active weight (relative to benchmark) is {item['algo_direction']}."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"The signal is being driven mainly by {item['decomposition_driver']}, which makes the headline move look more mechanical than broad-based."
        )
    return "This is a material active position that still needs an explicit current-month rationale."


def _challenge_type(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return "position_vs_signal_divergence"
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return "mechanical_signal_fragility"
    return "material_position_needing_refresh"


def _challenge_headline(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return (
            f"{item['label']} remains {item['positioning_direction']} despite both the STF and the algo active weight leaning "
            f"{item['vir_direction']}/{item['algo_direction']} (relative to benchmark)."
        )
    if item["signal_alignment"] == "partially_aligned":
        return (
            f"{item['label']} still carries a meaningful {item['positioning_direction']} even though only part of the signal stack agrees."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"{item['label']} is still sized materially, but the current signal looks mainly { _friendly_driver_name(item['decomposition_driver']) }-driven."
        )
    return f"{item['label']} remains a material active expression that needs an explicit current-month defense."


def _challenge_interpretation(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return (
            "This now looks less like neutral portfolio noise and more like an active choice to hold a view "
            "that current model evidence is not confirming."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            "The headline move should not be treated as a clean fundamental confirmation until the broader "
            "evidence stack validates it."
        )
    return "The position may still be valid, but the evidence base should be refreshed rather than rolled forward by habit."


def _challenge_thesis_under_pressure(item: dict[str, Any]) -> str:
    active_thesis = item.get("active_thesis") or {}
    thesis_text = str(active_thesis.get("thesis_text", "")).strip()
    if thesis_text:
        return thesis_text
    if item["signal_alignment"] == "diverging":
        return (
            f"The implicit thesis is that a {item['positioning_direction']} to {item['label']} still deserves this size "
            "even though the current STF/algo stack is pointing the other way."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"The implicit thesis is that the current {item['label']} signal is robust enough to trust even if the latest move "
            f"is largely {_friendly_driver_name(item['decomposition_driver'])}-driven."
        )
    return f"The implicit thesis is that {item['label']} remains an intentional conviction position rather than legacy implementation residue."


def _challenge_positioning_tension(item: dict[str, Any]) -> str:
    top_sources = _top_security_names(item, limit=2)
    source_text = f" Top underlying names include {', '.join(top_sources)}." if top_sources else ""
    return (
        f"Fund weight is {item['portfolio_weight']:.2f}% versus benchmark {item['benchmark_weight']:.2f}%, "
        f"leaving a {item['active_weight']:+.2f} pt active {item['positioning_direction']} in {item['label']}."
        f"{source_text}"
    )


def _challenge_model_signal_tension(item: dict[str, Any]) -> str:
    vir_now = _format_signal_value(item.get("vir_now"))
    vir_delta = _format_signal_delta(item.get("vir_delta_mom"))
    algo_active = _format_pct_value(item.get("algo_active_weight"))
    return (
        f"STF is {item['vir_direction']} at {vir_now}"
        f"{vir_delta}, while the algo active weight is {algo_active} (relative to benchmark) and points {item['algo_direction']}."
    )


def _challenge_vir_decomposition_readthrough(item: dict[str, Any]) -> str:
    driver = item.get("decomposition_driver", "")
    if not driver:
        return "No STF decomposition row was available in the current packet."
    if item["decomposition_assessment"] == "broad_based":
        return (
            f"The STF move looks broad-based rather than one-off noise, even though {_friendly_driver_name(driver)} is the largest single contributor."
        )
    if item["decomposition_assessment"] == "valuation_led":
        return (
            f"The signal is being driven mainly by {_friendly_driver_name(driver)}, so confirmation should come from fresher "
            "fundamental follow-through rather than treating the headline move as fully underwritten."
        )
    if item["decomposition_assessment"] == "currency_led":
        return (
            f"The signal is being driven mainly by {_friendly_driver_name(driver)}, so the PM should separate macro/currency effects "
            "from the underlying asset-class thesis."
        )
    return (
        f"The dominant decomposition input is {_friendly_driver_name(driver)}, which still reads as part of a fundamentally usable signal."
    )


def _challenge_relative_signal_readthrough(item: dict[str, Any]) -> str:
    ctx = item.get("stf_relative_context")
    if not ctx or item.get("vir_now") is None:
        return ""
    stf_pct = f"{item['vir_now'] * 100:+.2f}%"
    median_pct = f"{ctx['universe_median_stf'] * 100:+.2f}%"
    universe = ctx["universe"]
    side = "above" if ctx["vs_median"] >= 0 else "below"
    base = (
        f"STF is {stf_pct} in absolute terms but ranks #{ctx['rank']} of {ctx['universe_size']} in {universe} "
        f"({side} the {median_pct} universe median)"
    )
    if ctx.get("universe_all_negative"):
        driver = ctx.get("universe_dominant_driver", "")
        driver_text = f" and led by {_friendly_driver_name(driver)}" if driver else ""
        base += (
            f" — the whole {universe} complex is negative{driver_text}, a regime backdrop, so this exposure is "
            "relatively preferred even though the absolute signal is negative"
        )
    if ctx.get("historical_percentile") is not None:
        pct = round(ctx["historical_percentile"] * 100)
        win = ctx.get("history_window_months", STF_HISTORY_WINDOW)
        base += (
            f". Versus its own {win}-month history the current STF is at the {_ordinal(pct)} percentile, "
            "a separate read from the peer rank"
        )
    return base + "."


def _challenge_market_context_readthrough(item: dict[str, Any]) -> str:
    summary = _summary_lead(item.get("sharepoint_research_summary", ""))
    if summary:
        return summary
    return "No matched current research deck was available for a direct market-context readthrough in this packet."


def _challenge_measured_risk_readthrough(item: dict[str, Any], *, risk_context: dict[str, Any]) -> str:
    sector_match = _risk_sector_match(item, risk_context=risk_context)
    style_match = _risk_style_match(item, risk_context=risk_context)
    if sector_match:
        holdings = [
            security.get("security_name", "")
            for security in sector_match.get("top_sector_holdings", [])
            if security.get("security_name")
        ]
        holdings_text = f" Key holdings in that risk bucket include {', '.join(holdings[:3])}." if holdings else ""
        return (
            f"Measured risk currently points to {sector_match['risk_driver']} as a relevant driver at "
            f"{sector_match.get('share_of_variance_pct', 0.0):.2f}% of active variance for the mapped "
            f"{sector_match.get('mapped_sector', item['label'])} bucket.{holdings_text}"
        )
    if style_match:
        return (
            f"Measured style risk is elevated in {style_match['label']} at {style_match.get('share_of_variance_pct', 0.0):.2f}% "
            "of active variance, which raises the bar for holding a large style expression without fresh underwriting."
        )
    specific = _specific_watch_match(item, risk_context=risk_context)
    if specific:
        return (
            f"This position also appears in the specific-risk watchlist, which means the active weight is large enough "
            "that position-level outcomes matter even if the top-down signal looks mixed."
        )
    return "No direct measured-risk match was found for this challenge candidate in the current risk workbook."


def _challenge_return_attribution_readthrough(item: dict[str, Any], *, risk_context: dict[str, Any]) -> str:
    return_mtd = risk_context.get("return_attribution_mtd", {})
    if not return_mtd:
        return "No month-to-date return attribution block was available from the risk workbook."
    if item["positioning_direction"] == "underweight":
        contribution = return_mtd.get("period_underweight_return")
        return (
            f"Month-to-date underweight positions contributed {contribution:.2f}% if measured on the risk workbook window, "
            "so keeping a large underweight requires confidence that the thesis still outweighs the recent performance drag."
        ) if contribution is not None else "Return attribution did not provide a usable underweight contribution figure."
    contribution = return_mtd.get("period_overweight_return")
    return (
        f"Month-to-date overweight positions contributed {contribution:.2f}% over the risk workbook window, "
        "which helps frame whether this active bet is being paid for in current performance."
    ) if contribution is not None else "Return attribution did not provide a usable overweight contribution figure."


def _challenge_pm_decision_fork(item: dict[str, Any]) -> str:
    direction = item["positioning_direction"]
    return (
        f"Decide whether to defend the current {direction} as an intentional thesis, resize it if the evidence no longer supports "
        "the current scale, or keep it on watch pending fresher signal and underwriting evidence."
    )


def _challenge_primary_pm_question(item: dict[str, Any]) -> str:
    active_thesis = item.get("active_thesis") or {}
    thesis_text = str(active_thesis.get("thesis_text", "")).strip()
    if thesis_text:
        return (
            f"What specific current evidence still supports the thesis '{thesis_text}' given the portfolio is {item['active_weight']:+.2f} pts "
            f"{item['positioning_direction']} and the latest STF/algo stack is {item['vir_direction']}/{item['algo_direction']}?"
        )
    if item["signal_alignment"] == "diverging":
        return (
            f"What is the live underwriting case for keeping {item['label']} at {item['active_weight']:+.2f} pts "
            f"{item['positioning_direction']} when both the STF and the algo active weight currently point {item['vir_direction']}/{item['algo_direction']}?"
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"What evidence would make us trust the {item['label']} view as a durable thesis rather than a mostly "
            f"{_friendly_driver_name(item['decomposition_driver'])}-led move?"
        )
    return f"What current evidence still justifies keeping {item['label']} at this size rather than treating it as a position that needs to be refreshed?"


def _challenge_evidence_needed_next(item: dict[str, Any]) -> str:
    active_thesis = item.get("active_thesis") or {}
    falsification = str(active_thesis.get("falsification_conditions", "")).strip()
    if falsification:
        return falsification
    if item["signal_alignment"] == "diverging":
        return (
            f"Check the next STF decomposition, top-holding lineage inside {item['label']}, and any updated research or earnings/rates context that would explain why the active position should stay off-signal."
        )
    if item["decomposition_assessment"] in {"valuation_led", "currency_led"}:
        return (
            f"Check whether the next month's signal still leans on {_friendly_driver_name(item['decomposition_driver'])} or broadens into a more durable fundamental confirmation."
        )
    return f"Check the next month's STF/algo confirmation plus top-holding lineage to confirm that {item['label']} is still an intentional expression."


def _challenge_source_quality(item: dict[str, Any]) -> str:
    parts = ["model", "positioning"]
    if item.get("active_thesis", {}).get("thesis_text"):
        parts.append("memory")
    elif item.get("internal_history_excerpt"):
        parts.append("internal_history")
    else:
        parts.append("missing_direct_prior_thesis")
    if item.get("sharepoint_research_summary"):
        parts.append("sharepoint_research")
    return "+".join(parts)


def _challenge_research_status(item: dict[str, Any], *, logical_snapshot_date: str) -> dict[str, Any]:
    primary_match = item.get("sharepoint_research", {}).get("primary_match")
    if not primary_match:
        return {"status": "missing_research_match", "months_old": None, "folder_month": ""}
    folder_month = str(primary_match.get("folder_month", "")).strip()
    if not folder_month:
        return {"status": "matched_without_month", "months_old": None, "folder_month": ""}
    months_old = _months_between(folder_month, logical_snapshot_date.replace("-", "")[:6])
    if months_old is None:
        return {"status": "matched_without_month", "months_old": None, "folder_month": folder_month}
    if months_old >= 24:
        status = "stale_research_match"
    elif months_old >= 12:
        status = "aging_research_match"
    else:
        status = "current_research_match"
    return {"status": status, "months_old": months_old, "folder_month": folder_month}


def _challenge_top_holding_lineage(item: dict[str, Any]) -> str:
    securities = item.get("source_breakdown", {}).get("securities", [])
    if not securities:
        return "No security lineage was available for this challenge candidate."
    lines = []
    for security in securities[:3]:
        name = str(security.get("security_name", "")).strip()
        active_weight = security.get("active_weight", 0.0)
        sources = [
            f"{source.get('source_name', '')} {float(source.get('portfolio_weight', 0.0)):.2f}%"
            for source in security.get("sources", [])[:2]
            if source.get("source_name")
        ]
        source_text = f" via {', '.join(sources)}" if sources else ""
        if name:
            lines.append(f"{name} ({active_weight:+.2f} pts active){source_text}")
    return "; ".join(lines) if lines else "No security lineage was available for this challenge candidate."


def _challenge_priority_score(
    item: dict[str, Any],
    *,
    risk_context: dict[str, Any],
    research_status: dict[str, Any],
) -> float:
    score = abs(float(item.get("active_weight", 0.0))) * 1.4
    if item.get("signal_alignment") == "diverging":
        score += 4.0
    elif item.get("signal_alignment") == "partially_aligned":
        score += 2.0
    if item.get("decomposition_assessment") in {"valuation_led", "currency_led"}:
        score += 1.0
    if research_status.get("status") == "stale_research_match":
        score += 2.0
    elif research_status.get("status") == "missing_research_match":
        score += 1.5
    if item.get("active_thesis", {}).get("thesis_text"):
        score += 0.5
    elif item.get("internal_history_excerpt"):
        score += 0.25
    else:
        score += 1.0
    sector_match = _risk_sector_match(item, risk_context=risk_context)
    if sector_match:
        score += min(3.0, float(sector_match.get("share_of_variance_pct", 0.0)) / 1.5)
    style_match = _risk_style_match(item, risk_context=risk_context)
    if style_match:
        score += min(2.0, float(style_match.get("share_of_variance_pct", 0.0)) / 8.0)
    if _specific_watch_match(item, risk_context=risk_context):
        score += 1.5
    return_mtd = risk_context.get("return_attribution_mtd", {})
    if return_mtd:
        factor_drag = float(return_mtd.get("active_industry_factor_returns") or 0.0)
        underweight_drag = float(return_mtd.get("period_underweight_return") or 0.0)
        overweight_drag = float(return_mtd.get("period_overweight_return") or 0.0)
        if item.get("positioning_direction") == "underweight" and underweight_drag < 0:
            score += min(2.0, abs(underweight_drag))
        if item.get("positioning_direction") == "overweight" and overweight_drag <= 0:
            score += 1.5
        if item.get("category") == "Eq Sector" and factor_drag < 0:
            score += min(1.5, abs(factor_drag))
    return score


def _risk_sector_match(item: dict[str, Any], *, risk_context: dict[str, Any]) -> dict[str, Any] | None:
    if item.get("category") != "Eq Sector":
        return None
    label = str(item.get("label", "")).strip()
    for row in risk_context.get("likely_holdings_contributors", []):
        if str(row.get("mapped_sector", "")).strip() == label:
            return row
    return None


def _risk_style_match(item: dict[str, Any], *, risk_context: dict[str, Any]) -> dict[str, Any] | None:
    if item.get("category") != "Eq Size / Style":
        return None
    label = str(item.get("label", "")).lower()
    style_rows = risk_context.get("top_style_risk_drivers", [])
    if any(token in label for token in ("small", "mid", "large")):
        return next((row for row in style_rows if row.get("label") == "Size"), None)
    if "growth" in label or "value" in label:
        return next((row for row in style_rows if row.get("label") in {"Medium-Term Momentum", "Market Sensitivity"}), None)
    return None


def _specific_watch_match(item: dict[str, Any], *, risk_context: dict[str, Any]) -> dict[str, Any] | None:
    label = str(item.get("label", "")).strip()
    category = str(item.get("category", "")).strip()
    return next(
        (
            row
            for row in risk_context.get("specific_risk_watchlist", [])
            if str(row.get("label", "")).strip() == label and str(row.get("category", "")).strip() == category
        ),
        None,
    )


def _months_between(folder_month: str, logical_month: str) -> int | None:
    if len(folder_month) != 6 or len(logical_month) != 6:
        return None
    try:
        fy, fm = int(folder_month[:4]), int(folder_month[4:6])
        ly, lm = int(logical_month[:4]), int(logical_month[4:6])
    except ValueError:
        return None
    return (ly - fy) * 12 + (lm - fm)


def _challenge_internal_context_summary(item: dict[str, Any]) -> str:
    active_thesis = item.get("active_thesis") or {}
    thesis_text = str(active_thesis.get("thesis_text", "")).strip()
    if thesis_text:
        return thesis_text
    excerpt = str(item.get("internal_history_excerpt", "")).strip()
    if excerpt:
        return _summary_lead(excerpt)
    return "Direct prior thesis evidence is missing in the current packet."


def _challenge_devils_advocate_statement(item: dict[str, Any]) -> str:
    if item["signal_alignment"] == "diverging":
        return (
            f"The portfolio may be carrying legacy conviction in {item['label']} while the current signal stack is already telling a different story."
        )
    return (
        f"The {item['label']} position may still be right, but the evidence could be narrower and more mechanical than the current sizing implies."
    )


def _top_security_names(item: dict[str, Any], *, limit: int) -> list[str]:
    securities = item.get("source_breakdown", {}).get("securities", [])
    names = []
    for security in securities[:limit]:
        name = str(security.get("security_name", "")).strip()
        if name:
            names.append(name)
    return names


def _summary_lead(text: str, *, limit: int = 220) -> str:
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0]
    if len(sentence) <= limit:
        return sentence
    return sentence[: limit - 3].rstrip() + "..."


def _friendly_driver_name(driver: str) -> str:
    mapping = {
        "growth": "growth",
        "yield": "yield",
        "inflation": "inflation",
        "currency_usd": "currency",
        "valuation_adjustment_top_down": "top-down valuation adjustment",
        "valuation_adjustment_combined": "combined valuation adjustment",
        "valuation_adjustment_bottom_up": "bottom-up valuation adjustment",
    }
    return mapping.get(driver, driver.replace("_", " "))


def _format_signal_value(value: float | None) -> str:
    # STF is a return-style signal stored as a decimal; surface it as a percentage.
    if value is None:
        return "missing"
    return f"{value * 100:+.2f}%"


def _format_signal_delta(value: float | None) -> str:
    if value is None:
        return ""
    return f" ({value * 100:+.2f}% MoM)"


def _format_pct_value(value: float | None) -> str:
    if value is None:
        return "missing"
    return f"{value:+.2f} pts"


def _benchmark_name_from_detail_rows(
    rows: list[dict[str, str]],
    *,
    fund: str,
    snapshot_date: str,
) -> str:
    """Return the benchmark source name carried by the PCT-derived detail rows."""
    contribution_by_source: dict[str, float] = {}
    for row in rows:
        if row.get("fund", "").strip() != fund:
            continue
        if row.get("snapshot_date", "").strip() != snapshot_date:
            continue
        benchmark_contribution = abs(_to_float(row.get("fund_benchmark_security_contribution")))
        if benchmark_contribution <= 1e-12:
            continue
        source_name = row.get("account_name", "").strip()
        if not source_name:
            continue
        contribution_by_source[source_name] = contribution_by_source.get(source_name, 0.0) + benchmark_contribution
    if not contribution_by_source:
        return ""
    return max(contribution_by_source, key=contribution_by_source.get)


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
