from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AGENT2_SRC = ROOT / "agent2" / "src"
if str(AGENT2_SRC) not in sys.path:
    sys.path.insert(0, str(AGENT2_SRC))

from agent2.bedrock_review_runner import _validate_review_payload
from agent2.evidence_pack_builder import build_evidence_pack
from agent2.review_packet_builder import _build_challenge_book, _build_pm_questions


def _sample_risk_context():
    return {
        "available": True,
        "top_style_risk_drivers": [{"label": "Size", "share_of_variance_pct": 9.41}],
        "top_industry_risk_drivers": [{"label": "Capital Markets", "share_of_variance_pct": 0.58}],
        "likely_holdings_contributors": [
            {
                "risk_driver": "Capital Markets",
                "mapped_sector": "Industrials",
                "share_of_variance_pct": 0.58,
                "top_sector_holdings": [{"security_name": "Honeywell"}],
            }
        ],
        "specific_risk_watchlist": [
            {"label": "Industrials", "category": "Eq Sector", "active_weight": 3.34}
        ],
        "return_attribution_mtd": {
            "period_overweight_return": 0.59,
            "period_underweight_return": -3.13,
            "active_industry_factor_returns": -1.24,
        },
    }


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
                {"security_name": "Honeywell", "active_weight": 0.6, "sources": [{"source_name": "MFS", "portfolio_weight": 0.5}]},
                {"security_name": "RTX", "active_weight": 0.4, "sources": [{"source_name": "Systematic Large", "portfolio_weight": 0.3}]},
            ],
        },
        "active_thesis": {
            "thesis_text": "Maintain baseline thesis tracking for the US industrials overweight.",
            "falsification_conditions": "Revisit if the dominant decomposition driver rotates away from valuation support.",
        },
        "internal_history_excerpt": "The Industrials overweight is linked to our SMID overweight.",
        "sharepoint_research": {"primary_match": {"folder_month": "202505"}},
        "sharepoint_research_summary": "Equity Sector Review: US Industrials. We have a neutral stance on the industrials sector, but some industries are undervalued.",
        "vir_snapshot_date": "2026-05-31",
    }
    base.update(overrides)
    return base


def test_challenge_book_emits_pm_decision_card_fields():
    challenge = _build_challenge_book(
        [_sample_position()],
        risk_context=_sample_risk_context(),
        logical_snapshot_date="2026-05-31",
    )[0]

    assert challenge["challenge_id"] == "ch_us-id-eq_2026-05-31"
    assert challenge["challenge_type"] == "position_vs_signal_divergence"
    assert "Industrials" in challenge["challenge_headline"]
    assert challenge["thesis_under_pressure"].startswith("Maintain baseline thesis tracking")
    assert "Fund weight is" in challenge["positioning_tension"]
    assert "VIR is underweight" in challenge["model_signal_tension"]
    assert "Measured risk currently points" in challenge["measured_risk_readthrough"]
    assert "Month-to-date overweight positions contributed" in challenge["return_attribution_readthrough"]
    assert challenge["source_quality"] == "model+positioning+memory+sharepoint_research"
    assert "why is this still overweight" not in challenge["primary_pm_question"].lower()


def test_pm_questions_start_from_challenge_book():
    challenge_book = _build_challenge_book(
        [_sample_position()],
        risk_context=_sample_risk_context(),
        logical_snapshot_date="2026-05-31",
    )
    questions = _build_pm_questions([_sample_position()], challenge_book, [], risk_context={"available": False})

    assert questions[0]["question"] == challenge_book[0]["primary_pm_question"]
    assert questions[0]["why_now"] == challenge_book[0]["challenge_headline"]


def test_validate_review_payload_rejects_generic_challenge_questions():
    payload = {
        "executive_summary": "summary",
        "key_insights": [
            {"label": "A", "insight": "one", "why_it_matters": "now"},
            {"label": "B", "insight": "two", "why_it_matters": "now"},
            {"label": "C", "insight": "three", "why_it_matters": "now"},
        ],
        "challenge_brief": [
            {
                "label": "Industrials",
                "challenge_headline": "Industrials remains overweight against the signal stack.",
                "thesis_under_pressure": "The overweight should still work despite current disagreement.",
                "positioning_tension": "Fund weight is 15.5% versus benchmark 12.2%.",
                "model_signal_tension": "VIR and algo both lean underweight.",
                "vir_decomposition_readthrough": "The move is valuation led.",
                "market_context_readthrough": "The sector research deck is neutral.",
                "measured_risk_readthrough": "Measured risk points to the same bucket.",
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


def test_validate_review_payload_accepts_deep_challenge_fields():
    payload = {
        "executive_summary": "summary",
        "key_insights": [
            {"label": "A", "insight": "one", "why_it_matters": "now"},
            {"label": "B", "insight": "two", "why_it_matters": "now"},
            {"label": "C", "insight": "three", "why_it_matters": "now"},
        ],
        "challenge_brief": [
            {
                "label": "Industrials",
                "challenge_headline": "Industrials remains overweight against the signal stack.",
                "thesis_under_pressure": "The overweight should still work despite current disagreement.",
                "positioning_tension": "Fund weight is 15.5% versus benchmark 12.2%.",
                "model_signal_tension": "VIR and algo both lean underweight.",
                "vir_decomposition_readthrough": "The move is valuation led.",
                "market_context_readthrough": "The sector research deck is neutral.",
                "measured_risk_readthrough": "Measured risk points to the same bucket.",
                "exact_holdings_causing_it": "Honeywell +0.60 pts, RTX +0.40 pts.",
                "exact_vir_algo_decomp_explanation": "VIR -0.039, algo -2.92 pts, top-down valuation is the main drag.",
                "exact_risk_contribution": "Industrials maps to 1.43% of active industry variance.",
                "exact_internal_research_excerpt": "Internal sector review says neutral with selected undervalued industries.",
                "exact_external_market_context": "No approved-source catalyst materially strengthens the bull case.",
                "bull_case": "Selected sub-industries may still be undervalued.",
                "bear_case": "The aggregate overweight is fighting both signals.",
                "devils_advocate": "This may be legacy sleeve positioning rather than refreshed conviction.",
                "what_would_change_my_mind": "A clear reversal in the valuation driver or fresh research support.",
                "pm_decision_fork": "Defend, resize, or keep on watch.",
                "primary_pm_question": "Which exact holdings justify this overweight against both signals?",
                "evidence_needed_next": "Check next month's decomposition and sleeve notes.",
                "confidence": "Medium confidence because holdings and model evidence are strong, but market context is thin.",
                "source_quality": "model+positioning+sharepoint_research",
            }
        ],
        "pm_questions": [],
        "follow_up": [],
        "dashboard_highlights": [],
    }

    validated = _validate_review_payload(payload)

    assert validated["challenge_brief"][0]["confidence"].startswith("Medium")


def test_evidence_pack_defaults_to_deep_memo():
    challenge_book = _build_challenge_book(
        [_sample_position()],
        risk_context=_sample_risk_context(),
        logical_snapshot_date="2026-05-31",
    )
    packet = {
        "header": {"fund": "MStar US Equity", "snapshot_date": "2026-05-31", "review_date": "2026-06-15"},
        "fund_snapshot": {"headline_summary": ["headline"], "largest_overweights": [], "largest_underweights": [], "style_posture": []},
        "material_positions": [_sample_position()],
        "challenge_book": challenge_book,
        "top_movers": [],
        "decomposition_summary": [],
        "risk_context": _sample_risk_context(),
        "data_quality_flags": [{"flag_type": "stale_research"}],
    }

    evidence = build_evidence_pack(packet, refresh_market_context=False)

    assert evidence["run_goal"]["output_style"] == "deep_challenge_memo"
    assert len(evidence["top_challenges"]) == 1
    assert "challenge_market_context" in evidence
    assert "challenge_support_packets" in evidence
    assert "risk_and_attribution" in evidence
    assert "supporting_positions" in evidence


def test_evidence_pack_can_expand_to_top_four_challenges():
    challenge_book = _build_challenge_book(
        [
            _sample_position(),
            _sample_position(acid="US FN EQ", label="Financials", active_weight=3.07),
            _sample_position(acid="US SG EQ", label="United States Sml Growth", category="Eq Size / Style", active_weight=3.01),
            _sample_position(acid="US MV EQ", label="United States Mid Value", category="Eq Size / Style", active_weight=2.60),
        ],
        risk_context=_sample_risk_context(),
        logical_snapshot_date="2026-05-31",
    )
    packet = {
        "header": {"fund": "MStar US Equity", "snapshot_date": "2026-05-31", "review_date": "2026-06-15"},
        "fund_snapshot": {"headline_summary": ["headline"], "largest_overweights": [], "largest_underweights": [], "style_posture": []},
        "material_positions": [
            _sample_position(),
            _sample_position(acid="US FN EQ", label="Financials", active_weight=3.07),
            _sample_position(acid="US SG EQ", label="United States Sml Growth", category="Eq Size / Style", active_weight=3.01),
            _sample_position(acid="US MV EQ", label="United States Mid Value", category="Eq Size / Style", active_weight=2.60),
        ],
        "challenge_book": challenge_book,
        "top_movers": [],
        "decomposition_summary": [],
        "risk_context": _sample_risk_context(),
        "data_quality_flags": [{"flag_type": "stale_research"}],
    }

    evidence = build_evidence_pack(packet, refresh_market_context=False, challenge_count_target=4)

    assert evidence["run_goal"]["output_style"] == "deep_challenge_memo"
    assert evidence["cost_guardrails"]["target_output_tokens"] == 4200
    assert evidence["run_goal"]["challenge_count_target"] == 4
    assert len(evidence["top_challenges"]) == 4
    assert len(evidence["challenge_support_packets"]) == 4


def test_compact_mode_uses_compact_output_style_and_budget():
    challenge_book = _build_challenge_book(
        [_sample_position()],
        risk_context=_sample_risk_context(),
        logical_snapshot_date="2026-05-31",
    )
    packet = {
        "header": {"fund": "MStar US Equity", "snapshot_date": "2026-05-31", "review_date": "2026-06-15"},
        "fund_snapshot": {"headline_summary": ["headline"], "largest_overweights": [], "largest_underweights": [], "style_posture": []},
        "material_positions": [_sample_position()],
        "challenge_book": challenge_book,
        "top_movers": [],
        "decomposition_summary": [],
        "risk_context": _sample_risk_context(),
        "data_quality_flags": [{"flag_type": "stale_research"}],
    }

    evidence = build_evidence_pack(packet, refresh_market_context=False, output_style="challenge_cards")

    assert evidence["run_goal"]["output_style"] == "decision_cards_first"
    assert evidence["cost_guardrails"]["target_output_tokens"] == 2600
