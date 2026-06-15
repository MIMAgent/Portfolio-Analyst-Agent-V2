"""Lightweight payload validators for Model 1 write tools."""

from __future__ import annotations

from typing import Any


class SchemaValidationError(ValueError):
    """Raised when an output payload does not match the v1 contract."""


COMMON_HEADER_FIELDS = ("fund", "snapshot_date", "as_of_date", "review_run_id")
PM_CHALLENGE_TEXT_FIELDS = (
    "challenge_headline",
    "thesis_under_pressure",
    "positioning_tension",
    "model_signal_tension",
    "vir_decomposition_readthrough",
    "market_context_readthrough",
    "pm_decision_fork",
    "primary_pm_question",
    "evidence_needed_next",
    "source_quality",
)
GENERIC_PM_QUESTION_PATTERNS = (
    "is this still intentional",
    "why is this still overweight",
    "why is the fund still overweight",
    "why is this still underweight",
    "why is the fund still underweight",
)


def validate_change_brief(payload: dict[str, Any], *, fund: str) -> None:
    _require_mapping(payload, "content")
    _validate_header(
        payload.get("header"),
        fund=fund,
        required=COMMON_HEADER_FIELDS
        + ("prior_snapshot_date", "parser_version", "mapping_version", "governance_version", "algo_version", "run_mode"),
    )
    _require_text(payload, "executive_summary")
    _require_list(payload, "material_movers")
    _require_mapping(payload.get("sizing_artifact_summary"), "sizing_artifact_summary")
    _require_mapping(payload.get("memory_updates_summary"), "memory_updates_summary")
    _require_mapping(payload.get("triggers_fired_summary"), "triggers_fired_summary")
    _require_list(payload, "evidence_index")
    for index, item in enumerate(payload.get("material_movers", [])):
        _require_mapping(item, f"material_movers[{index}]")
        _require_text(item, "acid")
        _require_text(item, "narrative")
        _require_list(item, "evidence_pointers")


def validate_sizing_considerations(payload: dict[str, Any], *, fund: str) -> None:
    _require_mapping(payload, "content")
    _validate_header(
        payload.get("header"),
        fund=fund,
        required=COMMON_HEADER_FIELDS + ("algo_version", "mapping_version", "run_mode"),
    )
    _require_mapping(payload.get("perspective_summary"), "perspective_summary")
    for field in ("algo_vs_positioning_agreement", "algo_vs_positioning_disagreement", "largest_algo_mom_changes"):
        _require_list(payload, field)
        for index, item in enumerate(payload.get(field, [])):
            _require_mapping(item, f"{field}[{index}]")
            _require_text(item, "acid")
            _require_text(item, "narrative")
            _require_list(item, "evidence_pointers")
    _require_list(payload, "evidence_index")


def validate_challenge_brief(
    payload: dict[str, Any],
    *,
    fund: str,
    fired_trigger_ids: set[str] | None = None,
    fired_trigger_types: dict[str, str] | None = None,
) -> None:
    _require_mapping(payload, "content")
    _validate_header(
        payload.get("header"),
        fund=fund,
        required=COMMON_HEADER_FIELDS + ("parser_version", "mapping_version", "governance_version"),
    )
    items = _require_list(payload, "items")
    if not items:
        raise SchemaValidationError("Challenge Brief requires at least one item.")
    accepted_count = 0
    for index, item in enumerate(items):
        _require_mapping(item, f"items[{index}]")
        challenge_id = _require_text(item, "challenge_id")
        trigger_candidate_id = _require_text(item, "trigger_candidate_id")
        trigger_type = _require_text(item, "trigger_type")
        if fired_trigger_ids is not None and trigger_candidate_id not in fired_trigger_ids:
            raise SchemaValidationError(f"Challenge item references non-fired trigger: {trigger_candidate_id}")
        if fired_trigger_types is not None:
            expected_type = fired_trigger_types.get(trigger_candidate_id)
            if expected_type and trigger_type != expected_type:
                raise SchemaValidationError(
                    f"Challenge item trigger_type {trigger_type!r} does not match fired trigger "
                    f"{trigger_candidate_id!r} type {expected_type!r}."
                )
        if challenge_id:
            accepted_count += 1
        for field in ("acid", "disagreement_statement", "challenge", "next_review_checkpoint"):
            _require_text(item, field)
        for field in PM_CHALLENGE_TEXT_FIELDS:
            if field in item and item.get(field) not in (None, ""):
                _require_text(item, field)
        _reject_generic_challenge_question(item)
        _require_mapping(item.get("position_summary"), "position_summary")
        _require_list(item, "evidence_pointers")
    if accepted_count == 0:
        raise SchemaValidationError("Challenge Brief cannot dismiss every item.")
    _require_list(payload, "evidence_index")


def reject_prescriptive_sizing_language(payload: dict[str, Any]) -> None:
    banned = ("buy ", "sell ", "trade ", "target weight", "increase to", "decrease to", "recommend ")
    for path, value in _iter_strings(payload):
        normalized = value.lower()
        if any(term in normalized for term in banned):
            raise SchemaValidationError(f"Prescriptive sizing language rejected at {path}.")


def _reject_generic_challenge_question(item: dict[str, Any]) -> None:
    text = " ".join(
        str(item.get(field, ""))
        for field in ("challenge", "primary_pm_question")
    ).lower()
    if any(pattern in text for pattern in GENERIC_PM_QUESTION_PATTERNS):
        raise SchemaValidationError(
            "Challenge question is too generic; name the thesis, implementation issue, or evidence tension under review."
        )


def _validate_header(header: Any, *, fund: str, required: tuple[str, ...]) -> None:
    _require_mapping(header, "header")
    for field in required:
        if field == "prior_snapshot_date":
            if field not in header:
                raise SchemaValidationError(f"Missing required field: {field}")
        else:
            _require_text(header, field)
    if header.get("fund") != fund:
        raise SchemaValidationError(f"Header fund {header.get('fund')!r} does not match tool fund {fund!r}.")


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaValidationError(f"{field_name} must be an object.")
    return value


def _require_list(payload: dict[str, Any], field_name: str) -> list[Any]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise SchemaValidationError(f"{field_name} must be a list.")
    return value


def _require_text(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if value in (None, ""):
        raise SchemaValidationError(f"Missing required field: {field_name}")
    return str(value)


def _iter_strings(value: Any, *, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _iter_strings(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_strings(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


__all__ = [
    "PM_CHALLENGE_TEXT_FIELDS",
    "SchemaValidationError",
    "reject_prescriptive_sizing_language",
    "validate_challenge_brief",
    "validate_change_brief",
    "validate_sizing_considerations",
]
