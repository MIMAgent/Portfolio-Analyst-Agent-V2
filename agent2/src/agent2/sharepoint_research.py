"""Match ACIDs to SharePoint-synced research decks and extract compact slide context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Any
from xml.etree import ElementTree
from zipfile import ZipFile


DEFAULT_SHAREPOINT_RESEARCH_ROOT = Path(
    r"C:\Users\schuri2\MORNINGSTAR INC\MIM Global Research - Final Research (yyyymm-AC-ACID-project title)"
)

POWERPOINT_EXTENSIONS = {".pptx", ".ppt"}

ACID_ALIASES: dict[str, list[str]] = {
    "US IT EQ": ["US IT", "INFORMATION TECHNOLOGY"],
    "US ID EQ": ["US ID", "INDUSTRIALS"],
    "US FN EQ": ["US FN", "FINANCIALS"],
    "US HC EQ": ["US HC", "HEALTH CARE"],
    "US CD EQ": ["US CD", "CONSUMER DISCRETIONARY"],
    "US CS EQ": ["US CS", "COMMUNICATION SERVICES"],
    "US EN EQ": ["US EN", "ENERGY"],
    "US MT EQ": ["US MT", "MATERIALS"],
    "US TL EQ": ["US TL", "TECH LEADERS", "INFORMATION TECHNOLOGY"],
    "US UT EQ": ["US UT", "UTILITIES"],
    "US RE EQ": ["US RE", "REAL ESTATE"],
    "US EQ": ["US EQ", "UNITED STATES"],
    "US LRG G EQ": ["US LRG G", "US LARGE GROWTH", "US LG"],
    "US LRG V EQ": ["US LRG V", "US LARGE VALUE", "US LV"],
    "US LRG EQ": ["US LRG", "US LARGE"],
    "US MID G EQ": ["US MID G", "US MID GROWTH", "US MG"],
    "US MID V EQ": ["US MID V", "US MID VALUE", "US MV"],
    "US MID EQ": ["US MID"],
    "US SML G EQ": ["US SML G", "US SMALL GROWTH", "US SM G"],
    "US SML V EQ": ["US SML V", "US SMALL VALUE", "US SM V"],
    "US SML EQ": ["US SML", "US SMALL", "US SM"],
    "JP EQ": ["JP EQ", "JAPAN"],
    "UK EQ": ["UK EQ", "UNITED KINGDOM"],
    "EM EQ": ["EM EQ", "EMERGING MARKETS"],
    "EU EQ": ["EU EQ", "EUROPE"],
    "TW EQ": ["TW EQ", "TAIWAN"],
    "CN EQ": ["CN EQ", "CHINA"],
    "BR EQ": ["BR EQ", "BRAZIL"],
}

STYLE_CONFLICTS = [
    ("LRG G", "LRG V"),
    ("MID G", "MID V"),
    ("SML G", "SML V"),
    ("GROWTH", "VALUE"),
]

SLIDE_TEXT_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


@dataclass(frozen=True)
class ResearchCandidate:
    folder_name: str
    file_name: str
    full_path: str
    extension: str
    folder_month: str
    last_modified: str
    folder_normalized: str
    file_normalized: str


def build_research_index(
    root_dir: str | Path | None = DEFAULT_SHAREPOINT_RESEARCH_ROOT,
) -> list[ResearchCandidate]:
    root = Path(root_dir) if root_dir else None
    if not root or not root.exists():
        return []

    candidates: list[ResearchCandidate] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in POWERPOINT_EXTENSIONS:
            continue
        folder_name = path.parent.name
        file_name = path.name
        try:
            last_modified = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        except OSError:
            last_modified = ""
        candidates.append(
            ResearchCandidate(
                folder_name=folder_name,
                file_name=file_name,
                full_path=str(path),
                extension=path.suffix.lower(),
                folder_month=_extract_month(folder_name or file_name),
                last_modified=last_modified,
                folder_normalized=_normalize_text(folder_name),
                file_normalized=_normalize_text(file_name),
            )
        )
    return candidates


def match_research_for_position(
    *,
    acid: str,
    label: str,
    research_index: list[ResearchCandidate],
) -> dict[str, Any]:
    if not research_index:
        return _empty_match(acid)

    scored_matches: list[dict[str, Any]] = []
    for candidate in research_index:
        scored = _score_candidate(acid=acid, label=label, candidate=candidate)
        if scored is not None:
            scored_matches.append(scored)

    scored_matches.sort(
        key=lambda item: (
            item["score"],
            item["folder_month"],
            1 if item["extension"] == ".pptx" else 0,
            item["last_modified"],
        ),
        reverse=True,
    )

    if not scored_matches:
        return _empty_match(acid)

    primary = scored_matches[0]
    extracted = extract_pptx_research_context(primary["full_path"]) if primary["extension"] == ".pptx" else {}
    confidence = min(0.99, max(0.5, primary["score"] / 100.0))
    return {
        "acid": acid,
        "match_status": "matched",
        "matched_via": primary["matched_via"],
        "matched_token": primary["matched_token"],
        "confidence": round(confidence, 3),
        "primary_match": primary,
        "secondary_matches": scored_matches[1:4],
        "extracted_context": extracted,
    }


def extract_pptx_research_context(path: str | Path, *, max_slides: int = 6, max_chars: int = 2200) -> dict[str, Any]:
    pptx_path = Path(path)
    if not pptx_path.exists() or pptx_path.suffix.lower() != ".pptx":
        return {
            "slide_count": 0,
            "slide_titles": [],
            "summary_text": "",
        }

    slide_texts: list[str] = []
    slide_titles: list[str] = []
    try:
        with ZipFile(pptx_path) as archive:
            slide_names = sorted(
                [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)],
                key=_slide_sort_key,
            )
            for slide_name in slide_names[:max_slides]:
                xml_text = archive.read(slide_name)
                root = ElementTree.fromstring(xml_text)
                fragments = [
                    node.text.strip()
                    for node in root.findall(".//a:t", SLIDE_TEXT_NS)
                    if node.text and node.text.strip()
                ]
                if not fragments:
                    continue
                slide_text = " ".join(fragments)
                slide_texts.append(slide_text)
                slide_titles.append(fragments[0][:120])
    except Exception:
        return {
            "slide_count": 0,
            "slide_titles": [],
            "summary_text": "",
        }

    summary_text = " ".join(slide_texts)
    summary_text = re.sub(r"\s+", " ", summary_text).strip()
    if len(summary_text) > max_chars:
        summary_text = summary_text[: max_chars - 3].rstrip() + "..."

    return {
        "slide_count": len(slide_texts),
        "slide_titles": slide_titles,
        "summary_text": summary_text,
    }


def _empty_match(acid: str) -> dict[str, Any]:
    return {
        "acid": acid,
        "match_status": "unmatched",
        "matched_via": "",
        "matched_token": "",
        "confidence": 0.0,
        "primary_match": None,
        "secondary_matches": [],
        "extracted_context": {
            "slide_count": 0,
            "slide_titles": [],
            "summary_text": "",
        },
    }


def _score_candidate(*, acid: str, label: str, candidate: ResearchCandidate) -> dict[str, Any] | None:
    acid_normalized = _normalize_text(acid)
    label_normalized = _normalize_text(label)
    combined = f"{candidate.folder_normalized} {candidate.file_normalized}".strip()

    if _has_style_conflict(acid_normalized, combined) or _has_style_conflict(label_normalized, combined):
        return None

    best_score = -1.0
    matched_via = ""
    matched_token = ""

    for token, mode in _candidate_tokens(acid=acid, label=label):
        folder_hit = token in candidate.folder_normalized
        file_hit = token in candidate.file_normalized
        if not folder_hit and not file_hit:
            continue

        if mode == "exact" and folder_hit:
            score = 100.0
        elif mode == "exact" and file_hit:
            score = 95.0
        elif mode == "alias" and folder_hit:
            score = 85.0
        elif mode == "alias" and file_hit:
            score = 80.0
        else:
            score = 60.0

        if folder_hit and file_hit:
            score += 5.0
        score += _month_score(candidate.folder_month)
        if candidate.extension == ".pptx":
            score += 3.0
        elif candidate.extension == ".ppt":
            score += 1.0

        if score > best_score:
            best_score = score
            matched_via = mode
            matched_token = token

    if best_score < 0:
        return None

    return {
        "folder_month": candidate.folder_month,
        "folder_name": candidate.folder_name,
        "file_name": candidate.file_name,
        "full_path": candidate.full_path,
        "extension": candidate.extension,
        "last_modified": candidate.last_modified,
        "score": round(best_score, 3),
        "matched_via": matched_via,
        "matched_token": matched_token,
    }


def _candidate_tokens(*, acid: str, label: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    acid_normalized = _normalize_text(acid)
    label_normalized = _normalize_text(label)

    if acid_normalized:
        tokens.append((acid_normalized, "exact"))
    for alias in ACID_ALIASES.get(acid, []):
        normalized_alias = _normalize_text(alias)
        if normalized_alias:
            tokens.append((normalized_alias, "alias"))
    if label_normalized:
        tokens.append((label_normalized, "alias"))

    acid_parts = acid_normalized.split()
    if acid_parts and acid_parts[-1] in {"EQ", "FI", "FX"}:
        fallback = " ".join(acid_parts[:-1]).strip()
        if fallback:
            tokens.append((fallback, "normalized"))

    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def _normalize_text(value: str) -> str:
    value = value.upper()
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"[^A-Z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _extract_month(value: str) -> str:
    match = re.match(r"^(\d{6})", value)
    return match.group(1) if match else ""


def _month_score(yyyymm: str) -> float:
    if not yyyymm:
        return 0.0
    try:
        dt = datetime.strptime(yyyymm, "%Y%m")
    except ValueError:
        return 0.0
    base = datetime(2000, 1, 1)
    return min(10.0, max(0.0, (dt - base).days / 3650))


def _has_style_conflict(reference: str, candidate: str) -> bool:
    if not reference:
        return False
    for lhs, rhs in STYLE_CONFLICTS:
        if lhs in reference and rhs in candidate:
            return True
        if rhs in reference and lhs in candidate:
            return True
    return False


def _slide_sort_key(value: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", value)
    return int(match.group(1)) if match else 0
