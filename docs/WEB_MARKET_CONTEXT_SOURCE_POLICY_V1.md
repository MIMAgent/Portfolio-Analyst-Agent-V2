# Web Market Context Source Policy V1

Purpose: define credible sources for live/current-period market context retrieval.

This policy is for live PM review context. Historical replay requires additional as-of-date controls and should not use unrestricted current web search.

## Machine-Readable Source List

Approved sources are stored in:

```text
config/approved_market_context_sources.json
```

Live web/search tooling must use this allowlist before writing any context row. Search can use a broad search endpoint, but accepted results must match one of the approved source domains before the agent may cite them.

## Approved Source Categories

### Official Macro And Policy Sources

Use these for facts about labor markets, inflation, rates, monetary policy, and economic activity:

- U.S. Bureau of Labor Statistics: `bls.gov`
- Institute for Supply Management: `ismworld.org`
- Federal Reserve: `federalreserve.gov`

Preferred uses:

- BLS: payrolls, unemployment, wages, JOLTS, CPI, real earnings.
- ISM: manufacturing/services PMI, new orders, prices, supplier deliveries, employment.
- Federal Reserve: policy statements, minutes, speeches, rate/inflation/labor-market assessment.

### Earnings, Sector, And Market Research Sources

Use these for earnings, sector, valuation, and market context:

- FactSet Earnings Insight: `advantage.factset.com`
- S&P Global Market Intelligence / Ratings: `spglobal.com`
- Nasdaq market reviews: `nasdaq.com`
- Goldman Sachs research insights: `goldmansachs.com`

Preferred uses:

- FactSet: S&P 500 earnings surprises, revenue surprises, earnings growth, revisions, guidance, sector earnings, valuation.
- S&P Global: sector research, credit context, technology capex, earnings context.
- Nasdaq: market and sector performance commentary.
- Goldman Sachs: thematic market research, AI/capex context, valuation context.

## Specific Approved Report

### FactSet Earnings Insight

- Source ID: `factset_earnings_insight`
- Publisher: FactSet Research Systems Inc.
- Domain: `advantage.factset.com`
- URL: `https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_052926A.pdf`
- Publication date: `2026-05-29`

Approved uses:

- Earnings surprises
- Revenue surprises
- Earnings growth
- Earnings revisions
- Earnings guidance
- Sector earnings context
- Valuation context

Why it matters for the current pilot:

- It can sharpen US IT and US Large Growth underweight questions by adding earnings-growth, EPS-surprise, and valuation context.
- It can sharpen US Industrials challenge questions by comparing sector earnings/revenue contribution against the negative VIR/algo signal.
- It can help distinguish valuation-driven underweights from fundamental earnings-revision concerns.

Example PM framing:

```text
If FactSet shows broad positive earnings surprises and upward revisions, does the fund's US IT / US Large Growth underweight remain primarily a valuation discipline, or is it underexposed to improving earnings breadth?
```

## Guardrails

- Treat approved sources as market/fundamental context, not as trade recommendations.
- Cite the cached context row produced from this source in PM-facing output.
- Reject search results from non-approved domains before writing to `monthly_market_context.csv`.
- Do not use a source for historical replay unless its publication date is on or before the review `as_of_date`.
- Treat live search snippets as current-period context. For historical backtests, use curated source files or archived context rows that were available as of the replay date.
- Prefer official sources for economic data facts and research/commentary sources for interpretation.
- When sources conflict, surface the tension rather than forcing a single conclusion.
