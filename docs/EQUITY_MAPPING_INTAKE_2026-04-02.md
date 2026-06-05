# Equity Mapping Intake - 2026-04-02

## Source

Local source file received from PM:

- `Equity_mapping_file.csv`

This file is treated as the current equity ACID seed taxonomy file.

## Validation Summary

Observed checks from the local intake pass:

- row count: `476`
- duplicate ACIDs: `0`
- blank `acid` values: `0`
- blank `asset_class_name` values: `0`
- blank `category` values: `0`

Observed categories and counts:

- `Country`: `72`
- `Region`: `65`
- `Sector`: `142`
- `Industry`: `100`
- `Style`: `97`

## Interpretation Decision

The file is valid for immediate use as a seed taxonomy input.

It should not replace the shared mapping schema.
Instead, it should be normalized according to:

- `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`

That means the file provides the current row-level equity ACID taxonomy, while the shared schema and normalization rules provide the behavioral interpretation fields the agent needs.

## Warning Review Item

One likely source anomaly was observed during intake:

- `EM UT EQ` / `EM Utilities` is labeled as `Industry`

This looks inconsistent with the surrounding emerging-market sector sleeve pattern, where nearby ACIDs are mapped as `Sector`.

v1 handling recommendation:

- preserve the source file as provided
- treat this row as a warning for PM review
- do not silently rewrite the source taxonomy without explicit confirmation

## Result

The equity mapping intake is accepted.

The repo now has:

- the shared schema in `docs/ACID_MAPPING_SCHEMA_V1.md`
- the normalization contract in `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`
- this intake record documenting the actual seed file received on 2026-04-02
