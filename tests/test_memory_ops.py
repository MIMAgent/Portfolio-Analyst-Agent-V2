"""Proposed-only memory write operation tests."""

from __future__ import annotations

from datetime import date
import json

import pytest

from portfolio_analyst_agent.memory_approval import approve_memory_record, list_proposed_memory
from portfolio_analyst_agent.memory_ops import apply_ops
from portfolio_analyst_agent.memory_store import recall_memory_store


def _governance_file(tmp_path, *, auto_apply=False):
    path = tmp_path / "agent_governance.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "agent_governance_v1",
                "events": [
                    {
                        "governance_version": "test",
                        "effective_from": "2026-01-01",
                        "parameters": {"auto_apply_memory_ops": auto_apply},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _run_metadata():
    return {
        "review_run_id": "rrun_test",
        "snapshot_date": "2026-04-06",
        "as_of_date": "2026-04-06",
    }


def test_create_thesis_appends_proposed_memory_row(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    applied = apply_ops(
        fund="Fund",
        memory_path=memory_path,
        governance_path=_governance_file(tmp_path),
        run_metadata=_run_metadata(),
        ops=[
            {
                "op_type": "create_thesis",
                "acid": "US LRG EQ",
                "thesis_text": "Large cap thesis.",
                "thesis_drivers": ["valuation"],
                "falsification_conditions": "If driver weakens.",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
            }
        ],
    )

    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    row = payload["tables"]["thesis_ledger"][0]
    assert applied[0]["review_state"] == "proposed"
    assert row["review_state"] == "proposed"
    assert row["status"] == "active"


def test_shadow_recall_can_include_proposed_memory(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    apply_ops(
        fund="Fund",
        memory_path=memory_path,
        governance_path=_governance_file(tmp_path),
        run_metadata=_run_metadata(),
        ops=[
            {
                "op_type": "create_thesis",
                "acid": "US LRG EQ",
                "thesis_text": "Large cap thesis.",
                "thesis_drivers": ["valuation"],
                "falsification_conditions": "If driver weakens.",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
            }
        ],
    )

    authoritative = recall_memory_store(
        fund="Fund",
        snapshot_date=date(2026, 4, 6),
        as_of_date=date(2026, 4, 6),
        memory_path=memory_path,
    )
    shadow = recall_memory_store(
        fund="Fund",
        snapshot_date=date(2026, 4, 6),
        as_of_date=date(2026, 4, 6),
        memory_path=memory_path,
        include_proposed=True,
    )

    assert authoritative["thesis_ledger"] == []
    assert authoritative["summary"]["authority_rule"] == "approved_applied_only"
    assert shadow["thesis_ledger"][0]["review_state"] == "proposed"
    assert shadow["summary"]["authority_rule"] == "approved_applied_proposed_shadow"


def test_approve_memory_record_appends_approved_copy(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    applied = apply_ops(
        fund="Fund",
        memory_path=memory_path,
        governance_path=_governance_file(tmp_path),
        run_metadata=_run_metadata(),
        ops=[
            {
                "op_type": "create_thesis",
                "acid": "US LRG EQ",
                "thesis_text": "Large cap thesis.",
                "thesis_drivers": ["valuation"],
                "falsification_conditions": "If driver weakens.",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
            }
        ],
    )
    record_id = applied[0]["record_id"]

    proposed = list_proposed_memory(memory_path=memory_path)
    result = approve_memory_record(
        table="thesis_ledger",
        record_id=record_id,
        approved_by="analyst@example.com",
        memory_path=memory_path,
        note="Reviewed",
    )
    recalled = recall_memory_store(
        fund="Fund",
        snapshot_date=date(2026, 4, 6),
        as_of_date=date(2026, 4, 6),
        memory_path=memory_path,
    )

    assert proposed[0]["record_id"] == record_id
    assert result["review_state"] == "approved"
    assert recalled["thesis_ledger"][0]["review_state"] == "approved"
    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    assert len(payload["tables"]["thesis_ledger"]) == 2


def test_auto_apply_true_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="auto_apply_memory_ops=false"):
        apply_ops(
            fund="Fund",
            memory_path=tmp_path / "memory_records.json",
            governance_path=_governance_file(tmp_path, auto_apply=True),
            run_metadata=_run_metadata(),
            ops=[
                {
                    "op_type": "create_thesis",
                    "acid": "US LRG EQ",
                    "thesis_text": "Large cap thesis.",
                    "thesis_drivers": ["valuation"],
                    "falsification_conditions": "If driver weakens.",
                    "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
                }
            ],
        )


def test_conflicting_ops_in_one_call_are_rejected(tmp_path):
    op = {
        "op_type": "create_thesis",
        "acid": "US LRG EQ",
        "thesis_text": "Large cap thesis.",
        "thesis_drivers": ["valuation"],
        "falsification_conditions": "If driver weakens.",
        "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
    }
    with pytest.raises(ValueError, match="Conflicting memory ops"):
        apply_ops(
            fund="Fund",
            memory_path=tmp_path / "memory_records.json",
            governance_path=_governance_file(tmp_path),
            run_metadata=_run_metadata(),
            ops=[op, {**op, "thesis_text": "Different."}],
        )


def test_append_only_challenge_close_reads_latest_status(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    governance_path = _governance_file(tmp_path)
    opened = apply_ops(
        fund="Fund",
        memory_path=memory_path,
        governance_path=governance_path,
        run_metadata=_run_metadata(),
        ops=[
            {
                "op_type": "open_challenge",
                "trigger_candidate_id": "trig_1",
                "acid": "US LRG EQ",
                "trigger_type": "sign_disagreement",
                "challenge_text": "Explain this disagreement.",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
            }
        ],
    )
    challenge_id = opened[0]["record_id"]

    apply_ops(
        fund="Fund",
        memory_path=memory_path,
        governance_path=governance_path,
        run_metadata=_run_metadata(),
        ops=[
            {
                "op_type": "close_challenge",
                "challenge_id": challenge_id,
                "resolution_text": "Resolved by review.",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r2"}],
            }
        ],
    )

    payload = json.loads(memory_path.read_text(encoding="utf-8"))
    assert len(payload["tables"]["open_challenges"]) == 2

    recalled = recall_memory_store(
        fund="Fund",
        snapshot_date=date(2026, 4, 6),
        as_of_date=date(2026, 4, 6),
        memory_path=memory_path,
    )
    assert recalled["open_challenges"] == []
