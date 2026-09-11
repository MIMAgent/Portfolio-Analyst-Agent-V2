// House View — the cross-sleeve read.
//
// Every other surface in this app is scoped to ONE fund. This module is the only
// one that reads all sleeves at once, because the thing it exists to surface is
// invisible from inside any single fund review: exposures the house holds through
// more than one sleeve, where the sleeves disagree with each other.
//
// The central fact, verified against the data and re-asserted at runtime below:
// STF and the algo's active weight are IDENTICAL across sleeves for every shared
// exposure. The model speaks with one voice to all three books. So a cross-sleeve
// difference is never a signal disagreement — it is always a positioning decision
// somebody made. That is what makes these items committee material rather than
// data-quality noise.
//
// HONESTY CONSTRAINT: the packets carry no AUM or fund size, so there is no way to
// compute a true house-level exposure. Everything here is an UNWEIGHTED per-sleeve
// comparison of active weights. Nothing in this module should ever be presented as
// "the house owns X%" — it cannot be derived from the data available.

import { FUND_DATASETS } from '../data/funds/index.js'
import fundAum from '../data/fundAum.json'

const FUND_IDS = Object.keys(FUND_DATASETS)

// Sleeve size turns a per-sleeve comparison into a capital-weighted one. A 2 pt
// overweight in the $1.9bn sleeve is not the same bet as 2 pt in the $450m sleeve,
// and without this the page implied they were.
//
// CAVEAT that must stay visible: each sleeve's active weight is measured against
// ITS OWN benchmark (US Market / Global ex-US / Global). Summing dollars across
// sleeves therefore gives a capital-weighted ACTIVE TILT, not a position against a
// single blended benchmark. It is directionally right and materially useful; it is
// not a benchmark-exact aggregate.
const AUM_M = Object.fromEntries(
  FUND_IDS.map((id) => [id, Number(fundAum.funds?.[id]?.aumMillions) || 0]),
)
const TOTAL_AUM_M = Object.values(AUM_M).reduce((a, b) => a + b, 0)
const hasAum = TOTAL_AUM_M > 0
// active_weight is in percentage points, AUM in $m -> $m of active exposure
const dollarsOf = (fundId, activePts) =>
  hasAum && activePts !== null ? (AUM_M[fundId] * activePts) / 100 : null

const positionsOf = (ds) => (ds.packet?.material_positions || []).filter((p) => p.acid)
const challengesOf = (ds) => (ds.evidence?.top_challenges || []).filter((t) => t.acid)

export const houseFunds = FUND_IDS.map((id) => {
  const ds = FUND_DATASETS[id]
  return {
    id,
    navName: ds.navName,
    fundName: ds.fundName,
    short: ds.navName.replace('Global Opportunistic', 'Global Opp'),
    positions: positionsOf(ds).length,
    challenges: challengesOf(ds).length,
    benchmark: ds.evidence?.header?.benchmark || '',
    aumM: AUM_M[id] || 0,
    share: TOTAL_AUM_M ? (AUM_M[id] || 0) / TOTAL_AUM_M : 0,
  }
})

// acid -> { fundId -> position }
const byAcid = (() => {
  const map = new Map()
  for (const id of FUND_IDS) {
    for (const p of positionsOf(FUND_DATASETS[id])) {
      if (!map.has(p.acid)) map.set(p.acid, {})
      map.get(p.acid)[id] = p
    }
  }
  return map
})()

// acid -> { fundId -> challenge }
const challengeByAcid = (() => {
  const map = new Map()
  for (const id of FUND_IDS) {
    for (const t of challengesOf(FUND_DATASETS[id])) {
      if (!map.has(t.acid)) map.set(t.acid, {})
      map.get(t.acid)[id] = t
    }
  }
  return map
})()

const num = (v) => (v === null || v === undefined || Number.isNaN(Number(v)) ? null : Number(v))
const EPS = 1e-9

// A shared exposure is one held in two or more sleeves.
const shared = [...byAcid.entries()].filter(([, funds]) => Object.keys(funds).length >= 2)

// -------- Is the model really speaking with one voice? Verify, don't assume. -----
// If a future data change breaks this, the framing below stops being true, so it is
// measured rather than asserted.
function agreementOn(field) {
  let identical = 0
  let differing = 0
  for (const [, funds] of shared) {
    const vals = Object.values(funds).map((p) => num(p[field])).filter((v) => v !== null)
    if (vals.length < 2) continue
    if (Math.max(...vals) - Math.min(...vals) > EPS) differing += 1
    else identical += 1
  }
  return { identical, differing }
}

const stfAgreement = agreementOn('vir_now')
const algoAgreement = agreementOn('algo_active_weight')

export const houseMeta = {
  sleeves: houseFunds.length,
  snapshotDate: FUND_DATASETS[FUND_IDS[0]]?.evidence?.header?.snapshot_date || '',
  reviewDate: FUND_DATASETS[FUND_IDS[0]]?.evidence?.header?.review_date || '',
  distinctExposures: byAcid.size,
  sharedExposures: shared.length,
  stfIdentical: stfAgreement.identical,
  stfDiffering: stfAgreement.differing,
  algoIdentical: algoAgreement.identical,
  algoDiffering: algoAgreement.differing,
  // true only while the model genuinely says the same thing to every sleeve
  oneVoice: stfAgreement.differing === 0 && algoAgreement.differing === 0,
  hasAum,
  totalAumM: TOTAL_AUM_M,
  aumAsOf: fundAum.asOf || '',
  aumApproximate: fundAum.precision === 'approximate',
  // Coverage is NOT confirmed as the full equity book, so this view calls itself a
  // three-sleeve aggregate. Do not relabel without confirming.
  coverageConfirmed: false,
}

function baseRow(acid, funds) {
  const any = Object.values(funds)[0]
  const sleeves = Object.entries(funds).map(([fundId, p]) => ({
    fundId,
    short: houseFunds.find((f) => f.id === fundId)?.short || fundId,
    active: num(p.active_weight),
    portfolio: num(p.portfolio_weight),
    benchmark: num(p.benchmark_weight),
    alignment: p.signal_alignment,
    challenged: Boolean(challengeByAcid.get(acid)?.[fundId]),
    dollars: dollarsOf(fundId, num(p.active_weight)),
  })).filter((s) => s.active !== null)
  // Net vs gross is the whole point of having AUM: gross is the active risk the
  // house is actually running on this exposure, net is what it ends up with after
  // the sleeves fight each other. The gap between them is capital at work against itself.
  const dollars = sleeves.map((s) => s.dollars).filter((d) => d !== null)
  const netUsd = dollars.length ? dollars.reduce((a, b) => a + b, 0) : null
  const grossUsd = dollars.length ? dollars.reduce((a, b) => a + Math.abs(b), 0) : null
  const offsetPct = grossUsd ? 1 - Math.abs(netUsd) / grossUsd : null
  return {
    acid,
    label: any.label,
    category: any.category,
    stf: num(any.vir_now),
    algo: num(any.algo_active_weight),
    algoView: any.algo_view,
    driver: any.decomposition_driver,
    sleeves,
    netUsd,
    grossUsd,
    offsetPct,
    cancelledUsd: grossUsd !== null && netUsd !== null ? grossUsd - Math.abs(netUsd) : null,
  }
}

// -------- 1. Opposing bets: sleeves on opposite sides of the same exposure ------
// Two sleeves paying active risk in opposite directions on an identical signal.
// At the house level this is risk spent to cancel out — and no single fund review
// can see it, because each sleeve's own book looks internally coherent.
const MATERIAL_PT = 0.25

export const opposingBets = shared
  .map(([acid, funds]) => baseRow(acid, funds))
  .filter((r) => {
    const vals = r.sleeves.map((s) => s.active)
    return Math.max(...vals) > MATERIAL_PT && Math.min(...vals) < -MATERIAL_PT
  })
  .map((r) => {
    const vals = r.sleeves.map((s) => s.active)
    const longs = r.sleeves.filter((s) => s.active > MATERIAL_PT)
    const shorts = r.sleeves.filter((s) => s.active < -MATERIAL_PT)
    // the two sleeves furthest apart — the concrete pair worth naming
    const long = [...longs].sort((a, b) => b.active - a.active)[0]
    const short = [...shorts].sort((a, b) => a.active - b.active)[0]
    return {
      ...r,
      spread: Math.max(...vals) - Math.min(...vals),
      longs,
      shorts,
      widest: { long, short },
      challengedIn: r.sleeves.filter((s) => s.challenged).map((s) => s.short),
    }
  })
  // Rank by capital working against itself, not by pts spread — pts systematically
  // overweights the smallest sleeve, which is exactly the distortion AUM removes.
  .sort((a, b) => (b.cancelledUsd ?? 0) - (a.cancelledUsd ?? 0) || b.spread - a.spread)

// Only ONE category may be summed. material_positions mixes Eq Sector (54),
// Country (44), Eq Size / Style (9) and Region (4) — overlapping partitions of the
// same equity universe, so a stock sits in a sector AND a style AND a country.
// Adding offsetting capital across them would double- and triple-count. Sectors
// partition the universe exactly once, so the sector total is additive and is the
// only cross-exposure figure this module will report.
export const sectorOffset = (() => {
  const rows = opposingBets.filter((r) => r.category === 'Eq Sector')
  return {
    usd: rows.reduce((a, r) => a + (r.cancelledUsd || 0), 0),
    count: rows.length,
    grossUsd: rows.reduce((a, r) => a + (r.grossUsd || 0), 0),
  }
})()

// -------- 2. Conviction gaps: same call, very different size --------------------
// Same exposure, same direction, identical STF and identical algo view — but one
// sleeve holds a multiple of the other's active weight. Not a contradiction; a
// question about who is right on sizing, which is exactly a committee question.
const MIN_SIZE_PT = 0.5
const MIN_RATIO = 1.75

export const convictionGaps = shared
  .map(([acid, funds]) => baseRow(acid, funds))
  .map((r) => {
    const vals = r.sleeves.map((s) => s.active)
    const sameDirection = vals.every((v) => v > 0) || vals.every((v) => v < 0)
    const mags = vals.map(Math.abs)
    const lo = Math.min(...mags)
    const hi = Math.max(...mags)
    const sorted = [...r.sleeves].sort((a, b) => Math.abs(b.active) - Math.abs(a.active))
    return {
      ...r,
      sameDirection,
      lo,
      hi,
      ratio: lo > 0 ? hi / lo : Infinity,
      biggest: sorted[0],
      smallest: sorted[sorted.length - 1],
      challengedIn: r.sleeves.filter((s) => s.challenged).map((s) => s.short),
    }
  })
  .filter((r) => r.sameDirection && r.lo >= MIN_SIZE_PT && r.ratio >= MIN_RATIO && Number.isFinite(r.ratio))
  .sort((a, b) => Math.abs(b.grossUsd ?? 0) - Math.abs(a.grossUsd ?? 0) || (b.hi - b.lo) - (a.hi - a.lo))

// -------- 3. Challenged in more than one sleeve --------------------------------
// The agent independently raised the SAME exposure in two separate fund reviews,
// and neither review can mention the other.
export const crossChallenges = [...challengeByAcid.entries()]
  .filter(([, funds]) => Object.keys(funds).length >= 2)
  .map(([acid, funds]) => {
    const row = baseRow(acid, byAcid.get(acid) || {})
    return {
      ...row,
      inFunds: Object.keys(funds),
      headlines: Object.entries(funds).map(([fundId, t]) => ({
        fundId,
        short: houseFunds.find((f) => f.id === fundId)?.short || fundId,
        label: t.label,
        priority: t.priority,
        score: num(t.challenge_score),
      })),
    }
  })
  .sort((a, b) => b.inFunds.length - a.inFunds.length)

// -------- 4. Label echoes: same THEME, different regional cell ------------------
// "Industrials" is challenged in two sleeves — but as US ID EQ in one and EU ID EQ
// in the other. That is a thematic echo, NOT the same exposure, and conflating the
// two would be exactly the kind of overstatement that costs the tool its credibility.
export const labelEchoes = (() => {
  const byLabel = new Map()
  for (const [acid, funds] of challengeByAcid.entries()) {
    const row = byAcid.get(acid)
    const any = row ? Object.values(row)[0] : null
    const label = any?.label
    if (!label) continue
    if (!byLabel.has(label)) byLabel.set(label, [])
    for (const fundId of Object.keys(funds)) {
      byLabel.get(label).push({ acid, fundId, short: houseFunds.find((f) => f.id === fundId)?.short || fundId })
    }
  }
  return [...byLabel.entries()]
    .filter(([, rows]) => new Set(rows.map((r) => r.acid)).size >= 2)
    .map(([label, rows]) => ({ label, rows }))
})()

// -------- 5. One research note underwriting several sleeves ---------------------
export const sharedResearch = (() => {
  const docs = new Map()
  for (const id of FUND_IDS) {
    for (const p of positionsOf(FUND_DATASETS[id])) {
      const doc = p.sharepoint_research_path
      if (!doc) continue
      if (!docs.has(doc)) docs.set(doc, { doc, funds: new Set(), positions: 0 })
      const entry = docs.get(doc)
      entry.funds.add(id)
      entry.positions += 1
    }
  }
  return [...docs.values()]
    .filter((d) => d.funds.size >= 2)
    .map((d) => ({ ...d, funds: [...d.funds], fundCount: d.funds.size }))
    .sort((a, b) => b.positions - a.positions)
})()
