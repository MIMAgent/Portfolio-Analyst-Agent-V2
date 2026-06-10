"""Build a frontend-friendly bundle from the tracked monthly review artifacts."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MONTHLY_REVIEW_ROOT = ROOT / "artifacts" / "monthly_review"
FRONTEND_DATA_DIR = ROOT / "frontend" / "Example_frontendV1" / "src" / "data"
DEFAULT_OUTPUT = FRONTEND_DATA_DIR / "monthlyReviewBundle.json"
DEFAULT_ALIGNMENT_OUTPUT = FRONTEND_DATA_DIR / "fundWeightsVirAlgo.json"
DEFAULT_LINEAGE_OUTPUT = FRONTEND_DATA_DIR / "exposureLineage.json"
DEFAULT_ALIGNMENT_CSV = ROOT / "artifacts" / "rolled_exposures" / "fund_weights_vir_algo_multisignal.csv"
DEFAULT_LINEAGE_CSV = ROOT / "artifacts" / "rolled_exposures" / "fund_rolled_exposure_detail.csv"


def build_bundle(snapshot_date: str | None = None) -> dict[str, Any]:
    snapshot_dir = _resolve_snapshot_dir(snapshot_date)
    funds, as_of_date = _load_snapshot_funds(snapshot_dir)

    return {
        "bundle_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "snapshot_date": snapshot_dir.name,
        "as_of_date": as_of_date,
        "fund_count": len(funds),
        "funds": funds,
    }


def _resolve_snapshot_dir(snapshot_date: str | None) -> Path:
    if snapshot_date:
        snapshot_dir = MONTHLY_REVIEW_ROOT / snapshot_date
        if not snapshot_dir.exists():
            raise FileNotFoundError(f"Monthly review snapshot not found: {snapshot_dir}")
        return snapshot_dir

    candidates = sorted(path for path in MONTHLY_REVIEW_ROOT.iterdir() if path.is_dir())
    if not candidates:
        raise FileNotFoundError(f"No monthly review snapshots found in {MONTHLY_REVIEW_ROOT}")
    return candidates[-1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_snapshot_funds(snapshot_dir: Path) -> tuple[list[dict[str, Any]], str]:
    batch_index_path = snapshot_dir / "batch_index.json"
    if batch_index_path.exists():
        batch_index = _load_json(batch_index_path)
        funds = []
        for result in batch_index["results"]:
            output_dir = ROOT / result["output_dir"]
            run_payload = _load_json(output_dir / "run_payload.json")
            run_summary_markdown = (output_dir / "run_summary.md").read_text(encoding="utf-8")
            detailed_review = _load_detailed_review_assets(output_dir)
            funds.append(
                {
                    "slug": output_dir.name,
                    "fund": result["fund"],
                    "snapshot_date": result["snapshot_date"],
                    "review_run_id": result["review_run_id"],
                    "run_summary_markdown": run_summary_markdown,
                    **detailed_review,
                    "run_payload": run_payload,
                    "index_entry": result,
                }
            )
        return funds, batch_index["as_of_date"]

    fund_dirs = sorted(path for path in snapshot_dir.iterdir() if path.is_dir())
    funds = [_build_single_run_fund_entry(path, snapshot_dir.name) for path in fund_dirs if _looks_like_single_run_dir(path)]
    if not funds:
        raise FileNotFoundError(f"No monthly review runs found in {snapshot_dir}")
    as_of_date = next(
        (
            entry.get("run_payload", {})
            .get("review_run_metadata", {})
            .get("as_of_date", "")
            for entry in funds
            if entry.get("run_payload", {}).get("review_run_metadata", {}).get("as_of_date", "")
        ),
        snapshot_dir.name,
    )
    return funds, as_of_date


def _looks_like_single_run_dir(path: Path) -> bool:
    return (path / "change_brief.json").exists() or (path / "pm_review.md").exists()


def _build_single_run_fund_entry(run_dir: Path, snapshot_date: str) -> dict[str, Any]:
    change_brief = _read_optional_json(run_dir / "change_brief.json")
    sizing = _read_optional_json(run_dir / "sizing_considerations.json")
    challenge = _read_optional_json(run_dir / "challenge_brief.json")
    metadata = dict(change_brief.get("header", {}))
    fund = metadata.get("fund", run_dir.name)
    detailed_review = _load_detailed_review_assets(run_dir)
    run_summary_markdown = _read_optional_text(run_dir / "pm_review.md") or _fallback_summary_markdown(
        fund=fund,
        snapshot_date=metadata.get("snapshot_date", snapshot_date),
        as_of_date=metadata.get("as_of_date", snapshot_date),
        review_run_id=metadata.get("review_run_id", ""),
        run_mode=metadata.get("run_mode", "ad_hoc"),
        available_files=[path.name for path in sorted(run_dir.iterdir()) if path.is_file()],
    )
    run_payload = {
        "review_run_metadata": metadata,
        "fund_snapshot_summary": {
            "coverage": {},
            "memory_summary": {},
            "trigger_summary": {},
        },
        "change_brief": change_brief,
        "sizing_considerations": sizing,
        "challenge_brief": challenge,
    }
    return {
        "slug": run_dir.name,
        "fund": fund,
        "snapshot_date": metadata.get("snapshot_date", snapshot_date),
        "review_run_id": metadata.get("review_run_id", ""),
        "run_summary_markdown": run_summary_markdown,
        **detailed_review,
        "run_payload": run_payload,
        "index_entry": {
            "fund": fund,
            "snapshot_date": metadata.get("snapshot_date", snapshot_date),
            "review_run_id": metadata.get("review_run_id", ""),
            "output_dir": run_dir.relative_to(ROOT).as_posix(),
        },
    }


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_detailed_review_assets(run_dir: Path) -> dict[str, Any]:
    artifact_paths = {
        "pm_review_markdown": _repo_relative(run_dir / "pm_review.md"),
        "pm_review_html": _repo_relative(run_dir / "pm_review.html"),
        "change_brief_json": _repo_relative(run_dir / "change_brief.json"),
        "change_brief_markdown": _repo_relative(run_dir / "change_brief.md"),
        "sizing_considerations_json": _repo_relative(run_dir / "sizing_considerations.json"),
        "sizing_considerations_markdown": _repo_relative(run_dir / "sizing_considerations.md"),
        "challenge_brief_json": _repo_relative(run_dir / "challenge_brief.json"),
        "challenge_brief_markdown": _repo_relative(run_dir / "challenge_brief.md"),
        "agent_trace_json": _repo_relative(run_dir / "agent_trace.json"),
    }
    return {
        "detailed_review_markdown": _read_optional_text(run_dir / "pm_review.md"),
        "detailed_review_html": _read_optional_text(run_dir / "pm_review.html"),
        "artifact_paths": artifact_paths,
    }


def _repo_relative(path: Path) -> str:
    if not path.exists():
        return ""
    return path.relative_to(ROOT).as_posix()


def _fallback_summary_markdown(
    *,
    fund: str,
    snapshot_date: str,
    as_of_date: str,
    review_run_id: str,
    run_mode: str,
    available_files: list[str],
) -> str:
    lines = [
        f"# Monthly Review Run - {fund}",
        "",
        f"- Snapshot date: {snapshot_date}",
        f"- As-of date: {as_of_date}",
        f"- Review run id: {review_run_id or 'N/A'}",
        f"- Run mode: {run_mode or 'ad_hoc'}",
        "",
        "## Output Files",
        "",
    ]
    for name in available_files:
        lines.append(f"- `{name}`")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_json_array(path: Path, payload: list[dict[str, Any]] | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_structured_frontend_data() -> tuple[list[dict[str, str]], dict[str, Any]]:
    alignment_rows = _load_csv_rows(DEFAULT_ALIGNMENT_CSV)
    lineage_rows = _load_csv_rows(DEFAULT_LINEAGE_CSV)
    return alignment_rows, _build_exposure_lineage(lineage_rows)


def _build_exposure_lineage(rows: list[dict[str, str]]) -> dict[str, Any]:
    funds: dict[str, dict[str, Any]] = {}
    for row in rows:
        fund = row.get("fund", "").strip()
        acid = row.get("acid", "").strip()
        if not fund or not acid:
            continue

        fund_bucket = funds.setdefault(fund, {})
        acid_bucket = fund_bucket.setdefault(
            acid,
            {
                "securityCount": 0,
                "totalActiveContribution": 0.0,
                "_security_map": {},
                "_path_map": {},
            },
        )

        security_name = row.get("security_name", "").strip() or row.get("common_identifier", "").strip() or "Unknown"
        identifier = row.get("common_identifier", "").strip() or security_name
        path_label = row.get("h_path", "").strip() or row.get("asset_class_broad", "").strip()
        source_name = row.get("account_name", "").strip() or security_name
        portcode = row.get("portcode", "").strip()
        target = _float(row.get("fund_target_security_contribution"))
        benchmark = _float(row.get("fund_benchmark_security_contribution"))
        active = target - benchmark

        acid_bucket["totalActiveContribution"] += active

        security_bucket = acid_bucket["_security_map"].setdefault(
            identifier,
            {
                "securityName": security_name,
                "identifier": identifier,
                "activeContribution": 0.0,
                "targetContribution": 0.0,
                "benchmarkContribution": 0.0,
                "_source_map": {},
            },
        )
        security_bucket["activeContribution"] += active
        security_bucket["targetContribution"] += target
        security_bucket["benchmarkContribution"] += benchmark

        source_key = (source_name, portcode, path_label)
        source_bucket = security_bucket["_source_map"].setdefault(
            source_key,
            {
                "sourceName": source_name,
                "portcode": portcode,
                "path": path_label,
                "activeContribution": 0.0,
                "targetContribution": 0.0,
                "benchmarkContribution": 0.0,
            },
        )
        source_bucket["activeContribution"] += active
        source_bucket["targetContribution"] += target
        source_bucket["benchmarkContribution"] += benchmark

        path_bucket = acid_bucket["_path_map"].setdefault(
            path_label,
            {
                "path": path_label,
                "activeContribution": 0.0,
                "targetContribution": 0.0,
                "benchmarkContribution": 0.0,
                "rows": 0,
            },
        )
        path_bucket["activeContribution"] += active
        path_bucket["targetContribution"] += target
        path_bucket["benchmarkContribution"] += benchmark
        path_bucket["rows"] += 1

    for fund_bucket in funds.values():
        for acid, acid_bucket in list(fund_bucket.items()):
            security_values = []
            for security_bucket in acid_bucket.pop("_security_map").values():
                sources = sorted(
                    security_bucket.pop("_source_map").values(),
                    key=lambda item: abs(float(item["activeContribution"])),
                    reverse=True,
                )
                security_bucket["sourceCount"] = len(sources)
                security_bucket["sources"] = sources
                security_values.append(security_bucket)
            security_values.sort(key=lambda item: abs(float(item["activeContribution"])), reverse=True)
            acid_bucket["securityCount"] = len(security_values)
            acid_bucket["securities"] = security_values
            path_values = sorted(
                acid_bucket.pop("_path_map").values(),
                key=lambda item: abs(float(item["activeContribution"])),
                reverse=True,
            )
            acid_bucket["byPath"] = path_values
            fund_bucket[acid] = acid_bucket
    return funds


def _float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the React monthly review bundle.")
    parser.add_argument(
        "--snapshot-date",
        default=None,
        help="Optional monthly review snapshot directory to bundle. Defaults to the latest available.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output JSON path for the frontend bundle.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    bundle = build_bundle(snapshot_date=args.snapshot_date)
    alignment_rows, exposure_lineage = build_structured_frontend_data()
    output_path = Path(args.output)
    _write_json(output_path, bundle)
    _write_json_array(DEFAULT_ALIGNMENT_OUTPUT, alignment_rows)
    _write_json_array(DEFAULT_LINEAGE_OUTPUT, exposure_lineage)
    print(f"snapshot_date={bundle['snapshot_date']}")
    print(f"fund_count={bundle['fund_count']}")
    print(f"output={output_path}")
    print(f"alignment_rows={len(alignment_rows)}")
    print(f"alignment_output={DEFAULT_ALIGNMENT_OUTPUT}")
    print(f"lineage_output={DEFAULT_LINEAGE_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
