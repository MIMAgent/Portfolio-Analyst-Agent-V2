# Agent2 Workspace

This folder is the isolated workspace for the next-generation Portfolio Analyst agent.

## Purpose

`agent2/` is now the canonical workspace for the new PM challenge methodology.

The older implementation remains in:

- `src/portfolio_analyst_agent/`
- `scripts/`
- `docs/`

This folder is for:

- the canonical PM challenge runner
- agent2 philosophy
- input and retrieval design
- output schema design
- ingestion and retrieval logic for internal research and old IC docs
- future implementation files specific to agent2

## Working rule

When building agent2, prefer adding new files under this folder rather than changing the older agent unless there is a deliberate migration step.
Inside `agent2`, both output surfaces are supported:

- `deep_challenge_memo` for analyst / PM review
- `challenge_cards` for compact dashboard-friendly output

The default path remains `deep_challenge_memo`.

## Initial contents

- `AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`
- `IC_DOC_INGESTION_SPEC_V1.md`

## Current direction

Agent2 combines three evidence lanes:

1. structured portfolio / VIR / algo / decomposition data
2. internal research and prior IC history
3. trusted external web context

The main output target is a structured review packet that can later power both:

- Word documents
- frontend application views

## Canonical run path

The canonical Bedrock run path in `agent2` is:

- build the review packet
- build the evidence pack
- generate either the deep challenge memo or the compact challenge cards
- save JSON and markdown artifacts for downstream UI and document surfaces

The default review shape is:

- executive summary
- 3 key insights
- 4 deep challenge briefs
- 3 PM questions
- 3 follow-up actions
- 4-6 dashboard highlights

The compact review shape keeps:

- executive summary
- 3-4 key insights
- 3-4 compact challenge briefs
- 3 PM questions
- 3 follow-up actions
- 4-6 dashboard highlights
