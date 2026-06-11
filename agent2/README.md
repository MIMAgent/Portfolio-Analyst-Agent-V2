# Agent2 Workspace

This folder is the isolated workspace for the next-generation Portfolio Analyst agent.

## Purpose

`agent2/` exists so new design and implementation work can move forward without disturbing the current agent/runtime path.

The older implementation remains in:

- `src/portfolio_analyst_agent/`
- `scripts/`
- `docs/`

This folder is for:

- agent2 philosophy
- input and retrieval design
- output schema design
- ingestion planning for old IC docs and internal research
- future implementation files specific to agent2

## Working rule

When building agent2, prefer adding new files under this folder rather than changing the older agent unless there is a deliberate migration step.

## Initial contents

- `AGENT2_PHILOSOPHY_AND_OPERATING_MODEL_V1.md`
- `IC_DOC_INGESTION_SPEC_V1.md`

## Current direction

Agent2 is intended to combine three evidence lanes:

1. structured portfolio / VIR / algo / decomposition data
2. internal research and prior IC history
3. trusted external web context

The main output target is a structured review packet that can later power both:

- Word documents
- frontend application views
