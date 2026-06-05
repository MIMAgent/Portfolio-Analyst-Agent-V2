"""Trigger tests focused on the C2 coverage-honoring contract.

A sign-disagreement trigger compares an active bet against its benchmark. When a
fund has no benchmark coverage, firing the trigger is meaningless (audit C2): the
trigger must honor the `benchmark_coverage_ok` flag emitted upstream.
"""

from __future__ import annotations

from portfolio_analyst_agent.challenge_triggers import (
    _benchmark_coverage_ok,
    _dedupe_trigger_rows,
    _evaluate_better_expression_candidate,
    _matching_exception_ids,
)
from portfolio_analyst_agent.acid_mapping import AcidMappingRow, MappingIndex


def test_coverage_ok_honors_explicit_flag_true():
    assert _benchmark_coverage_ok({"benchmark_coverage_ok": "True"}) is True


def test_coverage_ok_honors_explicit_flag_false():
    assert _benchmark_coverage_ok({"benchmark_coverage_ok": "False"}) is False


def test_coverage_ok_falls_back_to_benchmark_match_pct_when_flag_absent():
    # Older alignment CSVs predate the explicit flag; presence of a benchmark match
    # percentage stands in for coverage.
    assert _benchmark_coverage_ok({"benchmark_match_pct": "1.0"}) is True
    assert _benchmark_coverage_ok({"benchmark_match_pct": ""}) is False
    assert _benchmark_coverage_ok({}) is False


# --- H2: deterministic perspective dedupe ------------------------------------

def _persp_rows(order):
    return [
        {"acid_type": "acid_country", "acid": "X", "algo_perspective": p, "row_id": f"r_{p}"}
        for p in order
    ]


def test_dedupe_prefers_local_real_regardless_of_order():
    for order in (["usd_unhedged", "local_real"], ["local_real", "usd_unhedged"]):
        (picked,) = _dedupe_trigger_rows(_persp_rows(order))
        assert picked["algo_perspective"] == "local_real"


def test_dedupe_fallback_is_order_independent():
    # No local_real present: the pick must not depend on CSV row order (audit H2).
    a = _dedupe_trigger_rows(_persp_rows(["usd_unhedged", "usd_hedged"]))
    b = _dedupe_trigger_rows(_persp_rows(["usd_hedged", "usd_unhedged"]))
    assert a[0]["algo_perspective"] == b[0]["algo_perspective"]


# --- Exception governance ----------------------------------------------------

def test_proposed_exception_does_not_suppress_trigger():
    exceptions = [
        {
            "exception_id": "exc_proposed",
            "review_state": "proposed",
            "scope": "acid",
            "acid": "US LRG EQ",
            "trigger_types": ["sign_disagreement"],
        },
        {
            "exception_id": "exc_approved",
            "review_state": "approved",
            "scope": "acid",
            "acid": "US LRG EQ",
            "trigger_types": ["sign_disagreement"],
        },
    ]

    assert _matching_exception_ids(exceptions, acid="US LRG EQ", trigger_type="sign_disagreement") == [
        "exc_approved"
    ]


# --- Trigger 5: better expression available ----------------------------------

def test_better_expression_fires_when_investable_peer_has_better_stf(tmp_path):
    mapping = MappingIndex(
        [
            AcidMappingRow(
                row_id="m1",
                acid="US LRG EQ",
                fields={
                    "comparison_group": "us_equity",
                    "relative_value_group": "us_equity",
                    "investable_flag": "true",
                    "asset_class_name": "US Large",
                    "interpretation_type": "broad_market_beta",
                },
            ),
            AcidMappingRow(
                row_id="m2",
                acid="US SML EQ",
                fields={
                    "comparison_group": "us_equity",
                    "relative_value_group": "us_equity",
                    "investable_flag": "true",
                    "asset_class_name": "US Small",
                    "interpretation_type": "style_relative_value",
                },
            ),
        ],
        source_path=tmp_path / "mapping.csv",
    )
    row = {
        "row_id": "fms_current",
        "acid": "US LRG EQ",
        "acid_type": "acid_country",
        "active_rolled_exposure": "2.0",
        "fund_target_rolled_exposure": "60.0",
        "fund_benchmark_rolled_exposure": "58.0",
        "vir_join_status": "matched_to_vir",
        "vir_workbook_type": "equity_model",
        "vir_stf": "1.0",
        "vir_snapshot_date": "2026-04-06",
    }
    vir_signal_lookup = {
        "US SML EQ": {
            "snapshot_date": "2026-04-06",
            "stf": "2.5",
            "row_id": "vir_peer",
        }
    }

    candidate = _evaluate_better_expression_candidate(
        fund="Fund",
        snapshot_date=__import__("datetime").date(2026, 4, 6),
        row=row,
        mapping_index=mapping,
        vir_signal_lookup=vir_signal_lookup,
        exceptions=[],
    )

    assert candidate["evaluation_status"] == "fired"
    assert candidate["best_peer_acid"] == "US SML EQ"
