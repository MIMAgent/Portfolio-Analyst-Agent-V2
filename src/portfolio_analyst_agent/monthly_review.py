"""Deterministic monthly review harness for Model 1."""

from __future__ import annotations

from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .agent_tools import DEFAULT_ALIGNMENT_CSV, evaluate_challenge_triggers, get_fund_snapshot, recall_memory
from .csv_sources import resolve_existing_csv_source
from .evidence import file_sha256
from .fund_review import DEFAULT_FUND_ORDER
from .governance import DEFAULT_GOVERNANCE_PATH, load_governance


DEFAULT_OUTPUT_ROOT = Path("artifacts/monthly_review")
DEFAULT_VIR_HISTORY_CSV = Path("artifacts/equity_vir_history.csv")
PARSER_VERSION = "rolled_exposure_alignment_multisignal_v1"
MAPPING_VERSION = "mapping_layer_pending_review"
ALGO_VERSION = "algo_workbooks_current"


def run_monthly_review(
    *,
    fund: str,
    snapshot_date: str | None = None,
    as_of_date: str,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    run_mode: str = "ad_hoc",
) -> dict[str, Any]:
    fund_snapshot = get_fund_snapshot(fund, snapshot_date=snapshot_date, as_of_date=as_of_date)
    effective_snapshot_date = fund_snapshot["run_metadata"]["snapshot_date"]
    governance = load_governance(as_of_date=as_of_date)
    prior_snapshot_date = _prior_snapshot_date(fund=fund, snapshot_date=effective_snapshot_date)
    memory = recall_memory(
        fund,
        snapshot_date=effective_snapshot_date,
        as_of_date=as_of_date,
    )
    triggers = evaluate_challenge_triggers(
        fund,
        snapshot_date=effective_snapshot_date,
        as_of_date=as_of_date,
    )

    review_run_id = _review_run_id(
        fund=fund,
        snapshot_date=effective_snapshot_date,
        as_of_date=as_of_date,
    )
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    review_dir = Path(output_root) / effective_snapshot_date / _slugify(fund)
    review_dir.mkdir(parents=True, exist_ok=True)

    acid_rows = fund_snapshot["acid_rows"]
    material_rows = _material_rows(acid_rows)
    evidence_index = _build_evidence_index(material_rows, triggers["trigger_candidates"])

    header = {
        "fund": fund,
        "snapshot_date": effective_snapshot_date,
        "prior_snapshot_date": prior_snapshot_date,
        "as_of_date": as_of_date,
        "review_run_id": review_run_id,
        "parser_version": PARSER_VERSION,
        "mapping_version": MAPPING_VERSION,
        "governance_version": governance.governance_version,
        "algo_version": ALGO_VERSION,
        "run_mode": run_mode,
    }

    change_brief = {
        "header": header,
        "executive_summary": _executive_summary(fund_snapshot, triggers),
        "material_movers": _material_movers(material_rows),
        "decomposition_narrative": _decomposition_narrative(memory, triggers),
        "lineage_notes": [],
        "sizing_artifact_summary": _sizing_artifact_summary(acid_rows),
        "memory_updates_summary": {
            "theses_affirmed": 0,
            "theses_updated": 0,
            "theses_marked_weakening": 0,
            "theses_marked_contradicted": 0,
            "theses_created": 0,
            "challenges_opened": 0,
            "challenges_closed": 0,
            "watch_items_opened": 0,
            "watch_items_closed": 0,
            "exceptions_logged": 0,
            "exceptions_expired": 0,
            "stale_items_flagged": 0,
            "proposed_memory_ops": [],
        },
        "triggers_fired_summary": triggers["summary"],
        "evidence_index": evidence_index,
    }

    sizing_considerations = {
        "header": {
            "fund": fund,
            "snapshot_date": effective_snapshot_date,
            "as_of_date": as_of_date,
            "review_run_id": review_run_id,
            "algo_version": ALGO_VERSION,
            "mapping_version": MAPPING_VERSION,
            "run_mode": run_mode,
        },
        "perspective_summary": _perspective_summary(acid_rows),
        "algo_vs_positioning_agreement": _algo_positioning_rows(acid_rows, "agreement"),
        "algo_vs_positioning_disagreement": _algo_positioning_rows(acid_rows, "disagreement"),
        "largest_algo_mom_changes": _largest_algo_mom_changes(acid_rows),
        "coverage_notes": _coverage_notes(fund_snapshot),
        "evidence_index": evidence_index,
    }

    challenge_items = _challenge_items(triggers["trigger_candidates"])
    challenge_brief = None
    if challenge_items:
        challenge_brief = {
            "header": {
                "fund": fund,
                "snapshot_date": effective_snapshot_date,
                "as_of_date": as_of_date,
                "review_run_id": review_run_id,
                "parser_version": PARSER_VERSION,
                "mapping_version": MAPPING_VERSION,
                "governance_version": governance.governance_version,
            },
            "items": challenge_items,
            "evidence_index": evidence_index,
        }

    run_payload = {
        "review_run_metadata": {
            **header,
            "generated_at": generated_at,
            "source_file_hashes": _source_hashes(),
        },
        "fund_snapshot_summary": {
            "coverage": fund_snapshot["coverage"],
            "memory_summary": memory["summary"],
            "trigger_summary": triggers["summary"],
        },
        "change_brief": change_brief,
        "sizing_considerations": sizing_considerations,
        "challenge_brief": challenge_brief,
    }

    _write_json(review_dir / "run_payload.json", run_payload)
    _write_json(review_dir / "change_brief_draft.json", change_brief)
    _write_json(review_dir / "sizing_considerations_draft.json", sizing_considerations)
    if challenge_brief is not None:
        _write_json(review_dir / "challenge_brief_draft.json", challenge_brief)
    _write_markdown(review_dir / "run_summary.md", _render_summary_markdown(run_payload))

    return {
        "fund": fund,
        "snapshot_date": effective_snapshot_date,
        "review_run_id": review_run_id,
        "output_dir": review_dir.as_posix(),
        "change_brief_json": (review_dir / "change_brief_draft.json").as_posix(),
        "sizing_considerations_json": (review_dir / "sizing_considerations_draft.json").as_posix(),
        "challenge_brief_json": (review_dir / "challenge_brief_draft.json").as_posix() if challenge_brief else "",
        "run_summary_md": (review_dir / "run_summary.md").as_posix(),
        "trigger_summary": triggers["summary"],
    }


def run_monthly_review_batch(
    *,
    funds: list[str] | None = None,
    snapshot_date: str | None = None,
    as_of_date: str,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    run_mode: str = "ad_hoc",
) -> dict[str, Any]:
    selected_funds = funds or list(DEFAULT_FUND_ORDER)
    results = [
        run_monthly_review(
            fund=fund,
            snapshot_date=snapshot_date,
            as_of_date=as_of_date,
            output_root=output_root,
            run_mode=run_mode,
        )
        for fund in selected_funds
    ]
    batch_payload = {
        "as_of_date": as_of_date,
        "snapshot_date": snapshot_date or "",
        "fund_count": len(results),
        "results": results,
    }
    batch_dir = Path(output_root) / (snapshot_date or results[0]["snapshot_date"])
    _write_json(batch_dir / "batch_index.json", batch_payload)
    return batch_payload


def _material_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped = _dedupe_acid_rows(rows)
    material = [
        row
        for row in deduped
        if _to_float(row.get("active_rolled_exposure")) is not None and abs(_to_float(row.get("active_rolled_exposure")) or 0.0) >= 1.0
    ]
    return sorted(material, key=lambda row: abs(_to_float(row.get("active_rolled_exposure")) or 0.0), reverse=True)


def _material_movers(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    movers = []
    for row in rows[:12]:
        movers.append(
            {
                "acid": row.get("acid", ""),
                "acid_type": row.get("acid_type", ""),
                "active_rolled_exposure": _to_float(row.get("active_rolled_exposure")),
                "target_rolled_exposure": _to_float(row.get("fund_target_rolled_exposure")),
                "benchmark_rolled_exposure": _to_float(row.get("fund_benchmark_rolled_exposure")),
                "vir_stf": _to_float(row.get("vir_stf")),
                "vir_delta_stf": _to_float(row.get("vir_delta_stf")),
                "vir_rank_change_by_stf": _to_float(row.get("vir_rank_change_by_stf")),
                "decomposition_drivers": {},
                "narrative": _mover_narrative(row),
                "evidence_pointers": [
                    {"artifact_path": DEFAULT_ALIGNMENT_CSV.as_posix(), "row_id": row.get("row_id", "")}
                ],
            }
        )
    return movers


def _mover_narrative(row: dict[str, str]) -> str:
    active = _to_float(row.get("active_rolled_exposure")) or 0.0
    direction = "overweight" if active > 0 else "underweight"
    return f"{row.get('acid', '')} is a material {direction} at {active:.4f} active exposure."


def _executive_summary(snapshot: dict[str, Any], triggers: dict[str, Any]) -> str:
    fund = snapshot["fund_metadata"]["fund"]
    coverage = snapshot["coverage"]
    summary = triggers["summary"]
    return (
        f"{fund} review loaded with target coverage {coverage['target_match_pct']}, "
        f"benchmark coverage {coverage['benchmark_match_pct']}, and "
        f"{summary['fired_count']} fired trigger candidates."
    )


def _decomposition_narrative(memory: dict[str, Any], triggers: dict[str, Any]) -> str:
    thesis_count = memory["summary"]["thesis_ledger_count"]
    thesis_backed = triggers["summary"].get("thesis_backed_row_count", 0)
    return (
        f"Thesis ledger entries available: {thesis_count}. "
        f"Thesis-backed trigger rows evaluated: {thesis_backed}."
    )


def _sizing_artifact_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    agreements = _algo_positioning_rows(rows, "agreement")[:5]
    disagreements = _algo_positioning_rows(rows, "disagreement")[:5]
    largest_changes = _largest_algo_mom_changes(rows)[:5]
    return {
        "artifact_path": "artifacts/monthly_review/<snapshot_date>/<fund>/sizing_considerations_draft.json",
        "headline_agreements": agreements,
        "headline_disagreements": disagreements,
        "largest_algo_mom_changes": largest_changes,
        "evidence_pointers": _collect_evidence(agreements + disagreements + largest_changes),
    }


def _perspective_summary(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        "local_real": _perspective_line(rows, "local_real"),
        "usd_unhedged": _perspective_line(rows, "usd_unhedged"),
    }


def _perspective_line(rows: list[dict[str, str]], perspective: str) -> str:
    perspective_rows = [row for row in rows if row.get("algo_perspective") == perspective and row.get("algo_join_status") == "matched_to_algo"]
    return f"{len(perspective_rows)} matched algo rows available for {perspective}."


def _algo_positioning_rows(rows: list[dict[str, str]], mode: str) -> list[dict[str, Any]]:
    deduped = [row for row in rows if row.get("algo_perspective") in {"local_real", "usd_unhedged"} and row.get("algo_join_status") == "matched_to_algo"]
    selected: list[dict[str, Any]] = []
    for row in deduped:
        active = _to_float(row.get("active_rolled_exposure"))
        algo_active = _to_float(row.get("algo_active_weight"))
        if active is None or algo_active is None or active == 0 or algo_active == 0:
            continue
        same_sign = active * algo_active > 0
        if mode == "agreement" and not same_sign:
            continue
        if mode == "disagreement" and same_sign:
            continue
        selected.append(
            {
                "acid": row.get("acid", ""),
                "perspective": row.get("algo_perspective", ""),
                "narrative": (
                    f"{row.get('acid', '')} shows {'agreement' if same_sign else 'disagreement'} "
                    f"between active exposure ({active:.4f}) and algo active weight ({algo_active:.4f})."
                ),
                "evidence_pointers": [
                    {"artifact_path": DEFAULT_ALIGNMENT_CSV.as_posix(), "row_id": row.get("row_id", "")}
                ],
                "_rank": abs(active - algo_active) if mode == "disagreement" else abs(active) + abs(algo_active),
            }
        )
    ordered = sorted(selected, key=lambda row: row["_rank"], reverse=True)[:10]
    for row in ordered:
        row.pop("_rank", None)
    return ordered


def _largest_algo_mom_changes(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        metric = _to_float(row.get("algo_active_weight_mom"))
        if metric is None:
            continue
        selected.append(
            {
                "acid": row.get("acid", ""),
                "perspective": row.get("algo_perspective", ""),
                "metric_type": "algo_active_weight_mom",
                "value": metric,
                "narrative": f"{row.get('acid', '')} has algo active MoM change of {metric:.4f}.",
                "evidence_pointers": [
                    {"artifact_path": DEFAULT_ALIGNMENT_CSV.as_posix(), "row_id": row.get("row_id", "")}
                ],
            }
        )
    return sorted(selected, key=lambda row: abs(row["value"]), reverse=True)[:10]


def _coverage_notes(snapshot: dict[str, Any]) -> str:
    coverage = snapshot["coverage"]
    return (
        f"Target coverage {coverage['target_match_pct']} and benchmark coverage "
        f"{coverage['benchmark_match_pct']}."
    )


def _challenge_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fired = [row for row in candidates if row.get("evaluation_status") == "fired"]
    items = []
    for row in fired:
        items.append(
            {
                "challenge_id": "",
                "trigger_candidate_id": row.get("trigger_candidate_id", ""),
                "acid": row.get("acid", ""),
                "trigger_type": row.get("trigger_type", ""),
                "position_summary": {
                    "active_rolled_exposure": row.get("active_rolled_exposure"),
                    "target_rolled_exposure": row.get("fund_target_rolled_exposure"),
                    "benchmark_rolled_exposure": row.get("fund_benchmark_rolled_exposure"),
                },
                "disagreement_statement": row.get("reason", ""),
                "challenge": f"Review whether {row.get('acid', '')} remains the intended expression.",
                "cleaner_expression": "",
                "falsification_framing": "",
                "next_review_checkpoint": "",
                "evidence_pointers": row.get("evidence", []),
            }
        )
    return items


def _build_evidence_index(material_rows: list[dict[str, str]], trigger_candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    entries: list[dict[str, str]] = []
    for row in material_rows:
        item = (DEFAULT_ALIGNMENT_CSV.as_posix(), row.get("row_id", ""))
        if item[1] and item not in seen:
            seen.add(item)
            entries.append({"artifact_path": item[0], "row_id": item[1]})
    for row in trigger_candidates:
        for pointer in row.get("evidence", []):
            item = (pointer.get("artifact_path", ""), pointer.get("row_id", ""))
            if item[0] and item[1] and item not in seen:
                seen.add(item)
                entries.append({"artifact_path": item[0], "row_id": item[1]})
    return entries


def _collect_evidence(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    collected: list[dict[str, str]] = []
    for row in rows:
        for pointer in row.get("evidence_pointers", []):
            item = (pointer.get("artifact_path", ""), pointer.get("row_id", ""))
            if item[0] and item[1] and item not in seen:
                seen.add(item)
                collected.append({"artifact_path": item[0], "row_id": item[1]})
    return collected


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_summary_markdown(payload: dict[str, Any]) -> str:
    header = payload["review_run_metadata"]
    trigger_summary = payload["fund_snapshot_summary"]["trigger_summary"]
    challenge_brief = payload["challenge_brief"]
    lines = [
        f"# Monthly Review Run - {header['fund']}",
        "",
        f"- Snapshot date: {header['snapshot_date']}",
        f"- Prior snapshot date: {header['prior_snapshot_date'] or 'N/A'}",
        f"- As-of date: {header['as_of_date']}",
        f"- Review run id: {header['review_run_id']}",
        f"- Run mode: {header['run_mode']}",
        "",
        "## Trigger Summary",
        "",
        f"- Fired: {trigger_summary['fired_count']}",
        f"- Borderline: {trigger_summary.get('borderline_count', 0)}",
        f"- Suppressed: {trigger_summary['suppressed_count']}",
        f"- Not triggered: {trigger_summary['not_triggered_count']}",
        f"- Not evaluable: {trigger_summary['not_evaluable_count']}",
        "",
        "## Output Files",
        "",
        "- `change_brief_draft.json`",
        "- `sizing_considerations_draft.json`",
    ]
    if challenge_brief is not None:
        lines.append("- `challenge_brief_draft.json`")
    return "\n".join(lines).rstrip() + "\n"


def _review_run_id(*, fund: str, snapshot_date: str, as_of_date: str) -> str:
    digest = hashlib.sha256(f"{fund}|{snapshot_date}|{as_of_date}".encode("utf-8")).hexdigest()[:12]
    return f"rrun_{digest}"


def _prior_snapshot_date(*, fund: str, snapshot_date: str) -> str:
    dates = []
    with Path(DEFAULT_ALIGNMENT_CSV).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("fund") == fund and row.get("snapshot_date"):
                dates.append(row["snapshot_date"])
    ordered = sorted(set(dates))
    if snapshot_date not in ordered:
        return ""
    index = ordered.index(snapshot_date)
    return ordered[index - 1] if index > 0 else ""


def _source_hashes() -> dict[str, str]:
    paths = [
        Path("artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv"),
        Path("artifacts/rolled_exposures/fund_rollthrough_definitions.csv"),
        Path("artifacts/rolled_exposures/fund_rollthrough_coverage.csv"),
        Path("artifacts/agent_memory/memory_records.json"),
        Path("artifacts/equity_vir_history.csv"),
        Path(DEFAULT_GOVERNANCE_PATH),
    ]
    resolved_paths = [resolve_existing_csv_source(path) or path for path in paths]
    return {path.as_posix(): file_sha256(path) for path in resolved_paths if path.exists()}


def _dedupe_acid_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row.get("acid_type", ""), row.get("acid", "")), []).append(row)
    selected = []
    for group_rows in grouped.values():
        local_real = next((row for row in group_rows if row.get("algo_perspective") == "local_real"), None)
        selected.append(local_real or group_rows[0])
    return selected


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "fund"


def _to_float(raw_value: Any) -> float | None:
    if raw_value in (None, ""):
        return None
    return float(raw_value)


__all__ = ["run_monthly_review", "run_monthly_review_batch"]
