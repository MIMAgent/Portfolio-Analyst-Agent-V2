"""Tool registry for the LLM runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .. import agent_tools
from ..citations import extract_tokens
from ..write_tools import (
    update_memory,
    write_challenge_brief,
    write_change_brief,
    write_sizing_considerations,
)


ToolCallable = Callable[[dict[str, Any]], Any]


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    callable: ToolCallable
    kind: str

    def anthropic_tool(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolRunContext:
    fund: str
    snapshot_date: str | None
    as_of_date: str
    run_metadata: dict[str, Any]
    output_root: str | Path = "artifacts/monthly_review"
    memory_path: str | Path = "artifacts/agent_memory/memory_records.json"
    governance_path: str | Path = "config/agent_governance.json"
    include_proposed_memory: bool = False
    fired_trigger_ids: set[str] = field(default_factory=set)
    fired_trigger_types: dict[str, str] = field(default_factory=dict)


def build_tool_registry(context: ToolRunContext) -> dict[str, ToolSpec]:
    registry: dict[str, ToolSpec] = {}

    def add(name: str, description: str, input_schema: dict[str, Any], func: ToolCallable, kind: str) -> None:
        registry[name] = ToolSpec(name, description, input_schema, func, kind)

    add(
        "get_fund_snapshot",
        "Return current fund ACID rows enriched with mapping metadata.",
        _object_schema({"fund": "string", "snapshot_date": "string", "as_of_date": "string"}),
        lambda args: agent_tools.get_fund_snapshot(
            fund=context.fund,
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
        ),
        "read",
    )
    add(
        "recall_memory",
        "Return approved/applied prior memory and proposed counts.",
        _object_schema({"fund": "string", "snapshot_date": "string", "as_of_date": "string"}),
        lambda args: agent_tools.recall_memory(
            fund=context.fund,
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
            memory_path=context.memory_path,
            include_proposed=context.include_proposed_memory,
        ),
        "read",
    )
    add(
        "evaluate_challenge_triggers",
        "Return deterministic trigger candidates for one fund.",
        _object_schema({"fund": "string", "snapshot_date": "string", "as_of_date": "string"}),
        lambda args: _record_triggers(
            context,
            agent_tools.evaluate_challenge_triggers(
                fund=context.fund,
                snapshot_date=context.snapshot_date,
                as_of_date=context.as_of_date,
            ),
        ),
        "read",
    )
    add(
        "get_acid_history",
        "Return replay-safe historical VIR rows for one ACID.",
        _object_schema({"acid": "string", "snapshot_date": "string", "as_of_date": "string", "lookback_months": "integer"}, required=("acid",)),
        lambda args: agent_tools.get_acid_history(
            acid=args["acid"],
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
            lookback_months=int(args.get("lookback_months", 12)),
        ),
        "read",
    )
    add(
        "get_exposure_lineage",
        "Return account/security lineage rows for one fund/ACID exposure.",
        _object_schema({"fund": "string", "acid": "string", "snapshot_date": "string", "as_of_date": "string", "limit": "integer"}, required=("acid",)),
        lambda args: agent_tools.get_exposure_lineage(
            fund=context.fund,
            acid=args["acid"],
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
            limit=int(args.get("limit", 100)),
        ),
        "read",
    )
    add(
        "get_peer_context",
        "Return mapping-driven peer context for one ACID.",
        _object_schema({"acid": "string", "snapshot_date": "string", "as_of_date": "string"}, required=("acid",)),
        lambda args: agent_tools.get_peer_context(
            acid=args["acid"],
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
        ),
        "read",
    )
    add(
        "get_market_context",
        "Return approved monthly market/fundamental context rows for an ACID, fund, comparison group, or global scope. Use only cited rows; if no rows are returned, do not invent macro context.",
        _object_schema(
            {
                "fund": "string",
                "acid": "string",
                "comparison_group": "string",
                "snapshot_date": "string",
                "as_of_date": "string",
                "limit": "integer",
            }
        ),
        lambda args: agent_tools.get_market_context(
            fund=context.fund,
            acid=args.get("acid"),
            comparison_group=args.get("comparison_group"),
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
            limit=int(args.get("limit", 12)),
        ),
        "read",
    )
    add(
        "search_market_context",
        "Search approved web sources only, cache citable market/fundamental context rows, and return the rows added. Use concise queries for material movers or fired challenges, then call get_market_context for the same ACID/comparison group.",
        _object_schema(
            {
                "query": "string",
                "fund": "string",
                "acid": "string",
                "comparison_group": "string",
                "snapshot_date": "string",
                "as_of_date": "string",
                "max_results": "integer",
                "max_sources": "integer",
            },
            required=("query",),
        ),
        lambda args: agent_tools.search_market_context(
            query=args["query"],
            fund=context.fund,
            acid=args.get("acid"),
            comparison_group=args.get("comparison_group"),
            snapshot_date=context.snapshot_date,
            as_of_date=context.as_of_date,
            max_results=int(args.get("max_results", 6)),
            max_sources=int(args.get("max_sources", 4)),
        ),
        "read",
    )
    add(
        "write_change_brief",
        "Validate and persist the concise Change Brief artifact. Provide content with executive_summary, material_movers, and cited narratives; run metadata fields are filled automatically.",
        _change_brief_schema(),
        lambda args: write_change_brief(
            context.fund,
            _prepare_change_brief_content(args, context=context),
            output_root=context.output_root,
            memory_path=context.memory_path,
        ),
        "write",
    )
    add(
        "write_sizing_considerations",
        "Validate and persist optional Sizing Considerations after Change Brief succeeds. Keep lists short and non-prescriptive.",
        _sizing_schema(),
        lambda args: write_sizing_considerations(
            context.fund,
            _prepare_sizing_content(args, context=context),
            output_root=context.output_root,
            memory_path=context.memory_path,
        ),
        "write",
    )
    add(
        "write_challenge_brief",
        "Validate and persist the conditional Challenge Brief artifact for accepted fired trigger candidates only. Provide content.items with challenge_id, trigger_candidate_id, acid, trigger_type, disagreement_statement, challenge, and cited evidence.",
        _challenge_schema(),
        lambda args: write_challenge_brief(
            context.fund,
            _prepare_challenge_content(args, context=context),
            fired_trigger_ids=context.fired_trigger_ids or None,
            fired_trigger_types=context.fired_trigger_types or None,
            output_root=context.output_root,
            memory_path=context.memory_path,
        ),
        "write",
    )
    add(
        "update_memory",
        "Validate and append proposed-only memory operations.",
        _object_schema({"fund": "string", "ops": "array"}, required=("ops",)),
        lambda args: update_memory(
            context.fund,
            args["ops"],
            run_metadata=context.run_metadata,
            memory_path=context.memory_path,
            governance_path=context.governance_path,
        ),
        "write",
    )
    return registry


def _record_triggers(context: ToolRunContext, result: dict[str, Any]) -> dict[str, Any]:
    fired_rows = [
        row
        for row in result.get("trigger_candidates", [])
        if row.get("evaluation_status") == "fired"
    ]
    context.fired_trigger_ids = {
        row.get("trigger_candidate_id", "")
        for row in fired_rows
    }
    context.fired_trigger_types = {
        row.get("trigger_candidate_id", ""): row.get("trigger_type", "")
        for row in fired_rows
        if row.get("trigger_candidate_id")
    }
    return result


def _prepare_change_brief_content(args: dict[str, Any], *, context: ToolRunContext) -> dict[str, Any]:
    content = _extract_content(args)
    content = _hydrate_header(content, context=context)
    content.setdefault("material_movers", [])
    content.setdefault("sizing_artifact_summary", {})
    content.setdefault("memory_updates_summary", {})
    content.setdefault("triggers_fired_summary", {})
    content.setdefault("evidence_index", [])
    content["material_movers"] = [
        _hydrate_change_brief_mover(item)
        for item in content.get("material_movers", [])
        if isinstance(item, dict)
    ]
    return content


def _prepare_sizing_content(args: dict[str, Any], *, context: ToolRunContext) -> dict[str, Any]:
    content = _extract_content(args)
    content = _hydrate_header(content, context=context)
    content.setdefault("perspective_summary", {})
    content.setdefault("algo_vs_positioning_agreement", [])
    content.setdefault("algo_vs_positioning_disagreement", [])
    content.setdefault("largest_algo_mom_changes", [])
    content.setdefault("evidence_index", [])
    return content


def _prepare_challenge_content(args: dict[str, Any], *, context: ToolRunContext) -> dict[str, Any]:
    content = _extract_content(args)
    content = _hydrate_header(content, context=context)
    for alias in ("challenge_items", "challenges", "accepted_challenges", "trigger_challenges"):
        if "items" not in content and alias in content:
            content["items"] = content[alias]
    if "items" not in content:
        candidate_item = {
            key: value
            for key, value in content.items()
            if key not in {"header", "evidence_index"}
        }
        content["items"] = [candidate_item] if candidate_item else []
    if not isinstance(content.get("items"), list):
        content["items"] = [content["items"]] if isinstance(content.get("items"), dict) else []
    content["items"] = [
        _hydrate_challenge_item(item, context=context, index=index)
        for index, item in enumerate(content.get("items", []))
        if isinstance(item, dict)
    ]
    content.setdefault("evidence_index", [])
    return content


def _hydrate_change_brief_mover(item: dict[str, Any]) -> dict[str, Any]:
    hydrated = dict(item)
    fallback_token = _first_evidence_pointer_token(hydrated)
    if not fallback_token:
        return hydrated
    for field_name in ("pm_takeaway", "review_question", "what_would_change_view"):
        value = hydrated.get(field_name)
        if isinstance(value, str) and value.strip() and not extract_tokens(value):
            hydrated[field_name] = f"{value.rstrip()} {fallback_token}"
    return hydrated


def _first_evidence_pointer_token(payload: dict[str, Any]) -> str:
    pointers = payload.get("evidence_pointers", [])
    if not isinstance(pointers, list):
        return ""
    for pointer in pointers:
        if not isinstance(pointer, dict):
            continue
        artifact_path = str(pointer.get("artifact_path", "")).strip()
        row_id = str(pointer.get("row_id", "")).strip()
        if artifact_path and row_id:
            return f"csv:{artifact_path}#row_id={row_id}"
    return ""


def _hydrate_challenge_item(item: dict[str, Any], *, context: ToolRunContext, index: int) -> dict[str, Any]:
    hydrated = dict(item)
    if not hydrated.get("disagreement_statement"):
        hydrated["disagreement_statement"] = _first_non_empty(
            hydrated,
            ("disagreement_statement", "narrative", "rationale", "signal_disagreement", "positioning_tension"),
        )
    if not hydrated.get("challenge"):
        hydrated["challenge"] = _first_non_empty(
            hydrated,
            ("challenge", "review_question", "challenge_question", "pm_question", "question"),
        )
    if not hydrated.get("trigger_candidate_id") and len(context.fired_trigger_ids) == 1:
        hydrated["trigger_candidate_id"] = next(iter(context.fired_trigger_ids))
    if not hydrated.get("challenge_id") and hydrated.get("trigger_candidate_id"):
        hydrated["challenge_id"] = f"chg_{str(hydrated['trigger_candidate_id']).removeprefix('trig_')}"
    if not hydrated.get("next_review_checkpoint"):
        hydrated["next_review_checkpoint"] = "Next monthly review"
    hydrated.setdefault("position_summary", {})
    hydrated.setdefault("evidence_pointers", [])
    if not hydrated.get("acid") and hydrated.get("position_summary", {}).get("acid"):
        hydrated["acid"] = hydrated["position_summary"]["acid"]
    if not hydrated.get("trigger_type"):
        trigger_id = hydrated.get("trigger_candidate_id", "")
        if trigger_id in context.fired_trigger_types:
            hydrated["trigger_type"] = context.fired_trigger_types[trigger_id]
        else:
            unique_types = {value for value in context.fired_trigger_types.values() if value}
            if len(unique_types) == 1:
                hydrated["trigger_type"] = next(iter(unique_types))
    return hydrated


def _first_non_empty(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _extract_content(args: dict[str, Any]) -> dict[str, Any]:
    content = args.get("content")
    if content is None:
        content = {
            key: value
            for key, value in args.items()
            if key not in {"fund"}
        }
    if not isinstance(content, dict):
        return {}
    for envelope_key in ("change_brief", "sizing_considerations", "challenge_brief", "payload", "artifact"):
        nested = content.get(envelope_key)
        if isinstance(nested, dict):
            return nested
    return content


def _hydrate_header(content: dict[str, Any], *, context: ToolRunContext) -> dict[str, Any]:
    """Attach authoritative run metadata so the LLM can focus on analysis."""

    if not isinstance(content, dict):
        return content
    hydrated = dict(content)
    existing_header = hydrated.get("header")
    header = dict(existing_header) if isinstance(existing_header, dict) else {}
    header.update(
        {
            "fund": context.fund,
            "snapshot_date": context.snapshot_date or context.run_metadata.get("snapshot_date", ""),
            "prior_snapshot_date": header.get("prior_snapshot_date", ""),
            "as_of_date": context.as_of_date,
            "review_run_id": context.run_metadata.get("review_run_id", ""),
            "parser_version": context.run_metadata.get("parser_version", ""),
            "mapping_version": context.run_metadata.get("mapping_version", ""),
            "governance_version": context.run_metadata.get("governance_version", ""),
            "algo_version": context.run_metadata.get("algo_version", ""),
            "run_mode": context.run_metadata.get("run_mode", ""),
        }
    )
    hydrated["header"] = header
    return hydrated


def _object_schema(properties: dict[str, str], required: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            name: _property_schema(kind)
            for name, kind in properties.items()
        },
        "required": list(required),
        "additionalProperties": True,
    }


def _property_schema(kind: str) -> dict[str, Any]:
    if kind == "object":
        return {"type": "object"}
    if kind == "array":
        return {"type": "array"}
    if kind == "integer":
        return {"type": "integer"}
    return {"type": "string"}


def _change_brief_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["content"],
        "additionalProperties": True,
        "properties": {
            "fund": {"type": "string"},
            "content": {
                "type": "object",
                "required": ["executive_summary", "material_movers"],
                "additionalProperties": True,
                "properties": {
                    "executive_summary": {
                        "type": "string",
                        "maxLength": 900,
                        "description": "Concise cited summary. Must include citation_ref tokens from read tools.",
                    },
                    "material_movers": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "required": ["acid", "narrative", "evidence_pointers"],
                            "additionalProperties": True,
                            "properties": {
                                "acid": {"type": "string"},
                                "active_rolled_exposure": {"type": "number"},
                                "target_rolled_exposure": {"type": "number"},
                                "benchmark_rolled_exposure": {"type": "number"},
                                "vir_stf": {"type": "number"},
                                "vir_delta_stf": {"type": "number"},
                                "vir_rank_change_by_stf": {"type": "number"},
                                "narrative": {
                                    "type": "string",
                                    "maxLength": 900,
                                    "description": "Cited factual narrative using citation_ref tokens from read tools.",
                                },
                                "pm_takeaway": {
                                    "type": "string",
                                    "maxLength": 500,
                                    "description": "Cited PM-facing implication, written as a review-ready observation rather than a recommendation.",
                                },
                                "review_question": {
                                    "type": "string",
                                    "maxLength": 500,
                                    "description": "Specific PM review question tied to this ACID and the cited evidence.",
                                },
                                "what_would_change_view": {
                                    "type": "string",
                                    "maxLength": 500,
                                    "description": "Specific evidence or market/model development that would change the interpretation.",
                                },
                                "evidence_pointers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "artifact_path": {"type": "string"},
                                            "row_id": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "sizing_artifact_summary": {"type": "object"},
                    "memory_updates_summary": {"type": "object"},
                    "triggers_fired_summary": {"type": "object"},
                    "evidence_index": {"type": "array"},
                },
            },
        },
    }


def _sizing_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["content"],
        "additionalProperties": True,
        "properties": {
            "fund": {"type": "string"},
            "content": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "perspective_summary": {"type": "object"},
                    "algo_vs_positioning_agreement": {"type": "array", "maxItems": 3},
                    "algo_vs_positioning_disagreement": {"type": "array", "maxItems": 3},
                    "largest_algo_mom_changes": {"type": "array", "maxItems": 3},
                    "evidence_index": {"type": "array"},
                },
            },
        },
    }


def _challenge_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["content"],
        "additionalProperties": True,
        "properties": {
            "fund": {"type": "string"},
            "content": {
                "type": "object",
                "required": ["items"],
                "additionalProperties": True,
                "properties": {
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "required": ["trigger_candidate_id", "acid", "trigger_type", "disagreement_statement", "challenge", "evidence_pointers"],
                            "additionalProperties": True,
                            "properties": {
                                "challenge_id": {"type": "string"},
                                "trigger_candidate_id": {"type": "string"},
                                "acid": {"type": "string"},
                                "trigger_type": {"type": "string"},
                                "position_summary": {"type": "object"},
                                "disagreement_statement": {
                                    "type": "string",
                                    "description": "Cited statement of why current positioning conflicts with the fired trigger.",
                                },
                                "challenge": {
                                    "type": "string",
                                    "description": "Cited PM challenge question/framing, factual and non-prescriptive.",
                                },
                                "next_review_checkpoint": {"type": "string"},
                                "evidence_pointers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "artifact_path": {"type": "string"},
                                            "row_id": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "evidence_index": {"type": "array"},
                },
            },
        },
    }


__all__ = ["ToolRunContext", "ToolSpec", "build_tool_registry"]
