"""Build one fund-level table that combines rolled weights, VIR, and algo signals.

DEPRECATED single-signal path. It keys the latest-algo join by `acid` only, so it
overwrites same-ACID rows across algo perspectives (audit M2). Use the multisignal
path (`fund_weights_vir_algo_multisignal`) instead, which preserves one row per
perspective. Retained only for backward compatibility; do not build new work on it.
"""

from __future__ import annotations

from pathlib import Path
import warnings

from .rolled_exposures import build_rolled_exposures
from .rolled_exposure_alignment import (
    FundExposureAlignmentRow,
    build_fund_exposure_alignment,
    write_alignment_csv,
)


def build_fund_weights_vir_algo(
    workbook_path: str | Path,
    output_dir: str | Path,
    vir_csv: str | Path | None = None,
    algo_workbooks: list[str | Path] | None = None,
    combined_output: str | Path | None = None,
) -> dict[str, Path]:
    """Build rolled exposures, align them, and write one fund-level combined CSV."""

    warnings.warn(
        "build_fund_weights_vir_algo is deprecated (single-signal path collapses algo "
        "perspectives per ACID; audit M2). Use build_fund_weights_vir_algo_multisignal.",
        DeprecationWarning,
        stacklevel=2,
    )

    output_dir = Path(output_dir)
    rolled_outputs = build_rolled_exposures(workbook_path, output_dir)

    fund_rows = build_fund_exposure_alignment(
        fund_summary_csv=rolled_outputs["fund_summary"],
        vir_csv=vir_csv,
        algo_workbooks=algo_workbooks,
    )

    combined_path = Path(combined_output) if combined_output else output_dir / "fund_weights_vir_algo.csv"
    alignment_path = write_alignment_csv(fund_rows, combined_path)

    return {
        "fund_summary": rolled_outputs["fund_summary"],
        "fund_weights_vir_algo": alignment_path,
    }


__all__ = [
    "FundExposureAlignmentRow",
    "build_fund_weights_vir_algo",
]
