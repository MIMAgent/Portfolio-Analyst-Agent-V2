"""Equity VIR history normalization and trend helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import csv
import json

from .parse_utils import safe_float
from .workbook_xml import XlsxWorkbook

PARSER_VERSION = "equity_history_v1"

HISTORY_HEADER_TO_CANONICAL = {
    "acid": "acid",
    "valdate": "snapshot_date",
    "lr10_combined": "local_real_vir",
    "usdn_uh10_combined": "local_nominal_vir",
    "usdn_h10": "usd_hedged_vir",
    "lruc": "unconditional_vir",
    "infl_rd": "inflation",
    "usd_rduh10": "currency_usd",
    "yield_rd10": "yield",
    "growth_rd": "growth",
    "valadj_rd10": "valuation_adjustment_top_down",
    "valadj_rd10_combined": "valuation_adjustment_combined",
    "pfv_agg": "price_to_fair_value",
}

REQUIRED_HISTORY_HEADERS = tuple(HISTORY_HEADER_TO_CANONICAL.keys())


@dataclass(frozen=True)
class EquityHistoryRecord:
    snapshot_date: date
    ingested_at: str
    parser_version: str
    workbook_type: str
    acid: str
    asset_class_name: str | None
    local_real_vir: float | None
    local_nominal_vir: float | None
    usd_hedged_vir: float | None
    unconditional_vir: float | None
    stf: float | None
    price_to_fair_value: float | None
    inflation: float | None
    currency_usd: float | None
    yield_: float | None
    growth: float | None
    valuation_adjustment_top_down: float | None
    valuation_adjustment_combined: float | None
    valuation_adjustment_bottom_up: float | None
    prior_stf: float | None
    delta_stf: float | None
    delta_local_real_vir: float | None
    delta_local_nominal_vir: float | None
    delta_usd_hedged_vir: float | None
    delta_unconditional_vir: float | None
    delta_price_to_fair_value: float | None
    prior_rank_in_category_by_stf: int | None
    rank_in_category_by_stf: int | None
    rank_change_by_stf: int | None
    raw_row: str
    raw_headers: str


@dataclass(frozen=True)
class EquityHistoryParseResult:
    workbook_path: Path
    row_count: int
    snapshot_dates: list[date]
    records: list[EquityHistoryRecord]

    def summary(self) -> dict[str, object]:
        return {
            "source_file": self.workbook_path.name,
            "row_count": self.row_count,
            "snapshot_count": len(self.snapshot_dates),
            "latest_snapshot_date": self.snapshot_dates[-1].isoformat() if self.snapshot_dates else None,
            "acid_count": len({record.acid for record in self.records}),
        }


def parse_equity_history_workbook(workbook_path: str | Path) -> EquityHistoryParseResult:
    workbook_path = Path(workbook_path)
    workbook = XlsxWorkbook(workbook_path)
    worksheet = workbook.worksheet("Sheet1")

    header_map = _header_map(worksheet)
    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    raw_headers = json.dumps(header_map, sort_keys=True)

    base_rows: list[dict[str, object]] = []
    for row_number in sorted(worksheet.rows):
        if row_number == 1:
            continue

        acid = worksheet.get_cell(row_number, header_map["acid"]).strip()
        if not acid:
            continue

        snapshot_raw = worksheet.get_cell(row_number, header_map["snapshot_date"]).strip()
        if not snapshot_raw:
            continue

        raw_row: dict[str, str] = {}
        for source_header, canonical_name in HISTORY_HEADER_TO_CANONICAL.items():
            column_number = header_map[canonical_name]
            raw_row[source_header] = worksheet.get_cell(row_number, column_number).strip()

        local_real_vir = _to_float(raw_row["lr10_combined"])
        unconditional_vir = _to_float(raw_row["lruc"])
        valuation_adjustment_top_down = _to_float(raw_row["valadj_rd10"])
        valuation_adjustment_combined = _to_float(raw_row["valadj_rd10_combined"])

        base_rows.append(
            {
                "snapshot_date": date.fromisoformat(snapshot_raw),
                "ingested_at": ingested_at,
                "parser_version": PARSER_VERSION,
                "workbook_type": "equity_model",
                "acid": acid,
                "asset_class_name": None,
                "local_real_vir": local_real_vir,
                "local_nominal_vir": _to_float(raw_row["usdn_uh10_combined"]),
                "usd_hedged_vir": _to_float(raw_row["usdn_h10"]),
                "unconditional_vir": unconditional_vir,
                "stf": _diff(local_real_vir, unconditional_vir),
                "price_to_fair_value": _to_float(raw_row["pfv_agg"]),
                "inflation": _to_float(raw_row["infl_rd"]),
                "currency_usd": _to_float(raw_row["usd_rduh10"]),
                "yield_": _to_float(raw_row["yield_rd10"]),
                "growth": _to_float(raw_row["growth_rd"]),
                "valuation_adjustment_top_down": valuation_adjustment_top_down,
                "valuation_adjustment_combined": valuation_adjustment_combined,
                "valuation_adjustment_bottom_up": _bottom_up_valuation(
                    valuation_adjustment_top_down,
                    valuation_adjustment_combined,
                ),
                "raw_row": json.dumps(raw_row, sort_keys=True),
                "raw_headers": raw_headers,
            }
        )

    records = _apply_trend_fields(base_rows)
    snapshot_dates = sorted({record.snapshot_date for record in records})
    return EquityHistoryParseResult(
        workbook_path=workbook_path,
        row_count=len(records),
        snapshot_dates=snapshot_dates,
        records=records,
    )


def write_equity_history_csv(records: list[EquityHistoryRecord], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "snapshot_date",
        "ingested_at",
        "parser_version",
        "workbook_type",
        "acid",
        "asset_class_name",
        "local_real_vir",
        "local_nominal_vir",
        "usd_hedged_vir",
        "unconditional_vir",
        "stf",
        "price_to_fair_value",
        "inflation",
        "currency_usd",
        "yield",
        "growth",
        "valuation_adjustment_top_down",
        "valuation_adjustment_combined",
        "valuation_adjustment_bottom_up",
        "prior_stf",
        "delta_stf",
        "delta_local_real_vir",
        "delta_local_nominal_vir",
        "delta_usd_hedged_vir",
        "delta_unconditional_vir",
        "delta_price_to_fair_value",
        "prior_rank_in_category_by_stf",
        "rank_in_category_by_stf",
        "rank_change_by_stf",
        "raw_row",
        "raw_headers",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["snapshot_date"] = row["snapshot_date"].isoformat()
            row["yield"] = row.pop("yield_")
            writer.writerow(row)

    return output_path


def _header_map(worksheet) -> dict[str, int]:
    observed_headers: dict[str, int] = {}
    for column_number, raw_header in worksheet.nonempty_cells(1):
        normalized = raw_header.strip().lower()
        if normalized in HISTORY_HEADER_TO_CANONICAL:
            observed_headers[HISTORY_HEADER_TO_CANONICAL[normalized]] = column_number

    missing = [
        header
        for header in REQUIRED_HISTORY_HEADERS
        if HISTORY_HEADER_TO_CANONICAL[header] not in observed_headers
    ]
    if missing:
        raise ValueError(f"Missing required history headers: {missing}")

    return observed_headers


def _apply_trend_fields(base_rows: list[dict[str, object]]) -> list[EquityHistoryRecord]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in base_rows:
        grouped.setdefault(str(row["acid"]), []).append(row)

    for acid_rows in grouped.values():
        acid_rows.sort(key=lambda row: row["snapshot_date"])
        previous: dict[str, object] | None = None
        for row in acid_rows:
            row["prior_stf"] = previous["stf"] if previous else None
            row["delta_stf"] = _delta(row["stf"], previous["stf"] if previous else None)
            row["delta_local_real_vir"] = _delta(row["local_real_vir"], previous["local_real_vir"] if previous else None)
            row["delta_local_nominal_vir"] = _delta(
                row["local_nominal_vir"],
                previous["local_nominal_vir"] if previous else None,
            )
            row["delta_usd_hedged_vir"] = _delta(row["usd_hedged_vir"], previous["usd_hedged_vir"] if previous else None)
            row["delta_unconditional_vir"] = _delta(
                row["unconditional_vir"],
                previous["unconditional_vir"] if previous else None,
            )
            row["delta_price_to_fair_value"] = _delta(
                row["price_to_fair_value"],
                previous["price_to_fair_value"] if previous else None,
            )
            previous = row

    by_snapshot: dict[date, list[dict[str, object]]] = {}
    for row in base_rows:
        by_snapshot.setdefault(row["snapshot_date"], []).append(row)

    rank_lookup: dict[tuple[date, str], int] = {}
    for snapshot_date, snapshot_rows in by_snapshot.items():
        ranked = sorted(
            [row for row in snapshot_rows if row["stf"] is not None],
            key=lambda row: row["stf"],
            reverse=True,
        )
        for rank, row in enumerate(ranked, start=1):
            rank_lookup[(snapshot_date, str(row["acid"]))] = rank

    records: list[EquityHistoryRecord] = []
    for acid_rows in grouped.values():
        previous_rank: int | None = None
        for row in acid_rows:
            current_rank = rank_lookup.get((row["snapshot_date"], str(row["acid"])))
            row["rank_in_category_by_stf"] = current_rank
            row["prior_rank_in_category_by_stf"] = previous_rank
            row["rank_change_by_stf"] = (
                previous_rank - current_rank
                if previous_rank is not None and current_rank is not None
                else None
            )
            previous_rank = current_rank
            records.append(EquityHistoryRecord(**row))

    records.sort(key=lambda record: (record.snapshot_date, record.acid))
    return records


def _to_float(raw_value: str | None) -> float | None:
    return safe_float(raw_value)


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _delta(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None:
        return None
    return current - prior


def _bottom_up_valuation(top_down: float | None, combined: float | None) -> float | None:
    if top_down is None or combined is None:
        return None
    return 2 * combined - top_down


__all__ = [
    "EquityHistoryParseResult",
    "EquityHistoryRecord",
    "parse_equity_history_workbook",
    "write_equity_history_csv",
]
