import { signedPts, num } from '../lib/format.js'

/* ---------- Diverging active-weight bars (CSS-driven) ---------- */
export function DivergingBars({ rows }) {
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.active)), 1)
  return (
    <div className="bars">
      {rows.map((r) => {
        const w = (Math.abs(r.active) / maxAbs) * 50
        const positive = r.active > 0
        const tone = !r.off && positive ? 'pos' : 'neg'
        const fillStyle = positive
          ? { left: '50%', width: `${w}%` }
          : { left: `${50 - w}%`, width: `${w}%` }
        return (
          <div className="bar-row" key={r.label}>
            <div className={`bar-name${r.off ? ' flag' : ''}`} title={r.label}>
              {r.off && <span className="bar-flag">⚑</span>}
              {r.label}
            </div>
            <div className="bar-track">
              <div className="bar-axis" />
              <div className={`bar-fill ${tone}`} style={fillStyle} />
            </div>
            <div className={`bar-val ${positive ? 'pos' : 'neg'}`}>{signedPts(r.active)}</div>
            <div className="bar-vir">{Number.isNaN(r.vir) ? '—' : num(r.vir, 3)}</div>
          </div>
        )
      })}
    </div>
  )
}

/* ---------- VIR vs active-weight scatter (SVG) ---------- */
export function VirScatter({ points }) {
  const W = 560, H = 320
  const m = { t: 14, r: 16, b: 38, l: 46 }
  const iw = W - m.l - m.r
  const ih = H - m.t - m.b

  const xs = points.map((p) => p.x)
  const ys = points.map((p) => p.y)
  const xMin = Math.min(-2, Math.floor(Math.min(...xs) - 1))
  const xMax = Math.max(2, Math.ceil(Math.max(...xs) + 1))
  const yMin = Math.min(...ys, -0.02)
  const yMax = Math.max(...ys, 0.02)
  const yPad = (yMax - yMin) * 0.15 || 0.01

  const sx = (x) => m.l + ((x - xMin) / (xMax - xMin)) * iw
  const sy = (y) => m.t + (1 - (y - (yMin - yPad)) / ((yMax + yPad) - (yMin - yPad))) * ih

  const xTicks = []
  for (let t = xMin; t <= xMax; t += 2) xTicks.push(t)
  const yTicks = []
  const yStep = (yMax - yMin) > 0.08 ? 0.04 : 0.02
  for (let t = Math.ceil((yMin - yPad) / yStep) * yStep; t <= yMax + yPad; t += yStep) {
    yTicks.push(Number(t.toFixed(3)))
  }

  const x0 = sx(0)
  const y0 = sy(0)

  return (
    <div className="scatter-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="VIR signal vs active weight scatter">
        {/* contra-signal quadrant shading: OW + negative VIR, UW + positive VIR */}
        <rect x={x0} y={m.t} width={m.l + iw - x0} height={y0 - m.t} fill="#fbeeec" opacity="0.5" />
        <rect x={m.l} y={y0} width={x0 - m.l} height={m.t + ih - y0} fill="#fbeeec" opacity="0.5" />

        {/* gridlines */}
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line x1={m.l} x2={W - m.r} y1={sy(t)} y2={sy(t)} stroke="#eceae3" strokeWidth="1" />
            <text x={m.l - 8} y={sy(t) + 3} textAnchor="end" fontSize="10" fill="#86868f" fontFamily="JetBrains Mono">
              {t.toFixed(2)}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={sx(t)} y={H - 14} textAnchor="middle" fontSize="10" fill="#86868f" fontFamily="JetBrains Mono">
            {t > 0 ? `+${t}` : t}
          </text>
        ))}

        {/* zero axes */}
        <line x1={x0} x2={x0} y1={m.t} y2={m.t + ih} stroke="#d2cec2" strokeWidth="1" strokeDasharray="3 3" />
        <line x1={m.l} x2={W - m.r} y1={y0} y2={y0} stroke="#d2cec2" strokeWidth="1" strokeDasharray="3 3" />

        {/* points */}
        {points.map((p, i) => {
          const cx = sx(p.x), cy = sy(p.y)
          if (p.off) {
            return (
              <polygon
                key={i}
                points={`${cx},${cy - 5.5} ${cx + 5},${cy + 4.5} ${cx - 5},${cy + 4.5}`}
                fill="#c0392b" opacity="0.9"
              >
                <title>{`${p.label}: active ${signedPts(p.x)}pts, VIR ${num(p.y, 3)}`}</title>
              </polygon>
            )
          }
          return (
            <circle key={i} cx={cx} cy={cy} r="5" fill="#2a4bd7" opacity="0.85">
              <title>{`${p.label}: active ${signedPts(p.x)}pts, VIR ${num(p.y, 3)}`}</title>
            </circle>
          )
        })}

        {/* axis titles */}
        <text x={m.l + iw / 2} y={H - 1} textAnchor="middle" fontSize="10" fill="#adaca8">Active weight (pts)</text>
        <text x={12} y={m.t + ih / 2} textAnchor="middle" fontSize="10" fill="#adaca8" transform={`rotate(-90 12 ${m.t + ih / 2})`}>VIR</text>
      </svg>
      <div className="scatter-legend">
        <div className="legend-item"><span className="legend-dot" /> Aligned</div>
        <div className="legend-item"><span className="legend-tri" /> Off-signal (contra-signal quadrant)</div>
      </div>
    </div>
  )
}
