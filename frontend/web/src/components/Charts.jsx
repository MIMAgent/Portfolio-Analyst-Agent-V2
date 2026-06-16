import { useState } from 'react'
import { signedPts, num } from '../lib/format.js'

/* ---------- Diverging active-weight bars (CSS-driven) ---------- */
export function DivergingBars({ rows }) {
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.active)), 1)
  if (!rows.length) return <div className="empty-note">No positions in this category.</div>
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

/* ---------- VIR vs active-weight scatter (SVG, interactive) ---------- */
export function VirScatter({ points }) {
  const [hover, setHover] = useState(null)
  const W = 640, H = 400
  const m = { t: 16, r: 18, b: 42, l: 52 }
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
  const hp = hover != null ? points[hover] : null

  return (
    <div className="scatter-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="VIR signal vs active weight scatter">
        {/* contra-signal quadrant shading: OW + negative VIR, UW + positive VIR */}
        <rect x={x0} y={m.t} width={m.l + iw - x0} height={y0 - m.t} fill="#fbeeec" opacity="0.45" />
        <rect x={m.l} y={y0} width={x0 - m.l} height={m.t + ih - y0} fill="#fbeeec" opacity="0.45" />

        {/* gridlines */}
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line x1={m.l} x2={W - m.r} y1={sy(t)} y2={sy(t)} stroke="#eceae3" strokeWidth="1" />
            <text x={m.l - 9} y={sy(t) + 3} textAnchor="end" fontSize="10.5" fill="#86868f" fontFamily="JetBrains Mono">
              {t.toFixed(2)}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={sx(t)} y={H - 16} textAnchor="middle" fontSize="10.5" fill="#86868f" fontFamily="JetBrains Mono">
            {t > 0 ? `+${t}` : t}
          </text>
        ))}

        {/* zero axes */}
        <line x1={x0} x2={x0} y1={m.t} y2={m.t + ih} stroke="#d2cec2" strokeWidth="1" strokeDasharray="3 3" />
        <line x1={m.l} x2={W - m.r} y1={y0} y2={y0} stroke="#d2cec2" strokeWidth="1" strokeDasharray="3 3" />

        {/* hover crosshair */}
        {hp && (
          <g>
            <line x1={sx(hp.x)} x2={sx(hp.x)} y1={m.t} y2={m.t + ih} stroke="#c9c6bb" strokeWidth="1" />
            <line x1={m.l} x2={W - m.r} y1={sy(hp.y)} y2={sy(hp.y)} stroke="#c9c6bb" strokeWidth="1" />
          </g>
        )}

        {/* points */}
        {points.map((p, i) => {
          const cx = sx(p.x), cy = sy(p.y)
          const active = i === hover
          if (p.off) {
            const s = active ? 7.5 : 6
            return (
              <polygon
                key={i}
                points={`${cx},${cy - s} ${cx + s * 0.9},${cy + s * 0.8} ${cx - s * 0.9},${cy + s * 0.8}`}
                fill="#c0392b" opacity={active ? 1 : 0.85}
                stroke={active ? '#fff' : 'none'} strokeWidth="1.5"
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                style={{ cursor: 'pointer' }}
              />
            )
          }
          return (
            <circle
              key={i} cx={cx} cy={cy} r={active ? 7.5 : 5.5}
              fill="#2a4bd7" opacity={active ? 1 : 0.8}
              stroke={active ? '#fff' : 'none'} strokeWidth="1.5"
              onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
              style={{ cursor: 'pointer' }}
            />
          )
        })}

        {/* callout */}
        {hp && (() => {
          const cx = sx(hp.x), cy = sy(hp.y)
          const bw = Math.max(140, hp.label.length * 7 + 26)
          const bx = Math.min(Math.max(cx + 12, m.l), W - m.r - bw)
          const by = Math.max(cy - 46, m.t)
          return (
            <g pointerEvents="none">
              <rect x={bx} y={by} width={bw} height={40} rx="7" fill="#1b1b1f" opacity="0.96" />
              <text x={bx + 12} y={by + 16} fontSize="11.5" fontWeight="600" fill="#fff" fontFamily="Hanken Grotesk">{hp.label}</text>
              <text x={bx + 12} y={by + 31} fontSize="10.5" fill="#cfcfd4" fontFamily="JetBrains Mono">
                {signedPts(hp.x)} pts · VIR {num(hp.y, 3)} · {hp.off ? 'off-signal' : 'aligned'}
              </text>
            </g>
          )
        })()}

        {/* axis titles */}
        <text x={m.l + iw / 2} y={H - 1} textAnchor="middle" fontSize="10.5" fill="#adaca8">Active weight (pts)</text>
        <text x={13} y={m.t + ih / 2} textAnchor="middle" fontSize="10.5" fill="#adaca8" transform={`rotate(-90 13 ${m.t + ih / 2})`}>VIR</text>
      </svg>
      <div className="scatter-legend">
        <div className="legend-item"><span className="legend-dot" /> Aligned</div>
        <div className="legend-item"><span className="legend-tri" /> Off-signal (contra-signal quadrant)</div>
        <div className="legend-item" style={{ marginLeft: 'auto', color: 'var(--ink-4)' }}>Hover a point for detail</div>
      </div>
    </div>
  )
}
