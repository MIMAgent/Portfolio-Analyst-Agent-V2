"""Build one fund-level table that preserves both algo perspectives per eligible ACID."""

from __future__ import annotations

from pathlib import Path

from .rolled_exposures import build_rolled_exposures
from .rolled_exposure_alignment_multisignal import (
    FundExposureAlignmentRow,
    build_fund_exposure_alignment,
    write_alignment_csv,
)


def build_fund_weights_vir_algo_multisignal(
    workbook_path: str | Path,
    output_dir: str | Path,
    vir_csv: str | Path | None = None,
    algo_workbooks: list[str | Path] | None = None,
    combined_output: str | Path | None = None,
) -> dict[str, Path]:
    """Build rolled exposures, align them, and write one fund-level combined CSV."""

    output_dir = Path(output_dir)
    rolled_outputs = build_rolled_exposures(workbook_path, output_dir)

    fund_rows = build_fund_exposure_alignment(
        fund_summary_csv=rolled_outputs["fund_summary"],
        vir_csv=vir_csv,
        algo_workbooks=algo_workbooks,
    )

    combined_path = (
        Path(combined_output)
        if combined_output
        else output_dir / "fund_weights_vir_algo_multisignal.csv"
    )
    alignment_path = write_alignment_csv(fund_rows, combined_path)

    return {
        "fund_summary": rolled_outputs["fund_summary"],
        "fund_weights_vir_algo_multisignal": alignment_path,
    }


__all__ = [
    "FundExposureAlignmentRow",
    "build_fund_weights_vir_algo_multisignal",
]
