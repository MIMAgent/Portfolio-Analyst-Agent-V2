# Holdings Exposure Mapping Decision v1

Last updated: April 2, 2026

## Decision

For the current holdings workflow, the holdings file should be treated as an exposure-based file rather than a security-level holdings file.

The file is expected to contain human-readable labels for benchmark and portfolio exposures such as:

- `US Industrials`
- `Japan Utilities`
- `Large Cap Value`
- `Korea`

These labels will be mapped to the appropriate ACID through an explicit governed crosswalk.

## What This Means

This resolves the current holdings-design question in the following way:

- the holdings file does not need to contain `ACID` directly for v1
- the primary join method for this holdings source will be an approved label-to-ACID crosswalk
- the crosswalk should be exact and governed, not fuzzy and implicit

## Recommended Join Key Shape

Do not key only on raw label text when the label could be ambiguous.

Recommended production join key:

- `model_family`
- `exposure_dimension`
- `source_label`
- optional context field if needed

Recommended dimensions:

- `sector`
- `country`
- `style`

Recommended optional context fields when needed:

- `benchmark_family`
- `region_scope`
- `fund_family`
- `source_system`

This matters because some labels may not be globally unique.
For example, `Large Cap Value` may mean different ACIDs depending on whether the context is US, ACWI, EAFE, or another benchmark family.

## Recommended Crosswalk Shape

```csv
model_family,exposure_dimension,source_label,benchmark_family,acid,acid_name,match_method,status,owner,effective_from,notes
```

## Example Rows

```csv
model_family,exposure_dimension,source_label,benchmark_family,acid,acid_name,match_method,status,owner,effective_from,notes
equity,sector,US Industrials,us_equity,US ID EQ,US Industrials,manual_approved,active,pm_team,2026-04-02,US sector exposure row
equity,sector,Japan Utilities,japan_equity,JP UT EQ,Japan Utilities,manual_approved,active,pm_team,2026-04-02,Japan sector exposure row
equity,country,Korea,global_equity,KR EQ,Korea,manual_approved,active,pm_team,2026-04-02,Country exposure row
equity,style,Large Cap Value,us_equity,US LRG V EQ,US Large Cap Value Stocks,manual_approved,active,pm_team,2026-04-02,US style exposure row
equity,style,Large Cap Value,acwi_equity,ACWI LRG V EQ,ACWI Large Cap Value Stocks,manual_approved,active,pm_team,2026-04-02,Global style exposure row
```

## Parser / Enrichment Behavior

Recommended holdings flow for this source:

1. ingest the holdings exposure rows exactly as delivered
2. classify each row by `exposure_dimension`
3. join to the approved exposure-label crosswalk
4. enrich each holdings row with canonical `ACID`
5. flag any unmatched label as `unmapped`
6. produce a validation report for PM review

## Important Constraint

Do not assume that a human-readable label alone is always enough.

Safe cases:

- `US Industrials`
- `Japan Utilities`
- `Korea`

Potentially ambiguous cases:

- `Large Cap Value`
- `Growth`
- `Quality`
- `Utilities` without region context

For ambiguous labels, use the benchmark or portfolio context in the crosswalk key.

## v1 Recommendation

For the expected holdings file:

- use a dedicated crosswalk such as `holdings_exposure_to_acid_crosswalk.csv`
- start with `sector`, `country`, and `style`
- require exact approved mappings
- keep unmapped rows visible for review rather than guessing

## Outcome

This means the holdings ingestion design for v1 should assume:

- exposure-level benchmark and portfolio rows
- human-readable labels as the source representation
- explicit label-to-ACID mapping as the canonical join path
