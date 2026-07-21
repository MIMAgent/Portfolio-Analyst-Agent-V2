/*
 * Signals & Decomp — a fund-specific model diagnostic.
 * All decomposition values come from the selected fund's review packet.
 * Confidence is based only on observable signal concentration; the UI does not
 * assert a market-regime narrative that is absent from the fund evidence.
 */
import { useMemo, useState } from 'react'
import { decompPositions } from '../lib/data.js'
import { stfPct, signedStfPct } from '../lib/format.js'

const LABELS = {
  growth: 'Growth',
  yield: 'Yield',
  inflation: 'Inflation',
  currency_usd: 'Currency (USD)',
  valuation_adjustment_top_down: 'Valuation — top-down',
  valuation_adjustment_bottom_up: 'Valuation — bottom-up',
  valuation_adjustment_combined: 'Valuation — combined',
}
const ORDER = ['growth', 'yield', 'inflation', 'currency_usd', 'valuation_adjustment_top_down', 'valuation_adjustment_bottom_up']

export default function SignalsDecomp() {
  const list = decompPositions
  const [acid, setAcid] = useState(list[0]?.acid)
  const sel = useMemo(() => list.find((p) => p.acid === acid) || list[0], [acid, list])

  const comps = ORDER
    .filter((k) => sel?.values?.[k] !== undefined)
    .map((k) => ({ k, label: LABELS[k], value: Number(sel.values[k]) }))
  const maxAbs = Math.max(...comps.map((c) => Math.abs(c.value)), 0.01)
  const totalAbs = comps.reduce((sum, c) => sum + Math.abs(c.value), 0) || 1
  const dominant = comps.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0]
  const dominantShare = Math.round((Math.abs(dominant?.value || 0) / totalAbs) * 100)
  const concentrated = dominantShare >= 50
  const modelDir = sel?.vir < 0 ? 'underweight' : 'overweight'

  return (
    <div className="canvas">
      <div className="demo-banner">
        <span className="demo-tag">Live fund data</span>
        <span>The decomposition and concentration diagnostic come from the selected fund's latest STF review packet.</span>
      </div>

      <div className="regime">
        <div className="regime-l">
          <div className="eyebrow" style={{ color: 'var(--brand-2)' }}>Model diagnostic</div>
          <div className="regime-name">Evidence-led signal review</div>
        </div>
        <p className="regime-read">This view does not assume the same market regime across funds. It highlights the live signal components and flags when one driver accounts for most of the model read.</p>
      </div>

      <div className="cb-toolbar" style={{ marginTop: 18 }}>
        <div className="chips">
          {list.slice(0, 8).map((p) => (
            <button key={p.acid} className={`chip${p.acid === sel?.acid ? ' active' : ''}`} onClick={() => setAcid(p.acid)}>{p.name}</button>
          ))}
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head">
            <div className="panel-title">STF decomposition — {sel?.name}</div>
            <div className="panel-sub eyebrow">Live components · selected fund</div>
          </div>
          <div className="decomp">
            {comps.map((c) => {
              const width = (Math.abs(c.value) / maxAbs) * 50
              const positive = c.value > 0
              const isDominant = c.k === dominant?.k
              return (
                <div className={`decomp-row${isDominant ? ' dom' : ''}`} key={c.k}>
                  <div className="decomp-name">{c.label}{isDominant && <span className="dom-tag">dominant</span>}</div>
                  <div className="bar-track">
                    <div className="bar-axis" />
                    <div className={`bar-fill ${positive ? 'pos' : 'neg'}`} style={positive ? { left: '50%', width: `${width}%` } : { left: `${50 - width}%`, width: `${width}%` }} />
                  </div>
                  <div className={`decomp-val ${positive ? 'pos' : 'neg'}`}>{signedStfPct(c.value)}</div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="panel" style={{ borderTop: `3px solid ${concentrated ? 'var(--warn)' : 'var(--pos)'}` }}>
          <div className="panel-head">
            <div className="panel-title">Signal concentration verdict</div>
            <div className="panel-sub eyebrow">How broad is the model read?</div>
          </div>

          <div className="verdict">
            <div className={`verdict-badge ${concentrated ? 'warn' : 'pos'}`}>{concentrated ? 'Concentrated — review' : 'Broad-based signal'}</div>
            <p className="verdict-body">
              The model reads <b>{modelDir}</b> (STF {stfPct(sel?.vir)}{Number.isNaN(sel?.virDelta) ? '' : `, ${signedStfPct(sel?.virDelta)} MoM`}).
              The largest component, <b>{dominant?.label}</b>, represents <b>{dominantShare}%</b> of absolute component magnitude.
              {concentrated
                ? ' Treat the headline signal with care because its direction depends heavily on one driver.'
                : ' The signal is distributed across multiple drivers, reducing single-component dependency.'}
            </p>
          </div>

          <div className="reliability-list">
            <div className="eyebrow" style={{ marginBottom: 8 }}>Components by absolute magnitude</div>
            {comps.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).map((c) => (
              <div className="rel-row" key={c.k}>
                <span className="rel-dot rel-neutral" />
                <span className="rel-name">{c.label}</span>
                <span className="rel-why">{signedStfPct(c.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel section-gap">
        <div className="panel-head">
          <div className="panel-title">What would reduce confidence in the model read</div>
          <div className="panel-sub eyebrow">Fund-specific review checks</div>
        </div>
        <div className="trigger-grid">
          <div className="trigger"><div className="trigger-h">Single-driver concentration</div><p>A dominant component can make the headline STF sensitive to one assumption or data revision.</p></div>
          <div className="trigger"><div className="trigger-h">Signal-position disagreement</div><p>A large gap between STF direction and the live portfolio weight warrants explicit PM review.</p></div>
          <div className="trigger"><div className="trigger-h">Stale model snapshot</div><p>A widening gap between the signal snapshot and review date can reduce relevance in fast-moving markets.</p></div>
          <div className="trigger"><div className="trigger-h">Missing corroborating evidence</div><p>Market or research claims should only change confidence when they are present in the selected fund's evidence packet.</p></div>
        </div>
      </div>
    </div>
  )
}
