"""Ingest old mutual fund checklist DOCX files into structured internal-history records."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class SectionDefinition:
    key: str
    label: str
    starts_with: tuple[str, ...]


SECTION_DEFINITIONS = (
    SectionDefinition(
        key="benchmark_relative_overweights_underweights",
        label="Benchmark Relative Overweights And Underweights",
        starts_with=("what are the fund s largest benchmark relative overweight and underweight",),
    ),
    SectionDefinition(
        key="offsets_for_largest_overweight",
        label="Offsets For Largest Overweight",
        starts_with=("what offsets does the fund hold to mitigate the risk of the largest overweight",),
    ),
    SectionDefinition(
        key="algo_relative_overweights_underweights",
        label="Algo Relative Overweights And Underweights",
        starts_with=("what are the fund s largest algo relative overweight and underweight",),
    ),
    SectionDefinition(
        key="fund_specific_range_usage",
        label="Fund Specific Range Usage",
        starts_with=("what percentage of your allowable range is your largest overweight",),
    ),
    SectionDefinition(
        key="directional_moves_rationale",
        label="Directional Moves And Rationale",
        starts_with=("what moves are you making and what is your rationale",),
    ),
    SectionDefinition(
        key="range_of_added_positions",
        label="Range Of Added Positions",
        starts_with=("what percentage of your range are you now holding in the sectors countries etc that you are adding to",),
    ),
    SectionDefinition(
        key="what_would_need_to_happen_to_add",
        label="What Would Need To Happen To Add",
        starts_with=("what would need to happen for you to add further to this position",),
    ),
    SectionDefinition(
        key="considered_but_not_done",
        label="Considered But Not Done",
        starts_with=("what moves did you consider but decide against",),
    ),
    SectionDefinition(
        key="robustness_best_worst_environment",
        label="Robustness Best And Worst Environment",
        starts_with=("what macroeconomic environment do you believe your portfolio is best and worst positioned for",),
    ),
    SectionDefinition(
        key="vulnerability_room_to_move",
        label="Vulnerability Room To Move",
        starts_with=("if the environment that the portfolio is most vulnerable to plays out",),
    ),
    SectionDefinition(
        key="miscellaneous_comments",
        label="Miscellaneous Comments",
        starts_with=("what further comments would you like to make on current positioning and the proposed moves",),
    ),
    SectionDefinition(
        key="roadmap",
        label="Roadmap",
        starts_with=("roadmap",),
    ),
)


THEME_DEFINITIONS = (
    {
        "theme_id": "information_technology_underweight",
        "label": "Information Technology Underweight",
        "patterns": (r"\binformation technology\b", r"\bit underweight\b", r"\bmag 7\b", r"\bapple\b", r"\bsoftware\b", r"\bsemiconductor\b"),
        "join_hints": {"acid_candidates": ["US IT"], "categories": ["Eq Sector"]},
    },
    {
        "theme_id": "smid_overweight",
        "label": "SMID Overweight",
        "patterns": (r"\bsmid overweight\b", r"\bsmall cap\b", r"\bmid cap\b", r"\bsmall caps\b"),
        "join_hints": {"acid_candidates": ["US MID EQ", "US SML EQ"], "categories": ["Eq Size / Style"]},
    },
    {
        "theme_id": "industrials_overweight",
        "label": "Industrials Overweight",
        "patterns": (r"\bindustrials\b",),
        "join_hints": {"acid_candidates": ["US ID EQ"], "categories": ["Eq Sector"]},
    },
    {
        "theme_id": "financials_overweight",
        "label": "Financials Overweight",
        "patterns": (r"\bfinancials\b", r"\bbank of america\b", r"\bwells fargo\b", r"\bblackrock\b", r"\bvisa\b"),
        "join_hints": {"acid_candidates": ["US FN EQ"], "categories": ["Eq Sector"]},
    },
    {
        "theme_id": "ai_leadership_risk",
        "label": "AI Leadership Risk",
        "patterns": (r"\bai\b", r"\bmag 7\b", r"\belite 8\b", r"\bnvidia\b", r"\bbroadcom\b"),
        "join_hints": {"acid_candidates": ["US IT"], "categories": ["Eq Sector"]},
    },
    {
        "theme_id": "subadvisor_and_sleeve_structure",
        "label": "Subadvisor And Sleeve Structure",
        "patterns": (r"\bsubadvisor", r"\bsubadvisors\b", r"\bsleeve\b", r"\bcompletion portfolio\b", r"\bopp value\b", r"\bclearbridge\b", r"\bwasatch\b"),
        "join_hints": {"acid_candidates": [], "categories": []},
    },
    {
        "theme_id": "value_tilt",
        "label": "Value Tilt",
        "patterns": (r"\bvalue\b", r"\bgrowth\b", r"\bstyle\b"),
        "join_hints": {"acid_candidates": ["US LRG V EQ", "US MID V EQ", "US SML V EQ"], "categories": ["Eq Size / Style"]},
    },
)


def ingest_checklist_doc(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    paragraphs = _read_docx_paragraphs(source_path)
    metadata = _extract_metadata(paragraphs)
    trade_proposal = _extract_trade_proposal(paragraphs)
    sections = _extract_sections(paragraphs)
    themes = _extract_themes(sections)

    return {
        "source_path": str(source_path),
        "source_filename": source_path.name,
        "document_type": "mutual_fund_checklist",
        "fund": metadata.get("fund", ""),
        "document_date": metadata.get("date", ""),
        "pm_names": metadata.get("pm_names", []),
        "trade_proposal": trade_proposal,
        "sections": sections,
        "themes": themes,
        "document_summary": _build_document_summary(metadata, trade_proposal, sections, themes),
    }


def ingest_many_checklists(paths: list[str | Path]) -> dict[str, Any]:
    documents = [ingest_checklist_doc(path) for path in paths]
    theme_counter = Counter()
    for document in documents:
        theme_counter.update(theme["theme_id"] for theme in document.get("themes", []))

    return {
        "document_count": len(documents),
        "documents": documents,
        "recurring_themes": [
            {"theme_id": theme_id, "occurrence_count": count}
            for theme_id, count in theme_counter.most_common()
        ],
    }


def write_ingestion_outputs(payload: dict[str, Any], *, output_json: str | Path, output_jsonl: str | Path) -> None:
    output_json = Path(output_json)
    output_jsonl = Path(output_jsonl)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for document in payload.get("documents", []):
            handle.write(json.dumps(document) + "\n")


def _read_docx_paragraphs(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NAMESPACE)]
        text = "".join(texts).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def _extract_metadata(paragraphs: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {"fund": "", "date": "", "pm_names": []}
    for index, paragraph in enumerate(paragraphs[:-1]):
        normalized = _normalize(paragraph)
        value = paragraphs[index + 1].strip()
        if normalized == "fund" and not metadata["fund"]:
            metadata["fund"] = value
        elif normalized == "date" and not metadata["date"]:
            metadata["date"] = value
        elif normalized in {"pm s", "pms"} and not metadata["pm_names"]:
            metadata["pm_names"] = [item.strip() for item in value.split(",") if item.strip()]
    return metadata


def _extract_trade_proposal(paragraphs: list[str]) -> dict[str, Any]:
    start = _find_first_index(paragraphs, lambda value: _normalize(value) == "trade proposal")
    end = _find_first_index(paragraphs, lambda value: _normalize(value).startswith("blank sheet of paper questions"))
    body = []
    if start is not None and end is not None and end > start:
        body = [paragraphs[index].strip() for index in range(start + 1, end) if paragraphs[index].strip()]
    return {
        "status": "none" if not body or all(_normalize(item) in {"na", "no trades proposed"} or "no trades proposed" in _normalize(item) for item in body) else "present",
        "items": body,
        "summary": " ".join(body).strip(),
    }


def _extract_sections(paragraphs: list[str]) -> list[dict[str, Any]]:
    start = _find_first_index(paragraphs, lambda value: _normalize(value).startswith("blank sheet of paper questions"))
    if start is None:
        return []

    candidates: list[tuple[int, SectionDefinition]] = []
    for index in range(start + 1, len(paragraphs)):
        normalized = _normalize(paragraphs[index])
        for definition in SECTION_DEFINITIONS:
            if any(normalized.startswith(prefix) for prefix in definition.starts_with):
                candidates.append((index, definition))
                break

    sections: list[dict[str, Any]] = []
    for position, (index, definition) in enumerate(candidates):
        next_index = candidates[position + 1][0] if position + 1 < len(candidates) else len(paragraphs)
        body = [paragraphs[item].strip() for item in range(index + 1, next_index) if paragraphs[item].strip()]
        sections.append(
            {
                "section_key": definition.key,
                "section_label": definition.label,
                "prompt": paragraphs[index].strip(),
                "body_paragraphs": body,
                "body_text": " ".join(body).strip(),
            }
        )
    return sections


def _extract_themes(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []
    for definition in THEME_DEFINITIONS:
        matches = []
        compiled_patterns = [re.compile(pattern, flags=re.IGNORECASE) for pattern in definition["patterns"]]
        for section in sections:
            text = section.get("body_text", "")
            if any(pattern.search(text) for pattern in compiled_patterns):
                matches.append(
                    {
                        "section_key": section["section_key"],
                        "evidence_excerpt": _truncate(section["body_text"], 220),
                    }
                )
        if matches:
            themes.append(
                {
                    "theme_id": definition["theme_id"],
                    "label": definition["label"],
                    "join_hints": definition["join_hints"],
                    "matches": matches,
                }
            )
    return themes


def _build_document_summary(
    metadata: dict[str, Any],
    trade_proposal: dict[str, Any],
    sections: list[dict[str, Any]],
    themes: list[dict[str, Any]],
) -> dict[str, Any]:
    section_keys = [section["section_key"] for section in sections]
    return {
        "fund": metadata.get("fund", ""),
        "document_date": metadata.get("date", ""),
        "pm_names": metadata.get("pm_names", []),
        "trade_status": trade_proposal.get("status", ""),
        "section_count": len(sections),
        "section_keys": section_keys,
        "theme_ids": [theme["theme_id"] for theme in themes],
    }


def _find_first_index(values: list[str], predicate: Any) -> int | None:
    for index, value in enumerate(values):
        if predicate(value):
            return index
    return None


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else f"{value[: limit - 3].rstrip()}..."
