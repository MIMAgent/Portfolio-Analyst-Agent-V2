# Mapping Status - 2026-04-06

## Resolution

The previously flagged equity mapping anomaly has now been resolved.

Confirmed PM decision:

- `EM UT EQ` / `EM Utilities` should be classified as `Sector`, not `Industry`

## Source Updates Applied Locally

The following local source files were updated to reflect that correction:

- `Equity_mapping_file.csv`
- `equity_mapping_normalized_v1.csv`

The normalized interpretation was updated accordingly:

- `family = Sector`
- `comparison_group = equity_sector_relative_value`
- `relative_value_group = equity_sector_relative_value`
- `interpretation_type = sector_relative_value`

## Current Close Recommendation

### Equity mapping

Status: `Closed`

Reason:

- seed taxonomy file has already been validated
- normalization rules are defined
- the only flagged anomaly has now been explicitly resolved by PM guidance

### Fixed income mapping

Status: `Closed for current design phase`

Reason:

- parser contract is defined
- shared ACID mapping approach is defined
- treasury hedged-YTM helper governance is defined
- treasury and corporate maturity-bucket interpretation rules are defined

Follow-up that may still happen later:

- intake and validation of the actual fixed income mapping file once it is assembled

That follow-up is an implementation input, not a blocker to closing the current mapping-design decision track.

## Practical Conclusion

It is reasonable to close the current equity and fixed income mapping design workstream.

What remains open in the broader project is not mapping design itself, but downstream implementation work such as:

- monthly algo artifact review
- holdings implementation and cross-reference execution
- first parser/code scaffolding

## Related References

- `docs/ACID_MAPPING_SCHEMA_V1.md`
- `docs/EQUITY_MAPPING_NORMALIZATION_V1.md`
- `docs/EQUITY_MAPPING_INTAKE_2026-04-02.md`
- `docs/FIXED_INCOME_VIR_PARSER_SPEC_V1.md`
- `session_log.md`
