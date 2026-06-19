"""Bridge agent2 challenge candidates to approved-source market context.

v2 — driver-aware, multi-lens retrieval. For each challenge we run several
targeted queries against the approved SECTOR/MACRO sources (rates, PMI,
earnings, valuation, ...) chosen from the exposure's category and dominant
decomposition driver. Each lens is scoped under a distinct compound
`comparison_group` ("<label> · <lens>") so retrieved rows stay attributable to
their lens (the store keys by scope, not by query). Returns both the legacy
sector `rows` and a structured, lens-tagged `market_evidence` list.

NOTE: the approved-source allowlist is sector/macro-level (BLS, ISM, the Fed,
FactSet, S&P Global, Nasdaq, Goldman) — there is no per-name source, so this is
sector/macro context by design, not single-stock research.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_analyst_agent.agent_tools import get_market_context, search_market_context  # noqa: E402


MAX_LENSES = 3


def build_challenge_market_context(
    *,
    header: dict[str, Any],
    challenge_candidates: list[dict[str, Any]],
    positions_by_acid: dict[str, dict[str, Any]] | None = None,
    refresh_missing: bool = True,
    max_challenges: int = 4,
    max_rows_per_challenge: int = 3,
    max_rows_per_lens: int = 2,
) -> list[dict[str, Any]]:
    positions_by_acid = positions_by_acid or {}
    rows: list[dict[str, Any]] = []
    snapshot_date = str(header.get("snapshot_date", "")).strip()
    as_of_date = str(header.get("review_date") or header.get("as_of_date") or snapshot_date).strip()
    fund = str(header.get("fund", "")).strip()

    for challenge in challenge_candidates[:max_challenges]:
        acid = str(challenge.get("acid", "")).strip()
        label = str(challenge.get("label", "")).strip()
        category = str(challenge.get("category", "")).strip()
        driver = str((positions_by_acid.get(acid) or {}).get("decomposition_driver", "")).strip()

        base_query = _challenge_market_query(acid=acid, label=label, category=category)

        # Legacy sector rows (scope = label) — keep exact_external_market_context working.
        base_rows = _fetch(
            snapshot_date, as_of_date, fund,
            acid=acid or None, comparison_group=label or None,
            query=base_query, limit=max_rows_per_challenge,
            refresh=refresh_missing, max_sources=3,
        )

        # Driver-aware, lens-scoped evidence.
        market_evidence: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for key, query in _lenses_for(label=label, category=category, driver=driver):
            scope = f"{label} · {key}" if label else key
            lens_rows = _fetch(
                snapshot_date, as_of_date, fund,
                acid=None, comparison_group=scope,
                query=query, limit=max_rows_per_lens,
                refresh=refresh_missing, max_sources=3,
            )
            for r in lens_rows[:max_rows_per_lens]:
                dedupe = (r.get("headline", ""), r.get("source_url", ""))
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                market_evidence.append({"lens": key, "query_used": query, **_row_fields(r)})

        rows.append(
            {
                "acid": acid,
                "label": label,
                "category": category,
                "query_used": base_query,
                "rows": [_row_fields(r) for r in base_rows[:max_rows_per_challenge]],
                "market_evidence": market_evidence,
            }
        )
    return rows


def _fetch(
    snapshot_date: str,
    as_of_date: str,
    fund: str,
    *,
    acid: str | None,
    comparison_group: str | None,
    query: str,
    limit: int,
    refresh: bool,
    max_sources: int,
) -> list[dict[str, Any]]:
    context = get_market_context(
        snapshot_date=snapshot_date, as_of_date=as_of_date, fund=fund,
        acid=acid, comparison_group=comparison_group, limit=limit,
    )
    if refresh and not context.get("rows"):
        try:
            search_market_context(
                query=query, snapshot_date=snapshot_date, as_of_date=as_of_date, fund=fund,
                acid=acid, comparison_group=comparison_group,
                max_results=limit, max_sources=max_sources,
            )
            context = get_market_context(
                snapshot_date=snapshot_date, as_of_date=as_of_date, fund=fund,
                acid=acid, comparison_group=comparison_group, limit=limit,
            )
        except Exception:  # best-effort enrichment only
            pass
    return context.get("rows", [])


def _row_fields(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": r.get("headline", ""),
        "narrative": r.get("narrative", ""),
        "fundamental_readthrough": r.get("fundamental_readthrough", ""),
        "pm_question": r.get("pm_question", ""),
        "source_label": r.get("source_label", ""),
        "source_date": r.get("source_date", ""),
        "source_url": r.get("source_url", ""),
        "citation_ref": r.get("citation_ref", ""),
    }


def _lenses_for(*, label: str, category: str, driver: str) -> list[tuple[str, str]]:
    """Pick up to MAX_LENSES (lens_key, query) pairs from category + driver."""
    cat = category.lower()
    d = (driver or "").lower()
    lenses: list[tuple[str, str]] = []

    def add(key: str, query: str) -> None:
        if not any(key == existing for existing, _ in lenses):
            lenses.append((key, query))

    subject = _query_subject(label, category)

    # Always: earnings + valuation (FactSet / S&P / Goldman).
    add("earnings", f"{subject} Q1 2026 earnings growth revisions guidance")
    add("valuation", f"{subject} forward valuation P/E vs history 2026")

    # Category-specific macro lens.
    if cat == "eq sector":
        if label == "Industrials":
            add("pmi", "US ISM manufacturing PMI new orders production prices May 2026")
        elif label == "Financials":
            add("rates", "US interest rates Federal Reserve policy credit spreads May 2026")
        elif label == "Information Technology":
            add("capex", "US technology AI capital expenditure demand earnings 2026")
        else:
            add("macro", f"US {label} sector demand macro outlook May 2026")
    elif "size" in cat or "style" in cat:
        style = "growth" if "Growth" in label else "value"
        add("smallcap", f"US small cap {style} earnings breadth interest rates May 2026")
    elif cat in {"country", "region"}:
        add("macro", f"{label} equity market macro earnings valuation May 2026")

    # Emphasis from the dominant decomposition driver.
    if "yield" in d:
        add("rates", "US interest rates Federal Reserve policy yield curve May 2026")
    elif "valuation" in d:
        add("valuation", f"US {label} valuation P/E dispersion vs history 2026")
    elif "growth" in d:
        add("earnings", f"US {label} earnings growth momentum revisions 2026")

    return lenses[:MAX_LENSES]


def _query_subject(label: str, category: str) -> str:
    """A natural query subject from the exposure label (e.g. 'US small-cap growth')."""
    cat = category.lower()
    if cat == "eq sector":
        return f"US {label} sector"
    if "size" in cat or "style" in cat:
        clean = (
            label.replace("United States", "")
            .replace("Sml", "small-cap")
            .replace("Mid", "mid-cap")
            .replace("Lrg", "large-cap")
            .strip()
        )
        return f"US {clean}".replace("  ", " ").strip()
    if cat in {"country", "region"}:
        return f"{label} equity market"
    return f"US {label}"


def _challenge_market_query(*, acid: str, label: str, category: str) -> str:
    category_lower = category.lower()
    if category_lower == "eq sector":
        if label == "Industrials":
            return "US industrials sector valuation manufacturing PMI new orders earnings May 2026"
        if label == "Financials":
            return "US financials sector valuation rates spreads earnings May 2026"
        if label == "Information Technology":
            return "US information technology sector earnings valuation AI leadership May 2026"
        if label == "Consumer Discretionary":
            return "US consumer discretionary sector valuation earnings demand May 2026"
    if category_lower == "eq size / style":
        if "Growth" in label:
            return f"US {label} valuation earnings momentum market leadership May 2026"
        return f"US {label} valuation rates style leadership May 2026"
    if category_lower == "country":
        return f"{label} equity market earnings valuation macro May 2026"
    if category_lower == "region":
        return f"{label} equity market earnings valuation macro May 2026"
    return f"{acid or label} equity market context May 2026"


__all__ = ["build_challenge_market_context"]
