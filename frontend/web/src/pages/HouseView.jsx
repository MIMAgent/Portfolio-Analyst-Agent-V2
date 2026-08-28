import { useState } from 'react'
import {
  houseFunds, houseMeta, opposingBets, convictionGaps,
  crossChallenges, labelEchoes, sharedResearch, sectorOffset,
} from '../lib/house.js'
import { signedPts, signedStfPct, fmtDate, usdM, signedUsdM } from '../lib/format.js'

// Sleeve bar: active weight on a shared zero axis so three sleeves can be compared
// at a glance. Scaled to the widest active weight on the row, not to a global max,
// because the question here is "how far apart are these sleeves", not "how big".
function SleeveRow({ sleeves, scale }) {
  return (
    <div className="hv-sleeves">
      {sleeves.map((s) => {
        const w = Math.min(50, (Math.abs(s.active) / scale) * 50)
        const pos = s.active > 0
        return (
          <div className="hv-sleeve" key={s.fundId}>
            <div className="hv-sleeve-name">{s.short}</div>
            <div className="hv-track">
              <div className="hv-zero" />
              <div
                className={`hv-fill ${pos ? 'pos' : 'neg'}`}
                style={pos ? { left: '50%', width: `${w}%` } : { left: `${50 - w}%`, width: `${w}%` }}
              />
            </div>
            <div className={`hv-sleeve-val ${pos ? 'pos' : 'neg'}`}>{signedPts(s.active, 2)}</div>
            {s.dollars !== null && (
              <div className={`hv-sleeve-usd ${pos ? 'pos' : 'neg'}`}>{signedUsdM(s.dollars)}</div>
            )}
            {s.challenged
              ? <span className="hv-flag" title="Challenged in this sleeve's review">⚑</span>
              : <span className="hv-flag-sp" />}
          </div>
        )
      })}
    </div>
  )
}

// Gross = active risk actually being run on this exposure. Net = what survives the
// sleeves disagreeing. The gap is the number a committee has never been shown.
function NetGross({ row }) {
  if (row.grossUsd === null || !row.grossUsd) return null
  return (
    <div className="hv-netgross">
      <div className="hv-ng-item">
        <div className="hv-ng-lab eyebrow">Gross active</div>
        <div className="hv-ng-val">{usdM(row.grossUsd)}</div>
      </div>
      <div className="hv-ng-arrow">→</div>
      <div className="hv-ng-item">
        <div className="hv-ng-lab eyebrow">Net</div>
        <div className={`hv-ng-val ${row.netUsd < 0 ? 'neg' : 'pos'}`}>{signedUsdM(row.netUsd)}</div>
      </div>
      <div className="hv-ng-bar">
        <div className="hv-ng-fill" style={{ width: `${Math.min(100, (row.offsetPct || 0) * 100)}%` }} />
      </div>
      <div className="hv-ng-off">
        <b>{Math.round((row.offsetPct || 0) * 100)}%</b> offsets internally
        <span className="hv-ng-sub">{usdM(row.cancelledUsd)} of capital against itself</span>
      </div>
    </div>
  )
}

function ModelStrip({ row }) {
  return (
    <div className="hv-model">
      <span className="hv-model-item">STF <b>{signedStfPct(row.stf)}</b></span>
      <span className="hv-model-sep">·</span>
      <span className="hv-model-item">Algo active <b>{signedPts(row.algo, 2)} pts</b></span>
      <span className="hv-model-sep">·</span>
      <span className="hv-model-note">identical in every sleeve</span>
    </div>
  )
}

const SECTIONS = [
  { id: 'opposing', label: 'Opposing bets', count: (d) => d.opposingBets.length },
  { id: 'conviction', label: 'Same call, different size', count: (d) => d.convictionGaps.length },
  { id: 'challenged', label: 'Challenged twice', count: (d) => d.crossChallenges.length },
  { id: 'research', label: 'Shared research', count: (d) => d.sharedResearch.length },
]

export default function HouseView() {
  const [section, setSection] = useState('opposing')
  const data = { opposingBets, convictionGaps, crossChallenges, sharedResearch }

  return (
    <div className="canvas">
      {/* The framing claim, measured rather than asserted. */}
      <section className="hv-hero rise d1">
        <div className="hv-hero-main">
          <div className="eyebrow">
            {houseMeta.sleeves}-sleeve equity aggregate · {usdM(houseMeta.totalAumM)}
            {houseMeta.aumApproximate ? ' (approx)' : ''} · {fmtDate(houseMeta.snapshotDate)}
          </div>
          <h2 className="hv-hero-title">
            {houseMeta.oneVoice
              ? 'One model, three books.'
              : 'The sleeves are working from different signals.'}
          </h2>
          <p className="hv-hero-text">
            {houseMeta.oneVoice ? (
              <>
                Across the <b>{houseMeta.sharedExposures}</b> exposures held in more than one sleeve, STF and the
                algo's active weight are <b>identical every time</b> — {houseMeta.stfIdentical} of {houseMeta.stfIdentical} on
                the signal, {houseMeta.algoIdentical} of {houseMeta.algoIdentical} on the algo. The model tells all
                three books the same thing. Where the books differ, that is a positioning decision somebody made —
                not a disagreement about what the model says.
              </>
            ) : (
              <>
                {houseMeta.stfDiffering} shared exposures carry a different STF between sleeves and{' '}
                {houseMeta.algoDiffering} a different algo weight. Reconcile those before reading anything below.
              </>
            )}
          </p>
        </div>
        <div className="hv-hero-stats">
          <div className="hv-stat">
            <div className="hv-stat-val">{houseMeta.sharedExposures}</div>
            <div className="hv-stat-lab eyebrow">Exposures held in ≥2 sleeves</div>
            <div className="hv-stat-sub">of {houseMeta.distinctExposures} distinct</div>
          </div>
          <div className="hv-stat">
            <div className="hv-stat-val neg">{opposingBets.length}</div>
            <div className="hv-stat-lab eyebrow">Sleeves on opposite sides</div>
            <div className="hv-stat-sub">active risk spent against itself</div>
          </div>
          <div className="hv-stat">
            <div className="hv-stat-val warn">
              {houseMeta.hasAum ? usdM(sectorOffset.usd) : convictionGaps.length}
            </div>
            <div className="hv-stat-lab eyebrow">
              {houseMeta.hasAum ? 'Sector capital working against itself' : 'Same call, different size'}
            </div>
            <div className="hv-stat-sub">
              {houseMeta.hasAum
                ? `${sectorOffset.count} opposed sectors · sectors only, to avoid double-counting`
                : '≥1.75× active-weight gap'}
            </div>
          </div>
        </div>
      </section>

      <div className="hv-roster">
        {houseFunds.map((f) => (
          <div className="hv-roster-item" key={f.id}>
            <span className="hv-roster-name">{f.navName}</span>
            <span className="hv-roster-meta">
              {houseMeta.hasAum ? `${usdM(f.aumM)} · ${(f.share * 100).toFixed(0)}%` : `${f.positions} positions`}
              {' · '}{f.challenges} challenges
            </span>
          </div>
        ))}
      </div>

      <nav className="chips chips-sm hv-nav">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            className={`chip${section === s.id ? ' active' : ''}`}
            onClick={() => setSection(s.id)}
          >
            {s.label}<span className="hv-nav-count">{s.count(data)}</span>
          </button>
        ))}
      </nav>

      {section === 'opposing' && (
        <section className="panel rise d2">
          <div className="panel-head">
            <div className="panel-title">Sleeves on opposite sides of the same exposure</div>
            <div className="panel-sub eyebrow">
              Ranked by spread · identical STF and algo in every row · part of this active risk nets off at
              house level, and no single fund review can see it
            </div>
          </div>
          <div className="hv-list">
            {opposingBets.slice(0, 8).map((r) => (
              <div className="hv-row" key={r.acid}>
                <div className="hv-row-head">
                  <div>
                    <div className="hv-row-title">{r.label}</div>
                    <div className="hv-row-meta eyebrow">{r.acid} · {r.category}</div>
                  </div>
                  <div className="hv-spread">
                    <div className="hv-spread-val">{r.spread.toFixed(2)}</div>
                    <div className="eyebrow">pts spread</div>
                  </div>
                </div>
                <ModelStrip row={r} />
                <SleeveRow sleeves={r.sleeves} scale={Math.max(...r.sleeves.map((s) => Math.abs(s.active)))} />
                <NetGross row={r} />
                <p className="hv-read">
                  <b>{r.widest.long.short} {signedPts(r.widest.long.active, 2)}</b> against{' '}
                  <b>{r.widest.short.short} {signedPts(r.widest.short.active, 2)}</b>
                  {r.sleeves.length > 2 ? ` (${r.longs.length} long, ${r.shorts.length} short)` : ''} — the algo says{' '}
                  {signedPts(r.algo, 2)} pts to both.{' '}
                  {r.challengedIn.length > 0
                    ? `Raised in ${r.challengedIn.join(' and ')}, where only one side of it is visible.`
                    : 'Neither sleeve review raises it, because inside each book the position is coherent.'}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {section === 'conviction' && (
        <section className="panel rise d2">
          <div className="panel-head">
            <div className="panel-title">Same direction, materially different conviction</div>
            <div className="panel-sub eyebrow">
              Identical signal and identical algo view, but one sleeve holds a multiple of the other — either one is
              under-committed or the other is over-committed, and nothing in the evidence says which
            </div>
          </div>
          <div className="hv-list">
            {convictionGaps.slice(0, 8).map((r) => (
              <div className="hv-row" key={r.acid}>
                <div className="hv-row-head">
                  <div>
                    <div className="hv-row-title">{r.label}</div>
                    <div className="hv-row-meta eyebrow">{r.acid} · {r.category}</div>
                  </div>
                  <div className="hv-spread">
                    <div className="hv-spread-val">{r.ratio.toFixed(1)}×</div>
                    <div className="eyebrow">size gap</div>
                  </div>
                </div>
                <ModelStrip row={r} />
                <SleeveRow sleeves={r.sleeves} scale={r.hi} />
                <NetGross row={r} />
                <p className="hv-read">
                  <b>{r.biggest.short} {signedPts(r.biggest.active, 2)}</b> versus{' '}
                  <b>{r.smallest.short} {signedPts(r.smallest.active, 2)}</b> — a {(r.hi - r.lo).toFixed(2)} pt
                  difference on an identical read, against an algo weight of {signedPts(r.algo, 2)} pts.
                  {r.challengedIn.length > 0
                    ? ` Challenged in ${r.challengedIn.join(' and ')} only.`
                    : ' Neither sleeve was challenged on it.'}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {section === 'challenged' && (
        <section className="panel rise d2">
          <div className="panel-head">
            <div className="panel-title">Raised independently in more than one sleeve</div>
            <div className="panel-sub eyebrow">
              The agent flagged the same exposure in separate fund reviews — neither review can reference the other
            </div>
          </div>
          <div className="hv-list">
            {crossChallenges.map((r) => (
              <div className="hv-row" key={r.acid}>
                <div className="hv-row-head">
                  <div>
                    <div className="hv-row-title">{r.label}</div>
                    <div className="hv-row-meta eyebrow">{r.acid} · {r.category}</div>
                  </div>
                  <div className="hv-spread">
                    <div className="hv-spread-val">{r.inFunds.length}</div>
                    <div className="eyebrow">sleeves</div>
                  </div>
                </div>
                <ModelStrip row={r} />
                <SleeveRow sleeves={r.sleeves} scale={Math.max(...r.sleeves.map((s) => Math.abs(s.active)))} />
                <div className="hv-scores">
                  {r.headlines.map((h) => (
                    <span className="hv-score" key={h.fundId}>
                      {h.short}<b>{h.score?.toFixed(2) ?? '—'}</b>
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {labelEchoes.length > 0 && (
            <div className="hv-echo">
              <div className="eyebrow">Thematic echoes — same name, different exposure</div>
              {labelEchoes.map((e) => (
                <p className="hv-echo-row" key={e.label}>
                  <b>{e.label}</b> is challenged in {new Set(e.rows.map((r) => r.fundId)).size} sleeves, but as{' '}
                  {[...new Set(e.rows.map((r) => r.acid))].join(' and ')} — different regional cells, not the same
                  position. Related theme; not a shared exposure.
                </p>
              ))}
            </div>
          )}
        </section>
      )}

      {section === 'research' && (
        <section className="panel rise d2">
          <div className="panel-head">
            <div className="panel-title">One research note underwriting several sleeves</div>
            <div className="panel-sub eyebrow">
              If the note is wrong or stale, the error is correlated across the house
            </div>
          </div>
          <div className="hv-docs">
            {sharedResearch.slice(0, 10).map((d) => (
              <div className="hv-doc" key={d.doc}>
                <div className="hv-doc-name">{d.doc}</div>
                <div className="hv-doc-meta">
                  <span className="hv-doc-count">{d.positions} positions</span>
                  <span className="hv-doc-funds">
                    {d.funds.map((id) => houseFunds.find((f) => f.id === id)?.short || id).join(' · ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Stated plainly, because the absence of AUM is a real limit on this view. */}
      <p className="hv-caveat">
        {houseMeta.hasAum ? (
          <>
            Dollar figures weight each sleeve by size ({usdM(houseMeta.totalAumM)} total, as of{' '}
            {fmtDate(houseMeta.aumAsOf)}
            {houseMeta.aumApproximate ? ', approximate' : ''}). Two limits worth stating: each sleeve's active
            weight is measured against <b>its own benchmark</b> (US Market / Global ex-US / Global), so a net
            figure is a capital-weighted <b>active tilt</b>, not a position against one blended benchmark; and
            these three sleeves are <b>not confirmed to be the full equity book</b>, so this is a three-sleeve
            aggregate rather than a house total. No cross-exposure total is shown, because sectors, styles and
            countries overlap and summing them would double-count.
          </>
        ) : (
          <>
            Active weights are compared <b>per sleeve and unweighted</b> — no fund size is available, so a 2 pt
            overweight in a small sleeve and in a large one appear the same.
          </>
        )}
      </p>
    </div>
  )
}
