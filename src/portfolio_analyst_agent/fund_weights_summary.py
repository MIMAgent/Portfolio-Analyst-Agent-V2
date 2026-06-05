"""Build an analyst-facing markdown summary from the combined fund weights/VIR/algo CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FundCombinedRow:
    snapshot_date: str
    fund: str
    acid_type: str
    acid: str
    fund_target_rolled_exposure: float | None
    fund_benchmark_rolled_exposure: float | None
    active_rolled_exposure: float | None
    source_security_count: int | None
    sample_source_securities: str
    vir_stf: float | None
    vir_delta_stf: float | None
    algo_absolute_weight: float | None
    algo_active_weight: float | None
    algo_benchmark_weight: float | None
    vir_join_status: str
    algo_join_status: str


def load_fund_combined_rows(csv_path: str | Path) -> list[FundCombinedRow]:
    rows: list[FundCombinedRow] = []
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                FundCombinedRow(
                    snapshot_date=row.get("snapshot_date", ""),
                    fund=row.get("fund", ""),
                    acid_type=row.get("acid_type", ""),
                    acid=row.get("acid", ""),
                    fund_target_rolled_exposure=_to_float(row.get("fund_target_rolled_exposure")),
                    fund_benchmark_rolled_exposure=_to_float(row.get("fund_benchmark_rolled_exposure")),
                    active_rolled_exposure=_to_float(row.get("active_rolled_exposure")),
                    source_security_count=_to_int(row.get("source_security_count")),
                    sample_source_securities=row.get("sample_source_securities", ""),
                    vir_stf=_to_float(row.get("vir_stf")),
                    vir_delta_stf=_to_float(row.get("vir_delta_stf")),
                    algo_absolute_weight=_to_float(row.get("algo_absolute_weight")),
                    algo_active_weight=_to_float(row.get("algo_active_weight")),
                    algo_benchmark_weight=_to_float(row.get("algo_benchmark_weight")),
                    vir_join_status=row.get("vir_join_status", ""),
                    algo_join_status=row.get("algo_join_status", ""),
                )
            )
    return rows


def build_fund_weights_summary_markdown(rows: list[FundCombinedRow]) -> str:
    if not rows:
        raise ValueError("Cannot build a fund summary with no rows.")

    snapshot_date = max(row.snapshot_date for row in rows)
    funds = sorted({row.fund for row in rows})
    vir_matched = sum(1 for row in rows if row.vir_join_status == "matched_to_vir")
    algo_matched = sum(1 for row in rows if row.algo_join_status == "matched_to_algo")

    lines: list[str] = [
        "# Fund Weights, VIR, And Algo Summary",
        "",
        f"Snapshot date: {snapshot_date}",
        "",
        "This report summarizes the combined fund-level ACID table built from rolled exposures, VIR, and latest algo signals.",
        "",
        "## Coverage",
        "",
        f"- funds covered: {len(funds)}",
        f"- total fund-acid rows: {len(rows)}",
        f"- rows matched to VIR: {vir_matched}",
        f"- rows matched to algo: {algo_matched}",
        "",
    ]

    for fund in funds:
        fund_rows = [row for row in rows if row.fund == fund]
        vir_count = sum(1 for row in fund_rows if row.vir_join_status == "matched_to_vir")
        algo_count = sum(1 for row in fund_rows if row.algo_join_status == "matched_to_algo")
        # Sum exposure WITHIN each acid_type, never across them. acid_country and
        # acid_region_sector are alternate taxonomies over the SAME securities, so a
        # cross-type sum double-counts (audit C1: ~199% for equity funds). Dedupe by
        # acid within a type so repeated rows (e.g. one per algo perspective in the
        # multisignal CSV) are not counted multiple times either.
        target_by_type = _exposure_by_acid_type(fund_rows, lambda row: row.fund_target_rolled_exposure)
        benchmark_by_type = _exposure_by_acid_type(fund_rows, lambda row: row.fund_benchmark_rolled_exposure)

        lines.extend(
            [
                f"## {fund}",
                "",
                f"- ACID rows: {len(fund_rows)}",
                f"- VIR matched rows: {vir_count}",
                f"- algo matched rows: {algo_count}",
                "- summed target rolled exposure by ACID type:",
            ]
        )
        lines.extend(_exposure_breakdown_lines(target_by_type))
        lines.append("- summed benchmark rolled exposure by ACID type:")
        lines.extend(_exposure_breakdown_lines(benchmark_by_type))
        lines.append("")

        _append_section(
            lines,
            "Largest Active Overweights",
            _top_rows(fund_rows, lambda row: row.active_rolled_exposure, positive_only=True),
            include_vir=True,
            include_algo=True,
        )
        _append_section(
            lines,
            "Largest Active Underweights",
            _top_rows(fund_rows, lambda row: row.active_rolled_exposure, negative_only=True),
            include_vir=True,
            include_algo=True,
        )
        _append_section(
            lines,
            "Highest VIR STF Exposures",
            _top_rows([row for row in fund_rows if row.vir_stf is not None], lambda row: row.vir_stf),
            include_vir=True,
            include_algo=False,
        )
        _append_section(
            lines,
            "Largest VIR And Fund Active Gaps",
            _top_rows(
                [row for row in fund_rows if row.active_rolled_exposure is not None and row.vir_stf is not None],
                lambda row: abs((row.active_rolled_exposure or 0.0) - (row.vir_stf or 0.0)),
            ),
            include_vir=True,
            include_algo=False,
            include_gap=True,
        )
        _append_section(
            lines,
            "Largest Algo And Fund Active Gaps",
            _top_rows(
                [row for row in fund_rows if row.active_rolled_exposure is not None and row.algo_active_weight is not None],
                lambda row: abs((row.active_rolled_exposure or 0.0) - (row.algo_active_weight or 0.0)),
            ),
            include_vir=False,
            include_algo=True,
            include_gap=True,
        )

    return "\n".join(lines).rstrip() + "\n"


def write_fund_weights_summary_markdown(rows: list[FundCombinedRow], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_fund_weights_summary_markdown(rows), encoding="utf-8")
    return output_path


def _append_section(
    lines: list[str],
    title: str,
    rows: list[FundCombinedRow],
    *,
    include_vir: bool,
    include_algo: bool,
    include_gap: bool = False,
    limit: int = 10,
) -> None:
    lines.extend([f"### {title}", ""])
    if not rows:
        lines.extend(["No rows available.", ""])
        return

    header = ["ACID", "Type", "Target", "Bench", "Active"]
    if include_vir:
        header.extend(["VIR STF", "VIR dSTF"])
    if include_algo:
        header.extend(["Algo Abs", "Algo Active"])
    if include_gap:
        header.append("Gap")
    header.extend(["Sec Ct", "Sample Securities"])

    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")

    for row in rows[:limit]:
        values = [
            row.acid,
            row.acid_type,
            _fmt(row.fund_target_rolled_exposure),
            _fmt(row.fund_benchmark_rolled_exposure),
            _fmt(row.active_rolled_exposure),
        ]
        if include_vir:
            values.extend([_fmt(row.vir_stf), _fmt(row.vir_delta_stf)])
        if include_algo:
            values.extend([_fmt(row.algo_absolute_weight), _fmt(row.algo_active_weight)])
        if include_gap:
            gap = _gap_value(row, include_vir=include_vir, include_algo=include_algo)
            values.append(_fmt(gap))
        values.extend([str(row.source_security_count or ""), _shorten(row.sample_source_securities)])
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")


def _exposure_by_acid_type(rows: list[FundCombinedRow], metric) -> dict[str, float]:
    """Sum a per-acid exposure within each acid_type, deduped by acid.

    Exposure is a property of an (acid_type, acid), not of an algo perspective, so
    multiple rows for the same acid (as in the multisignal CSV) contribute once.
    """
    seen: set[tuple[str, str]] = set()
    totals: dict[str, float] = {}
    for row in rows:
        key = (row.acid_type, row.acid)
        if key in seen:
            continue
        seen.add(key)
        value = metric(row)
        if value is None:
            continue
        totals[row.acid_type] = totals.get(row.acid_type, 0.0) + value
    return totals


def _exposure_breakdown_lines(totals: dict[str, float]) -> list[str]:
    if not totals:
        return ["  - (none)"]
    return [f"  - {acid_type}: {_fmt(totals[acid_type])}" for acid_type in sorted(totals)]


def _top_rows(
    rows: list[FundCombinedRow],
    metric,
    *,
    positive_only: bool = False,
    negative_only: bool = False,
) -> list[FundCombinedRow]:
    available = [row for row in rows if metric(row) is not None]
    if positive_only:
        available = [row for row in available if (metric(row) or 0.0) > 0]
        return sorted(available, key=lambda row: metric(row) or 0.0, reverse=True)
    if negative_only:
        available = [row for row in available if (metric(row) or 0.0) < 0]
        return sorted(available, key=lambda row: metric(row) or 0.0)
    return sorted(available, key=lambda row: metric(row) or 0.0, reverse=True)


def _gap_value(row: FundCombinedRow, *, include_vir: bool, include_algo: bool) -> float | None:
    if include_algo and row.algo_active_weight is not None and row.active_rolled_exposure is not None:
        return abs(row.active_rolled_exposure - row.algo_active_weight)
    if include_vir and row.vir_stf is not None and row.active_rolled_exposure is not None:
        return abs(row.active_rolled_exposure - row.vir_stf)
    return None


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _shorten(value: str, limit: int = 120) -> str:
    cleaned = value.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _to_float(raw_value: str | None) -> float | None:
    if raw_value is None or raw_value == "":
        return None
    return float(raw_value)


def _to_int(raw_value: str | None) -> int | None:
    if raw_value is None or raw_value == "":
        return None
    return int(float(raw_value))


__all__ = [
    "FundCombinedRow",
    "build_fund_weights_summary_markdown",
    "load_fund_combined_rows",
    "write_fund_weights_summary_markdown",
]
