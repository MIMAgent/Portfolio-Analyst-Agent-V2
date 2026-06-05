# Agent Reasoning Loop And Memory v1

## Purpose

This document defines the v1 contract for the Portfolio Analyst Agent's monthly reasoning loop, tool surface, memory model, output package, historical replay controls, and contingent Challenge framing.

It is the deliverable called for by Sprint 3 in `docs/PROJECT_DASHBOARD_Q2_2026.md` ("Agent operating design"). It supersedes the agent-loop placeholders in `MODEL1_OUTPUT_PACKAGE_DECISION_PENDING.md` for Model 1 design, and it stands alongside the parser specs and mapping schema rather than replacing them.

This document is not an implementation. It is the contract the implementation must conform to.

## Design Principles Carried Forward

- The agent is LLM-led. Python provides ingestion, persistence, validation, audit logging, replay controls, and tool wrappers. The LLM performs hypothesis formation, decomposition interpretation, position challenge, memory proposals, and PM-facing output.
- ACID is the canonical join key.
- The mapping layer is behavioral, not just taxonomic. `interpretation_type`, `comparison_group`, `relative_value_group`, `parent_family`, `investable_flag`, `curve_aware`, and `stf_favorable_direction` directly drive how the agent reasons.
- The universal behavior rule applies: the agent does not stop at saying an asset class is attractive or unattractive. It identifies the more precise expression within the broader sleeve.
- Every analytical claim must be evidence-citable to a stable row ID, a memory entry, or a deterministic derivation.
- Historical replay must be explicitly controlled. Prior-period reviews must not retrieve data, documents, memory, or derived artifacts created after the run's `as_of_date`.

## Operating Mode

The Model 1 agent operates one fund at a time.

The fund queue is driven by `DEFAULT_FUND_ORDER` in `src/portfolio_analyst_agent/fund_review.py`. The Python harness manages the queue. The LLM does not aggregate across funds. Cross-fund firmwide synthesis is deferred to Model 3.

Per fund, the agent produces:

- one Change Brief, always
- one Sizing Considerations artifact, always when algo coverage is available
- one Challenge Brief, only when at least one Challenge trigger fires and at least one candidate is accepted by the agent
- a structured set of memory operations, initially proposed for review unless governance permits auto-apply

A monthly run is the cartesian product of: one snapshot date, one as-of date, one fund queue, one parser version, one mapping version, one governance version, and one algo version. The Python harness records this as a `review_run_id` and propagates it into every artifact and memory entry produced by the run.

## Run Metadata

Every per-fund run carries this metadata:

```
ReviewRunMetadata {
  review_run_id,
  fund,
  snapshot_date,
  prior_snapshot_date,
  as_of_date,
  parser_version,
  mapping_version,
  governance_version,
  algo_version,
  source_file_hashes,
  generated_at,
  run_mode                       // live_monthly | historical_replay | ad_hoc
}
```

Rules:

- `as_of_date` is required. In live monthly mode it normally equals the run date.
- In historical replay mode, every read tool must enforce `record_available_date <= as_of_date`.
- Source file hashes are captured for each input workbook, CSV, mapping file, governance file, and generated intermediate artifact used by the run.
- A run is not valid unless `parser_version`, `mapping_version`, `governance_version`, and `algo_version` are known.

## Historical Replay Guardrails

Historical replay is useful for workflow QA, parser validation, and reviewing whether the agent asks reasonable questions from contemporaneous evidence. It is not a clean predictive backtest, because the base LLM may have latent knowledge of events after the replay date.

Replay mode must enforce:

- all read tools accept `as_of_date`
- memory reads expose only entries created on or before `as_of_date`
- memory reads expose only the version of an entry valid as of `as_of_date`
- input artifacts are selected by `snapshot_date` and availability date, not by latest file present on disk
- output language includes a `historical_replay` run-mode marker
- tools reject requests that would retrieve future-dated rows or future memory

Replay mode reduces hindsight leakage but does not eliminate it. Results from historical replay should be treated as reasoning and workflow tests, not as standalone evidence of forecasting skill.

## The Per-Fund Monthly Loop

The loop is a playbook the agent works through, not a fixed pipeline. The agent is permitted to revisit earlier steps when later evidence demands it. The harness records the actual tool-call sequence as the analytical trace.

### Step 0. Initialize

Inputs supplied by the harness:

- `fund`
- `snapshot_date`
- `prior_snapshot_date`
- `as_of_date`
- `review_run_id`
- parser, mapping, governance, and algo versions

### Step 1. Recall

Call `recall_memory(fund, snapshot_date, as_of_date)` to load the fund's prior context:

- thesis ledger entries
- open challenge tracker entries
- accepted exceptions log entries
- unresolved watch items

The agent reads these before consulting current data so that this month's snapshot is interpreted against last month's stated view, not in isolation.

### Step 2. Snapshot

Call `get_fund_snapshot(fund, snapshot_date, as_of_date)` to load the current state:

- rolled exposure rows for the fund by ACID
- target, benchmark, active, and month-over-month exposure fields
- VIR fields by ACID
- algo fields by ACID and perspective
- coverage and benchmark diagnostics
- join statuses

### Step 3. Mover Identification

For each material ACID position in the fund, identify what changed at the VIR, algo, and exposure level. Python returns structured fields; the agent decides which changes matter analytically.

Materiality may be triggered by any configured threshold:

- `materiality_threshold_active`
- `materiality_threshold_target`
- `materiality_threshold_benchmark`
- `materiality_threshold_exposure_mom`
- `materiality_threshold_algo_mom`

### Step 4. Selective Lineage

For any mover or anomaly that warrants explanation, call `get_exposure_lineage(fund, acid, snapshot_date, as_of_date)` to retrieve the underlying account contributions and security-level rows. The agent decides which ACIDs warrant lineage; not every ACID needs it.

### Step 5. Selective Peer Context

For each material position whose mapping indicates relative-value reasoning, call `get_peer_context(acid, snapshot_date, as_of_date)` to evaluate whether the current expression is the cleanest implementation or whether a peer in the same group is materially more attractive.

This is the input that powers Challenge Trigger 5.

### Step 6. Selective History

For movers with status changes that may indicate a regime shift rather than a one-month blip, call `get_acid_history(acid, snapshot_date, as_of_date, lookback_months)` to inspect the STF and decomposition trajectory.

### Step 7. Trigger Evaluation

Call `evaluate_challenge_triggers(fund, snapshot_date, as_of_date)`. This is a deterministic Python tool that returns structured trigger candidates.

Python identifies candidates. The agent decides whether each candidate merits inclusion in the Challenge Brief.

Each trigger candidate has a stable `trigger_candidate_id`. A `challenge_id` is created only when the agent opens or updates a challenge through memory operations.

### Step 8. Synthesize Change Brief

Call `write_change_brief(fund, content)` with the structured payload defined below. The Change Brief is always produced, even when nothing material has changed.

### Step 9. Synthesize Sizing Considerations

Call `write_sizing_considerations(fund, content)` when algo coverage is available. This artifact is separate from the Change Brief. The Change Brief may summarize the sizing artifact, but the detailed algo discussion lives in its own artifact.

### Step 10. Propose Memory Updates

Call `update_memory(fund, ops)` with the structured list of memory operations.

In Model 1, memory operations are stored with a review state. Governance may permit selected operations to auto-apply, but the default is to persist them as `proposed` for human review.

When the agent accepts a trigger candidate, `update_memory` creates or updates the corresponding challenge and returns the final `challenge_id`.

### Step 11. Synthesize Challenge Brief

If at least one trigger candidate was accepted and a corresponding challenge record exists, call `write_challenge_brief(fund, content)`.

If no trigger fires, or if the agent dismisses all candidates with documented reasoning, no Challenge Brief is emitted.

### Step 12. Close

The harness writes the analytical trace and closes the per-fund run. The next fund in the queue begins.

## Tool Surface

The tool surface is medium-coarse: one tool per analytical question an institutional PM analyst would naturally ask out loud.

All tools accept and return JSON-serializable structured payloads. Field names mirror the canonical fields already defined in the parser specs.

### Read Tools

#### 1. `get_fund_snapshot`

Inputs:

- `fund`
- `snapshot_date`
- `as_of_date`

Returns:

- `fund_metadata`: fund name, snapshot date, benchmark family, fund rollthrough definition fields
- `coverage`: target match pct, benchmark match pct, benchmark expected status
- `acid_rows`: rows from `fund_weights_vir_algo_multisignal.csv` filtered to this fund, with stable `row_id`
- `diagnostics`: references to benchmark, VIR, algo, and mapping diagnostics
- `run_metadata`: version and source hash fields needed for citation and audit

#### 2. `get_acid_history`

Inputs:

- `acid`
- `snapshot_date`
- `as_of_date`
- `lookback_months` (default 12)
- `model_family` (optional; auto-resolved from the ACID mapping if omitted)

Returns:

- time series of STF, delta STF, rank, and decomposition fields per snapshot
- stable `row_id` per time-series row
- regime flag fields if computable

#### 3. `get_exposure_lineage`

Inputs:

- `fund`
- `acid`
- `snapshot_date`
- `as_of_date`

Returns:

- account-level contributions to this fund's exposure
- security-level rows from `fund_rolled_exposure_detail.csv`
- stable `row_id` per lineage row
- `security_name`, `common_identifier`, `h_path`, `security_weight`, `account_weight`, `fund_target_security_contribution`, and `fund_benchmark_security_contribution`

#### 4. `get_peer_context`

Inputs:

- `acid`
- `snapshot_date`
- `as_of_date`

Returns:

- the ACID's mapping fields
- peer ACIDs in the same `comparison_group`
- peer ACIDs in the same `relative_value_group`
- the parent family ACID's current signal if `parent_family` is populated
- `stf_favorable_direction` for the ACID and peers
- stable `row_id` values for all returned rows

#### 5. `recall_memory`

Inputs:

- `fund`
- `snapshot_date`
- `as_of_date`
- `scope` (optional list, subset of `["thesis_ledger", "open_challenges", "exceptions", "watch_items"]`; default all)

Returns:

- thesis ledger entries valid as of `as_of_date`
- open challenge tracker entries valid as of `as_of_date`
- accepted exception entries valid as of `as_of_date`
- unresolved watch items valid as of `as_of_date`

#### 6. `evaluate_challenge_triggers`

Inputs:

- `fund`
- `snapshot_date`
- `as_of_date`

Returns:

- list of trigger candidates
- candidate fields: `trigger_candidate_id`, `acid`, `trigger_type`, `evidence`, `suppression_status`
- `trigger_type` values: `sign_disagreement`, `decomposition_rotation`, `better_expression_available`

This tool is deterministic. The agent does not invent trigger candidates. The agent judges whether each fired candidate merits a Challenge Brief item or should be dismissed.

### Write Tools

#### 7. `write_change_brief`

Inputs:

- `fund`
- `content`: a `ChangeBriefPayload` matching the schema in the Output Package section

Behavior:

- validates the payload against the schema
- rejects writes containing narrative claims without citation tokens
- persists Markdown and JSON forms under `artifacts/monthly_review/<snapshot_date>/<fund>/`

#### 8. `write_sizing_considerations`

Inputs:

- `fund`
- `content`: a `SizingConsiderationsPayload`

Behavior:

- validates factual algo and positioning claims against citation tokens
- persists Markdown and JSON forms alongside the Change Brief
- does not recommend trades or target weights

#### 9. `update_memory`

Inputs:

- `fund`
- `ops`: list of typed memory operations

Operation types:

- `affirm_thesis(acid, evidence_pointers)`
- `update_thesis(acid, thesis_text, thesis_drivers, falsification_conditions, evidence_pointers)`
- `create_thesis(acid, thesis_text, thesis_drivers, falsification_conditions, evidence_pointers)`
- `mark_thesis_weakening(acid, reason, evidence_pointers)`
- `mark_thesis_contradicted(acid, reason, evidence_pointers)`
- `supersede_thesis(acid, reason)`
- `open_challenge(trigger_candidate_id, acid, trigger_type, challenge_text, evidence_pointers)`
- `update_challenge(challenge_id, trigger_candidate_id, challenge_text, evidence_pointers)`
- `close_challenge(challenge_id, resolution_text, evidence_pointers)`
- `escalate_challenge_to_ic(challenge_id, reason)`
- `dismiss_challenge(trigger_candidate_id, reason, evidence_pointers)`
- `create_watch_item(acid, watch_text, review_checkpoint, evidence_pointers)`
- `close_watch_item(watch_item_id, reason, evidence_pointers)`
- `log_exception(acid_or_pattern, trigger_types, exception_text, effective_from, review_cadence, evidence_pointers)`
- `expire_exception(exception_id, reason)`

Behavior:

- each op is schema-validated
- each op records `review_run_id`, `snapshot_date`, `as_of_date`, and timestamp
- each op receives `review_state`: `proposed`, `approved`, `applied`, or `rejected`
- conflicting ops within the same call are rejected
- accepted trigger candidates return the corresponding `challenge_id`

#### 10. `write_challenge_brief`

Inputs:

- `fund`
- `content`: a `ChallengeBriefPayload`

Behavior:

- validates that each item references a fired `trigger_candidate_id`
- validates that each accepted item has a corresponding `challenge_id`
- rejects writes where every item is dismissed
- persists Markdown and JSON forms alongside the Change Brief

## Memory Model

Memory is persisted as JSON files in v1 under `artifacts/memory/`. A real database is deferred to Model 2 and is the natural place to introduce row-level access controls and the `visibility_scope` enforcement needed for Model 3.

### Tier 1 - Required For Model 1

#### Thesis ledger

Keyed by `(fund, acid)` with status `active`.

Fields:

- `thesis_id`
- `fund`
- `acid`
- `thesis_text`
- `thesis_drivers`
- `last_affirmed_snapshot_date`
- `last_affirmed_stf`
- `last_affirmed_decomp`
- `falsification_conditions`
- `status`: `active` | `weakening` | `contradicted` | `superseded`
- `review_state`: `proposed` | `approved` | `applied` | `rejected`
- `created_at`
- `updated_at`
- `created_by_review_run_id`
- `last_updated_by_review_run_id`
- `visibility_scope`: defaults to `personal` in Model 1
- `evidence_pointers`

Invariants:

- only one applied row per `(fund, acid)` may have status `active` at any time
- a thesis can be `superseded` only by a new thesis on the same `(fund, acid)`
- `last_affirmed_snapshot_date` may not move backward

#### Open challenge tracker

Keyed by `challenge_id`.

Fields:

- `challenge_id`
- `trigger_candidate_id`
- `fund`
- `acid`
- `trigger_type`: `sign_disagreement` | `decomposition_rotation` | `better_expression_available`
- `trigger_evidence`
- `challenge_text`
- `status`: `open` | `resolved` | `escalated_to_ic` | `dismissed_with_reason`
- `review_state`: `proposed` | `approved` | `applied` | `rejected`
- `opened_at_snapshot_date`
- `last_seen_snapshot_date`
- `resolved_at_snapshot_date`
- `resolution_text`
- `dismissal_reason`
- `created_by_review_run_id`
- `evidence_pointers`

Behavior:

- when a trigger fires for an existing open challenge, the agent updates `last_seen_snapshot_date` and re-affirms or revises the challenge text rather than creating a duplicate
- a challenge that has not been seen for `stale_challenge_threshold_months` is flagged for attention but is not auto-resolved

#### Accepted exceptions log

Keyed by `exception_id`.

Fields:

- `exception_id`
- `fund`
- `scope`: `acid` | `acid_pattern` | `fund_wide`
- `acid` or `acid_pattern`
- `trigger_types`: list of trigger types covered by the exception
- `exception_text`
- `effective_from`
- `effective_to`
- `review_cadence`: `monthly` | `quarterly` | `annually` | `ad_hoc`
- `last_reviewed_snapshot_date`
- `review_state`: `proposed` | `approved` | `applied` | `rejected`
- `created_by_review_run_id`
- `evidence_pointers`

Behavior:

- an exception suppresses Challenge triggers that match its scope and `trigger_types` while it is active
- suppressed triggers remain visible in the Change Brief's memory updates summary
- exceptions are reviewed at their `review_cadence`

#### Watch item tracker

Keyed by `watch_item_id`.

Purpose:

- capture important cited observations that do not meet a formal Challenge trigger
- preserve analyst curiosity without weakening the discipline of the Challenge Brief

Fields:

- `watch_item_id`
- `fund`
- `acid`
- `watch_text`
- `reason`
- `review_checkpoint`
- `status`: `open` | `closed`
- `review_state`: `proposed` | `approved` | `applied` | `rejected`
- `created_by_review_run_id`
- `last_seen_snapshot_date`
- `evidence_pointers`

### Tier 2 - Deferred To Model 2

- standing house views at fund or firm level
- decision audit trail
- human approval queue for proposed memory operations
- durable database persistence and row-level access controls

### Tier 3 - Deferred To Model 3

- cross-PM shared observations
- endorsement and challenge mechanics
- IC promotion workflow

Tier 1 schemas already include `visibility_scope` so that Tier 3 can be enforced later without a breaking migration. In Model 1, the field is always `personal`.

## Output Package

The Model 1 monthly output package has three artifacts:

- Change Brief
- Sizing Considerations
- Challenge Brief, conditional

The Sizing Considerations artifact is separate from the Change Brief. This preserves the prior decision that algo output should be its own artifact while still allowing the Change Brief to cite and summarize it.

### Change Brief

Always produced.

Schema:

```
ChangeBriefPayload {
  header: {
    fund,
    snapshot_date,
    prior_snapshot_date,
    as_of_date,
    review_run_id,
    parser_version,
    mapping_version,
    governance_version,
    algo_version,
    run_mode
  },
  executive_summary,
  material_movers: [
    {
      acid,
      active_rolled_exposure,
      target_rolled_exposure,
      benchmark_rolled_exposure,
      exposure_mom,
      vir_stf,
      vir_delta_stf,
      vir_rank_change_by_stf,
      decomposition_drivers,
      narrative,
      evidence_pointers
    }
  ],
  decomposition_narrative,
  lineage_notes: [
    {
      acid,
      contributing_accounts,
      contributing_securities_sample,
      narrative,
      evidence_pointers
    }
  ],
  sizing_artifact_summary: {
    artifact_path,
    headline_agreements,
    headline_disagreements,
    largest_algo_mom_changes,
    evidence_pointers
  },
  memory_updates_summary: {
    theses_affirmed,
    theses_updated,
    theses_marked_weakening,
    theses_marked_contradicted,
    theses_created,
    challenges_opened,
    challenges_closed,
    watch_items_opened,
    watch_items_closed,
    exceptions_logged,
    exceptions_expired,
    stale_items_flagged,
    proposed_memory_ops
  },
  triggers_fired_summary,
  evidence_index
}
```

### Sizing Considerations

Always produced when algo coverage is available.

Schema:

```
SizingConsiderationsPayload {
  header: {
    fund,
    snapshot_date,
    as_of_date,
    review_run_id,
    algo_version,
    mapping_version,
    run_mode
  },
  perspective_summary: {
    local_real,
    usd_unhedged
  },
  algo_vs_positioning_agreement: [
    { acid, perspective, narrative, evidence_pointers }
  ],
  algo_vs_positioning_disagreement: [
    { acid, perspective, narrative, evidence_pointers }
  ],
  largest_algo_mom_changes: [
    { acid, perspective, metric_type, value, narrative, evidence_pointers }
  ],
  coverage_notes,
  evidence_index
}
```

The artifact is factual and non-prescriptive. It may say the algo output is more or less aligned with current positioning. It may not recommend trades or target weights.

### Challenge Brief

Conditional. Emitted only when at least one trigger fires and at least one item is not dismissed.

Schema:

```
ChallengeBriefPayload {
  header: { fund, snapshot_date, as_of_date, review_run_id, parser_version, mapping_version, governance_version },
  items: [
    {
      challenge_id,
      trigger_candidate_id,
      acid,
      trigger_type,
      position_summary: {
        active_rolled_exposure,
        target_rolled_exposure,
        benchmark_rolled_exposure
      },
      disagreement_statement,
      challenge,
      cleaner_expression,
      falsification_framing,
      next_review_checkpoint,
      evidence_pointers
    }
  ],
  evidence_index
}
```

## Challenge Trigger Predicates

Three core triggers are included in v1. VIR/algo disagreement is captured factually inside the Sizing Considerations artifact and does not by itself open a Challenge. STF trend reversal is treated as a sub-condition of decomposition rotation.

All thresholds are governance parameters maintained outside agent code.

### Trigger 1 - Sign disagreement

Fires when:

- `abs(active_rolled_exposure) >= materiality_threshold_active`
- the active direction conflicts with the VIR direction signal
- VIR direction signal is based on category quartiles and `stf_favorable_direction`

Signal rule:

- if `stf_favorable_direction = higher_is_better`, top quartile is `overweight` and bottom quartile is `underweight`
- if `stf_favorable_direction = lower_is_better`, bottom quartile is `overweight` and top quartile is `underweight`
- middle two quartiles are `neutral` and do not trigger

### Trigger 3 - Decomposition rotation

Fires when:

- a thesis exists for `(fund, acid)` with status `active`
- the dominant decomposition driver in the current snapshot differs from the dominant driver recorded in the thesis at last affirmation
- the prior dominant driver has weakened by `decomposition_weakening_threshold` or changed sign

Dominant driver is the largest absolute contribution among the decomposition fields relevant to the model family.

### Trigger 5 - Better expression available

Fires when:

- the position is in an ACID whose `interpretation_type` supports relative-value comparison or whose `curve_aware = true`
- a peer ACID in the same `relative_value_group` has STF at least `peer_advantage_threshold` better in the favorable direction
- the peer has `investable_flag = true`
- the fund holds the parent or broad ACID and either does not hold the better peer or holds it at materially lower weight than the parent

This trigger operationalizes the universal behavior rule from `ACID_MAPPING_SCHEMA_V1.md`.

### Trigger Suppression

A trigger is suppressed when an active accepted exception covers the `(fund, acid)` and explicitly includes the relevant `trigger_type`.

Suppressed triggers are still recorded in the Change Brief's memory updates summary.

### Near Misses

Near-miss triggers do not open a Challenge Brief item in v1. They may be surfaced as watch items when:

- the candidate falls just below a materiality threshold
- the agent identifies a cited reason to monitor the position
- the observation is useful but not strong enough for formal challenge framing

The exact near-miss thresholds remain an open governance calibration item.

## Evidence And Citation Contract

Every analytical claim in any artifact and every memory entry's `evidence_pointers` field must resolve to one of:

- a CSV row reference: `csv:<artifact_path>#row_id=<stable_row_id>`
- a memory entry reference: `mem:<table>#<record_id>`
- a derivation reference: `deriv:<formula_name>?inputs=<row_refs>`

Stable `row_id` values are required for generated CSV artifacts. Compound key citations may be used during prototyping, but they are not sufficient for production because labels and values can contain duplicates or change formatting.

The Change Brief, Sizing Considerations artifact, and Challenge Brief embed citation tokens inline. The rendering layer resolves them to human-readable references for PM display and structured links for downstream tooling.

The write tools reject payloads where any narrative claim is missing a citation token. This is enforced at the tool boundary.

## Validation Rules

The agent run is rejected if:

- any memory operation violates a Tier 1 schema invariant
- a Challenge Brief is emitted without a corresponding fired trigger candidate
- a Challenge Brief item lacks a corresponding challenge record
- a narrative claim lacks a resolvable citation token
- the fund being reviewed is not in `DEFAULT_FUND_ORDER`
- `parser_version`, `mapping_version`, `governance_version`, or `algo_version` cannot be determined
- a read tool retrieves data after `as_of_date`

The agent run warns but does not fail when:

- some bond ACIDs in the fund are missing from VIR, until FI VIR normalization is added to the aligned output
- an exception is logged for an ACID that is not in the current mapping file
- an open challenge has gone more than `stale_challenge_threshold_months` without resolution
- a thesis has not been affirmed in more than `stale_thesis_threshold_months` and the position is still material
- algo coverage for a fund is materially incomplete relative to the fund's exposures
- benchmark diagnostics indicate a fund-level benchmark is unavailable or unusable

## Governance Parameters

These are configuration values, not constants in code. They live in a single governance file such as `config/agent_governance.yaml` and are versioned alongside the mapping files.

- `materiality_threshold_active` (default placeholder: 50 bps)
- `materiality_threshold_target`
- `materiality_threshold_benchmark`
- `materiality_threshold_exposure_mom`
- `materiality_threshold_algo_mom`
- `decomposition_weakening_threshold` (default placeholder: 33 percent)
- `peer_advantage_threshold` (default placeholder: 25 bps)
- `near_miss_threshold_buffer`
- `stale_challenge_threshold_months` (default placeholder: 3)
- `stale_thesis_threshold_months` (default placeholder: 6)
- `vir_quartile_universe`
- `auto_apply_memory_ops`

Each parameter change is a logged governance event with `effective_from` semantics, mirroring the crosswalk file approach.

## Out Of Scope For v1

- automatic trade or sizing recommendations
- cross-fund firmwide synthesis
- IC packet assembly
- shared memory across users
- enforcement of `visibility_scope` beyond defaulting to `personal`
- challenge triggers beyond the three defined here
- claims that historical replay is a clean ex-ante backtest

## Open Follow-Ups

- Calibrate numeric thresholds against several historical and forward shadow months before locking defaults.
- Add the FI VIR normalization layer so bond ACIDs can participate in Triggers 1, 3, and 5. Until that lands, bond ACIDs should be flagged `not_evaluable_for_vir_triggers` rather than treated as no-trigger.
- Decide whether near-miss triggers should be surfaced in the Change Brief, the Sizing Considerations artifact, or only as watch items.
- Decide whether memory edits should default to proposed-only in Model 1 or whether some low-risk operations can auto-apply.
- Decide the on-disk layout of the v1 memory JSON files.
- Define the UI rendering contract for citation tokens and evidence drill-down.

## Relationship To Other Specs

This spec depends on:

- `EQUITY_VIR_PARSER_SPEC_V1.md` for equity decomposition field definitions
- `FIXED_INCOME_VIR_PARSER_SPEC_V1.md` for fixed income decomposition field definitions
- `ACID_MAPPING_SCHEMA_V1.md` for behavioral mapping fields
- `MONTHLY_ALGO_PARSER_SPEC_V1.md` for the algo metric blocks consumed in the separate sizing artifact
- `ROLLED_EXPOSURE_AND_FUND_ALIGNMENT_WORKFLOW_2026-04-09.md` for the `fund_weights_vir_algo_multisignal.csv` contract that backs `get_fund_snapshot`

This spec does not modify any of the above. It consumes them.
