# Bootstrap ACID Mapping 2026-04-29

## Purpose

This note records the first draft machine-readable ACID mapping created directly from the repo's current generated artifacts.

The intent is to unblock early `better_expression_available` development with a reviewable starting point.
It is not yet the final source of truth.

## Generated Artifact

- `data/acid_mapping_bootstrap_v1.csv`

## How It Was Built

The draft mapping is generated from the ACIDs currently present in:

- `artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv`

The generator script is:

- `scripts/build_bootstrap_acid_mapping.py`

## Current Scope

- includes the ACIDs currently flowing through the repo artifacts
- includes both equity and fixed-income rows
- is strongest for:
  - US equity broad / size / style relationships
  - regional and country equity sector rows
  - broad fixed-income parent and curve-style exposures

## Important Note

This file is heuristic.

That means:

- comparison groups were inferred from ACID naming patterns
- parent-family relationships were inferred from naming conventions
- interpretation types were chosen from the schema doc and current repo context

This is the current bootstrap approach.
It is meant to be checked and corrected.

## What Needs Review

The highest-priority human review items are:

1. peer-group logic
   - `comparison_group`
   - `relative_value_group`
2. parent-child logic
   - especially for non-US equity sleeves
   - especially for fixed-income parent families
3. investability choices
   - for example whether certain parent or helper rows should be excluded
4. interpretation types
   - especially for fixed income and special cases like `Alts`

## Why This Exists

The project needs a machine-readable relationship map so the code can answer questions like:

- what are the valid peers for this ACID?
- is this ACID a broad parent or a more precise child?
- is there a better investable expression within the same sleeve?

Without this file, the code cannot build `better_expression_available` cleanly.
