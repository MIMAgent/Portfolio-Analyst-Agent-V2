# Decomposition Rotation Calibration 2026-04-29

## Purpose

This note records the current v1 implementation rule for the `decomposition_rotation` trigger.

This is the current operating rule.
It is not necessarily the permanent rule.
It should be revised later if PM review, thesis usage, or broader model-family support suggests a better design.

## What The Trigger Means

`decomposition_rotation` asks:

- is the current thesis for an ACID still being driven by the same dominant reason as when the thesis was last affirmed?

It is not checking whether the fund is simply opposite the signal.
It is checking whether the *why* behind the position has materially changed.

## Current Scope

The current implementation is intentionally narrow.

It currently supports:

- equity VIR rows only
- rows with matched VIR
- rows with an active thesis memory record for the same `(fund, acid)`
- rows with a usable `last_affirmed_decomp` payload in thesis memory

It does not yet support:

- fixed-income decomposition rotation
- model-family-specific decomposition sets beyond equity
- thesis auto-seeding
- decomposition-based borderline logic

## Current Decision Rules

### Base materiality gate

- `abs(active_rolled_exposure) >= 1.0`

### Thesis requirement

The row must have an active thesis memory record for `(fund, acid)`.

Without an active thesis, no decomposition-rotation candidate is evaluated.

### Current decomposition fields used for equity

- `growth`
- `yield`
- `inflation`
- `currency_usd`
- `valuation_adjustment_top_down`
- `valuation_adjustment_combined`
- `valuation_adjustment_bottom_up`

### Dominant driver rule

The dominant driver is the decomposition field with the largest absolute value.

### Rotation rule

The trigger fires when:

- the current dominant driver is different from the last affirmed dominant driver
- and the prior dominant driver has weakened enough

### Current weakening rule

The prior dominant driver counts as weakened enough when either:

- its sign flips
- or its absolute magnitude declines by at least `0.01`

## Why This Rule Was Chosen

This is the simplest deterministic first pass that fits the current repo state.

It was chosen because:

- the repo already has equity decomposition fields in `artifacts/equity_vir_history.csv`
- the memory model already defines a thesis ledger
- the project does not yet have reviewed thesis records on disk

So the cleanest implementation was:

- build the engine now
- keep the rule explicit
- require thesis memory
- avoid inventing pseudo-theses from raw data alone

## Current Practical Result

The trigger engine is implemented, but there are currently no live decomposition-rotation candidates because:

- `thesis_ledger` is still empty in `artifacts/agent_memory/memory_records.json`

That is expected at this stage.

## What We Need To Think About To Add Layers Later

### 1. Thesis seeding and affirmation

The trigger becomes useful only when the repo has real thesis records with:

- `last_affirmed_snapshot_date`
- `last_affirmed_decomp`
- a meaningful thesis statement

### 2. Better weakening calibration

The current `0.01` weakening rule is a simple default.

Later we may want:

- different thresholds by asset class
- different thresholds by driver type
- a relative-percent weakening rule instead of a flat absolute rule

### 3. Borderline rotation state

Right now the trigger is:

- `fired`
- `suppressed`
- `not_triggered`
- `not_evaluable`

Later we may want a `borderline` state, similar to the sign-disagreement trigger.

### 4. Fixed-income support

The current version does not support fixed-income decomposition rotation.

That will likely require:

- fixed-income VIR normalization
- a fixed-income decomposition-field set
- possibly different dominant-driver logic

### 5. More nuanced dominant-driver logic

Today we pick the largest absolute field.

Later we may want:

- grouped valuation logic
- model-family-specific driver precedence
- tie-breaking logic when two drivers are close

## Important Note

This is the current operating rule.
It is intentionally conservative and narrow.

It should be changed later if:

- PM review suggests the weakening threshold is too sensitive or not sensitive enough
- the dominant-driver rule is too simplistic
- fixed-income thesis tracking is added
- thesis seeding becomes robust enough to support more frequent rotation analysis
