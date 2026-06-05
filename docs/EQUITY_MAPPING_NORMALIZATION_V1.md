# Equity Mapping Normalization v1

## Purpose

This document defines how the current equity mapping file should be normalized into the shared ACID mapping schema.

Source file observed locally:

- `Equity_mapping_file.csv`

Current columns:

- `acid`
- `asset_class_name`
- `category`

## Intake Result

The current equity mapping file is valid as a seed taxonomy file.

Observed checks:

- row count: 476
- duplicate ACIDs: 0
- blank required values: 0
- category values observed: `Country`, `Region`, `Sector`, `Industry`, `Style`
- coverage versus `202602-Equity Model.xlsx`: exact 1:1 ACID match

That means the file is suitable for immediate enrichment use, even though it is thinner than the full shared ACID mapping schema.

## Normalization Rule

The current 3-column file should be normalized into the shared schema using deterministic defaults.

### Direct field mapping

- `acid` -> `acid`
- `asset_class_name` -> `asset_class_name`
- `model_family` -> `equity`
- `family` -> use the current `category` value

### Category-driven interpretation mapping

- `Country` -> `interpretation_type = region_relative_value`
- `Region` -> `interpretation_type = region_relative_value`
- `Sector` -> `interpretation_type = sector_relative_value`
- `Industry` -> `interpretation_type = industry_relative_value`
- `Style` -> `interpretation_type = style_relative_value`

## Comparison Group Defaults

Until a richer mapping file is provided, use category-level default comparison groups.

- `Country` -> `equity_country_relative_value`
- `Region` -> `equity_region_relative_value`
- `Sector` -> `equity_sector_relative_value`
- `Industry` -> `equity_industry_relative_value`
- `Style` -> `equity_style_relative_value`

These defaults are intentionally generic. They allow the agent to reason correctly at the category level without pretending to know a more specific peer set than the current mapping file provides.

## Investable Flag Default

Set:

- `investable_flag = true`

for v1 normalization of the current equity mapping file.

Reason:

The file is being used as the current working opportunity set for the analyst agent, and the PM has not provided a separate equity investability exclusion list yet.

If a later mapping file distinguishes benchmark-only or non-implementable exposures, that file should override this default.

## Recommended Optional Defaults

The following shared-schema fields may be left null in the normalized v1 equity mapping until richer metadata is available:

- `subtype`
- `market_scope`
- `region`
- `country`
- `sector`
- `industry`
- `style`
- `currency_exposure_type`
- `maturity_bucket`
- `curve_aware`
- `parent_family`
- `relative_value_group`
- `index_provider`
- `benchmark_role`
- `notes`

## Shared Schema Update

Because the current equity mapping file includes an `Industry` category, the shared schema should explicitly recognize:

- `industry_relative_value`

as an allowed `interpretation_type`.

## Example Normalized Rows

### Country example

```csv
acid,asset_class_name,model_family,family,comparison_group,interpretation_type,investable_flag
AU EQ,Australia,equity,Country,equity_country_relative_value,region_relative_value,true
```

### Sector example

```csv
acid,asset_class_name,model_family,family,comparison_group,interpretation_type,investable_flag
ACWI EN EQ,AC World Energy,equity,Sector,equity_sector_relative_value,sector_relative_value,true
```

### Industry example

```csv
acid,asset_class_name,model_family,family,comparison_group,interpretation_type,investable_flag
Wld EN10 EQ,World Industry Energy,equity,Industry,equity_industry_relative_value,industry_relative_value,true
```

### Style example

```csv
acid,asset_class_name,model_family,family,comparison_group,interpretation_type,investable_flag
ACWI LRG G EQ,ACWI Large Cap Growth Stocks,equity,Style,equity_style_relative_value,style_relative_value,true
```

## Practical Use

This normalization approach allows the current equity mapping file to be used immediately for:

- category-aware agent interpretation
- top-mover grouping by equity category
- correct relative-value framing by category
- later extension into a richer mapping file without breaking parser contracts

## Next Step

When desired, the current equity mapping file can be upgraded from a taxonomy seed into a richer shared-schema mapping file by adding optional fields rather than replacing the structure entirely.
