# Challenge Trigger Calibration 2026-04-29

## Purpose

This note records the current calibration decision for the first deterministic `sign_disagreement` trigger in Model 1.

This is intentionally a governance note rather than a permanent schema document.
The rule below is the current operating rule.
It may be changed later if PM review shows too much noise or too much missed signal.

## Current Decision

We are keeping the first trigger implementation narrow and deterministic.

The current `sign_disagreement` logic now has three analytical outcomes for rows that have:

- material active exposure
- matched equity VIR
- a top-quartile or bottom-quartile VIR directional view
- active direction that conflicts with that VIR view

The outcomes are:

- `fired`
- `borderline`
- `suppressed`

Rows that do not meet the directional conflict condition remain `not_triggered`.
Rows without usable VIR remain `not_evaluable`.

## Current Rule

### Base materiality gate

- `abs(active_rolled_exposure) >= 1.0`

### VIR directional gate

- `rank_percentile <= 0.25` means VIR directional view = `overweight`
- `rank_percentile >= 0.75` means VIR directional view = `underweight`
- middle quartiles are `neutral`

### Current fired vs borderline split

If the row has a directional conflict:

- classify as `fired` when either:
  - `abs(active_rolled_exposure) >= 1.5`
  - or the VIR percentile is stronger than the quartile edge:
    - `rank_percentile <= 0.20`
    - or `rank_percentile >= 0.80`
- otherwise classify as `borderline`

### Suppression

If an active accepted exception covers the `(fund, acid, trigger_type)`, the trigger is classified as:

- `suppressed`

This applies even if the row would otherwise be `fired` or `borderline`.

## Why This Rule Was Chosen

This calibration was chosen after reviewing the first pilot outputs.

The earlier simpler rule treated every quartile disagreement above `1.0` active exposure as a full trigger.
That created at least one row that felt analytically plausible but slightly too weak to lock in as a full trigger:

- `MStar International Equity`
  - `NL EQ`
  - active `+1.0788`
  - VIR rank percentile `0.7970`

That row is now treated as `borderline` instead of `fired`.

At the same time, stronger rows still remain fully fired, such as:

- `MStar US Equity`
  - `US ID EQ`
  - active `+3.4307`
  - VIR rank percentile `0.9060`
- `MStar International Equity`
  - `EU ID EQ`
  - active `+2.3010`
  - VIR rank percentile `0.8226`
- `MStar International Equity`
  - `JP IT EQ`
  - active `+1.0249`
  - VIR rank percentile `0.9081`

## Options Considered

### Option 1

Raise the global materiality threshold above `1.0`.

Why not chosen now:

- too blunt
- risks suppressing genuinely important rows that are strongly negative on VIR but only modestly above `1.0`

### Option 2

Tighten the quartile cutoff and keep only fire/no-fire.

Why not chosen now:

- removes useful nuance
- hides rows that deserve human review but not full challenge status

### Option 3

Keep the current threshold and add a `borderline` state.

Why chosen now:

- preserves stronger signals
- reduces noise
- keeps weaker disagreements visible without overcommitting them as formal fired triggers

## Important Note

This is the current operating rule.
It does not have to be permanent.

It should be changed later if PM review shows either of these:

- too many borderline rows that should really be fired
- too many fired rows that should really be borderline or ignored

The intended next review step is:

1. review fired and borderline rows against PM judgment
2. decide whether the thresholds are still right
3. then lock or revise the calibration before broadening the trigger set
