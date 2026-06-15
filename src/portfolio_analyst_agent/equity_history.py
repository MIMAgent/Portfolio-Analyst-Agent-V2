"""Equity VIR history normalization and trend helpers."""

from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import csv
import json
import re
from zipfile import ZIP_DEFLATED, ZipFile

from .csv_sources import csv_zip_mirror_path, open_csv_text, resolve_existing_csv_source
from .parse_utils import safe_float
from .workbook_xml import XlsxWorkbook

PARSER_VERSION = "equity_history_v1"
DEFAULT_EQUITY_VIR_BASE_HISTORY_CSV = Path("artifacts/equity_vir_history.csv")
DEFAULT_EQUITY_VIR_DATASET_CSV = Path("artifacts/vir/equity_vir_dataset.csv")

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

GENERAL_MODEL_MACHINE_HEADERS = {
    "local_real_vir": "LR10_Combined",
    "local_nominal_vir": "N10USD_Combined",
    "unconditional_vir": "LRUC",
    "price_to_fair_value": "PFV_t",
    "inflation": "Infl_RD10",
    "currency_usd": "USD_RD10",
    "yield_": "Yld_RD10",
    "growth": "Growth_RD10",
    "valuation_adjustment_top_down": "ValAdj_RD10",
    "valuation_adjustment_combined": "ValAdj_RD10_Combined",
}


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
    worksheet_names = set(workbook._worksheets.keys())
    if "Sheet1" in worksheet_names:
        return _parse_sheet1_history_workbook(workbook_path, workbook)
    if "General Model" in worksheet_names:
        return _parse_general_model_workbook(workbook_path, workbook)
    raise KeyError(f"Unsupported equity model workbook layout in {workbook_path.name}: {sorted(worksheet_names)}")


def load_equity_history_records_from_csv(csv_path: str | Path) -> list[EquityHistoryRecord]:
    records: list[EquityHistoryRecord] = []
    with open_csv_text(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            snapshot_date = date.fromisoformat(row["snapshot_date"])
            local_real_vir = _to_float(row.get("local_real_vir"))
            unconditional_vir = _to_float(row.get("unconditional_vir"))
            local_nominal_vir = _to_float(row.get("local_nominal_vir"))
            inflation = _to_float(row.get("inflation"))
            currency_usd = _to_float(row.get("currency_usd"))
            yield_ = _to_float(row.get("yield"))
            growth = _to_float(row.get("growth"))
            valuation_adjustment_top_down = _to_float(row.get("valuation_adjustment_top_down"))
            valuation_adjustment_combined = _to_float(row.get("valuation_adjustment_combined"))
            price_to_fair_value = _to_float(row.get("price_to_fair_value"))

            if all(
                value is None
                for value in (
                    local_real_vir,
                    unconditional_vir,
                    local_nominal_vir,
                    inflation,
                    currency_usd,
                    yield_,
                    growth,
                    valuation_adjustment_top_down,
                    valuation_adjustment_combined,
                    price_to_fair_value,
                )
            ):
                continue

            records.append(
                EquityHistoryRecord(
                    snapshot_date=snapshot_date,
                    ingested_at=row.get("ingested_at", ""),
                    parser_version=row.get("parser_version", PARSER_VERSION),
                    workbook_type=row.get("workbook_type", "equity_model"),
                    acid=row.get("acid", ""),
                    asset_class_name=row.get("asset_class_name") or None,
                    local_real_vir=local_real_vir,
                    local_nominal_vir=local_nominal_vir,
                    usd_hedged_vir=_to_float(row.get("usd_hedged_vir")),
                    unconditional_vir=unconditional_vir,
                    stf=_to_float(row.get("stf")),
                    price_to_fair_value=price_to_fair_value,
                    inflation=inflation,
                    currency_usd=currency_usd,
                    yield_=yield_,
                    growth=growth,
                    valuation_adjustment_top_down=valuation_adjustment_top_down,
                    valuation_adjustment_combined=valuation_adjustment_combined,
                    valuation_adjustment_bottom_up=_to_float(row.get("valuation_adjustment_bottom_up")),
                    prior_stf=_to_float(row.get("prior_stf")),
                    delta_stf=_to_float(row.get("delta_stf")),
                    delta_local_real_vir=_to_float(row.get("delta_local_real_vir")),
                    delta_local_nominal_vir=_to_float(row.get("delta_local_nominal_vir")),
                    delta_usd_hedged_vir=_to_float(row.get("delta_usd_hedged_vir")),
                    delta_unconditional_vir=_to_float(row.get("delta_unconditional_vir")),
                    delta_price_to_fair_value=_to_float(row.get("delta_price_to_fair_value")),
                    prior_rank_in_category_by_stf=_to_int(row.get("prior_rank_in_category_by_stf")),
                    rank_in_category_by_stf=_to_int(row.get("rank_in_category_by_stf")),
                    rank_change_by_stf=_to_int(row.get("rank_change_by_stf")),
                    raw_row=row.get("raw_row", ""),
                    raw_headers=row.get("raw_headers", ""),
                )
            )
    return records


def merge_equity_history_records(
    existing_records: list[EquityHistoryRecord],
    new_records: list[EquityHistoryRecord],
) -> list[EquityHistoryRecord]:
    merged: dict[tuple[date, str], dict[str, object]] = {}
    for record in existing_records:
        merged[(record.snapshot_date, record.acid)] = _record_to_base_row(record)
    for record in new_records:
        merged[(record.snapshot_date, record.acid)] = _record_to_base_row(record)
    return _apply_trend_fields(list(merged.values()))


def discover_equity_model_workbooks(data_root: str | Path) -> list[Path]:
    root = Path(data_root)
    return sorted(
        path.resolve()
        for path in root.glob("*/*Equity Model.xlsx")
        if path.is_file() and not path.name.startswith("~$")
    )


def build_equity_vir_dataset(
    *,
    base_history_csv: str | Path = DEFAULT_EQUITY_VIR_BASE_HISTORY_CSV,
    monthly_workbooks: list[str | Path] | None = None,
    output_csv: str | Path = DEFAULT_EQUITY_VIR_DATASET_CSV,
    include_existing_output: bool = True,
) -> tuple[Path, list[EquityHistoryRecord]]:
    merged_records: list[EquityHistoryRecord] = []
    output_path = Path(output_csv)

    if include_existing_output:
        existing_source = resolve_existing_csv_source(output_path)
        if existing_source:
            merged_records = merge_equity_history_records(
                merged_records,
                load_equity_history_records_from_csv(existing_source),
            )

    base_source = resolve_existing_csv_source(base_history_csv)
    if base_source:
        merged_records = merge_equity_history_records(
            merged_records,
            load_equity_history_records_from_csv(base_source),
        )

    for workbook_path in [Path(path).resolve() for path in monthly_workbooks or []]:
        result = parse_equity_history_workbook(workbook_path)
        merged_records = merge_equity_history_records(merged_records, result.records)

    output_path = write_equity_history_csv(merged_records, output_path)
    write_equity_history_zip_mirror(output_path)
    return output_path, merged_records


def _parse_sheet1_history_workbook(workbook_path: Path, workbook: XlsxWorkbook) -> EquityHistoryParseResult:
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


def _parse_general_model_workbook(workbook_path: Path, workbook: XlsxWorkbook) -> EquityHistoryParseResult:
    worksheet = workbook.worksheet("General Model")
    header_map = _general_model_header_map(worksheet)
    snapshot_date = _general_model_snapshot_date(worksheet)
    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    raw_headers = json.dumps(header_map, sort_keys=True)

    base_rows: list[dict[str, object]] = []
    for row_number in sorted(worksheet.rows):
        if row_number <= 5:
            continue

        acid = worksheet.get_cell(row_number, header_map["acid"]).strip()
        if not acid:
            continue

        asset_class_name = worksheet.get_cell(row_number, header_map["asset_class_name"]).strip() or None
        local_real_vir = _to_float(worksheet.get_cell(row_number, header_map["local_real_vir"]).strip())
        unconditional_vir = _to_float(worksheet.get_cell(row_number, header_map["unconditional_vir"]).strip())
        local_nominal_vir = _to_float(worksheet.get_cell(row_number, header_map["local_nominal_vir"]).strip())
        price_to_fair_value = _to_float(worksheet.get_cell(row_number, header_map["price_to_fair_value"]).strip())
        inflation = _to_float(worksheet.get_cell(row_number, header_map["inflation"]).strip())
        currency_usd = _to_float(worksheet.get_cell(row_number, header_map["currency_usd"]).strip())
        yield_ = _to_float(worksheet.get_cell(row_number, header_map["yield_"]).strip())
        growth = _to_float(worksheet.get_cell(row_number, header_map["growth"]).strip())
        valuation_adjustment_top_down = _to_float(
            worksheet.get_cell(row_number, header_map["valuation_adjustment_top_down"]).strip()
        )
        valuation_adjustment_combined = _to_float(
            worksheet.get_cell(row_number, header_map["valuation_adjustment_combined"]).strip()
        )

        if all(
            value is None
            for value in (
                local_real_vir,
                unconditional_vir,
                local_nominal_vir,
                inflation,
                yield_,
                growth,
                valuation_adjustment_top_down,
                valuation_adjustment_combined,
            )
        ):
            continue

        raw_row = {
            "acid": acid,
            "asset_class_name": asset_class_name or "",
            "snapshot_date": snapshot_date.isoformat(),
            "lr10_combined": worksheet.get_cell(row_number, header_map["local_real_vir"]).strip(),
            "lruc": worksheet.get_cell(row_number, header_map["unconditional_vir"]).strip(),
            "usdn_uh10_combined": worksheet.get_cell(row_number, header_map["local_nominal_vir"]).strip(),
            "pfv_agg": worksheet.get_cell(row_number, header_map["price_to_fair_value"]).strip(),
            "infl_rd": worksheet.get_cell(row_number, header_map["inflation"]).strip(),
            "usd_rduh10": worksheet.get_cell(row_number, header_map["currency_usd"]).strip(),
            "yield_rd10": worksheet.get_cell(row_number, header_map["yield_"]).strip(),
            "growth_rd": worksheet.get_cell(row_number, header_map["growth"]).strip(),
            "valadj_rd10": worksheet.get_cell(row_number, header_map["valuation_adjustment_top_down"]).strip(),
            "valadj_rd10_combined": worksheet.get_cell(row_number, header_map["valuation_adjustment_combined"]).strip(),
        }

        base_rows.append(
            {
                "snapshot_date": snapshot_date,
                "ingested_at": ingested_at,
                "parser_version": PARSER_VERSION,
                "workbook_type": "equity_model",
                "acid": acid,
                "asset_class_name": asset_class_name,
                "local_real_vir": local_real_vir,
                "local_nominal_vir": local_nominal_vir,
                "usd_hedged_vir": None,
                "unconditional_vir": unconditional_vir,
                "stf": _diff(local_real_vir, unconditional_vir),
                "price_to_fair_value": price_to_fair_value,
                "inflation": inflation,
                "currency_usd": currency_usd,
                "yield_": yield_,
                "growth": growth,
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
    return EquityHistoryParseResult(
        workbook_path=workbook_path,
        row_count=len(records),
        snapshot_dates=[snapshot_date] if records else [],
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


def write_equity_history_zip_mirror(csv_path: str | Path) -> Path:
    csv_path = Path(csv_path)
    mirror_path = csv_zip_mirror_path(csv_path)
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(mirror_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(csv_path, arcname=csv_path.name)
    return mirror_path


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


def _general_model_header_map(worksheet) -> dict[str, int]:
    header_map: dict[str, int] = {}
    for column_number, raw_header in worksheet.nonempty_cells(3):
        normalized = raw_header.strip()
        for key, expected in GENERAL_MODEL_MACHINE_HEADERS.items():
            if normalized == expected:
                header_map[key] = column_number

    for column_number, raw_header in worksheet.nonempty_cells(5):
        normalized = raw_header.strip()
        if normalized == "ACIDs":
            header_map["acid"] = column_number
        elif normalized == "Asset Class Name":
            header_map["asset_class_name"] = column_number

    required = {"acid", "asset_class_name", *GENERAL_MODEL_MACHINE_HEADERS.keys()}
    missing = sorted(required - set(header_map.keys()))
    if missing:
        raise ValueError(f"Missing required General Model headers: {missing}")
    return header_map


def _general_model_snapshot_date(worksheet) -> date:
    token = ""
    for _, raw_header in worksheet.nonempty_cells(5):
        value = raw_header.strip()
        if "As of " in value:
            token = value
            break
    match = re.search(r"As of (\d{2})/(\d{4})", token)
    if not match:
        raise ValueError("Could not determine General Model snapshot month from row 5 headers.")
    month = int(match.group(1))
    year = int(match.group(2))
    return date(year, month, calendar.monthrange(year, month)[1])


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


def _record_to_base_row(record: EquityHistoryRecord) -> dict[str, object]:
    return {
        "snapshot_date": record.snapshot_date,
        "ingested_at": record.ingested_at,
        "parser_version": record.parser_version,
        "workbook_type": record.workbook_type,
        "acid": record.acid,
        "asset_class_name": record.asset_class_name,
        "local_real_vir": record.local_real_vir,
        "local_nominal_vir": record.local_nominal_vir,
        "usd_hedged_vir": record.usd_hedged_vir,
        "unconditional_vir": record.unconditional_vir,
        "stf": record.stf,
        "price_to_fair_value": record.price_to_fair_value,
        "inflation": record.inflation,
        "currency_usd": record.currency_usd,
        "yield_": record.yield_,
        "growth": record.growth,
        "valuation_adjustment_top_down": record.valuation_adjustment_top_down,
        "valuation_adjustment_combined": record.valuation_adjustment_combined,
        "valuation_adjustment_bottom_up": record.valuation_adjustment_bottom_up,
        "raw_row": record.raw_row,
        "raw_headers": record.raw_headers,
    }


def _to_float(raw_value: str | None) -> float | None:
    return safe_float(raw_value)


def _to_int(raw_value: str | None) -> int | None:
    if raw_value is None or raw_value == "":
        return None
    return int(float(raw_value))


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
    "DEFAULT_EQUITY_VIR_BASE_HISTORY_CSV",
    "DEFAULT_EQUITY_VIR_DATASET_CSV",
    "EquityHistoryParseResult",
    "EquityHistoryRecord",
    "build_equity_vir_dataset",
    "discover_equity_model_workbooks",
    "load_equity_history_records_from_csv",
    "merge_equity_history_records",
    "parse_equity_history_workbook",
    "write_equity_history_csv",
    "write_equity_history_zip_mirror",
]
