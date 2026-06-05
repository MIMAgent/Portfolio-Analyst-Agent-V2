"""Monthly algo workbook parser."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
import csv

from .parse_utils import safe_float
from .workbook_xml import XlsxWorkbook, _number_to_column


@dataclass(frozen=True)
class MetricBlock:
    metric_type: str
    start_row: int
    end_row: int
    label_row: int | None = None
    label_value: str | None = None


@dataclass(frozen=True)
class SheetSpec:
    sheet_dimension: str
    blocks: tuple[MetricBlock, ...]
    summary_label_row: int
    summary_label_value: str


@dataclass(frozen=True)
class AlgoRecord:
    snapshot_date: date
    source_file: str
    sheet_name: str
    algo_perspective: str
    sheet_dimension: str
    metric_type: str
    acid: str
    period_end: date
    value: float | None
    source_row: int
    source_column: str
    raw_header_value: str


@dataclass(frozen=True)
class AlgoParseResult:
    workbook_path: Path
    algo_perspective: str
    snapshot_date: date
    records: list[AlgoRecord]

    def summary(self) -> dict[str, object]:
        counts_by_metric: dict[str, int] = {}
        counts_by_sheet: dict[str, int] = {}

        for record in self.records:
            counts_by_metric[record.metric_type] = counts_by_metric.get(record.metric_type, 0) + 1
            counts_by_sheet[record.sheet_dimension] = counts_by_sheet.get(record.sheet_dimension, 0) + 1

        return {
            "source_file": self.workbook_path.name,
            "algo_perspective": self.algo_perspective,
            "snapshot_date": self.snapshot_date.isoformat(),
            "record_count": len(self.records),
            "counts_by_metric": counts_by_metric,
            "counts_by_sheet": counts_by_sheet,
        }


SHEET_SPECS: dict[str, SheetSpec] = {
    "Countries": SheetSpec(
        sheet_dimension="countries",
        blocks=(
            MetricBlock(metric_type="absolute_weight", start_row=2, end_row=52),
            MetricBlock(metric_type="active_weight", start_row=55, end_row=105, label_row=54, label_value="Active Weights"),
            MetricBlock(metric_type="benchmark_weight", start_row=108, end_row=158, label_row=107, label_value="Bench Weights"),
            MetricBlock(metric_type="absolute_weight_mom", start_row=161, end_row=211, label_row=160, label_value="Mom"),
            MetricBlock(metric_type="active_weight_mom", start_row=214, end_row=264, label_row=213, label_value="Active Mom"),
        ),
        summary_label_row=266,
        summary_label_value="Region Weight",
    ),
    "RegionalSectors": SheetSpec(
        sheet_dimension="regional_sectors",
        blocks=(
            MetricBlock(metric_type="absolute_weight", start_row=2, end_row=50),
            MetricBlock(metric_type="active_weight", start_row=53, end_row=101, label_row=52, label_value="Active Weights"),
            MetricBlock(metric_type="benchmark_weight", start_row=104, end_row=152, label_row=103, label_value="Bench Weights"),
            MetricBlock(metric_type="absolute_weight_mom", start_row=155, end_row=203, label_row=154, label_value="Mom"),
            MetricBlock(metric_type="active_weight_mom", start_row=206, end_row=254, label_row=205, label_value="Active Mom"),
        ),
        summary_label_row=256,
        summary_label_value="Region Weight",
    ),
}


def excel_serial_to_date(raw_value: str) -> date:
    serial = int(float(raw_value))
    return date(1899, 12, 30) + timedelta(days=serial)


def infer_algo_perspective(workbook_path: str | Path) -> str:
    file_name = Path(workbook_path).name.lower()
    if "algo lr" in file_name:
        return "local_real"
    if "algo usd unhedged" in file_name:
        return "usd_unhedged"
    raise ValueError(
        f"Could not infer algo perspective from {Path(workbook_path).name!r}. "
        "Expected 'Algo LR' or 'Algo USD Unhedged' in the filename."
    )


def parse_algo_workbook(workbook_path: str | Path) -> AlgoParseResult:
    workbook_path = Path(workbook_path)
    workbook = XlsxWorkbook(workbook_path)
    algo_perspective = infer_algo_perspective(workbook_path)

    records: list[AlgoRecord] = []
    all_periods: set[date] = set()

    for sheet_name, sheet_spec in SHEET_SPECS.items():
        worksheet = workbook.worksheet(sheet_name)
        period_columns = _period_columns_for_sheet(worksheet)
        all_periods.update(period_end for _, _, period_end in period_columns)

        summary_label = worksheet.get_cell(sheet_spec.summary_label_row, 1)
        if summary_label != sheet_spec.summary_label_value:
            raise ValueError(
                f"{workbook_path.name}::{sheet_name} expected summary label "
                f"{sheet_spec.summary_label_value!r} in row {sheet_spec.summary_label_row}, got {summary_label!r}."
            )

        for block in sheet_spec.blocks:
            _validate_block_label(workbook_path, sheet_name, worksheet, block)

            for row_number in range(block.start_row, block.end_row + 1):
                acid = worksheet.get_cell(row_number, 1).strip()
                if not acid:
                    continue

                for column_number, raw_header, period_end in period_columns:
                    raw_value = worksheet.get_cell(row_number, column_number).strip()
                    value = safe_float(
                        raw_value,
                        context=f"algo {acid} row {row_number} col {_number_to_column(column_number)}",
                    )
                    records.append(
                        AlgoRecord(
                            snapshot_date=max(all_periods) if all_periods else period_end,
                            source_file=workbook_path.name,
                            sheet_name=sheet_name,
                            algo_perspective=algo_perspective,
                            sheet_dimension=sheet_spec.sheet_dimension,
                            metric_type=block.metric_type,
                            acid=acid,
                            period_end=period_end,
                            value=value,
                            source_row=row_number,
                            source_column=_number_to_column(column_number),
                            raw_header_value=raw_header,
                        )
                    )

    if not records:
        raise ValueError(f"No algo records were parsed from {workbook_path.name}.")

    snapshot_date = max(all_periods)
    records = [
        AlgoRecord(
            snapshot_date=snapshot_date,
            source_file=record.source_file,
            sheet_name=record.sheet_name,
            algo_perspective=record.algo_perspective,
            sheet_dimension=record.sheet_dimension,
            metric_type=record.metric_type,
            acid=record.acid,
            period_end=record.period_end,
            value=record.value,
            source_row=record.source_row,
            source_column=record.source_column,
            raw_header_value=record.raw_header_value,
        )
        for record in records
    ]

    return AlgoParseResult(
        workbook_path=workbook_path,
        algo_perspective=algo_perspective,
        snapshot_date=snapshot_date,
        records=records,
    )


def parse_multiple_algo_workbooks(workbook_paths: list[str | Path]) -> list[AlgoParseResult]:
    return [parse_algo_workbook(workbook_path) for workbook_path in workbook_paths]


def write_records_csv(records: list[AlgoRecord], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(asdict(records[0]).keys()) if records else [
        "snapshot_date",
        "source_file",
        "sheet_name",
        "algo_perspective",
        "sheet_dimension",
        "metric_type",
        "acid",
        "period_end",
        "value",
        "source_row",
        "source_column",
        "raw_header_value",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["snapshot_date"] = row["snapshot_date"].isoformat()
            row["period_end"] = row["period_end"].isoformat()
            writer.writerow(row)

    return output_path


def _period_columns_for_sheet(worksheet) -> list[tuple[int, str, date]]:
    period_columns: list[tuple[int, str, date]] = []
    for column_number, raw_header in worksheet.nonempty_cells(1, start_column=2):
        try:
            period_end = excel_serial_to_date(raw_header)
        except ValueError as exc:
            raise ValueError(
                f"Could not parse month header {raw_header!r} in {worksheet.name} row 1 column {column_number}."
            ) from exc
        period_columns.append((column_number, raw_header, period_end))

    if not period_columns:
        raise ValueError(f"No month headers found in worksheet {worksheet.name!r}.")

    return period_columns


def _validate_block_label(workbook_path: Path, sheet_name: str, worksheet, block: MetricBlock) -> None:
    if block.label_row is None or block.label_value is None:
        return

    observed = worksheet.get_cell(block.label_row, 1)
    if observed != block.label_value:
        raise ValueError(
            f"{workbook_path.name}::{sheet_name} expected section label {block.label_value!r} "
            f"in row {block.label_row}, got {observed!r}."
        )


__all__ = [
    "AlgoParseResult",
    "AlgoRecord",
    "parse_algo_workbook",
    "parse_multiple_algo_workbooks",
    "write_records_csv",
]
