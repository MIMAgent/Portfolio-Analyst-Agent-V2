"""Read tools for the Model 1 agent harness."""

from __future__ import annotations

from datetime import date
import csv
from pathlib import Path
from typing import Any

from .acid_mapping import DEFAULT_ACID_MAPPING_CSV, load_mapping
from .challenge_triggers import DEFAULT_VIR_HISTORY_CSV, evaluate_challenge_triggers as _evaluate_challenge_triggers
from .csv_sources import open_csv_text, resolve_existing_csv_source
from .evidence import file_sha256, stable_row_id
from .market_context_search import SearchDefaults, search_market_context_web
from .memory_store import DEFAULT_MEMORY_PATH, recall_memory_store


DEFAULT_ALIGNMENT_CSV = Path("artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv")
DEFAULT_FUND_DETAIL_CSV = Path("artifacts/rolled_exposures/fund_rolled_exposure_detail.csv")
DEFAULT_MARKET_CONTEXT_CSV = Path("artifacts/market_context/monthly_market_context.csv")


def get_fund_snapshot(
    fund: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    alignment_csv: str | Path = DEFAULT_ALIGNMENT_CSV,
    mapping_csv: str | Path = DEFAULT_ACID_MAPPING_CSV,
) -> dict[str, Any]:
    """Return the current fund snapshot used by the LLM reasoning loop."""

    as_of = _require_date(as_of_date, "as_of_date")
    alignment_path = Path(alignment_csv)
    mapping_index = load_mapping(as_of_date=as_of, mapping_csv=mapping_csv)
    all_rows = _load_csv_rows(alignment_path)

    fund_rows = [row for row in all_rows if row.get("fund") == fund]
    if not fund_rows:
        raise ValueError(f"No rows found for fund: {fund}")

    selected_snapshot = _select_snapshot_date(fund_rows, snapshot_date, as_of)
    selected_rows = [
        mapping_index.enrich_row(_with_row_id(row, alignment_path))
        for row in fund_rows
        if _parse_optional_date(row.get("snapshot_date")) == selected_snapshot
    ]

    _enforce_as_of(selected_rows, as_of)

    artifact_dir = alignment_path.parent
    definitions = _load_optional_csv(artifact_dir / "fund_rollthrough_definitions.csv")
    coverage_rows = _load_optional_csv(artifact_dir / "fund_rollthrough_coverage.csv")

    return {
        "fund_metadata": _fund_metadata(fund, selected_snapshot, definitions),
        "coverage": _coverage(fund, coverage_rows),
        "acid_rows": selected_rows,
        "diagnostics": _diagnostics(fund, artifact_dir),
        "run_metadata": {
            "fund": fund,
            "snapshot_date": selected_snapshot.isoformat(),
            "as_of_date": as_of.isoformat(),
            "source_file_hashes": _source_hashes(
                [
                    alignment_path,
                    artifact_dir / "fund_rollthrough_definitions.csv",
                    artifact_dir / "fund_rollthrough_coverage.csv",
                    artifact_dir / "funds_with_no_usable_benchmark.csv",
                    artifact_dir / "acid_rows_with_zero_benchmark_exposure_in_benchmarked_funds.csv",
                    Path(mapping_csv),
                ]
            ),
            "tool_version": "get_fund_snapshot_v1",
        },
    }


def recall_memory(
    fund: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    scope: list[str] | tuple[str, ...] | None = None,
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
    include_proposed: bool = False,
) -> dict[str, Any]:
    """Return prior memory entries for one fund as of a controlled replay date."""

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")
    return recall_memory_store(
        fund=fund,
        snapshot_date=selected_snapshot,
        as_of_date=as_of,
        scope=scope,
        memory_path=memory_path,
        include_proposed=include_proposed,
    )


def evaluate_challenge_triggers(
    fund: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    vir_history_csv: str | Path = DEFAULT_VIR_HISTORY_CSV,
) -> dict[str, Any]:
    """Return deterministic challenge trigger candidates for one fund."""

    return _evaluate_challenge_triggers(
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        vir_history_csv=vir_history_csv,
    )


def get_acid_history(
    acid: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    lookback_months: int = 12,
    model_family: str | None = None,
    vir_history_csv: str | Path = DEFAULT_VIR_HISTORY_CSV,
) -> dict[str, Any]:
    """Return replay-safe historical VIR rows for one ACID."""

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")
    if lookback_months < 1:
        raise ValueError("lookback_months must be positive.")

    start_date = _subtract_months(selected_snapshot, lookback_months)
    path = Path(vir_history_csv)
    rows = []
    with open_csv_text(path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            row_date = _parse_optional_date(row.get("snapshot_date"))
            if row_date is None or row_date < start_date or row_date > selected_snapshot or row_date > as_of:
                continue
            if row.get("acid") != acid:
                continue
            if model_family and not _model_family_matches(row, model_family):
                continue
            rows.append(_with_row_id(row, path))

    return {
        "acid": acid,
        "snapshot_date": selected_snapshot.isoformat(),
        "as_of_date": as_of.isoformat(),
        "lookback_months": lookback_months,
        "model_family": model_family or "",
        "row_count": len(rows),
        "rows": rows,
        "run_metadata": {
            "source_file_hashes": _source_hashes([path]),
            "tool_version": "get_acid_history_v1",
        },
    }


def get_exposure_lineage(
    fund: str,
    acid: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    detail_csv: str | Path = DEFAULT_FUND_DETAIL_CSV,
    limit: int = 100,
) -> dict[str, Any]:
    """Return account/security rows that roll up into one fund/ACID exposure."""

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")

    detail_path = Path(detail_csv)
    matched = []
    for row in _load_csv_rows(detail_path):
        row_date = _parse_optional_date(row.get("snapshot_date"))
        if row_date != selected_snapshot or row_date > as_of:
            continue
        if row.get("fund") != fund or row.get("acid") != acid:
            continue
        matched.append(_with_row_id(row, detail_path))

    matched = sorted(
        matched,
        key=lambda row: abs(_optional_float(row.get("fund_target_security_contribution")) or 0.0),
        reverse=True,
    )
    limited = matched[:limit]

    return {
        "fund": fund,
        "acid": acid,
        "snapshot_date": selected_snapshot.isoformat(),
        "as_of_date": as_of.isoformat(),
        "row_count": len(matched),
        "returned_row_count": len(limited),
        "limit": limit,
        "rows": limited,
        "run_metadata": {
            "source_file_hashes": _source_hashes([detail_path]),
            "tool_version": "get_exposure_lineage_v1",
        },
    }


def get_peer_context(
    acid: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    alignment_csv: str | Path = DEFAULT_ALIGNMENT_CSV,
    mapping_csv: str | Path = DEFAULT_ACID_MAPPING_CSV,
) -> dict[str, Any]:
    """Return mapping-driven peer context for one ACID."""

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")

    mapping_index = load_mapping(as_of_date=as_of, mapping_csv=mapping_csv)
    mapping = mapping_index.get(acid)
    if mapping is None:
        peers = []
        acid_mapping = None
    else:
        peers = mapping_index.peers_for(mapping)
        acid_mapping = _mapping_with_citation(mapping.to_dict(), mapping_csv)

    alignment_path = Path(alignment_csv)
    peer_acids = {peer.acid for peer in peers}
    peer_acids.add(acid)
    current_rows = [
        mapping_index.enrich_row(_with_row_id(row, alignment_path))
        for row in _load_csv_rows(alignment_path)
        if row.get("acid") in peer_acids and _parse_optional_date(row.get("snapshot_date")) == selected_snapshot
    ]
    _enforce_as_of(current_rows, as_of)

    return {
        "acid": acid,
        "snapshot_date": selected_snapshot.isoformat(),
        "as_of_date": as_of.isoformat(),
        "mapping_status": "matched_to_mapping" if mapping else "missing_in_mapping",
        "mapping": acid_mapping,
        "peer_count": len(peers),
        "peers": [_mapping_with_citation(peer.to_dict(), mapping_csv) for peer in peers],
        "current_snapshot_row_count": len(current_rows),
        "current_snapshot_rows": current_rows,
        "run_metadata": {
            "source_file_hashes": _source_hashes([Path(mapping_csv), alignment_path]),
            "tool_version": "get_peer_context_v1",
        },
    }


def get_market_context(
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    fund: str | None = None,
    acid: str | None = None,
    comparison_group: str | None = None,
    market_context_csv: str | Path = DEFAULT_MARKET_CONTEXT_CSV,
    limit: int = 12,
) -> dict[str, Any]:
    """Return approved monthly market/fundamental context rows.

    This is intentionally file-backed rather than model-memory-backed so replay
    runs only use context available as of the review date.
    """

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")
    path = Path(market_context_csv)
    resolved_path = resolve_existing_csv_source(path) or path
    if not resolved_path.exists():
        return {
            "snapshot_date": selected_snapshot.isoformat(),
            "as_of_date": as_of.isoformat(),
            "fund": fund or "",
            "acid": acid or "",
            "comparison_group": comparison_group or "",
            "row_count": 0,
            "rows": [],
            "context_status": "missing_market_context_file",
            "expected_artifact": path.as_posix(),
            "run_metadata": {"tool_version": "get_market_context_v1", "source_file_hashes": {}},
        }

    rows: list[dict[str, str]] = []
    with open_csv_text(path) as csv_file:
        for row in csv.DictReader(csv_file):
            row_snapshot = _parse_optional_date(row.get("snapshot_date"))
            row_as_of = _parse_optional_date(row.get("as_of_date")) or row_snapshot
            if row_snapshot is None or row_snapshot > selected_snapshot:
                continue
            if row_as_of is not None and row_as_of > as_of:
                continue
            if not _market_context_matches(row, fund=fund, acid=acid, comparison_group=comparison_group):
                continue
            rows.append(_with_row_id(row, path))

    rows = sorted(
        rows,
        key=lambda row: _market_context_sort_key(
            row,
            fund=fund,
            acid=acid,
            comparison_group=comparison_group,
        ),
        reverse=True,
    )[:limit]
    rows = [
        {
            **row,
            "citation_ref": f"csv:{path.as_posix()}#row_id={row.get('row_id', '')}",
        }
        for row in rows
    ]
    return {
        "snapshot_date": selected_snapshot.isoformat(),
        "as_of_date": as_of.isoformat(),
        "fund": fund or "",
        "acid": acid or "",
        "comparison_group": comparison_group or "",
        "row_count": len(rows),
        "rows": rows,
        "context_status": "matched_context_rows" if rows else "no_relevant_context_rows",
        "run_metadata": {
            "tool_version": "get_market_context_v1",
            "source_file_hashes": _source_hashes([path]),
        },
    }


def search_market_context(
    query: str,
    snapshot_date: str | date | None = None,
    as_of_date: str | date | None = None,
    fund: str | None = None,
    acid: str | None = None,
    comparison_group: str | None = None,
    market_context_csv: str | Path = DEFAULT_MARKET_CONTEXT_CSV,
    max_results: int = 6,
    max_sources: int = 4,
) -> dict[str, Any]:
    """Search approved web sources and cache citable market-context rows."""

    selected_snapshot = _require_date(snapshot_date, "snapshot_date")
    as_of = _require_date(as_of_date, "as_of_date")
    if selected_snapshot > as_of:
        raise ValueError("snapshot_date may not be after as_of_date.")
    return search_market_context_web(
        query=query,
        defaults=SearchDefaults(
            snapshot_date=selected_snapshot.isoformat(),
            as_of_date=as_of.isoformat(),
            fund=fund or "",
            acid=acid or "",
            comparison_group=comparison_group or "",
        ),
        output_csv=market_context_csv,
        max_results=max_results,
        max_sources=max_sources,
        append=True,
    )


def _load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _load_optional_csv(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if not path.exists():
        return []
    return _load_csv_rows(path)


def _mapping_with_citation(row: dict[str, Any], mapping_csv: str | Path) -> dict[str, Any]:
    row_id = row.get("row_id", "")
    if row_id:
        return {
            **row,
            "citation_ref": f"csv:{Path(mapping_csv).as_posix()}#row_id={row_id}",
        }
    return row


def _market_context_matches(
    row: dict[str, str],
    *,
    fund: str | None,
    acid: str | None,
    comparison_group: str | None,
) -> bool:
    scope_type = row.get("scope_type", "").strip().lower()
    scope_value = row.get("scope_value", "").strip()
    if scope_type in {"global", "market", "macro"}:
        return True
    if fund and scope_type == "fund" and scope_value == fund:
        return True
    if acid and scope_type == "acid" and scope_value == acid:
        return True
    if comparison_group and scope_type == "comparison_group" and scope_value == comparison_group:
        return True
    return False


def _market_context_sort_key(
    row: dict[str, str],
    *,
    fund: str | None,
    acid: str | None,
    comparison_group: str | None,
) -> tuple[Any, ...]:
    scope_score = _market_context_scope_score(row, fund=fund, acid=acid, comparison_group=comparison_group)
    relevance_score = _market_context_relevance_score(row, acid=acid, comparison_group=comparison_group)
    priority_score = _market_context_priority_score(row.get("priority", ""))
    row_date = _parse_optional_date(row.get("snapshot_date")) or date.min
    return (scope_score, relevance_score, priority_score, row_date, row.get("row_id", ""))


def _market_context_scope_score(
    row: dict[str, str],
    *,
    fund: str | None,
    acid: str | None,
    comparison_group: str | None,
) -> int:
    scope_type = row.get("scope_type", "").strip().lower()
    scope_value = row.get("scope_value", "").strip()
    if acid and scope_type == "acid" and scope_value == acid:
        return 40
    if comparison_group and scope_type == "comparison_group" and scope_value == comparison_group:
        return 30
    if fund and scope_type == "fund" and scope_value == fund:
        return 25
    if scope_type in {"market", "macro"}:
        return 10
    if scope_type == "global":
        return 5
    return 0


def _market_context_relevance_score(row: dict[str, str], *, acid: str | None, comparison_group: str | None) -> int:
    text = " ".join(
        [
            row.get("headline", ""),
            row.get("narrative", ""),
            row.get("fundamental_readthrough", ""),
            row.get("pm_question", ""),
            row.get("sector", ""),
            row.get("asset_class", ""),
        ]
    ).lower()
    score = 0
    for phrase in _market_context_relevance_phrases(acid=acid, comparison_group=comparison_group):
        if phrase in text:
            score += 5 if " " in phrase else 2
    if _looks_like_navigation_context(text):
        score -= 50
    if "s&p 500" in text or "s&p500" in text:
        score -= 1
    if "earnings scorecard" in text or "companies reporting actual results" in text:
        score -= 5
    return score


def _market_context_relevance_phrases(*, acid: str | None, comparison_group: str | None) -> tuple[str, ...]:
    acid_phrases = {
        "US IT EQ": (
            "information technology",
            "technology",
            "software",
            "semiconductor",
            "semiconductors",
            "ai",
            "artificial intelligence",
            "data center",
            "data centers",
            "capital spending",
            "capex",
        ),
        "US ID EQ": (
            "industrials",
            "industrial",
            "manufacturing",
            "new orders",
            "pmi",
            "production",
            "capex",
            "capital spending",
            "defense",
            "aerospace",
        ),
        "US LRG G EQ": (
            "large-cap growth",
            "large cap growth",
            "magnificent 7",
            "mag-7",
            "mega-cap",
            "megacap",
            "growth",
            "valuation",
            "ai",
        ),
        "US LRG EQ": (
            "large-cap",
            "large cap",
            "s&p 500",
            "sp500",
            "valuation",
            "earnings growth",
        ),
    }
    phrases = list(acid_phrases.get(acid or "", ()))
    if comparison_group == "us_equity_sectors":
        phrases.extend(["sector", "sectors", "earnings", "revenue", "guidance"])
    return tuple(phrases)


def _market_context_priority_score(priority: str) -> int:
    try:
        return -int(priority)
    except ValueError:
        return 0


def _looks_like_navigation_context(text: str) -> bool:
    navigation_markers = (
        "table of contents",
        "charts q",
        "forward 12-month p/e ratio",
        "trailing 12-mont",
        "www.factset.com 2 earnings insight",
    )
    return any(marker in text for marker in navigation_markers)


def _require_date(raw_value: str | date | None, field_name: str) -> date:
    if raw_value is None:
        raise ValueError(f"{field_name} is required.")
    if isinstance(raw_value, date):
        return raw_value
    return date.fromisoformat(raw_value)


def _parse_optional_date(raw_value: str | None) -> date | None:
    if not raw_value:
        return None
    return date.fromisoformat(raw_value)


def _select_snapshot_date(
    rows: list[dict[str, str]],
    requested_snapshot_date: str | date | None,
    as_of_date: date,
) -> date:
    if requested_snapshot_date is not None:
        selected = _require_date(requested_snapshot_date, "snapshot_date")
        if selected > as_of_date:
            raise ValueError("snapshot_date may not be after as_of_date.")
        return selected

    available = sorted(
        snapshot
        for snapshot in {_parse_optional_date(row.get("snapshot_date")) for row in rows}
        if snapshot is not None and snapshot <= as_of_date
    )
    if not available:
        raise ValueError("No fund snapshot is available on or before as_of_date.")
    return available[-1]


def _enforce_as_of(rows: list[dict[str, str]], as_of_date: date) -> None:
    for row in rows:
        for field_name in ("snapshot_date", "vir_snapshot_date", "algo_snapshot_date"):
            field_date = _parse_optional_date(row.get(field_name))
            if field_date is not None and field_date > as_of_date:
                raise ValueError(f"{field_name} may not be after as_of_date.")


def _with_row_id(row: dict[str, str], path: str | Path) -> dict[str, str]:
    if row.get("row_id"):
        return row
    return {"row_id": stable_row_id(row, namespace=Path(path).as_posix()), **row}


def _fund_metadata(
    fund: str,
    snapshot_date: date,
    definitions: list[dict[str, str]],
) -> dict[str, Any]:
    definition = next((row for row in definitions if row.get("fund") == fund), {})
    return {
        "fund": fund,
        "snapshot_date": snapshot_date.isoformat(),
        "benchmark_family": definition.get("benchmark_family", ""),
        "definition": definition,
    }


def _coverage(fund: str, coverage_rows: list[dict[str, str]]) -> dict[str, Any]:
    row = next((item for item in coverage_rows if item.get("fund") == fund), {})
    return {
        "target_match_pct": _optional_float(row.get("target_match_pct")),
        "benchmark_match_pct": _optional_float(row.get("benchmark_match_pct")),
        "benchmark_expected_status": row.get("benchmark_expected_status", ""),
        "raw": row,
    }


def _diagnostics(fund: str, artifact_dir: Path) -> dict[str, Any]:
    return {
        "funds_with_no_usable_benchmark": _diagnostic_rows(
            artifact_dir / "funds_with_no_usable_benchmark.csv", fund
        ),
        "zero_benchmark_acid_rows": _diagnostic_rows(
            artifact_dir / "acid_rows_with_zero_benchmark_exposure_in_benchmarked_funds.csv",
            fund,
        ),
    }


def _diagnostic_rows(path: Path, fund: str) -> dict[str, Any]:
    rows = [row for row in _load_optional_csv(path) if row.get("fund") == fund]
    return {
        "artifact_path": path.as_posix(),
        "row_count": len(rows),
        "rows": [_with_row_id(row, path) for row in rows],
    }


def _source_hashes(paths: list[Path]) -> dict[str, str]:
    resolved_paths = [resolve_existing_csv_source(path) or path for path in paths]
    return {path.as_posix(): file_sha256(path) for path in resolved_paths if path.exists()}


def _optional_float(raw_value: str | None) -> float | None:
    if raw_value is None or raw_value == "":
        return None
    return float(raw_value)


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(value.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    first_next = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    return (first_next - date(year, month, 1)).days


def _model_family_matches(row: dict[str, str], model_family: str) -> bool:
    normalized = model_family.strip().lower()
    candidates = [
        row.get("model_family", ""),
        row.get("workbook_type", ""),
    ]
    return any(normalized in candidate.strip().lower() for candidate in candidates if candidate)


__all__ = [
    "evaluate_challenge_triggers",
    "get_acid_history",
    "get_exposure_lineage",
    "get_fund_snapshot",
    "get_market_context",
    "search_market_context",
    "get_peer_context",
    "recall_memory",
]
