"""JSON-backed v1 memory store for the Model 1 agent harness."""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from .evidence import file_sha256


DEFAULT_MEMORY_PATH = Path("artifacts/agent_memory/memory_records.json")
DEFAULT_MEMORY_SCOPES = (
    "thesis_ledger",
    "open_challenges",
    "exceptions",
    "watch_items",
)
ACTIVE_REVIEW_STATES = {"proposed", "approved", "applied"}
AUTHORITATIVE_REVIEW_STATES = {"approved", "applied"}
ACTIVE_THESIS_STATUSES = {"active", "weakening", "contradicted"}
ACTIVE_CHALLENGE_STATUSES = {"open"}
ACTIVE_WATCH_STATUSES = {"open"}


def recall_memory_store(
    *,
    fund: str,
    snapshot_date: date,
    as_of_date: date,
    scope: Sequence[str] | None = None,
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
    include_proposed: bool = False,
) -> dict[str, Any]:
    requested_scope = _normalize_scope(scope)
    path = Path(memory_path)
    payload = _load_memory_payload(path)
    tables = payload.get("tables", {})
    authoritative_states = ACTIVE_REVIEW_STATES if include_proposed else AUTHORITATIVE_REVIEW_STATES
    authority_rule = "approved_applied_proposed_shadow" if include_proposed else "approved_applied_only"

    thesis_rows = _select_thesis_rows(
        tables.get("thesis_ledger", []),
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        review_states=authoritative_states,
    ) if "thesis_ledger" in requested_scope else []
    challenge_rows = _select_challenge_rows(
        tables.get("open_challenges", []),
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        review_states=authoritative_states,
    ) if "open_challenges" in requested_scope else []
    exception_rows = _select_exception_rows(
        tables.get("exceptions", []),
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        review_states=authoritative_states,
    ) if "exceptions" in requested_scope else []
    watch_rows = _select_watch_rows(
        tables.get("watch_items", []),
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        review_states=authoritative_states,
    ) if "watch_items" in requested_scope else []

    summary_rows = _summary_rows(
        tables=tables,
        requested_scope=requested_scope,
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
    )
    all_rows = thesis_rows + challenge_rows + exception_rows + watch_rows
    return {
        "fund": fund,
        "snapshot_date": snapshot_date.isoformat(),
        "as_of_date": as_of_date.isoformat(),
        "scope_requested": list(requested_scope),
        "summary": {
            "thesis_ledger_count": len(thesis_rows),
            "open_challenges_count": len(challenge_rows),
            "exceptions_count": len(exception_rows),
            "watch_items_count": len(watch_rows),
            "approved_count": _count_review_state(summary_rows, "approved"),
            "applied_count": _count_review_state(summary_rows, "applied"),
            "proposed_count": _count_review_state(summary_rows, "proposed"),
            "authority_rule": authority_rule,
            "include_proposed_shadow": include_proposed,
        },
        "thesis_ledger": thesis_rows,
        "open_challenges": challenge_rows,
        "exceptions": exception_rows,
        "watch_items": watch_rows,
        "run_metadata": {
            "memory_path": path.as_posix(),
            "schema_version": payload.get("schema_version", ""),
            "source_file_hashes": {path.as_posix(): file_sha256(path)} if path.exists() else {},
            "tool_version": "recall_memory_v1",
        },
    }


def _load_memory_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "agent_memory_v1",
            "tables": {scope: [] for scope in DEFAULT_MEMORY_SCOPES},
        }
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    tables = payload.setdefault("tables", {})
    for scope in DEFAULT_MEMORY_SCOPES:
        rows = tables.get(scope, [])
        if not isinstance(rows, list):
            raise ValueError(f"Memory scope must be a list: {scope}")
        tables[scope] = _latest_rows(scope, rows)
    return payload


def _latest_rows(scope: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse append-only memory rows to latest record per logical ID."""

    key_field = {
        "thesis_ledger": "thesis_id",
        "open_challenges": "challenge_id",
        "exceptions": "exception_id",
        "watch_items": "watch_item_id",
    }[scope]
    latest: dict[str, dict[str, Any]] = {}
    unkeyed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        key = str(row.get(key_field, "")).strip()
        if not key:
            unkeyed.append(row)
            continue
        current = latest.get(key)
        if current is None or _row_sort_key(row, index) >= _row_sort_key(current, -1):
            latest[key] = row
    return unkeyed + list(latest.values())


def _row_sort_key(row: dict[str, Any], index: int) -> tuple[str, str, int]:
    return (
        str(row.get("updated_at", "")),
        str(row.get("created_at", "")),
        index,
    )


def _normalize_scope(scope: Sequence[str] | None) -> tuple[str, ...]:
    if scope is None:
        return DEFAULT_MEMORY_SCOPES
    unknown = sorted(set(scope) - set(DEFAULT_MEMORY_SCOPES))
    if unknown:
        raise ValueError(f"Unsupported memory scope: {', '.join(unknown)}")
    return tuple(scope)


def _summary_rows(
    *,
    tables: dict[str, list[dict[str, Any]]],
    requested_scope: tuple[str, ...],
    fund: str,
    snapshot_date: date,
    as_of_date: date,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if "thesis_ledger" in requested_scope:
        rows.extend(
            _select_thesis_rows(
                tables.get("thesis_ledger", []),
                fund=fund,
                snapshot_date=snapshot_date,
                as_of_date=as_of_date,
                review_states=ACTIVE_REVIEW_STATES,
            )
        )
    if "open_challenges" in requested_scope:
        rows.extend(
            _select_challenge_rows(
                tables.get("open_challenges", []),
                fund=fund,
                snapshot_date=snapshot_date,
                as_of_date=as_of_date,
                review_states=ACTIVE_REVIEW_STATES,
            )
        )
    if "exceptions" in requested_scope:
        rows.extend(
            _select_exception_rows(
                tables.get("exceptions", []),
                fund=fund,
                snapshot_date=snapshot_date,
                as_of_date=as_of_date,
                review_states=ACTIVE_REVIEW_STATES,
            )
        )
    if "watch_items" in requested_scope:
        rows.extend(
            _select_watch_rows(
                tables.get("watch_items", []),
                fund=fund,
                snapshot_date=snapshot_date,
                as_of_date=as_of_date,
                review_states=ACTIVE_REVIEW_STATES,
            )
        )
    return rows


def _select_thesis_rows(
    rows: list[dict[str, Any]],
    *,
    fund: str,
    snapshot_date: date,
    as_of_date: date,
    review_states: set[str],
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if row.get("fund") != fund:
            continue
        if row.get("review_state") not in review_states:
            continue
        if row.get("status") not in ACTIVE_THESIS_STATUSES:
            continue
        if not _is_record_available(row, as_of_date):
            continue
        if _optional_date(row.get("last_affirmed_snapshot_date")) not in (None,) and _optional_date(
            row.get("last_affirmed_snapshot_date")
        ) > snapshot_date:
            continue
        selected.append(row)
    return _sorted(selected)


def _select_challenge_rows(
    rows: list[dict[str, Any]],
    *,
    fund: str,
    snapshot_date: date,
    as_of_date: date,
    review_states: set[str],
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if row.get("fund") != fund:
            continue
        if row.get("review_state") not in review_states:
            continue
        if row.get("status") not in ACTIVE_CHALLENGE_STATUSES:
            continue
        if not _is_record_available(row, as_of_date):
            continue
        if _optional_date(row.get("opened_at_snapshot_date")) not in (None,) and _optional_date(
            row.get("opened_at_snapshot_date")
        ) > snapshot_date:
            continue
        selected.append(row)
    return _sorted(selected)


def _select_exception_rows(
    rows: list[dict[str, Any]],
    *,
    fund: str,
    snapshot_date: date,
    as_of_date: date,
    review_states: set[str],
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if row.get("fund") != fund:
            continue
        if row.get("review_state") not in review_states:
            continue
        if not _is_record_available(row, as_of_date):
            continue
        effective_from = _optional_date(row.get("effective_from"))
        effective_to = _optional_date(row.get("effective_to"))
        if effective_from is not None and effective_from > snapshot_date:
            continue
        if effective_to is not None and effective_to < snapshot_date:
            continue
        selected.append(row)
    return _sorted(selected)


def _select_watch_rows(
    rows: list[dict[str, Any]],
    *,
    fund: str,
    snapshot_date: date,
    as_of_date: date,
    review_states: set[str],
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if row.get("fund") != fund:
            continue
        if row.get("review_state") not in review_states:
            continue
        if row.get("status") not in ACTIVE_WATCH_STATUSES:
            continue
        if not _is_record_available(row, as_of_date):
            continue
        if _optional_date(row.get("last_seen_snapshot_date")) not in (None,) and _optional_date(
            row.get("last_seen_snapshot_date")
        ) > snapshot_date:
            continue
        selected.append(row)
    return _sorted(selected)


def _is_record_available(row: dict[str, Any], as_of_date: date) -> bool:
    business_available_date = _business_available_date(row)
    if business_available_date is not None:
        return business_available_date <= as_of_date
    created_at = _optional_datetime(row.get("created_at"))
    if created_at is None:
        return True
    return created_at.date() <= as_of_date


def _business_available_date(row: dict[str, Any]) -> date | None:
    for field_name in (
        "record_available_date",
        "last_affirmed_snapshot_date",
        "opened_at_snapshot_date",
        "last_seen_snapshot_date",
        "effective_from",
    ):
        value = _optional_date(row.get(field_name))
        if value is not None:
            return value
    return None


def _count_review_state(rows: Iterable[dict[str, Any]], review_state: str) -> int:
    return sum(1 for row in rows if row.get("review_state") == review_state)


def _sorted(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("fund", "")),
            str(row.get("acid", "")),
            str(row.get("exception_id", row.get("challenge_id", row.get("thesis_id", row.get("watch_item_id", ""))))),
        ),
    )


def _optional_date(raw_value: Any) -> date | None:
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, date):
        return raw_value
    return date.fromisoformat(str(raw_value))


def _optional_datetime(raw_value: Any) -> datetime | None:
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, datetime):
        return raw_value
    normalized = str(raw_value).replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


__all__ = [
    "DEFAULT_MEMORY_PATH",
    "DEFAULT_MEMORY_SCOPES",
    "recall_memory_store",
]
