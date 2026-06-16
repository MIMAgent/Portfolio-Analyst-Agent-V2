import { kpis, execBullets, activeWeightRows, scatterPoints, header } from '../lib/data.js'
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
          <div className="panel-head">
            <div className="panel-title">Active weight vs benchmark</div>
            <div className="panel-sub eyebrow">Top 15 by magnitude · pts · ⚑ off-signal · VIR shown right</div>
          </div>
          <DivergingBars rows={activeWeightRows} />
        </div>

        <div className="panel rise d5">
          <div className="panel-head">
            <div className="panel-title">VIR signal vs active weight</div>
            <div className="panel-sub eyebrow">Contra-signal quadrants shaded red</div>
          </div>
          <VirScatter points={scatterPoints} />
        </div>
      </section>
    </div>
  )
}
