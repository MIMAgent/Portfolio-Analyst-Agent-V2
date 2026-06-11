# Agent 2.0 Philosophy And Operating Model v1

Last updated: 2026-06-10

## Purpose

This document defines the philosophy and intended operating model for the next Portfolio Analyst Agent iteration ("agent2.0").

The goal is not to generate a Word document first. The goal is to generate a richer, reusable data product that can later power:

- Word IC documents
- the frontend application
- PM review summaries
- downstream export surfaces

The core design principle is that the agent should work like a strong PM analyst:

- start from actual portfolio and signal data
- compare current positioning against prior stated views
- use trustworthy live external context when it materially improves the challenge
- produce structured review output rather than loose prose

---

## Core Philosophy

### 1. The agent is a research-and-challenge system, not a document formatter

The first job of agent2.0 is to produce decision-grade review data.

That means:

- identifying what matters in the portfolio
- finding where positioning and signal disagree
- checking whether the disagreement is already explained internally
- testing the current position against current outside evidence
- surfacing the right PM-facing challenge questions

Formatting into Word or app UI comes later.

### 2. The agent should reason like a human analyst

The agent should not merely summarize tables.

It should:

- locate the material active bets
- determine whether those bets align with VIR and algo
- determine whether a prior internal thesis exists
- determine whether current external evidence supports or weakens the position
- present the resulting tension in a clear PM-facing way

This is especially important for "devil's advocate", "bull case", "bear case", and "what changed?" sections.

### 3. The agent should combine multiple evidence lanes

Agent2.0 should not depend on only one input type.

It should combine:

- structured portfolio data
- internal research and prior IC history
- trustworthy live external context

That combination is what makes the output useful.

### 4. The agent should never invent a thesis

The agent may synthesize evidence.
It may not fabricate:

- PM rationale
- prior committee questions
- internal research conclusions
- external market facts

If evidence is missing, the output should say so clearly.

### 5. The agent should separate source types

The output should distinguish between:

- portfolio facts
- internal house view
- external live context

This makes the output more trustworthy and allows future UI surfaces to show provenance cleanly.

---

## What Agent2.0 Is Trying To Produce

Agent2.0 should produce a structured review packet for each fund.

That packet is expected to contain sections such as:

- fund header / metadata
- active weight summary
- benchmark-relative overweights and underweights
- VIR vs algo vs positioning divergence
- top VIR movers and decomposition implications
- challenge candidates
- devil's advocate / positions requiring discussion
- PM-facing review questions
- roadmap / next-review agenda
- citations and source lineage
- data-quality or evidence-gap flags

This output should be canonical.
Word and frontend layers should read from this packet rather than re-derive logic independently.

---

## The Three Evidence Lanes

### 1. Structured Portfolio Lane

This is the factual portfolio and signal layer already present in the repo.

Examples:

- fund positions
- benchmark positions
- active weights
- rolled exposures
- VIR values and trend
- VIR decomposition values and driver mix
- algo values and trend
- exposure lineage
- ACID mapping and category classification

This lane answers:

- What does the fund hold?
- Where is it overweight or underweight?
- What do VIR and algo say now?
- What changed month over month?
- What is driving the VIR move: valuation, earnings, carry, currency, rates, spreads, or another component?

### 2. Internal Research Lane

This is the internal memory and rationale layer.

Examples:

- prior IC documents
- prior PM review outputs
- internal research notes
- PM rationale documents
- old challenge summaries
- synced SharePoint content

Current expected local source:

- `C:\Users\schuri2\MORNINGSTAR INC\MIM Global Research - Final Research (yyyymm-AC-ACID-project title)`

This lane answers:

- What did we say before?
- Was the position intentional?
- Has the committee already asked about this?
- Does internal research support or contradict the current sizing?

### 3. Trusted External Context Lane

This is the live outside-information lane.

Examples:

- company filings
- investor relations updates
- earnings releases and presentations
- official economic data
- central-bank and government sources
- other approved high-trust financial sources

This lane answers:

- What is happening now in the real world?
- What evidence supports the bull case?
- What evidence supports the bear case?
- Is the current signal fundamental, mechanical, early, crowded, or weakening?

---

## Source Trust Policy

Agent2.0 should have broad freedom to search for context, but only from trustworthy sources.

### Preferred source hierarchy

1. Official company sources
   - investor relations
   - earnings releases
   - company presentations
   - official filings

2. Official regulatory / public data sources
   - SEC / EDGAR
   - Federal Reserve / FRED
   - BLS
   - BEA
   - other direct official datasets

3. Internal sources
   - SharePoint-synced research files
   - old IC documents
   - prior agent artifacts
   - PM notes and internal research

4. Approved external financial and macro sources
   - only if explicitly allowed by source policy

### Avoid by default

- random blogs
- low-quality finance aggregators
- unsourced commentary
- AI-generated summaries with no primary sourcing
- weak-quality SEO market content

### Operating rule

The agent should be allowed to search when needed, but every material claim in output should still be anchored to a trustworthy cited source.

---

## How The Agent Should Think

The agent should use a repeating reasoning pattern:

1. Find the important position or exposure.
2. Check current portfolio sizing.
3. Check benchmark-relative active weight.
4. Check VIR and algo signals.
5. Check VIR decomposition and determine what is actually driving the signal move.
6. Check whether the trend is improving, weakening, or mechanically driven.
7. Check prior internal rationale and committee history.
8. Check current trustworthy external evidence.
9. Build the challenge:
   - what supports the position
   - what challenges the position
   - what needs PM confirmation

That reasoning pattern should drive sections such as:

- bull case
- bear case
- devil's advocate
- review questions
- next-review checkpoints

---

## How Bull Case / Bear Case Should Be Built

### Bull case

The bull case should come from evidence such as:

- supportive VIR or algo direction
- improving multi-month trend
- constructive decomposition, where the signal is supported by durable drivers rather than a single weak or mechanical component
- supportive internal research
- supportive current external evidence
- cleaner expression opportunities
- valuation or earnings evidence that reinforces the signal

### Bear case

The bear case should come from evidence such as:

- contradictory or weakening external evidence
- signal that is early, noisy, or mostly mechanical
- decomposition showing that the move is dominated by a fragile component such as multiple compression, FX carry, or another non-fundamental driver
- prior internal concerns
- mandate or implementation constraints
- crowding risk
- policy, macro, earnings, or balance-sheet risks

### Devil's advocate

The devil's advocate section should not be generic.

It should identify positions where:

- portfolio sizing is material
- the current signal has moved
- prior house rationale is absent, stale, or unresolved
- external evidence meaningfully challenges the status quo

Its function is not to recommend trades.
Its function is to force explicit PM confirmation.

### Decomposition is a required part of challenge quality

The agent should not treat every positive VIR move as equally persuasive.

It should ask:

- Is the move earnings-led or valuation-led?
- Is it broad-based or concentrated in one component?
- Is it fundamental or mostly mechanical?
- Is the signal more compelling for an unhedged portfolio than for a hedged one?
- Does the decomposition support the current PM stance, or does it make the signal look weaker than the headline number?

Examples:

- A technology upgrade driven mostly by multiple compression is different from one driven by improving earnings revisions.
- An EM local debt improvement driven mostly by FX carry may be less compelling for a hedged portfolio than the headline VIR suggests.
- A region move supported by repeated earnings and valuation improvement should be treated differently from a one-month tactical bounce.

Decomposition should therefore be used in:

- top mover interpretation
- bull case / bear case construction
- "signal valid but early" judgments
- devil's advocate ranking
- PM review questions

---

## What The Agent Should Do When Evidence Is Missing

If evidence is limited, the agent should narrow the claim rather than invent detail.

Examples:

- "No documented PM rationale found in current internal sources."
- "External evidence is mixed; no strong confirming fundamental source found."
- "Signal improved, but current justification appears mechanical rather than earnings-led."

Missing evidence is itself a useful output.

---

## Minimum Inputs For Agent2.0

Ignoring advanced risk analytics for now, the minimum required inputs are:

- fund positions / benchmark positions
- rolled exposures
- VIR data
- VIR decomposition data
- algo data
- ACID mapping
- fund metadata
- internal prior-review documents
- trusted external web context

### Strongly recommended additional inputs

- PM names by fund
- benchmark names by fund
- prior IC questions and committee notes
- internal research stance documents
- archived PM rationale or thesis notes

---

## SharePoint Philosophy

For now, SharePoint should be treated as a synced local document source, not as an immediate API integration problem.

Phase-1 expectation:

- SharePoint content is synced locally through OneDrive
- the agent reads those local files directly

This is faster and operationally simpler than building Microsoft Graph integration before the retrieval and output model are stable.

Direct API-based SharePoint access can be added later if automation needs justify it.

---

## What Agent2.0 Should Output First

The first goal should be a structured JSON review packet, for example:

- `agent2_review_packet.json`

That packet should be the single source of truth for:

- frontend rendering
- Word generation
- HTML summaries
- review comparison over time

Do not make Word the primary format.

---

## Non-Goals For The First Version

The first agent2.0 version does not need to:

- generate final polished Word output
- support every possible fund-specific section
- replicate advanced FactSet risk analytics
- automate direct SharePoint upload/download
- cover all historical research files at once

The first version should focus on producing strong structured review data with clear provenance.

---

## Practical Operating Model

### Step 1

Use structured portfolio data to identify material exposures and signal divergences.

### Step 2

Check VIR decomposition to determine whether the signal is durable, fragile, or mostly mechanical.

### Step 3

Retrieve relevant internal history from synced research / IC documents.

### Step 4

Retrieve trustworthy external evidence for current market or company context.

### Step 5

Synthesize the evidence into structured challenge output.

### Step 6

Persist the resulting review packet with explicit source lineage.

---

## Summary

Agent2.0 should act like a PM analyst that:

- knows the portfolio
- remembers what the team said before
- checks trustworthy outside evidence
- challenges positions where the evidence and positioning no longer line up

The system should be built around evidence synthesis and structured output, not around Word generation.

That is the right foundation for both the application and future committee documents.
