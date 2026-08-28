import signalHistory from '../signalHistory.json'

import usEvidence from './us-equity/evidence.json'
import usPacket from './us-equity/packet.json'
import usReview from './us-equity/review.json'
import usManifest from './us-equity/manifest.json'
import usFactorRisk from './us-equity/factorRisk.json'

import internationalEvidence from './international-equity/evidence.json'
import internationalPacket from './international-equity/packet.json'
import internationalReview from './international-equity/review.json'
import internationalManifest from './international-equity/manifest.json'
import internationalFactorRisk from './international-equity/factorRisk.json'

import goeEvidence from './goe/evidence.json'
import goePacket from './goe/packet.json'
import goeReview from './goe/review.json'
import goeManifest from './goe/manifest.json'
import goeFactorRisk from './goe/factorRisk.json'

function stfHistoryFor(fundName) {
  const fund = signalHistory.funds?.[fundName] || {}
  const acids = Object.fromEntries(
    Object.entries(fund.acids || {}).map(([acid, payload]) => [
      acid,
      (payload.series || [])
        .map((row) => row.vir_stf)
        .filter((value) => value !== null && value !== undefined && Number.isFinite(Number(value))),
    ]),
  )
  return {
    window_months: signalHistory.dates?.length || 0,
    as_of: signalHistory.dateRange?.end || '',
    acids,
  }
}

export const FUND_DATASETS = {
  'us-equity': {
    id: 'us-equity',
    navName: 'US Equity',
    fundName: 'MStar US Equity',
    evidence: usEvidence,
    packet: usPacket,
    review: usReview,
    manifest: usManifest,
    factorRisk: usFactorRisk,
    stfHistory: stfHistoryFor('MStar US Equity'),
  },
  'international-equity': {
    id: 'international-equity',
    navName: 'International Equity',
    fundName: 'MStar International Equity',
    evidence: internationalEvidence,
    packet: internationalPacket,
    review: internationalReview,
    manifest: internationalManifest,
    factorRisk: internationalFactorRisk,
    stfHistory: stfHistoryFor('MStar International Equity'),
  },
  goe: {
    id: 'goe',
    navName: 'Global Opportunistic',
    fundName: 'MStar Global Opportunistic Equity',
    evidence: goeEvidence,
    packet: goePacket,
    review: goeReview,
    manifest: goeManifest,
    factorRisk: goeFactorRisk,
    stfHistory: stfHistoryFor('MStar Global Opportunistic Equity'),
  },
}

export const FUND_OPTIONS = Object.values(FUND_DATASETS)
export const DEFAULT_FUND_ID = 'us-equity'

export function resolveFundDataset(fundId) {
  return FUND_DATASETS[fundId] || FUND_DATASETS[DEFAULT_FUND_ID]
}
