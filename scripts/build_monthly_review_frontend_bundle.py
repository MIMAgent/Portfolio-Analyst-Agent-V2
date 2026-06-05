"""Build a frontend-friendly bundle from the tracked monthly review artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MONTHLY_REVIEW_ROOT = ROOT / "artifacts" / "monthly_review"
DEFAULT_OUTPUT = ROOT / "frontend" / "Example_frontendV1" / "src" / "data" / "monthlyReviewBundle.json"


def build_bundle(snapshot_date: str | None = None) -> dict[str, Any]:
    snapshot_dir = _resolve_snapshot_dir(snapshot_date)
    batch_index = _load_json(snapshot_dir / "batch_index.json")

    funds = []
    for result in batch_index["results"]:
        output_dir = ROOT / result["output_dir"]
        run_payload = _load_json(output_dir / "run_payload.json")
        run_summary_markdown = (output_dir / "run_summary.md").read_text(encoding="utf-8")
        funds.append(
            {
                "slug": output_dir.name,
                "fund": result["fund"],
                "snapshot_date": result["snapshot_date"],
                "review_run_id": result["review_run_id"],
                "run_summary_markdown": run_summary_markdown,
                "run_payload": run_payload,
                "index_entry": result,
            }
        )

    return {
        "bundle_generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "snapshot_date": snapshot_dir.name,
        "as_of_date": batch_index["as_of_date"],
        "fund_count": batch_index["fund_count"],
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
    output_path = Path(args.output)
    _write_json(output_path, bundle)
    print(f"snapshot_date={bundle['snapshot_date']}")
    print(f"fund_count={bundle['fund_count']}")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
