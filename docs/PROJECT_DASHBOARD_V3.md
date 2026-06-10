# Portfolio Analyst Agent V2 - Project Dashboard v3

Last updated: April 2, 2026

## Purpose

This dashboard is a meeting-ready planning view for the full Portfolio Analyst Agent V2 program.

It is grounded in:

- `PM_Analyst_Agent_Deployment_Architecture.md`
- current parser and mapping decisions already documented in the repo
- the agreed principle that this must remain a true LLM-led agent, not a deterministic rules engine disguised as one

## Core Working Team

Current project partners for the design and pilot phase:

- PM lead
- Shivika
- Codex agent as build and documentation support

## Program Objective

Build Portfolio Analyst Agent V2 from a single-user monthly VIR analysis workflow into a collaborative institutional intelligence platform.

End-state deployment target:

- Model 1: shared report consumer
- Model 2: shared agent with personal PM views
- Model 3: collaborative intelligence platform with shared memory and IC synthesis

## Current Snapshot

| Area | Status | Notes |
|------|--------|-------|
| Product direction | In progress | End-state deployment path is now defined across Models 1-3 |
| Equity parser contract | Defined | Workbook structure, STF, decomposition, and derived fields are locked in |
| Fixed income parser contract | Defined | CSV structure, STF, decomposition, and treasury hedged-YTM helper rule are locked in |
| Shared ACID mapping schema | Defined | Mapping layer is behavior-aware, not just taxonomy |
| Equity mapping intake | In progress | Seed mapping file validated; one likely anomaly flagged for review |
| Holdings ingestion | Not started | Waiting on sample holdings file and join rules |
| Agent workflow | Not started | Need tool loop, report templates, memory policy, and output contracts |
| Deployment platform | Not started | Model 1 can run locally; Model 2+ need infra decisions |

## Phase Roadmap

| Phase | Deployment Model | Target Window | Goal | Exit Criteria |
|------|------------------|---------------|------|---------------|
| Phase 0 | Discovery and design | April 1, 2026 - April 17, 2026 | Lock the data contracts and delivery plan | Parser specs, mapping approach, roadmap, and pilot scope agreed by the PM lead and Shivika |
| Phase 1 | Model 1 | April 20, 2026 - May 29, 2026 | Deliver the first usable monthly VIR analyst workflow | First monthly VIR Change Brief is judged at least as good as the current manual process |
| Phase 2 | Model 2 foundation | June 1, 2026 - July 31, 2026 | Move from manual workflow to shared service foundation | Shared data store, API foundation, permissions model, and pilot-ready interface exist |
| Phase 3 | Model 2 enrichment | August 3, 2026 - October 30, 2026 | Add risk, alerting, and IC preparation depth | Pilot PMs use the tool independently for fund-specific analysis |
| Phase 4 | Model 3 | November 2, 2026 - March 26, 2027 | Add shared intelligence and collaborative IC synthesis | Shared memory, governance, and collaborative IC workflows are operational |

## Epic Board

| Epic | Status | Target Phase | Owner | Deliverable |
|------|--------|--------------|-------|-------------|
| E1. Product and architecture alignment | In progress | Phase 0 | PM lead + Shivika | Locked scope, success metrics, deployment path |
| E2. Equity model parser and mapping | In progress | Phase 0 | PM lead + Shivika + agent | Final equity parser contract and normalized mapping behavior |
| E3. Fixed income model parser and mapping | In progress | Phase 0 | PM lead + Shivika + agent | Final fixed income parser contract and mapping approach |
| E4. Holdings ingestion and ACID cross-reference | Not started | Phase 1 | PM lead + Shivika + agent | Holdings schema, parser spec, join rules, alignment outputs |
| E5. Agent reasoning loop and report generation | Not started | Phase 1 | PM lead + Shivika + agent | Monthly review loop, Challenge Brief, VIR Change Brief, IC draft output |
| E6. Model 1 pilot operations | Not started | Phase 1 | PM lead + Shivika | Monthly runbook, review process, distribution workflow |
| E7. Shared data platform | Not started | Phase 2 | Dev + IT + PM lead | Postgres or SQL Server schema, ingestion jobs, admin controls |
| E8. API, auth, and permissions | Not started | Phase 2 | Dev + IT | SSO, fund permissions, scoped API layer |
| E9. Pilot PM interface | Not started | Phase 2 | Dev + PM lead + Shivika | Web app, Teams bot, or equivalent pilot surface |
| E10. Risk and monitoring enrichment | Not started | Phase 3 | Dev + PM lead + Shivika | FactSet integration, alerts, scenario analysis |
| E11. IC prep workflow | Not started | Phase 3 | PM lead + Shivika + dev | Repeatable IC assembly workflow |
| E12. Shared memory and collaboration | Not started | Phase 4 | Dev + PM lead + Shivika + compliance | Visibility controls, endorsement/challenge, shared synthesis |
| E13. Governance, audit, and rollout | Not started | Phase 4 | IT + compliance + PM lead + Shivika | Production controls, retention, onboarding, rollout plan |

## Open Questions

### Immediate decisions for the next 2 weeks

| Question | Why it matters | Owner | Due by |
|---------|----------------|-------|--------|
| Will fixed income mappings live in the same file as equity, or in a separate file with the same schema? | Affects ingestion design, admin workflow, and validation | PM lead + Shivika | April 10, 2026 |
| Should the fixed income treasury hedged-YTM allowlist live in parser config or the mapping file? | Determines where business logic is governed | PM lead + Shivika | April 10, 2026 |
| What does the holdings file look like, and does it carry ACID directly? | This is the key dependency for portfolio cross-reference | PM lead + Shivika | April 10, 2026 |
| What is the minimum Model 1 output set for pilot success? | Prevents overbuilding before first live use | PM lead + Shivika | April 10, 2026 |
| Who are the first 2-3 pilot PMs for Model 2? | Needed to shape fund permission model and front-end requirements | PM lead + Shivika + management | April 17, 2026 |

### Phase 1 to Phase 2 decisions

| Question | Why it matters | Owner | Due by |
|---------|----------------|-------|--------|
| Where will the shared database live: Azure, AWS, or on-prem? | Core infrastructure decision for Model 2 | IT + PM lead | May 29, 2026 |
| Will the LLM run via OpenAI enterprise API or Azure OpenAI? | Compliance, procurement, and deployment architecture depend on it | IT + InfoSec + PM lead | May 29, 2026 |
| Which user surface comes first: web app, Teams bot, or both? | Shapes API design and onboarding flow | PM lead + Shivika + IT | May 29, 2026 |
| Who owns ongoing maintenance after pilot: PM, dev team, or shared ownership? | Affects staffing, backlog, and support model | Management | May 29, 2026 |

### Model 3 decisions

| Question | Why it matters | Owner | Due by |
|---------|----------------|-------|--------|
| What approval model governs personal to team to firm sharing? | Required before shared memory goes live | Team leads + compliance | October 30, 2026 |
| What can be promoted to IC visibility automatically vs manually? | Prevents noise and preserves quality control | IC chair + PM lead + Shivika | October 30, 2026 |
| How long should shared memory persist before review or expiration? | Needed for governance and knowledge retention | Compliance | October 30, 2026 |
| How visible should cross-team observations be? | Determines collaboration model and information boundary rules | Compliance + management | October 30, 2026 |

## Immediate To-Do List

### This week

- Finalize the fixed income mapping structure decision
- Receive and inspect a sample holdings file
- Define holdings parser requirements and ACID join rules
- Resolve whether `EM UT EQ` should remain `Industry` or be corrected to `Sector`
- Confirm the minimum Model 1 deliverables for the first pilot month

### Next 30 days

- Write holdings parser spec
- Write cross-reference and alignment-spec doc
- Define the agent tool surface for monthly review
- Define VIR Change Brief and Challenge Brief output templates
- Define memory categories and evidence storage contract
- Run the first end-to-end Model 1 dry run using real monthly files

### Before Model 2 starts

- Select database target
- Select LLM hosting path
- Select pilot PM group
- Decide the first front-end surface
- Define admin process for user-to-fund permissions

## Sprint Plan

Assumption: two-week sprint cadence beginning Monday, April 6, 2026.

| Sprint | Dates | Phase | Objective | Milestone |
|-------|-------|-------|-----------|-----------|
| Sprint 0 | April 1, 2026 - April 3, 2026 | Phase 0 | Project framing and architecture alignment | Deployment architecture and build direction clarified |
| Sprint 1 | April 6, 2026 - April 17, 2026 | Phase 0 | Lock model data contracts | Equity and fixed income parser contracts, mapping schema, and dashboard are in place |
| Sprint 2 | April 20, 2026 - May 1, 2026 | Phase 1 | Build holdings and join design | Holdings parser spec and ACID cross-reference rules are complete |
| Sprint 3 | May 4, 2026 - May 15, 2026 | Phase 1 | Build agent workflow design | Monthly review loop, report structures, memory categories, and output contracts are defined |
| Sprint 4 | May 18, 2026 - May 29, 2026 | Phase 1 | Execute Model 1 pilot month | First live VIR Change Brief and Challenge Brief are produced and reviewed |
| Sprint 5 | June 1, 2026 - June 12, 2026 | Phase 2 | Shared data layer foundation | Production database schema and ingestion pipeline design are complete |
| Sprint 6 | June 15, 2026 - June 26, 2026 | Phase 2 | API and security foundation | Fund-scoped API contracts and permission model are implemented |
| Sprint 7 | June 29, 2026 - July 10, 2026 | Phase 2 | Pilot interface foundation | First PM-facing interface is usable in pilot form |
| Sprint 8 | July 13, 2026 - July 24, 2026 | Phase 2 | Pilot onboarding and ops hardening | 2-3 pilot PMs can use the agent independently |
| Sprint 9 | August 3, 2026 - August 14, 2026 | Phase 3 | Risk data foundation | FactSet or equivalent risk integration plan is working in test form |
| Sprint 10 | August 17, 2026 - August 28, 2026 | Phase 3 | Alerts and monitoring | Alert framework and initial scenario outputs are available |
| Sprint 11 | September 8, 2026 - September 18, 2026 | Phase 3 | IC workflow | IC prep workflow produces reusable committee drafts |
| Sprint 12 | October 5, 2026 - October 16, 2026 | Phase 3 | Pilot scale-up | Tool is ready to expand beyond the first pilot PM cohort |
| Sprint 13 | November 2, 2026 - November 13, 2026 | Phase 4 | Shared memory foundation | Visibility levels, shared-memory schema, and audit model are implemented |
| Sprint 14 | November 16, 2026 - November 27, 2026 | Phase 4 | Collaboration mechanics | Endorsement, challenge, and shared-item lifecycle are usable |
| Sprint 15 | November 30, 2026 - December 11, 2026 | Phase 4 | Collaborative IC synthesis | Cross-user IC assembly works with shared observations |
| Sprint 16 | January 11, 2027 - January 22, 2027 | Phase 4 | Knowledge integrations | SharePoint, MAR, or research-document integrations are piloted if available |
| Sprint 17 | February 1, 2027 - February 12, 2027 | Phase 4 | Governance hardening | Retention, approval, and compliance controls are complete |
| Sprint 18 | March 1, 2027 - March 12, 2027 | Phase 4 | Rollout readiness | Production rollout checklist is complete |
| Sprint 19 | March 15, 2027 - March 26, 2027 | Phase 4 | Full program closeout | Model 3 launch readiness review completed |

## Milestones

| Milestone | Target Date | Definition of done |
|----------|-------------|--------------------|
| M1. Data-contract freeze | April 17, 2026 | Equity and fixed income parser and mapping contracts are stable enough to begin implementation |
| M2. Holdings integration design | May 1, 2026 | Holdings schema and join rules are agreed |
| M3. Model 1 pilot output | May 29, 2026 | First live monthly package is delivered and reviewed |
| M4. Shared-service foundation | June 26, 2026 | Shared DB, permission model, and API skeleton are in place |
| M5. Pilot PM launch | July 24, 2026 | Pilot PMs can use the system without operator mediation |
| M6. Risk and IC enrichment | October 16, 2026 | Risk and IC features are meaningfully useful to pilots |
| M7. Shared-memory alpha | November 27, 2026 | Collaborative memory works for team users |
| M8. Model 3 readiness | March 26, 2027 | Governance, rollout, and end-state operating model are ready |

## Risks and Dependencies

| Risk | Impact | Mitigation |
|------|--------|------------|
| Holdings data does not contain ACID or clean join keys | Delays cross-reference and portfolio-specific analysis | Get sample early and define mapping fallback immediately |
| Model output formats drift month to month | Breaks ingestion and slows adoption | Preserve raw rows, isolate mapping layer, and validate on ingest |
| LLM hosting decision slips | Blocks Model 2 infrastructure work | Keep Model 1 local and LLM-agnostic while infra choice is pending |
| Too much manual governance too early | Slows adoption and PM participation | Keep Model 1 and early Model 2 lightweight; add approvals only in Phase 4 |
| Shared memory creates noise | Weakens trust in Model 3 | Introduce visibility rules, endorsement, and challenge workflows before firm-wide rollout |
| Tool behaves like a rules engine instead of an analyst | Undermines core product value | Keep judgment inside the LLM loop and keep deterministic code limited to parsing, storage, validation, and evidence retrieval |

## Suggested Meeting Agenda for Today

1. Confirm the roadmap shape: Model 1 to Model 2 to Model 3.
2. Agree the first true success metric for Model 1.
3. Decide the fixed income mapping file approach.
4. Review the expected holdings file and join strategy.
5. Decide the minimum pilot output package.
6. Align on roles between the PM lead and Shivika for Phase 0 and Phase 1.
7. Name the first pilot PM users and likely stakeholders for IT and compliance.

## Success Metrics by Phase

| Phase | Primary success metric |
|------|------------------------|
| Phase 0 | Team agrees on data contracts, roadmap, and pilot scope |
| Phase 1 | Agent output is trusted enough to replace the current manual monthly VIR review workflow |
| Phase 2 | Pilot PMs use the tool independently for fund-specific analysis |
| Phase 3 | Agent becomes the default workflow for VIR review, alerts, and IC prep in the pilot group |
| Phase 4 | Shared memory improves IC synthesis and preserves institutional knowledge across users |

## Recommended Operating Principle

Start narrow, prove value quickly, and only productionize the parts the team actually pulls on.

That means:

- keep Model 1 fast and analyst-grade
- use Model 2 to scale personalized access safely
- use Model 3 only after there is clear demand for shared intelligence and governance is defined
