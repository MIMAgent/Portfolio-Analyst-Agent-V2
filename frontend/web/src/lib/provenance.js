/**
 * Market-context provenance: does the research behind a challenge actually
 * speak to that challenge's market?
 *
 * The backend (agent2) now answers this at retrieval time and emits
 * `market_evidence_status` on every challenge. The fund JSON currently shipped
 * predates that fix, so this module derives the same answer at render time from
 * data every packet already carries — the exposure's ACID and each row's source
 * label. The derivation and the emitted field agree, so a regenerated packet
 * changes nothing here; it just replaces a derived value with a stated one.
 *
 * Why it matters: all four International challenges (France, United Kingdom,
 * India, European Industrials) currently render a FactSet excerpt about S&P 500
 * earnings under the heading "Approved-source market context", with a working
 * source link. Presented as sourced, it is worse than an empty panel.
 */

// An ACID is positional: "<REGION> [<CATEGORY>] EQ". "US ID EQ" is US
// industrials, "EU ID EQ" is European industrials, a bare "ID EQ" is Indonesia.
// Mirrors parse_acid() in src/portfolio_analyst_agent/market_context_regions.py.
export function acidRegion(acid) {
  const tokens = String(acid || '').trim().split(/\s+/).filter(Boolean)
  return tokens.length ? tokens[0].toUpperCase() : ''
}

// Countries that a bloc-level source legitimately covers.
const BLOC_MEMBERS = {
  EU: ['AT', 'BE', 'CZ', 'DE', 'DK', 'ES', 'FI', 'FR', 'GR', 'HU', 'IE', 'IT',
       'NL', 'NO', 'PL', 'PT', 'SE', 'CH'],
  EM: ['BR', 'CL', 'CN', 'CO', 'EG', 'HU', 'ID', 'IN', 'KR', 'MX', 'MY', 'PE',
       'PH', 'PL', 'QA', 'TH', 'TR', 'TW', 'ZA', 'AE', 'ARAB'],
}

// The approved-source registry is seven fixed entries. Five are explicitly
// US-scoped; S&P Global and Goldman are global and match any region. Keyed on a
// lowercase fragment of the source label so small naming changes still match.
const SOURCE_REGION = [
  ['factset', 'US'],
  ['bureau of labor', 'US'],
  ['ism', 'US'],
  ['federal reserve', 'US'],
  ['nasdaq', 'US'],
  ['s&p global', null],
  ['goldman', null],
]

/** The region a source speaks to: a code, or null for a global source. */
export function sourceRegion(label) {
  const l = String(label || '').toLowerCase()
  for (const [fragment, region] of SOURCE_REGION) {
    if (l.includes(fragment)) return region
  }
  return null
}

/** True when a source cannot speak to this exposure's market. */
export function isRegionMismatch(exposureRegion, sourceLabel) {
  const src = sourceRegion(sourceLabel)
  if (!src || !exposureRegion) return false
  if (src === exposureRegion) return false
  return !(BLOC_MEMBERS[src] || []).includes(exposureRegion)
}

/**
 * Resolve the panel state for one challenge.
 *
 * Prefers the backend's stated status when present; otherwise derives it.
 *   sourced — rows exist and every one speaks to this market
 *   thin    — rows exist but at least one is off-region, or lenses came back short
 *   absent  — nothing was retrieved
 */
export function marketState({ status, rows, lenses, exposureRegion }) {
  const list = Array.isArray(rows) ? rows : []
  if (String(status || '').toUpperCase() === 'ABSENT') return 'absent'
  if (!list.length) return 'absent'
  const mismatched = list.some((r) => isRegionMismatch(exposureRegion, r.source))
  if (mismatched) return 'thin'
  const attempted = Array.isArray(lenses) ? lenses.length : 0
  return attempted && list.length < attempted ? 'thin' : 'sourced'
}

/**
 * The sentence shown when there is no usable research. Uses the backend's note
 * verbatim when it exists, since that note names the actual retrieval reason.
 */
export function absenceCopy({ note, label }) {
  // The agent's note names the actual retrieval reason — whether no approved
  // source covers the region, or sources were searched and nothing matched.
  // Derived copy cannot tell those apart, so it stays true of both rather than
  // guessing: claiming "no source covers US" would be plainly false, since the
  // whole allowlist is US-scoped.
  if (note) return note
  const what = label ? ` for ${label}` : ''
  return `No approved-source research was retrieved${what}. There is no external market evidence behind this challenge — the cases below rest on internal research and measured risk only.`
}
