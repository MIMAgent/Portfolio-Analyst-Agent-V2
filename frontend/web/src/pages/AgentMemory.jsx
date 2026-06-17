/*
 * Agent Memory — forward-looking demo surface.
 * All data on this page is ILLUSTRATIVE: it shows the system at maturity, once
 * months of reviews, PM responses, and outcomes have accumulated. It is the
 * "why this compounds" story for the showcase, not live data.
 */
import { signedNum, signedPct } from '../lib/format.js'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']

// Industrials challenge, tracked across 6 months (illustrative).
const STF = [-0.021, -0.028, -0.033, -0.041, -0.040, -0.039]
const ALGO = [-1.4, -1.9, -2.3, -2.7, -2.85, -2.92]

const TIMELINE = [
  { m: 'Jan 2026', status: 'raised', tone: 'warn', title: 'Challenge first raised', body: 'Industrials +2.9pt overweight flagged off-signal (STF & algo both underweight).' },
  { m: 'Feb 2026', status: 'watch', tone: 'ink', title: 'PM response logged', body: '"Monitoring — sleeve-driven, not a deliberate sector call." No thesis filed.' },
  { m: 'Mar 2026', status: 'watch', tone: 'ink', title: 'Placeholder thesis recorded', body: '"Maintain baseline thesis tracking." Agent marks it a monitoring note, not conviction.' },
  { m: 'Apr 2026', status: 'escalated', tone: 'warn', title: 'PM committed to act', body: 'PM: "will document the sector case at next IC." Agent stores the commitment.' },
  { m: 'May 2026', status: 'unresolved', tone: 'neg', title: 'Commitment not met', body: 'No thesis filed. Sector research now >12 months stale. Agent escalates persistence.' },
  { m: 'Jun 2026', status: 'unresolved · 6 mo', tone: 'neg', title: 'Still open — now with a cost', body: 'Placeholder unchanged. Position cost −124bps MTD. Divergence has widened every month.' },
]

const LEDGER = [
  { d: '2026-04-06', type: 'PM rationale', tone: 'ink', text: '"Added IT & Financials per the algo." — the algo has since inverted to underweight on both.' },
  { d: '2026-04-06', type: 'Thesis', tone: 'warn', text: 'Industrials thesis = placeholder; never upgraded. 71 days stale and counting.' },
  { d: '2026-04-22', type: 'Commitment', tone: 'neg', text: 'PM agreed to document the sector case at IC. Not filed as of Jun review.' },
  { d: '2026-05-31', type: 'Research', tone: 'warn', text: 'Matched sector deck dated May 2025 — 12+ months old, neutral stance only.' },
  { d: '2026-06-15', type: 'Outcome', tone: 'neg', text: 'Flagged position underperformed: industry factor drag −1.24% MTD, −124bps from this bucket.' },
]

const SCORE = [
  { k: 'Challenges tracked', v: '23', sub: 'across 6 monthly reviews', tone: 'ink' },
  { k: 'Off-signal hit rate', v: '61%', sub: '14 of 23 later underperformed', tone: 'pos' },
  { k: 'Avg lead time', v: '1.8 mo', sub: 'flagged before the drag showed', tone: 'pos' },
  { k: 'Open > 3 months', v: '6', sub: 'unresolved, now persistence-ranked', tone: 'neg' },
  { k: 'Avg time to document', v: '2.4 mo', sub: 'from raise to written thesis', tone: 'warn' },
]

function Spark() {
  const W = 520, H = 200, m = { t: 16, r: 16, b: 26, l: 36 }
  const iw = W - m.l - m.r, ih = H - m.t - m.b
  const norm = (arr) => {
    const lo = Math.min(...arr), hi = Math.max(...arr)
    return arr.map((v) => (hi === lo ? 0.5 : (v - lo) / (hi - lo)))
  }
  const line = (arr) => {
    const n = norm(arr)
    return arr.map((_, i) => `${m.l + (i / (arr.length - 1)) * iw},${m.t + (1 - n[i]) * ih}`).join(' ')
  }
  const pts = (arr, color) => {
    const n = norm(arr)
    return arr.map((v, i) => (
      <circle key={i} cx={m.l + (i / (arr.length - 1)) * iw} cy={m.t + (1 - n[i]) * ih} r="3.5" fill={color} />
    ))
  }
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Signal trajectory">
      {MONTHS.map((mo, i) => (
        <text key={mo} x={m.l + (i / (MONTHS.length - 1)) * iw} y={H - 8} textAnchor="middle" fontSize="10" fill="#86868f" fontFamily="JetBrains Mono">{mo}</text>
      ))}
      <polyline points={line(STF)} fill="none" stroke="#c0392b" strokeWidth="2" />
      <polyline points={line(ALGO)} fill="none" stroke="#2a4bd7" strokeWidth="2" strokeDasharray="4 3" />
      {pts(STF, '#c0392b')}
      {pts(ALGO, '#2a4bd7')}
      <text x={m.l} y={m.t - 4} fontSize="10" fill="#c0392b" fontFamily="Hanken Grotesk" fontWeight="600">STF deteriorating →</text>
    </svg>
  )
}

export default function AgentMemory() {
  return (
    <div className="canvas">
      <div className="demo-banner">
        <span className="demo-tag">Illustrative</span>
        <span>Forward-looking view of the system at maturity — how a single challenge compounds once months of reviews, PM responses, and outcomes accumulate. Not live data.</span>
      </div>

      <section className="kpi-row" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {SCORE.map((s, i) => (
          <div className={`kpi tone-${s.tone} rise d${i + 1}`} key={s.k}>
            <div className="kpi-label eyebrow">{s.k}</div>
            <div className={`kpi-val ${s.tone === 'neg' ? 'neg' : s.tone === 'pos' ? 'pos' : s.tone === 'warn' ? 'warn' : ''}`}>{s.v}</div>
            <div className="kpi-sub">{s.sub}</div>
          </div>
        ))}
      </section>

      <div className="grid-2">
        <div className="panel rise d4">
          <div className="panel-head">
            <div className="panel-title">Industrials — challenge persistence</div>
            <div className="panel-sub eyebrow">Same challenge, tracked across 6 monthly reviews</div>
          </div>
          <div className="timeline">
            {TIMELINE.map((t) => (
              <div className="tl-row" key={t.m}>
                <div className={`tl-dot tl-${t.tone}`} />
                <div className="tl-body">
                  <div className="tl-head">
                    <span className="tl-month">{t.m}</span>
                    <span className={`tag ${t.tone === 'neg' ? 'neg' : t.tone === 'warn' ? 'warn' : 'ink'}`}>{t.status}</span>
                  </div>
                  <div className="tl-title">{t.title}</div>
                  <div className="tl-text">{t.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rise d5" style={{ display: 'grid', gap: 16, alignContent: 'start' }}>
          <div className="panel">
            <div className="panel-head">
              <div className="panel-title">Signal trajectory</div>
              <div className="panel-sub eyebrow">STF (solid) & algo (dashed) — divergence widening, not converging</div>
            </div>
            <Spark />
            <div className="spark-legend">
              <span><i className="lg-stf" /> STF {signedNum(STF[5], 3)} <small>(from {signedNum(STF[0], 3)})</small></span>
              <span><i className="lg-algo" /> Algo {signedNum(ALGO[5], 2)}pt <small>(from {signedNum(ALGO[0], 2)})</small></span>
            </div>
          </div>

          <div className="panel cross-fund">
            <div className="eyebrow" style={{ color: 'var(--brand-2)', marginBottom: 8 }}>Cross-fund pattern detected</div>
            <p>The same small-cap momentum tilt now appears in <b>3 of 5 equity funds</b> (US Equity, Global Opp, Intl Equity) — an aggregate <b>+5.4pt house-level style bet</b> that no single fund review would surface. Only visible with breadth across the book.</p>
          </div>
        </div>
      </div>

      <div className="panel rise d6 section-gap">
        <div className="panel-head">
          <div className="panel-title">What the agent remembers</div>
          <div className="panel-sub eyebrow">Accumulated context that sharpens every subsequent review</div>
        </div>
        <div className="ledger">
          {LEDGER.map((l, i) => (
            <div className="ledger-row" key={i}>
              <span className="ledger-date mono">{l.d}</span>
              <span className={`tag ${l.tone === 'neg' ? 'neg' : l.tone === 'warn' ? 'warn' : 'ink'}`}>{l.type}</span>
              <span className="ledger-text">{l.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
