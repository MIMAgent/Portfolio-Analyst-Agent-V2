"""Review run metadata helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from .evidence import file_sha256
from .governance import DEFAULT_GOVERNANCE_PATH, load_governance


PARSER_VERSION = "rolled_exposure_alignment_multisignal_v1"
MAPPING_VERSION = "mapping_layer_pending_review"
ALGO_VERSION = "algo_workbooks_current"


def build_review_run_metadata(
    *,
    fund: str,
    snapshot_date: str,
    as_of_date: str,
    run_mode: str = "ad_hoc",
    source_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    governance = load_governance(as_of_date=as_of_date)
    review_run_id = _review_run_id(fund=fund, snapshot_date=snapshot_date, as_of_date=as_of_date)
    paths = [Path(DEFAULT_GOVERNANCE_PATH), *(Path(path) for path in (source_paths or []))]
    return {
        "fund": fund,
        "snapshot_date": snapshot_date,
        "as_of_date": as_of_date,
        "review_run_id": review_run_id,
        "parser_version": PARSER_VERSION,
        "mapping_version": MAPPING_VERSION,
        "governance_version": governance.governance_version,
        "algo_version": ALGO_VERSION,
        "run_mode": run_mode,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_file_hashes": {path.as_posix(): file_sha256(path) for path in paths if path.exists()},
    }


def _review_run_id(*, fund: str, snapshot_date: str, as_of_date: str) -> str:
    digest = hashlib.sha256(f"{fund}|{snapshot_date}|{as_of_date}".encode("utf-8")).hexdigest()[:12]
    return f"rrun_{digest}"


__all__ = ["ALGO_VERSION", "MAPPING_VERSION", "PARSER_VERSION", "build_review_run_metadata"]
