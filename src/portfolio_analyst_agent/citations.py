"""Citation token parsing, resolution, and narrative enforcement."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from .csv_sources import open_csv_text
from .evidence import stable_row_id
from .memory_store import DEFAULT_MEMORY_PATH


CITATION_PATTERN = re.compile(r"(csv:[^\s\]\)]+|mem:[^\s\]\)]+|deriv:[^\s\]\)]+|trigger:[^\s\]\)]+)")
TRAILING_TOKEN_PUNCTUATION = ".,;:"
NARRATIVE_FIELD_NAMES = {
    "challenge",
    "challenge_text",
    "cleaner_expression",
    "decomposition_narrative",
    "disagreement_statement",
    "executive_summary",
    "falsification_framing",
    "fundamental_readthrough",
    "headline",
    "lineage_notes",
    "narrative",
    "pm_question",
    "pm_takeaway",
    "reason",
    "review_question",
    "resolution_text",
    "watch_text",
    "what_would_change_view",
}


class CitationError(ValueError):
    """Raised when a citation token is malformed or cannot resolve."""


def extract_tokens(text: str) -> list[str]:
    return [_clean_token(token) for token in CITATION_PATTERN.findall(text or "")]


def resolve_token(token: str, *, memory_path: str | Path = DEFAULT_MEMORY_PATH) -> bool:
    token = _clean_token(token)
    if token.startswith("csv:"):
        return _resolve_csv_token(token)
    if token.startswith("mem:"):
        return _resolve_memory_token(token, memory_path=memory_path)
    if token.startswith("deriv:"):
        return _resolve_derivation_token(token, memory_path=memory_path)
    if token.startswith("trigger:"):
        return _resolve_trigger_token(token)
    raise CitationError(f"Unsupported citation token: {token}")


def enforce_payload_citations(
    payload: dict[str, Any],
    *,
    memory_path: str | Path = DEFAULT_MEMORY_PATH,
) -> None:
    """Require every narrative field to contain at least one resolvable token."""

    failures: list[str] = []
    for field_path, value in _iter_narrative_strings(payload):
        tokens = extract_tokens(value)
        if not tokens:
            failures.append(f"{field_path}: missing citation token")
            continue
        for token in tokens:
            try:
                resolve_token(token, memory_path=memory_path)
            except (CitationError, FileNotFoundError, ValueError) as exc:
                failures.append(f"{field_path}: {token}: {exc}")
    for field_path, token in _iter_evidence_pointer_tokens(payload):
        try:
            resolve_token(token, memory_path=memory_path)
        except (CitationError, FileNotFoundError, ValueError) as exc:
            failures.append(f"{field_path}: {token}: {exc}")
    if failures:
        raise CitationError("; ".join(failures))


def _resolve_csv_token(token: str) -> bool:
    ref = token.removeprefix("csv:")
    path_text, marker, fragment = ref.partition("#")
    if marker != "#" or not fragment.startswith("row_id="):
        raise CitationError("CSV citation must use csv:<path>#row_id=<id>.")
    row_id = fragment.removeprefix("row_id=")
    if not row_id:
        raise CitationError("CSV citation row_id is empty.")

    with open_csv_text(Path(path_text)) as handle:
        for row in csv.DictReader(handle):
            generated_row_id = stable_row_id(row, namespace=Path(path_text).as_posix())
            if row.get("row_id") == row_id or generated_row_id == row_id:
                return True
    raise CitationError(f"CSV row_id not found: {row_id}")


def _clean_token(token: str) -> str:
    return token.strip().rstrip(TRAILING_TOKEN_PUNCTUATION)


def _resolve_memory_token(token: str, *, memory_path: str | Path) -> bool:
    ref = token.removeprefix("mem:")
    table, marker, record_id = ref.partition("#")
    if marker != "#" or not table or not record_id:
        raise CitationError("Memory citation must use mem:<table>#<record_id>.")

    raw_payload = _load_memory_payload(memory_path)
    rows = raw_payload.get("tables", {}).get(table, [])
    id_field = {
        "thesis_ledger": "thesis_id",
        "open_challenges": "challenge_id",
        "exceptions": "exception_id",
        "watch_items": "watch_item_id",
    }.get(table)
    if id_field is None:
        raise CitationError(f"Unsupported memory table: {table}")
    if any(row.get(id_field) == record_id for row in rows):
        return True
    raise CitationError(f"Memory record not found: {record_id}")


def _resolve_derivation_token(token: str, *, memory_path: str | Path) -> bool:
    ref = token.removeprefix("deriv:")
    formula, marker, query = ref.partition("?")
    if not formula:
        raise CitationError("Derivation citation formula name is empty.")
    if marker != "?":
        raise CitationError("Derivation citation must include ?inputs=<refs>.")
    inputs = parse_qs(query).get("inputs", [])
    if not inputs:
        raise CitationError("Derivation citation inputs are empty.")
    input_tokens = [value.strip() for raw in inputs for value in raw.split(",") if value.strip()]
    if not input_tokens:
        raise CitationError("Derivation citation inputs are empty.")
    return all(resolve_token(input_token, memory_path=memory_path) for input_token in input_tokens)


def _resolve_trigger_token(token: str) -> bool:
    ref = token.removeprefix("trigger:")
    tool_version, marker, trigger_id = ref.partition("#")
    if marker != "#" or not tool_version or not trigger_id:
        raise CitationError("Trigger citation must use trigger:<tool_version>#<trigger_candidate_id>.")
    if not tool_version.startswith("evaluate_challenge_triggers_"):
        raise CitationError(f"Unsupported trigger tool version: {tool_version}")
    if not trigger_id.startswith("trig_"):
        raise CitationError(f"Invalid trigger candidate id: {trigger_id}")
    return True


def _iter_narrative_strings(value: Any, *, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in NARRATIVE_FIELD_NAMES and isinstance(child, str) and child.strip():
                yield child_path, child
            else:
                yield from _iter_narrative_strings(child, path=child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_narrative_strings(child, path=f"{path}[{index}]")


def _iter_evidence_pointer_tokens(value: Any, *, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "evidence_pointers" and isinstance(child, list):
                for index, pointer in enumerate(child):
                    pointer_path = f"{child_path}[{index}]"
                    if not isinstance(pointer, dict):
                        yield pointer_path, "csv:#row_id="
                        continue
                    artifact_path = str(pointer.get("artifact_path", "")).strip()
                    row_id = str(pointer.get("row_id", "")).strip()
                    if not artifact_path and not row_id:
                        continue
                    yield pointer_path, f"csv:{artifact_path}#row_id={row_id}"
            else:
                yield from _iter_evidence_pointer_tokens(child, path=child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_evidence_pointer_tokens(child, path=f"{path}[{index}]")


def _load_memory_payload(memory_path: str | Path) -> dict[str, Any]:
    path = Path(memory_path)
    if not path.exists():
        return {"tables": {}}
    import json

    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["CitationError", "enforce_payload_citations", "extract_tokens", "resolve_token"]
