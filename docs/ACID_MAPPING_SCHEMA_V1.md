# ACID Mapping Schema v1

## Purpose

This document defines the shared mapping contract for ACID enrichment across equity and fixed income models.

The key design principle is:

The mapping layer must not only classify each ACID. It must also tell the agent how to think about that exposure.

That means the mapping file is not just taxonomy. It is behavioral metadata for the LLM agent.

## Why This Exists

The parser extracts model data.
The mapping file adds analytical meaning.
The LLM agent uses both to form judgment.

Without the mapping layer, the agent can calculate a signal but cannot reliably know:

- what the exposure is actually expressing
- what the right comparison set is
- whether the exposure is broad beta, a curve segment, a style tilt, a sector tilt, or a currency-sensitive expression
- which decomposition or discussion frame matters most
- how a PM would realistically implement or challenge the signal

## Scope

This schema is intended to support:

- equity ACIDs
- fixed income ACIDs
- future multi-asset extensions if needed

## Core Design Rule

Every ACID mapping should include enough metadata for the agent to answer:

- what is this exposure?
- what broader family does it belong to?
- what is the right comparison group?
- what are the key expression dimensions?
- what kind of PM commentary should be generated for it?

## Recommended Mapping File Shape

A CSV is recommended for v1.
One row per ACID.

### Required fields

- `acid`
- `asset_class_name`
- `model_family`
  - example values: `equity`, `fixed_income`
- `family`
  - broad exposure family such as `Agg`, `Corp`, `T`, `Gov`, `US Large Cap`, `Growth`, `Technology`
- `comparison_group`
  - the primary relative-value peer group the agent should use
- `interpretation_type`
  - short code describing how the agent should analyze the exposure
- `investable_flag`
  - `true` or `false`

### Recommended common optional fields

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

## Interpretation Types

The `interpretation_type` field is important because it encodes how the agent should reason about the asset.

Recommended v1 values:

- `broad_market_beta`
  - broad equity or bond market exposure
- `sector_relative_value`
  - compare against broad market and adjacent sectors
- `industry_relative_value`
  - compare against broad market, sector peers, and adjacent industries
- `style_relative_value`
  - compare against broad market and adjacent styles
- `region_relative_value`
  - compare against global or peer-region exposures
- `curve_segment_relative_value`
  - compare one maturity bucket against the broad parent and adjacent curve points
- `spread_product_relative_value`
  - compare spread sectors against alternatives with similar risk usage
- `currency_sensitive_expression`
  - emphasize FX contribution and whether the expression matches portfolio intent
- `inflation_sensitive_expression`
  - emphasize inflation linkage and real-rate context
- `benchmark_anchor`
  - broad strategic sleeve the PM may use as core exposure
- `cash_proxy`
  - emphasize optionality and relative attractiveness versus duration/spread risk

## Universal Behavior Rule

This rule applies across both equities and fixed income:

The agent should not stop at saying an asset class is attractive or unattractive.
It should also explain the more precise opportunity within that broader sleeve.

Examples:

- If a broad corporate index looks fair but short corporates are closer to fair OAS with limited yield give-up, the agent should identify short corporates as the cleaner expression.
- If Treasury curve steepening creates better value in intermediates than the broad Treasury index, the agent should identify the curve segment rather than only the parent family.
- If a broad equity market looks attractive but the opportunity is concentrated in one style or sector, the agent should name that more precise expression.

## Fixed Income-Specific Guidance

### Treasury and corporate curve behavior

For `T` and `Corp`, maturity bucket is part of the thesis, not just metadata.

That means the mapping should support commentary such as:

- short-term corporates are significantly closer to fair OAS than the broad index and may offer attractive value despite limited yield give-up
- continued steepening has created a better opportunity in intermediate Treasuries than in the broad Treasury index

Recommended fields for these ACIDs:

- `family`
- `maturity_bucket`
- `curve_aware = true`
- `parent_family`
- `relative_value_group`

### Treasury allowlist helper rule

For the fixed income USD-hedged-YTM helper, the current treasury allowlist is:

- `AU T`
- `CA T`
- `EU T`
- `EU T: DEU`
- `EU T: ESP`
- `EU T: FRA`
- `EU T: ITA`
- `JP T`
- `UK T`

This allowlist may live either in parser config or in the mapping file. v1 supports either approach.

## Equity-Specific Guidance

Equity mappings should also carry behavioral context, not just category labels.

Examples:

- sector exposures should support comparison versus broad equity and adjacent sectors
- industry exposures should support comparison versus broad equity, sector peers, and adjacent industries
- style exposures should support comparison versus broad market and adjacent styles
- region/country exposures should support comparison versus substitutes and should flag when opportunity is broad-based versus concentrated

Recommended optional fields for equity ACIDs:

- `sector`
- `industry`
- `style`
- `region`
- `country`
- `comparison_group`
- `relative_value_group`

## Example Rows

### Fixed income example

```csv
acid,asset_class_name,model_family,family,subtype,market_scope,currency_exposure_type,maturity_bucket,curve_aware,parent_family,comparison_group,relative_value_group,interpretation_type,investable_flag,index_provider,notes
AU T,Australia Treasury,fixed_income,T,government,Australia,local,intermediate,true,T,dm_treasury_curve,dm_treasury_curve,curve_segment_relative_value,true,Bloomberg,Treasury curve segment used for hedged USD helper rule
```

### Equity example

```csv
acid,asset_class_name,model_family,family,sector,region,comparison_group,relative_value_group,interpretation_type,investable_flag,notes
US Tech,US Technology,equity,Equity Sector,Technology,US,us_equity_sectors,us_equity_sectors,sector_relative_value,true,Compare versus broad US equity and other sectors
```

## Parser Integration Rule

Parsers should not depend on this mapping file to ingest raw model data.
They should be able to ingest the raw snapshot first.

Then, if a mapping file is present, enrichment should attach:

- taxonomy fields
- interpretation fields
- comparison-group metadata
- implementation notes used by the agent

If a mapping row is missing for an ACID:

- ingestion should not fail
- enrichment should record the ACID as unmapped
- the agent should be told that interpretation context is incomplete

## Validation Rules

The mapping file should fail validation if:

- `acid` is duplicated
- any required field is missing
- `interpretation_type` is not in the approved set
- boolean fields are not parseable as booleans

Warn but do not fail if:

- optional fields are missing
- notes are blank
- parent/relative-value groups are absent for exposures that are not curve- or peer-sensitive

## Current Expected Inputs

The next expected mapping artifact is the equity ACID category mapping file.

After that, the same shared schema can be used to decide whether fixed income mappings should live in the same file or in a separate fixed income mapping file.
