import { useState } from 'react'
import { activeFundId, fundOptions, header, challenges, evidence } from './lib/data.js'
import { pct, signedPct, fmtDate } from './lib/format.js'
import Overview from './pages/Overview.jsx'
import FactorRisk from './pages/FactorRisk.jsx'
import ChallengeBrief from './pages/ChallengeBrief.jsx'
import SignalsDecomp from './pages/SignalsDecomp.jsx'
import FundOfFunds from './pages/FundOfFunds.jsx'
import ICPrep from './pages/ICPrep.jsx'
import AgentMemory from './pages/AgentMemory.jsx'

const summary = evidence.risk_and_attribution?.summary || {}
const mtd = evidence.risk_and_attribution?.return_attribution_mtd || {}
const icQueued = (evidence.top_challenges || []).length

const FUND_GROUPS = [
  {
    label: 'Equity',
    funds: fundOptions.map((fund) => ({ ...fund, active: fund.id === activeFundId })),
  },
  {
    label: 'Fixed Income',
    funds: [
      { name: 'Alts' },
      { name: 'Total Return' },
      { name: 'Municipal Bond' },
      { name: 'Multisector Bond' },
      { name: 'Defensive Bond' },
    ],
  },
  {
    label: 'Multi-Asset',
    funds: [
      { name: 'Global Income' },
    ],
  },
]

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'factorrisk', label: 'Factor Risk' },
  { id: 'challenge', label: 'Challenge Brief', count: challenges.length },
  { id: 'signals', label: 'Signals & Decomp' },
  { id: 'fof', label: 'Fund of Funds' },
  { id: 'ic', label: 'IC Prep', count: icQueued },
  { id: 'memory', label: 'Agent Memory' },
]

export default function App() {
  const [tab, setTab] = useState('overview')
  const [icFocus, setIcFocus] = useState(null)

  const openIC = (id) => {
    setIcFocus(id || null)
    setTab('ic')
  }

  const selectFund = (fundId) => {
    if (!fundId || fundId === activeFundId) return
    const url = new URL(window.location.href)
    if (fundId === 'us-equity') url.searchParams.delete('fund')
    else url.searchParams.set('fund', fundId)
    window.location.assign(url.toString())
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><span className="brand-dot" /> PM Analyst Agent</div>
          <div className="brand-sub eyebrow">Portfolio Review</div>
          <div className="brand-sub eyebrow" style={{ marginTop: 8, color: 'var(--ink-3)' }}>
            {fmtDate(header.snapshot_date)} — {fmtDate(header.review_date)}
          </div>
        </div>

        {FUND_GROUPS.map((g) => (
          <div className="nav-group" key={g.label}>
            <div className="nav-group-label eyebrow">{g.label}</div>
            {g.funds.map((f) => (
              <button
                key={f.name}
                className={`nav-item${f.active ? ' active' : ''}`}
                disabled={!f.id}
                aria-pressed={f.id ? f.active : undefined}
                onClick={() => selectFund(f.id)}
              >
                <span className="nav-name">{f.name}</span>
                {Number.isFinite(f.count) && (
                  <span className={`nav-badge${f.count > 0 ? ' alert' : ''}`}>{f.count}</span>
                )}
              </button>
            ))}
          </div>
        ))}

        <div className="sidebar-foot">
          <div className="eyebrow" style={{ color: 'var(--ink-3)' }}>Bedrock · Sonnet 4.6</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="tb-fund">{header.fund}</div>
          <div className="tb-sep" />
          <div className="tb-stat">Snapshot <b>{fmtDate(header.snapshot_date)}</b></div>
          <div className="tb-stat">TE <b>{pct(summary.active_predicted_risk_pct, 2)}</b></div>
          <div className="tb-stat">MTD Active <b className={Number(mtd.active_period_return) < 0 ? 'neg' : 'pos'}>{signedPct(mtd.active_period_return, 2)}</b></div>
          <div className="tb-stat">Active Share <b>{pct(summary.active_share_pct, 1)}</b></div>
          <div className="tb-actions">
            <button className="btn" onClick={() => openIC()}>IC Prep ↗</button>
            <button className="btn primary">Run Review ↗</button>
          </div>
        </header>

        <nav className="tabs">
          {TABS.map((t) => (
            <button key={t.id} className={`tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
              {t.label}
              {t.count ? <span className="tab-count">{t.count}</span> : null}
            </button>
          ))}
        </nav>

        {tab === 'overview' && <Overview />}
        {tab === 'factorrisk' && <FactorRisk />}
        {tab === 'challenge' && <ChallengeBrief onOpenIC={openIC} />}
        {tab === 'signals' && <SignalsDecomp />}
        {tab === 'fof' && <FundOfFunds />}
        {tab === 'ic' && <ICPrep focusId={icFocus} />}
        {tab === 'memory' && <AgentMemory />}
      </main>
    </div>
  )
}
