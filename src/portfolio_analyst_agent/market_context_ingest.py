"""Ingest approved source notes into citable monthly market-context rows."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .evidence import file_sha256
from .row_ids import generic_row_id


MARKET_CONTEXT_COLUMNS = (
    "row_id",
    "snapshot_date",
    "as_of_date",
    "scope_type",
    "scope_value",
    "priority",
    "headline",
    "narrative",
    "fundamental_readthrough",
    "pm_question",
    "source_label",
    "source_date",
    "region",
    "country",
    "sector",
    "asset_class",
    "source_url",
    "source_path",
    "source_file_hash",
    "notes",
)


SUPPORTED_SOURCE_SUFFIXES = {".md", ".markdown", ".txt", ".text"}


@dataclass(frozen=True)
class IngestDefaults:
    snapshot_date: str
    as_of_date: str
    source_label: str = "Approved market context note"
    source_date: str = ""
    scope_type: str = "global"
    scope_value: str = ""
    priority: str = "3"


def ingest_market_context_documents(
    *,
    input_dir: str | Path,
    output_csv: str | Path,
    defaults: IngestDefaults,
    append: bool = False,
) -> dict[str, Any]:
    """Convert approved Markdown/text context notes into market-context CSV rows."""

    _require_iso_date(defaults.snapshot_date, "snapshot_date")
    _require_iso_date(defaults.as_of_date, "as_of_date")
    if defaults.source_date:
        _require_iso_date(defaults.source_date, "source_date")
    if date.fromisoformat(defaults.snapshot_date) > date.fromisoformat(defaults.as_of_date):
        raise ValueError("snapshot_date may not be after as_of_date.")

    source_dir = Path(input_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"Market context source folder not found: {source_dir}")
    rows = list(_rows_from_documents(source_dir, defaults=defaults))

    output_path = Path(output_csv)
    if append and output_path.exists():
        existing_rows = _read_existing_rows(output_path)
        rows = _dedupe_rows(existing_rows + rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MARKET_CONTEXT_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "input_dir": source_dir.as_posix(),
        "output_csv": output_path.as_posix(),
        "row_count": len(rows),
        "append": append,
    }


def _rows_from_documents(input_dir: Path, *, defaults: IngestDefaults) -> Iterable[dict[str, str]]:
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SOURCE_SUFFIXES:
            continue
        metadata, body = _parse_front_matter(path.read_text(encoding="utf-8-sig"))
        row = _row_from_document(path, metadata=metadata, body=body, defaults=defaults)
        if row["narrative"]:
            yield row


def _row_from_document(
    path: Path,
    *,
    metadata: dict[str, str],
    body: str,
    defaults: IngestDefaults,
) -> dict[str, str]:
    snapshot_date = metadata.get("snapshot_date", defaults.snapshot_date)
    as_of_date = metadata.get("as_of_date", defaults.as_of_date)
    source_date = metadata.get("source_date", defaults.source_date or as_of_date)
    _require_iso_date(snapshot_date, "snapshot_date")
    _require_iso_date(as_of_date, "as_of_date")
    _require_iso_date(source_date, "source_date")
    if date.fromisoformat(snapshot_date) > date.fromisoformat(as_of_date):
        raise ValueError(f"{path}: snapshot_date may not be after as_of_date.")
    if date.fromisoformat(source_date) > date.fromisoformat(as_of_date):
        raise ValueError(f"{path}: source_date may not be after as_of_date.")

    headline = metadata.get("headline") or _headline_from_body(body) or path.stem.replace("_", " ").replace("-", " ")
    narrative = metadata.get("narrative") or _compact_body(body)
    row = {
        "snapshot_date": snapshot_date,
        "as_of_date": as_of_date,
        "scope_type": metadata.get("scope_type", defaults.scope_type),
        "scope_value": metadata.get("scope_value", defaults.scope_value),
        "priority": metadata.get("priority", defaults.priority),
        "headline": headline,
        "narrative": narrative,
        "fundamental_readthrough": metadata.get("fundamental_readthrough", ""),
        "pm_question": metadata.get("pm_question", ""),
        "source_label": metadata.get("source_label", defaults.source_label),
        "source_date": source_date,
        "region": metadata.get("region", ""),
        "country": metadata.get("country", ""),
        "sector": metadata.get("sector", ""),
        "asset_class": metadata.get("asset_class", ""),
        "source_url": metadata.get("source_url", ""),
        "source_path": path.as_posix(),
        "source_file_hash": file_sha256(path),
        "notes": metadata.get("notes", ""),
    }
    row["row_id"] = metadata.get("row_id", "") or generic_row_id(row, namespace="market_context", prefix="mctx")
    return {column: row.get(column, "") for column in MARKET_CONTEXT_COLUMNS}


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()
    metadata: dict[str, str] = {}
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    if end_index is None:
        return {}, text.strip()
    return metadata, "\n".join(lines[end_index + 1 :]).strip()


def _headline_from_body(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        if stripped:
            return stripped[:100]
    return ""


def _compact_body(body: str) -> str:
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return " ".join(lines).strip()


def _read_existing_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        row_id = row.get("row_id", "")
        if row_id:
            deduped[row_id] = row
    return list(deduped.values())


def _require_iso_date(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")
    date.fromisoformat(value)


__all__ = ["IngestDefaults", "MARKET_CONTEXT_COLUMNS", "ingest_market_context_documents"]
