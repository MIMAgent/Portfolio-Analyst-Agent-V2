"""Build a lightweight frontend JSON for 12-month VIR and algo history."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.algo_parser import parse_algo_workbook  # noqa: E402
from portfolio_analyst_agent.csv_sources import open_csv_text  # noqa: E402


FRONTEND_DATA_DIR = ROOT / "frontend" / "Example_frontendV1" / "src" / "data"
DEFAULT_ALIGNMENT_JSON = FRONTEND_DATA_DIR / "fundWeightsVirAlgo.json"
DEFAULT_OUTPUT = FRONTEND_DATA_DIR / "signalHistory.json"
DEFAULT_ALGO_WORKBOOK = ROOT / "data" / "2026-05-31" / "Algo LR (3).xlsx"
DEFAULT_VIR_HISTORY = ROOT / "artifacts" / "equity_vir_history.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a 12-month frontend signal history JSON.")
    parser.add_argument("--alignment-json", default=str(DEFAULT_ALIGNMENT_JSON))
    parser.add_argument("--algo-workbook", default=str(DEFAULT_ALGO_WORKBOOK))
    parser.add_argument("--vir-history", default=str(DEFAULT_VIR_HISTORY))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    alignment_rows = json.loads(Path(args.alignment_json).read_text(encoding="utf-8"))
    fund_acids = _build_fund_acids(alignment_rows)
    target_acids = {acid for acids in fund_acids.values() for acid in acids}

    algo_series, chart_dates = _load_algo_history(Path(args.algo_workbook), target_acids)
    vir_series = _load_vir_history(Path(args.vir_history), target_acids, chart_dates)

    payload = {
        "dateRange": {
            "start": chart_dates[0] if chart_dates else "",
            "end": chart_dates[-1] if chart_dates else "",
        },
        "dates": chart_dates,
        "funds": {},
    }

    for fund, acids in sorted(fund_acids.items()):
        acid_payload = {}
        for acid in sorted(acids):
            points = []
            algo_points = algo_series.get(acid, {})
            vir_points = vir_series.get(acid, {})
            for snapshot_date in chart_dates:
                points.append(
                    {
                        "date": snapshot_date,
                        "algo_active_weight": algo_points.get(snapshot_date),
                        "vir_stf": vir_points.get(snapshot_date),
                    }
                )

            acid_payload[acid] = {
                "series": points,
                "coverage": {
                    "algo_points": sum(1 for item in points if item["algo_active_weight"] is not None),
                    "vir_points": sum(1 for item in points if item["vir_stf"] is not None),
                    "algo_latest_date": _latest_non_null_date(points, "algo_active_weight"),
                    "vir_latest_date": _latest_non_null_date(points, "vir_stf"),
                },
            }

        payload["funds"][fund] = {"acids": acid_payload}

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"fund_count={len(payload['funds'])}")
    print(f"acid_count={len(target_acids)}")
    print(f"chart_start={payload['dateRange']['start']}")
    print(f"chart_end={payload['dateRange']['end']}")
    print(f"output={output_path}")
    return 0


def _build_fund_acids(rows: list[dict[str, object]]) -> dict[str, set[str]]:
    funds: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        fund = str(row.get("fund", "")).strip()
        acid = str(row.get("acid", "")).strip()
        if not fund or not acid:
            continue
        funds[fund].add(acid)
    return funds


def _load_algo_history(workbook_path: Path, target_acids: set[str]) -> tuple[dict[str, dict[str, float | None]], list[str]]:
    result = parse_algo_workbook(workbook_path)
    active_rows = [row for row in result.records if row.metric_type == "active_weight" and row.acid in target_acids]
    all_dates = sorted({row.period_end for row in active_rows})
    window_dates = all_dates[-12:]
    window_lookup = {item.isoformat() for item in window_dates}

    series: dict[str, dict[str, float | None]] = defaultdict(dict)
    for row in active_rows:
        snapshot_date = row.period_end.isoformat()
        if snapshot_date not in window_lookup:
            continue
        series[row.acid][snapshot_date] = row.value

    return series, [item.isoformat() for item in window_dates]


def _load_vir_history(
    source_path: Path,
    target_acids: set[str],
    chart_dates: list[str],
) -> dict[str, dict[str, float | None]]:
    target_dates = set(chart_dates)
    series: dict[str, dict[str, float | None]] = defaultdict(dict)

    with open_csv_text(source_path) as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            acid = (row.get("acid") or "").strip()
            snapshot_date = (row.get("snapshot_date") or "").strip()
            if acid not in target_acids or snapshot_date not in target_dates:
                continue
            if snapshot_date < "2000-01-01":
                continue
            series[acid][snapshot_date] = _to_float(row.get("stf"))

    return series


def _latest_non_null_date(points: list[dict[str, object]], field_name: str) -> str:
    for item in reversed(points):
        if item.get(field_name) is not None:
            return str(item["date"])
    return ""


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
