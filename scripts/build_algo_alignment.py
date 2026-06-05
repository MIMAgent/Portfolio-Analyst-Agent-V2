"""Join the latest algo signals to normalized VIR and holdings CSV inputs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.algo_parser import parse_multiple_algo_workbooks  # noqa: E402
from portfolio_analyst_agent.alignment import (  # noqa: E402
    join_algo_to_holdings,
    join_algo_to_vir,
    load_holdings_rows_from_csv,
    load_vir_rows_from_csv,
)
from portfolio_analyst_agent.sizing_snapshot import latest_signals_from_results  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build algo alignment outputs against VIR and holdings CSVs.")
    parser.add_argument("workbooks", nargs="+", help="Path(s) to algo workbook files.")
    parser.add_argument(
        "--vir-csv",
        help="Normalized VIR CSV path. When provided, writes an algo-to-VIR alignment CSV.",
    )
    parser.add_argument(
        "--holdings-csv",
        help="Normalized holdings CSV path. When provided, writes an algo-to-holdings alignment CSV.",
    )
    parser.add_argument(
        "--algo-vir-output",
        default="artifacts/algo_vir_alignment.csv",
        help="CSV output path for algo-to-VIR alignment rows.",
    )
    parser.add_argument(
        "--algo-holdings-output",
        default="artifacts/algo_holdings_alignment.csv",
        help="CSV output path for algo-to-holdings alignment rows.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.vir_csv and not args.holdings_csv:
        parser.error("Provide at least one of --vir-csv or --holdings-csv.")

    latest_signals = latest_signals_from_results(parse_multiple_algo_workbooks(args.workbooks))
    print(f"latest_signal_count={len(latest_signals)}")

    if args.vir_csv:
        vir_rows = load_vir_rows_from_csv(args.vir_csv)
        joined_vir = join_algo_to_vir(latest_signals, vir_rows)
        output_path = write_dataclass_csv(joined_vir, args.algo_vir_output)
        print(f"algo_vir_alignment_count={len(joined_vir)}")
        print(f"algo_vir_alignment_csv={output_path}")

    if args.holdings_csv:
        holdings_rows = load_holdings_rows_from_csv(args.holdings_csv)
        joined_holdings = join_algo_to_holdings(latest_signals, holdings_rows)
        output_path = write_dataclass_csv(joined_holdings, args.algo_holdings_output)
        print(f"algo_holdings_alignment_count={len(joined_holdings)}")
        print(f"algo_holdings_alignment_csv={output_path}")

    return 0


def write_dataclass_csv(rows: list[object], output_path: str | Path) -> Path:
    if not rows:
        raise ValueError("Cannot write an empty CSV with no dataclass rows.")
    if not is_dataclass(rows[0]):
        raise TypeError("Expected dataclass instances.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    first_row = normalize_row(asdict(rows[0]))
    fieldnames = list(first_row.keys())

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(first_row)
        for row in rows[1:]:
            writer.writerow(normalize_row(asdict(row)))

    return output_path


def normalize_row(row: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, date):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
