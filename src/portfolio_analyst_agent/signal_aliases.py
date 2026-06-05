"""Helpers for aliasing and deriving ACID-level VIR and algo signals."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .alignment import VirRow
    from .sizing_snapshot import AlgoLatestSignal


VIR_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "EM EQ": ("EM Comp EQ",),
    "AU RE EQ": ("AU EQ",),
}


ALGO_DIRECT_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "US RE EQ": ("US REIT",),
    "AU RE EQ": ("AU REIT",),
    "EM RE EQ": ("EM REIT",),
    "EU RE EQ": ("EU REIT",),
    "JP CD EQ": ("JP EQ",),
    "JP CS EQ": ("JP EQ",),
    "JP EN EQ": ("JP EQ",),
    "JP FN EQ": ("JP EQ",),
    "JP HC EQ": ("JP EQ",),
    "JP ID EQ": ("JP EQ",),
    "JP IT EQ": ("JP EQ",),
    "JP MT EQ": ("JP EQ",),
    "JP RE EQ": ("JP EQ",),
    "JP TL EQ": ("JP EQ",),
}


ALGO_COMPOSITE_MAP: dict[str, tuple[str, ...]] = {
    "US MID EQ": ("US MID G EQ", "US MID V EQ"),
    "US SML EQ": ("US SML G EQ", "US SML V EQ"),
    "US LRG EQ": ("US LRG G EQ", "US LRG V EQ"),
}


def build_vir_index(vir_rows: list[VirRow]) -> dict[str, VirRow]:
    indexed: dict[str, VirRow] = {}
    for row in sorted(vir_rows, key=lambda item: (item.acid, item.snapshot_date)):
        indexed[row.acid] = row

    for alias_acid, source_acids in VIR_ALIAS_MAP.items():
        existing_row = indexed.get(alias_acid)
        if existing_row is not None and _vir_row_has_signal(existing_row):
            continue
        for source_acid in source_acids:
            source_row = indexed.get(source_acid)
            if source_row is not None and _vir_row_has_signal(source_row):
                indexed[alias_acid] = replace(source_row, acid=alias_acid)
                break

    return indexed


def augment_algo_signals(signals: list[AlgoLatestSignal]) -> list[AlgoLatestSignal]:
    indexed: dict[tuple[str, str, str], AlgoLatestSignal] = {}
    for signal in sorted(signals, key=lambda item: (item.acid, item.sheet_dimension, item.algo_perspective)):
        indexed[(signal.acid, signal.sheet_dimension, signal.algo_perspective)] = signal

    _add_direct_alias_signals(indexed)
    _add_composite_signals(indexed)

    return sorted(
        indexed.values(),
        key=lambda item: (item.algo_perspective, item.sheet_dimension, item.acid, item.snapshot_date),
    )


def _add_direct_alias_signals(indexed: dict[tuple[str, str, str], AlgoLatestSignal]) -> None:
    additions: list[AlgoLatestSignal] = []
    for (acid, sheet_dimension, algo_perspective), signal in list(indexed.items()):
        for alias_acid, source_acids in ALGO_DIRECT_ALIAS_MAP.items():
            if acid not in source_acids:
                continue
            alias_key = (alias_acid, sheet_dimension, algo_perspective)
            if alias_key in indexed:
                continue
            additions.append(replace(signal, acid=alias_acid))

    for signal in additions:
        indexed[(signal.acid, signal.sheet_dimension, signal.algo_perspective)] = signal


def _add_composite_signals(indexed: dict[tuple[str, str, str], AlgoLatestSignal]) -> None:
    by_context: dict[tuple[str, str], dict[str, AlgoLatestSignal]] = {}
    for signal in indexed.values():
        by_context.setdefault((signal.algo_perspective, signal.sheet_dimension), {})[signal.acid] = signal

    additions: list[AlgoLatestSignal] = []
    for (algo_perspective, sheet_dimension), signals_for_context in by_context.items():
        for composite_acid, component_acids in ALGO_COMPOSITE_MAP.items():
            composite_key = (composite_acid, sheet_dimension, algo_perspective)
            if composite_key in indexed:
                continue

            components = [signals_for_context.get(component_acid) for component_acid in component_acids]
            if any(component is None for component in components):
                continue

            first = components[0]
            additions.append(
                first.__class__(
                    snapshot_date=first.snapshot_date,
                    algo_perspective=algo_perspective,
                    sheet_dimension=sheet_dimension,
                    acid=composite_acid,
                    absolute_weight=_sum_metric(components, "absolute_weight"),
                    active_weight=_sum_metric(components, "active_weight"),
                    benchmark_weight=_sum_metric(components, "benchmark_weight"),
                    absolute_weight_mom=_sum_metric(components, "absolute_weight_mom"),
                    active_weight_mom=_sum_metric(components, "active_weight_mom"),
                )
            )

    for signal in additions:
        indexed[(signal.acid, signal.sheet_dimension, signal.algo_perspective)] = signal


def _sum_metric(signals: list[AlgoLatestSignal | None], attribute: str) -> float | None:
    values = [getattr(signal, attribute) for signal in signals if signal is not None]
    present_values = [value for value in values if value is not None]
    if not present_values:
        return None
    return sum(present_values)


def _vir_row_has_signal(row: VirRow) -> bool:
    return any(
        value is not None
        for value in (
            row.stf,
            row.delta_stf,
            row.rank_in_category_by_stf,
            row.rank_change_by_stf,
        )
    )


__all__ = [
    "augment_algo_signals",
    "build_vir_index",
]
