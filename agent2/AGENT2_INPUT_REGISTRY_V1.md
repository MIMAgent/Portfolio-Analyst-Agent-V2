# Agent2 Input Registry v1

Last updated: 2026-06-10

## Purpose

This document defines the input sources for agent2.

It answers:

- what the agent reads
- where those inputs come from
- which inputs are authoritative
- which inputs are derived
- which output sections each input powers

The key design choice for agent2 is:

- **raw monthly source files are the authoritative inputs**
- derived CSV / JSON artifacts are parser outputs, not the primary source of truth

---

## Core Rule

For agent2, the authoritative monthly inputs for:

- VIR
- algo
- fund positioning
- benchmark positioning

should come from the monthly source files provided by the user.

Current authoritative source pack:

- `data/2026-05-31/RMv2_PCT_Mstar_funds_2026-06-08.xlsm`
- `data/2026-05-31/202605-Equity Model.xlsx`
- `data/2026-05-31/202605- Fixed Income Model.csv`
- `data/2026-05-31/Algo LR (3).xlsx`

Per user instruction, these should be treated as the May 2026 source pack even where a filename carries a June 2026 date.

---

## Input Families

Agent2 uses three input families:

1. structured monthly source files
2. internal document sources
3. trusted external web sources

---

## 1. Structured Monthly Source Files

These are the primary portfolio and signal inputs.

### 1.1 Morningstar fund workbook

**Path**

- `data/2026-05-31/RMv2_PCT_Mstar_funds_2026-06-08.xlsm`

**Type**

- raw monthly workbook

**Required**

- yes

**Primary role**

- authoritative source for fund and benchmark positioning
- holdings / sleeve / look-through structure

**Agent2 sections powered**

- `header`
- `fund_snapshot`
- `material_positions`
- `fund_snapshot.largest_overweights`
- `fund_snapshot.largest_underweights`
- `portfolio_implications`

**Key outputs expected from parsing**

- fund position weights
- benchmark weights
- active weights
- look-through and lineage inputs
- sleeve-level and security-level contributors

---

### 1.2 Equity VIR workbook

**Path**

- `data/2026-05-31/202605-Equity Model.xlsx`

**Type**

- raw monthly workbook

**Required**

- yes for equity funds and equity sleeves

**Primary role**

- authoritative equity VIR source
- should also provide decomposition / driver detail where available

**Agent2 sections powered**

- `material_positions`
- `signal_summary`
- `top_movers`
- `decomposition_summary`
- `challenge_book`
- `pm_questions`

**Key outputs expected from parsing**

- current VIR
- month-over-month VIR change
- rank / relative attractiveness
- decomposition driver contributions
- headline vs driver-level interpretation

---

### 1.3 Fixed Income VIR file

**Path**

- `data/2026-05-31/202605- Fixed Income Model.csv`

**Type**

- raw monthly file

**Required**

- yes for fixed income funds / bond ACIDs

**Primary role**

- authoritative fixed income VIR source

**Agent2 sections powered**

- `material_positions`
- `signal_summary`
- `top_movers`
- `decomposition_summary`
- `challenge_book`

**Key outputs expected from parsing**

- fixed income VIR values
- fixed income VIR changes
- decomposition inputs where present

---

### 1.4 Algo workbook

**Path**

- `data/2026-05-31/Algo LR (3).xlsx`

**Type**

- raw monthly workbook

**Required**

- yes

**Primary role**

- authoritative algo signal source

**Agent2 sections powered**

- `material_positions`
- `signal_summary`
- `top_movers`
- `challenge_book`
- `pm_questions`

**Key outputs expected from parsing**

- algo active weight
- algo direction / stance
- algo month-over-month change
- disagreement vs current positioning

---

## 2. Derived Structured Artifacts

These are not the primary source of truth.
They are parser outputs that make agent retrieval easier and more stable.

### 2.1 Rolled exposure artifacts

**Paths**

- `artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/fund_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/account_rolled_exposure_summary.csv`
- `artifacts/rolled_exposures/account_rolled_exposure_detail.csv`
- `artifacts/rolled_exposures/fund_rollthrough_definitions.csv`
- `artifacts/rolled_exposures/fund_rollthrough_coverage.csv`

**Type**

- derived parser outputs

**Required**

- yes for the first practical implementation layer

**Primary role**

- provide normalized fund/benchmark/active views by ACID
- provide stable lineage and cross-reference surfaces

**Agent2 sections powered**

- `fund_snapshot`
- `material_positions`
- `signal_summary`
- `portfolio_implications`
- `source_index`

**Important note**

These should be regenerated from the raw monthly files, not manually edited.

---

### 2.2 Production frontend data

**Paths**

- `frontend/web/src/data/funds/index.js`
- `frontend/web/src/data/funds/<fund-id>/`
- `frontend/web/src/data/signalHistory.json`

**Type**

- derived presentation data and fund registry

**Required**

- no for agent2 core logic

**Primary role**

- used by the production Netlify UI
- not a primary agent input

**Agent2 sections powered**

- none directly in the preferred design

**Important note**

Agent2 should not depend on frontend copies as its source of truth. The only
production frontend is `frontend/web`; do not create a parallel implementation.

---

## 3. Internal Document Sources

These provide prior rationale, committee history, and internal house view.

### 3.1 Old IC checklist docs

**Current sample files**

- `C:/Users/schuri2/Downloads/March 2026 Mutual Fund Checklist - US Equity.docx`
- `C:/Users/schuri2/Downloads/April 2026 Mutual Fund Checklist - US Equity.docx`
- `C:/Users/schuri2/Downloads/May 2026 Mutual Fund Checklist - US Equity.docx`

**Type**

- internal historical documents

**Required**

- strongly recommended

**Primary role**

- prior PM rationale
- recurring checklist language
- prior committee framing
- persistent or unresolved issues

**Agent2 sections powered**

- `challenge_book`
- `pm_questions`
- `portfolio_implications`
- `roadmap`
- `data_quality_flags`

**Key outputs expected from ingestion**

- prior internal view
- previous rationale
- recurring positioning themes
- stale or unresolved items

---

### 3.2 SharePoint-synced internal research folder

**Path**

- `C:\Users\schuri2\MORNINGSTAR INC\MIM Global Research - Final Research (yyyymm-AC-ACID-project title)`

**Type**

- synced internal research folder

**Required**

- strongly recommended

**Primary role**

- internal research
- project-level documents
- PM / analyst supporting material

**Agent2 sections powered**

- `challenge_book`
- `pm_questions`
- `portfolio_implications`
- `roadmap`
- `source_index`

**Important note**

For phase 1, this local synced folder is sufficient.
Direct SharePoint API access is not required yet.

---

## 4. Trusted External Web Sources

These provide current real-world context.

### 4.1 External source class

**Type**

- trusted external web sources

**Required**

- yes for full challenge quality

**Primary role**

- provide live context for bull case / bear case / challenge construction

**Agent2 sections powered**

- `top_movers`
- `decomposition_summary`
- `challenge_book`
- `pm_questions`
- `portfolio_implications`

### Preferred source hierarchy

1. official company sources
2. official filings and public data
3. internal sources
4. approved external market / macro sources

### Examples

- company investor relations
- SEC / EDGAR
- Federal Reserve / FRED
- BLS
- BEA
- other approved high-trust sources

### Important note

The agent should have room to search broadly enough to think like an analyst, but should only retain and cite trustworthy sources.

---

## 5. Fund Metadata

This is a lightweight but important input family.

### 5.1 Fund metadata table

**Status**

- not yet formalized

**Required**

- yes

**Expected fields**

- fund name
- fund slug
- fund type
- benchmark
- PM names
- optional mandate notes

**Agent2 sections powered**

- `header`
- `fund_snapshot`
- `run_metadata`

**Implementation note**

This can start as a small CSV or JSON file under `agent2/inputs/`.

---

## Required vs Optional Summary

### Required for first usable agent2 run

- `RMv2_PCT_Mstar_funds_2026-06-08.xlsm`
- `202605-Equity Model.xlsx`
- `202605- Fixed Income Model.csv`
- `Algo LR (3).xlsx`
- rolled exposure parser outputs
- basic fund metadata

### Strongly recommended for strong analytical output

- old IC docs
- SharePoint-synced internal research files
- trusted external web context

### Optional for later phases

- direct SharePoint API integration
- richer archived PM review history
- broader fund-specific rule libraries

---

## Input To Output Mapping

### `fund_snapshot`

Powered by:

- Morningstar workbook
- rolled exposure outputs
- fund metadata

### `material_positions`

Powered by:

- Morningstar workbook
- equity VIR
- fixed income VIR
- algo workbook
- rolled exposure outputs

### `signal_summary`

Powered by:

- VIR
- algo
- decomposition
- rolled exposure outputs

### `top_movers`

Powered by:

- VIR
- decomposition
- trusted external web

### `decomposition_summary`

Powered by:

- equity VIR workbook
- fixed income VIR file
- trusted external web context for interpretation

### `challenge_book`

Powered by:

- positions / active weights
- VIR
- algo
- decomposition
- old IC docs
- SharePoint research docs
- trusted external web

### `pm_questions`

Powered by:

- all three evidence lanes together

### `portfolio_implications`

Powered by:

- portfolio data
- internal history
- external context

### `roadmap`

Powered by:

- old IC docs
- internal research docs
- current open challenge themes

---

## Operating Rule

Agent2 should always prefer:

1. raw monthly source files for current portfolio / signal truth
2. derived artifacts for normalized retrieval
3. internal documents for prior rationale
4. trusted external sources for current confirming or challenging evidence

That keeps the agent both grounded and useful.

---

## Summary

The key input design decision is simple:

- current truth comes from the monthly source files you provided
- historical internal rationale comes from old IC docs and synced research files
- current live challenge context comes from trusted external sources

That is the input foundation for agent2.
