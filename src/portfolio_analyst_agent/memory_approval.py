"""Manual approval helpers for proposed memory records."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .memory_store import DEFAULT_MEMORY_PATH, DEFAULT_MEMORY_SCOPES


MEMORY_ID_FIELDS = {
    "thesis_ledger": "thesis_id",
    "open_challenges": "challenge_id",
    "exceptions": "exception_id",
    "watch_items": "watch_item_id",
}


def approve_memory_record(
    *,
    table: str,
    record_id: str,
    approved_by: str,
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
    note: str = "",
) -> dict[str, Any]:
    """Append an approved copy of the latest proposed memory record."""

    if table not in MEMORY_ID_FIELDS:
        raise ValueError(f"Unsupported memory table: {table}")
    if not record_id:
        raise ValueError("record_id is required.")
    if not approved_by:
        raise ValueError("approved_by is required.")

    path = Path(memory_path)
    payload = _load_payload(path)
    rows = payload["tables"][table]
    source = _latest_row(rows, MEMORY_ID_FIELDS[table], record_id)
    if source is None:
        raise ValueError(f"No memory record found for {table}/{record_id}.")
    if source.get("review_state") != "proposed":
        raise ValueError(f"Latest memory record for {table}/{record_id} is not proposed.")

    timestamp = _utc_now()
    approved = deepcopy(source)
    approved.update(
        {
            "review_state": "approved",
            "approved_at": timestamp,
            "approved_by": approved_by,
            "approval_note": note,
            "updated_at": timestamp,
        }
    )
    rows.append(approved)
    _atomic_write(path, payload)
    return {
        "table": table,
        "record_id": record_id,
        "review_state": "approved",
        "approved_by": approved_by,
        "memory_path": path.as_posix(),
    }


def list_proposed_memory(
    *,
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
    table: str | None = None,
) -> list[dict[str, Any]]:
    """Return latest proposed memory records for review."""

    path = Path(memory_path)
    payload = _load_payload(path)
    tables = [table] if table else list(DEFAULT_MEMORY_SCOPES)
    unknown = sorted(set(tables) - set(DEFAULT_MEMORY_SCOPES))
    if unknown:
        raise ValueError(f"Unsupported memory table: {', '.join(unknown)}")

    proposed: list[dict[str, Any]] = []
    for table_name in tables:
        id_field = MEMORY_ID_FIELDS[table_name]
        latest: dict[str, dict[str, Any]] = {}
        for row in payload["tables"][table_name]:
            record_id = str(row.get(id_field, "")).strip()
            if not record_id:
                continue
            current = latest.get(record_id)
            if current is None or _row_sort_key(row) >= _row_sort_key(current):
                latest[record_id] = row
        for record_id, row in latest.items():
            if row.get("review_state") == "proposed":
                proposed.append(
                    {
                        "table": table_name,
                        "record_id": record_id,
                        "fund": row.get("fund", ""),
                        "acid": row.get("acid", ""),
                        "status": row.get("status", ""),
                        "source_op_type": row.get("source_op_type", ""),
                        "created_at": row.get("created_at", ""),
                        "updated_at": row.get("updated_at", ""),
                    }
                )
    return sorted(proposed, key=lambda row: (row["table"], row.get("fund", ""), row.get("acid", ""), row["record_id"]))


def _latest_row(rows: list[dict[str, Any]], id_field: str, record_id: str) -> dict[str, Any] | None:
    latest = None
    for row in rows:
        if row.get(id_field) != record_id:
            continue
        if latest is None or _row_sort_key(row) >= _row_sort_key(latest):
            latest = row
    return latest


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("updated_at", "")), str(row.get("created_at", "")))


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


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = ["approve_memory_record", "list_proposed_memory"]
