"""Approved-source web search for market-context rows.

The agent does not browse the open web directly. This module searches only the
approved source registry, converts result snippets into citable context rows,
and appends them to the same CSV consumed by get_market_context.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from html import unescape
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
import re
from typing import Any
import zlib
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from .market_context_ingest import MARKET_CONTEXT_COLUMNS
from .market_context_sources import DEFAULT_APPROVED_SOURCES_PATH, load_approved_market_context_sources
from .row_ids import generic_row_id


DEFAULT_MARKET_CONTEXT_CSV = Path("artifacts/market_context/monthly_market_context.csv")
DEFAULT_SEARCH_ENDPOINT = "https://duckduckgo.com/html/?q={query}"
DEFAULT_SEARCH_ENDPOINTS = (
    "https://duckduckgo.com/html/?q={query}",
    "https://html.duckduckgo.com/html/?q={query}",
)


@dataclass(frozen=True)
class SearchDefaults:
    snapshot_date: str
    as_of_date: str
    fund: str = ""
    acid: str = ""
    comparison_group: str = ""
    priority: str = "2"


def search_market_context_web(
    *,
    query: str,
    defaults: SearchDefaults,
    output_csv: str | Path = DEFAULT_MARKET_CONTEXT_CSV,
    approved_sources_path: str | Path = DEFAULT_APPROVED_SOURCES_PATH,
    max_results: int = 6,
    max_sources: int = 4,
    append: bool = True,
    timeout_seconds: int = 10,
    search_endpoint: str = DEFAULT_SEARCH_ENDPOINT,
) -> dict[str, Any]:
    """Search approved domains and append citable rows to monthly context CSV."""

    query = " ".join(query.split())
    if not query:
        raise ValueError("query is required.")
    _require_iso_date(defaults.snapshot_date, "snapshot_date")
    _require_iso_date(defaults.as_of_date, "as_of_date")
    if date.fromisoformat(defaults.snapshot_date) > date.fromisoformat(defaults.as_of_date):
        raise ValueError("snapshot_date may not be after as_of_date.")
    if max_results < 1:
        raise ValueError("max_results must be positive.")
    if max_sources < 1:
        raise ValueError("max_sources must be positive.")

    sources_payload = load_approved_market_context_sources(approved_sources_path)
    sources = _select_sources(sources_payload["sources"], acid=defaults.acid, query=query, max_sources=max_sources)
    rows: list[dict[str, str]] = []
    searched_domains: list[str] = []
    diagnostics: list[dict[str, Any]] = []

    for source in sources:
        if len(rows) >= max_results:
            break
        domain = source["domain"]
        searched_domains.append(domain)
        source_query = f"{query} site:{domain}"
        source_diagnostic: dict[str, Any] = {
            "source_id": source.get("source_id", ""),
            "domain": domain,
            "search_result_count": 0,
            "accepted_search_result_count": 0,
            "fallback_row_count": 0,
            "fallback_status": "",
        }
        search_results = []
        for html in _fetch_search_pages(source_query, endpoint=search_endpoint, timeout_seconds=timeout_seconds):
            search_results.extend(_parse_search_results(html))
        deduped_search_results = _dedupe_results(search_results)
        source_diagnostic["search_result_count"] = len(deduped_search_results)
        for result in deduped_search_results:
            if len(rows) >= max_results:
                break
            if not _url_matches_domain(result["url"], domain):
                continue
            rows.append(_row_from_result(result, source=source, query=query, defaults=defaults))
            source_diagnostic["accepted_search_result_count"] += 1
        if len(rows) < max_results and not any(
            _url_matches_domain(row.get("source_url", ""), domain) for row in rows
        ):
            fallback_rows, fallback_status = _fallback_rows_from_source(
                source,
                query=query,
                defaults=defaults,
                timeout_seconds=timeout_seconds,
            )
            source_diagnostic["fallback_status"] = fallback_status
            source_diagnostic["fallback_row_count"] = len(fallback_rows)
            for fallback in fallback_rows:
                if len(rows) >= max_results:
                    break
                rows.append(fallback)
        diagnostics.append(source_diagnostic)

    rows = _dedupe_rows(rows)
    output_path = Path(output_csv)
    existing_rows = _read_existing_rows(output_path) if append and output_path.exists() else []
    combined_rows = _dedupe_rows(existing_rows + rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MARKET_CONTEXT_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(combined_rows)

    return {
        "query": query,
        "snapshot_date": defaults.snapshot_date,
        "as_of_date": defaults.as_of_date,
        "fund": defaults.fund,
        "acid": defaults.acid,
        "comparison_group": defaults.comparison_group,
        "searched_domains": searched_domains,
        "new_row_count": len(rows),
        "total_row_count": len(combined_rows),
        "output_csv": output_path.as_posix(),
        "context_status": "searched_approved_sources" if rows else "no_approved_source_results",
        "rows": [
            {
                **row,
                "citation_ref": f"csv:{output_path.as_posix()}#row_id={row.get('row_id', '')}",
            }
            for row in rows
        ],
        "run_metadata": {
            "tool_version": "search_market_context_web_v1",
            "search_endpoint": search_endpoint,
            "approved_sources_path": Path(approved_sources_path).as_posix(),
            "source_diagnostics": diagnostics,
        },
    }


def _select_sources(sources: list[dict[str, Any]], *, acid: str, query: str, max_sources: int) -> list[dict[str, Any]]:
    if not acid:
        return sorted(sources, key=lambda source: _source_score(source, query=query, acid=acid), reverse=True)[:max_sources]

    matched = [
        source
        for source in sources
        if acid in source.get("relevant_acids", [])
    ]
    macro = [
        source
        for source in sources
        if source not in matched and source.get("default_scope_type") in {"macro", "market"}
    ]
    return sorted(matched + macro, key=lambda source: _source_score(source, query=query, acid=acid), reverse=True)[:max_sources]


def _source_score(source: dict[str, Any], *, query: str, acid: str) -> int:
    haystack = " ".join(
        [
            source.get("source_id", ""),
            source.get("source_name", ""),
            source.get("source_type", ""),
            source.get("default_scope_value", ""),
            " ".join(source.get("approved_use", [])),
            source.get("notes", ""),
        ]
    ).lower()
    query_words = _expanded_query_words(query)
    score = sum(2 for word in query_words if word in haystack)
    if acid and acid in source.get("relevant_acids", []):
        score += 5
    query_lowered = query.lower()
    if any(term in query_lowered for term in ("manufacturing", "pmi", "new orders", "industrial", "industrials")):
        if source.get("source_id") == "ism_pmi_reports":
            score += 20
        if source.get("source_id") == "factset_earnings_insight":
            score -= 4
    if any(term in query_lowered for term in ("information technology", "technology", "ai", "capex", "earnings")):
        if source.get("source_id") in {"factset_earnings_insight", "sp_global_market_intelligence_and_ratings", "goldman_sachs_research_insights"}:
            score += 6
    return score


def _fetch_search_pages(query: str, *, endpoint: str, timeout_seconds: int) -> list[str]:
    endpoints = DEFAULT_SEARCH_ENDPOINTS if endpoint == DEFAULT_SEARCH_ENDPOINT else (endpoint,)
    pages = []
    for candidate in endpoints:
        try:
            pages.append(_fetch_url(candidate.format(query=quote_plus(query)), timeout_seconds=timeout_seconds))
        except OSError:
            continue
    return pages


def _fetch_url(url: str, *, timeout_seconds: int, max_bytes: int = 1_000_000) -> str:
    return _fetch_bytes(url, timeout_seconds=timeout_seconds, max_bytes=max_bytes).decode("utf-8", errors="replace")


def _fetch_bytes(url: str, *, timeout_seconds: int, max_bytes: int = 1_000_000) -> bytes:
    if not url.startswith("https://"):
        raise ValueError("Only https URLs may be fetched.")
    request = Request(
        url,
        headers={
            "User-Agent": "portfolio-analyst-agent/0.1 approved-source-search",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - approved-source/search URL.
        return response.read(max_bytes)


def _parse_search_results(html: str) -> list[dict[str, str]]:
    parser = _DuckDuckGoResultParser()
    parser.feed(html)
    parser.close_result()
    return _dedupe_results(parser.results + _regex_search_results(html))


class _DuckDuckGoResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._active: dict[str, str] | None = None
        self._capture: str = ""
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        class_attr = attrs_dict.get("class", "")
        if tag == "a" and ("result__a" in class_attr or "result-link" in class_attr):
            self.close_result()
            self._active = {"url": _normalize_result_url(attrs_dict.get("href", "")), "title": "", "snippet": ""}
            self._capture = "title"
            self._text_parts = []
        elif self._active is not None and ("result__snippet" in class_attr or "result-snippet" in class_attr):
            self._capture = "snippet"
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._active is None or not self._capture:
            return
        if tag not in {"a", "div"}:
            return
        text = _clean_text(" ".join(self._text_parts))
        if self._capture == "title":
            self._active["title"] = text
            if tag == "a":
                self._capture = ""
        elif self._capture == "snippet":
            self._active["snippet"] = text
            self._maybe_commit()
            self._capture = ""
        self._text_parts = []

    def _maybe_commit(self) -> None:
        if self._active and self._active.get("url") and self._active.get("title"):
            self.results.append(self._active)
        self._active = None

    def close_result(self) -> None:
        self._maybe_commit()
        self._capture = ""
        self._text_parts = []


def _normalize_result_url(raw_url: str) -> str:
    raw_url = unescape(raw_url)
    parsed = urlparse(raw_url)
    if parsed.query:
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    return raw_url


def _regex_search_results(html: str) -> list[dict[str, str]]:
    results = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.IGNORECASE | re.DOTALL):
        title = _clean_text(re.sub(r"<[^>]+>", " ", match.group(2)))
        url = _normalize_result_url(match.group(1))
        if title and url.startswith("https://"):
            results.append({"url": url, "title": title, "snippet": ""})
    return results


def _dedupe_results(results: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for result in results:
        url = result.get("url", "")
        if url and url not in deduped:
            deduped[url] = result
    return list(deduped.values())


def _url_matches_domain(url: str, domain: str) -> bool:
    host = urlparse(url).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    domain = domain.lower()
    return host == domain or host.endswith(f".{domain}")


def _row_from_result(
    result: dict[str, str],
    *,
    source: dict[str, Any],
    query: str,
    defaults: SearchDefaults,
) -> dict[str, str]:
    scope_type, scope_value = _scope(defaults, source=source)
    source_date = source.get("publication_date") or defaults.as_of_date
    row = {
        "snapshot_date": defaults.snapshot_date,
        "as_of_date": defaults.as_of_date,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "priority": defaults.priority,
        "headline": result.get("title", ""),
        "narrative": result.get("snippet", "") or result.get("title", ""),
        "fundamental_readthrough": f"Approved-source web context for query: {query}",
        "pm_question": "",
        "source_label": source.get("source_name", ""),
        "source_date": source_date,
        "region": "",
        "country": "",
        "sector": "",
        "asset_class": "",
        "source_url": result.get("url", ""),
        "source_path": "",
        "source_file_hash": "",
        "notes": f"source_id={source.get('source_id', '')}; live_web_search=true",
    }
    row["row_id"] = generic_row_id(row, namespace="market_context_web", prefix="mctx")
    return {column: row.get(column, "") for column in MARKET_CONTEXT_COLUMNS}


def _fallback_rows_from_source(
    source: dict[str, Any],
    *,
    query: str,
    defaults: SearchDefaults,
    timeout_seconds: int,
) -> tuple[list[dict[str, str]], str]:
    source_url = source.get("url", "")
    if not source_url or not _url_matches_domain(source_url, source.get("domain", "")):
        return [], "source_url_missing_or_domain_mismatch"
    title = source.get("source_name", "")
    snippets: list[str] = []
    if source_url.lower().endswith(".pdf"):
        try:
            pdf_bytes = _fetch_bytes(source_url, timeout_seconds=timeout_seconds, max_bytes=25_000_000)
            snippets = _relevant_snippets(_extract_pdf_text(pdf_bytes), query=query, acid=defaults.acid, limit=2)
        except OSError as exc:
            return [], f"pdf_fetch_failed:{exc.__class__.__name__}"
    else:
        try:
            html = _fetch_url(source_url, timeout_seconds=timeout_seconds, max_bytes=500_000)
            metadata = _html_metadata(html)
            title = metadata.get("title") or title
            candidate = metadata.get("description", "")
            if _is_relevant(candidate or title, query=query, acid=defaults.acid):
                snippets = [candidate or title]
        except OSError as exc:
            return [], f"html_fetch_failed:{exc.__class__.__name__}"

    rows = []
    for index, snippet in enumerate(snippets, start=1):
        rows.append(
            _row_from_result(
                {"url": source_url, "title": f"{title} excerpt {index}", "snippet": snippet},
                source=source,
                query=query,
                defaults=defaults,
            )
        )
    if rows:
        return rows, "query_relevant_source_excerpt"
    return [], "no_query_relevant_source_excerpt"


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    pypdf_text = _extract_pdf_text_with_pypdf(pdf_bytes)
    if pypdf_text:
        return pypdf_text

    chunks: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, flags=re.DOTALL):
        stream = match.group(1).strip(b"\r\n")
        decoded = _decode_pdf_stream(stream)
        chunks.extend(_pdf_text_strings(decoded))
    if not chunks:
        chunks.extend(_pdf_text_strings(pdf_bytes))
    return _clean_text(" ".join(chunks))


def _extract_pdf_text_with_pypdf(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return ""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        page_text = [page.extract_text() or "" for page in reader.pages[:20]]
    except Exception:  # noqa: BLE001 - optional parser fallback should be best-effort.
        return ""
    return _clean_text(" ".join(page_text))


def _decode_pdf_stream(stream: bytes) -> bytes:
    try:
        return zlib.decompress(stream)
    except zlib.error:
        return stream


def _pdf_text_strings(data: bytes) -> list[str]:
    text = data.decode("latin-1", errors="ignore")
    strings = []
    for raw in re.findall(r"\((.*?)\)\s*Tj|\((.*?)\)", text, flags=re.DOTALL):
        value = raw[0] or raw[1]
        cleaned = _clean_text(value.replace("\\(", "(").replace("\\)", ")").replace("\\n", " "))
        if len(cleaned) >= 20 and _looks_like_text(cleaned):
            strings.append(cleaned)
    return strings


def _looks_like_text(value: str) -> bool:
    alpha_count = sum(1 for char in value if char.isalpha())
    return alpha_count >= max(8, len(value) // 3)


def _relevant_snippets(text: str, *, query: str, acid: str = "", limit: int) -> list[str]:
    candidates = _snippet_candidates(text)
    scored = [
        (_relevance_score(candidate, query=query), candidate)
        for candidate in candidates
        if _is_relevant(candidate, query=query, acid=acid)
    ]
    scored = sorted(scored, key=lambda item: item[0], reverse=True)
    snippets = []
    for score, candidate in scored:
        if score <= 0:
            continue
        snippet = candidate[:700].strip()
        if snippet and not _is_duplicate_snippet(snippet, snippets):
            snippets.append(snippet)
        if len(snippets) >= limit:
            break
    return snippets


def _snippet_candidates(text: str) -> list[str]:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    candidates = list(sentences)
    for index in range(len(sentences) - 1):
        candidates.append(f"{sentences[index]} {sentences[index + 1]}")
    return _dedupe_text([candidate for candidate in candidates if 40 <= len(candidate) <= 1200 and not _is_navigation_text(candidate)])


def _relevance_score(text: str, *, query: str) -> int:
    text_words = set(_keywords(text))
    query_words = _expanded_query_words(query)
    intersection = text_words.intersection(query_words)
    score = len(intersection) * 2
    lowered = text.lower()
    query_lowered = query.lower()

    phrase_groups = [
        ("information technology", {"information technology", "technology", "tech", "software", "semiconductor", "semiconductors"}),
        ("large cap growth", {"large-cap growth", "large cap growth", "magnificent 7", "megacap", "mega-cap", "growth"}),
        ("industrials", {"industrial", "industrials", "manufacturing", "new orders", "pmi", "capex", "capital spending"}),
        ("earnings", {"earnings", "eps", "revenue", "guidance", "estimate", "estimates", "revision", "revisions"}),
        ("ai capex", {"ai", "artificial intelligence", "capex", "capital spending", "data center", "data centers"}),
    ]
    for query_trigger, phrases in phrase_groups:
        if any(word in query_lowered for word in query_trigger.split()) or query_trigger in query_lowered:
            score += sum(4 for phrase in phrases if phrase in lowered)

    if "s&p 500" in lowered or "s&p500" in lowered:
        score -= 1
    if "earnings scorecard" in lowered or "companies reporting actual results" in lowered:
        score -= 5
    if "key metrics" in lowered:
        score -= 2
    if _is_navigation_text(text):
        score -= 100
    return score


def _is_relevant(text: str, *, query: str, acid: str = "") -> bool:
    if not text:
        return False
    if _is_navigation_text(text):
        return False
    text_words = set(_keywords(text))
    query_words = _expanded_query_words(query)
    if not text_words or not query_words:
        return False
    if len(text_words.intersection(query_words)) < 2:
        return False
    acid_words = _acid_required_words(acid)
    if acid_words and not text_words.intersection(acid_words):
        return False
    return True


def _is_navigation_text(text: str) -> bool:
    lowered = text.lower()
    navigation_markers = (
        "table of contents",
        "charts q",
        "forward 12-month p/e ratio",
        "trailing 12-mont",
        "www.factset.com 2 earnings insight",
    )
    return any(marker in lowered for marker in navigation_markers)


def _acid_required_words(acid: str) -> set[str]:
    required = {
        "US IT EQ": {"technology", "tech", "information", "software", "semiconductor", "semiconductors", "ai", "data", "capex"},
        "US LRG G EQ": {"growth", "large", "cap", "magnificent", "megacap", "mega", "technology", "ai", "valuation"},
        "US LRG EQ": {"large", "cap", "s&p", "sp500", "broad", "earnings", "valuation"},
        "US ID EQ": {"industrial", "industrials", "manufacturing", "orders", "pmi", "capex", "cyclical", "defense", "aerospace"},
    }
    return required.get(acid, set())


def _dedupe_text(values: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for value in values:
        key = _clean_text(value).lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(value)
    return deduped


def _is_duplicate_snippet(candidate: str, existing: list[str]) -> bool:
    candidate_key = _clean_text(candidate).lower()
    candidate_words = set(_keywords(candidate_key))
    for snippet in existing:
        snippet_key = _clean_text(snippet).lower()
        if candidate_key in snippet_key or snippet_key in candidate_key:
            return True
        snippet_words = set(_keywords(snippet_key))
        if candidate_words and snippet_words:
            overlap = len(candidate_words.intersection(snippet_words)) / max(1, min(len(candidate_words), len(snippet_words)))
            if overlap >= 0.85:
                return True
    return False


def _expanded_query_words(query: str) -> set[str]:
    words = set(_keywords(query))
    synonyms = {
        "technology": {"tech", "information", "semiconductor", "software", "hardware"},
        "tech": {"technology", "information", "semiconductor", "software", "hardware"},
        "earnings": {"eps", "profit", "profits", "estimate", "estimates", "guidance", "revision", "revisions"},
        "revisions": {"revision", "estimate", "estimates", "guidance", "earnings", "eps"},
        "capex": {"capex", "capital", "expenditure", "expenditures", "spending", "investment"},
        "ai": {"artificial", "intelligence", "capex", "spending", "investment"},
        "growth": {"earnings", "revenue", "sales", "profit"},
        "industrial": {"industrials", "manufacturing", "orders", "pmi", "cyclical"},
        "industrials": {"industrial", "manufacturing", "orders", "pmi", "cyclical"},
    }
    expanded = set(words)
    for word in words:
        expanded.update(synonyms.get(word, set()))
    return expanded


def _keywords(text: str) -> list[str]:
    stop_words = {"the", "and", "for", "with", "from", "this", "that", "about", "market", "markets", "equity", "equities"}
    return [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())
        if len(word) >= 3 and word not in stop_words
    ]


def _html_metadata(html: str) -> dict[str, str]:
    title = ""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if title_match:
        title = _clean_text(re.sub(r"<[^>]+>", " ", title_match.group(1)))
    description = ""
    desc_match = re.search(
        r"<meta\b(?=[^>]*name=[\"']description[\"'])(?=[^>]*content=[\"']([^\"']+)[\"'])[^>]*>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if desc_match:
        description = _clean_text(desc_match.group(1))
    return {"title": title, "description": description}


def _scope(defaults: SearchDefaults, *, source: dict[str, Any]) -> tuple[str, str]:
    if defaults.acid:
        return "acid", defaults.acid
    if defaults.comparison_group:
        return "comparison_group", defaults.comparison_group
    if defaults.fund:
        return "fund", defaults.fund
    return source.get("default_scope_type", "market"), source.get("default_scope_value", "")


def _read_existing_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        row_id = row.get("row_id", "")
        if row_id:
            deduped[row_id] = row
    return list(deduped.values())


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _require_iso_date(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")
    date.fromisoformat(value)


__all__ = ["SearchDefaults", "search_market_context_web"]
