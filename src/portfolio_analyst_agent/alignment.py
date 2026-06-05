"""Thin alignment helpers for joining algo signals to VIR and holdings rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import csv
from pathlib import Path

from .csv_sources import open_csv_text
from .parse_utils import safe_float
from .sizing_snapshot import AlgoLatestSignal


@dataclass(frozen=True)
class VirRow:
    snapshot_date: date
    acid: str
    workbook_type: str
    stf: float | None
    delta_stf: float | None
    rank_in_category_by_stf: float | None
    rank_change_by_stf: float | None


@dataclass(frozen=True)
class HoldingRow:
    snapshot_date: date
    portfolio_name: str
    section_type: str
    acid: str
    mapping_status: str
    row_label: str
    row_type: str
    parent_region: str
    asset_class_name: str
    column_header: str
    is_total: bool
    value: float | None


@dataclass(frozen=True)
class AlgoVirAlignmentRow:
    snapshot_date: date
    algo_perspective: str
    sheet_dimension: str
    acid: str
    absolute_weight: float | None
    active_weight: float | None
    benchmark_weight: float | None
    absolute_weight_mom: float | None
    active_weight_mom: float | None
    vir_snapshot_date: date | None
    workbook_type: str | None
    stf: float | None
    delta_stf: float | None
    rank_in_category_by_stf: float | None
    rank_change_by_stf: float | None
    join_status: str


@dataclass(frozen=True)
class AlgoHoldingsAlignmentRow:
    snapshot_date: date
    algo_perspective: str
    sheet_dimension: str
    acid: str
    portfolio_name: str
    section_type: str
    holdings_snapshot_date: date
    holdings_value: float | None
    row_label: str
    row_type: str
    parent_region: str
    column_header: str
    is_total: bool
    absolute_weight: float | None
    active_weight: float | None
    benchmark_weight: float | None
    absolute_weight_mom: float | None
    active_weight_mom: float | None
    join_status: str


def load_vir_rows_from_csv(csv_path: str | Path) -> list[VirRow]:
    rows: list[VirRow] = []
    with open_csv_text(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                VirRow(
                    snapshot_date=date.fromisoformat(row["snapshot_date"]),
                    acid=row["acid"],
                    workbook_type=row.get("workbook_type", ""),
                    stf=_to_float(row.get("stf")),
                    delta_stf=_to_float(row.get("delta_stf")),
                    rank_in_category_by_stf=_to_float(row.get("rank_in_category_by_stf")),
                    rank_change_by_stf=_to_float(row.get("rank_change_by_stf")),
                )
            )
    return rows


def load_holdings_rows_from_csv(csv_path: str | Path) -> list[HoldingRow]:
    rows: list[HoldingRow] = []
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                HoldingRow(
                    snapshot_date=date.fromisoformat(row["snapshot_date"]),
                    portfolio_name=row.get("portfolio_name", ""),
                    section_type=row.get("section_type", ""),
                    acid=row.get("acid", ""),
                    mapping_status=row.get("mapping_status", ""),
                    row_label=row.get("row_label", ""),
                    row_type=row.get("row_type", ""),
                    parent_region=row.get("parent_region", ""),
                    asset_class_name=row.get("asset_class_name", ""),
                    column_header=row.get("column_header", ""),
                    is_total=_to_bool(row.get("is_total")),
                    value=_to_float(row.get("value")),
                )
            )
    return rows


def join_algo_to_vir(signals: list[AlgoLatestSignal], vir_rows: list[VirRow]) -> list[AlgoVirAlignmentRow]:
    indexed: dict[str, VirRow] = {}
    for row in sorted(vir_rows, key=lambda item: (item.acid, item.snapshot_date)):
        indexed[row.acid] = row

    joined: list[AlgoVirAlignmentRow] = []
    for signal in signals:
        vir_row = indexed.get(signal.acid)
        join_status = "matched_to_vir" if vir_row else "missing_in_vir"
        joined.append(
            AlgoVirAlignmentRow(
                snapshot_date=signal.snapshot_date,
                algo_perspective=signal.algo_perspective,
                sheet_dimension=signal.sheet_dimension,
                acid=signal.acid,
                absolute_weight=signal.absolute_weight,
                active_weight=signal.active_weight,
                benchmark_weight=signal.benchmark_weight,
                absolute_weight_mom=signal.absolute_weight_mom,
                active_weight_mom=signal.active_weight_mom,
                vir_snapshot_date=vir_row.snapshot_date if vir_row else None,
                workbook_type=vir_row.workbook_type if vir_row else None,
                stf=vir_row.stf if vir_row else None,
                delta_stf=vir_row.delta_stf if vir_row else None,
                rank_in_category_by_stf=vir_row.rank_in_category_by_stf if vir_row else None,
                rank_change_by_stf=vir_row.rank_change_by_stf if vir_row else None,
                join_status=join_status,
            )
        )
    return joined


def join_algo_to_holdings(signals: list[AlgoLatestSignal], holdings_rows: list[HoldingRow]) -> list[AlgoHoldingsAlignmentRow]:
    eligible_rows = [
        row
        for row in holdings_rows
        if row.acid
        and row.mapping_status == "mapped"
        and row.section_type in {"portfolio_weight", "benchmark_weight", "active_weight", "risk_contribution"}
    ]

    indexed: dict[str, list[HoldingRow]] = {}
    for row in eligible_rows:
        indexed.setdefault(row.acid, []).append(row)

    joined: list[AlgoHoldingsAlignmentRow] = []
    for signal in signals:
        holding_matches = indexed.get(signal.acid, [])
        if not holding_matches:
            joined.append(
                AlgoHoldingsAlignmentRow(
                    snapshot_date=signal.snapshot_date,
                    algo_perspective=signal.algo_perspective,
                    sheet_dimension=signal.sheet_dimension,
                    acid=signal.acid,
                    portfolio_name="",
                    section_type="",
                    holdings_snapshot_date=signal.snapshot_date,
                    holdings_value=None,
                    row_label="",
                    row_type="",
                    parent_region="",
                    column_header="",
                    is_total=False,
                    absolute_weight=signal.absolute_weight,
                    active_weight=signal.active_weight,
                    benchmark_weight=signal.benchmark_weight,
                    absolute_weight_mom=signal.absolute_weight_mom,
                    active_weight_mom=signal.active_weight_mom,
                    join_status="missing_in_holdings",
                )
            )
            continue

        for holding_row in holding_matches:
            joined.append(
                AlgoHoldingsAlignmentRow(
                    snapshot_date=signal.snapshot_date,
                    algo_perspective=signal.algo_perspective,
                    sheet_dimension=signal.sheet_dimension,
                    acid=signal.acid,
                    portfolio_name=holding_row.portfolio_name,
                    section_type=holding_row.section_type,
                    holdings_snapshot_date=holding_row.snapshot_date,
                    holdings_value=holding_row.value,
                    row_label=holding_row.row_label,
                    row_type=holding_row.row_type,
                    parent_region=holding_row.parent_region,
                    column_header=holding_row.column_header,
                    is_total=holding_row.is_total,
                    absolute_weight=signal.absolute_weight,
                    active_weight=signal.active_weight,
                    benchmark_weight=signal.benchmark_weight,
                    absolute_weight_mom=signal.absolute_weight_mom,
                    active_weight_mom=signal.active_weight_mom,
                    join_status="matched_to_holdings",
                )
            )
    return joined


def _to_float(raw_value: str | None) -> float | None:
    return safe_float(raw_value)


def _to_bool(raw_value: str | None) -> bool:
    return str(raw_value).strip().lower() in {"true", "1", "yes"}


__all__ = [
    "AlgoHoldingsAlignmentRow",
    "AlgoVirAlignmentRow",
    "HoldingRow",
    "VirRow",
    "join_algo_to_holdings",
    "join_algo_to_vir",
    "load_holdings_rows_from_csv",
    "load_vir_rows_from_csv",
]
