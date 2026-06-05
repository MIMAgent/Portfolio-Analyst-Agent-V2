"""Cross-reference rolled exposure outputs to VIR rows and latest algo signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import csv
from pathlib import Path

from .alignment import VirRow, load_vir_rows_from_csv
from .algo_parser import parse_multiple_algo_workbooks
from .row_ids import account_alignment_row_id, fund_alignment_row_id
from .signal_aliases import build_vir_index
from .sizing_snapshot import AlgoLatestSignal, latest_signals_from_results


@dataclass(frozen=True)
class AccountExposureAlignmentRow:
    snapshot_date: date
    exposure_source: str
    source_file: str
    portcode: str
    account_name: str
    acid_type: str
    acid: str
    account_rolled_exposure: float | None
    source_security_count: int | None
    sample_source_securities: str
    vir_snapshot_date: date | None
    vir_workbook_type: str | None
    vir_stf: float | None
    vir_delta_stf: float | None
    vir_rank_in_category_by_stf: float | None
    vir_rank_change_by_stf: float | None
    algo_snapshot_date: date | None
    algo_perspective: str | None
    algo_sheet_dimension: str | None
    algo_absolute_weight: float | None
    algo_active_weight: float | None
    algo_benchmark_weight: float | None
    algo_absolute_weight_mom: float | None
    algo_active_weight_mom: float | None
    vir_join_status: str
    algo_join_status: str


@dataclass(frozen=True)
class FundExposureAlignmentRow:
    snapshot_date: date
    exposure_source: str
    source_file: str
    fund: str
    acid_type: str
    acid: str
    fund_target_rolled_exposure: float | None
    fund_benchmark_rolled_exposure: float | None
    active_rolled_exposure: float | None
    matched_target_weight: float | None
    target_match_pct: float | None
    matched_benchmark_weight: float | None
    benchmark_match_pct: float | None
    benchmark_coverage_ok: bool | None
    source_security_count: int | None
    sample_source_securities: str
    vir_snapshot_date: date | None
    vir_workbook_type: str | None
    vir_stf: float | None
    vir_delta_stf: float | None
    vir_rank_in_category_by_stf: float | None
    vir_rank_change_by_stf: float | None
    algo_snapshot_date: date | None
    algo_perspective: str | None
    algo_sheet_dimension: str | None
    algo_absolute_weight: float | None
    algo_active_weight: float | None
    algo_benchmark_weight: float | None
    algo_absolute_weight_mom: float | None
    algo_active_weight_mom: float | None
    vir_join_status: str
    algo_join_status: str


@dataclass(frozen=True)
class AlgoJoinExpectation:
    algo_perspective: str | None
    algo_sheet_dimension: str | None
    algo_join_status: str


def build_account_exposure_alignment(
    account_summary_csv: str | Path,
    vir_csv: str | Path | None = None,
    algo_workbooks: list[str | Path] | None = None,
) -> list[AccountExposureAlignmentRow]:
    account_rows = _load_csv_rows(account_summary_csv)
    vir_index = _latest_vir_by_acid(load_vir_rows_from_csv(vir_csv)) if vir_csv else {}
    algo_index, algo_specs_by_dimension = _algo_context(algo_workbooks)

    rows: list[AccountExposureAlignmentRow] = []
    for row in account_rows:
        acid = row["acid"]
        acid_type = row.get("acid_type", "")
        vir_row = vir_index.get(acid)
        vir_has_signal = _vir_has_signal(vir_row)

        for expectation in _algo_expectations(
            acid_type=acid_type,
            algo_workbooks=algo_workbooks,
            algo_specs_by_dimension=algo_specs_by_dimension,
        ):
            algo_row = _algo_row_for_expectation(algo_index, acid, expectation)
            algo_join_status = "matched_to_algo" if algo_row else expectation.algo_join_status
            rows.append(
                AccountExposureAlignmentRow(
                    snapshot_date=date.fromisoformat(row["snapshot_date"]),
                    exposure_source="account_summary",
                    source_file=row.get("source_file", ""),
                    portcode=row.get("portcode", ""),
                    account_name=row.get("account_name", ""),
                    acid_type=acid_type,
                    acid=acid,
                    account_rolled_exposure=_to_float(row.get("account_rolled_exposure")),
                    source_security_count=_to_int(row.get("source_security_count")),
                    sample_source_securities=row.get("sample_source_securities", ""),
                    vir_snapshot_date=vir_row.snapshot_date if vir_has_signal else None,
                    vir_workbook_type=vir_row.workbook_type if vir_has_signal else None,
                    vir_stf=vir_row.stf if vir_has_signal else None,
                    vir_delta_stf=vir_row.delta_stf if vir_has_signal else None,
                    vir_rank_in_category_by_stf=vir_row.rank_in_category_by_stf if vir_has_signal else None,
                    vir_rank_change_by_stf=vir_row.rank_change_by_stf if vir_has_signal else None,
                    algo_snapshot_date=algo_row.snapshot_date if algo_row else None,
                    algo_perspective=(
                        algo_row.algo_perspective if algo_row else expectation.algo_perspective
                    ),
                    algo_sheet_dimension=(
                        algo_row.sheet_dimension if algo_row else expectation.algo_sheet_dimension
                    ),
                    algo_absolute_weight=algo_row.absolute_weight if algo_row else None,
                    algo_active_weight=algo_row.active_weight if algo_row else None,
                    algo_benchmark_weight=algo_row.benchmark_weight if algo_row else None,
                    algo_absolute_weight_mom=algo_row.absolute_weight_mom if algo_row else None,
                    algo_active_weight_mom=algo_row.active_weight_mom if algo_row else None,
                    vir_join_status="matched_to_vir" if vir_has_signal else "missing_in_vir",
                    algo_join_status=algo_join_status,
                )
            )
    return rows


def build_fund_exposure_alignment(
    fund_summary_csv: str | Path,
    vir_csv: str | Path | None = None,
    algo_workbooks: list[str | Path] | None = None,
) -> list[FundExposureAlignmentRow]:
    fund_rows = _load_csv_rows(fund_summary_csv)
    vir_index = _latest_vir_by_acid(load_vir_rows_from_csv(vir_csv)) if vir_csv else {}
    algo_index, algo_specs_by_dimension = _algo_context(algo_workbooks)

    rows: list[FundExposureAlignmentRow] = []
    for row in fund_rows:
        acid = row["acid"]
        acid_type = row.get("acid_type", "")
        vir_row = vir_index.get(acid)
        vir_has_signal = _vir_has_signal(vir_row)

        for expectation in _algo_expectations(
            acid_type=acid_type,
            algo_workbooks=algo_workbooks,
            algo_specs_by_dimension=algo_specs_by_dimension,
        ):
            algo_row = _algo_row_for_expectation(algo_index, acid, expectation)
            algo_join_status = "matched_to_algo" if algo_row else expectation.algo_join_status
            rows.append(
                FundExposureAlignmentRow(
                    snapshot_date=date.fromisoformat(row["snapshot_date"]),
                    exposure_source="fund_summary",
                    source_file=row.get("source_file", ""),
                    fund=row.get("fund", ""),
                    acid_type=acid_type,
                    acid=acid,
                    fund_target_rolled_exposure=_to_float(row.get("fund_target_rolled_exposure")),
                    fund_benchmark_rolled_exposure=_to_float(row.get("fund_benchmark_rolled_exposure")),
                    active_rolled_exposure=_to_float(row.get("active_rolled_exposure")),
                    matched_target_weight=_to_float(row.get("matched_target_weight")),
                    target_match_pct=_to_float(row.get("target_match_pct")),
                    matched_benchmark_weight=_to_float(row.get("matched_benchmark_weight")),
                    benchmark_match_pct=_to_float(row.get("benchmark_match_pct")),
                    benchmark_coverage_ok=_to_bool(row.get("benchmark_coverage_ok")),
                    source_security_count=_to_int(row.get("source_security_count")),
                    sample_source_securities=row.get("sample_source_securities", ""),
                    vir_snapshot_date=vir_row.snapshot_date if vir_has_signal else None,
                    vir_workbook_type=vir_row.workbook_type if vir_has_signal else None,
                    vir_stf=vir_row.stf if vir_has_signal else None,
                    vir_delta_stf=vir_row.delta_stf if vir_has_signal else None,
                    vir_rank_in_category_by_stf=vir_row.rank_in_category_by_stf if vir_has_signal else None,
                    vir_rank_change_by_stf=vir_row.rank_change_by_stf if vir_has_signal else None,
                    algo_snapshot_date=algo_row.snapshot_date if algo_row else None,
                    algo_perspective=(
                        algo_row.algo_perspective if algo_row else expectation.algo_perspective
                    ),
                    algo_sheet_dimension=(
                        algo_row.sheet_dimension if algo_row else expectation.algo_sheet_dimension
                    ),
                    algo_absolute_weight=algo_row.absolute_weight if algo_row else None,
                    algo_active_weight=algo_row.active_weight if algo_row else None,
                    algo_benchmark_weight=algo_row.benchmark_weight if algo_row else None,
                    algo_absolute_weight_mom=algo_row.absolute_weight_mom if algo_row else None,
                    algo_active_weight_mom=algo_row.active_weight_mom if algo_row else None,
                    vir_join_status="matched_to_vir" if vir_has_signal else "missing_in_vir",
                    algo_join_status=algo_join_status,
                )
            )
    return rows


def write_alignment_csv(rows: list[object], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write an empty alignment CSV.")

    first_row = _with_row_id(_normalize_row(asdict(rows[0])), output_path)
    fieldnames = list(first_row.keys())

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(first_row)
        for row in rows[1:]:
            writer.writerow(_with_row_id(_normalize_row(asdict(row)), output_path))
    return output_path


def _latest_vir_by_acid(vir_rows: list[VirRow]) -> dict[str, VirRow]:
    return build_vir_index(vir_rows)


def _algo_context(
    workbooks: list[str | Path] | None,
) -> tuple[dict[tuple[str, str, str], AlgoLatestSignal], dict[str, list[AlgoJoinExpectation]]]:
    if not workbooks:
        return {}, {}

    signals = latest_signals_from_results(parse_multiple_algo_workbooks(list(workbooks)))
    indexed: dict[tuple[str, str, str], AlgoLatestSignal] = {}
    specs_by_dimension: dict[str, set[str]] = {}
    for signal in sorted(signals, key=lambda item: (item.acid, item.sheet_dimension, item.algo_perspective)):
        indexed[(signal.acid, signal.sheet_dimension, signal.algo_perspective)] = signal
        specs_by_dimension.setdefault(signal.sheet_dimension, set()).add(signal.algo_perspective)

    normalized_specs: dict[str, list[AlgoJoinExpectation]] = {}
    for dimension, perspectives in specs_by_dimension.items():
        normalized_specs[dimension] = [
            AlgoJoinExpectation(
                algo_perspective=perspective,
                algo_sheet_dimension=dimension,
                algo_join_status="missing_in_algo",
            )
            for perspective in sorted(perspectives)
        ]

    return indexed, normalized_specs


def _algo_expectations(
    acid_type: str,
    algo_workbooks: list[str | Path] | None,
    algo_specs_by_dimension: dict[str, list[AlgoJoinExpectation]],
) -> list[AlgoJoinExpectation]:
    if not algo_workbooks:
        return [AlgoJoinExpectation(None, None, "algo_not_provided")]

    dimension = _algo_dimension_for_acid_type(acid_type)
    if dimension is None:
        return [AlgoJoinExpectation(None, None, "not_applicable_for_acid_type")]

    specs = algo_specs_by_dimension.get(dimension, [])
    if specs:
        return specs

    return [AlgoJoinExpectation(None, dimension, "missing_in_algo")]


def _algo_dimension_for_acid_type(acid_type: str) -> str | None:
    mapping = {
        "acid_country": "countries",
        "acid_region_sector": "regional_sectors",
    }
    return mapping.get(acid_type)


def _algo_row_for_expectation(
    algo_index: dict[tuple[str, str, str], AlgoLatestSignal],
    acid: str,
    expectation: AlgoJoinExpectation,
) -> AlgoLatestSignal | None:
    if expectation.algo_perspective is None or expectation.algo_sheet_dimension is None:
        return None
    return algo_index.get((acid, expectation.algo_sheet_dimension, expectation.algo_perspective))


def _load_csv_rows(csv_path: str | Path) -> list[dict[str, str]]:
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _vir_has_signal(vir_row: VirRow | None) -> bool:
    if vir_row is None:
        return False
    return any(
        value is not None
        for value in (
            vir_row.stf,
            vir_row.delta_stf,
            vir_row.rank_in_category_by_stf,
            vir_row.rank_change_by_stf,
        )
    )


def _normalize_row(row: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, date):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized


def _with_row_id(row: dict[str, object], output_path: str | Path) -> dict[str, object]:
    path_name = Path(output_path).name
    if row.get("row_id"):
        return row

    if path_name.startswith("account_"):
        row_id = account_alignment_row_id(
            snapshot_date=row.get("snapshot_date", ""),
            portcode=row.get("portcode", ""),
            acid_type=row.get("acid_type", ""),
            acid=row.get("acid", ""),
            algo_perspective=row.get("algo_perspective", ""),
        )
    else:
        row_id = fund_alignment_row_id(
            snapshot_date=row.get("snapshot_date", ""),
            fund=row.get("fund", ""),
            acid_type=row.get("acid_type", ""),
            acid=row.get("acid", ""),
            algo_perspective=row.get("algo_perspective", ""),
        )
    return {"row_id": row_id, **row}


def _to_float(raw_value: str | None) -> float | None:
    if raw_value is None or raw_value == "":
        return None
    return float(raw_value)


def _to_int(raw_value: str | None) -> int | None:
    if raw_value is None or raw_value == "":
        return None
    return int(float(raw_value))


def _to_bool(raw_value: str | None) -> bool | None:
    if raw_value is None or raw_value == "":
        return None
    return str(raw_value).strip().lower() in {"true", "1", "yes"}


__all__ = [
    "AccountExposureAlignmentRow",
    "FundExposureAlignmentRow",
    "build_account_exposure_alignment",
    "build_fund_exposure_alignment",
    "write_alignment_csv",
]
