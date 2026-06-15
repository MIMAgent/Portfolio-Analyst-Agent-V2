# PM Challenge Card Contract V1

Purpose: make first-layer Challenge Brief cards useful for PM review rather than generic status documentation.

## Problem

The previous challenge card could say that positioning and VIR disagreed, but it often failed to explain:

- what thesis is under pressure
- why the disagreement matters now
- whether evidence is model, portfolio, market, or memory based
- what decision the PM actually needs to make
- what evidence would confirm, weaken, or retire the challenge

## Challenge Item Fields

Each `challenge_brief.items[]` row should include these PM-facing fields when evidence supports them:

- `challenge_headline`: one-line PM-facing issue statement.
- `thesis_under_pressure`: the investment thesis or implicit positioning premise being challenged.
- `positioning_tension`: active exposure versus benchmark/portfolio context.
- `model_signal_tension`: VIR/algo direction, rank, momentum, or trigger conflict.
- `vir_decomposition_readthrough`: decomposition driver context when available.
- `market_context_readthrough`: cited earnings, macro, sector, rates, spread, or policy context when available.
- `pm_decision_fork`: concise non-prescriptive choices for review, such as defend, resize, offset, or watch.
- `primary_pm_question`: the main PM review question; avoid generic wording like “is this still intentional?”
- `evidence_needed_next`: specific evidence to check at the next review.
- `source_quality`: short note on evidence quality, for example `model+positioning+market_context`, `model+positioning_only`, or `missing_direct_prior_thesis`.

## Evidence Rules

- Do not use unrelated memory or research notes just because they mention the same broad asset class.
- If prior memory/research does not directly match the ACID, sector, thesis, or explicit tag, say direct prior thesis evidence is missing.
- Market context must come from approved/cited rows.
- Decomposition claims must cite VIR history or trigger evidence.
- Keep fields factual and non-prescriptive. The agent may frame review options, but must not recommend trades or target weights.

## First-Layer Card Goal

The first layer should answer: “What exactly does the PM need to defend, resize, monitor, or explain?”

It should be concise enough for triage and specific enough that a PM recognizes the actual investment issue.
