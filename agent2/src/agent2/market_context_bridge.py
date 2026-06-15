"""Bridge agent2 challenge candidates to approved-source market context."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_analyst_agent.agent_tools import get_market_context, search_market_context  # noqa: E402


def build_challenge_market_context(
    *,
    header: dict[str, Any],
    challenge_candidates: list[dict[str, Any]],
    refresh_missing: bool = True,
    max_challenges: int = 4,
    max_rows_per_challenge: int = 3,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    snapshot_date = str(header.get("snapshot_date", "")).strip()
    as_of_date = str(header.get("review_date") or header.get("as_of_date") or snapshot_date).strip()
    fund = str(header.get("fund", "")).strip()

    for challenge in challenge_candidates[:max_challenges]:
        acid = str(challenge.get("acid", "")).strip()
        label = str(challenge.get("label", "")).strip()
        category = str(challenge.get("category", "")).strip()

        context = get_market_context(
            snapshot_date=snapshot_date,
            as_of_date=as_of_date,
            fund=fund,
            acid=acid or None,
            comparison_group=label or None,
            limit=max_rows_per_challenge,
        )
        refresh_attempted = False
        refresh_error = ""
        if refresh_missing and not context.get("rows"):
            refresh_attempted = True
            try:
                search_market_context(
                    query=_challenge_market_query(acid=acid, label=label, category=category),
                    snapshot_date=snapshot_date,
                    as_of_date=as_of_date,
                    fund=fund,
                    acid=acid or None,
                    comparison_group=label or None,
                    max_results=max_rows_per_challenge,
                    max_sources=3,
                )
                context = get_market_context(
                    snapshot_date=snapshot_date,
                    as_of_date=as_of_date,
                    fund=fund,
                    acid=acid or None,
                    comparison_group=label or None,
                    limit=max_rows_per_challenge,
                )
            except Exception as exc:  # best-effort enrichment only
                refresh_error = str(exc)

        rows.append(
            {
                "acid": acid,
                "label": label,
                "category": category,
                "query_used": _challenge_market_query(acid=acid, label=label, category=category),
                "context_status": context.get("context_status", ""),
                "refresh_attempted": refresh_attempted,
                "refresh_error": refresh_error,
                "rows": [
                    {
                        "headline": row.get("headline", ""),
                        "narrative": row.get("narrative", ""),
                        "fundamental_readthrough": row.get("fundamental_readthrough", ""),
                        "pm_question": row.get("pm_question", ""),
                        "source_label": row.get("source_label", ""),
                        "source_date": row.get("source_date", ""),
                        "source_url": row.get("source_url", ""),
                        "citation_ref": row.get("citation_ref", ""),
                    }
                    for row in context.get("rows", [])[:max_rows_per_challenge]
                ],
            }
        )
    return rows


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
