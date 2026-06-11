# IC Doc Ingestion Spec v1

Last updated: 2026-06-10

## Purpose

This document defines how agent2 should ingest old IC / mutual fund checklist documents.

The goal is not to preserve raw document layout.
The goal is to extract reusable internal-history signals that can be combined with:

- current portfolio data
- VIR / algo / decomposition
- trusted external context

## Why this matters

Old IC documents are the best source of:

- prior PM rationale
- repeated positioning themes
- prior committee framing
- stale or unresolved challenge items
- continuity from one month to the next

These documents help the agent answer:

- What did we say before?
- Is the current position still intentional?
- Has this concern persisted across months?
- Is the current signal change actually new, or have we been discussing the same issue already?

---

## Initial document family

Initial example documents reviewed:

- `March 2026 Mutual Fund Checklist - US Equity.docx`
- `April 2026 Mutual Fund Checklist - US Equity.docx`
- `May 2026 Mutual Fund Checklist - US Equity.docx`

## What these documents contain

The US Equity checklist documents consistently include:

- fund
- date
- PM names
- trade proposal
- benchmark-relative over/underweights
- sector and size/style rationale
- algo-relative comments
- directional moves
- robustness considerations
- miscellaneous / current positioning comments
- roadmap / future work

## Stable recurring prompts observed

Examples of recurring prompt structure:

- "What are the fund's largest benchmark relative overweight and underweight?"
- "What offsets does the fund hold to mitigate the risk of the largest overweight?"
- "What are the fund's largest algo relative overweight and underweight?"
- "What moves are you making and what is your rationale?"
- "What would need to happen for you to add further to this position?"
- "What moves did you consider but decide against?"
- "What macroeconomic environment do you believe your portfolio is best and worst positioned for?"
- "What further comments would you like to make on current positioning and the proposed moves?"
- "What asset classes do you intend to do work on?"

These recurring structures make the docs highly suitable for patterned extraction.

---

## Extraction goal

The ingestion layer should convert each IC document into structured internal-history data.

### Minimum metadata fields

- `fund`
- `document_date`
- `pm_names`
- `document_type`
- `source_path`
- `source_filename`

### Section-level extraction targets

- `trade_proposal`
- `benchmark_overweight_underweight_rationale`
- `sector_positioning_comments`
- `size_style_positioning_comments`
- `algo_positioning_comments`
- `largest_risk_offsets`
- `directional_moves`
- `considered_but_not_done`
- `robustness_best_case_environment`
- `robustness_worst_case_environment`
- `vulnerability_room_to_move`
- `misc_positioning_comments`
- `roadmap_items`

### Theme-level extraction targets

In addition to section text, the ingestion layer should identify recurring themes such as:

- IT underweight
- SMID overweight
- Industrials overweight
- Financials overweight
- Mag 7 / AI vulnerability
- software / semiconductors discussion
- subadvisor or sleeve-driven exposure
- value vs growth stance

These themes should be stored as structured tags or normalized summary entries.

---

## What the ingestion should produce

Each document should yield:

1. A structured record with metadata and extracted sections
2. A theme summary
3. A retrieval-friendly text representation
4. Stable source references for later citation

Possible output families:

- `agent2/internal_history/ic_docs.jsonl`
- `agent2/internal_history/ic_section_records.jsonl`
- `agent2/internal_history/ic_theme_index.json`

---

## How agent2 should use these documents

The agent should not simply quote old checklists.

It should use them to build:

- `prior_internal_view`
- `previous_rationale`
- `persistent_positioning_themes`
- `stale_or_unresolved_items`
- `prior_committee_language`
- `house_view_vs_current_signal`

### Example use

If the current month shows a large IT underweight while VIR improves:

- old IC docs can tell the agent this underweight has been repeatedly defended as intentional
- current decomposition and external context can then test whether that prior rationale still holds

That is much stronger than treating the current position as unexplained by default.

---

## Ingestion rules

### 1. Preserve meaning over layout

Do not optimize for Word formatting fidelity.
Optimize for usable analytical retrieval.

### 2. Prefer section extraction over naive full-text dump

A full-text copy is useful, but the main value comes from separating the document by question / answer section.

### 3. Preserve chronology

Document month and ordering matter.
The agent should be able to trace:

- what was said in March
- what changed in April
- what persisted into May

### 4. Preserve exact PM language when important

Some phrases matter because they show conviction, caution, or constraint.

Examples:

- "we feel we are near a limit"
- "we no longer manage to the algo at the fund level"
- "we are discussing IT replacements"

These should survive extraction cleanly.

### 5. Normalize recurring questions

If the same question appears every month with small wording differences, map it to one normalized section key.

---

## What the agent should infer from these docs

These docs are especially useful for detecting:

- persistent stated conviction
- repeated unresolved issues
- positions that were previously intentional but may now need re-testing
- themes that drift from explicit PM rationale into passive inertia

That makes them essential for:

- devil's advocate
- PM questions
- "what changed?" comparisons
- challenge ranking

---

## First-version scope

The first ingestion pass should focus on:

- `.docx` checklist documents
- one fund family at a time
- metadata extraction
- section extraction
- recurring-theme tagging

Do not try to solve every historical document format at once.

---

## Summary

Old IC documents should be treated as structured internal history, not as static archives.

Their value is that they preserve:

- prior rationale
- recurring committee questions
- persistent portfolio themes
- unresolved issues across months

That makes them a core input lane for agent2.
