"""Approved market-context source registry tests."""

from __future__ import annotations

from portfolio_analyst_agent.market_context_sources import approved_source_domains, load_approved_market_context_sources


def test_factset_earnings_insight_is_approved_source():
    payload = load_approved_market_context_sources()
    sources = {source["source_id"]: source for source in payload["sources"]}

    factset = sources["factset_earnings_insight"]
    assert factset["domain"] == "advantage.factset.com"
    assert factset["url"].endswith("EarningsInsight_052926A.pdf")
    assert "earnings_revisions" in factset["approved_use"]
    assert "valuation_context" in factset["approved_use"]
    assert "advantage.factset.com" in approved_source_domains()


def test_core_credible_market_context_domains_are_approved():
    domains = approved_source_domains()

    assert {
        "advantage.factset.com",
        "bls.gov",
        "ismworld.org",
        "federalreserve.gov",
        "spglobal.com",
        "nasdaq.com",
        "goldmansachs.com",
    }.issubset(domains)
