from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AGENT2_SRC = ROOT / "agent2" / "src"
if str(AGENT2_SRC) not in sys.path:
    sys.path.insert(0, str(AGENT2_SRC))

from agent2.bedrock_review_runner import _validate_review_payload
from agent2.review_packet_builder import _build_challenge_book, _build_pm_questions


def _sample_position(**overrides):
    base = {
        "acid": "US ID EQ",
        "label": "Industrials",
        "category": "Eq Sector",
        "active_weight": 3.34,
        "portfolio_weight": 15.5,
        "benchmark_weight": 12.16,
        "signal_alignment": "diverging",
        "positioning_direction": "overweight",
        "vir_direction": "underweight",
        "algo_direction": "underweight",
        "vir_now": -0.039,
        "vir_delta_mom": -0.006,
        "algo_active_weight": -2.92,
        "decomposition_assessment": "valuation_led",
        "decomposition_driver": "valuation_adjustment_top_down",
        "source_refs": [{"artifact_path": "test.csv", "row_id": "row-1"}],
        "source_breakdown": {
            "security_count": 2,
            "securities": [
                {"security_name": "Honeywell"},
                {"security_name": "RTX"},
            ],
        },
        "active_thesis": {
            "thesis_text": "Maintain baseline thesis tracking for the US industrials overweight.",
            "falsification_conditions": "Revisit if the dominant decomposition driver rotates away from valuation support.",
        },
        "internal_history_excerpt": "The Industrials overweight is linked to our SMID overweight.",
        "sharepoint_research_summary": "Equity Sector Review: US Industrials. We have a neutral stance on the industrials sector, but some industries are undervalued.",
        "vir_snapshot_date": "2026-05-31",
    }
    base.update(overrides)
    return base


def test_challenge_book_emits_pm_decision_card_fields():
    challenge = _build_challenge_book([_sample_position()])[0]

    assert challenge["challenge_id"] == "ch_us-id-eq_2026-05-31"
    assert challenge["challenge_type"] == "position_vs_signal_divergence"
    assert "Industrials" in challenge["challenge_headline"]
    assert challenge["thesis_under_pressure"].startswith("Maintain baseline thesis tracking")
    assert "Fund weight is" in challenge["positioning_tension"]
    assert "VIR is underweight" in challenge["model_signal_tension"]
    assert challenge["source_quality"] == "model+positioning+memory+sharepoint_research"
    assert "why is this still overweight" not in challenge["primary_pm_question"].lower()


def test_pm_questions_start_from_challenge_book():
    challenge_book = _build_challenge_book([_sample_position()])
    questions = _build_pm_questions([_sample_position()], challenge_book, [], risk_context={"available": False})

    assert questions[0]["question"] == challenge_book[0]["primary_pm_question"]
    assert questions[0]["why_now"] == challenge_book[0]["challenge_headline"]


def test_validate_review_payload_rejects_generic_challenge_questions():
    payload = {
        "executive_summary": "summary",
        "current_positioning": [],
        "what_changed": [],
        "bull_case": [],
        "bear_case": [],
        "devils_advocate": [],
        "challenge_brief": [
            {
                "label": "Industrials",
                "challenge_headline": "Industrials remains overweight against the signal stack.",
                "thesis_under_pressure": "The overweight should still work despite current disagreement.",
                "positioning_tension": "Fund weight is 15.5% versus benchmark 12.2%.",
                "model_signal_tension": "VIR and algo both lean underweight.",
                "vir_decomposition_readthrough": "The move is valuation led.",
                "market_context_readthrough": "The sector research deck is neutral.",
                "pm_decision_fork": "Defend, resize, or keep on watch.",
                "primary_pm_question": "Why is this still overweight?",
                "evidence_needed_next": "Check next month's decomposition.",
                "source_quality": "model+positioning_only",
            }
        ],
        "pm_questions": [],
        "follow_up": [],
        "dashboard_highlights": [],
    }

    with pytest.raises(ValueError, match="generic PM question"):
        _validate_review_payload(payload)
