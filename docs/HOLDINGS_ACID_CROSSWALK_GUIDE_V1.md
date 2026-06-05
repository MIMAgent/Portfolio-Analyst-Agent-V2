# Holdings to ACID Crosswalk Guide v1

## Purpose

This document defines the fallback join approach when a holdings file does not contain `ACID` directly.

Preferred design:

- holdings file includes `ACID`

Fallback design:

- holdings file does not include `ACID`
- use an explicit crosswalk file maintained outside parser code

The crosswalk file should be treated as governed data, not fuzzy logic hidden in the parser.

## Design Principle

Do not use fuzzy matching as the primary production join method.

Use fuzzy matching only to suggest candidates for human review.
The production join should come from one of:

- direct ACID in holdings
- exact source-system code to ACID map
- exact sleeve or benchmark bucket to ACID map
- approved manual crosswalk row

## Recommended File Shape

Use CSV for v1.
One row per approved source-to-ACID mapping.

### Required fields

- `source_system`
- `source_key`
- `source_name`
- `mapping_level`
- `acid`
- `acid_name`
- `match_method`
- `status`
- `owner`
- `effective_from`

### Recommended optional fields

- `fund_scope`
- `benchmark_name`
- `source_category`
- `source_subcategory`
- `currency`
- `notes`
- `confidence`
- `effective_to`
- `reviewed_at`
- `reviewed_by`

## Field Definitions

- `source_system`
  - where the holdings record came from
  - examples: `aladdin`, `factset`, `manual_portfolio_export`, `target_risk_sheet`
- `source_key`
  - the most stable join key available in the holdings source
  - examples: sleeve code, benchmark code, security identifier, internal bucket code
- `source_name`
  - human-readable holdings label as seen by PMs
- `mapping_level`
  - what level the mapping operates at
  - examples: `security`, `sleeve`, `benchmark_bucket`, `asset_class_bucket`
- `acid`
  - canonical ACID used by the VIR models
- `acid_name`
  - human-readable ACID description
- `match_method`
  - examples: `direct_exact`, `code_map`, `manual_approved`, `rules_based_approved`
- `status`
  - examples: `active`, `deprecated`, `pending_review`
- `owner`
  - who owns the correctness of the row
- `effective_from` / `effective_to`
  - date range for valid usage

## Example Crosswalk File

```csv
source_system,source_key,source_name,mapping_level,fund_scope,acid,acid_name,match_method,status,owner,effective_from,effective_to,notes
manual_portfolio_export,US_LC_GROWTH,US Large Cap Growth,sleeve,all_equity_funds,US LRG G EQ,US Large Cap Growth Stocks,manual_approved,active,pm_team,2026-04-01,,Maps equity style sleeve to ACID
manual_portfolio_export,EM_LOCAL_DEBT,EM Local Currency Debt,sleeve,global_multi_asset,EM LC T (Mstar),EM Local Currency Debt (Morningstar Index),manual_approved,active,pm_team,2026-04-01,,Use broad local currency debt ACID until more granular sleeve split exists
manual_portfolio_export,US_TSY_5_7,US Treasury 5-7 Year,sleeve,all_fixed_income_funds,US T 5-7,US Treasury 5-7Y,manual_approved,active,pm_team,2026-04-01,,Curve-sensitive treasury mapping
manual_portfolio_export,US_HY_CORP,US High Yield Corporates,sleeve,credit_funds,Corp: HY,High Yield Corporates,manual_approved,active,pm_team,2026-04-01,,Primary HY spread sleeve
manual_portfolio_export,BLOOMBERG_US_AGG,Bloomberg US Aggregate,benchmark_bucket,target_risk_funds,Agg,US Aggregate Bond Index,code_map,active,pm_team,2026-04-01,,Investable core FI benchmark exposure
manual_portfolio_export,US_TECH,US Technology,sleeve,all_equity_funds,US IT EQ,US Information Technology,manual_approved,active,pm_team,2026-04-01,,Sector sleeve
```

## How To Create It

### Step 1: inspect the holdings source

For a sample holdings file, identify the most stable candidate key.
Use this priority order:

1. `ACID` already present
2. internal sleeve code or benchmark code
3. stable portfolio bucket label
4. security identifier plus approved reference map
5. raw name only, as a last resort

### Step 2: define the mapping grain

Decide what the holdings rows actually represent.
Typical cases:

- security-level holdings
- sleeve-level allocations
- benchmark bucket rows
- strategy model buckets

The crosswalk should use the same grain as the holdings source.
If the holdings file is sleeve-based, do not pretend it is security-level.

### Step 3: map only stable items first

Start with the rows that are obvious and stable:

- broad equity sleeves
- sector sleeves
- Treasury curve buckets
- corporate buckets
- benchmark exposures
- EM hard/local debt sleeves

Leave ambiguous rows as `pending_review` rather than forcing a guess.

### Step 4: validate with PM review

For each mapped row, ask:

- is this the right ACID?
- is this the right comparison group?
- is this the right expression of the holdings sleeve?
- is this mapping too broad or too narrow?

### Step 5: use the crosswalk in ingestion

Holdings parser flow should be:

1. ingest holdings rows as delivered
2. try direct `ACID` join if present
3. if no `ACID`, join through approved crosswalk
4. if no crosswalk hit, label the row `unmapped`
5. include unmapped rows in validation output for correction

## Join Precedence

Recommended production precedence:

1. direct `ACID` from holdings row
2. exact `source_system + source_key` crosswalk hit
3. exact approved benchmark-bucket crosswalk hit
4. exact approved sleeve-name crosswalk hit
5. no match -> `unmapped`

Do not silently fall through to fuzzy matching.

## Validation Rules

The crosswalk should fail validation if:

- the same `source_system + source_key + effective_from` maps to multiple active ACIDs
- required fields are blank
- active rows overlap in time for the same key with conflicting ACIDs

Warn but do not fail if:

- confidence is blank
- notes are blank
- owner is generic rather than person-specific

## Suggested v1 Workflow

For this project, the simplest v1 process is:

- receive one sample holdings file
- identify whether it is security-level or sleeve-level
- draft the first crosswalk manually
- review it with PM lead and Shivika
- use it as the approved fallback join table
- improve it only where unmapped rows appear in testing

## Recommendation

If the holdings file does not include `ACID`, create a separate governed file such as:

- `holdings_to_acid_crosswalk.csv`

Do not embed these mappings directly in parser code.
