"""Region-, period- and absence-awareness in the challenge market-context bridge.

These guard the three defects that made the International and GOE reviews cite
market facts that were never in their evidence pack: US-shaped queries fired for
non-US exposures, a cache scope keyed on a region-agnostic label so one sleeve
read another's rows, and an empty result set that looked identical to a
retrieval nobody had run.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
AGENT2_SRC = ROOT / "agent2" / "src"
if str(AGENT2_SRC) not in sys.path:
    sys.path.insert(0, str(AGENT2_SRC))

from agent2 import market_context_bridge as bridge
from portfolio_analyst_agent.market_context_search import (
    _acid_required_words,
    _is_region_mismatch,
    _is_relevant,
    _keywords,
)


HEADER = {
    "fund": "MStar International Equity",
    "snapshot_date": "2026-06-30",
    "review_date": "2026-07-21",
}


def _us_only_registry(tmp_path: Path) -> Path:
    """An approved-source registry with no global and no non-US source."""

    path = tmp_path / "approved.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "approved_market_context_sources_v1",
                "sources": [
                    {
                        "source_id": "ism",
                        "source_name": "ISM PMI Reports",
                        "publisher": "ISM",
                        "domain": "ismworld.org",
                        "url": "https://www.ismworld.org/",
                        "approved_use": ["pmi"],
                        "default_scope_type": "macro",
                        "default_scope_value": "US PMI",
                        "relevant_acids": ["US ID EQ"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def no_rows(monkeypatch):
    """Retrieval that finds nothing, and records every scope it was asked for."""

    scopes: list[str | None] = []

    def fake_get(**kwargs):
        scopes.append(kwargs.get("comparison_group"))
        return {"rows": []}

    def fake_search(**kwargs):
        return {"rows": []}

    monkeypatch.setattr(bridge, "get_market_context", fake_get)
    monkeypatch.setattr(bridge, "search_market_context", fake_search)
    return scopes


@pytest.fixture
def one_row(monkeypatch):
    def fake_get(**kwargs):
        return {
            "rows": [
                {
                    "headline": "Euro area manufacturing new orders",
                    "narrative": "New orders rose.",
                    "source_label": "S&P Global",
                    "source_url": "https://www.spglobal.com/pmi",
                }
            ]
        }

    monkeypatch.setattr(bridge, "get_market_context", fake_get)
    monkeypatch.setattr(bridge, "search_market_context", lambda **kwargs: {"rows": []})


def _european_industrials() -> list[dict]:
    return [{"acid": "EU ID EQ", "label": "Industrials", "category": "Eq Sector"}]


def _build(challenges, *, sources_path=None, **kwargs):
    return bridge.build_challenge_market_context(
        header=HEADER,
        challenge_candidates=challenges,
        approved_sources_path=sources_path or (ROOT / "config" / "approved_market_context_sources.json"),
        **kwargs,
    )


# --- period -----------------------------------------------------------------


def test_period_label_comes_from_the_snapshot_date():
    assert bridge._period_label("2026-06-30") == "June 2026"
    assert bridge._period_label("2026-01-31") == "January 2026"
    assert bridge._period_label("") == ""
    assert bridge._period_label("not-a-date") == ""


def test_queries_carry_the_snapshot_month_not_a_hardcoded_one(no_rows):
    rows = _build(_european_industrials())

    assert rows[0]["period"] == "June 2026"
    assert "June 2026" in rows[0]["query_used"]
    assert "May 2026" not in rows[0]["query_used"]


# --- region -----------------------------------------------------------------


def test_non_us_exposure_is_not_queried_as_us(no_rows):
    rows = _build(_european_industrials())

    query = rows[0]["query_used"]
    assert query.startswith("European industrials sector")
    assert "US " not in query
    assert rows[0]["region_code"] == "EU"
    assert rows[0]["region"] == "European"


def test_us_exposure_still_reads_as_us(no_rows):
    rows = _build([{"acid": "US ID EQ", "label": "Industrials", "category": "Eq Sector"}])

    assert rows[0]["query_used"].startswith("US industrials sector")
    assert rows[0]["region_code"] == "US"


def test_macro_lens_names_the_right_central_bank(no_rows):
    lenses = dict(
        bridge._lenses_for(
            acid="EU FN EQ", label="Financials", category="Eq Sector", driver="", period="June 2026"
        )
    )
    assert "European Central Bank" in lenses["rates"]
    assert "Federal Reserve" not in lenses["rates"]

    us_lenses = dict(
        bridge._lenses_for(
            acid="US FN EQ", label="Financials", category="Eq Sector", driver="", period="June 2026"
        )
    )
    assert "Federal Reserve" in us_lenses["rates"]


def test_country_exposure_keeps_its_own_label(no_rows):
    rows = _build([{"acid": "JP EQ", "label": "Japan", "category": "Country"}])

    assert rows[0]["query_used"].startswith("Japan equity market")
    assert rows[0]["region_code"] == "JP"


# --- cache scope ------------------------------------------------------------


def test_lens_scope_is_keyed_on_the_acid_not_the_shared_label():
    us = bridge._lens_scope(acid="US ID EQ", label="Industrials", lens="pmi")
    eu = bridge._lens_scope(acid="EU ID EQ", label="Industrials", lens="pmi")

    assert us == "US ID EQ · pmi"
    assert us != eu


def test_two_sleeves_sharing_a_label_do_not_share_a_scope(no_rows):
    _build([{"acid": "US ID EQ", "label": "Industrials", "category": "Eq Sector"}])
    us_scopes = [scope for scope in no_rows if scope and "·" in scope]
    no_rows.clear()
    _build(_european_industrials())
    eu_scopes = [scope for scope in no_rows if scope and "·" in scope]

    assert us_scopes and eu_scopes
    assert not set(us_scopes).intersection(eu_scopes)


# --- absence ----------------------------------------------------------------


def test_empty_retrieval_is_reported_as_absent_with_a_reason(no_rows):
    row = _build(_european_industrials())[0]

    assert row["market_evidence_status"] == bridge.STATUS_ABSENT
    assert row["market_evidence_absent_reason"] == bridge.REASON_NO_MATCHING_ROW
    assert "no external market evidence" in row["market_evidence_note"].lower()
    assert row["lenses_attempted"]


def test_region_with_no_approved_source_says_so(no_rows, tmp_path):
    row = _build(_european_industrials(), sources_path=_us_only_registry(tmp_path))[0]

    assert row["market_evidence_status"] == bridge.STATUS_ABSENT
    assert row["market_evidence_absent_reason"] == bridge.REASON_NO_SOURCE_FOR_REGION
    assert "European" in row["market_evidence_note"]
    # Nothing was fetched, so no scope was ever requested.
    assert no_rows == []


def test_us_region_is_still_supported_by_a_us_only_registry(no_rows, tmp_path):
    row = _build(
        [{"acid": "US ID EQ", "label": "Industrials", "category": "Eq Sector"}],
        sources_path=_us_only_registry(tmp_path),
    )[0]

    assert row["market_evidence_absent_reason"] == bridge.REASON_NO_MATCHING_ROW
    assert no_rows  # retrieval was attempted


def test_found_evidence_is_reported_as_present(one_row):
    row = _build(_european_industrials())[0]

    assert row["market_evidence_status"] == bridge.STATUS_PRESENT
    assert row["market_evidence_absent_reason"] == ""
    assert row["market_evidence_note"] == ""
    assert row["market_evidence"]


# --- relevance gate ---------------------------------------------------------


def test_relevance_gate_covers_acids_beyond_the_tuned_four():
    # US FN EQ was previously ungated: any text passed the acid check.
    assert "bank" in _acid_required_words("US FN EQ")
    assert "energy" in _acid_required_words("EU EN EQ")
    assert "small" in _acid_required_words("US SML V EQ")
    # A country exposure has no sector topic; it must name the place.
    assert "japan" in _acid_required_words("JP EQ")


def test_tuned_acid_word_sets_are_unchanged():
    assert _acid_required_words("US IT EQ") == {
        "technology", "tech", "information", "software", "semiconductor", "semiconductors", "ai", "data", "capex",
    }


def test_us_manufacturing_text_is_not_filed_under_a_european_exposure():
    text = (
        "The US ISM manufacturing PMI registered 48.7 percent in June, with new orders "
        "contracting as domestic factory production slowed."
    )
    query = "European industrials sector manufacturing PMI new orders June 2026"

    assert _is_region_mismatch(set(_keywords(text)), acid="EU ID EQ") is True
    assert _is_relevant(text, query=query, acid="EU ID EQ") is False
    # The same passage is legitimate evidence for the US sleeve.
    assert _is_relevant(text, query="US industrials sector manufacturing PMI new orders", acid="US ID EQ") is True


def test_text_naming_its_own_region_survives_the_gate():
    text = (
        "Euro area manufacturing new orders rose in June as European industrial production "
        "recovered, though the US remains the weaker market."
    )
    query = "European industrials sector manufacturing PMI new orders June 2026"

    assert _is_region_mismatch(set(_keywords(text)), acid="EU ID EQ") is False
    assert _is_relevant(text, query=query, acid="EU ID EQ") is True


def test_country_exposures_are_not_region_gated_against_each_other():
    # Only broad blocs are treated as contradictory; a Netherlands exposure is
    # not rejected for a passage that mentions Belgium.
    assert _is_region_mismatch({"belgium", "brussels"}, acid="NL EQ") is False
