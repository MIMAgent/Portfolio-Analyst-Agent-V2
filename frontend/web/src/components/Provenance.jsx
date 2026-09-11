/*
 * Approved-source market context, in one of three explicit states.
 *
 * Absence used to render as nothing at all, which reads as "not applicable"
 * rather than "we looked and found none". An off-region source used to render
 * as ordinary evidence, which is worse — it looks cited. Both are now stated.
 *
 * State is resolved in lib/provenance.js, from the agent's
 * `market_evidence_status` where a packet carries it and derived from the ACID
 * and source labels where it does not.
 */
import { sourceRegion } from '../lib/provenance.js'

const BADGE = {
  sourced: 'Sourced',
  thin: 'Thin',
  absent: 'No external research',
}

function ClashNote({ source }) {
  const region = sourceRegion(source)
  return (
    <p className="prov-clash">
      This source covers {region || 'another'} markets. It is shown because it was the only
      approved-source match, and it does not speak to this exposure’s market.
    </p>
  )
}

function Searched({ c }) {
  const lenses = c.marketLenses || []
  if (lenses.length) {
    return (
      <div className="prov-lens">
        Searched: {lenses.join(' · ')}
        {c.marketState === 'absent' ? ' — no source matched' : ''}
      </div>
    )
  }
  return c.marketQuery ? <div className="prov-lens">Searched: {c.marketQuery}</div> : null
}

/** Full panel for the Challenge Brief deep memo. */
export function MarketProvenance({ c }) {
  const state = c.marketState || 'absent'
  const rows = c.marketRows || []
  return (
    <div className={`prov prov-${state}`}>
      <div className="prov-head">
        <span className="ctx-label">Approved-source market context</span>
        <span className={`prov-badge ${state}`}>{BADGE[state]}</span>
        {c.marketRegion && <span className="prov-rgn">{c.marketRegion}</span>}
      </div>

      {state === 'absent' ? (
        <p className="prov-absent">{c.marketAbsentCopy}</p>
      ) : (
        <div className="mkt-list">
          {rows.slice(0, 4).map((r, i) => (
            <div className={`mkt-item${r.offRegion ? ' off-region' : ''}`} key={i}>
              <div className="mkt-head">
                <div className="mkt-headline">{r.headline || 'Market context'}</div>
                <div className="mkt-src">
                  {r.source}{r.date ? ` · ${r.date}` : ''}
                  {r.url ? <> · <a href={r.url} target="_blank" rel="noreferrer">source ↗</a></> : ''}
                </div>
              </div>
              {r.offRegion && <ClashNote source={r.source} />}
              {r.narrative && <p className="mkt-narr">{r.narrative}</p>}
            </div>
          ))}
        </div>
      )}

      <Searched c={c} />
    </div>
  )
}

/**
 * One-line evidence basis for the IC sign-off sheet, which shows no market
 * context at all today. A PM signing a decision should see what the cases in
 * front of them are built on.
 */
export function EvidenceBasis({ c }) {
  const state = c.marketState || 'absent'
  const rows = c.marketRows || []
  const offRegion = rows.filter((r) => r.offRegion)
  let body
  if (state === 'absent') {
    body = c.marketAbsentCopy
  } else if (offRegion.length) {
    const names = Array.from(new Set(offRegion.map((r) => r.source))).join(', ')
    body = `The only approved-source research matched for this exposure (${names}) covers ` +
      `${sourceRegion(offRegion[0].source) || 'another'} markets, not ${c.marketRegion}. Treat the ` +
      `external cases below as unsupported.`
  } else {
    const names = Array.from(new Set(rows.map((r) => r.source))).join(', ')
    body = `External cases are built on ${rows.length} approved-source ${rows.length === 1 ? 'finding' : 'findings'} (${names}).`
  }
  return (
    <div className={`ic-block ic-basis ic-basis-${state}`}>
      <div className="memo-section-title eyebrow">
        Evidence basis
        <span className={`prov-badge ${state}`}>{BADGE[state]}</span>
      </div>
      <p>{body}</p>
    </div>
  )
}
