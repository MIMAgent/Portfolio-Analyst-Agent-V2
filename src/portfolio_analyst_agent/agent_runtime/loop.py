"""Tool-use loop for one Model 1 fund review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from ..run_metadata import build_review_run_metadata
from .llm_client import LLMClient
from .prompts import SYSTEM_PROMPT, user_prompt
from .tool_registry import ToolRunContext, build_tool_registry


@dataclass(frozen=True)
class FundRunResult:
    fund: str
    snapshot_date: str
    as_of_date: str
    review_run_id: str
    output_dir: str
    trace_path: str
    completed_writes: list[str]
    turn_count: int


def run_fund(
    *,
    fund: str,
    snapshot_date: str,
    as_of_date: str,
    llm_client: LLMClient,
    output_root: str | Path = "artifacts/monthly_review",
    run_mode: str = "ad_hoc",
    max_turns: int = 20,
    required_writes: set[str] | None = None,
    include_proposed_memory: bool = False,
) -> FundRunResult:
    """Run one fund through the LLM tool-use loop."""

    run_metadata = build_review_run_metadata(
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        run_mode=run_mode,
    )
    context = ToolRunContext(
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        run_metadata=run_metadata,
        output_root=output_root,
        include_proposed_memory=include_proposed_memory,
    )
    registry = build_tool_registry(context)
    tools = [spec.anthropic_tool() for spec in registry.values()]
    required_write_set = required_writes or _required_writes()

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": user_prompt(
                fund=fund,
                snapshot_date=snapshot_date,
                as_of_date=as_of_date,
                run_mode=run_mode,
                required_writes=required_write_set,
            ),
        }
    ]
    trace: list[dict[str, Any]] = []
    completed_writes: set[str] = set()

    for turn_index in range(max_turns):
        try:
            response = llm_client.send(system=SYSTEM_PROMPT, messages=messages, tools=tools)
        except Exception as exc:
            trace.append(
                {
                    "turn_index": turn_index,
                    "event": "llm_error",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                }
            )
            trace_path = _write_trace(
                output_root=output_root,
                snapshot_date=snapshot_date,
                fund=fund,
                run_metadata=run_metadata,
                completed_writes=completed_writes,
                trace=trace,
                status="failed_llm_error",
            )
            raise RuntimeError(f"LLM call failed. Trace written to {trace_path}. Original error: {exc}") from exc
        messages.append({"role": "assistant", "content": response.content})
        trace.append(
            {
                "turn_index": turn_index,
                "event": "llm_response",
                "stop_reason": response.stop_reason,
                "usage": response.usage,
                "content_types": [block.get("type", "") for block in response.content],
            }
        )

        if response.stop_reason == "max_tokens":
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was truncated before a reliable tool call could be completed. "
                        "Retry with a much smaller artifact: at most 3 material movers, one short sentence per "
                        "PM-facing field, and cite each field with existing citation_ref tokens."
                    ),
                }
            )
            trace.append(
                {
                    "turn_index": turn_index,
                    "event": "max_tokens_retry_requested",
                    "reason": "truncated_response_not_executed",
                }
            )
            continue

        tool_uses = [block for block in response.content if block.get("type") == "tool_use"]
        if not tool_uses:
            if _has_required_writes(completed_writes, required_write_set):
                break
            raise RuntimeError("LLM stopped before required write tools completed.")

        tool_results = []
        for block in tool_uses:
            tool_name = block.get("name", "")
            tool_id = block.get("id", "")
            tool_input = block.get("input") or {}
            if tool_name not in registry:
                result_payload = {"error": f"Unknown tool: {tool_name}"}
                is_error = True
            else:
                try:
                    result_payload = registry[tool_name].callable(tool_input)
                    is_error = False
                    if registry[tool_name].kind == "write":
                        completed_writes.add(tool_name)
                except Exception as exc:  # noqa: BLE001 - surface tool errors to model trace
                    result_payload = {"error": str(exc), "error_type": exc.__class__.__name__}
                    is_error = True

            trace.append(
                {
                    "turn_index": turn_index,
                    "event": "tool_call",
                    "tool_name": tool_name,
                    "tool_id": tool_id,
                    "is_error": is_error,
                    "input_keys": sorted(tool_input.keys()),
                    "result_summary": _result_summary(result_payload),
                }
            )
            llm_result_payload = _llm_visible_result(
                tool_name=tool_name,
                result=result_payload,
                tool_kind=registry[tool_name].kind if tool_name in registry else "unknown",
                is_error=is_error,
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(llm_result_payload, default=str),
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})
        if _has_required_writes(completed_writes, required_write_set):
            trace.append(
                {
                    "turn_index": turn_index,
                    "event": "loop_closed",
                    "reason": "required_writes_completed",
                    "completed_writes": sorted(completed_writes),
                    "required_writes": sorted(required_write_set),
                }
            )
            break
    else:
        trace_path = _write_trace(
            output_root=output_root,
            snapshot_date=snapshot_date,
            fund=fund,
            run_metadata=run_metadata,
            completed_writes=completed_writes,
            trace=trace,
            status="failed_max_turns",
        )
        raise RuntimeError(f"Agent loop exceeded max_turns={max_turns}. Trace written to {trace_path}.")

    if not _has_required_writes(completed_writes, required_write_set):
        raise RuntimeError(f"Required write tools missing: {sorted(required_write_set - completed_writes)}")

    trace_path = _write_trace(
        output_root=output_root,
        snapshot_date=snapshot_date,
        fund=fund,
        run_metadata=run_metadata,
        completed_writes=completed_writes,
        trace=trace,
        status="completed",
    )
    output_dir = trace_path.parent
    return FundRunResult(
        fund=fund,
        snapshot_date=snapshot_date,
        as_of_date=as_of_date,
        review_run_id=run_metadata["review_run_id"],
        output_dir=output_dir.as_posix(),
        trace_path=trace_path.as_posix(),
        completed_writes=sorted(completed_writes),
        turn_count=len(trace),
    )


def _required_writes() -> set[str]:
    return {"write_change_brief"}


def _has_required_writes(completed_writes: set[str], required_writes: set[str]) -> bool:
    return required_writes.issubset(completed_writes)


def _result_summary(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        summary = {
            "keys": sorted(result.keys())[:20],
            "row_count": result.get("row_count", result.get("fund_count", "")),
            "candidate_count": result.get("summary", {}).get("candidate_count", "") if isinstance(result.get("summary"), dict) else "",
        }
        if "error" in result:
            summary["error"] = result.get("error")
            summary["error_type"] = result.get("error_type", "")
        return summary
    if isinstance(result, list):
        return {"list_length": len(result)}
    return {"type": type(result).__name__}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "fund"


def _llm_visible_result(*, tool_name: str, result: Any, tool_kind: str, is_error: bool) -> Any:
    """Keep model-visible read payloads small while preserving evidence handles."""

    if is_error or tool_kind != "read" or not isinstance(result, dict):
        return result

    if tool_name == "get_fund_snapshot":
        acid_rows = result.get("acid_rows", [])
        ranked_rows = sorted(
            [row for row in acid_rows if isinstance(row, dict)],
            key=lambda row: abs(_safe_float(row.get("active_rolled_exposure"))),
            reverse=True,
        )
        return {
            "fund_metadata": result.get("fund_metadata", {}),
            "coverage": result.get("coverage", {}),
            "acid_row_count": len(acid_rows),
            "top_active_rows": [
                _compact_row(row, citation_source="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv")
                for row in ranked_rows[:12]
            ],
            "diagnostics": _compact_diagnostics(result.get("diagnostics", {})),
            "run_metadata": result.get("run_metadata", {}),
            "compaction_note": "Model-visible payload compacted; use follow-up tools for deeper lineage/history.",
        }

    if tool_name == "evaluate_challenge_triggers":
        candidates = result.get("trigger_candidates", [])
        fired = [row for row in candidates if isinstance(row, dict) and row.get("evaluation_status") == "fired"]
        return {
            "summary": result.get("summary", {}),
            "supported_trigger_types": result.get("supported_trigger_types", []),
            "deferred_trigger_types": result.get("deferred_trigger_types", []),
            "fired_trigger_count": len(fired),
            "top_fired_triggers": [
                _compact_row(row, citation_source="artifacts/vir/equity_vir_dataset.csv")
                for row in fired[:12]
            ],
            "run_metadata": result.get("run_metadata", {}),
            "compaction_note": "Only top fired triggers are shown to limit context size.",
        }

    if tool_name == "get_acid_history":
        rows = result.get("rows", [])
        return {
            **{key: result.get(key) for key in ("acid", "snapshot_date", "as_of_date", "lookback_months", "model_family", "row_count")},
            "rows": [
                _compact_row(row, citation_source="artifacts/vir/equity_vir_dataset.csv")
                for row in rows[-12:]
                if isinstance(row, dict)
            ],
            "run_metadata": result.get("run_metadata", {}),
        }

    if tool_name == "get_exposure_lineage":
        rows = result.get("rows", [])
        return {
            **{key: result.get(key) for key in ("fund", "acid", "snapshot_date", "as_of_date", "row_count", "returned_row_count", "limit")},
            "rows": [
                _compact_row(row, citation_source="artifacts/rolled_exposures/fund_rolled_exposure_detail.csv")
                for row in rows[:15]
                if isinstance(row, dict)
            ],
            "run_metadata": result.get("run_metadata", {}),
            "compaction_note": "Only top lineage rows are returned to the model.",
        }

    if tool_name == "get_peer_context":
        current_rows = result.get("current_snapshot_rows", [])
        peers = result.get("peers", [])
        return {
            **{key: result.get(key) for key in ("acid", "snapshot_date", "as_of_date", "mapping_status", "mapping", "peer_count", "current_snapshot_row_count")},
            "peers": peers[:20] if isinstance(peers, list) else peers,
            "current_snapshot_rows": [
                _compact_row(row, citation_source="artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv")
                for row in current_rows[:20]
                if isinstance(row, dict)
            ],
            "run_metadata": result.get("run_metadata", {}),
        }

    if tool_name == "get_market_context":
        rows = result.get("rows", [])
        return {
            **{
                key: result.get(key)
                for key in ("snapshot_date", "as_of_date", "fund", "acid", "comparison_group", "row_count", "context_status", "expected_artifact")
            },
            "rows": [
                _compact_row(row, citation_source="artifacts/market_context/monthly_market_context.csv")
                for row in rows[:12]
                if isinstance(row, dict)
            ],
            "run_metadata": result.get("run_metadata", {}),
        }

    if tool_name == "search_market_context":
        rows = result.get("rows", [])
        return {
            **{
                key: result.get(key)
                for key in (
                    "query",
                    "snapshot_date",
                    "as_of_date",
                    "fund",
                    "acid",
                    "comparison_group",
                    "searched_domains",
                    "new_row_count",
                    "total_row_count",
                    "output_csv",
                    "context_status",
                )
            },
            "rows": [
                _compact_row(row, citation_source="artifacts/market_context/monthly_market_context.csv")
                for row in rows[:8]
                if isinstance(row, dict)
            ],
            "run_metadata": result.get("run_metadata", {}),
        }

    return result


def _compact_diagnostics(diagnostics: Any) -> Any:
    if not isinstance(diagnostics, dict):
        return diagnostics
    compacted = {}
    for key, value in diagnostics.items():
        if isinstance(value, dict):
            compacted[key] = {
                "artifact_path": value.get("artifact_path", ""),
                "row_count": value.get("row_count", 0),
                "rows": [_compact_row(row) for row in value.get("rows", [])[:5] if isinstance(row, dict)],
            }
        else:
            compacted[key] = value
    return compacted


def _compact_row(row: dict[str, Any], *, citation_source: str | None = None) -> dict[str, Any]:
    keep_fields = (
        "row_id",
        "acid",
        "acid_type",
        "asset_class_name",
        "family",
        "comparison_group",
        "relative_value_group",
        "interpretation_type",
        "snapshot_date",
        "fund",
        "fund_target_rolled_exposure",
        "fund_benchmark_rolled_exposure",
        "active_rolled_exposure",
        "fund_target_security_contribution",
        "fund_benchmark_security_contribution",
        "active_security_contribution",
        "source_security_name",
        "vir_stf",
        "vir_delta_stf",
        "vir_rank_in_category_by_stf",
        "vir_rank_change_by_stf",
        "algo_perspective",
        "algo_absolute_weight",
        "algo_active_weight",
        "algo_benchmark_weight",
        "algo_absolute_weight_mom",
        "algo_active_weight_mom",
        "trigger_candidate_id",
        "trigger_type",
        "evaluation_status",
        "severity",
        "rationale",
        "scope_type",
        "scope_value",
        "priority",
        "headline",
        "narrative",
        "fundamental_readthrough",
        "pm_question",
        "source_label",
        "source_date",
        "source_url",
        "citation_ref",
        "mapping_citation_ref",
    )
    compacted = {field: row[field] for field in keep_fields if field in row and row[field] not in (None, "")}
    if citation_source and compacted.get("row_id"):
        compacted["citation_ref"] = f"csv:{citation_source}#row_id={compacted['row_id']}"
    if compacted.get("trigger_candidate_id"):
        compacted["trigger_citation_ref"] = f"trigger:evaluate_challenge_triggers_v1#{compacted['trigger_candidate_id']}"
    return compacted


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _write_trace(
    *,
    output_root: str | Path,
    snapshot_date: str,
    fund: str,
    run_metadata: dict[str, Any],
    completed_writes: set[str],
    trace: list[dict[str, Any]],
    status: str,
) -> Path:
    output_dir = Path(output_root) / snapshot_date / _slugify(fund)
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / "agent_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "run_metadata": run_metadata,
                "status": status,
                "completed_writes": sorted(completed_writes),
                "trace": trace,
                "closed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return trace_path


__all__ = ["FundRunResult", "run_fund"]
