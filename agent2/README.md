# Agent2 Workspace

This folder is the isolated workspace for the next-generation Portfolio Analyst agent.

## Purpose

`agent2/` is now the canonical workspace for the new deep-memo PM challenge methodology.

The older implementation remains in:

- `src/portfolio_analyst_agent/`
- `scripts/`
- `docs/`

This folder is for:

- the canonical deep PM challenge memo runner
- agent2 philosophy
- input and retrieval design
- output schema design
- ingestion and retrieval logic for internal research and old IC docs
- future implementation files specific to agent2

## Working rule

When building agent2, prefer adding new files under this folder rather than changing the older agent unless there is a deliberate migration step.
Inside `agent2`, the compact / challenge-card methodology is no longer the active path. The canonical output path is the deep challenge memo structure.

## Initial contents

- `AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`
- `IC_DOC_INGESTION_SPEC_V1.md`

## Current direction

Agent2 combines three evidence lanes:

1. structured portfolio / VIR / algo / decomposition data
2. internal research and prior IC history
3. trusted external web context

The main output target is a deep structured review packet that can later power both:

- Word documents
- frontend application views

## Canonical run path

The canonical Bedrock run path in `agent2` is:

- build the review packet
- build the deep evidence pack
- generate the deep challenge memo
- save JSON and markdown artifacts for downstream UI and document surfaces

The default review shape is:

- executive summary
- 3 key insights
- 4 deep challenge briefs
- 3 PM questions
- 3 follow-up actions
- 4-6 dashboard highlights
