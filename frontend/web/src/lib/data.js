import evidence from '../data/evidence.json'
import packet from '../data/packet.json'
import review from '../data/review.json'
import manifest from '../data/manifest.json'
import { normKey } from './format.js'

export { evidence, packet, review, manifest }

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

// -------- Challenge Brief view model --------
const challengeByLabel = new Map(topChallenges.map((c) => [normKey(c.label), c]))
const supportByAcid = new Map(
  (evidence.challenge_support_packets || []).map((s) => [s.acid, s]),
)

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
    algo: signal.algo_active_weight,
    signalAlignment: signal.signal_alignment,
    thesis: item.thesis_under_pressure,
    positioning: item.positioning_tension,
    modelTension: item.model_signal_tension,
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
  }
})

export const challengeCategories = ['All', ...Array.from(new Set(challenges.map((c) => c.category).filter(Boolean)))]
