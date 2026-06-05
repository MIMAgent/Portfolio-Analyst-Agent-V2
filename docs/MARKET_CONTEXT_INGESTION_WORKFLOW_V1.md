# Market Context Ingestion Workflow V1

Purpose: let the agent use approved real-world context without manually writing `monthly_market_context.csv`.

## Live Approved-Source Search

For current-period review, the agent can search approved source domains and cache citable context rows:

```bash
python3 scripts/search_market_context.py \
  --query "US technology earnings revisions AI capex" \
  --snapshot-date 2026-06-04 \
  --as-of-date 2026-06-04 \
  --acid "US IT EQ"
```

This writes or appends rows to:

```text
artifacts/market_context/monthly_market_context.csv
```

The LLM runtime exposes the same path through `search_market_context`. The model does not browse arbitrary sites; search queries are scoped to `config/approved_market_context_sources.json`, and any result outside the approved domains is discarded before citation.

Live search is intended for current monthly review. Historical replay/backtest runs should use context files that were available as of the replay date to avoid hindsight contamination.

## Folder Layout

Put approved Markdown or text notes here:

```text
artifacts/market_context/source_docs/
```

Run:

```bash
python3 scripts/ingest_market_context.py \
  --snapshot-date 2026-04-06 \
  --as-of-date 2026-04-06
```

This writes:

```text
artifacts/market_context/monthly_market_context.csv
```

The live agent reads that CSV through `get_market_context`.

## Source Note Format

Each `.md` or `.txt` file may include a front-matter block:

```markdown
---
snapshot_date: 2026-04-06
as_of_date: 2026-04-06
scope_type: acid
scope_value: US ID EQ
priority: 1
headline: Industrials cyclical support weakened
source_label: Approved monthly market note
source_date: 2026-04-05
fundamental_readthrough: This matters because the fund is overweight Industrials while VIR and algo signals are negative.
pm_question: Is the Industrials overweight based on idiosyncratic fundamentals or a broader cyclical recovery thesis?
---

Industrials entered the review with weaker cyclical support as rate-cut expectations moved lower and labor-market data softened.
```

If front matter is missing, the script uses CLI defaults and the note body as the narrative.

## Scope Types

- `global`, `market`, or `macro`: returned for all context requests.
- `fund`: returned when `scope_value` matches the fund name.
- `acid`: returned when `scope_value` matches the ACID.
- `comparison_group`: returned when `scope_value` matches the mapping comparison group, such as `us_equity_sectors`.

## Replay Rule

Do not include context that was not known by `as_of_date`.

The script enforces:

- `snapshot_date <= as_of_date`
- `source_date <= as_of_date`

## PDF Workflow

For now, export or save PDFs as Markdown/text first, then place those files in `source_docs`.

PDF parsing can be added later, but keeping V1 text-based makes citations and review easier.
