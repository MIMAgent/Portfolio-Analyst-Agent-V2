export const isNum = (v) => v !== null && v !== undefined && !Number.isNaN(Number(v))

export function pct(v, d = 2) {
  if (!isNum(v)) return '—'
  return `${Number(v).toFixed(d)}%`
}

export function signedPct(v, d = 2) {
  if (!isNum(v)) return '—'
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(d)}%`
}

export function signedPts(v, d = 2) {
  if (!isNum(v)) return '—'
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(d)}`
}

export function num(v, d = 3) {
  if (!isNum(v)) return '—'
  return Number(v).toFixed(d)
}

export function signedNum(v, d = 3) {
  if (!isNum(v)) return '—'
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(d)}`
}

// STF (and its decomposition components) are stored as decimals; show as percent.
export function stfPct(v, d = 2) {
  if (!isNum(v)) return '—'
  return `${(Number(v) * 100).toFixed(d)}%`
}

export function signedStfPct(v, d = 2) {
  if (!isNum(v)) return '—'
  const n = Number(v) * 100
  return `${n > 0 ? '+' : ''}${n.toFixed(d)}%`
}

// Ordinal suffix for a whole number: 1 -> "1st", 91 -> "91st", 11 -> "11th".
export function ordinal(n) {
  if (!isNum(n)) return '—'
  const i = Math.round(Number(n))
  const v = i % 100
  const s = ['th', 'st', 'nd', 'rd']
  return `${i}${s[(v - 20) % 10] || s[v] || s[0]}`
}

// Dollar figures are carried in millions throughout house.js.
export function usdM(v, d = 1) {
  if (!isNum(v)) return '—'
  const n = Number(v)
  if (Math.abs(n) >= 1000) return `$${(n / 1000).toFixed(2)}bn`
  return `$${n.toFixed(d)}m`
}

export function signedUsdM(v, d = 1) {
  if (!isNum(v)) return '—'
  const n = Number(v)
  const body = Math.abs(n) >= 1000 ? `$${(Math.abs(n) / 1000).toFixed(2)}bn` : `$${Math.abs(n).toFixed(d)}m`
  return `${n < 0 ? '−' : '+'}${body}`
}

export function normKey(v) {
  return String(v || '').toLowerCase().replace(/[^a-z0-9]+/g, '')
}

export function titleCase(v) {
  if (!v) return ''
  return String(v).replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function fmtDate(v) {
  if (!v) return ''
  const d = new Date(`${v}T00:00:00`)
  if (Number.isNaN(d.getTime())) return v
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
