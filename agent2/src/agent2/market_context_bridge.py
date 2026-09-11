"""Bridge agent2 challenge candidates to approved-source market context.

v3 — region- and period-aware. For each challenge we run several targeted
queries against the approved SECTOR/MACRO sources (rates, PMI, earnings,
valuation, ...) chosen from the exposure's category code and dominant
decomposition driver.

Three things this layer must get right, because each one silently produces
fabricated-looking evidence when it is wrong:

1. **Region.** Exposure labels are region-agnostic — ``US ID EQ`` and
   ``EU ID EQ`` are both "Industrials". Queries derive their region from the
   ACID, never from a hardcoded "US".
2. **Scope.** Retrieved rows are keyed by scope, so the lens scope carries the
   ACID (``US ID EQ · pmi``), not the bare label. Keying by label alone served
   the US sleeve's rows back to the International sleeve.
3. **Absence.** The approved-source allowlist is US-centric (BLS, ISM, the Fed,
   FactSet, Nasdaq, plus two global research sources), so for most non-US
   exposures there is genuinely nothing to retrieve. That state is reported
   explicitly as ``market_evidence_status = "ABSENT"`` with a reason, rather
   than left as an empty list the model is expected to write around.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_analyst_agent.agent_tools import get_market_context, search_market_context  # noqa: E402
from portfolio_analyst_agent.market_context_regions import (  # noqa: E402
    category_subject,
    parse_acid,
    region_adjective,
    region_tokens,
)
from portfolio_analyst_agent.market_context_sources import (  # noqa: E402
    DEFAULT_APPROVED_SOURCES_PATH,
    load_approved_market_context_sources,
)


MAX_LENSES = 3

STATUS_PRESENT = "PRESENT"
STATUS_ABSENT = "ABSENT"

REASON_NO_SOURCE_FOR_REGION = "no_approved_source_covers_region"
REASON_NO_MATCHING_ROW = "no_approved_source_row_matched"


def build_challenge_market_context(
    *,
    header: dict[str, Any],
    challenge_candidates: list[dict[str, Any]],
    positions_by_acid: dict[str, dict[str, Any]] | None = None,
    refresh_missing: bool = True,
    max_challenges: int = 4,
    max_rows_per_challenge: int = 3,
    max_rows_per_lens: int = 2,
    approved_sources_path: str | Path = DEFAULT_APPROVED_SOURCES_PATH,
) -> list[dict[str, Any]]:
    positions_by_acid = positions_by_acid or {}
    rows: list[dict[str, Any]] = []
    snapshot_date = str(header.get("snapshot_date", "")).strip()
    as_of_date = str(header.get("review_date") or header.get("as_of_date") or snapshot_date).strip()
    fund = str(header.get("fund", "")).strip()
    period = _period_label(snapshot_date or as_of_date)
    covered_regions = _regions_covered_by_approved_sources(approved_sources_path)

    for challenge in challenge_candidates[:max_challenges]:
        acid = str(challenge.get("acid", "")).strip()
        label = str(challenge.get("label", "")).strip()
        category = str(challenge.get("category", "")).strip()
        driver = str((positions_by_acid.get(acid) or {}).get("decomposition_driver", "")).strip()
        parts = parse_acid(acid)
        region = parts.region_code

        base_query = _challenge_market_query(acid=acid, label=label, category=category, period=period)
        lenses = _lenses_for(acid=acid, label=label, category=category, driver=driver, period=period)
        region_supported = covered_regions is None or not region or region in covered_regions

        base_rows: list[dict[str, Any]] = []
        market_evidence: list[dict[str, Any]] = []

        if region_supported:
            # Legacy sector rows (scope = label) — keep exact_external_market_context working.
            base_rows = _fetch(
                snapshot_date, as_of_date, fund,
                acid=acid or None, comparison_group=label or None,
                query=base_query, limit=max_rows_per_challenge,
                refresh=refresh_missing, max_sources=3,
                relevance_acid=acid or None,
            )

            # Driver-aware, lens-scoped evidence.
            seen: set[tuple[str, str]] = set()
            for key, query in lenses:
                lens_rows = _fetch(
                    snapshot_date, as_of_date, fund,
                    acid=None, comparison_group=_lens_scope(acid=acid, label=label, lens=key),
                    query=query, limit=max_rows_per_lens,
                    refresh=refresh_missing, max_sources=3,
                    relevance_acid=acid or None,
                )
                for r in lens_rows[:max_rows_per_lens]:
                    dedupe = (r.get("headline", ""), r.get("source_url", ""))
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    market_evidence.append({"lens": key, "query_used": query, **_row_fields(r)})

        status, reason = _evidence_status(
            has_evidence=bool(market_evidence) or bool(base_rows),
            region_supported=region_supported,
        )

        rows.append(
            {
                "acid": acid,
                "label": label,
                "category": category,
                "region_code": region,
                "region": region_adjective(region),
                "period": period,
                "query_used": base_query,
                "lenses_attempted": [key for key, _ in lenses],
                "rows": [_row_fields(r) for r in base_rows[:max_rows_per_challenge]],
                "market_evidence": market_evidence,
                "market_evidence_status": status,
                "market_evidence_absent_reason": reason,
                "market_evidence_note": _absence_note(
                    reason=reason,
                    region=region_adjective(region),
                    subject=_query_subject(acid=acid, label=label, category=category),
                ),
            }
        )
    return rows


def _evidence_status(*, has_evidence: bool, region_supported: bool) -> tuple[str, str]:
    if has_evidence:
        return STATUS_PRESENT, ""
    if not region_supported:
        return STATUS_ABSENT, REASON_NO_SOURCE_FOR_REGION
    return STATUS_ABSENT, REASON_NO_MATCHING_ROW


def _absence_note(*, reason: str, region: str, subject: str) -> str:
    """A sentence the model can quote verbatim instead of inventing evidence."""

    if not reason:
        return ""
    subject = subject.strip() or "this exposure"
    if reason == REASON_NO_SOURCE_FOR_REGION:
        return (
            f"No approved market-context source covers {region or 'this region'}. "
            f"There is no external research in this pack for {subject}; say so rather than asserting market facts."
        )
    return (
        f"No approved-source research matched {subject} for this period. "
        "There is no external market evidence in this pack for it; say so rather than asserting market facts."
    )


def _lens_scope(*, acid: str, label: str, lens: str) -> str:
    """Scope key for a lens row.

    Keyed on the ACID because exposure labels repeat across regions — a bare
    "Industrials · pmi" scope is shared by the US and European sleeves.
    """

    subject = acid or label
    return f"{subject} · {lens}" if subject else lens


def _period_label(iso_date: str) -> str:
    """'2026-06-30' -> 'June 2026'. Empty when the date is missing or unparseable."""

    value = str(iso_date or "").strip()
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value[:10])
    except ValueError:
        return ""
    return f"{parsed.strftime('%B')} {parsed.year}"


def _regions_covered_by_approved_sources(
    approved_sources_path: str | Path = DEFAULT_APPROVED_SOURCES_PATH,
) -> set[str] | None:
    """Region codes at least one approved source can speak to.

    Returns ``None`` for "unrestricted" — either a global-scope source is
    approved, or the registry could not be read and retrieval should not be
    pre-emptively blocked on it. The relevance gate still screens whatever the
    search returns either way.
    """

    try:
        payload = load_approved_market_context_sources(approved_sources_path)
    except (OSError, ValueError):
        return None

    covered: set[str] = set()
    for source in payload.get("sources", []):
        scope_value = str(source.get("default_scope_value", "")).lower()
        if "global" in scope_value or "world" in scope_value:
            return None  # a global source can speak to any region
        for acid in source.get("relevant_acids", []):
            region = parse_acid(str(acid)).region_code
            if region:
                covered.add(region)
        scope_words = set(scope_value.replace(".", " ").split())
        for code in _CANDIDATE_REGION_CODES:
            if scope_words.intersection(region_tokens(code)):
                covered.add(code)
    return covered


# Blocs worth testing a source's scope string against; per-country coverage is
# established through relevant_acids, not prose.
_CANDIDATE_REGION_CODES = ("US", "EU", "UK", "JP", "EM")


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
    relevance_acid: str | None = None,
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
                relevance_acid=relevance_acid,
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


def _lenses_for(
    *,
    acid: str,
    label: str,
    category: str,
    driver: str,
    period: str = "",
) -> list[tuple[str, str]]:
    """Pick up to MAX_LENSES (lens_key, query) pairs from category + driver."""

    cat = category.lower()
    d = (driver or "").lower()
    parts = parse_acid(acid)
    region = parts.region_code
    adjective = region_adjective(region)
    lenses: list[tuple[str, str]] = []

    def add(key: str, query: str) -> None:
        if not any(key == existing for existing, _ in lenses):
            lenses.append((key, _with_period(query, period)))

    subject = _query_subject(acid=acid, label=label, category=category)
    year = period.split()[-1] if period else ""

    # Always: earnings + valuation (FactSet / S&P / Goldman).
    add("earnings", f"{subject} earnings growth revisions guidance")
    add("valuation", f"{subject} forward valuation P/E vs history {year}".strip())

    # Category-specific macro lens, keyed on the region-independent category code.
    code = parts.category_code
    if cat == "eq sector":
        if code == "ID":
            add("pmi", _pmi_query(region=region, adjective=adjective))
        elif code == "FN":
            add("rates", _rates_query(region=region, adjective=adjective))
        elif code == "IT":
            add("capex", f"{adjective} technology AI capital expenditure demand earnings")
        else:
            add("macro", f"{adjective} {label} sector demand macro outlook")
    elif "size" in cat or "style" in cat:
        style = "growth" if "Growth" in label else "value"
        add("smallcap", f"{adjective} small cap {style} earnings breadth interest rates")
    elif cat in {"country", "region"}:
        add("macro", f"{label} equity market macro earnings valuation")

    # Emphasis from the dominant decomposition driver.
    if "yield" in d:
        add("rates", _rates_query(region=region, adjective=adjective))
    elif "valuation" in d:
        add("valuation", f"{subject} valuation P/E dispersion vs history")
    elif "growth" in d:
        add("earnings", f"{subject} earnings growth momentum revisions")

    return lenses[:MAX_LENSES]


def _pmi_query(*, region: str, adjective: str) -> str:
    if region == "US":
        return "US ISM manufacturing PMI new orders production prices"
    return f"{adjective} manufacturing PMI new orders production"


def _rates_query(*, region: str, adjective: str) -> str:
    if region == "US":
        return "US interest rates Federal Reserve policy credit spreads"
    if region in {"EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "PT", "GR", "FI", "IE"}:
        return "euro area interest rates European Central Bank policy credit spreads"
    return f"{adjective} interest rates central bank policy credit spreads"


def _with_period(query: str, period: str) -> str:
    query = " ".join(query.split())
    if not period or period.lower() in query.lower():
        return query
    return f"{query} {period}"


def _query_subject(*, acid: str, label: str, category: str) -> str:
    """A natural query subject from the ACID (e.g. 'European industrials sector')."""

    parts = parse_acid(acid)
    adjective = region_adjective(parts.region_code)
    cat = category.lower()

    if cat in {"country", "region"}:
        return f"{label} equity market"

    subject = category_subject(parts.category_code)
    if not subject:
        # Unknown category code — fall back to the label, stripped of any
        # region words it already carries so we do not double them up.
        subject = _strip_region_words(label, parts.region_code) or label
        if cat == "eq sector":
            subject = f"{subject} sector"
    if not adjective:
        return subject
    return f"{adjective} {subject}".strip()


def _strip_region_words(label: str, region: str) -> str:
    tokens = region_tokens(region)
    kept = [word for word in label.split() if word.lower() not in tokens]
    return " ".join(kept).strip()


def _challenge_market_query(*, acid: str, label: str, category: str, period: str = "") -> str:
    subject = _query_subject(acid=acid, label=label, category=category)
    cat = category.lower()
    parts = parse_acid(acid)

    if cat == "eq sector":
        code = parts.category_code
        if code == "ID":
            query = f"{subject} valuation manufacturing PMI new orders earnings"
        elif code == "FN":
            query = f"{subject} valuation rates spreads earnings"
        elif code == "IT":
            query = f"{subject} earnings valuation AI leadership"
        elif code == "CD":
            query = f"{subject} valuation earnings demand"
        else:
            query = f"{subject} valuation earnings"
    elif cat == "eq size / style":
        if "Growth" in label:
            query = f"{subject} valuation earnings momentum market leadership"
        else:
            query = f"{subject} valuation rates style leadership"
    elif cat in {"country", "region"}:
        query = f"{subject} earnings valuation macro"
    else:
        query = f"{subject or acid or label} equity market context"

    return _with_period(query, period)


__all__ = [
    "REASON_NO_MATCHING_ROW",
    "REASON_NO_SOURCE_FOR_REGION",
    "STATUS_ABSENT",
    "STATUS_PRESENT",
    "build_challenge_market_context",
]
