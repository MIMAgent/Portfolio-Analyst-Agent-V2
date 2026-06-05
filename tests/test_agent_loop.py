"""Mocked LLM loop tests for Phase 4."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from portfolio_analyst_agent.agent_runtime import run_fund
from portfolio_analyst_agent.agent_runtime.llm_client import (
    LLMResponse,
    ScriptedLLMClient,
    _bedrock_converse_payload,
    _from_bedrock_block,
    _load_dotenv,
    _to_bedrock_message,
    _to_bedrock_tool,
)
from portfolio_analyst_agent.agent_runtime.loop import _llm_visible_result
from portfolio_analyst_agent.agent_runtime.tool_registry import ToolRunContext, build_tool_registry


class FailingLLMClient:
    def send(self, *, system, messages, tools):
        raise TimeoutError("timed out")


def _evidence_csv(tmp_path):
    path = tmp_path / "evidence.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "value"])
        writer.writeheader()
        writer.writerow({"row_id": "row_1", "value": "1"})
    return path


def _change_brief_payload(evidence_path: Path):
    token = f"csv:{evidence_path.as_posix()}#row_id=row_1"
    return {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "prior_snapshot_date": "",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_test",
            "parser_version": "p",
            "mapping_version": "m",
            "governance_version": "g",
            "algo_version": "a",
            "run_mode": "ad_hoc",
        },
        "executive_summary": f"Executive summary with citation {token}",
        "material_movers": [
            {
                "acid": "US LRG EQ",
                "active_rolled_exposure": 1.0,
                "target_rolled_exposure": 60.0,
                "benchmark_rolled_exposure": 59.0,
                "exposure_mom": 0.5,
                "vir_stf": 1.2,
                "vir_delta_stf": 0.1,
                "vir_rank_change_by_stf": 1,
                "decomposition_drivers": [],
                "narrative": f"Narrative with citation {token}",
                "evidence_pointers": [{"artifact_path": evidence_path.as_posix(), "row_id": "row_1"}],
            }
        ],
        "decomposition_narrative": "",
        "lineage_notes": [],
        "sizing_artifact_summary": {
            "artifact_path": "",
            "headline_agreements": [],
            "headline_disagreements": [],
            "largest_algo_mom_changes": [],
            "evidence_pointers": [],
        },
        "memory_updates_summary": {},
        "triggers_fired_summary": {},
        "evidence_index": [],
    }


def _challenge_brief_payload(evidence_path: Path):
    token = f"csv:{evidence_path.as_posix()}#row_id=row_1"
    return {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_test",
            "parser_version": "p",
            "mapping_version": "m",
            "governance_version": "g",
        },
        "items": [
            {
                "challenge_id": "chg_1",
                "trigger_candidate_id": "trig_1",
                "acid": "US LRG EQ",
                "trigger_type": "sign_disagreement",
                "position_summary": {},
                "disagreement_statement": f"Disagreement cited {token}",
                "challenge": f"Challenge cited {token}",
                "next_review_checkpoint": f"Next review cited {token}",
                "evidence_pointers": [{"artifact_path": evidence_path.as_posix(), "row_id": "row_1"}],
            }
        ],
        "evidence_index": [],
    }


def test_run_fund_executes_write_tool_and_writes_trace(tmp_path):
    evidence = _evidence_csv(tmp_path)
    scripted = ScriptedLLMClient(
        [
            LLMResponse(
                content=[
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "write_change_brief",
                        "input": {"fund": "Fund", "content": _change_brief_payload(evidence)},
                    }
                ],
                stop_reason="tool_use",
                usage={"input_tokens": 1, "output_tokens": 1},
            ),
            LLMResponse(
                content=[{"type": "text", "text": "Review complete."}],
                stop_reason="end_turn",
                usage={"input_tokens": 1, "output_tokens": 1},
            ),
        ]
    )

    result = run_fund(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        llm_client=scripted,
        output_root=tmp_path / "out",
    )

    assert "write_change_brief" in result.completed_writes
    assert Path(result.trace_path).exists()
    assert Path(result.output_dir, "change_brief.json").exists()
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["completed_writes"] == ["write_change_brief"]
    assert any(event["event"] == "tool_call" for event in trace["trace"])


def test_run_fund_can_require_challenge_brief(tmp_path):
    evidence = _evidence_csv(tmp_path)
    scripted = ScriptedLLMClient(
        [
            LLMResponse(
                content=[
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "write_change_brief",
                        "input": {"fund": "Fund", "content": _change_brief_payload(evidence)},
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "write_challenge_brief",
                        "input": {"fund": "Fund", "content": _challenge_brief_payload(evidence)},
                    },
                ],
                stop_reason="tool_use",
                usage={},
            ),
        ]
    )

    result = run_fund(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        llm_client=scripted,
        output_root=tmp_path / "out",
        required_writes={"write_change_brief", "write_challenge_brief"},
    )

    assert result.completed_writes == ["write_challenge_brief", "write_change_brief"]
    assert Path(result.output_dir, "challenge_brief.json").exists()


def test_run_fund_does_not_execute_truncated_write_tool(tmp_path):
    evidence = _evidence_csv(tmp_path)
    scripted = ScriptedLLMClient(
        [
            LLMResponse(
                content=[
                    {
                        "type": "tool_use",
                        "id": "toolu_truncated",
                        "name": "write_change_brief",
                        "input": {"content": {"material_movers": []}},
                    }
                ],
                stop_reason="max_tokens",
                usage={},
            ),
            LLMResponse(
                content=[
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "write_change_brief",
                        "input": {"fund": "Fund", "content": _change_brief_payload(evidence)},
                    }
                ],
                stop_reason="tool_use",
                usage={},
            ),
        ]
    )

    result = run_fund(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        llm_client=scripted,
        output_root=tmp_path / "out",
    )
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))

    assert result.completed_writes == ["write_change_brief"]
    assert any(event["event"] == "max_tokens_retry_requested" for event in trace["trace"])
    assert not any(event.get("tool_id") == "toolu_truncated" for event in trace["trace"])


def test_write_tool_hydrates_header_from_run_context(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = f"csv:{evidence.as_posix()}#row_id=row_1"
    context = ToolRunContext(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_context",
            "parser_version": "parser",
            "mapping_version": "mapping",
            "governance_version": "governance",
            "algo_version": "algo",
            "run_mode": "ad_hoc",
        },
        output_root=tmp_path / "out",
    )
    registry = build_tool_registry(context)
    payload = {
        "executive_summary": f"Executive summary with citation {token}",
        "material_movers": [
            {
                "acid": "US LRG EQ",
                "narrative": f"Narrative with citation {token}",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "sizing_artifact_summary": {},
        "memory_updates_summary": {},
        "triggers_fired_summary": {},
        "evidence_index": [],
    }

    result = registry["write_change_brief"].callable({"content": payload})

    written = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    assert written["header"]["review_run_id"] == "rrun_context"
    assert written["header"]["parser_version"] == "parser"


def test_write_tool_hydrates_pm_field_citations_from_evidence_pointer(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = f"csv:{evidence.as_posix()}#row_id=row_1"
    context = ToolRunContext(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_context",
            "parser_version": "parser",
            "mapping_version": "mapping",
            "governance_version": "governance",
            "algo_version": "algo",
            "run_mode": "ad_hoc",
        },
        output_root=tmp_path / "out",
    )
    registry = build_tool_registry(context)

    result = registry["write_change_brief"].callable(
        {
            "content": {
                "executive_summary": f"Executive summary with citation {token}",
                "material_movers": [
                    {
                        "acid": "US LRG EQ",
                        "narrative": f"Narrative with citation {token}",
                        "pm_takeaway": "PM takeaway without explicit citation.",
                        "review_question": "Review question without explicit citation?",
                        "what_would_change_view": "What would change view without explicit citation.",
                        "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
                    }
                ],
            }
        }
    )
    written = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    mover = written["material_movers"][0]

    assert mover["pm_takeaway"].endswith(token)
    assert mover["review_question"].endswith(token)
    assert mover["what_would_change_view"].endswith(token)


def test_read_tools_pin_fund_and_dates_to_run_context(monkeypatch):
    captured = {}

    def fake_get_fund_snapshot(*, fund, snapshot_date, as_of_date):
        captured.update({"fund": fund, "snapshot_date": snapshot_date, "as_of_date": as_of_date})
        return {"ok": True}

    monkeypatch.setattr(
        "portfolio_analyst_agent.agent_runtime.tool_registry.agent_tools.get_fund_snapshot",
        fake_get_fund_snapshot,
    )
    context = ToolRunContext(
        fund="Pinned Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={},
    )
    registry = build_tool_registry(context)

    registry["get_fund_snapshot"].callable(
        {"fund": "Wrong Fund", "snapshot_date": "2099-01-01", "as_of_date": "2099-01-01"}
    )

    assert captured == {
        "fund": "Pinned Fund",
        "snapshot_date": "2026-04-06",
        "as_of_date": "2026-04-06",
    }


def test_acid_read_tool_schemas_require_acid():
    context = ToolRunContext(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={},
    )
    registry = build_tool_registry(context)

    assert registry["get_acid_history"].input_schema["required"] == ["acid"]
    assert registry["get_exposure_lineage"].input_schema["required"] == ["acid"]
    assert registry["get_peer_context"].input_schema["required"] == ["acid"]


def test_write_tool_hydrates_change_brief_boilerplate_containers(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = f"csv:{evidence.as_posix()}#row_id=row_1"
    context = ToolRunContext(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_context",
            "parser_version": "parser",
            "mapping_version": "mapping",
            "governance_version": "governance",
            "algo_version": "algo",
            "run_mode": "ad_hoc",
        },
        output_root=tmp_path / "out",
    )
    registry = build_tool_registry(context)

    result = registry["write_change_brief"].callable(
        {
            "content": {
                "executive_summary": f"Executive summary with citation {token}",
                "material_movers": [
                    {
                        "acid": "US LRG EQ",
                        "narrative": f"Narrative with citation {token}",
                        "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
                    }
                ],
            }
        }
    )

    written = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
    assert written["sizing_artifact_summary"] == {}
    assert written["memory_updates_summary"] == {}
    assert written["triggers_fired_summary"] == {}
    assert written["evidence_index"] == []


def test_run_fund_rejects_completion_without_required_write(tmp_path):
    scripted = ScriptedLLMClient(
        [
            LLMResponse(
                content=[{"type": "text", "text": "Done without writing."}],
                stop_reason="end_turn",
                usage={},
            )
        ]
    )

    with pytest.raises(RuntimeError, match="before required write"):
        run_fund(
            fund="Fund",
            snapshot_date="2026-04-06",
            as_of_date="2026-04-06",
            llm_client=scripted,
            output_root=tmp_path / "out",
        )


def test_run_fund_writes_trace_on_llm_error(tmp_path):
    with pytest.raises(RuntimeError, match="LLM call failed"):
        run_fund(
            fund="Fund",
            snapshot_date="2026-04-06",
            as_of_date="2026-04-06",
            llm_client=FailingLLMClient(),
            output_root=tmp_path / "out",
        )

    trace_path = tmp_path / "out" / "2026-04-06" / "fund" / "agent_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert trace["status"] == "failed_llm_error"
    assert trace["trace"][0]["event"] == "llm_error"


def test_load_dotenv_sets_missing_env_value(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("ANTHROPIC_API_KEY=test_key\n", encoding="utf-8")

    _load_dotenv(env_path)

    assert __import__("os").environ["ANTHROPIC_API_KEY"] == "test_key"


def test_bedrock_tool_and_message_conversion():
    tool = {
        "name": "get_fund_snapshot",
        "description": "Read fund snapshot.",
        "input_schema": {"type": "object", "properties": {"fund": {"type": "string"}}},
    }
    bedrock_tool = _to_bedrock_tool(tool)
    assert bedrock_tool["toolSpec"]["name"] == "get_fund_snapshot"
    assert bedrock_tool["toolSpec"]["inputSchema"]["json"]["type"] == "object"

    message = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_1",
                "content": '{"ok": true}',
                "is_error": False,
            }
        ],
    }
    converted = _to_bedrock_message(message)
    result = converted["content"][0]["toolResult"]
    assert result["toolUseId"] == "toolu_1"
    assert result["status"] == "success"
    assert result["content"][0]["json"] == {"ok": True}

    normalized = _from_bedrock_block(
        {"toolUse": {"toolUseId": "abc", "name": "recall_memory", "input": {"fund": "Fund"}}}
    )
    assert normalized == {"type": "tool_use", "id": "abc", "name": "recall_memory", "input": {"fund": "Fund"}}


def test_bedrock_converse_payload_shape():
    payload = _bedrock_converse_payload(
        system="system",
        messages=[{"role": "user", "content": "hello"}],
        tools=[{"name": "recall_memory", "description": "Read memory", "input_schema": {"type": "object"}}],
        max_tokens=123,
    )

    assert payload["system"] == [{"text": "system"}]
    assert payload["messages"][0]["content"] == [{"text": "hello"}]
    assert payload["inferenceConfig"] == {"maxTokens": 123}
    assert payload["toolConfig"]["tools"][0]["toolSpec"]["name"] == "recall_memory"


def test_llm_visible_result_compacts_large_read_payload():
    result = {
        "fund_metadata": {"fund": "Fund"},
        "coverage": {},
        "acid_rows": [
            {"row_id": "small", "acid": "A", "active_rolled_exposure": "0.1", "very_large_field": "drop me"},
            {"row_id": "large", "acid": "B", "active_rolled_exposure": "5.0", "very_large_field": "drop me"},
        ],
        "diagnostics": {},
        "run_metadata": {},
    }

    compacted = _llm_visible_result(
        tool_name="get_fund_snapshot",
        result=result,
        tool_kind="read",
        is_error=False,
    )

    assert compacted["acid_row_count"] == 2
    assert compacted["top_active_rows"][0] == {
        "row_id": "large",
        "acid": "B",
        "active_rolled_exposure": "5.0",
        "citation_ref": "csv:artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv#row_id=large",
    }
    assert "very_large_field" not in compacted["top_active_rows"][0]
