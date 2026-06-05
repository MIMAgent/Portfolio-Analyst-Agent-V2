# Monthly Algo Parser Spec v1

## Purpose

This document defines the v1 parser contract for the monthly algo workbooks used to translate VIR and STF inputs into ACID-level sizing outputs.

The algo files are a separate artifact in the monthly workflow.
They should not replace the VIR review or the Challenge Brief.
They should provide sizing-oriented implementation context that the agent can reference and critique.

## Source Files

Validated local source files on April 9, 2026:

- `Algo LR.xlsx`
- `Algo USD Unhedged.xlsx`

Current interpretation:

- `Algo LR.xlsx` = local real VIR-based algo
- `Algo USD Unhedged.xlsx` = USD VIR-based algo on an unhedged basis for US-based investors

Both workbooks were observed to share the same sheet structure.

## Workbook Sheets

Observed sheets:

- `RegionalSectors`
- `Countries`
- `Global`
- `US`
- chart and support sheets

v1 scope for the analyst-facing parser is limited to:

- `Countries`
- `RegionalSectors`

## Common Structural Rules

### Header row

- row `1` contains the month columns
- column `A` = `acid`
- columns `B:` onward = monthly period columns

Observed month headers are stored as Excel serial dates.
Example serials observed:

- `46081` = `2026-02-28`
- `46053` = `2026-01-31`
- `46022` = `2025-12-31`
- `45991` = `2025-11-30`
- `45961` = `2025-10-31`

Parser requirement:

- convert Excel serial headers into canonical month-end dates

### Row-label rule

- column `A` contains either an ACID or a section label
- blank rows separate sections
- section labels define the metric block to which subsequent ACID rows belong

### Perspective rule

The workbook filename determines the algo perspective:

- `Algo LR.xlsx` -> `local_real`
- `Algo USD Unhedged.xlsx` -> `usd_unhedged`

## Countries Sheet Contract

The `Countries` sheet has a fixed v1 block layout.

### Absolute weights

- data rows: `2:52`
- metric type: `absolute_weight`

### Active weights

- row `54` = section label `Active Weights`
- data rows: `55:105`
- metric type: `active_weight`

### Benchmark weights

- row `107` = section label `Bench Weights`
- data rows: `108:158`
- metric type: `benchmark_weight`

### Month-over-month change in absolute weight

- row `160` = section label `Mom`
- data rows: `161:211`
- metric type: `absolute_weight_mom`

### Month-over-month change in active weight

- row `213` = section label `Active Mom`
- data rows: `214:264`
- metric type: `active_weight_mom`

### Out of scope summary block

- row `266` begins a lower summary table such as `Region Weight`
- v1 parser should exclude this lower summary block from the primary ACID-level algo artifact

## RegionalSectors Sheet Contract

The `RegionalSectors` sheet follows the same logical pattern as `Countries`, but with a different row count because the number of ACIDs is different.

### Absolute weights

- data rows: `2:50`
- metric type: `absolute_weight`

### Active weights

- row `52` = section label `Active Weights`
- data rows: `53:101`
- metric type: `active_weight`

### Benchmark weights

- row `103` = section label `Bench Weights`
- data rows: `104:152`
- metric type: `benchmark_weight`

### Month-over-month change in absolute weight

- row `154` = section label `Mom`
- data rows: `155:203`
- metric type: `absolute_weight_mom`

### Month-over-month change in active weight

- row `205` = section label `Active Mom`
- data rows: `206:254`
- metric type: `active_weight_mom`

### Out of scope summary block

- row `256` begins a lower summary table such as `Region Weight`
- v1 parser should exclude this lower summary block from the primary ACID-level algo artifact

## Normalized Output Contract

The parser should emit one normalized row per:

- `algo_perspective`
- `sheet_dimension`
- `metric_type`
- `acid`
- `period_end`

Recommended normalized fields:

- `snapshot_date`
- `source_file`
- `sheet_name`
- `algo_perspective`
- `sheet_dimension`
  - `countries`
  - `regional_sectors`
- `metric_type`
  - `absolute_weight`
  - `active_weight`
  - `benchmark_weight`
  - `absolute_weight_mom`
  - `active_weight_mom`
- `acid`
- `period_end`
- `value`
- `source_row`
- `source_column`
- `raw_header_value`

## Parsing Rules

- only ingest rows inside the ACID-level blocks defined above
- skip section-label rows
- skip blank rows
- ignore the lower summary block that begins with `Region Weight`
- preserve numeric zero as `0`
- preserve blank numeric cells as `null`
- do not infer missing values

## Validation Rules

Reject ingestion if any of the following are true:

- either workbook is missing
- `Countries` or `RegionalSectors` sheet is missing
- row `1` does not contain parseable month headers in columns `B:` onward
- expected section-label rows are missing
- the parser cannot identify ACID rows within the defined block boundaries

Warn but do not fail if:

- one or more ACIDs appear in only one perspective workbook
- some monthly cells are blank
- an ACID in the algo file is not present in the current mapping file or VIR snapshot

## Agent Use

The algo output should be treated as a separate monthly artifact that helps answer:

- what sizing the algo is suggesting by ACID
- how the suggested absolute and active weights compare with benchmark
- what changed month over month in the algo's preferred exposures
- whether the suggested sizing appears consistent with VIR and current portfolio positioning

The agent should use this artifact to add implementation context, not to issue trade instructions.

## Reporting Role

Recommended v1 artifact name:

- `Sizing Considerations Snapshot`

This artifact should likely include, at minimum:

- top country algo overweights and underweights
- top regional/sector algo overweights and underweights
- largest month-over-month changes in suggested absolute weight
- largest month-over-month changes in suggested active weight
- any material disagreement between the algo signal and current portfolio positioning

## Non-Goals for v1

The algo parser should not:

- replace the holdings parser
- replace VIR decomposition analysis
- treat algo weights as instructions to implement automatically
- ingest the lower summary tables as if they were ACID-level records

## What This Resolves

This review confirms that the monthly algo files are structured enough to be parsed deterministically and incorporated as the separate sizing artifact already contemplated in the Model 1 monthly workflow.

It narrows the remaining open output-package question to presentation and workflow design, not file-read feasibility.
