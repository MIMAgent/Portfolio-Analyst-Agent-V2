import { useMemo, useState } from 'react'
import { kpis, execBullets, chartPositions, positionCategories, scatterPoints, header } from '../lib/data.js'
import { isNum, fmtDate } from '../lib/format.js'
import { DivergingBars, VirScatter } from '../components/Charts.jsx'

function kpiValue(k) {
  if (!isNum(k.value)) return '—'
  const n = Number(k.value)
  const body = k.unit === '%' ? n.toFixed(2) : n.toFixed(0)
  const sign = k.signed && n > 0 ? '+' : ''
  return `${sign}${body}${k.unit}`
}

export default function Overview() {
  const [cat, setCat] = useState('All')

  const barRows = useMemo(() => {
    const base = cat === 'All' ? chartPositions : chartPositions.filter((p) => p.category === cat)
    return [...base]
      .sort((a, b) => Math.abs(b.active) - Math.abs(a.active))
      .slice(0, cat === 'All' ? 16 : 20)
  }, [cat])

  return (
    <div className="canvas">
      <section className="kpi-row">
        {kpis.map((k, i) => (
          <div className={`kpi tone-${k.tone} rise d${i + 1}`} key={k.key}>
            <div className="kpi-label eyebrow">{k.label}</div>
            <div className={`kpi-val ${k.tone === 'neg' ? 'neg' : k.tone === 'warn' ? 'warn' : k.tone === 'pos' ? 'pos' : ''}`}>
              {kpiValue(k)}
            </div>
            <div className="kpi-sub">{k.sub}</div>
          </div>
        ))}
      </section>

      <section className="exec rise d3">
        <div className="exec-head">
          <span className="eyebrow">Agent — Executive Summary</span>
          <span className="exec-rule" />
          <span className="eyebrow">{fmtDate(header.snapshot_date)}</span>
        </div>
        <div className="exec-list">
          {execBullets.slice(0, 4).map((b, i) => (
            <div className={`exec-bullet${b.neg ? ' neg' : ''}`} key={i}>
              <span className="tick" />
              <div><b>{b.label}.</b> {b.text}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid-2">
        <div className="panel rise d4">
          <div className="panel-head panel-head-row">
            <div>
              <div className="panel-title">Active weight vs benchmark</div>
              <div className="panel-sub eyebrow">pts · ⚑ off-signal · STF shown right</div>
            </div>
            <div className="chips chips-sm">
              {positionCategories.map((c) => (
                <button key={c.key} className={`chip${cat === c.key ? ' active' : ''}`} onClick={() => setCat(c.key)}>{c.label}</button>
              ))}
            </div>
          </div>
          <DivergingBars rows={barRows} />
        </div>

        <div className="panel rise d5">
          <div className="panel-head">
            <div className="panel-title">STF signal vs active weight</div>
            <div className="panel-sub eyebrow">Contra-signal quadrants shaded · hover a point for detail</div>
          </div>
          <VirScatter points={scatterPoints} />
        </div>
      </section>
    </div>
  )
}
