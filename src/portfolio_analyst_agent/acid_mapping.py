"""ACID mapping loader used by agent read tools."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
from typing import Any, Iterable

from .evidence import stable_row_id


DEFAULT_ACID_MAPPING_CSV = Path("data/acid_mapping_bootstrap_v1.csv")
MAPPING_FIELDS = (
    "asset_class_name",
    "model_family",
    "family",
    "comparison_group",
    "relative_value_group",
    "interpretation_type",
    "investable_flag",
    "subtype",
    "market_scope",
    "region",
    "country",
    "sector",
    "style",
    "currency_exposure_type",
    "maturity_bucket",
    "curve_aware",
    "parent_family",
    "index_provider",
    "benchmark_role",
    "notes",
)


@dataclass(frozen=True)
class AcidMappingRow:
    row_id: str
    acid: str
    fields: dict[str, str]

    def to_dict(self, *, prefix: str = "") -> dict[str, Any]:
        values: dict[str, Any] = {f"{prefix}acid": self.acid} if prefix else {"acid": self.acid}
        for field in MAPPING_FIELDS:
            key = f"{prefix}{field}" if prefix else field
            value = self.fields.get(field, "")
            if field in {"investable_flag", "curve_aware"}:
                values[key] = _to_bool(value)
            else:
                values[key] = value
        values[f"{prefix}row_id" if prefix else "row_id"] = self.row_id
        return values


class MappingIndex:
    def __init__(self, rows: Iterable[AcidMappingRow], *, source_path: Path):
        self.source_path = source_path
        self._by_acid = {row.acid: row for row in rows}

    def get(self, acid: str) -> AcidMappingRow | None:
        return self._by_acid.get(acid)

    def peers_for(self, row: AcidMappingRow) -> list[AcidMappingRow]:
        comparison_group = row.fields.get("comparison_group", "")
        relative_value_group = row.fields.get("relative_value_group", "")
        parent_family = row.fields.get("parent_family", "")
        peers = []
        for candidate in self._by_acid.values():
            if candidate.acid == row.acid:
                continue
            if comparison_group and candidate.fields.get("comparison_group") == comparison_group:
                peers.append(candidate)
                continue
            if relative_value_group and candidate.fields.get("relative_value_group") == relative_value_group:
                peers.append(candidate)
                continue
            if parent_family and candidate.fields.get("parent_family") == parent_family:
                peers.append(candidate)
        return sorted({peer.acid: peer for peer in peers}.values(), key=lambda item: item.acid)

    def enrich_row(self, row: dict[str, str]) -> dict[str, Any]:
        mapping = self.get(row.get("acid", ""))
        if mapping is None:
            return {
                **row,
                "mapping_status": "missing_in_mapping",
                **{f"mapping_{field}": "" for field in MAPPING_FIELDS},
                "mapping_row_id": "",
            }
        return {
            **row,
            "mapping_status": "matched_to_mapping",
            **mapping.to_dict(prefix="mapping_"),
            "mapping_citation_ref": f"csv:{self.source_path.as_posix()}#row_id={mapping.row_id}",
        }


def load_mapping(
    as_of_date: object | None = None,
    mapping_csv: str | Path = DEFAULT_ACID_MAPPING_CSV,
) -> MappingIndex:
    """Load the current ACID mapping.

    `as_of_date` is accepted now so the read-tool API is ready for effective-dated
    mappings later. The current bootstrap file is a point-in-time CSV.
    """

    path = Path(mapping_csv)
    rows: list[AcidMappingRow] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            acid = raw.get("acid", "").strip()
            if not acid:
                continue
            fields = {field: raw.get(field, "").strip() for field in MAPPING_FIELDS}
            rows.append(
                AcidMappingRow(
                    row_id=raw.get("row_id", "") or stable_row_id(raw, namespace=path.as_posix()),
                    acid=acid,
                    fields=fields,
                )
            )
    return MappingIndex(rows, source_path=path)


def _to_bool(raw_value: object) -> bool | None:
    if raw_value in (None, ""):
        return None
    return str(raw_value).strip().lower() in {"true", "1", "yes", "y"}


__all__ = ["AcidMappingRow", "DEFAULT_ACID_MAPPING_CSV", "MAPPING_FIELDS", "MappingIndex", "load_mapping"]
