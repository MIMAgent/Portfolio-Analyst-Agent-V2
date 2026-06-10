# Portfolio Analyst Agent V2 - Q2 2026 Execution Dashboard

Last updated: April 2, 2026

## Planning Assumption

This version replaces the earlier long-range sprint framing with a true quarter plan.

Working assumption:

- the active delivery window is Q2 2026
- the team wants aggressive execution, not a year-long roadmap
- the project should use the quarter to get to a real operating product, not just a concept deck

## Reality Check

A full production rollout of Model 1, Model 2, and Model 3 inside one quarter is not realistic without a staffed dev team and pre-cleared infrastructure.

What is realistic in one quarter:

- Model 1 fully operational
- Model 2 designed and partially built, with a credible pilot path
- Model 3 clearly specified, with governance and data model defined but not fully rolled out

So the quarter goal should be:

Deliver a trusted Model 1 operating workflow and a Model 2 pilot-ready foundation, while fully defining the Model 3 collaboration layer.

## Quarter Objective

By the end of Q2 2026, Portfolio Analyst Agent V2 should be able to:

- ingest equity and fixed income model outputs reliably
- ingest holdings and cross-reference positions to VIR signals
- generate a monthly VIR Change Brief and Challenge Brief
- maintain evidence-backed analytical memory
- support a credible transition path into a shared PM-facing service

## Quarter Success Criteria

| Outcome | Success bar by quarter end |
|------|-------------------------------|
| Data layer | Equity, fixed income, and holdings inputs are specified and testable |
| Analyst output | Monthly review package is trusted and usable by the team |
| Agent behavior | Output feels like analyst reasoning, not a deterministic rules report |
| Operating workflow | A repeatable monthly runbook exists |
| Scale path | Model 2 architecture, permissions, and pilot surface are defined well enough to begin implementation immediately after Q2 |

## Delivery Scope

### In scope for Q2

- equity parser contract and validation
- fixed income parser contract and validation
- ACID mapping framework
- holdings parser and join logic
- monthly review workflow
- Challenge Brief and VIR Change Brief templates
- memory and evidence contract
- Model 1 operating runbook
- Model 2 technical design package
- Model 3 governance and shared-memory design package

### Stretch scope for Q2

- early Model 2 alpha interface
- first shared database schema for multi-user migration
- draft permission model and API contract

### Out of scope for Q2 unless staffing expands

- full enterprise deployment
- complete SSO rollout
- firm-wide PM onboarding
- fully operational shared-memory collaboration product

## Quarter Workstreams

| Workstream | Owner | Q2 target |
|------|-------|------------|
| Product and workflow | PM lead + Shivika | Lock scope, outputs, review cadence, and user success metrics |
| Data contracts | PM lead + Shivika + agent | Finish model, mapping, and holdings specifications |
| Agent design | PM lead + Shivika + agent | Define the reasoning loop, memory model, and output contracts |
| Pilot operations | PM lead + Shivika | Run and evaluate Model 1 monthly workflow |
| Deployment architecture | PM lead + Shivika | Produce Model 2 build-ready architecture package |
| Governance design | PM lead + Shivika | Define Model 3 sharing and approval rules |

## Quarter Board

| Epic | Status | Priority | Quarter target |
|------|--------|----------|----------------|
| E1. Equity and FI model contracts | In progress | P0 | Complete and stable |
| E2. Mapping and enrichment rules | In progress | P0 | Complete and stable |
| E3. Holdings ingestion and ACID join | Not started | P0 | Complete |
| E4. Agent reasoning loop and output package | Not started | P0 | Complete |
| E5. Monthly operating workflow | Not started | P0 | Complete |
| E6. Model 2 architecture package | Not started | P1 | Complete |
| E7. Model 2 alpha technical foundation | Not started | P1 | Partial or complete if capacity allows |
| E8. Model 3 governance and collaboration design | Not started | P1 | Complete |

## Sprint Cadence

Assumption: 2-week sprints across the remainder of Q2 2026.

## Sprint Plan

| Sprint | Dates | Theme | Must-have exit |
|------|-------|-------|----------------|
| Sprint 1 | April 1 - April 12 | Data contract closure | Equity and fixed income parser specs are locked; mapping schema is usable; dashboard and delivery plan agreed |
| Sprint 2 | April 13 - April 26 | Holdings and cross-reference | Holdings sample is analyzed; holdings parser spec and ACID join rules are complete |
| Sprint 3 | April 27 - May 10 | Agent operating design | Reasoning loop, memory contract, evidence model, and report templates are complete |
| Sprint 4 | May 11 - May 24 | Model 1 dry run | First end-to-end dry run is completed using real data |
| Sprint 5 | May 25 - June 7 | Model 1 hardening | Monthly runbook, QA checklist, and review process are finalized |
| Sprint 6 | June 8 - June 21 | Model 2 design package | Shared service architecture, permission model, and API/front-end recommendation are complete |
| Sprint 7 | June 22 - June 30 | Quarter close | Model 1 sign-off complete; Model 2 next-step build package complete; Model 3 governance design documented |

## Sprint Backlog

### Sprint 1

- fixed income mapping-file structure decision completed
- hedged-YTM allowlist governance location decision completed
- equity mapping intake review completed
- resolve `EM UT EQ` category anomaly
- align on Model 1 success metric
- align on quarter delivery scope with Shivika

### Sprint 2

- inspect holdings sample
- define holdings parser schema
- define join precedence for exposure-label crosswalks and exception handling
- define alignment output states
- define missing-data handling rules

### Sprint 3

- define tool interfaces for the LLM agent
- define monthly review sequence
- define decomposition and challenge stages
- define memory categories and update rules
- define evidence citation structure
- finalize VIR Change Brief and Challenge Brief structure

### Sprint 4

- run first simulated month end-to-end
- test top-mover identification
- test cross-reference narrative quality
- test challenge framing quality
- identify failure cases and data gaps

### Sprint 5

- refine prompts and tool behavior
- finalize QA and reviewer checklist
- define publish/distribution workflow
- define standard monthly runbook
- prepare pilot materials for stakeholder review

### Sprint 6

- choose Model 2 recommended front end
- choose shared data-store recommendation
- define permission model
- define user roles and scoped behavior
- define API surface for chat, holdings, VIR, reports, and memory
- define Model 2 implementation handoff package

### Sprint 7

- finalize quarter-end readout
- confirm Model 1 go-forward operating process
- finalize Model 2 build backlog
- finalize Model 3 governance and collaboration design notes
- confirm Q3 implementation owners and dependencies

## Immediate Questions and Status

| Question | Status | Current decision or state | Owner | Impact |
|------|--------|---------------------------|-------|--------|
| Should fixed income mappings be separate from equity mappings? | Completed | Use separate equity and fixed income mapping files, both governed by the shared ACID schema. | PM lead + Shivika | Unblocks mapping governance and parser enrichment design |
| Should treasury hedged-YTM allowlist live in config or mapping? | Completed | Govern eligibility in the fixed income mapping file; parser keeps the calculation formula only. | PM lead + Shivika | Unblocks final FI parser governance model |
| Does the holdings file include ACID directly? | Completed for v1 design | No direct ACID is required for this source. Use an exact exposure-label-to-ACID crosswalk for sector, country, and style rows. | PM lead + Shivika | Unblocks cross-reference design |
| What is the minimum acceptable monthly output package? | Open | Keep open pending review of the monthly algo file. Subdecision already locked: the algo output should be a separate artifact. | PM lead + Shivika | Still blocks final Model 1 completion criteria |
| Which stakeholders need to bless Model 2 architecture in Q2? | Completed for current phase | For current planning work, the active key stakeholders are PM lead and Shivika. Broader IT, compliance, IAM, and data-owner approvals become relevant when moving from planning into shared-service implementation. | PM lead + Shivika | Unblocks current Q2 planning |

## Deliverables by Quarter End

### Must deliver

- final equity parser spec
- final fixed income parser spec
- shared ACID mapping schema
- holdings parser spec
- cross-reference and alignment spec
- monthly VIR Change Brief template
- monthly Challenge Brief template
- evidence and memory contract
- Model 1 runbook
- Model 2 architecture and implementation handoff
- Model 3 governance and shared-memory design note

### Nice to have

- first alpha UI mock or prototype
- first shared DB schema draft
- first API contract draft

## Decision Log Needed in the Quarter

These should be explicitly captured as decisions, not left implicit:

- Model 1 output pack definition
- holdings join hierarchy
- fixed income mapping-file strategy
- mapping governance ownership
- Model 2 front-end recommendation
- Model 2 hosting recommendation
- Model 3 visibility and approval model

## Risks

| Risk | Severity | Response |
|------|----------|----------|
| Holdings sample arrives late | High | Escalate immediately; no credible portfolio cross-reference exists without it |
| Team keeps expanding desired scope during Q2 | High | Freeze Q2 deliverables and push extras into Q3 |
| Model 1 output is analytically weak | High | Add more dry-run review cycles before calling the quarter successful |
| Architecture discussions crowd out working output | Medium | Keep Model 1 operational work as the primary quarter KPI |
| Model 3 collaboration ambitions pull effort too early | Medium | Keep Model 3 at design and governance level during Q2 |

## Recommended Meeting Agenda

1. Reset the timeline around a Q2 execution plan.
2. Agree what counts as quarter success.
3. Confirm the non-negotiable must-deliver outputs.
4. Confirm the completed decisions on fixed income mapping, hedged-YTM governance, and holdings crosswalk design.
5. Review the remaining open question on the monthly output package and the algo file.
6. Confirm what gets deferred to Q3.

## What To Say In The Meeting

A concise framing statement:

We should treat this as a quarter execution plan, not a year-long innovation roadmap. The quarter should end with a trusted Model 1 workflow in operation, a Model 2 build-ready design package, and a fully defined collaboration model for Model 3. That is aggressive but realistic.
