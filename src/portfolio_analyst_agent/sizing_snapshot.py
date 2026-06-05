"""Build PM-facing monthly sizing artifacts from normalized algo rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import csv
from pathlib import Path

from .algo_parser import AlgoParseResult
from .signal_aliases import augment_algo_signals


@dataclass(frozen=True)
class AlgoLatestSignal:
    """Latest-period algo signal collapsed to one row per ACID."""

    snapshot_date: date
    algo_perspective: str
    sheet_dimension: str
    acid: str
    absolute_weight: float | None
    active_weight: float | None
    benchmark_weight: float | None
    absolute_weight_mom: float | None
    active_weight_mom: float | None


@dataclass(frozen=True)
class SnapshotSection:
    title: str
    rows: list[AlgoLatestSignal]


@dataclass(frozen=True)
class DimensionSnapshot:
    algo_perspective: str
    sheet_dimension: str
    snapshot_date: date
    sections: list[SnapshotSection]


@dataclass(frozen=True)
class SizingSnapshot:
    snapshot_date: date
    dimensions: list[DimensionSnapshot]


def latest_signals_from_results(results: list[AlgoParseResult]) -> list[AlgoLatestSignal]:
    """Collapse normalized algo rows to the latest month-end signal set."""

    latest_signals: list[AlgoLatestSignal] = []
    metric_names = {
        "absolute_weight",
        "active_weight",
        "benchmark_weight",
        "absolute_weight_mom",
        "active_weight_mom",
    }

    for result in results:
        latest_records = [record for record in result.records if record.period_end == result.snapshot_date]
        grouped: dict[tuple[str, str, str], dict[str, float | None]] = {}

        for record in latest_records:
            if record.metric_type not in metric_names:
                continue

            key = (record.algo_perspective, record.sheet_dimension, record.acid)
            grouped.setdefault(
                key,
                {
                    "absolute_weight": None,
                    "active_weight": None,
                    "benchmark_weight": None,
                    "absolute_weight_mom": None,
                    "active_weight_mom": None,
                },
            )
            grouped[key][record.metric_type] = record.value

        for (algo_perspective, sheet_dimension, acid), metrics in sorted(grouped.items()):
            latest_signals.append(
                AlgoLatestSignal(
                    snapshot_date=result.snapshot_date,
                    algo_perspective=algo_perspective,
                    sheet_dimension=sheet_dimension,
                    acid=acid,
                    absolute_weight=metrics["absolute_weight"],
                    active_weight=metrics["active_weight"],
                    benchmark_weight=metrics["benchmark_weight"],
                    absolute_weight_mom=metrics["absolute_weight_mom"],
                    active_weight_mom=metrics["active_weight_mom"],
                )
            )

    return augment_algo_signals(latest_signals)


def build_sizing_snapshot(signals: list[AlgoLatestSignal], top_n: int = 10) -> SizingSnapshot:
    """Build a PM-readable sizing snapshot from latest algo signals."""

    if not signals:
        raise ValueError("Cannot build a sizing snapshot with no algo signals.")

    grouped: dict[tuple[str, str], list[AlgoLatestSignal]] = {}
    snapshot_date = max(signal.snapshot_date for signal in signals)
    for signal in signals:
        grouped.setdefault((signal.algo_perspective, signal.sheet_dimension), []).append(signal)

    dimensions: list[DimensionSnapshot] = []
    for (algo_perspective, sheet_dimension), dimension_signals in sorted(grouped.items()):
        sections = [
            SnapshotSection(
                title="Largest Absolute Weights",
                rows=_top_by_metric(dimension_signals, "absolute_weight", top_n, reverse=True),
            ),
            SnapshotSection(
                title="Top Active Overweights",
                rows=_top_positive(dimension_signals, "active_weight", top_n),
            ),
            SnapshotSection(
                title="Top Active Underweights",
                rows=_top_negative(dimension_signals, "active_weight", top_n),
            ),
            SnapshotSection(
                title="Largest Absolute Weight Increases",
                rows=_top_positive(dimension_signals, "absolute_weight_mom", top_n),
            ),
            SnapshotSection(
                title="Largest Absolute Weight Decreases",
                rows=_top_negative(dimension_signals, "absolute_weight_mom", top_n),
            ),
            SnapshotSection(
                title="Largest Active Weight Increases",
                rows=_top_positive(dimension_signals, "active_weight_mom", top_n),
            ),
            SnapshotSection(
                title="Largest Active Weight Decreases",
                rows=_top_negative(dimension_signals, "active_weight_mom", top_n),
            ),
        ]
        dimensions.append(
            DimensionSnapshot(
                algo_perspective=algo_perspective,
                sheet_dimension=sheet_dimension,
                snapshot_date=snapshot_date,
                sections=sections,
            )
        )

    return SizingSnapshot(snapshot_date=snapshot_date, dimensions=dimensions)


def render_sizing_snapshot_markdown(snapshot: SizingSnapshot) -> str:
    lines: list[str] = [
        "# Sizing Considerations Snapshot",
        "",
        f"Snapshot date: {snapshot.snapshot_date.isoformat()}",
        "",
        "This artifact summarizes the latest algo-implied sizing signals by perspective and dimension.",
        "",
    ]

    for dimension in snapshot.dimensions:
        perspective = dimension.algo_perspective.replace("_", " ").title()
        sheet_dimension = dimension.sheet_dimension.replace("_", " ").title()
        lines.extend(
            [
                f"## {perspective} - {sheet_dimension}",
                "",
            ]
        )

        for section in dimension.sections:
            lines.extend([f"### {section.title}", ""])
            if not section.rows:
                lines.append("No rows available.")
                lines.append("")
                continue

            lines.append("| ACID | Abs Wt | Active Wt | Bench Wt | Abs MoM | Active MoM |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for signal in section.rows:
                lines.append(
                    "| {acid} | {absolute_weight} | {active_weight} | {benchmark_weight} | {absolute_weight_mom} | {active_weight_mom} |".format(
                        acid=signal.acid,
                        absolute_weight=_fmt(signal.absolute_weight),
                        active_weight=_fmt(signal.active_weight),
                        benchmark_weight=_fmt(signal.benchmark_weight),
                        absolute_weight_mom=_fmt(signal.absolute_weight_mom),
                        active_weight_mom=_fmt(signal.active_weight_mom),
                    )
                )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_latest_signals_csv(signals: list[AlgoLatestSignal], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(asdict(signals[0]).keys()))
        writer.writeheader()
        for signal in signals:
            row = asdict(signal)
            row["snapshot_date"] = row["snapshot_date"].isoformat()
            writer.writerow(row)

    return output_path


def write_snapshot_markdown(snapshot: SizingSnapshot, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_sizing_snapshot_markdown(snapshot), encoding="utf-8")
    return output_path


def _metric_value(signal: AlgoLatestSignal, metric_name: str) -> float | None:
    return getattr(signal, metric_name)


def _top_by_metric(
    signals: list[AlgoLatestSignal],
    metric_name: str,
    top_n: int,
    reverse: bool,
) -> list[AlgoLatestSignal]:
    available = [signal for signal in signals if _metric_value(signal, metric_name) is not None]
    return sorted(available, key=lambda signal: _metric_value(signal, metric_name) or 0.0, reverse=reverse)[:top_n]


def _top_positive(signals: list[AlgoLatestSignal], metric_name: str, top_n: int) -> list[AlgoLatestSignal]:
    available = [
        signal
        for signal in signals
        if _metric_value(signal, metric_name) is not None and (_metric_value(signal, metric_name) or 0.0) > 0
    ]
    return sorted(available, key=lambda signal: _metric_value(signal, metric_name) or 0.0, reverse=True)[:top_n]


def _top_negative(signals: list[AlgoLatestSignal], metric_name: str, top_n: int) -> list[AlgoLatestSignal]:
    available = [
        signal
        for signal in signals
        if _metric_value(signal, metric_name) is not None and (_metric_value(signal, metric_name) or 0.0) < 0
    ]
    return sorted(available, key=lambda signal: _metric_value(signal, metric_name) or 0.0)[:top_n]


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


__all__ = [
    "AlgoLatestSignal",
    "SizingSnapshot",
    "build_sizing_snapshot",
    "latest_signals_from_results",
    "render_sizing_snapshot_markdown",
    "write_latest_signals_csv",
    "write_snapshot_markdown",
]
