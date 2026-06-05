"""Validated write-tool boundary tests."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from portfolio_analyst_agent.citations import CitationError
from portfolio_analyst_agent.agent_runtime.tool_registry import ToolRunContext, build_tool_registry
from portfolio_analyst_agent.pm_review_renderer import render_pm_review_markdown
from portfolio_analyst_agent.schemas import SchemaValidationError
from portfolio_analyst_agent.write_tools import (
    update_memory,
    write_challenge_brief,
    write_change_brief,
    write_sizing_considerations,
)


def _evidence_csv(tmp_path):
    path = tmp_path / "evidence.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "value"])
        writer.writeheader()
        writer.writerow({"row_id": "row_1", "value": "1"})
    return path


def _token(path: Path) -> str:
    return f"csv:{path.as_posix()}#row_id=row_1"


def _header(fund="Fund"):
    return {
        "fund": fund,
        "snapshot_date": "2026-04-06",
        "prior_snapshot_date": "",
        "as_of_date": "2026-04-06",
        "review_run_id": "rrun_1",
        "parser_version": "p",
        "mapping_version": "m",
        "governance_version": "g",
        "algo_version": "a",
        "run_mode": "ad_hoc",
    }


def _change_brief(path):
    token = _token(path)
    return {
        "header": _header(),
        "executive_summary": f"Material change is cited {token}",
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
                "narrative": f"Narrative is cited {token}",
                "evidence_pointers": [{"artifact_path": path.as_posix(), "row_id": "row_1"}],
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


def test_write_change_brief_persists_json_and_markdown(tmp_path):
    evidence = _evidence_csv(tmp_path)
    result = write_change_brief("Fund", _change_brief(evidence), output_root=tmp_path / "out")

    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["pm_review_markdown_path"]).exists()
    assert Path(result["pm_review_html_path"]).exists()
    pm_text = Path(result["pm_review_markdown_path"]).read_text(encoding="utf-8")
    assert "## Key Positioning Tensions" in pm_text
    assert "## Evidence Footnotes" in pm_text
    assert "Metrics: N/A" not in pm_text


def test_write_change_brief_rejects_uncited_claim(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    payload["executive_summary"] = "No citation here."

    with pytest.raises(CitationError):
        write_change_brief("Fund", payload, output_root=tmp_path / "out")


def test_pm_review_uses_explicit_pm_takeaway_and_question(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    token = _token(evidence)
    payload["material_movers"][0]["pm_takeaway"] = f"This is the PM-facing implication {token}"
    payload["material_movers"][0]["review_question"] = f"What would make this exposure too large for the signal? {token}"
    payload["material_movers"][0]["what_would_change_view"] = f"A cited reversal would change the view {token}"

    result = write_change_brief("Fund", payload, output_root=tmp_path / "out")
    pm_text = Path(result["pm_review_markdown_path"]).read_text(encoding="utf-8")

    assert "PM Takeaway" in pm_text
    assert "What would make this exposure too large for the signal?" in pm_text
    assert "What Would Change the View" in pm_text


def test_pm_review_cleans_trailing_commas_and_outer_citation_brackets(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = _change_brief(evidence)
    payload["executive_summary"] = f"Two citations [{token}, {token}]"

    markdown = render_pm_review_markdown(payload)

    assert "[1] [1]" in markdown
    assert f"`{token}`" in markdown
    assert f"`{token},`" not in markdown
    assert "[[1]" not in markdown


def test_write_change_brief_requires_citations_for_pm_takeaway_and_questions(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    token = _token(evidence)
    payload["material_movers"][0]["pm_takeaway"] = f"This is cited {token}"
    payload["material_movers"][0]["review_question"] = "This PM-facing question has no citation."

    with pytest.raises(CitationError, match="review_question"):
        write_change_brief("Fund", payload, output_root=tmp_path / "out")


def test_write_change_brief_rejects_bad_evidence_pointer(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    payload["material_movers"][0]["evidence_pointers"] = [
        {"artifact_path": evidence.as_posix(), "row_id": "missing_row"}
    ]

    with pytest.raises(CitationError, match="missing_row"):
        write_change_brief("Fund", payload, output_root=tmp_path / "out")


def test_pm_review_infers_signal_direction_from_narrative_when_metrics_missing(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    token = _token(evidence)
    payload["material_movers"][0].pop("active_rolled_exposure", None)
    payload["material_movers"][0].pop("vir_stf", None)
    payload["material_movers"][0]["narrative"] = (
        f"US ID EQ fired a sign_disagreement. The fund holds a +3.4 pp active rolled overweight "
        f"while VIR STF is -0.044 {token}"
    )

    result = write_change_brief("Fund", payload, output_root=tmp_path / "out")
    pm_text = Path(result["pm_review_markdown_path"]).read_text(encoding="utf-8")

    assert "active exposure is positive while STF is negative" in pm_text


def test_pm_review_infers_percent_metrics_and_hyphenated_vir_stf(tmp_path):
    evidence = _evidence_csv(tmp_path)
    payload = _change_brief(evidence)
    token = _token(evidence)
    payload["material_movers"][0].pop("active_rolled_exposure", None)
    payload["material_movers"][0].pop("target_rolled_exposure", None)
    payload["material_movers"][0].pop("benchmark_rolled_exposure", None)
    payload["material_movers"][0].pop("vir_stf", None)
    payload["material_movers"][0]["narrative"] = (
        f"Rolled active exposure is -6.89% (fund target 12.23% vs. benchmark 19.11%). "
        f"VIR-STF is -0.0408 {token}"
    )

    result = write_change_brief("Fund", payload, output_root=tmp_path / "out")
    pm_text = Path(result["pm_review_markdown_path"]).read_text(encoding="utf-8")

    assert "**Active:** -6.89%" in pm_text
    assert "**Target:** 12.23%" in pm_text
    assert "**Benchmark:** 19.11%" in pm_text
    assert "**STF:** -0.0408" in pm_text
    assert "Underweight is directionally aligned with a negative STF" in pm_text


def test_write_sizing_rejects_prescriptive_language(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_1",
            "algo_version": "a",
            "mapping_version": "m",
            "run_mode": "ad_hoc",
        },
        "perspective_summary": {"local_real": "", "usd_unhedged": ""},
        "algo_vs_positioning_agreement": [],
        "algo_vs_positioning_disagreement": [
            {
                "acid": "US LRG EQ",
                "perspective": "local_real",
                "narrative": f"Recommend increase to 5% {token}",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "largest_algo_mom_changes": [],
        "coverage_notes": "",
        "evidence_index": [],
    }

    with pytest.raises(SchemaValidationError, match="Prescriptive"):
        write_sizing_considerations("Fund", payload, output_root=tmp_path / "out")


def test_write_sizing_renders_markdown_sections(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_1",
            "algo_version": "a",
            "mapping_version": "m",
            "run_mode": "ad_hoc",
        },
        "perspective_summary": {
            "local_real": f"Local real perspective is cited {token}",
            "usd_unhedged": f"USD perspective is cited {token}",
        },
        "algo_vs_positioning_agreement": [
            {
                "acid": "US LRG EQ",
                "perspective": "local_real",
                "narrative": f"Agreement narrative is cited {token}",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "algo_vs_positioning_disagreement": [
            {
                "acid": "US ID EQ",
                "perspective": "usd_unhedged",
                "narrative": f"Disagreement narrative is cited {token}",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "largest_algo_mom_changes": [
            {
                "acid": "US IT EQ",
                "perspective": "local_real",
                "narrative": f"MoM change narrative is cited {token}",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "evidence_index": [],
    }

    result = write_sizing_considerations("Fund", payload, output_root=tmp_path / "out")
    markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")

    assert "## Perspective Summary" in markdown
    assert "## Algo vs Positioning Agreement" in markdown
    assert "## Algo vs Positioning Disagreement" in markdown
    assert "## Largest Algo MoM Changes" in markdown
    assert "US ID EQ (usd_unhedged): Disagreement narrative" in markdown


def test_write_challenge_requires_fired_trigger_and_challenge_id(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_1",
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
                "cleaner_expression": "",
                "falsification_framing": "",
                "next_review_checkpoint": "Next month",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "evidence_index": [],
    }

    with pytest.raises(SchemaValidationError, match="non-fired"):
        write_challenge_brief("Fund", payload, fired_trigger_ids={"trig_other"}, output_root=tmp_path / "out")

    result = write_challenge_brief("Fund", payload, fired_trigger_ids={"trig_1"}, output_root=tmp_path / "out")
    assert Path(result["json_path"]).exists()


def test_write_challenge_rejects_trigger_type_mismatch(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_1",
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
                "next_review_checkpoint": "Next month",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "evidence_index": [],
    }

    with pytest.raises(SchemaValidationError, match="does not match fired trigger"):
        write_challenge_brief(
            "Fund",
            payload,
            fired_trigger_ids={"trig_1"},
            fired_trigger_types={"trig_1": "decomposition_rotation"},
            output_root=tmp_path / "out",
        )


def test_write_challenge_renders_disagreement_and_checkpoint(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    payload = {
        "header": {
            "fund": "Fund",
            "snapshot_date": "2026-04-06",
            "as_of_date": "2026-04-06",
            "review_run_id": "rrun_1",
            "parser_version": "p",
            "mapping_version": "m",
            "governance_version": "g",
        },
        "items": [
            {
                "challenge_id": "chg_1",
                "trigger_candidate_id": "trig_1",
                "acid": "US ID EQ",
                "trigger_type": "sign_disagreement",
                "position_summary": {},
                "disagreement_statement": f"Disagreement cited {token}",
                "challenge": f"Challenge cited {token}",
                "next_review_checkpoint": "Next month",
                "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
            }
        ],
        "evidence_index": [],
    }

    result = write_challenge_brief("Fund", payload, fired_trigger_ids={"trig_1"}, output_root=tmp_path / "out")
    markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")

    assert "### US ID EQ (sign_disagreement)" in markdown
    assert "**Disagreement**" in markdown
    assert "**Challenge**" in markdown
    assert "**Next Review Checkpoint:** Next month" in markdown


def test_challenge_tool_hydrates_single_fired_trigger_and_common_aliases(tmp_path):
    evidence = _evidence_csv(tmp_path)
    token = _token(evidence)
    context = ToolRunContext(
        fund="Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        run_metadata={
            "review_run_id": "rrun_1",
            "parser_version": "p",
            "mapping_version": "m",
            "governance_version": "g",
            "algo_version": "a",
            "run_mode": "ad_hoc",
        },
        output_root=tmp_path / "out",
        fired_trigger_ids={"trig_1"},
    )
    registry = build_tool_registry(context)

    result = registry["write_challenge_brief"].callable(
        {
            "content": {
                "challenge_items": {
                    "acid": "US ID EQ",
                    "trigger_type": "sign_disagreement",
                    "position_summary": {"acid": "US ID EQ"},
                    "narrative": f"Positioning conflicts with the fired signal {token}",
                    "review_question": f"What evidence would justify keeping this conflict open {token}",
                    "evidence_pointers": [{"artifact_path": evidence.as_posix(), "row_id": "row_1"}],
                }
            }
        }
    )

    assert Path(result["json_path"]).exists()
    payload = Path(result["json_path"]).read_text(encoding="utf-8")
    assert '"challenge_id": "chg_1"' in payload
    assert '"trigger_candidate_id": "trig_1"' in payload
    assert '"disagreement_statement": "Positioning conflicts with the fired signal' in payload
    assert '"challenge": "What evidence would justify keeping this conflict open' in payload


def test_update_memory_delegates_to_memory_ops(tmp_path):
    governance = tmp_path / "agent_governance.json"
    governance.write_text(
        '{"schema_version":"agent_governance_v1","events":[{"governance_version":"g","effective_from":"2026-01-01","parameters":{"auto_apply_memory_ops":false}}]}',
        encoding="utf-8",
    )
    result = update_memory(
        "Fund",
        [
            {
                "op_type": "create_watch_item",
                "acid": "US LRG EQ",
                "watch_text": "Watch this cited observation.",
                "review_checkpoint": "Next month",
                "evidence_pointers": [{"artifact_path": "a.csv", "row_id": "r1"}],
            }
        ],
        run_metadata={"review_run_id": "rrun_1", "snapshot_date": "2026-04-06", "as_of_date": "2026-04-06"},
        memory_path=tmp_path / "memory_records.json",
        governance_path=governance,
    )

    assert result[0]["table"] == "watch_items"
