# Fixed Income Mapping Intake - 2026-04-06

## Source

Local source file prepared for PM review:

- `Fixed Income ACID Intake.csv`

This file is treated as the current fixed income ACID seed taxonomy file.

## Validation Summary

Observed checks from the local intake pass:

- intake row count: `432`
- unique intake ACIDs: `432`
- duplicate intake ACIDs: `0`
- blank `acid` values: `0`
- blank `asset_class_name` values: `0`
- blank `category` values: `0`

Coverage check versus the fixed income model export `202602- Fixed Income Model.csv`:

- model row count: `433`
- unique model ACIDs: `432`
- missing ACIDs in intake versus model unique set: `0`
- extra ACIDs in intake versus model unique set: `0`

Result:

- the intake file is an exact `1:1` coverage match versus the model's unique ACID universe

## Source Data Quirk

One duplicate ACID exists in the raw fixed income model export:

- `US GovRltd: 10+`

This appears twice in the source model CSV.

v1 handling decision:

- preserve the model-export observation as a source-data note
- keep the intake mapping file at one row per ACID
- deduplicate this ACID in the intake artifact

This is a source-file duplication issue, not a mapping-coverage issue.

## Category Families Used

Observed categories and counts in the intake file:

- `ABS`: `1`
- `Agg`: `17`
- `Cash`: `34`
- `CMBS`: `1`
- `Corp`: `47`
- `Corp: HY`: `4`
- `Credit`: `14`
- `EM HC Agg`: `3`
- `EM HC Corp`: `1`
- `EM HC T`: `2`
- `EM LC Gov`: `3`
- `EM LC IL`: `11`
- `EM LC T`: `117`
- `Gov`: `6`
- `GovRltd`: `18`
- `IL`: `53`
- `Lev Loan`: `1`
- `Securitized`: `3`
- `T`: `79`
- `US MBS`: `1`
- `US Muni`: `14`
- `US Muni: HY`: `1`
- `US Universal`: `1`

## Interpretation Decision

The file is valid for immediate use as a thin fixed income seed taxonomy input.

It should not replace the shared mapping schema.
Instead, it should be treated the same way as the equity intake:

- the intake file provides row-level fixed income ACID classification
- the shared schema provides the richer behavioral interpretation fields the agent needs

Relevant governing docs:

- `docs/ACID_MAPPING_SCHEMA_V1.md`
- `docs/FIXED_INCOME_VIR_PARSER_SPEC_V1.md`

## Classification Notes

The category values were assigned according to the fixed income mapping rules already agreed with PM.

Examples:

- treasury and treasury-curve sleeves remain in `T`
- corporate maturity buckets remain in `Corp`
- `EM HC T (Mstar)` and `EM HC T: Gbl Div.` roll into `EM HC T`
- `EM LC T` country and maturity sleeves roll into `EM LC T`
- `Secu` sleeves were normalized to `Securitized`
- `US Universal` remains its own category because it is a distinct strategic benchmark sleeve in the workflow

## Result

The fixed income mapping intake is accepted.

This closes the fixed income mapping artifact intake at the seed-taxonomy level and brings fixed income into parity with the earlier equity intake process.
