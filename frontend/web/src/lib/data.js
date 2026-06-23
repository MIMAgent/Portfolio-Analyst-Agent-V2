import evidence from '../data/evidence.json'
import packet from '../data/packet.json'
import review from '../data/review.json'
import manifest from '../data/manifest.json'
import stfHistory from '../data/stfHistory.json'
import factorRisk from '../data/factorRisk.json'
import { normKey } from './format.js'

export { evidence, packet, review, manifest, factorRisk }

export const header = evidence.header || {}
export const benchmark = header.benchmark || ''

const positions = packet.material_positions || []

// A position is "off-signal" when positioning fully diverges from the model
// (both VIR and algo lean the opposite way). partially_aligned is a softer
// tension and is not counted here.
export const isOffSignal = (p) => p?.signal_alignment === 'diverging'

const riskSummary = evidence.risk_and_attribution?.summary || {}
const mtd = evidence.risk_and_attribution?.return_attribution_mtd || {}
const offSignalCount = positions.filter(isOffSignal).length
const topChallenges = evidence.top_challenges || []
const criticalCount = topChallenges.filter((c) => c.priority === 'high').length

export const kpis = [
  {
    key: 'te', label: 'Tracking Error', tone: 'ink',
    value: riskSummary.active_predicted_risk_pct, unit: '%',
    sub: 'predicted active risk',
  },
  {
    key: 'share', label: 'Active Share', tone: 'pos',
    value: riskSummary.active_share_pct, unit: '%',
    sub: 'vs benchmark',
  },
  {
    key: 'mtd', label: 'MTD Active Return', tone: 'neg',
    value: mtd.active_period_return, unit: '%', signed: true,
    sub: 'underweight drag dominant',
  },
  {
    key: 'off', label: 'Off-Signal Positions', tone: 'warn',
    value: offSignalCount, unit: '',
    sub: `of ${positions.length} material positions`,
  },
  {
    key: 'ic', label: 'IC Items Queued', tone: 'ink',
    value: topChallenges.length, unit: '',
    sub: `${criticalCount} critical`,
  },
]

// Executive summary bullets — prefer key_insights (label + the "so-what"),
// fall back to dashboard_highlights.
export const execBullets = (() => {
  const insights = review.key_insights || []
  if (insights.length) {
    return insights.map((it) => ({
      label: it.label,
      text: it.why_it_matters || it.insight,
      neg: /off-signal|drag|deteriorat|worsen|risk|stale|no live|no matched/i.test(
        `${it.label} ${it.insight || ''}`,
      ),
    }))
  }
  return (review.dashboard_highlights || []).map((h) => ({ label: h.label, text: h.highlight, neg: false }))
})()

// Some sector labels repeat across regional cells (e.g. "Information Technology"
// for US / EU / EM / AU). Region-qualify those so each row is distinct.
const REGION = { US: 'US', EU: 'Europe', EM: 'EM', AU: 'Asia', GL: 'Global', DM: 'DM' }
const labelCounts = positions.reduce((acc, p) => {
  acc[p.label] = (acc[p.label] || 0) + 1
  return acc
}, {})
function displayName(p) {
  if ((labelCounts[p.label] || 0) > 1) {
    const prefix = String(p.acid || '').trim().split(/\s+/)[0]
    return `${REGION[prefix] || prefix} ${p.label}`.trim()
  }
  return p.label
}

// All material positions mapped for the active-weight chart (filtered + sorted
// in the component so the bars can be sliced by exposure category).
export const chartPositions = positions
  .filter((p) => p.label && p.active_weight !== undefined)
  .map((p) => ({
    name: displayName(p),
    label: p.label,
    acid: p.acid,
    category: p.category || 'Other',
    active: Number(p.active_weight || 0),
    vir: Number(p.vir_now ?? NaN),
    off: isOffSignal(p),
  }))

// Filter chips for the bar chart — friendly labels over the raw category field.
const CATEGORY_LABEL = {
  'Eq Sector': 'Sector',
  Country: 'Country',
  'Eq Size / Style': 'Size / Style',
  Region: 'Region',
  'Cash / Other': 'Cash',
}
export const positionCategories = [
  { key: 'All', label: 'All' },
  ...Array.from(new Set(chartPositions.map((p) => p.category)))
    .map((c) => ({ key: c, label: CATEGORY_LABEL[c] || c, count: chartPositions.filter((p) => p.category === c).length }))
    .sort((a, b) => b.count - a.count),
]

// Material positions that carry an STF decomposition — for the model-challenge view.
export const decompPositions = positions
  .filter((p) => p.decomposition_values && Math.abs(Number(p.active_weight || 0)) >= 0.8)
  .map((p) => ({
    name: displayName(p),
    acid: p.acid,
    label: p.label,
    values: p.decomposition_values,
    dominant: p.decomposition_driver,
    assessment: p.decomposition_assessment,
    vir: Number(p.vir_now ?? NaN),
    virDelta: Number(p.vir_delta_mom ?? NaN),
    algo: Number(p.algo_active_weight ?? NaN),
    active: Number(p.active_weight || 0),
    off: isOffSignal(p),
  }))
  .sort((a, b) => Math.abs(b.active) - Math.abs(a.active))

// Scatter points — active weight (x) vs STF (y).
export const scatterPoints = positions
  .filter((p) => p.active_weight !== undefined && p.vir_now !== undefined && p.vir_now !== null)
  .map((p) => ({
    label: displayName(p),
    category: p.category || 'Other',
    x: Number(p.active_weight || 0),
    y: Number(p.vir_now || 0),
    off: isOffSignal(p),
  }))

// -------- STF rank within its own universe --------
// STF is a valuation/attractiveness signal, not a sizing call, so we rank it
// against peers in the SAME universe rather than the whole model: US sectors vs
// US sectors, ex-US sectors vs ex-US sectors, US styles vs US styles, etc.
// Universe = region bucket (US vs ex-US) x category group. Rank 1 = most
// attractive (highest STF). The bundled material positions contain the full US
// sector (11) and US style (9) sets, so these ranks are exact for US exposures.
const regionPrefix = (acid) => String(acid || '').trim().split(/\s+/)[0]
const regionBucket = (acid) => (regionPrefix(acid) === 'US' ? 'US' : 'ex-US')
const CATEGORY_GROUP = {
  'Eq Sector': 'sectors',
  'Eq Size / Style': 'styles',
  Country: 'countries',
  Region: 'regions',
}
const stfUniverseKey = (p) => {
  const g = CATEGORY_GROUP[p.category]
  return g ? `${regionBucket(p.acid)} ${g}` : null
}

const stfRankByAcid = (() => {
  const universes = {}
  for (const p of positions) {
    if (p.vir_now === undefined || p.vir_now === null) continue
    const key = stfUniverseKey(p)
    if (!key) continue
    ;(universes[key] = universes[key] || []).push(p)
  }
  const map = new Map()
  for (const [label, arr] of Object.entries(universes)) {
    arr.sort((a, b) => Number(b.vir_now) - Number(a.vir_now))
    arr.forEach((p, i) => map.set(p.acid, { rank: i + 1, size: arr.length, universe: label }))
  }
  return map
})()

// -------- STF percentile within its own history (time-series, not peers) --------
// Where the current STF sits in the exposure's own trailing range (stfHistory.json,
// 12 monthly points). Higher percentile = more attractive vs its own past. This is
// orthogonal to the peer rank above: a position can be best-in-universe yet near its
// own 1-yr low (a regime-depressed winner).
const stfHistByAcid = (() => {
  const map = new Map()
  const acids = stfHistory.acids || {}
  const window = stfHistory.window_months
  for (const [acid, series] of Object.entries(acids)) {
    const vals = (series || []).map(Number).filter((v) => !Number.isNaN(v))
    if (vals.length < 2) continue
    // The series' last point is the current snapshot; rank it against its prior
    // history (excludes the current point — no self-counting, no rounding skew).
    const current = vals[vals.length - 1]
    const prior = vals.slice(0, -1)
    const pctile = prior.filter((v) => v < current).length / prior.length
    map.set(acid, { pctile, window, low: Math.min(...vals), high: Math.max(...vals), n: vals.length })
  }
  return map
})()

// -------- Challenge Brief view model --------
const challengeByLabel = new Map(topChallenges.map((c) => [normKey(c.label), c]))
const supportByAcid = new Map(
  (evidence.challenge_support_packets || []).map((s) => [s.acid, s]),
)
const marketByAcid = new Map(
  (evidence.challenge_market_context || []).map((m) => [m.acid, m]),
)

// Normalize a market-context row (the two sources use slightly different keys).
function normMarketRow(r) {
  return {
    headline: r.headline,
    narrative: r.narrative,
    readthrough: r.fundamental_readthrough,
    source: r.source_label || r.source,
    date: r.source_date || r.published_at,
    url: r.source_url || r.citation || r.url,
  }
}

function deriveDescriptor(item, top, signal) {
  if (item.descriptor) return item.descriptor
  const cat = top?.category || ''
  const tension = signal?.signal_alignment === 'aligned' ? 'signal aligned' : 'both model layers diverging'
  return [cat, tension].filter(Boolean).join('  |  ')
}

function deriveAction(item, top) {
  if (item.recommended_action) return item.recommended_action.toUpperCase()
  if (top?.priority === 'high') return 'REVIEW AT IC'
  return 'DOCUMENT OR RESIZE'
}

export const challenges = (review.challenge_brief || []).map((item, i) => {
  const top = challengeByLabel.get(normKey(item.label)) || {}
  const support = supportByAcid.get(top.acid) || {}
  const market = marketByAcid.get(top.acid) || {}
  const stf = stfRankByAcid.get(top.acid) || {}
  const stfHist = stfHistByAcid.get(top.acid) || {}
  const marketRowsRaw = Array.isArray(market.rows) && market.rows.length
    ? market.rows
    : (Array.isArray(support.exact_external_market_context) ? support.exact_external_market_context : [])
  const signal = support.exact_vir_algo_decomp_explanation || {}
  const holdings = Array.isArray(support.exact_holdings_causing_it)
    ? support.exact_holdings_causing_it
    : []
  return {
    id: top.challenge_id || `c${i}`,
    label: item.label,
    category: top.category || '',
    priority: top.priority || 'medium',
    score: top.challenge_score,
    descriptor: deriveDescriptor(item, top, signal),
    action: deriveAction(item, top),
    headline: item.challenge_headline,
    activeWeight: signal.active_weight,
    vir: signal.vir_now,
    stfRank: stf.rank,
    stfUniverseSize: stf.size,
    stfUniverse: stf.universe,
    stfHistPctile: stfHist.pctile,
    stfHistWindow: stfHist.window,
    stfHistLow: stfHist.low,
    stfHistHigh: stfHist.high,
    algo: signal.algo_active_weight,
    signalAlignment: signal.signal_alignment,
    thesis: item.thesis_under_pressure,
    positioning: item.positioning_tension,
    modelTension: item.model_signal_tension,
    relativeSignal: item.relative_signal_readthrough,
    decomp: item.vir_decomposition_readthrough,
    decompExact: item.exact_vir_algo_decomp_explanation,
    market: item.market_context_readthrough,
    risk: item.measured_risk_readthrough,
    riskExact: item.exact_risk_contribution,
    internalResearch: item.exact_internal_research_excerpt,
    externalContext: item.exact_external_market_context,
    bull: item.bull_case,
    bear: item.bear_case,
    devils: item.devils_advocate,
    changeMind: item.what_would_change_my_mind,
    fork: item.pm_decision_fork,
    question: item.primary_pm_question,
    evidenceNext: item.evidence_needed_next,
    confidence: item.confidence,
    sourceQuality: item.source_quality,
    holdings,
    holdingsProse: item.exact_holdings_causing_it,
    marketRows: marketRowsRaw.map(normMarketRow).filter((r) => r.headline || r.narrative),
    marketQuery: market.query_used,
    marketStatus: market.context_status,
  }
})

export const challengeCategories = ['All', ...Array.from(new Set(challenges.map((c) => c.category).filter(Boolean)))]

// -------- Fund of Funds: sleeve look-through --------
// Each material position carries a source_breakdown: the underlying securities
// and, per security, which subadvisor sleeves hold it. One pseudo-source is the
// benchmark itself ("...Market TR USD") — exclude it from sleeve attribution.
const isBenchSource = (s) => /tr usd|market tr/i.test(s.source_name || '')

// Friendly sleeve names (the raw feed uses long internal mandate codes).
const SLEEVE_NAMES = {
  'MS US EQUITY CLEARBRIDGE': 'ClearBridge',
  'MS US EQ SYSTEMATIC LARGE': 'Systematic Large',
  'MSTAR USEQ OPPORTUNISTIC': 'Opportunistic',
  'MSTAR USEQ COMPLETION': 'Completion',
  'MS US EQUITY MFS': 'MFS',
  'MS US EQ SYSTEMATIC SMID': 'Systematic SMID',
  'MS US EQUITY WASATCH': 'Wasatch',
  'SPDR Portfolio S&P 600 Sm Cap ETF': 'SPDR S&P 600',
  'SPDR® S&P 600 Small Cap Value ETF': 'SPDR S&P 600 Value',
}
export const sleeveLabel = (n) => SLEEVE_NAMES[n] || n

// Per-exposure look-through: for every material position, aggregate the sleeve
// portfolio weight that builds it, plus the underlying securities and the
// sleeves holding each.
export const lookthrough = positions
  .filter((p) => (p.source_breakdown?.securities || []).length)
  .map((p) => {
    const sleeveMap = {}
    const securities = (p.source_breakdown.securities || []).map((sec) => {
      const sleeves = []
      for (const s of sec.sources || []) {
        if (isBenchSource(s)) continue
        const w = Number(s.portfolio_weight) || 0
        if (w === 0) continue
        sleeves.push({ name: sleeveLabel(s.source_name), weight: w })
        sleeveMap[s.source_name] = (sleeveMap[s.source_name] || 0) + w
      }
      return {
        name: sec.security_name,
        port: Number(sec.portfolio_weight) || 0,
        bench: Number(sec.benchmark_weight) || 0,
        active: Number(sec.active_weight) || 0,
        sleeves: sleeves.sort((a, b) => b.weight - a.weight),
      }
    })
    const sleeves = Object.entries(sleeveMap)
      .map(([name, weight]) => ({ name: sleeveLabel(name), weight }))
      .sort((a, b) => b.weight - a.weight)
    const portTotal = sleeves.reduce((s, x) => s + x.weight, 0)
    return {
      acid: p.acid,
      name: displayName(p),
      label: p.label,
      category: p.category || 'Other',
      active: Number(p.active_weight) || 0,
      port: Number(p.portfolio_weight) || 0,
      bench: Number(p.benchmark_weight) || 0,
      securityCount: p.source_breakdown.security_count,
      sleeves,
      portTotal,
      securities: securities.sort((a, b) => Math.abs(b.active) - Math.abs(a.active)),
      off: isOffSignal(p),
    }
  })
  .sort((a, b) => Math.abs(b.active) - Math.abs(a.active))

// Fund-level sleeve roster across the material *sector* exposures. Sectors are
// mutually exclusive by security, so summing their sleeve weights gives a clean
// composition of the equity book by subadvisor.
export const sleeveRoster = (() => {
  const map = {}
  for (const p of positions.filter((p) => p.category === 'Eq Sector')) {
    for (const sec of p.source_breakdown?.securities || []) {
      for (const s of sec.sources || []) {
        if (isBenchSource(s)) continue
        const w = Number(s.portfolio_weight) || 0
        if (w === 0) continue
        map[s.source_name] = (map[s.source_name] || 0) + w
      }
    }
  }
  const total = Object.values(map).reduce((a, b) => a + b, 0) || 1
  return Object.entries(map)
    .map(([name, weight]) => ({ name: sleeveLabel(name), weight, share: (weight / total) * 100 }))
    .sort((a, b) => b.weight - a.weight)
})()

// Distinct sleeve names (roster order) — used to assign stable chart colors.
export const sleeveOrder = sleeveRoster.map((s) => s.name)

export const lookthroughCategories = [
  'All',
  ...Array.from(new Set(lookthrough.map((p) => p.category).filter(Boolean))),
]

// -------- IC Prep: per-challenge decision sheet --------
// Joins the challenge view model with the PM question and the recommended
// follow-up, both keyed by exposure label.
const pmqByLabel = new Map((review.pm_questions || []).map((q) => [normKey(q.label), q]))
const followByLabel = new Map((review.follow_up || []).map((f) => [normKey(f.label), f]))

export const icPackets = challenges.map((c) => {
  const q = pmqByLabel.get(normKey(c.label)) || {}
  const f = followByLabel.get(normKey(c.label)) || {}
  return {
    ...c,
    pmQuestion: q.question || c.question,
    whyNow: q.why_now,
    followAction: f.action,
    followWhy: f.why_it_matters,
  }
})
