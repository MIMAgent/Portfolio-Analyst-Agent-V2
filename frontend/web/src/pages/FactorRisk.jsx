/* Every number on this tab comes from the selected fund's weekly Axioma report. */
import { factorRisk as fr } from '../lib/data.js'
import { LineChart } from '../components/Charts.jsx'
import { pct, signedPct, signedNum, fmtDate } from '../lib/format.js'

const S = fr.series
const first = S[0]
const last = S[S.length - 1]
const dates = fr.dates
const A = fr.attribution

const fmtR = (v) => `${(v * 100).toFixed(2)}%`

// Direction words are DERIVED. This caption previously asserted tracking error
// "climbed" and bets were "getting bigger" while the chart above it fell — the
// prose was written once against one month's numbers and never moved again.
const dTE = last.activeRisk - first.activeRisk
const dFactor = last.activeFactorRisk - first.activeFactorRisk
const dSpecific = last.activeSpecificRisk - first.activeSpecificRisk
const teVerb = dTE >= 0 ? 'climbed' : 'fell'
const teNoun = dTE >= 0 ? 'rise' : 'decline'
const teSize = dTE >= 0 ? 'getting bigger' : 'getting smaller'
const teLed = Math.abs(dFactor) >= Math.abs(dSpecific) ? 'factor-led' : 'specific-led'
const specVerb = dSpecific >= 0 ? 'grew' : 'fell'
const fmtB = (v) => v.toFixed(2)

// ---- KPI strip ----
const specificShareEnd = (last.activeSpecificRisk ** 2) / (last.activeRisk ** 2)
const KPIS = [
  {
    label: 'Active Tracking Risk',
    val: fmtR(last.activeRisk), tone: 'warn',
    sub: `${signedPct((last.activeRisk - first.activeRisk) * 100)} since ${fmtDate(fr.meta.from)}`,
  },
  {
    label: 'Predicted Beta',
    val: fmtB(last.predictedBeta), tone: 'ink',
    sub: `${signedNum(last.predictedBeta - first.predictedBeta, 2)} over report window`,
  },
  {
    label: 'Active Beta',
    val: signedNum(last.activeBeta, 2), tone: last.activeBeta < 0 ? 'neg' : 'pos',
    sub: `from ${signedNum(first.activeBeta, 2)}`,
  },
  {
    label: 'Active Share',
    val: pct(last.activeShare * 100, 1), tone: 'ink',
    sub: `${fr.meta.holdings} holdings · ${pct(fr.meta.commonAssetsWeight * 100, 0)} overlap`,
  },
  {
    label: 'Specific Risk Share',
    val: pct(specificShareEnd * 100, 0), tone: 'ink',
    sub: 'of active variance — rest is factor bets',
  },
]

// ---- Cumulative return path (portfolio vs benchmark) ----
const cumOf = (key) => {
  let p = 1
  return fr.returns.map((r) => { p *= 1 + (r[key] || 0); return p - 1 })
}
const cumPort = cumOf('portfolio')
const cumBench = cumOf('benchmark')
const rDates = fr.returns.map((r) => r.date)

// ---- Risk-budget concentration (top contributors, ex-covariance) ----
const contribTop = fr.contributors.filter((c) => !c.isCov && c.pctVar > 0.003).slice(0, 9)
const contribMax = Math.max(...contribTop.map((c) => c.pctVar), 0.01)
const GROUP_COLOR = {
  Style: '#2a4bd7',
  Country: '#1f9d6b',
  Industry: '#8a8780',
  Currency: '#d08700',
  Local: '#7857a5',
  Market: '#d08700',
  Other: '#86868f',
}
const SHORT_NAME = {
  'Semiconductors & Semiconductor Equipment': 'Semiconductors',
  'Technology Hardware, Storage & Peripherals': 'Tech Hardware',
  'Internet Software & Services': 'Internet Software',
  'Medium-Term Momentum': 'Momentum',
  'Life Sciences Tools & Services': 'Life Sciences Tools',
}

// ---- Style exposures (current, sorted by |current|) ----
const styles = fr.styleExposure.factors.filter((f) => Math.abs(f.current) >= 0.02)
const styleMax = Math.max(...styles.map((f) => Math.abs(f.current)), 0.05)

// ---- Return attribution rows (cumulative over window) ----
const attribRows = [
  { label: 'Industry factor', v: A.activeIndustry },
  { label: 'Style factor', v: A.activeStyle },
  { label: 'Market factor', v: A.activeMarket },
  { label: 'Stock-specific', v: A.activeSpecific },
]
const attribMax = Math.max(...attribRows.map((r) => Math.abs(r.v)), 0.005)

function Spark({ values, color = '#86868f' }) {
  const W = 64, H = 18
  const lo = Math.min(...values), hi = Math.max(...values)
  const sx = (i) => (i / (values.length - 1)) * W
  const sy = (v) => H - 2 - ((v - lo) / ((hi - lo) || 1)) * (H - 4)
  const d = values.map((v, i) => `${i ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(' ')
  return (
    <svg className="fr-spark" viewBox={`0 0 ${W} ${H}`} width={W} height={H} aria-hidden="true">
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

export default function FactorRisk() {
  return (
    <div className="canvas">
      <div className="demo-banner">
        <span className="demo-tag" style={{ background: 'var(--pos-soft)', color: 'var(--pos)', borderColor: 'var(--pos-line)' }}>Real data · Axioma</span>
        <span>
          Ex-ante factor risk from the <b>{fr.meta.riskModel}</b> model — {fr.meta.portfolio} vs {fr.meta.benchmark},
          {' '}{fmtDate(fr.meta.from)} → {fmtDate(fr.meta.to)} ({fr.meta.periods} periods).
        </span>
      </div>

      <div className="kpi-row" style={{ marginTop: 18 }}>
        {KPIS.map((k) => (
          <div className={`kpi tone-${k.tone}`} key={k.label}>
            <div className="kpi-label eyebrow">{k.label}</div>
            <div className={`kpi-val ${k.tone === 'warn' ? 'warn' : k.tone === 'neg' ? 'neg' : ''}`}>{k.val}</div>
            <div className="kpi-sub">{k.sub}</div>
          </div>
        ))}
      </div>

      {/* HERO — active tracking risk trend */}
      <div className="panel section-gap">
        <div className="panel-head">
          <div className="panel-title">Active tracking risk — trend</div>
          <div className="panel-sub eyebrow">Predicted active risk and its factor / specific split · daily, annualized</div>
        </div>
        <LineChart
          dates={dates}
          height={320}
          yFormat={fmtR}
          series={[
            { label: 'Active tracking risk', color: '#c0392b', values: S.map((d) => d.activeRisk), width: 2.4 },
            { label: 'Factor component', color: '#2a4bd7', values: S.map((d) => d.activeFactorRisk), dash: true },
            { label: 'Specific component', color: '#1f9d6b', values: S.map((d) => d.activeSpecificRisk), dash: true },
          ]}
        />
        <p className="fr-note">
          Tracking error {teVerb} from <b>{fmtR(first.activeRisk)}</b> to <b>{fmtR(last.activeRisk)}</b> — the active bets are {teSize}.
          The {teNoun} is {teLed}; specific risk {specVerb} ({fmtR(first.activeSpecificRisk)} → {fmtR(last.activeSpecificRisk)}).
        </p>
      </div>

      <div className="grid-2 section-gap">
        {/* Cumulative return path — the gap opening up */}
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title">Cumulative return — portfolio vs benchmark</div>
            <div className="panel-sub eyebrow">Compounded daily · selected report window</div>
          </div>
          <LineChart
            dates={rDates}
            height={260}
            includeZero
            yFormat={fmtR}
            series={[
              { label: 'Portfolio', color: '#2a4bd7', values: cumPort, width: 2.4 },
              { label: 'Benchmark', color: '#86868f', values: cumBench, dash: true },
            ]}
          />
          <p className="fr-note">
            The portfolio compounded <b>{fmtR(A.portfolio)}</b> against the benchmark's <b>{fmtR(A.benchmark)}</b>,
            producing <b style={{ color: A.active < 0 ? 'var(--neg)' : 'var(--pos)' }}>{signedPct(A.active * 100)}</b> active return.
            Current active beta is {signedNum(last.activeBeta, 2)}.
          </p>
        </div>

        {/* Risk-budget concentration */}
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title">Where the risk budget sits</div>
            <div className="panel-sub eyebrow">Top contributors · % of active variance (latest)</div>
          </div>
          <div className="fr-conc">
            {contribTop.map((c) => (
              <div className="fr-conc-row" key={c.name}>
                <div className="fr-conc-name" title={c.name}>{SHORT_NAME[c.name] || c.name}</div>
                <div className="fr-conc-track">
                  <div className="fr-conc-fill" style={{ width: `${(c.pctVar / contribMax) * 100}%`, background: GROUP_COLOR[c.group] }} />
                </div>
                <div className="fr-conc-val">{pct(c.pctVar * 100, 1)}</div>
              </div>
            ))}
          </div>
          <div className="fr-conc-legend">
            {Object.entries(GROUP_COLOR).map(([g, col]) => (
              <span key={g}><i style={{ background: col }} />{g}</span>
            ))}
          </div>
          <p className="fr-note">
            The largest modeled contributors are <b>{contribTop.slice(0, 3).map((item) => item.name).join(', ')}</b>.
            Their contribution should be read alongside the selected fund's challenge cards and holdings.
          </p>
        </div>
      </div>

      <div className="grid-2 section-gap">
        {/* Style exposures */}
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title">Active style exposures</div>
            <div className="panel-sub eyebrow">Std-dev vs benchmark (latest) · sparkline = path over window</div>
          </div>
          <div className="bars">
            {styles.map((f) => {
              const pos = f.current > 0
              const w = (Math.abs(f.current) / styleMax) * 50
              return (
                <div className="bar-row fr-style-row" key={f.name}>
                  <div className="bar-name" title={f.name}>{f.name}</div>
                  <div className="bar-track">
                    <div className="bar-axis" />
                    <div className={`bar-fill ${pos ? 'pos' : 'neg'}`} style={pos ? { left: '50%', width: `${w}%` } : { left: `${50 - w}%`, width: `${w}%` }} />
                  </div>
                  <div className={`bar-val ${pos ? 'pos' : 'neg'}`}>{signedNum(f.current, 2)}</div>
                  <Spark values={f.series} color={pos ? '#1f9d6b' : '#c0392b'} />
                </div>
              )
            })}
          </div>
          <p className="fr-note">
            The largest current style exposures are <b>{styles.slice(0, 4).map((item) => item.name).join(', ')}</b>.
            The sparklines show whether each exposure is strengthening or fading during this report window.
          </p>
        </div>

        {/* Return attribution */}
        <div className="panel" style={{ borderTop: `3px solid var(${A.active < 0 ? '--neg' : '--pos'})` }}>
          <div className="panel-head">
            <div className="panel-title">Active return attribution</div>
            <div className="panel-sub eyebrow">Cumulative {fmtDate(A.from)} → {fmtDate(A.to)}</div>
          </div>

          <div className="fr-attrib-head">
            <div className="fr-att-big">
              <div className="eyebrow">Active return</div>
              <div className={`fr-att-num ${A.active < 0 ? 'neg' : 'pos'}`}>{signedPct(A.active * 100)}</div>
            </div>
            <div className="fr-att-vs">
              <div><span>Portfolio</span><b>{signedPct(A.portfolio * 100)}</b></div>
              <div><span>Benchmark</span><b>{signedPct(A.benchmark * 100)}</b></div>
            </div>
          </div>

          <div className="fr-attrib">
            {attribRows.map((r) => {
              const neg = r.v < 0
              const w = (Math.abs(r.v) / attribMax) * 50
              return (
                <div className="fr-conc-row" key={r.label}>
                  <div className="fr-conc-name">{r.label}</div>
                  <div className="bar-track">
                    <div className="bar-axis" />
                    <div className={`bar-fill ${neg ? 'neg' : 'pos'}`} style={neg ? { left: `${50 - w}%`, width: `${w}%` } : { left: '50%', width: `${w}%` }} />
                  </div>
                  <div className={`bar-val ${neg ? 'neg' : 'pos'}`}>{signedPct(r.v * 100)}</div>
                </div>
              )
            })}
          </div>
          <p className="fr-note">
            Factor attribution contributed <b>{signedPct(A.activeFactor * 100)}</b> and stock-specific attribution contributed
            {' '}<b>{signedPct(A.activeSpecific * 100)}</b> over the report window.
          </p>
        </div>
      </div>

      {/* Corroboration callout */}
      <div className="regime section-gap">
        <div className="regime-l">
          <div className="eyebrow" style={{ color: 'var(--brand-2)' }}>Model corroboration</div>
          <div className="regime-name">Risk context for the challenge review</div>
        </div>
        <p className="regime-read">
          The selected fund is running <b>{fmtR(last.activeRisk)}</b> active tracking risk with <b>{pct(last.activeShare * 100, 1)}</b> active share.
          The factor, industry, country, currency, and stock-specific results above provide an independent check on the agent's positioning and STF conclusions.
          Use the Challenge Brief to decide which concentrations should be defended, documented, or resized.
        </p>
      </div>
    </div>
  )
}
