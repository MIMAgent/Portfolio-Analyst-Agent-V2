/*
 * Fund of Funds — sleeve look-through.
 * REAL data: every weight is derived from packet.material_positions[].
 * source_breakdown — the underlying securities and which subadvisor sleeves
 * hold each. Answers "which sleeves build this exposure, and is an active bet
 * intentional or a structural byproduct of sleeve construction?"
 */
import { useMemo, useState } from 'react'
import { lookthrough, lookthroughCategories, sleeveRoster, sleeveOrder } from '../lib/data.js'
import { pct, signedPts, signedPct } from '../lib/format.js'

// Categorical palette for sleeves — restrained ink-blues + warm neutrals,
// assigned by roster order so a sleeve keeps its color across every view.
const PALETTE = ['#2a4bd7', '#213047', '#5a7bd4', '#a86a18', '#1f7a52', '#7a6cae', '#9a9388', '#c0392b', '#3f8ca0', '#b08968']
const colorFor = (name) => {
  const i = sleeveOrder.indexOf(name)
  return PALETTE[(i < 0 ? sleeveOrder.length : i) % PALETTE.length]
}

function StackedBar({ parts, total }) {
  if (!total) return null
  return (
    <div className="fof-stack">
      {parts.map((p) => {
        const w = (p.weight / total) * 100
        if (w < 0.4) return null
        return (
          <div
            key={p.name}
            className="fof-seg"
            style={{ width: `${w}%`, background: colorFor(p.name) }}
            title={`${p.name} — ${p.weight.toFixed(2)}%`}
          />
        )
      })}
    </div>
  )
}

export default function FundOfFunds() {
  const [cat, setCat] = useState('All')
  const list = useMemo(
    () => (cat === 'All' ? lookthrough : lookthrough.filter((p) => p.category === cat)),
    [cat],
  )
  const [acid, setAcid] = useState(lookthrough[0]?.acid)
  const sel = useMemo(() => {
    const inList = list.find((p) => p.acid === acid)
    return inList || list[0]
  }, [acid, list])

  const rosterTotal = sleeveRoster.reduce((s, x) => s + x.weight, 0)
  const owPos = (sel?.active || 0) >= 0
  // source_breakdown lists the top holdings (not all N), so the sleeve weights
  // cover only part of the full portfolio weight; surface the gap honestly.
  const covered = sel?.portTotal || 0
  const residual = Math.max(0, (sel?.port || 0) - covered)
  const listed = sel?.securities.length || 0
  const barMax = Math.max(...(sel?.sleeves || []).map((s) => s.weight), residual, 0.01)

  return (
    <div className="canvas">
      <div className="demo-banner">
        <span className="demo-tag">Real data · sleeve look-through</span>
        <span>Every exposure is decomposed to the <b>subadvisor sleeves</b> that build it. Use it to ask whether an active bet is an <b>intentional</b> sector view or a <b>structural byproduct</b> of how the sleeves aggregate.</span>
      </div>

      <div className="panel">
        <div className="panel-head panel-head-row">
          <div>
            <div className="panel-title">Sleeve composition of the equity book</div>
            <div className="panel-sub eyebrow">Portfolio weight across material sector exposures · {sleeveRoster.length} sleeves</div>
          </div>
        </div>
        <StackedBar parts={sleeveRoster} total={rosterTotal} />
        <div className="fof-roster">
          {sleeveRoster.map((s) => (
            <div className="fof-roster-row" key={s.name}>
              <span className="fof-swatch" style={{ background: colorFor(s.name) }} />
              <span className="fof-sleeve-name">{s.name}</span>
              <span className="fof-roster-share">{s.share.toFixed(1)}%</span>
              <span className="fof-roster-w">{pct(s.weight, 2)}</span>
            </div>
          ))}
        </div>
        <div className="fof-coverage">Built from each exposure's itemized top holdings; smaller positions aren't sleeve-attributed, so these are coverage-floor weights.</div>
      </div>

      <div className="cb-toolbar" style={{ marginTop: 18 }}>
        <div className="chips">
          {lookthroughCategories.map((c) => (
            <button key={c} className={`chip${cat === c ? ' active' : ''}`} onClick={() => setCat(c)}>{c === 'All' ? 'All exposures' : c}</button>
          ))}
        </div>
      </div>

      <div className="cb-toolbar">
        <div className="chips">
          {list.slice(0, 10).map((p) => (
            <button key={p.acid} className={`chip${p.acid === sel?.acid ? ' active' : ''}`} onClick={() => setAcid(p.acid)}>
              {p.name}<span className={`fof-chip-w ${p.active >= 0 ? 'pos' : 'neg'}`}>{signedPts(p.active, 1)}</span>
            </button>
          ))}
        </div>
      </div>

      {sel && (
        <div className="grid-2">
          <div className="panel" style={{ borderTop: `3px solid ${owPos ? 'var(--pos)' : 'var(--neg)'}` }}>
            <div className="panel-head panel-head-row">
              <div>
                <div className="panel-title">{sel.name}</div>
                <div className="panel-sub eyebrow">{sel.category} · {sel.securityCount} underlying securities</div>
              </div>
              <div className="memo-weight">
                <div className={`memo-weight-val ${owPos ? 'pos' : 'neg'}`}>{signedPts(sel.active, 2)}</div>
                <div className="memo-weight-label eyebrow">pts active</div>
              </div>
            </div>

            <div className="fof-meta">
              <div><span className="eyebrow">Portfolio</span><b>{pct(sel.port, 2)}</b></div>
              <div><span className="eyebrow">Benchmark</span><b>{pct(sel.bench, 2)}</b></div>
              <div><span className="eyebrow">Sleeves holding</span><b>{sel.sleeves.length}</b></div>
            </div>

            <div className="eyebrow" style={{ margin: '6px 0 10px' }}>Which sleeves build this exposure</div>
            <div className="fof-sleevebars">
              {sel.sleeves.map((s) => (
                <div className="fof-sleeve-row" key={s.name}>
                  <span className="fof-swatch" style={{ background: colorFor(s.name) }} />
                  <span className="fof-sleeve-name">{s.name}</span>
                  <div className="fof-bar-track">
                    <div className="fof-bar-fill" style={{ width: `${(s.weight / barMax) * 100}%`, background: colorFor(s.name) }} />
                  </div>
                  <span className="fof-sleeve-w">{pct(s.weight, 2)}</span>
                </div>
              ))}
              {residual >= 0.05 && (
                <div className="fof-sleeve-row fof-residual-row">
                  <span className="fof-swatch" style={{ background: 'var(--line-strong)' }} />
                  <span className="fof-sleeve-name">Other holdings (not itemized)</span>
                  <div className="fof-bar-track">
                    <div className="fof-bar-fill fof-residual" style={{ width: `${(residual / barMax) * 100}%` }} />
                  </div>
                  <span className="fof-sleeve-w">{pct(residual, 2)}</span>
                </div>
              )}
            </div>
            {residual >= 0.05 && (
              <div className="fof-coverage">
                Top {listed} of {sel.securityCount} holdings itemized — sleeves cover {pct(covered, 1)} of the {pct(sel.port, 1)} exposure; the remaining {pct(residual, 1)} sits across {sel.securityCount - listed} smaller names.
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panel-head">
              <div className="panel-title">Underlying securities</div>
              <div className="panel-sub eyebrow">Top names by active weight · sleeves holding each</div>
            </div>
            <div className="fof-sec-list">
              {sel.securities.slice(0, 8).map((sec) => (
                <div className="fof-sec" key={sec.name}>
                  <div className="fof-sec-head">
                    <span className="fof-sec-name">{sec.name}</span>
                    <span className={`fof-sec-active ${sec.active >= 0 ? 'pos' : 'neg'}`}>{signedPct(sec.active, 2)}</span>
                  </div>
                  <div className="fof-sec-sub">
                    <span>Port {pct(sec.port, 2)}</span>
                    <span>Bench {pct(sec.bench, 2)}</span>
                  </div>
                  {sec.sleeves.length > 0 && (
                    <div className="fof-sec-sleeves">
                      {sec.sleeves.map((s) => (
                        <span className="fof-sleeve-chip" key={s.name}>
                          <span className="fof-swatch sm" style={{ background: colorFor(s.name) }} />
                          {s.name} <b>{s.weight.toFixed(2)}</b>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
