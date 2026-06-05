"""Generate a structured review pack for one-by-one fund validation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .row_ids import fund_review_row_id


DEFAULT_FUND_ORDER = [
    "MStar US Equity",
    "MStar International Equity",
    "MStar Global Opportunistic Equity",
    "MStar Global Income",
    "MStar Municipal Bond",
    "MStar Total Return Bond",
    "MStar Defensive Bond",
    "MStar Multisector Bond",
    "MStar Alternatives",
]


@dataclass(frozen=True)
class FundCombinedReviewRow:
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
    algo_active_weight: float | None
    vir_join_status: str
    algo_join_status: str


@dataclass(frozen=True)
class FundCoverageRow:
    snapshot_date: str
    fund: str
    total_target_weight: float | None
    matched_target_weight: float | None
    target_match_pct: float | None
    total_benchmark_weight: float | None
    matched_benchmark_weight: float | None
    benchmark_match_pct: float | None


def load_fund_review_rows(csv_path: str | Path) -> list[FundCombinedReviewRow]:
    rows: list[FundCombinedReviewRow] = []
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                FundCombinedReviewRow(
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
                    algo_active_weight=_to_float(row.get("algo_active_weight")),
                    vir_join_status=row.get("vir_join_status", ""),
                    algo_join_status=row.get("algo_join_status", ""),
                )
            )
    return rows


def load_fund_coverage_rows(csv_path: str | Path) -> dict[str, FundCoverageRow]:
    coverage_by_fund: dict[str, FundCoverageRow] = {}
    with Path(csv_path).open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            coverage_row = FundCoverageRow(
                snapshot_date=row.get("snapshot_date", ""),
                fund=row.get("fund", ""),
                total_target_weight=_to_float(row.get("total_target_weight")),
                matched_target_weight=_to_float(row.get("matched_target_weight")),
                target_match_pct=_to_float(row.get("target_match_pct")),
                total_benchmark_weight=_to_float(row.get("total_benchmark_weight")),
                matched_benchmark_weight=_to_float(row.get("matched_benchmark_weight")),
                benchmark_match_pct=_to_float(row.get("benchmark_match_pct")),
            )
            coverage_by_fund[coverage_row.fund] = coverage_row
    return coverage_by_fund


def build_fund_review_checklist_rows(
    rows: list[FundCombinedReviewRow],
    coverage_by_fund: dict[str, FundCoverageRow],
) -> list[dict[str, str]]:
    checklist_rows: list[dict[str, str]] = []
    for review_order, fund in enumerate(_ordered_funds(rows), start=1):
        fund_rows = [row for row in rows if row.fund == fund]
        coverage = coverage_by_fund.get(fund)

        target_total = sum((row.fund_target_rolled_exposure or 0.0) for row in fund_rows)
        benchmark_total = sum((row.fund_benchmark_rolled_exposure or 0.0) for row in fund_rows)
        vir_matched = sum(1 for row in fund_rows if row.vir_join_status == "matched_to_vir")
        algo_matched = sum(1 for row in fund_rows if row.algo_join_status == "matched_to_algo")

        checklist_rows.append(
            {
                "row_id": fund_review_row_id(
                    snapshot_date=coverage.snapshot_date if coverage else _latest_snapshot_date(fund_rows),
                    fund=fund,
                ),
                "review_order": str(review_order),
                "fund": fund,
                "snapshot_date": coverage.snapshot_date if coverage else _latest_snapshot_date(fund_rows),
                "acid_rows": str(len(fund_rows)),
                "target_match_pct": _fmt_pct(coverage.target_match_pct if coverage else None),
                "benchmark_match_pct": _fmt_pct(coverage.benchmark_match_pct if coverage else None),
                "vir_matched_rows": str(vir_matched),
                "algo_matched_rows": str(algo_matched),
                "summed_target_rolled_exposure": _fmt(target_total),
                "summed_benchmark_rolled_exposure": _fmt(benchmark_total),
                "benchmark_expected_status": _benchmark_status(coverage),
                "coverage_ok": "",
                "top_3_suspicious_acids": "",
                "missing_vir_notes": "",
                "missing_algo_notes": "",
                "benchmark_notes": "",
                "lineage_notes": "",
                "action_needed": "",
                "review_status": "not_started",
                "next_step": "",
            }
        )
    return checklist_rows


def write_fund_review_checklist_csv(rows: list[dict[str, str]], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_id",
        "review_order",
        "fund",
        "snapshot_date",
        "acid_rows",
        "target_match_pct",
        "benchmark_match_pct",
        "vir_matched_rows",
        "algo_matched_rows",
        "summed_target_rolled_exposure",
        "summed_benchmark_rolled_exposure",
        "benchmark_expected_status",
        "coverage_ok",
        "top_3_suspicious_acids",
        "missing_vir_notes",
        "missing_algo_notes",
        "benchmark_notes",
        "lineage_notes",
        "action_needed",
        "review_status",
        "next_step",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def build_fund_review_workbook_markdown(
    rows: list[FundCombinedReviewRow],
    coverage_by_fund: dict[str, FundCoverageRow],
) -> str:
    if not rows:
        raise ValueError("Cannot build a fund review workbook with no rows.")

    lines = [
        "# Fund Review Workbook",
        "",
        f"Snapshot date: {max(row.snapshot_date for row in rows)}",
        "",
        "Use this workbook to review each fund one by one and confirm that rolled exposures, VIR joins, algo joins, and security lineage all look correct.",
        "",
        "## Review Questions",
        "",
        "For each fund, answer these questions:",
        "",
        "1. Does rollthrough coverage look complete?",
        "2. Do the largest active overweights and underweights look economically sensible?",
        "3. Are VIR matches present where equity ACIDs should match?",
        "4. Are algo matches present where eligible ACIDs should match?",
        "5. Are benchmark gaps expected, or do they indicate a workbook/parser issue?",
        "6. If something looks wrong, which ACIDs should we trace into security lineage next?",
        "",
        "## Suggested Review Order",
        "",
    ]

    for index, fund in enumerate(_ordered_funds(rows), start=1):
        lines.append(f"{index}. {fund}")
    lines.extend(["", "## Fund Worksheets", ""])

    for fund in _ordered_funds(rows):
        fund_rows = [row for row in rows if row.fund == fund]
        coverage = coverage_by_fund.get(fund)
        target_total = sum((row.fund_target_rolled_exposure or 0.0) for row in fund_rows)
        benchmark_total = sum((row.fund_benchmark_rolled_exposure or 0.0) for row in fund_rows)
        vir_matched = sum(1 for row in fund_rows if row.vir_join_status == "matched_to_vir")
        algo_matched = sum(1 for row in fund_rows if row.algo_join_status == "matched_to_algo")

        lines.extend(
            [
                f"## {fund}",
                "",
                "### Snapshot",
                "",
                f"- ACID rows: {len(fund_rows)}",
                f"- Target match pct: {_fmt_pct(coverage.target_match_pct if coverage else None)}",
                f"- Benchmark match pct: {_fmt_pct(coverage.benchmark_match_pct if coverage else None)}",
                f"- VIR matched rows: {vir_matched}",
                f"- Algo matched rows: {algo_matched}",
                f"- Summed target rolled exposure: {_fmt(target_total)}",
                f"- Summed benchmark rolled exposure: {_fmt(benchmark_total)}",
                f"- Benchmark expected status: {_benchmark_status(coverage)}",
                "",
                "### What To Check",
                "",
                "- Coverage OK?",
                "- Top 3 suspicious ACIDs?",
                "- Missing VIR rows that should have matched?",
                "- Missing algo rows that should have matched?",
                "- Benchmark issue or expected?",
                "- Need parser fix, join fix, or business-rule decision?",
                "",
                "### Largest Active Overweights",
                "",
            ]
        )
        _append_ranked_table(
            lines,
            _top_rows(fund_rows, lambda row: row.active_rolled_exposure, positive_only=True),
        )
        lines.extend(["### Largest Active Underweights", ""])
        _append_ranked_table(
            lines,
            _top_rows(fund_rows, lambda row: row.active_rolled_exposure, negative_only=True),
        )
        lines.extend(["### Largest Missing VIR Candidates", ""])
        _append_ranked_table(
            lines,
            _top_rows(
                [row for row in fund_rows if row.vir_join_status != "matched_to_vir"],
                lambda row: abs(row.active_rolled_exposure or 0.0),
            ),
        )
        lines.extend(["### Largest Missing Algo Candidates", ""])
        _append_ranked_table(
            lines,
            _top_rows(
                [row for row in fund_rows if row.algo_join_status != "matched_to_algo"],
                lambda row: abs(row.active_rolled_exposure or 0.0),
            ),
        )
        lines.extend(
            [
                "### Notes",
                "",
                "- Coverage:",
                "- Suspicious ACIDs:",
                "- VIR notes:",
                "- Algo notes:",
                "- Benchmark notes:",
                "- Lineage rows to inspect in `fund_rolled_exposure_detail.csv`:",
                "- Action needed:",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_fund_review_workbook_markdown(
    rows: list[FundCombinedReviewRow],
    coverage_by_fund: dict[str, FundCoverageRow],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_fund_review_workbook_markdown(rows, coverage_by_fund),
        encoding="utf-8",
    )
    return output_path


def build_fund_review_pack(
    combined_csv: str | Path,
    coverage_csv: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    rows = load_fund_review_rows(combined_csv)
    coverage_by_fund = load_fund_coverage_rows(coverage_csv)
    checklist_rows = build_fund_review_checklist_rows(rows, coverage_by_fund)

    output_dir = Path(output_dir)
    checklist_path = write_fund_review_checklist_csv(
        checklist_rows,
        output_dir / "fund_review_checklist.csv",
    )
    workbook_path = write_fund_review_workbook_markdown(
        rows,
        coverage_by_fund,
        output_dir / "fund_review_workbook.md",
    )

    return {
        "checklist_csv": checklist_path,
        "workbook_md": workbook_path,
    }


def _append_ranked_table(lines: list[str], rows: list[FundCombinedReviewRow], limit: int = 10) -> None:
    if not rows:
        lines.extend(["No rows available.", ""])
        return

    header = ["ACID", "Type", "Target", "Bench", "Active", "VIR", "Algo", "Sec Ct", "Sample Securities"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")

    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.acid,
                    row.acid_type,
                    _fmt(row.fund_target_rolled_exposure),
                    _fmt(row.fund_benchmark_rolled_exposure),
                    _fmt(row.active_rolled_exposure),
                    _fmt(row.vir_stf),
                    _fmt(row.algo_active_weight),
                    str(row.source_security_count or ""),
                    _shorten(row.sample_source_securities),
                ]
            )
            + " |"
        )

    lines.append("")


def _ordered_funds(rows: list[FundCombinedReviewRow]) -> list[str]:
    seen = {row.fund for row in rows}
    ordered = [fund for fund in DEFAULT_FUND_ORDER if fund in seen]
    remainder = sorted(seen - set(ordered))
    return ordered + remainder


def _top_rows(
    rows: list[FundCombinedReviewRow],
    metric,
    *,
    positive_only: bool = False,
    negative_only: bool = False,
) -> list[FundCombinedReviewRow]:
    available = [row for row in rows if metric(row) is not None]
    if positive_only:
        available = [row for row in available if (metric(row) or 0.0) > 0]
        return sorted(available, key=lambda row: metric(row) or 0.0, reverse=True)
    if negative_only:
        available = [row for row in available if (metric(row) or 0.0) < 0]
        return sorted(available, key=lambda row: metric(row) or 0.0)
    return sorted(available, key=lambda row: metric(row) or 0.0, reverse=True)


def _benchmark_status(coverage: FundCoverageRow | None) -> str:
    if coverage is None:
        return "unknown"
    if (coverage.total_benchmark_weight or 0.0) == 0.0:
        return "no_benchmark_weight_in_workbook"
    if coverage.benchmark_match_pct == 1.0:
        return "benchmarked_and_fully_matched"
    return "benchmark_present_with_partial_match"


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.1%}"


def _latest_snapshot_date(rows: list[FundCombinedReviewRow]) -> str:
    if not rows:
        return ""
    return max(row.snapshot_date for row in rows)


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
    "FundCombinedReviewRow",
    "FundCoverageRow",
    "build_fund_review_checklist_rows",
    "build_fund_review_pack",
    "build_fund_review_workbook_markdown",
    "load_fund_coverage_rows",
    "load_fund_review_rows",
    "write_fund_review_checklist_csv",
    "write_fund_review_workbook_markdown",
]
