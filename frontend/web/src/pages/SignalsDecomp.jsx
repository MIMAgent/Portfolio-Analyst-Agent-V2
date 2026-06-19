/*
 * Signals & Decomp — "Challenge the model" surface.
 * The STF decomposition values are REAL (from packet.material_positions).
 * The regime read and per-component reliability verdicts are ILLUSTRATIVE —
 * they demonstrate the agent critiquing its own model: which signal components
 * to trust vs discount given the prevailing market regime.
 */
import { useMemo, useState } from 'react'
import { decompPositions } from '../lib/data.js'
import { stfPct, signedStfPct } from '../lib/format.js'

// Illustrative regime read (would be agent-generated from market context).
const REGIME = {
  name: 'Momentum-led · growth-concentrated',
  read: 'Q1 2026 earnings growth (+28.6% blended) is concentrated in the "Magnificent 7" — Communication Services alone at +48.9%. In this regime, top-down valuation has been a losing signal for ~6 months: cheap stays cheap, momentum compounds. The implication for the STF: valuation-driven underweights are lower-confidence than their magnitude implies, while growth/earnings-momentum components are corroborated by the tape.',
}

const RELIABILITY = {
  growth: { v: 'trust', why: 'Earnings momentum confirmed by Q1 beats' },
  yield: { v: 'neutral', why: 'Rate path stable — modest, non-dominant signal' },
  inflation: { v: 'neutral', why: 'Cooling, but not driving leadership' },
  currency_usd: { v: 'trust', why: 'USD trend persistent and corroborated' },
  valuation_adjustment_top_down: { v: 'discount', why: 'Valuation a losing signal ~6mo in a momentum regime' },
  valuation_adjustment_bottom_up: { v: 'trust', why: 'Stock-level value still discriminating' },
  valuation_adjustment_combined: { v: 'discount', why: 'Dominated by the unreliable top-down component' },
}
const LABELS = {
  growth: 'Growth', yield: 'Yield', inflation: 'Inflation', currency_usd: 'Currency (USD)',
  valuation_adjustment_top_down: 'Valuation — top-down', valuation_adjustment_bottom_up: 'Valuation — bottom-up',
  valuation_adjustment_combined: 'Valuation — combined',
}
const ORDER = ['growth', 'yield', 'inflation', 'currency_usd', 'valuation_adjustment_top_down', 'valuation_adjustment_bottom_up']
const RTAG = { trust: 'pos', neutral: 'ink', discount: 'warn' }
const RLABEL = { trust: 'Trust', neutral: 'Neutral', discount: 'Discount' }

export default function SignalsDecomp() {
  const list = decompPositions
  const [acid, setAcid] = useState(list[0]?.acid)
  const sel = useMemo(() => list.find((p) => p.acid === acid) || list[0], [acid, list])

  const comps = ORDER
    .filter((k) => sel?.values?.[k] !== undefined)
    .map((k) => ({ k, label: LABELS[k], value: Number(sel.values[k]), rel: RELIABILITY[k]?.v || 'neutral', why: RELIABILITY[k]?.why }))
  const maxAbs = Math.max(...comps.map((c) => Math.abs(c.value)), 0.01)
  const totalAbs = comps.reduce((s, c) => s + Math.abs(c.value), 0) || 1
  const dominant = comps.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0]
  const dominantShare = Math.round((Math.abs(dominant?.value || 0) / totalAbs) * 100)
  const dominantRel = dominant?.rel
  const modelDir = sel?.vir < 0 ? 'underweight' : 'overweight'
  const lowConf = dominantRel === 'discount'

  return (
    <div className="canvas">
      <div className="demo-banner">
        <span className="demo-tag">Decomp real · verdict illustrative</span>
        <span>The agent challenges its <b>own model</b>: STF decomposition values are live; the regime read and per-component reliability show where to <b>trust vs discount</b> the signal given current markets.</span>
      </div>

      <div className="regime">
        <div className="regime-l">
          <div className="eyebrow" style={{ color: 'var(--brand-2)' }}>Market regime</div>
          <div className="regime-name">{REGIME.name}</div>
        </div>
        <p className="regime-read">{REGIME.read}</p>
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
            <div className="panel-sub eyebrow">Live components · reliability tagged by regime</div>
          </div>
          <div className="decomp">
            {comps.map((c) => {
              const w = (Math.abs(c.value) / maxAbs) * 50
              const pos = c.value > 0
              const isDom = c.k === dominant?.k
              return (
                <div className={`decomp-row${isDom ? ' dom' : ''}`} key={c.k}>
                  <div className="decomp-name">{c.label}{isDom && <span className="dom-tag">dominant</span>}</div>
                  <div className="bar-track">
                    <div className="bar-axis" />
                    <div className={`bar-fill ${pos ? 'pos' : 'neg'}`} style={pos ? { left: '50%', width: `${w}%` } : { left: `${50 - w}%`, width: `${w}%` }} />
                  </div>
                  <div className={`decomp-val ${pos ? 'pos' : 'neg'}`}>{signedStfPct(c.value)}</div>
                  <span className={`tag ${RTAG[c.rel]}`}>{RLABEL[c.rel]}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="panel" style={{ borderTop: `3px solid ${lowConf ? 'var(--warn)' : 'var(--pos)'}` }}>
          <div className="panel-head">
            <div className="panel-title">Model reliability verdict</div>
            <div className="panel-sub eyebrow">Should we trust the signal here?</div>
          </div>

          <div className="verdict">
            <div className={`verdict-badge ${lowConf ? 'warn' : 'pos'}`}>{lowConf ? 'Low-confidence — discount' : 'High-confidence — trust'}</div>
            <p className="verdict-body">
              The model reads <b>{modelDir}</b> (STF {stfPct(sel?.vir)}{Number.isNaN(sel?.virDelta) ? '' : `, ${signedStfPct(sel?.virDelta)} MoM`}).
              That read is <b>{dominantShare}%</b> driven by <b>{dominant?.label}</b>
              {lowConf
                ? ` — the least reliable component in a ${REGIME.name.split(' · ')[0]} regime. The signal's magnitude overstates its conviction; treat the ${modelDir} as soft and weight the corroborated growth/earnings components more heavily.`
                : ` — a component that is corroborated by current markets. The signal can be taken at face value.`}
            </p>
          </div>

          <div className="reliability-list">
            <div className="eyebrow" style={{ marginBottom: 8 }}>Why, component by component</div>
            {comps.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).map((c) => (
              <div className="rel-row" key={c.k}>
                <span className={`rel-dot rel-${c.rel}`} />
                <span className="rel-name">{c.label}</span>
                <span className="rel-why">{c.why}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel section-gap">
        <div className="panel-head">
          <div className="panel-title">What would make us discount the model more broadly</div>
          <div className="panel-sub eyebrow">Regime triggers the agent watches</div>
        </div>
        <div className="trigger-grid">
          <div className="trigger"><div className="trigger-h">Valuation signal decay</div><p>Top-down valuation has mis-fired ~6 consecutive months — the longer the streak, the more the agent down-weights valuation-driven STF reads.</p></div>
          <div className="trigger"><div className="trigger-h">Earnings-momentum confirmation</div><p>Q1 beats (+28.6% vs +13.1% est.) corroborate growth components, so growth-led signals get up-weighted vs valuation-led ones.</p></div>
          <div className="trigger"><div className="trigger-h">Leadership concentration</div><p>Mag-7 concentration means breadth signals and mean-reversion are unreliable; the agent flags single-factor-distorted decompositions.</p></div>
          <div className="trigger"><div className="trigger-h">Stale model snapshot</div><p>STF snapshot lag vs review date widens model error in fast-moving regimes — surfaced as a confidence haircut.</p></div>
        </div>
      </div>
    </div>
  )
}
