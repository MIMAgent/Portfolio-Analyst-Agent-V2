import { useState } from 'react'
import { header, challenges, evidence } from './lib/data.js'
import { pct, signedPct, fmtDate } from './lib/format.js'
import Overview from './pages/Overview.jsx'
import ChallengeBrief from './pages/ChallengeBrief.jsx'
import SignalsDecomp from './pages/SignalsDecomp.jsx'
import AgentMemory from './pages/AgentMemory.jsx'

const summary = evidence.risk_and_attribution?.summary || {}
const mtd = evidence.risk_and_attribution?.return_attribution_mtd || {}
const icQueued = (evidence.top_challenges || []).length

const FUND_GROUPS = [
  {
    label: 'Equity',
    funds: [
      { name: header.fund || 'MStar US Equity', count: challenges.length, active: true },
      { name: 'MStar Global Opp', count: 2 },
      { name: 'MStar Intl Equity', count: 0 },
    ],
  },
  {
    label: 'Fixed Income',
    funds: [
      { name: 'Core Plus Bond', count: 1 },
      { name: 'EM Local Debt', count: 0 },
    ],
  },
  {
    label: 'Multi-Asset',
    funds: [
      { name: 'Target Risk Mod', ok: true },
      { name: 'Target Risk Aggr', ok: true },
    ],
  },
]

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'challenge', label: 'Challenge Brief', count: challenges.length },
  { id: 'signals', label: 'Signals & Decomp' },
  { id: 'fof', label: 'Fund of Funds' },
  { id: 'ic', label: 'IC Prep', count: icQueued },
  { id: 'memory', label: 'Agent Memory' },
]

function Placeholder({ name }) {
  return (
    <div className="canvas">
      <div className="panel rise" style={{ textAlign: 'center', padding: '64px 24px' }}>
        <div className="panel-title">{name}</div>
        <div className="panel-sub eyebrow" style={{ marginTop: 8 }}>Next phase — this surface is scoped but not yet built.</div>
      </div>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('overview')

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
              <button key={f.name} className={`nav-item${f.active ? ' active' : ''}`} disabled={!f.active}>
                <span className="nav-name">{f.name}</span>
                {f.ok ? (
                  <span className="nav-badge ok">✓</span>
                ) : (
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
            <button className="btn">IC Prep ↗</button>
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
        {tab === 'challenge' && <ChallengeBrief />}
        {tab === 'signals' && <SignalsDecomp />}
        {tab === 'fof' && <Placeholder name="Fund of Funds" />}
        {tab === 'ic' && <Placeholder name="IC Prep" />}
        {tab === 'memory' && <AgentMemory />}
      </main>
    </div>
  )
}
