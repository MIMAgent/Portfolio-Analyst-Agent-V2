"""Approved-source market-context search tests."""

from __future__ import annotations

import csv
import json

from portfolio_analyst_agent.agent_tools import get_market_context, search_market_context
from portfolio_analyst_agent.market_context_search import SearchDefaults, search_market_context_web


def _registry(path):
    path.write_text(
        json.dumps(
            {
                "schema_version": "approved_market_context_sources_v1",
                "sources": [
                    {
                        "source_id": "factset",
                        "source_name": "FactSet Earnings Insight",
                        "publisher": "FactSet",
                        "domain": "advantage.factset.com",
                        "url": "https://advantage.factset.com/report.pdf",
                        "publication_date": "2026-05-29",
                        "approved_use": ["earnings_revisions"],
                        "default_scope_type": "market",
                        "default_scope_value": "US equity earnings",
                        "relevant_acids": ["US IT EQ"],
                    },
                    {
                        "source_id": "bls",
                        "source_name": "BLS Releases",
                        "publisher": "BLS",
                        "domain": "bls.gov",
                        "url": "https://www.bls.gov/",
                        "publication_date": "",
                        "approved_use": ["labor_market_context"],
                        "default_scope_type": "macro",
                        "default_scope_value": "US labor market",
                        "relevant_acids": ["US ID EQ"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_search_market_context_web_filters_to_approved_domain_and_writes_citable_rows(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    _registry(registry)

    html = """
    <html>
      <a class="result__a" href="https://advantage.factset.com/earnings">FactSet says earnings revisions improved</a>
      <div class="result__snippet">Technology earnings revisions have stabilized.</div>
      <a class="result__a" href="https://example.com/not-approved">Unapproved source</a>
      <div class="result__snippet">This should be filtered out.</div>
    </html>
    """
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [html],
    )

    result = search_market_context_web(
        query="US technology earnings revisions",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US IT EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=3,
        max_sources=1,
    )

    assert result["context_status"] == "searched_approved_sources"
    assert result["new_row_count"] == 1
    assert result["rows"][0]["citation_ref"].startswith(f"csv:{output_csv.as_posix()}#row_id=mctx_")
    assert result["rows"][0]["source_url"] == "https://advantage.factset.com/earnings"

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["scope_type"] == "acid"
    assert rows[0]["scope_value"] == "US IT EQ"
    assert rows[0]["source_label"] == "FactSet Earnings Insight"


def test_search_market_context_tool_rows_are_visible_to_get_market_context(tmp_path, monkeypatch):
    output_csv = tmp_path / "monthly_market_context.csv"
    html = """
    <html>
      <a class="result__a" href="https://advantage.factset.com/earnings">FactSet earnings update</a>
      <div class="result__snippet">Large-cap growth earnings are linked to AI capex expectations.</div>
    </html>
    """
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [html],
    )

    search_result = search_market_context(
        query="US large cap growth AI capex earnings",
        snapshot_date="2026-06-04",
        as_of_date="2026-06-04",
        acid="US LRG G EQ",
        market_context_csv=output_csv,
        max_results=2,
        max_sources=1,
    )
    context = get_market_context(
        snapshot_date="2026-06-04",
        as_of_date="2026-06-04",
        acid="US LRG G EQ",
        market_context_csv=output_csv,
    )

    assert search_result["new_row_count"] == 1
    assert context["context_status"] == "matched_context_rows"
    assert context["rows"][0]["headline"] == "FactSet earnings update"
    assert context["rows"][0]["citation_ref"].startswith(f"csv:{output_csv.as_posix()}#row_id=mctx_")


def test_search_market_context_does_not_write_generic_source_registry_fallback(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    _registry(registry)
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [""],
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_url",
        lambda url, *, timeout_seconds, max_bytes=1_000_000: "<html><title>BLS home</title><meta name=\"description\" content=\"General government statistics.\"></html>",
    )

    result = search_market_context_web(
        query="US industrial labor market wages",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US ID EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=3,
        max_sources=1,
    )

    assert result["context_status"] == "no_approved_source_results"
    assert result["new_row_count"] == 0
    assert result["run_metadata"]["source_diagnostics"][0]["fallback_status"] == "no_query_relevant_source_excerpt"


def test_search_market_context_writes_query_relevant_pdf_excerpt(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    _registry(registry)
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [""],
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_bytes",
        lambda url, *, timeout_seconds, max_bytes=1_000_000: b"%PDF fake",
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._extract_pdf_text",
        lambda pdf_bytes: (
            "Information Technology earnings estimates moved higher as AI capital spending remained resilient. "
            "Consumer staples commentary was unrelated."
        ),
    )

    result = search_market_context_web(
        query="US technology earnings revisions AI capex",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US IT EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=3,
        max_sources=1,
    )

    assert result["context_status"] == "searched_approved_sources"
    assert result["new_row_count"] == 1
    assert "Information Technology earnings estimates" in result["rows"][0]["narrative"]
    assert result["run_metadata"]["source_diagnostics"][0]["fallback_status"] == "query_relevant_source_excerpt"


def test_search_market_context_prefers_specific_excerpt_over_generic_scorecard(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    _registry(registry)
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [""],
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_bytes",
        lambda url, *, timeout_seconds, max_bytes=1_000_000: b"%PDF fake",
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._extract_pdf_text",
        lambda pdf_bytes: (
            "Key Metrics Earnings Scorecard: For Q1 2026, 85% of S&P 500 companies reported a positive EPS surprise. "
            "Information Technology reported strong earnings growth as AI capital spending and data center demand supported revenue estimates. "
            "Industrials commentary was unrelated."
        ),
    )

    result = search_market_context_web(
        query="Information Technology earnings growth AI capex revisions FactSet",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US IT EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=1,
        max_sources=1,
    )

    assert result["new_row_count"] == 1
    assert "Information Technology reported strong earnings growth" in result["rows"][0]["narrative"]


def test_search_market_context_rejects_table_of_contents_excerpt(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    _registry(registry)
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [""],
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_bytes",
        lambda url, *, timeout_seconds, max_bytes=1_000_000: b"%PDF fake",
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._extract_pdf_text",
        lambda pdf_bytes: (
            "Table of Contents Commentary Key Metrics Earnings Growth Revenue Growth Forward Estimates Valuation Charts Q126. "
            "Information Technology revenue growth improved as AI capital spending supported data center demand."
        ),
    )

    result = search_market_context_web(
        query="Information Technology earnings growth AI capex revisions FactSet",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US IT EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=1,
        max_sources=1,
    )

    assert result["new_row_count"] == 1
    assert "Table of Contents" not in result["rows"][0]["narrative"]
    assert "Information Technology revenue growth" in result["rows"][0]["narrative"]


def test_search_market_context_prioritizes_ism_for_industrials_pmi_query(tmp_path, monkeypatch):
    registry = tmp_path / "approved.json"
    output_csv = tmp_path / "monthly_market_context.csv"
    registry.write_text(
        json.dumps(
            {
                "schema_version": "approved_market_context_sources_v1",
                "sources": [
                    {
                        "source_id": "factset_earnings_insight",
                        "source_name": "FactSet Earnings Insight",
                        "publisher": "FactSet",
                        "domain": "advantage.factset.com",
                        "url": "https://advantage.factset.com/report.pdf",
                        "approved_use": ["earnings_growth"],
                        "default_scope_type": "market",
                        "default_scope_value": "US equity earnings",
                        "relevant_acids": ["US ID EQ"],
                    },
                    {
                        "source_id": "ism_pmi_reports",
                        "source_name": "Institute for Supply Management PMI Reports",
                        "publisher": "ISM",
                        "domain": "ismworld.org",
                        "url": "https://www.ismworld.org/supply-management-news-and-reports/reports/ism-pmi-reports/",
                        "approved_use": ["manufacturing_context", "new_orders", "industrial_cycle_context"],
                        "default_scope_type": "macro",
                        "default_scope_value": "US PMI",
                        "relevant_acids": ["US ID EQ"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_search_pages",
        lambda query, *, endpoint, timeout_seconds: [""],
    )
    monkeypatch.setattr(
        "portfolio_analyst_agent.market_context_search._fetch_url",
        lambda url, *, timeout_seconds, max_bytes=1_000_000: "<html><title>ISM PMI</title><meta name=\"description\" content=\"Manufacturing PMI new orders and production weakened for industrial companies.\"></html>",
    )

    result = search_market_context_web(
        query="US Industrials earnings manufacturing PMI new orders capex",
        defaults=SearchDefaults(snapshot_date="2026-06-04", as_of_date="2026-06-04", acid="US ID EQ"),
        output_csv=output_csv,
        approved_sources_path=registry,
        max_results=1,
        max_sources=1,
    )

    assert result["searched_domains"][0] == "ismworld.org"
    assert result["new_row_count"] == 1
    assert "Manufacturing PMI new orders" in result["rows"][0]["narrative"]
