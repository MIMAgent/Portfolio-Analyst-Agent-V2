"""Governance config loading and trigger threshold wiring."""

from __future__ import annotations

import json

from portfolio_analyst_agent.challenge_triggers import _evaluate_better_expression_candidate
from portfolio_analyst_agent.acid_mapping import AcidMappingRow, MappingIndex
from portfolio_analyst_agent.governance import load_governance


def test_load_governance_selects_latest_effective_event(tmp_path):
    path = tmp_path / "agent_governance.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "agent_governance_v1",
                "events": [
                    {
                        "governance_version": "v1",
                        "effective_from": "2026-01-01",
                        "parameters": {"materiality_threshold_active": 1.0, "auto_apply_memory_ops": False},
                    },
                    {
                        "governance_version": "v2",
                        "effective_from": "2026-04-01",
                        "parameters": {"materiality_threshold_active": 2.0, "auto_apply_memory_ops": False},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    governance = load_governance("2026-04-06", governance_path=path)

    assert governance.governance_version == "v2"
    assert governance.float_param("materiality_threshold_active") == 2.0


def test_better_expression_uses_governance_peer_threshold(tmp_path):
    governance_path = tmp_path / "agent_governance.json"
    governance_path.write_text(
        json.dumps(
            {
                "schema_version": "agent_governance_v1",
                "events": [
                    {
                        "governance_version": "strict",
                        "effective_from": "2026-04-01",
                        "parameters": {
                            "materiality_threshold_active": 1.0,
                            "peer_advantage_threshold_stf": 2.0,
                            "auto_apply_memory_ops": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    governance = load_governance("2026-04-06", governance_path=governance_path)
    mapping = MappingIndex(
        [
            AcidMappingRow(
                row_id="m1",
                acid="A",
                fields={"comparison_group": "g", "relative_value_group": "g", "investable_flag": "true"},
            ),
            AcidMappingRow(
                row_id="m2",
                acid="B",
                fields={"comparison_group": "g", "relative_value_group": "g", "investable_flag": "true"},
            ),
        ],
        source_path=tmp_path / "mapping.csv",
    )
    row = {
        "row_id": "r1",
        "acid": "A",
        "active_rolled_exposure": "2.0",
        "vir_join_status": "matched_to_vir",
        "vir_workbook_type": "equity_model",
        "vir_stf": "1.0",
    }

    candidate = _evaluate_better_expression_candidate(
        fund="Fund",
        snapshot_date=__import__("datetime").date(2026, 4, 6),
        row=row,
        mapping_index=mapping,
        vir_signal_lookup={"B": {"snapshot_date": "2026-04-06", "stf": "2.5", "row_id": "v1"}},
        exceptions=[],
        governance=governance,
    )

    assert candidate["evaluation_status"] == "not_triggered"
    assert candidate["best_peer_stf_advantage"] == 1.5
