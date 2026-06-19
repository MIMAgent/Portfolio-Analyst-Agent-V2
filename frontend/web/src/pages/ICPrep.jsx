/*
 * IC Prep — the "Open IC Prep" destination. A printable per-challenge decision
 * sheet built from REAL run data: the challenge view model joined with the PM
 * question (review.pm_questions) and recommended follow-up (review.follow_up).
 * One sheet per item; each is a self-contained page the PM can sign off at IC.
 */
import { useEffect } from 'react'
import { icPackets, header } from '../lib/data.js'
import { signedPts, stfPct, fmtDate, isNum, ordinal } from '../lib/format.js'

const PRIORITY_LABEL = { high: 'Urgent — decide at IC', medium: 'Watch', low: 'Monitor' }

function ForkOptions({ text }) {
  if (!text) return <p className="ic-muted">No decision fork on record.</p>
  const parts = text.split(/(?=Option [A-Z]:)/g).map((s) => s.trim()).filter(Boolean)
  if (parts.length <= 1) {
    return (
      <label className="ic-option">
        <span className="ic-check" />
        <span>{text}</span>
      </label>
    )
  }
  return (
    <div className="ic-options">
      {parts.map((p, i) => {
        const m = p.match(/^Option ([A-Z]):\s*([\s\S]*)$/)
        return (
          <label className="ic-option" key={i}>
            <span className="ic-check" />
            <span><b>{m ? `Option ${m[1]}` : 'Option'}</b> — {m ? m[2] : p}</span>
          </label>
        )
      })}
    </div>
  )
}

function Sheet({ c, index }) {
  const owPos = Number(c.activeWeight) >= 0
  return (
    <article className="ic-sheet" id={`ic-${c.id}`}>
      <div className={`memo-accent ${c.priority}`} />
      <header className="ic-head">
        <div>
          <div className="ic-eyebrow eyebrow">
            IC Decision Sheet · Item {index + 1} of {icPackets.length}
          </div>
          <h2 className="ic-title">{c.label}</h2>
          <div className="ic-sub">{header.fund} · {c.category} · snapshot {fmtDate(header.snapshot_date)}</div>
        </div>
        <div className="ic-head-right">
          {isNum(c.activeWeight) && (
            <div className="memo-weight">
              <div className={`memo-weight-val ${owPos ? 'pos' : 'neg'}`}>{signedPts(c.activeWeight, 2)}</div>
              <div className="memo-weight-label eyebrow">pts active</div>
            </div>
          )}
          <span className={`tag ${c.priority === 'high' ? 'neg' : c.priority === 'medium' ? 'warn' : 'pos'}`}>
            {PRIORITY_LABEL[c.priority] || c.priority}
          </span>
        </div>
      </header>

      {c.headline && <p className="ic-headline">{c.headline}</p>}

      <div className="ic-metrics">
        <div className="ic-metric"><span className="eyebrow">Active weight</span><b className={owPos ? 'pos' : 'neg'}>{signedPts(c.activeWeight, 2)}</b></div>
        <div className="ic-metric">
          <span className="eyebrow">STF signal</span>
          <b className={Number(c.vir) < 0 ? 'neg' : 'pos'}>{stfPct(c.vir)}</b>
          {isNum(c.stfRank) && <span className="ic-metric-sub">#{c.stfRank}/{c.stfUniverseSize} {c.stfUniverse}</span>}
          {isNum(c.stfHistPctile) && <span className="ic-metric-sub">{c.stfHistWindow === 12 ? '1-yr' : `${c.stfHistWindow}mo`} STF: {ordinal(Math.round(c.stfHistPctile * 100))} pct</span>}
        </div>
        <div className="ic-metric"><span className="eyebrow">Algo active</span><b className={Number(c.algo) < 0 ? 'neg' : 'pos'}>{isNum(c.algo) ? signedPts(c.algo, 2) : '—'}</b></div>
        <div className="ic-metric"><span className="eyebrow">Alignment</span><b>{c.signalAlignment ? c.signalAlignment.replace(/_/g, ' ') : '—'}</b></div>
      </div>

      <div className="ic-cols">
        {c.positioning && (
          <div className="ic-block">
            <div className="memo-section-title eyebrow">Positioning tension</div>
            <p>{c.positioning}</p>
          </div>
        )}
        {c.modelTension && (
          <div className="ic-block">
            <div className="memo-section-title eyebrow">Model signal tension</div>
            <p>{c.modelTension}</p>
          </div>
        )}
      </div>

      {c.pmQuestion && (
        <div className="ic-question">
          <div className="eyebrow">Question for the PM</div>
          <p>{c.pmQuestion}</p>
          {c.whyNow && <div className="ic-whynow"><span className="eyebrow">Why now</span> {c.whyNow}</div>}
        </div>
      )}

      <div className="ic-block ic-decision">
        <div className="memo-section-title eyebrow">Decision — select one</div>
        <ForkOptions text={c.fork} />
      </div>

      {(c.followAction || c.evidenceNext) && (
        <div className="ic-cols">
          {c.followAction && (
            <div className="ic-block">
              <div className="memo-section-title eyebrow">Recommended follow-up</div>
              <p>{c.followAction}</p>
              {c.followWhy && <p className="ic-muted" style={{ marginTop: 6 }}>{c.followWhy}</p>}
            </div>
          )}
          {c.evidenceNext && (
            <div className="ic-block">
              <div className="memo-section-title eyebrow">Evidence needed next</div>
              <p>{c.evidenceNext}</p>
            </div>
          )}
        </div>
      )}

      <footer className="ic-signoff">
        <div className="ic-sign"><span className="ic-line" /><span className="eyebrow">PM decision</span></div>
        <div className="ic-sign"><span className="ic-line" /><span className="eyebrow">Date</span></div>
        <div className="ic-sign-meta">{header.pm_names?.join(' · ')} · run {header.review_run_id}</div>
      </footer>
    </article>
  )
}

export default function ICPrep({ focusId }) {
  useEffect(() => {
    if (!focusId) return
    const el = document.getElementById(`ic-${focusId}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [focusId])

  return (
    <div className="canvas">
      <div className="ic-bar">
        <div>
          <div className="panel-title">IC Prep — {icPackets.length} items for the {fmtDate(header.review_date)} committee</div>
          <div className="panel-sub eyebrow">{header.fund} · benchmark {header.benchmark} · each sheet is print-ready</div>
        </div>
        <button className="btn primary" onClick={() => window.print()}>Print / Export ↗</button>
      </div>

      <ol className="ic-agenda">
        {icPackets.map((c, i) => (
          <li key={c.id}>
            <a href={`#ic-${c.id}`}>
              <span className={`ic-agenda-num ${c.priority}`}>{i + 1}</span>
              <span className="ic-agenda-label">{c.label}</span>
              <span className="ic-agenda-meta">{c.category}</span>
              {isNum(c.activeWeight) && <span className={`ic-agenda-w ${Number(c.activeWeight) >= 0 ? 'pos' : 'neg'}`}>{signedPts(c.activeWeight, 2)}</span>}
            </a>
          </li>
        ))}
      </ol>

      {icPackets.map((c, i) => <Sheet c={c} index={i} key={c.id} />)}
    </div>
  )
}
