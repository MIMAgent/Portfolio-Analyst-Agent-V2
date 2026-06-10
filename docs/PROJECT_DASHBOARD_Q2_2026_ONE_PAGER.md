# Portfolio Analyst Agent V2 - Q2 2026 One-Page Meeting Dashboard

Last updated: April 2, 2026

## Quarter Goal

Use Q2 2026 to move the project from design into a real operating workflow.

By quarter end, we should have:

- a trusted Model 1 monthly workflow in operation
- a build-ready Model 2 architecture package
- a fully defined Model 3 collaboration and governance design

## Core Team

- PM lead
- Shivika
- Codex agent as build and documentation support

## 7 Sprint Milestones

| Sprint | Dates | Outcome |
|------|-------|---------|
| Sprint 1 | April 1 - April 12 | Equity and fixed income parser specs, mapping framework, and delivery plan locked |
| Sprint 2 | April 13 - April 26 | Holdings parser and ACID join rules defined |
| Sprint 3 | April 27 - May 10 | Agent reasoning loop, memory contract, evidence model, and report templates complete |
| Sprint 4 | May 11 - May 24 | First full dry run completed using real data |
| Sprint 5 | May 25 - June 7 | Model 1 hardening complete: runbook, QA checklist, review workflow |
| Sprint 6 | June 8 - June 21 | Model 2 architecture package complete: permissions, API, front-end recommendation |
| Sprint 7 | June 22 - June 30 | Quarter closeout complete: Model 1 sign-off, Model 2 handoff, Model 3 governance design documented |

## Decision Status

| Decision | Status | Current state |
|------|--------|---------------|
| Fixed income mappings: same file as equity or separate file using same schema? | Completed | Separate files, same shared schema |
| Treasury hedged-YTM allowlist: parser config or mapping file? | Completed | Govern in fixed income mapping file |
| Holdings file: does it include ACID directly? | Completed for v1 design | Use an approved exposure-label-to-ACID crosswalk |
| Minimum Model 1 output package for success | Open | Still open pending review of the monthly algo file; the algo output will be a separate artifact |
| Stakeholders who need to approve Model 2 architecture in Q2 | Completed for current phase | Current key stakeholders are PM lead and Shivika |

## 3 Biggest Risks

| Risk | Impact | Response |
|------|--------|----------|
| Holdings sample arrives late | Blocks portfolio cross-reference design | Escalate immediately and prioritize holdings review |
| Scope expands too much during Q2 | Quarter ends with no operating product | Freeze must-deliver list and push extras to Q3 |
| Model 1 output is not trusted by users | Weakens the whole rollout path | Add more dry runs and tighten analyst-quality review |

## Must-Deliver Outputs by Quarter End

- final equity parser spec
- final fixed income parser spec
- shared ACID mapping schema
- holdings parser spec
- cross-reference and alignment spec
- monthly VIR Change Brief template
- monthly Challenge Brief template
- evidence and memory contract
- Model 1 runbook
- Model 2 architecture handoff
- Model 3 governance design note

## Meeting Framing

Suggested framing statement:

We should treat this as a quarter execution plan, not a long-range roadmap. If Q2 ends with a trusted Model 1 workflow, a build-ready Model 2 package, and a clearly defined Model 3 collaboration design, the project is in a very strong position going into Q3.
