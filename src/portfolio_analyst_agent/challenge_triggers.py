"""Deterministic v1 challenge trigger evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import csv
from fnmatch import fnmatch
import json
from pathlib import Path
from typing import Any

from .acid_mapping import DEFAULT_ACID_MAPPING_CSV, MappingIndex, load_mapping
from .csv_sources import open_csv_text, resolve_existing_csv_source
from .equity_history import DEFAULT_EQUITY_VIR_DATASET_CSV
from .evidence import file_sha256, stable_row_id
from .governance import DEFAULT_GOVERNANCE_PATH, GovernanceConfig, load_governance
from .row_ids import trigger_candidate_id


DEFAULT_VIR_HISTORY_CSV = DEFAULT_EQUITY_VIR_DATASET_CSV
MATERIALITY_THRESHOLD_ACTIVE = 1.0
STRONG_MATERIALITY_THRESHOLD_ACTIVE = 1.5
TOP_QUARTILE_MAX = 0.25
BOTTOM_QUARTILE_MIN = 0.75
STRONG_TOP_PERCENTILE_MAX = 0.20
STRONG_BOTTOM_PERCENTILE_MIN = 0.80
DECOMPOSITION_WEAKENING_THRESHOLD = 0.01
PEER_ADVANTAGE_THRESHOLD_STF = 1.0
SUPPORTED_TRIGGER_TYPES = ("sign_disagreement", "decomposition_rotation", "better_expression_available")
DEFERRED_TRIGGER_TYPES: tuple[str, ...] = ()
NON_EVALUABLE_VIR_WORKBOOK_TYPES = {"fixed_income_model"}
SUPPRESSING_EXCEPTION_REVIEW_STATES = {"approved", "applied"}
EQUITY_DECOMPOSITION_FIELDS = (
    "growth",
    "yield",
    "inflation",
    "currency_usd",
    "valuation_adjustment_top_down",
    "valuation_adjustment_combined",
    "valuation_adjustment_bottom_up",
)


@dataclass(frozen=True)
class QuartileContext:
    snapshot_date: date
    total_ranked_rows: int


def evaluate_challenge_triggers(
    fund: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    vir_history_csv: str | Path = DEFAULT_VIR_HISTORY_CSV,
    mapping_csv: str | Path = DEFAULT_ACID_MAPPING_CSV,
    governance_path: str | Path = DEFAULT_GOVERNANCE_PATH,
) -> dict[str, Any]:
    """Return deterministic trigger candidates for one fund and snapshot."""

    from .agent_tools import get_fund_snapshot, recall_memory

    snapshot = get_fund_snapshot(fund, snapshot_date=snapshot_date, as_of_date=as_of_date)
    selected_snapshot_date = date.fromisoformat(snapshot["run_metadata"]["snapshot_date"])
    selected_as_of_date = date.fromisoformat(snapshot["run_metadata"]["as_of_date"])
    memory = recall_memory(
        fund,
        snapshot_date=selected_snapshot_date,
        as_of_date=selected_as_of_date,
        scope=["exceptions", "thesis_ledger"],
    )

    quartile_lookup = _vir_quartile_lookup(vir_history_csv)
    decomp_lookup = _vir_decomposition_lookup(vir_history_csv)
    vir_signal_lookup = _latest_vir_signal_lookup(vir_history_csv, as_of_date=selected_as_of_date)
    mapping_index = load_mapping(as_of_date=selected_as_of_date, mapping_csv=mapping_csv)
    governance = load_governance(as_of_date=selected_as_of_date, governance_path=governance_path)
    trigger_rows = _dedupe_trigger_rows(snapshot["acid_rows"])
    exceptions = memory["exceptions"]
    thesis_by_acid = _active_thesis_by_acid(memory["thesis_ledger"])

    candidates: list[dict[str, Any]] = []
    suppressed_count = 0
    fired_count = 0
    borderline_count = 0
    not_evaluable_count = 0
    not_triggered_count = 0
    thesis_backed_row_count = 0

    for row in trigger_rows:
        sign_candidate = _evaluate_sign_disagreement_candidate(
            fund=fund,
            snapshot_date=selected_snapshot_date,
            row=row,
            quartile_lookup=quartile_lookup,
            exceptions=exceptions,
            governance=governance,
        )
        if sign_candidate is not None:
            candidates.append(sign_candidate)
            evaluation_status = sign_candidate["evaluation_status"]
            if evaluation_status == "suppressed":
                suppressed_count += 1
            elif evaluation_status == "fired":
                fired_count += 1
            elif evaluation_status == "borderline":
                borderline_count += 1
            elif evaluation_status == "not_triggered":
                not_triggered_count += 1
            else:
                not_evaluable_count += 1

        better_expression_candidate = _evaluate_better_expression_candidate(
            fund=fund,
            snapshot_date=selected_snapshot_date,
            row=row,
            mapping_index=mapping_index,
            vir_signal_lookup=vir_signal_lookup,
            exceptions=exceptions,
            governance=governance,
        )
        if better_expression_candidate is not None:
            candidates.append(better_expression_candidate)
            evaluation_status = better_expression_candidate["evaluation_status"]
            if evaluation_status == "suppressed":
                suppressed_count += 1
            elif evaluation_status == "fired":
                fired_count += 1
            elif evaluation_status == "borderline":
                borderline_count += 1
            elif evaluation_status == "not_triggered":
                not_triggered_count += 1
            else:
                not_evaluable_count += 1

        thesis = thesis_by_acid.get(row.get("acid", ""))
        if thesis is None:
            continue
        thesis_backed_row_count += 1
        rotation_candidate = _evaluate_decomposition_rotation_candidate(
            fund=fund,
            snapshot_date=selected_snapshot_date,
            row=row,
            thesis=thesis,
            decomp_lookup=decomp_lookup,
            exceptions=exceptions,
            governance=governance,
        )
        if rotation_candidate is None:
            continue
        candidates.append(rotation_candidate)
        evaluation_status = rotation_candidate["evaluation_status"]
        if evaluation_status == "suppressed":
            suppressed_count += 1
        elif evaluation_status == "fired":
            fired_count += 1
        elif evaluation_status == "borderline":
            borderline_count += 1
        elif evaluation_status == "not_triggered":
            not_triggered_count += 1
        else:
            not_evaluable_count += 1

    return {
        "fund": fund,
        "snapshot_date": selected_snapshot_date.isoformat(),
        "as_of_date": selected_as_of_date.isoformat(),
        "supported_trigger_types": list(SUPPORTED_TRIGGER_TYPES),
        "deferred_trigger_types": list(DEFERRED_TRIGGER_TYPES),
        "summary": {
            "candidate_count": len(candidates),
            "fired_count": fired_count,
            "borderline_count": borderline_count,
            "suppressed_count": suppressed_count,
            "not_triggered_count": not_triggered_count,
            "not_evaluable_count": not_evaluable_count,
            "thesis_backed_row_count": thesis_backed_row_count,
            "governance_version": governance.governance_version,
            "materiality_threshold_active": governance.float_param("materiality_threshold_active"),
            "strong_materiality_threshold_active": governance.float_param("strong_materiality_threshold_active"),
            "decomposition_weakening_threshold": governance.float_param("decomposition_weakening_threshold"),
            "peer_advantage_threshold_stf": governance.float_param("peer_advantage_threshold_stf"),
        },
        "trigger_candidates": candidates,
        "run_metadata": {
            "tool_version": "evaluate_challenge_triggers_v1",
            "source_file_hashes": _source_hashes(
                [
                    Path("artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv"),
                    Path("artifacts/rolled_exposures/fund_rollthrough_definitions.csv"),
                    Path("artifacts/rolled_exposures/fund_rollthrough_coverage.csv"),
                    Path(vir_history_csv),
                    Path(mapping_csv),
                    Path(governance_path),
                    Path("artifacts/agent_memory/memory_records.json"),
                ]
            ),
        },
    }


def _evaluate_sign_disagreement_candidate(
    *,
    fund: str,
    snapshot_date: date,
    row: dict[str, str],
    quartile_lookup: dict[tuple[date, str], QuartileContext],
    exceptions: list[dict[str, Any]],
    governance: GovernanceConfig | None = None,
) -> dict[str, Any] | None:
    governance = governance or _default_governance_for_tests()
    # Honor benchmark coverage (audit C2): when a fund has no benchmark to compare
    # against, `active_rolled_exposure` is intentionally null upstream. A sign
    # disagreement against a non-existent benchmark is meaningless, so do not fire.
    if not _benchmark_coverage_ok(row):
        return None

    active_value = _to_float(row.get("active_rolled_exposure"))
    if active_value is None or abs(active_value) < governance.float_param("materiality_threshold_active"):
        return None

    acid = row.get("acid", "")
    rank = _to_int(row.get("vir_rank_in_category_by_stf"))
    vir_snapshot_date = _optional_date(row.get("vir_snapshot_date"))
    workbook_type = row.get("vir_workbook_type", "")
    vir_join_status = row.get("vir_join_status", "")

    candidate = {
        "trigger_candidate_id": trigger_candidate_id(
            snapshot_date=snapshot_date,
            fund=fund,
            acid=acid,
            trigger_type="sign_disagreement",
        ),
        "acid": acid,
        "acid_type": row.get("acid_type", ""),
        "trigger_type": "sign_disagreement",
        "active_rolled_exposure": active_value,
        "fund_target_rolled_exposure": _to_float(row.get("fund_target_rolled_exposure")),
        "fund_benchmark_rolled_exposure": _to_float(row.get("fund_benchmark_rolled_exposure")),
        "vir_snapshot_date": row.get("vir_snapshot_date", ""),
        "vir_workbook_type": workbook_type,
        "vir_rank_in_category_by_stf": rank,
        "vir_stf": _to_float(row.get("vir_stf")),
        "suppression_status": "not_suppressed",
        "suppressed_by_exception": False,
        "matching_exception_ids": [],
        "evidence": [
            {
                "artifact_path": "artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
                "row_id": row.get("row_id", ""),
            }
        ],
        "reason": "",
        "directional_view": "unknown",
        "active_direction": "overweight" if active_value > 0 else "underweight",
        "evaluation_status": "not_evaluable",
    }

    if vir_join_status != "matched_to_vir":
        candidate["reason"] = "VIR is not matched for this row."
        return candidate

    if workbook_type in NON_EVALUABLE_VIR_WORKBOOK_TYPES:
        candidate["reason"] = "Fixed income VIR trigger evaluation is not implemented yet."
        return candidate

    if vir_snapshot_date is None or rank is None:
        candidate["reason"] = "VIR rank context is missing for this row."
        return candidate

    quartile_context = quartile_lookup.get((vir_snapshot_date, workbook_type))
    if quartile_context is None or quartile_context.total_ranked_rows <= 0:
        candidate["reason"] = "VIR category size is unavailable for quartile evaluation."
        return candidate

    rank_percentile = rank / quartile_context.total_ranked_rows
    directional_view = _directional_view_from_rank_percentile(rank_percentile, governance=governance)
    candidate["directional_view"] = directional_view
    candidate["vir_rank_percentile"] = rank_percentile
    candidate["vir_category_size"] = quartile_context.total_ranked_rows

    if directional_view == "neutral":
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "VIR signal is in the middle quartiles and does not trigger."
        return candidate

    disagreement = (
        candidate["active_direction"] == "overweight" and directional_view == "underweight"
    ) or (
        candidate["active_direction"] == "underweight" and directional_view == "overweight"
    )
    if not disagreement:
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "Active direction does not conflict with the VIR directional view."
        return candidate

    matching_exception_ids = _matching_exception_ids(exceptions, acid=acid, trigger_type="sign_disagreement")
    candidate["matching_exception_ids"] = matching_exception_ids

    if matching_exception_ids:
        candidate["suppression_status"] = "suppressed"
        candidate["suppressed_by_exception"] = True
        candidate["evaluation_status"] = "suppressed"
        candidate["reason"] = "Trigger is covered by an active accepted exception."
        return candidate

    candidate["suppression_status"] = "not_suppressed"
    if _is_borderline_candidate(active_value=active_value, rank_percentile=rank_percentile, governance=governance):
        candidate["evaluation_status"] = "borderline"
        candidate["reason"] = (
            "Material active exposure conflicts with the VIR quartile directional view, "
            "but the disagreement is currently classified as borderline rather than a full fired trigger."
        )
        return candidate

    candidate["evaluation_status"] = "fired"
    candidate["reason"] = (
        "Material active exposure conflicts with the VIR directional view and meets the current stronger "
        "fire threshold."
    )
    return candidate


def _evaluate_decomposition_rotation_candidate(
    *,
    fund: str,
    snapshot_date: date,
    row: dict[str, str],
    thesis: dict[str, Any],
    decomp_lookup: dict[tuple[date, str], dict[str, float]],
    exceptions: list[dict[str, Any]],
    governance: GovernanceConfig | None = None,
) -> dict[str, Any] | None:
    governance = governance or _default_governance_for_tests()
    active_value = _to_float(row.get("active_rolled_exposure"))
    if active_value is None or abs(active_value) < governance.float_param("materiality_threshold_active"):
        return None

    acid = row.get("acid", "")
    vir_snapshot_date = _optional_date(row.get("vir_snapshot_date"))
    workbook_type = row.get("vir_workbook_type", "")
    vir_join_status = row.get("vir_join_status", "")
    prior_decomp = _parse_decomposition_payload(thesis.get("last_affirmed_decomp"))
    prior_snapshot_date = _optional_date(thesis.get("last_affirmed_snapshot_date"))

    candidate = {
        "trigger_candidate_id": trigger_candidate_id(
            snapshot_date=snapshot_date,
            fund=fund,
            acid=acid,
            trigger_type="decomposition_rotation",
        ),
        "acid": acid,
        "acid_type": row.get("acid_type", ""),
        "trigger_type": "decomposition_rotation",
        "active_rolled_exposure": active_value,
        "fund_target_rolled_exposure": _to_float(row.get("fund_target_rolled_exposure")),
        "fund_benchmark_rolled_exposure": _to_float(row.get("fund_benchmark_rolled_exposure")),
        "vir_snapshot_date": row.get("vir_snapshot_date", ""),
        "vir_workbook_type": workbook_type,
        "suppression_status": "not_suppressed",
        "suppressed_by_exception": False,
        "matching_exception_ids": [],
        "thesis_id": thesis.get("thesis_id", ""),
        "thesis_status": thesis.get("status", ""),
        "prior_affirmed_snapshot_date": thesis.get("last_affirmed_snapshot_date", ""),
        "evidence": [
            {
                "artifact_path": "artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
                "row_id": row.get("row_id", ""),
            }
        ],
        "reason": "",
        "evaluation_status": "not_evaluable",
    }

    if vir_join_status != "matched_to_vir":
        candidate["reason"] = "VIR is not matched for this row."
        return candidate

    if workbook_type in NON_EVALUABLE_VIR_WORKBOOK_TYPES:
        candidate["reason"] = "Fixed income decomposition rotation is not implemented yet."
        return candidate

    if workbook_type != "equity_model":
        candidate["reason"] = "Decomposition rotation is currently implemented only for equity VIR rows."
        return candidate

    if vir_snapshot_date is None:
        candidate["reason"] = "Current VIR snapshot date is missing for this row."
        return candidate

    if not prior_decomp:
        candidate["reason"] = "Thesis memory does not yet include a prior affirmed decomposition payload."
        return candidate

    current_decomp = decomp_lookup.get((vir_snapshot_date, acid))
    if not current_decomp:
        candidate["reason"] = "Current decomposition values are unavailable for this ACID and VIR snapshot."
        return candidate

    prior_driver = _dominant_driver(prior_decomp)
    current_driver = _dominant_driver(current_decomp)
    if prior_driver is None or current_driver is None:
        candidate["reason"] = "Dominant decomposition driver could not be determined."
        return candidate

    prior_driver_name, prior_driver_value = prior_driver
    current_driver_name, current_driver_value = current_driver

    candidate["prior_dominant_driver"] = prior_driver_name
    candidate["prior_dominant_driver_value"] = prior_driver_value
    candidate["current_dominant_driver"] = current_driver_name
    candidate["current_dominant_driver_value"] = current_driver_value
    candidate["prior_snapshot_date"] = prior_snapshot_date.isoformat() if prior_snapshot_date else ""

    changed_driver = prior_driver_name != current_driver_name
    weakened_enough = _weakened_enough(
        prior_driver_value=prior_driver_value,
        current_driver_value=current_decomp.get(prior_driver_name),
        governance=governance,
    )
    candidate["driver_changed"] = changed_driver
    candidate["prior_driver_weakened"] = weakened_enough

    if not changed_driver:
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "Dominant decomposition driver has not changed since the last affirmed thesis."
        return candidate

    if not weakened_enough:
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "Dominant driver changed, but the prior driver has not weakened enough to count as a rotation."
        return candidate

    matching_exception_ids = _matching_exception_ids(exceptions, acid=acid, trigger_type="decomposition_rotation")
    candidate["matching_exception_ids"] = matching_exception_ids
    if matching_exception_ids:
        candidate["suppression_status"] = "suppressed"
        candidate["suppressed_by_exception"] = True
        candidate["evaluation_status"] = "suppressed"
        candidate["reason"] = "Decomposition rotation is covered by an active accepted exception."
        return candidate

    candidate["evaluation_status"] = "fired"
    candidate["reason"] = (
        "Dominant decomposition driver has changed and the prior driver has weakened enough to count as a rotation."
    )
    return candidate


def _evaluate_better_expression_candidate(
    *,
    fund: str,
    snapshot_date: date,
    row: dict[str, str],
    mapping_index: MappingIndex,
    vir_signal_lookup: dict[str, dict[str, Any]],
    exceptions: list[dict[str, Any]],
    governance: GovernanceConfig | None = None,
) -> dict[str, Any] | None:
    governance = governance or _default_governance_for_tests()
    active_value = _to_float(row.get("active_rolled_exposure"))
    if active_value is None or abs(active_value) < governance.float_param("materiality_threshold_active"):
        return None

    acid = row.get("acid", "")
    current_stf = _to_float(row.get("vir_stf"))
    vir_join_status = row.get("vir_join_status", "")
    workbook_type = row.get("vir_workbook_type", "")

    candidate = {
        "trigger_candidate_id": trigger_candidate_id(
            snapshot_date=snapshot_date,
            fund=fund,
            acid=acid,
            trigger_type="better_expression_available",
        ),
        "acid": acid,
        "acid_type": row.get("acid_type", ""),
        "trigger_type": "better_expression_available",
        "active_rolled_exposure": active_value,
        "fund_target_rolled_exposure": _to_float(row.get("fund_target_rolled_exposure")),
        "fund_benchmark_rolled_exposure": _to_float(row.get("fund_benchmark_rolled_exposure")),
        "vir_snapshot_date": row.get("vir_snapshot_date", ""),
        "vir_workbook_type": workbook_type,
        "vir_stf": current_stf,
        "suppression_status": "not_suppressed",
        "suppressed_by_exception": False,
        "matching_exception_ids": [],
        "peer_advantage_threshold_stf": governance.float_param("peer_advantage_threshold_stf"),
        "evidence": [
            {
                "artifact_path": "artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
                "row_id": row.get("row_id", ""),
            }
        ],
        "reason": "",
        "evaluation_status": "not_evaluable",
    }

    if vir_join_status != "matched_to_vir" or current_stf is None:
        candidate["reason"] = "Current VIR signal is unavailable for expression comparison."
        return candidate

    if workbook_type in NON_EVALUABLE_VIR_WORKBOOK_TYPES:
        candidate["reason"] = "Fixed income better-expression trigger evaluation is not implemented yet."
        return candidate

    mapping = mapping_index.get(acid)
    if mapping is None:
        candidate["reason"] = "ACID mapping is missing, so peer expression comparison is unavailable."
        return candidate

    peers = [peer for peer in mapping_index.peers_for(mapping) if peer.fields.get("investable_flag") == "true"]
    scored_peers = []
    for peer in peers:
        signal = vir_signal_lookup.get(peer.acid)
        if signal is None:
            continue
        peer_stf = _to_float(signal.get("stf"))
        if peer_stf is None:
            continue
        advantage = peer_stf - current_stf
        scored_peers.append((advantage, peer, signal, peer_stf))

    if not scored_peers:
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "No investable peer in the mapping peer set has a comparable VIR STF signal."
        return candidate

    best_advantage, best_peer, best_signal, best_peer_stf = max(scored_peers, key=lambda item: item[0])
    candidate["best_peer_acid"] = best_peer.acid
    candidate["best_peer_asset_class_name"] = best_peer.fields.get("asset_class_name", "")
    candidate["best_peer_interpretation_type"] = best_peer.fields.get("interpretation_type", "")
    candidate["best_peer_vir_snapshot_date"] = best_signal.get("snapshot_date", "")
    candidate["best_peer_vir_stf"] = best_peer_stf
    candidate["best_peer_stf_advantage"] = best_advantage
    candidate["comparison_group"] = mapping.fields.get("comparison_group", "")
    candidate["relative_value_group"] = mapping.fields.get("relative_value_group", "")
    candidate["evidence"].append(
        {
            "artifact_path": DEFAULT_VIR_HISTORY_CSV.as_posix(),
            "row_id": best_signal.get("row_id", ""),
        }
    )

    if best_advantage < governance.float_param("peer_advantage_threshold_stf"):
        candidate["evaluation_status"] = "not_triggered"
        candidate["reason"] = "Best mapped peer does not clear the STF advantage threshold."
        return candidate

    matching_exception_ids = _matching_exception_ids(exceptions, acid=acid, trigger_type="better_expression_available")
    candidate["matching_exception_ids"] = matching_exception_ids
    if matching_exception_ids:
        candidate["suppression_status"] = "suppressed"
        candidate["suppressed_by_exception"] = True
        candidate["evaluation_status"] = "suppressed"
        candidate["reason"] = "Better-expression trigger is covered by an active accepted exception."
        return candidate

    candidate["evaluation_status"] = "fired"
    candidate["reason"] = (
        "A mapped investable peer has a materially better STF signal, suggesting the current active expression "
        "may not be the cleanest implementation of the opportunity set."
    )
    return candidate


def _dedupe_trigger_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row.get("acid_type", ""), row.get("acid", "")), []).append(row)

    selected: list[dict[str, str]] = []
    for group_rows in grouped.values():
        local_real = next((row for row in group_rows if row.get("algo_perspective") == "local_real"), None)
        if local_real is not None:
            selected.append(local_real)
            continue
        # Deterministic fallback: pick by a stable key (perspective name, then row_id)
        # rather than CSV row order, so the same input always yields the same trigger
        # row (audit H2: `group_rows[0]` was order-dependent).
        selected.append(min(group_rows, key=lambda row: (row.get("algo_perspective") or "", row.get("row_id") or "")))
    return selected


def _vir_quartile_lookup(vir_history_csv: str | Path) -> dict[tuple[date, str], QuartileContext]:
    counts: dict[tuple[date, str], int] = {}
    with open_csv_text(vir_history_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            snapshot_date = _optional_date(row.get("snapshot_date"))
            workbook_type = row.get("workbook_type", "")
            stf = _to_float(row.get("stf"))
            if snapshot_date is None or not workbook_type or stf is None:
                continue
            key = (snapshot_date, workbook_type)
            counts[key] = counts.get(key, 0) + 1
    return {
        key: QuartileContext(snapshot_date=key[0], total_ranked_rows=count)
        for key, count in counts.items()
    }


def _vir_decomposition_lookup(vir_history_csv: str | Path) -> dict[tuple[date, str], dict[str, float]]:
    lookup: dict[tuple[date, str], dict[str, float]] = {}
    with open_csv_text(vir_history_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            snapshot_date = _optional_date(row.get("snapshot_date"))
            acid = row.get("acid", "")
            if snapshot_date is None or not acid:
                continue
            values: dict[str, float] = {}
            for field in EQUITY_DECOMPOSITION_FIELDS:
                value = _to_float(row.get(field))
                if value is not None:
                    values[field] = value
            if values:
                lookup[(snapshot_date, acid)] = values
    return lookup


def _latest_vir_signal_lookup(vir_history_csv: str | Path, *, as_of_date: date) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    path = Path(vir_history_csv)
    with open_csv_text(path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            snapshot_date = _optional_date(row.get("snapshot_date"))
            acid = row.get("acid", "")
            if snapshot_date is None or snapshot_date > as_of_date or not acid:
                continue
            current = lookup.get(acid)
            if current is not None and _optional_date(current.get("snapshot_date")) >= snapshot_date:
                continue
            lookup[acid] = {
                **row,
                "row_id": row.get("row_id", "") or stable_row_id(row, namespace=path.as_posix()),
            }
    return lookup


def _directional_view_from_rank_percentile(
    rank_percentile: float,
    governance: GovernanceConfig | None = None,
) -> str:
    governance = governance or _default_governance_for_tests()
    if rank_percentile <= governance.float_param("top_quartile_max"):
        return "overweight"
    if rank_percentile >= governance.float_param("bottom_quartile_min"):
        return "underweight"
    return "neutral"


def _is_borderline_candidate(
    *,
    active_value: float,
    rank_percentile: float,
    governance: GovernanceConfig | None = None,
) -> bool:
    governance = governance or _default_governance_for_tests()
    if abs(active_value) >= governance.float_param("strong_materiality_threshold_active"):
        return False
    if rank_percentile <= governance.float_param("top_quartile_max"):
        return rank_percentile > governance.float_param("strong_top_percentile_max")
    if rank_percentile >= governance.float_param("bottom_quartile_min"):
        return rank_percentile < governance.float_param("strong_bottom_percentile_min")
    return False


def _matching_exception_ids(
    exceptions: list[dict[str, Any]],
    *,
    acid: str,
    trigger_type: str,
) -> list[str]:
    matching_ids: list[str] = []
    for exception in exceptions:
        if exception.get("review_state") not in SUPPRESSING_EXCEPTION_REVIEW_STATES:
            continue
        covered_types = exception.get("trigger_types", [])
        if covered_types and trigger_type not in covered_types:
            continue
        scope = exception.get("scope", "")
        exception_acid = exception.get("acid", "")
        pattern = exception.get("acid_pattern", "")
        if scope == "fund_wide":
            matching_ids.append(exception.get("exception_id", ""))
        elif scope == "acid" and exception_acid == acid:
            matching_ids.append(exception.get("exception_id", ""))
        elif scope == "acid_pattern" and pattern and fnmatch(acid, pattern):
            matching_ids.append(exception.get("exception_id", ""))
    return [value for value in matching_ids if value]


def _active_thesis_by_acid(thesis_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    for row in thesis_rows:
        acid = str(row.get("acid", "")).strip()
        if acid:
            active[acid] = row
    return active


def _parse_decomposition_payload(raw_value: Any) -> dict[str, float]:
    if raw_value in (None, ""):
        return {}
    if isinstance(raw_value, dict):
        return {str(key): float(value) for key, value in raw_value.items() if value not in (None, "")}
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return {str(key): float(value) for key, value in parsed.items() if value not in (None, "")}
    return {}


def _dominant_driver(values: dict[str, float]) -> tuple[str, float] | None:
    eligible = [(name, value) for name, value in values.items() if name in EQUITY_DECOMPOSITION_FIELDS]
    if not eligible:
        return None
    return max(eligible, key=lambda item: abs(item[1]))


def _weakened_enough(
    *,
    prior_driver_value: float,
    current_driver_value: float | None,
    governance: GovernanceConfig | None = None,
) -> bool:
    governance = governance or _default_governance_for_tests()
    if current_driver_value is None:
        return True
    if prior_driver_value == 0:
        return current_driver_value != 0
    if prior_driver_value * current_driver_value < 0:
        return True
    return (
        abs(prior_driver_value) - abs(current_driver_value)
        >= governance.float_param("decomposition_weakening_threshold")
    )


def _default_governance_for_tests() -> GovernanceConfig:
    return GovernanceConfig(
        governance_version="legacy_module_defaults",
        effective_from=date(1900, 1, 1),
        parameters={
            "materiality_threshold_active": MATERIALITY_THRESHOLD_ACTIVE,
            "strong_materiality_threshold_active": STRONG_MATERIALITY_THRESHOLD_ACTIVE,
            "top_quartile_max": TOP_QUARTILE_MAX,
            "bottom_quartile_min": BOTTOM_QUARTILE_MIN,
            "strong_top_percentile_max": STRONG_TOP_PERCENTILE_MAX,
            "strong_bottom_percentile_min": STRONG_BOTTOM_PERCENTILE_MIN,
            "decomposition_weakening_threshold": DECOMPOSITION_WEAKENING_THRESHOLD,
            "peer_advantage_threshold_stf": PEER_ADVANTAGE_THRESHOLD_STF,
        },
        source_path=DEFAULT_GOVERNANCE_PATH,
        source_file_hash=None,
    )


def _source_hashes(paths: list[Path]) -> dict[str, str]:
    resolved_paths = [resolve_existing_csv_source(path) or path for path in paths]
    return {path.as_posix(): file_sha256(path) for path in resolved_paths if path.exists()}


def _to_float(raw_value: str | None) -> float | None:
    if raw_value in (None, ""):
        return None
    return float(raw_value)


def _to_int(raw_value: str | None) -> int | None:
    if raw_value in (None, ""):
        return None
    return int(float(raw_value))


def _benchmark_coverage_ok(row: dict[str, str]) -> bool:
    """Whether this fund has a populated benchmark to evaluate active bets against.

    Honors the explicit `benchmark_coverage_ok` flag emitted upstream (audit C2);
    falls back to benchmark-match presence for older alignment CSVs that predate it.
    """
    raw = row.get("benchmark_coverage_ok")
    if raw not in (None, ""):
        return str(raw).strip().lower() in {"true", "1", "yes"}
    return _to_float(row.get("benchmark_match_pct")) is not None


def _optional_date(raw_value: str | None) -> date | None:
    if raw_value in (None, ""):
        return None
    return date.fromisoformat(raw_value)


__all__ = ["evaluate_challenge_triggers"]
