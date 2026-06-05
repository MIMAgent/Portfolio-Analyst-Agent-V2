# Market Context Input Spec V1

Purpose: provide approved real-world macro, market, and fundamental context to the LLM agent without relying on model memory or hindsight.

Default artifact path:

```text
artifacts/market_context/monthly_market_context.csv
```

The agent reads this file through `get_market_context` and may cite rows in Change Briefs, Sizing Considerations, and Challenge Briefs.

## Required Columns

- `snapshot_date`: Review snapshot date, formatted `YYYY-MM-DD`.
- `as_of_date`: Latest date by which this context was known, formatted `YYYY-MM-DD`.
- `scope_type`: One of `global`, `market`, `macro`, `fund`, `acid`, or `comparison_group`.
- `scope_value`: Matching value for the scope. Use fund name, ACID, comparison group, or blank for global/macro rows.
- `headline`: Short description of the context.
- `narrative`: Cited, PM-usable factual context.
- `fundamental_readthrough`: Why the context matters for portfolio review.
- `pm_question`: Optional PM question suggested by the context.
- `source_label`: Internal source, research note, market deck, or approved data source name.
- `source_date`: Source date, formatted `YYYY-MM-DD`.

## Optional Columns

- `row_id`: Stable row ID. If blank, the tool generates one.
- `priority`: Sort hint such as `1`, `2`, or `3`.
- `region`: Region label.
- `country`: Country label.
- `sector`: Sector label.
- `asset_class`: Asset-class label.
- `source_url`: Optional URL or internal reference.
- `notes`: Internal notes for operators.

## Example Rows

```csv
row_id,snapshot_date,as_of_date,scope_type,scope_value,priority,headline,narrative,fundamental_readthrough,pm_question,source_label,source_date,region,country,sector,asset_class,source_url,notes
mctx_001,2026-04-06,2026-04-06,acid,US IT EQ,1,Technology earnings revisions softened,"Technology earnings revision breadth weakened into the review date.",A negative VIR signal in US IT should be reviewed against whether earnings weakness is already reflected in valuation or still deteriorating.,Does the PM view the IT underweight as valuation-led or earnings-risk-led?,Monthly Market Context Deck,2026-04-05,US,US,Information Technology,Equity,,
mctx_002,2026-04-06,2026-04-06,comparison_group,us_equity_sectors,2,Rate-cut pricing moved lower,"Market-implied policy easing declined into the review date.",Cyclical sector overweights should be checked against whether rates and labor data support the growth-sensitive exposure.,Is the Industrials overweight based on idiosyncratic fundamentals or a broader cyclical recovery thesis?,Monthly Market Context Deck,2026-04-05,US,US,,Equity,,
```

Do not add context rows for events that occurred after `as_of_date` when running historical replays.
