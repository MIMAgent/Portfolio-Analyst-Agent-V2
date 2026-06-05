"""Proposed-only memory write operations for the Model 1 agent harness."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .governance import DEFAULT_GOVERNANCE_PATH, load_governance
from .memory_store import DEFAULT_MEMORY_PATH, DEFAULT_MEMORY_SCOPES


THESIS_OPS = {
    "affirm_thesis",
    "create_thesis",
    "update_thesis",
    "mark_thesis_weakening",
    "mark_thesis_contradicted",
    "supersede_thesis",
}
CHALLENGE_OPS = {
    "open_challenge",
    "update_challenge",
    "close_challenge",
    "escalate_challenge_to_ic",
    "dismiss_challenge",
}
WATCH_OPS = {"create_watch_item", "close_watch_item"}
EXCEPTION_OPS = {"log_exception", "expire_exception"}
SUPPORTED_MEMORY_OPS = THESIS_OPS | CHALLENGE_OPS | WATCH_OPS | EXCEPTION_OPS


def apply_ops(
    *,
    fund: str,
    ops: list[dict[str, Any]],
    run_metadata: dict[str, Any],
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
    governance_path: str | Path = DEFAULT_GOVERNANCE_PATH,
) -> list[dict[str, Any]]:
    """Validate and append proposed memory rows.

    Model 1 never auto-applies memory writes. Every accepted operation is stamped
    `review_state = "proposed"` and appended to the JSON memory store.
    """

    if not ops:
        return []

    snapshot_date = _require_date(run_metadata.get("snapshot_date"), "snapshot_date")
    as_of_date = _require_date(run_metadata.get("as_of_date"), "as_of_date")
    if snapshot_date > as_of_date:
        raise ValueError("snapshot_date may not be after as_of_date.")

    governance = load_governance(as_of_date=as_of_date, governance_path=governance_path)
    if governance.bool_param("auto_apply_memory_ops"):
        raise ValueError("Model 1 memory writes require auto_apply_memory_ops=false.")

    path = Path(memory_path)
    payload = _load_payload(path)
    tables = payload["tables"]
    latest = _latest_indexes(tables)
    timestamp = _utc_now()
    review_run_id = _required_text(run_metadata, "review_run_id")

    _reject_conflicting_ops(ops)

    appended: list[tuple[str, dict[str, Any], str]] = []
    applied: list[dict[str, Any]] = []
    for op in ops:
        op_type = _required_text(op, "op_type")
        if op_type not in SUPPORTED_MEMORY_OPS:
            raise ValueError(f"Unsupported memory op_type: {op_type}")

        table_name, row = _row_for_op(
            fund=fund,
            op=op,
            op_type=op_type,
            latest=latest,
            snapshot_date=snapshot_date,
            timestamp=timestamp,
            review_run_id=review_run_id,
        )
        tables[table_name].append(row)
        latest = _latest_indexes(tables)
        record_id = _record_id(table_name, row)
        appended.append((table_name, row, record_id))
        applied.append(
            {
                "op_type": op_type,
                "table": table_name,
                "record_id": record_id,
                "review_state": row["review_state"],
                "status": row.get("status", ""),
            }
        )

    _atomic_write(path, payload)
    return applied


def _row_for_op(
    *,
    fund: str,
    op: dict[str, Any],
    op_type: str,
    latest: dict[str, dict[str, dict[str, Any]]],
    snapshot_date: date,
    timestamp: str,
    review_run_id: str,
) -> tuple[str, dict[str, Any]]:
    if op_type == "create_thesis":
        acid = _required_text(op, "acid")
        _ensure_no_active_thesis(latest, fund=fund, acid=acid)
        row = _base_row(op, timestamp=timestamp, review_run_id=review_run_id)
        row.update(
            {
                "thesis_id": _memory_id("ths", fund, acid, review_run_id, timestamp),
                "fund": fund,
                "acid": acid,
                "thesis_text": _required_text(op, "thesis_text"),
                "thesis_drivers": _required_list(op, "thesis_drivers"),
                "last_affirmed_snapshot_date": snapshot_date.isoformat(),
                "last_affirmed_stf": op.get("last_affirmed_stf", ""),
                "last_affirmed_decomp": op.get("last_affirmed_decomp", ""),
                "falsification_conditions": _required_text(op, "falsification_conditions"),
                "status": "active",
                "visibility_scope": op.get("visibility_scope", "personal"),
                "evidence_pointers": _required_list(op, "evidence_pointers"),
            }
        )
        return "thesis_ledger", row

    if op_type in {"affirm_thesis", "update_thesis", "mark_thesis_weakening", "mark_thesis_contradicted", "supersede_thesis"}:
        existing = _find_thesis(latest, fund=fund, acid=_required_text(op, "acid"))
        row = _replacement(existing, timestamp=timestamp, review_run_id=review_run_id)
        if op_type == "affirm_thesis":
            row["last_affirmed_snapshot_date"] = snapshot_date.isoformat()
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "update_thesis":
            row["thesis_text"] = _required_text(op, "thesis_text")
            row["thesis_drivers"] = _required_list(op, "thesis_drivers")
            row["falsification_conditions"] = _required_text(op, "falsification_conditions")
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "mark_thesis_weakening":
            row["status"] = "weakening"
            row["status_reason"] = _required_text(op, "reason")
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "mark_thesis_contradicted":
            row["status"] = "contradicted"
            row["status_reason"] = _required_text(op, "reason")
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "supersede_thesis":
            row["status"] = "superseded"
            row["status_reason"] = _required_text(op, "reason")
        return "thesis_ledger", row

    if op_type == "open_challenge":
        row = _base_row(op, timestamp=timestamp, review_run_id=review_run_id)
        row.update(
            {
                "challenge_id": _memory_id("chg", fund, _required_text(op, "trigger_candidate_id"), review_run_id, timestamp),
                "trigger_candidate_id": _required_text(op, "trigger_candidate_id"),
                "fund": fund,
                "acid": _required_text(op, "acid"),
                "trigger_type": _required_text(op, "trigger_type"),
                "trigger_evidence": op.get("trigger_evidence", []),
                "challenge_text": _required_text(op, "challenge_text"),
                "status": "open",
                "opened_at_snapshot_date": snapshot_date.isoformat(),
                "last_seen_snapshot_date": snapshot_date.isoformat(),
                "resolved_at_snapshot_date": "",
                "resolution_text": "",
                "dismissal_reason": "",
                "evidence_pointers": _required_list(op, "evidence_pointers"),
            }
        )
        return "open_challenges", row

    if op_type in {"update_challenge", "close_challenge", "escalate_challenge_to_ic"}:
        existing = _required_existing(latest["open_challenges"], _required_text(op, "challenge_id"), "challenge_id")
        row = _replacement(existing, timestamp=timestamp, review_run_id=review_run_id)
        if op_type == "update_challenge":
            row["trigger_candidate_id"] = _required_text(op, "trigger_candidate_id")
            row["challenge_text"] = _required_text(op, "challenge_text")
            row["last_seen_snapshot_date"] = snapshot_date.isoformat()
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "close_challenge":
            row["status"] = "resolved"
            row["resolved_at_snapshot_date"] = snapshot_date.isoformat()
            row["resolution_text"] = _required_text(op, "resolution_text")
            row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        elif op_type == "escalate_challenge_to_ic":
            row["status"] = "escalated_to_ic"
            row["resolution_text"] = _required_text(op, "reason")
        return "open_challenges", row

    if op_type == "dismiss_challenge":
        row = _base_row(op, timestamp=timestamp, review_run_id=review_run_id)
        row.update(
            {
                "challenge_id": _memory_id("chg", fund, _required_text(op, "trigger_candidate_id"), "dismissed", review_run_id),
                "trigger_candidate_id": _required_text(op, "trigger_candidate_id"),
                "fund": fund,
                "acid": op.get("acid", ""),
                "trigger_type": op.get("trigger_type", ""),
                "trigger_evidence": op.get("trigger_evidence", []),
                "challenge_text": "",
                "status": "dismissed_with_reason",
                "opened_at_snapshot_date": snapshot_date.isoformat(),
                "last_seen_snapshot_date": snapshot_date.isoformat(),
                "resolved_at_snapshot_date": snapshot_date.isoformat(),
                "resolution_text": "",
                "dismissal_reason": _required_text(op, "reason"),
                "evidence_pointers": _required_list(op, "evidence_pointers"),
            }
        )
        return "open_challenges", row

    if op_type == "create_watch_item":
        row = _base_row(op, timestamp=timestamp, review_run_id=review_run_id)
        row.update(
            {
                "watch_item_id": _memory_id("wat", fund, _required_text(op, "acid"), review_run_id, timestamp),
                "fund": fund,
                "acid": _required_text(op, "acid"),
                "watch_text": _required_text(op, "watch_text"),
                "reason": op.get("reason", ""),
                "review_checkpoint": _required_text(op, "review_checkpoint"),
                "status": "open",
                "last_seen_snapshot_date": snapshot_date.isoformat(),
                "evidence_pointers": _required_list(op, "evidence_pointers"),
            }
        )
        return "watch_items", row

    if op_type == "close_watch_item":
        existing = _required_existing(latest["watch_items"], _required_text(op, "watch_item_id"), "watch_item_id")
        row = _replacement(existing, timestamp=timestamp, review_run_id=review_run_id)
        row["status"] = "closed"
        row["reason"] = _required_text(op, "reason")
        row["evidence_pointers"] = _required_list(op, "evidence_pointers")
        return "watch_items", row

    if op_type == "log_exception":
        acid_or_pattern = _required_text(op, "acid_or_pattern")
        scope = "acid_pattern" if any(char in acid_or_pattern for char in "*?") else "acid"
        row = _base_row(op, timestamp=timestamp, review_run_id=review_run_id)
        row.update(
            {
                "exception_id": _memory_id("exc", fund, acid_or_pattern, review_run_id, timestamp),
                "fund": fund,
                "scope": scope,
                "acid": acid_or_pattern if scope == "acid" else "",
                "acid_pattern": acid_or_pattern if scope == "acid_pattern" else "",
                "trigger_types": _required_list(op, "trigger_types"),
                "exception_text": _required_text(op, "exception_text"),
                "effective_from": _required_text(op, "effective_from"),
                "effective_to": "",
                "review_cadence": _required_text(op, "review_cadence"),
                "last_reviewed_snapshot_date": snapshot_date.isoformat(),
                "evidence_pointers": _required_list(op, "evidence_pointers"),
            }
        )
        return "exceptions", row

    if op_type == "expire_exception":
        existing = _required_existing(latest["exceptions"], _required_text(op, "exception_id"), "exception_id")
        row = _replacement(existing, timestamp=timestamp, review_run_id=review_run_id)
        row["effective_to"] = snapshot_date.isoformat()
        row["expiration_reason"] = _required_text(op, "reason")
        return "exceptions", row

    raise ValueError(f"Unsupported memory op_type: {op_type}")


def _base_row(op: dict[str, Any], *, timestamp: str, review_run_id: str) -> dict[str, Any]:
    return {
        "review_state": "proposed",
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_by_review_run_id": review_run_id,
        "last_updated_by_review_run_id": review_run_id,
        "source_op_type": op["op_type"],
    }


def _replacement(existing: dict[str, Any], *, timestamp: str, review_run_id: str) -> dict[str, Any]:
    row = deepcopy(existing)
    row["review_state"] = "proposed"
    row["updated_at"] = timestamp
    row["last_updated_by_review_run_id"] = review_run_id
    return row


def _load_payload(path: Path) -> dict[str, Any]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": "agent_memory_v1", "tables": {}}
    tables = payload.setdefault("tables", {})
    for scope in DEFAULT_MEMORY_SCOPES:
        rows = tables.get(scope, [])
        if not isinstance(rows, list):
            raise ValueError(f"Memory scope must be a list: {scope}")
        tables.setdefault(scope, rows)
    return payload


def _latest_indexes(tables: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "thesis_ledger": _latest_by_id(tables["thesis_ledger"], "thesis_id"),
        "open_challenges": _latest_by_id(tables["open_challenges"], "challenge_id"),
        "exceptions": _latest_by_id(tables["exceptions"], "exception_id"),
        "watch_items": _latest_by_id(tables["watch_items"], "watch_item_id"),
    }


def _latest_by_id(rows: list[dict[str, Any]], key_field: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get(key_field, "")).strip()
        if not key:
            continue
        latest[key] = row
    return latest


def _reject_conflicting_ops(ops: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, str]] = set()
    for op in ops:
        op_type = _required_text(op, "op_type")
        if op_type in THESIS_OPS:
            key = ("thesis", str(op.get("acid", "")))
        elif op_type in CHALLENGE_OPS:
            key = ("challenge", str(op.get("challenge_id") or op.get("trigger_candidate_id") or ""))
        elif op_type in WATCH_OPS:
            key = ("watch", str(op.get("watch_item_id") or op.get("acid") or ""))
        elif op_type in EXCEPTION_OPS:
            key = ("exception", str(op.get("exception_id") or op.get("acid_or_pattern") or ""))
        else:
            key = ("unknown", op_type)
        if key in seen:
            raise ValueError(f"Conflicting memory ops in one call for {key[0]} {key[1]!r}.")
        seen.add(key)


def _ensure_no_active_thesis(latest: dict[str, dict[str, dict[str, Any]]], *, fund: str, acid: str) -> None:
    for row in latest["thesis_ledger"].values():
        if row.get("fund") == fund and row.get("acid") == acid and row.get("status") in {"active", "weakening", "contradicted"}:
            if row.get("review_state") in {"proposed", "approved", "applied"}:
                raise ValueError(f"Active thesis already exists for {fund} / {acid}.")


def _find_thesis(latest: dict[str, dict[str, dict[str, Any]]], *, fund: str, acid: str) -> dict[str, Any]:
    for row in latest["thesis_ledger"].values():
        if row.get("fund") == fund and row.get("acid") == acid and row.get("status") in {"active", "weakening", "contradicted"}:
            return row
    raise ValueError(f"No active thesis found for {fund} / {acid}.")


def _required_existing(rows: dict[str, dict[str, Any]], record_id: str, field_name: str) -> dict[str, Any]:
    row = rows.get(record_id)
    if row is None:
        raise ValueError(f"No memory record found for {field_name}={record_id!r}.")
    return row


def _record_id(table_name: str, row: dict[str, Any]) -> str:
    field = {
        "thesis_ledger": "thesis_id",
        "open_challenges": "challenge_id",
        "exceptions": "exception_id",
        "watch_items": "watch_item_id",
    }[table_name]
    return str(row[field])


def _memory_id(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _required_text(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if value in (None, ""):
        raise ValueError(f"Missing required field: {field_name}")
    return str(value)


def _required_list(payload: dict[str, Any], field_name: str) -> list[Any]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Missing required non-empty list: {field_name}")
    return value


def _require_date(raw_value: Any, field_name: str) -> date:
    if raw_value in (None, ""):
        raise ValueError(f"Missing required field: {field_name}")
    if isinstance(raw_value, date):
        return raw_value
    return date.fromisoformat(str(raw_value))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


__all__ = ["SUPPORTED_MEMORY_OPS", "apply_ops"]
