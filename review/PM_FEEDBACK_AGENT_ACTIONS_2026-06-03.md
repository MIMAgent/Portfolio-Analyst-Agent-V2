# PM Feedback → Actionable Agent Updates

**Date:** 2026-06-03
**Source:** `PM Feedback_MB_RW_DM.docx` — interview responses from three PMs (RW, MB, DM) across VIR workflow, portfolio monitoring, board prep, team/process, and a "one thing" wish.
**Companion docs:** `AGENT_DESIGN_REVIEW_2026-06-03.md` (code-level), `AGENT_STRUCTURE_AND_IMPACT_2026-06-03.md` (strategic).
**Purpose:** Translate what PMs actually said into concrete changes to the agent's design, schema, and roadmap.

---

## The five themes the PMs handed us

1. **The anchor signal is contested in the feedback — resolved in favor of STF.** MB anchors on **raw VIR** ("clients can't eat spread-to-fair"); RW and DM anchor on **Spread-to-Fair / STF** (the relative-value + risk metric the whole process is built on). **Team decision (2026-06-03): STF remains the canonical anchor.** Raw VIR is carried as secondary context and MB's view is expressed through documented overrides on specific cells, not by changing the anchor. PMs will still *override* the model in specific cells (MB: "the equity model is perennially biased against IT").
2. **"What changed most" is the entry point** — and they want it as *ranks*, not just levels (DM: US/country sector VIR ranks and STF ranks; RW: "what has changed the most first").
3. **They get surprised by exposures finer than they monitor** — MB found a food-products overweight *larger* than software; a momentum-factor underweight; RW/DM cite AI winner/loser exposure. "Look-through to the industry level is important… not enough to just see sector weight."
4. **Rationale lives in people's heads** (MB, Q12) — and board prep's #1 pain is **data accuracy**, not analysis (all three).
5. **The "one thing" wishes are decision-support, not commentary** — intra-month recompute of "what newly bubbled up" (RW, DM), "what am I *under*-exposed to?" (MB), and "show me VIR/STF *without* the MER FV adjustment" (DM).

---

## Tier 1 — High conviction, multiple PMs, leverages existing machinery

### 1. STF stays the anchor; raw VIR rides alongside as context, with ranks + rank-change
**Decision (2026-06-03):** **Spread-to-Fair (STF) is the canonical anchor signal.** This is fixed by process mandate, not a per-PM preference — it matches how RW and DM describe the process being designed ("our relative valuation scores, absolute valuation scores, and the algorithm are all based on spread to fair, not VIR"). MB's raw-VIR preference is **not** handled by switching the anchor; it is handled as documented standing overrides on specific cells (see #2).
**Said by:** RW (STF — process basis), DM (STF drives the Opp Value algos), MB (prefers raw VIR — *resolved via overrides, not anchor change*).
**Today:** the agent leans on `stf_favorable_direction` + quartiles to fire sign-disagreement. Keep that — it is correct and now explicitly endorsed.
**Change:** triggers and the directional view **anchor on STF**. Every material mover *also* carries **raw VIR alongside** (each with **category rank and rank-change** — DM anchors on ranks) so MB's lens is visible and, more importantly, so the agent can **surface VIR-vs-STF divergence**, which is exactly where the model-bias cases and overrides live (e.g., IT: attractive on raw VIR / MER P/FV, unattractive on the model's STF). Schema change to `material_movers`: add `stf`, `stf_rank`, `stf_rank_delta` as the **primary** fields and `vir_raw`, `vir_rank`, `vir_rank_delta` as **secondary context**; add a `vir_stf_divergence` flag to mark cells where the two disagree materially. The disagreement that opens a challenge is evaluated on **STF**, with raw VIR reported as context only.

### 2. Per-PM standing overrides / house-views as first-class trigger suppressors
**Said by:** MB ("model perennially biased against IT… we adjust accordingly, otherwise we hold IT at a massive underweight"); DM/MB (Korea & US IT unconditionals are "suspect," so STFs are suspect).
**Today:** the exceptions log exists in the memory schema but is inert (nothing writes/approves it; recall is broken — see code review C1).
**Change:** wire standing overrides so they **suppress dogmatic challenges** on the covered ACID/cell and instead annotate: *"model flags IT as a sign-disagreement; you hold a standing MER-P/FV override opened YYYY-MM — does it still hold?"* Add a **data-quality flag** for known-suspect cells (Korea, US IT unconditionals) so triggers there are downgraded to "watch," not "challenge." This is the single clearest validation of the *model-of-the-PM* idea from the strategic doc.

### 3. Move-attribution: split every material VIR move into **valuation/FV-update vs price-movement**
**Said by:** all three — it's the *first* diagnostic. RW: "depends on if it's a fair-value update or driven by price movements." DM: "valuation is easy to determine; if not, ask MAR about fundamental updates." MB: "normally the valuation adjustment term."
**Today:** decomposition fields exist in the pipeline but the agent doesn't label the *cause* of a move.
**Change:** for each mover, compute and label the dominant driver (valuation-adjustment / FV change vs price) from the decomposition, and route the narrative accordingly (price-driven → "confirm fundamental risk unchanged"; FV-driven → "decomposition shows X"). This is deterministic-computable and directly mirrors the PM's own mental flowchart.

### 4. Multi-horizon by default (1M / 1Y / 3Y), not just month-over-month
**Said by:** MB — "we probably focus too much on m/o/m moves without zooming out to a 1- or 3-year lens, where certain 1-month moves might not appear that big."
**Today:** the agent is monthly-snapshot-centric; `get_acid_history` exists but is used "selectively."
**Change:** make multi-horizon framing the **default** on movers. Explicitly flag the two asymmetries: a big 1M move that's *small* in 3Y context (down-weight), and a *small* 1M move that's a large cumulative drift (up-weight). Ties to the "time is the missing dimension" point in the strategic doc.

### 5. Finer-than-sector concentration surprise detector
**Said by:** MB (food-products overweight > software overweight; "look-through to the industry level is important"); DM (style-box allocation/selection).
**Today:** rolled-exposure + lineage machinery already rolls to country / region-sector / bond ACIDs and can drill to security.
**Change:** roll active exposure to **multiple granularities** and flag where a *non-headline* bucket rivals or exceeds a *headline* active bet, or where security-level concentration hides inside a modest sector weight. This directly answers Q6 ("an exposure you didn't realize you had") and reuses the strongest existing part of the codebase.

---

## Tier 2 — High value, modest new scope

### 6. Opportunity-gap / negative-space scan: "what am I *under*-exposed to?"
**Said by:** MB, Q13 — *"To what opportunity/opportunities is my portfolio not exposed enough?"* "I always worry I'm not expressing certain opportunities… because I haven't encountered certain research."
**Change:** generalize the *better-expression* trigger from "is there a cleaner peer for what you hold" to "**which attractive ACIDs (by STF/VIR rank) do you hold below benchmark/peers or not at all**," cross-referenced with whether research coverage exists. This is the inverse-of-holdings scan from the strategic doc — now explicitly requested. Pushes the agent toward decision-*support* without prescribing trades.

### 7. Intra-month / on-demand "what newly bubbled up" runs
**Said by:** RW (Q13, seconded by DM) — "push a button intra-month and produce the VIRs and Algos… in a month like March with a lot of volatility it isn't easy to see how price movements bubbled up any new attractive assets."
**Today:** the runtime *already* supports `as_of_date` + `ad_hoc` `run_mode`. The missing piece is framing.
**Change:** add a **delta-since-last-review** output — what newly screens attractive/unattractive due to price moves since the last snapshot — and make intra-month triggering a first-class, low-friction path (especially post-volatility). Low effort given existing replay infrastructure; high perceived value.

### 8. MER fair-value-adjustment toggle (VIR/STF with and without MER FV)
**Said by:** DM, Q13 — "show me equivalent VIR and STF *without* MER FV adjustment (we have this so it should be easy)… Philip does not want to use MER at all." Ties to MB's IT example (IT screens attractive *through an MER P/FV lens*) and the Korea/US-IT "suspect unconditional" concern.
**Change:** carry both adjusted and unadjusted VIR/STF through the snapshot and let the artifact present/toggle. Data reportedly exists; mostly a parser/schema plumbing task with outsized goodwill.

### 9. Thematic & factor lookthrough (AI winners/losers, momentum, etc.)
**Said by:** RW & DM (AI disruption exposure was the wish-I-knew-sooner); MB (momentum-factor underweight surfaced by Axioma — "shouldn't be extremely underweight a factor rewarded historically").
**Change:** allow holdings to carry **thematic/factor tags** so the agent can roll up cross-cutting exposures that don't map to a single ACID (AI-winner/loser, factor tilts). Higher effort (tagging + possibly ingesting Axioma factor data) but it targets exactly the "risk that built up I didn't see" category.

---

## Tier 3 — Board/IC prep & memory (confirms the strategic reframings)

### 10. The thesis/rationale ledger answers "rationale lives in people's heads"
**Said by:** MB, Q12 — "trying to get better at documenting the rationale for stock-level trades… I don't make a record of these conversations, so they 'live in people's heads.'" RW catches up via "historical positioning, historical peer reviews." MB, Q9: wants "longer-term changes in fund-level positioning… how portfolios evolved over time."
**Implication:** this is the strongest external validation of **ledger-as-product**. Prioritize making memory real (recall loop) and capturing cited position rationale + falsification conditions that **evolve over multiple quarters**, not a once-written field.

### 11. Attribution analytics for board prep
**Said by:** RW, Q9 — excess-return decomposition by *decision point* (asset allocation vs subadviser vs internal strategies, like the annual post-mortems); DM, Q9 — allocation-to-style-box and selection-within-style-box (Brinson-style); DM, Q8 — open to **AI generating monthly performance-review slides** (but Fund Spotlights stay human).
**Change:** add deterministic attribution (allocation vs selection by style box; decision-point excess-return decomposition) with LLM narration. A bounded, clearly-scoped automation target with explicit PM buy-in.

### 12. Performance-number reconciliation — point the audit machinery here
**Said by:** all three, Q8 — the #1 board-prep wish is **100% accuracy on performance numbers** (MB: "wouldn't trust the team to have 100% accuracy"; DM: sleeve numbers & measurement periods "took a long time due to inaccuracies").
**Implication / reframe:** the agent was engineered for *audit* (citation tokens, source hashing, replay gating). For monthly VIR commentary that rigor is partly pre-investment — **but for board-prep number reconciliation it is exactly the product.** A citation-backed, reconciled performance/sleeve-number output may be the agent's fastest path to undeniable usefulness.

### 13. Tracking-error ex-ante vs ex-post reconciliation
**Said by:** MB & DM — "ex-ante TE has been greatly understating ex-post TE"; DM disagrees with Axioma's ex-ante TE but watches it; both "told to increase TE."
**Change:** track and flag the ex-ante/ex-post TE divergence over time. Skeptical PMs still want it surfaced and reconciled, not asserted.

---

## How this updates the structural thinking

- **It confirms salience-first over completeness.** Every entry question is cross-sectional and attention-allocating — *"what changed most," "what am I under-exposed to," "what concentration did I miss."* None of the PMs asked for a full brief on every fund. The exception/triage reframing is the right one.
- **It confirms ledger-as-product** (Q12: rationale lives in heads) and **decision-support over pure questioning** (Q13 wishes are all "show me / tell me what I'm missing," not "ask me a question").
- **It adds a theme the prior docs missed:** *data accuracy is the highest-value, most-trusted use of the agent's audit DNA.* Board-prep reconciliation may outrank monthly VIR narrative as the first place to ship real value.
- **It demands epistemic humility in the signal layer — but with a fixed anchor.** STF is the anchor by mandate, so the agent *does* assert a single favorable direction (STF-based). Humility applies to two things layered on top: (a) carry raw VIR as context and flag VIR-vs-STF divergence, since divergence is where overrides arise; and (b) flag named cells where the underlying unconditional is distrusted (Korea, US IT), downgrading triggers there to "watch" rather than "challenge." The anchor is settled; the caveats around it are not.
- **Cadence flexibility is a free win.** Intra-month on-demand runs are explicitly wanted and the runtime already supports `as_of_date` / `ad_hoc` — framing, not plumbing.

### Suggested immediate moves
1. **Tier 1 #1–#3** (dual-anchor ranks, override suppression, move-attribution) — all reuse existing data and fix the most-cited workflow steps.
2. **Tier 2 #7** (intra-month "what bubbled up") and **#8** (MER toggle) — low effort, directly requested, high goodwill.
3. **Tier 3 #12** (performance-number reconciliation) — the audit machinery's highest-leverage target; pick one board book and prove it.
