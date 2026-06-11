"""Retrieve relevant internal-history context from ingested IC checklist records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import re
from typing import Any


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "what",
    "have",
    "your",
    "fund",
    "funds",
    "against",
    "about",
    "would",
    "their",
    "they",
    "were",
    "will",
    "when",
    "where",
    "which",
    "does",
    "hold",
    "risk",
    "largest",
    "relative",
    "overweight",
    "underweight",
    "give",
    "both",
    "position",
    "current",
    "proposed",
    "moves",
    "move",
    "being",
    "into",
    "within",
}


@dataclass(frozen=True)
class SectionMatch:
    document_date: str
    source_filename: str
    section_key: str
    section_label: str
    prompt: str
    body_text: str
    score: float
    matched_terms: list[str]
    related_themes: list[str]


def load_internal_history(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_recurring_themes(
    payload: dict[str, Any],
    *,
    fund: str,
    before_date: str | None = None,
) -> list[dict[str, Any]]:
    documents = _filter_documents(payload, fund=fund, before_date=before_date)
    counts = Counter()
    theme_examples: dict[str, dict[str, Any]] = {}
    for document in documents:
        for theme in document.get("themes", []):
            theme_id = theme.get("theme_id", "")
            if not theme_id:
                continue
            counts[theme_id] += 1
            theme_examples.setdefault(
                theme_id,
                {
                    "theme_id": theme_id,
                    "label": theme.get("label", ""),
                    "join_hints": theme.get("join_hints", {}),
                },
            )
    return [
        {
            **theme_examples[theme_id],
            "occurrence_count": count,
        }
        for theme_id, count in counts.most_common()
    ]


def retrieve_relevant_history(
    payload: dict[str, Any],
    *,
    fund: str,
    query: str = "",
    theme_ids: list[str] | None = None,
    section_keys: list[str] | None = None,
    before_date: str | None = None,
    max_sections: int = 8,
) -> dict[str, Any]:
    documents = _filter_documents(payload, fund=fund, before_date=before_date)
    query_terms = _tokenize(query)
    requested_theme_ids = set(theme_ids or [])
    requested_section_keys = set(section_keys or [])

    matches: list[SectionMatch] = []
    for document in documents:
        section_theme_map = _build_section_theme_map(document)
        for section in document.get("sections", []):
            score, matched_terms, related_themes = _score_section(
                section,
                query_terms=query_terms,
                requested_theme_ids=requested_theme_ids,
                requested_section_keys=requested_section_keys,
                section_theme_map=section_theme_map,
                document_date=document.get("document_date", ""),
            )
            if score <= 0:
                continue
            matches.append(
                SectionMatch(
                    document_date=document.get("document_date", ""),
                    source_filename=document.get("source_filename", ""),
                    section_key=section.get("section_key", ""),
                    section_label=section.get("section_label", ""),
                    prompt=section.get("prompt", ""),
                    body_text=section.get("body_text", ""),
                    score=score,
                    matched_terms=matched_terms,
                    related_themes=related_themes,
                )
            )

    matches.sort(key=lambda item: (-item.score, _sortable_date(item.document_date), item.source_filename))
    selected = matches[:max_sections]

    return {
        "fund": fund,
        "query": query,
        "theme_ids": sorted(requested_theme_ids),
        "section_keys": sorted(requested_section_keys),
        "before_date": before_date or "",
        "recurring_themes": summarize_recurring_themes(payload, fund=fund, before_date=before_date),
        "matches": [
            {
                "document_date": match.document_date,
                "source_filename": match.source_filename,
                "section_key": match.section_key,
                "section_label": match.section_label,
                "prompt": match.prompt,
                "body_text": match.body_text,
                "score": round(match.score, 3),
                "matched_terms": match.matched_terms,
                "related_themes": match.related_themes,
            }
            for match in selected
        ],
    }


def _filter_documents(payload: dict[str, Any], *, fund: str, before_date: str | None) -> list[dict[str, Any]]:
    cutoff = _parse_date(before_date) if before_date else None
    filtered = []
    for document in payload.get("documents", []):
        if document.get("fund") != fund:
            continue
        document_date = _parse_date(document.get("document_date", ""))
        if cutoff and document_date and document_date >= cutoff:
            continue
        filtered.append(document)
    return filtered


def _build_section_theme_map(document: dict[str, Any]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for theme in document.get("themes", []):
        theme_id = theme.get("theme_id", "")
        for match in theme.get("matches", []):
            section_key = match.get("section_key", "")
            if section_key:
                mapping.setdefault(section_key, []).append(theme_id)
    return mapping


def _score_section(
    section: dict[str, Any],
    *,
    query_terms: set[str],
    requested_theme_ids: set[str],
    requested_section_keys: set[str],
    section_theme_map: dict[str, list[str]],
    document_date: str,
) -> tuple[float, list[str], list[str]]:
    section_key = section.get("section_key", "")
    related_themes = section_theme_map.get(section_key, [])
    text = " ".join([section.get("prompt", ""), section.get("body_text", "")])
    section_terms = _tokenize(text)

    score = 0.0
    matched_terms: list[str] = []

    if query_terms:
        term_overlap = sorted(query_terms.intersection(section_terms))
        if term_overlap:
            matched_terms = term_overlap
            score += len(term_overlap) * 2.0
    else:
        score += 0.5

    if requested_theme_ids:
        theme_overlap = sorted(requested_theme_ids.intersection(related_themes))
        if theme_overlap:
            score += len(theme_overlap) * 3.0
        else:
            return 0.0, matched_terms, related_themes

    if requested_section_keys:
        if section_key in requested_section_keys:
            score += 2.5
        else:
            return 0.0, matched_terms, related_themes

    if not query_terms and not requested_theme_ids and not requested_section_keys:
        score += 1.0

    score += _recency_bonus(document_date)
    return score, matched_terms, related_themes


def _tokenize(value: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1 and token not in STOP_WORDS
    }
    return tokens


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m/%d/%Y", "%m/%d/%Y", "%m/%-d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    parts = re.findall(r"\d+", value)
    if len(parts) == 3:
        month, day, year = parts
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None
    return None


def _sortable_date(value: str) -> tuple[int, int, int]:
    parsed = _parse_date(value)
    if parsed is None:
        return (0, 0, 0)
    return (parsed.year, parsed.month, parsed.day)


def _recency_bonus(value: str) -> float:
    parsed = _parse_date(value)
    if parsed is None:
        return 0.0
    return parsed.toordinal() / 1_000_000.0
