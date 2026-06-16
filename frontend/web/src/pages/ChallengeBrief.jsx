import { useMemo, useState } from 'react'
import { challenges, challengeCategories } from '../lib/data.js'
import { signedPts, signedPct, num, pct, isNum, titleCase } from '../lib/format.js'

const PRIORITY_LABEL = { high: 'Urgent', medium: 'Watch', low: 'Monitor' }

function signalTags(c) {
  const tags = []
  if (isNum(c.vir)) tags.push({ t: `VIR ${c.vir < 0 ? 'Underweight' : 'Overweight'}`, cls: c.vir < 0 ? 'neg' : 'pos' })
  if (isNum(c.algo)) tags.push({ t: `Algo ${c.algo < 0 ? 'Underweight' : 'Overweight'}`, cls: c.algo < 0 ? 'neg' : 'pos' })
  tags.push({ t: PRIORITY_LABEL[c.priority] || c.priority, cls: c.priority === 'high' ? 'neg' : c.priority === 'medium' ? 'warn' : 'pos' })
  const conf = (c.confidence || '').match(/^(high|medium|moderate|low)/i)
  if (conf) tags.push({ t: `Confidence: ${titleCase(conf[1])}`, cls: 'ink' })
  return tags
}

function Holdings({ rows }) {
  if (!rows.length) return null
  const top = [...rows]
    .sort((a, b) => Math.abs(Number(b.active_weight || 0)) - Math.abs(Number(a.active_weight || 0)))
    .slice(0, 5)
  return (
    <div className="memo-holdings">
      <div className="holding-row header">
        <span>Security</span><span style={{ textAlign: 'right' }}>Port</span>
        <span style={{ textAlign: 'right' }}>Bench</span><span style={{ textAlign: 'right' }}>Active</span>
      </div>
      {top.map((h) => (
        <div className="holding-row" key={h.security_name}>
          <div className="holding-name">{h.security_name}</div>
          <div className="holding-num">{pct(h.portfolio_weight, 2)}</div>
          <div className="holding-num">{pct(h.benchmark_weight, 2)}</div>
          <div className={`holding-num ${Number(h.active_weight) >= 0 ? 'pos' : 'neg'}`}>{signedPct(h.active_weight, 2)}</div>
        </div>
      ))}
    </div>
  )
}

function DeepMemo({ c, index }) {
  const owPos = Number(c.activeWeight) >= 0
  return (
    <article className="memo rise">
      <div className={`memo-accent ${c.priority}`} />
      <div className="memo-head">
        <div>
          <div className="memo-eyebrow">
            <span className="eyebrow">Challenge {index + 1}</span>
            <span style={{ color: 'var(--line-strong)' }}>·</span>
            <span className="eyebrow" style={{ color: 'var(--ink-3)' }}>{c.category}</span>
          </div>
          <div className="memo-title">{c.label}</div>
          {c.descriptor && <div className="memo-descriptor">{c.descriptor}</div>}
          <div className="tag-row" style={{ marginTop: 12 }}>
            {signalTags(c).map((t) => <span key={t.t} className={`tag ${t.cls}`}>{t.t}</span>)}
          </div>
        </div>
        {isNum(c.activeWeight) && (
          <div className="memo-weight">
            <div className={`memo-weight-val ${owPos ? 'pos' : 'neg'}`}>{signedPts(c.activeWeight, 2)}</div>
            <div className="memo-weight-label eyebrow">pts active</div>
          </div>
        )}
      </div>

      <div className="memo-body">
        {c.thesis && (
          <div className="memo-section">
            <div className="memo-section-title eyebrow">Thesis Under Pressure</div>
            <p>{c.thesis}</p>
          </div>
        )}

        {c.holdings.length > 0 && (
          <div className="memo-section">
            <div className="memo-section-title eyebrow">Holdings Driving the Exposure</div>
            <Holdings rows={c.holdings} />
          </div>
        )}

        {c.decomp && (
          <div className="memo-section">
            <div className="memo-section-title eyebrow">VIR Decomposition</div>
            <p>{c.decomp}</p>
          </div>
        )}

        {(c.bull || c.bear) && (
          <div className="memo-section">
            <div className="memo-section-title eyebrow">Devil's Advocate</div>
            <div className="duo">
              {c.bull && <div className="case bull"><div className="case-label">Bull case</div><p>{c.bull}</p></div>}
              {c.bear && <div className="case bear"><div className="case-label">Bear case</div><p>{c.bear}</p></div>}
            </div>
          </div>
        )}
      </div>

      {c.question && (
        <div className="memo-question">
          <div className="eyebrow">Question for PM</div>
          <p>{c.question}</p>
        </div>
      )}

      <div className="memo-foot">
        {c.action && <span className="tag action">{c.action}</span>}
        {c.confidence && <span className="confidence">{c.confidence}</span>}
        <span className="spacer" />
        <button className="btn">Open IC Prep ↗</button>
      </div>
    </article>
  )
}

function Compact({ c, index }) {
  const owPos = Number(c.activeWeight) >= 0
  return (
    <article className="compact rise">
      <div className={`memo-accent ${c.priority}`} />
      <div className="compact-inner">
        <div className="compact-head">
          <div>
            <div className="compact-title">{c.label}</div>
            <div className="compact-desc">{c.descriptor}</div>
          </div>
          {isNum(c.activeWeight) && <div className={`compact-w ${owPos ? 'pos' : 'neg'}`}>{signedPts(c.activeWeight, 2)}</div>}
        </div>
        <div className="tag-row">
          {signalTags(c).slice(0, 3).map((t) => <span key={t.t} className={`tag ${t.cls}`}>{t.t}</span>)}
          {c.action && <span className="tag action">{c.action}</span>}
        </div>
        {c.question && <div className="compact-q">{c.question}</div>}
      </div>
    </article>
  )
}

export default function ChallengeBrief() {
  const [cat, setCat] = useState('All')
  const [mode, setMode] = useState('deep')

  const filtered = useMemo(
    () => (cat === 'All' ? challenges : challenges.filter((c) => c.category === cat)),
    [cat],
  )

  return (
    <div className="canvas">
      <div className="cb-toolbar">
        <div className="chips">
          {challengeCategories.map((cc) => (
            <button key={cc} className={`chip${cat === cc ? ' active' : ''}`} onClick={() => setCat(cc)}>{cc}</button>
          ))}
        </div>
        <div className="seg">
          <button className={mode === 'deep' ? 'active' : ''} onClick={() => setMode('deep')}>Deep memo</button>
          <button className={mode === 'compact' ? 'active' : ''} onClick={() => setMode('compact')}>Compact cards</button>
        </div>
      </div>

      <div className="cb-banner">
        <span className="flag-icon">⚑</span>
        <div><b>{filtered.length} position{filtered.length === 1 ? '' : 's'} require PM review before the next IC.</b> Each card fuses active weight, the VIR/algo signal stack, prior internal notes, and matched research into a single decision.</div>
      </div>

      {mode === 'deep' ? (
        filtered.map((c, i) => <DeepMemo c={c} index={i} key={c.id} />)
      ) : (
        <div className="compact-grid">
          {filtered.map((c, i) => <Compact c={c} index={i} key={c.id} />)}
        </div>
      )}
    </div>
  )
}
