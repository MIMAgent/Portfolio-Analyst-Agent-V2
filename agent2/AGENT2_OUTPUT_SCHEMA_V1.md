# Agent2 Output Schema v1

Last updated: 2026-06-10

## Purpose

This document defines the first structured output contract for agent2.

The output is intended to be the canonical review packet that can later power:

- Word documents
- the frontend application
- HTML summaries
- archived monthly review records

The output should be built for analytical reuse first, not for direct visual presentation.

---

## Design Principles

### 1. One canonical packet per fund per review run

Each agent2 run should produce one structured packet for one fund and one review date.

### 2. Separate facts from reasoning

The packet should distinguish between:

- raw portfolio facts
- internal-history context
- external-context evidence
- agent interpretations

### 3. Preserve provenance

Every meaningful analytical statement should be traceable to one or more source references.

### 4. Support multiple output surfaces

The packet should be rich enough to support:

- app panels
- Word sections
- PM-review summaries
- future comparisons across months

---

## Top-Level Shape

Suggested file name:

- `agent2_review_packet.json`

Top-level structure:

```json
{
  "header": {},
  "fund_snapshot": {},
  "material_positions": [],
  "signal_summary": {},
  "top_movers": [],
  "decomposition_summary": [],
  "challenge_book": [],
  "pm_questions": [],
  "portfolio_implications": [],
  "roadmap": [],
  "data_quality_flags": [],
  "source_index": [],
  "run_metadata": {}
}
```

---

## 1. `header`

Purpose:

- identify the fund and review instance

Suggested fields:

```json
{
  "fund": "MStar US Equity",
  "fund_slug": "mstar-us-equity",
  "fund_type": "equity",
  "benchmark": "Russell 3000",
  "pm_names": ["Doug McGraw", "Mike Budzinski"],
  "snapshot_date": "2026-05-31",
  "as_of_date": "2026-05-31",
  "review_date": "2026-06-10",
  "review_run_id": "rrun_xxx"
}
```

---

## 2. `fund_snapshot`

Purpose:

- provide a compact summary of current fund posture

Suggested fields:

```json
{
  "largest_overweights": [],
  "largest_underweights": [],
  "category_exposures": [],
  "style_posture": [],
  "headline_summary": []
}
```

### `largest_overweights`

Array of objects such as:

```json
{
  "category": "Eq Sector",
  "label": "Financials",
  "active_weight": 3.5,
  "benchmark_weight": 12.0,
  "portfolio_weight": 15.5,
  "source_refs": []
}
```

### `largest_underweights`

Same shape as `largest_overweights`.

### `category_exposures`

Use this for things like:

- region
- country
- sector
- size/style

Example:

```json
{
  "group": "Eq Size / Style",
  "label": "Small Cap",
  "active_weight": 7.1,
  "signal_direction": "constructive",
  "source_refs": []
}
```

### `style_posture`

Examples:

- value-leaning
- growth-leaning
- SMID overweight
- defensive vs cyclical

Each item should be explicit.

---

## 3. `material_positions`

Purpose:

- provide the main analytical working set

This is the most important section.
Each object should represent one material position / exposure / category item under review.

Suggested shape:

```json
{
  "position_id": "mstar-us-equity__em-asia",
  "acid": "EM Asia",
  "category": "Region",
  "portfolio_weight": 2.1,
  "benchmark_weight": 5.6,
  "active_weight": -3.5,
  "vir_now": 6.2,
  "vir_delta_mom": 0.3,
  "algo_view": "constructive",
  "algo_active_weight": 1.8,
  "signal_alignment": "diverge",
  "signal_quality": "improving",
  "decomposition_assessment": "broad_based",
  "internal_history_status": "no_recent_rationale_found",
  "external_context_status": "supportive",
  "importance_score": 8.7,
  "source_refs": []
}
```

### Why this section matters

Everything else can be derived or ranked off this section.

---

## 4. `signal_summary`

Purpose:

- summarize the fund-wide relationship between positioning, VIR, algo, and decomposition

Suggested shape:

```json
{
  "aligned_positions": [],
  "diverging_positions": [],
  "mechanical_signals": [],
  "fund_level_observations": []
}
```

### `aligned_positions`

Brief list of areas where:

- position
- VIR
- algo

are directionally aligned.

### `diverging_positions`

Brief list of areas where:

- current positioning conflicts with VIR and/or algo

### `mechanical_signals`

List where decomposition suggests:

- mostly multiple compression
- mostly FX carry
- mostly tactical noise
- otherwise fragile signal construction

### `fund_level_observations`

Short agent-created analytical statements, such as:

- "The fund's largest persistent divergence remains its underweight to EM Asia despite improving signal support."
- "The IT underweight remains structurally important, but some current upgrades appear more valuation-led than earnings-led."

---

## 5. `top_movers`

Purpose:

- capture the most important signal changes this month

Suggested shape:

```json
{
  "acid": "US IT",
  "category": "Sector",
  "vir_now": 7.0,
  "vir_delta_mom": 1.2,
  "direction": "up",
  "headline_assessment": "valid_but_early",
  "why_it_moved": "multiple_compression_drove_upgrade",
  "portfolio_relevance": "fund remains underweight",
  "source_refs": []
}
```

These should not just restate deltas.
They should interpret them.

---

## 6. `decomposition_summary`

Purpose:

- make decomposition a first-class output surface

Suggested shape:

```json
{
  "acid": "US IT",
  "vir_now": 7.0,
  "vir_delta_mom": 1.2,
  "drivers": [
    {
      "driver": "multiple_compression",
      "contribution": 1.0,
      "share_of_move_pct": 83.0
    },
    {
      "driver": "earnings_revision",
      "contribution": 0.1,
      "share_of_move_pct": 8.0
    }
  ],
  "signal_type": "mechanical",
  "agent_assessment": "upgrade_is_real_but_mostly_valuation_led",
  "source_refs": []
}
```

This section should support judgments like:

- fundamental
- mechanical
- early
- broad-based
- fragile
- supportive for hedged or unhedged exposure

---

## 7. `challenge_book`

Purpose:

- store the most important PM-facing challenge items

Suggested shape:

```json
{
  "challenge_id": "ch_em_asia_2026_05",
  "acid": "EM Asia",
  "category": "Region",
  "priority": "high",
  "challenge_type": "position_vs_signal_divergence",
  "observation": "The fund remains materially underweight despite four months of improving VIR.",
  "interpretation": "The persistence of the underweight looks more like positioning inertia unless prior PM rationale still holds.",
  "bull_case": [
    "Earnings and valuation trends have both improved.",
    "Signal support has persisted across multiple months."
  ],
  "bear_case": [
    "China and Taiwan risk may still justify a cautious stance.",
    "Signal improvement could reverse if macro support weakens."
  ],
  "devils_advocate_statement": "Current positioning appears to lag both signal direction and external evidence.",
  "pm_question": "What specific risk still justifies maintaining this underweight?",
  "what_would_change_view": "A renewed deterioration in earnings revisions would weaken the current challenge.",
  "internal_context_summary": "No recent PM rationale was found in current internal sources.",
  "external_context_summary": "Current external evidence is broadly supportive but still macro-sensitive.",
  "source_refs": []
}
```

This section is where the agent's critical thinking is most visible.

---

## 8. `pm_questions`

Purpose:

- provide explicit PM-facing questions, separate from challenge items

Suggested shape:

```json
{
  "question_id": "q_us_equity_001",
  "priority": "high",
  "topic": "US IT underweight",
  "question": "If the sector upgrade remains mostly valuation-led, what evidence would make us treat it as fundamental enough to revisit the underweight?",
  "reason": "Headline signal improved, but decomposition remains weak.",
  "linked_position_ids": [],
  "source_refs": []
}
```

These questions may be tied to:

- one position
- one broader theme
- one fund-level vulnerability

---

## 9. `portfolio_implications`

Purpose:

- hold short analytical statements about what the current data implies for the portfolio

Suggested shape:

```json
{
  "type": "fund_level_implication",
  "statement": "The fund remains vulnerable to renewed AI-led market leadership because the largest underweights still cluster in large-cap technology.",
  "confidence": "medium",
  "source_refs": []
}
```

Examples:

- style exposure implications
- implementation inefficiency
- persistent vulnerability
- offset structure
- crowding risk

---

## 10. `roadmap`

Purpose:

- capture next-cycle research or review agenda items

Suggested shape:

```json
{
  "topic": "US Tech earnings confirmation",
  "why_it_matters": "Would determine whether the current upgrade is mechanical or fundamental.",
  "linked_positions": [],
  "source_refs": []
}
```

This should support next-review preparation.

---

## 11. `data_quality_flags`

Purpose:

- show what the agent could not fully verify or retrieve

Suggested shape:

```json
{
  "flag_type": "missing_internal_rationale",
  "severity": "medium",
  "scope": "EM Asia",
  "message": "No recent internal rationale found in retrieved documents.",
  "source_refs": []
}
```

Examples:

- missing internal doc coverage
- weak external evidence
- stale benchmark mapping
- incomplete decomposition data
- stale PM metadata

---

## 12. `source_index`

Purpose:

- central registry of the sources used in the packet

Suggested shape:

```json
{
  "source_id": "src_001",
  "source_type": "portfolio_data",
  "label": "fund_weights_vir_algo_multisignal.csv row xyz",
  "path_or_url": "artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv",
  "citation_ref": "csv:artifacts/rolled_exposures/fund_weights_vir_algo_multisignal.csv#row_id=abc",
  "date": "2026-05-31"
}
```

Expected source types:

- `portfolio_data`
- `internal_doc`
- `external_web`
- `derived_analysis`

---

## 13. `run_metadata`

Purpose:

- track how the packet was built

Suggested shape:

```json
{
  "agent_version": "agent2_v1",
  "prompt_version": "agent2_prompt_v1",
  "review_run_id": "rrun_xxx",
  "generated_at": "2026-06-10T12:00:00Z",
  "input_versions": {
    "portfolio_snapshot": "2026-05-31",
    "vir_snapshot": "2026-05-31",
    "algo_snapshot": "2026-05-31"
  }
}
```

---

## Output Writing Principles

### 1. Facts should be structured

Numbers and states should be emitted as fields, not buried in prose.

### 2. Interpretations should be short and explicit

Avoid long essay-style output inside JSON.

### 3. Every important reasoning item should have provenance

Use source references consistently.

### 4. Missing evidence should be represented explicitly

Do not fake completeness.

---

## First-Version Priority

If implementation needs to be phased, build these first:

1. `header`
2. `fund_snapshot`
3. `material_positions`
4. `top_movers`
5. `decomposition_summary`
6. `challenge_book`
7. `pm_questions`
8. `data_quality_flags`
9. `source_index`
10. `run_metadata`

The rest can be layered in after that.

---

## Summary

The agent2 packet should be:

- structured
- evidence-based
- source-aware
- reusable across UI surfaces
- rich enough to capture both facts and analytical challenge

This output contract is the foundation for the rest of the implementation.
