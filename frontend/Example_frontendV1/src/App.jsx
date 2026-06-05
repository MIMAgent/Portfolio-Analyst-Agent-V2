import { useDeferredValue, useState } from 'react'
import bundle from './data/monthlyReviewBundle.json'

const acidTypeLabels = {
  acid_bond: 'Bond',
  acid_country: 'Country',
  acid_region_sector: 'Region / Sector',
}

export default function App() {
  const funds = bundle.funds
  const [selectedSlug, setSelectedSlug] = useState(funds[0]?.slug ?? '')
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query.trim().toLowerCase())

  const selectedFund = funds.find((fund) => fund.slug === selectedSlug) ?? funds[0]
  const payload = selectedFund?.run_payload
  const changeBrief = payload?.change_brief
  const sizing = payload?.sizing_considerations
  const challengeBrief = payload?.challenge_brief
  const coverage = payload?.fund_snapshot_summary?.coverage
  const memorySummary = payload?.fund_snapshot_summary?.memory_summary ?? {}
  const triggerSummary = payload?.fund_snapshot_summary?.trigger_summary ?? {}

  const materialMovers = filterItems(changeBrief?.material_movers ?? [], deferredQuery, materialMoverText)
  const agreements = filterItems(sizing?.algo_vs_positioning_agreement ?? [], deferredQuery, sizingText)
  const disagreements = filterItems(sizing?.algo_vs_positioning_disagreement ?? [], deferredQuery, sizingText)
  const challenges = filterItems(challengeBrief?.items ?? [], deferredQuery, challengeText)
  const evidenceIndex = changeBrief?.evidence_index ?? challengeBrief?.evidence_index ?? []
  const sourceHashes = Object.entries(payload?.review_run_metadata?.source_file_hashes ?? {})

  return (
    <div className="review-shell">
      <aside className="rail">
        <div className="brand-block">
          <span className="eyebrow">Portfolio Analyst Agent</span>
          <h1>Monthly Review Viewer</h1>
          <p>
            One place to review the Change Brief, sizing lens, challenge items, and evidence context
            from the tracked monthly review outputs.
          </p>
        </div>

        <section className="rail-section">
          <div className="section-kicker">Bundle Snapshot</div>
          <div className="mini-metrics">
            <MiniMetric label="Snapshot" value={bundle.snapshot_date} />
            <MiniMetric label="As of" value={bundle.as_of_date} />
            <MiniMetric label="Funds" value={String(bundle.fund_count)} />
          </div>
        </section>

        <section className="rail-section">
          <div className="section-kicker">Funds</div>
          <div className="fund-stack">
            {funds.map((fund) => {
              const fundTriggerSummary = fund.run_payload.fund_snapshot_summary.trigger_summary
              return (
                <button
                  key={fund.slug}
                  type="button"
                  className={`fund-card ${fund.slug === selectedFund?.slug ? 'is-active' : ''}`}
                  onClick={() => setSelectedSlug(fund.slug)}
                >
                  <span className="fund-card-name">{fund.fund}</span>
                  <span className="fund-card-meta">
                    Fired {fundTriggerSummary.fired_count} / Borderline {fundTriggerSummary.borderline_count}
                  </span>
                </button>
              )
            })}
          </div>
        </section>
      </aside>

      <main className="review-main">
        <section className="hero-panel">
          <div className="hero-copy">
            <span className="eyebrow">Selected Fund</span>
            <h2>{selectedFund?.fund}</h2>
            <p>{changeBrief?.executive_summary}</p>
            <div className="chip-row">
              <Chip label={`Run ${payload?.review_run_metadata?.review_run_id ?? 'N/A'}`} />
              <Chip label={`Mode ${payload?.review_run_metadata?.run_mode ?? 'N/A'}`} subtle />
              <Chip label={`Generated ${payload?.review_run_metadata?.generated_at ?? 'N/A'}`} subtle />
            </div>
          </div>

          <div className="hero-metrics">
            <MetricCard
              tone="gold"
              label="Target Coverage"
              value={formatPercent(coverage?.target_match_pct)}
              subvalue="Matched rolled target weight"
            />
            <MetricCard
              tone="mint"
              label="Benchmark Coverage"
              value={formatPercent(coverage?.benchmark_match_pct)}
              subvalue="Matched rolled benchmark weight"
            />
            <MetricCard
              tone="rose"
              label="Fired Triggers"
              value={String(triggerSummary.fired_count ?? 0)}
              subvalue={`${triggerSummary.borderline_count ?? 0} borderline`}
            />
            <MetricCard
              tone="sky"
              label="Memory Footprint"
              value={`${memorySummary.approved_count ?? 0} approved`}
              subvalue={`${memorySummary.proposed_count ?? 0} proposed`}
            />
          </div>
        </section>

        <section className="toolbar-panel">
          <label className="search-box">
            <span>Search ACID, narrative, or challenge</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="US ID EQ, disagreement, cash, JP IT EQ..."
            />
          </label>

          <div className="toolbar-stats">
            <ToolbarStat label="Material Movers" value={String(materialMovers.length)} />
            <ToolbarStat label="Sizing Disagreements" value={String(disagreements.length)} />
            <ToolbarStat label="Challenge Items" value={String(challenges.length)} />
            <ToolbarStat label="Evidence Pointers" value={String(evidenceIndex.length)} />
          </div>
        </section>

        <section className="content-grid">
          <article className="panel panel-span-two">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Change Brief</span>
                <h3>Material Movers</h3>
              </div>
              <div className="panel-meta">
                {materialMovers.length} rows
              </div>
            </div>
            <div className="table-scroll">
              <table className="review-table">
                <thead>
                  <tr>
                    <th>ACID</th>
                    <th>Type</th>
                    <th>Active</th>
                    <th>Target</th>
                    <th>Benchmark</th>
                    <th>VIR STF</th>
                    <th>Rank Change</th>
                    <th>Narrative</th>
                  </tr>
                </thead>
                <tbody>
                  {materialMovers.map((item) => (
                    <tr key={`${selectedFund.slug}-${item.acid}`}>
                      <td>
                        <strong>{item.acid}</strong>
                      </td>
                      <td>{acidTypeLabels[item.acid_type] ?? item.acid_type}</td>
                      <td className={toneForNumber(item.active_rolled_exposure)}>
                        {formatNumber(item.active_rolled_exposure)}
                      </td>
                      <td>{formatNumber(item.target_rolled_exposure)}</td>
                      <td>{formatNumber(item.benchmark_rolled_exposure)}</td>
                      <td>{formatNumber(item.vir_stf)}</td>
                      <td>{formatInteger(item.vir_rank_change_by_stf)}</td>
                      <td>{item.narrative}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Sizing Considerations</span>
                <h3>Agreement Signals</h3>
              </div>
              <div className="panel-meta">{agreements.length} rows</div>
            </div>
            <NarrativeList items={agreements} emptyMessage="No agreement rows match the current search." />
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Sizing Considerations</span>
                <h3>Disagreement Signals</h3>
              </div>
              <div className="panel-meta">{disagreements.length} rows</div>
            </div>
            <NarrativeList items={disagreements} emptyMessage="No disagreement rows match the current search." />
          </article>

          <article className="panel panel-span-two">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Challenge Brief</span>
                <h3>Triggered Review Items</h3>
              </div>
              <div className="panel-meta">{challenges.length} rows</div>
            </div>
            {challenges.length ? (
              <div className="challenge-grid">
                {challenges.map((item) => (
                  <div key={item.trigger_candidate_id} className="challenge-card">
                    <div className="challenge-topline">
                      <span className="challenge-acid">{item.acid}</span>
                      <span className="challenge-trigger">{item.trigger_type}</span>
                    </div>
                    <p className="challenge-text">{item.challenge}</p>
                    <p className="challenge-detail">{item.disagreement_statement}</p>
                    <dl className="challenge-stats">
                      <div>
                        <dt>Active</dt>
                        <dd>{formatNumber(item.position_summary?.active_rolled_exposure)}</dd>
                      </div>
                      <div>
                        <dt>Target</dt>
                        <dd>{formatNumber(item.position_summary?.target_rolled_exposure)}</dd>
                      </div>
                      <div>
                        <dt>Benchmark</dt>
                        <dd>{formatNumber(item.position_summary?.benchmark_rolled_exposure)}</dd>
                      </div>
                    </dl>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState copy="No fired challenge items for this fund under the current trigger rules." />
            )}
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Run Summary</span>
                <h3>Quick Readout</h3>
              </div>
            </div>
            <pre className="markdown-block">{selectedFund?.run_summary_markdown}</pre>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Evidence + Sources</span>
                <h3>Hash + Pointer Index</h3>
              </div>
            </div>
            <div className="subpanel">
              <h4>Source file hashes</h4>
              <ul className="hash-list">
                {sourceHashes.map(([path, hash]) => (
                  <li key={path}>
                    <span>{path}</span>
                    <code>{hash.slice(0, 16)}...</code>
                  </li>
                ))}
              </ul>
            </div>
            <div className="subpanel">
              <h4>Evidence pointers</h4>
              <ul className="evidence-list">
                {evidenceIndex.slice(0, 24).map((pointer) => (
                  <li key={`${pointer.artifact_path}-${pointer.row_id}`}>
                    <code>{pointer.row_id}</code>
                    <span>{pointer.artifact_path}</span>
                  </li>
                ))}
              </ul>
              {evidenceIndex.length > 24 ? (
                <p className="support-copy">
                  Showing the first 24 evidence pointers out of {evidenceIndex.length}.
                </p>
              ) : null}
            </div>
          </article>
        </section>
      </main>
    </div>
  )
}

function MetricCard({ label, value, subvalue, tone }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{subvalue}</small>
    </article>
  )
}

function MiniMetric({ label, value }) {
  return (
    <div className="mini-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ToolbarStat({ label, value }) {
  return (
    <div className="toolbar-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Chip({ label, subtle = false }) {
  return <span className={`chip ${subtle ? 'is-subtle' : ''}`}>{label}</span>
}

function NarrativeList({ items, emptyMessage }) {
  if (!items.length) {
    return <EmptyState copy={emptyMessage} />
  }

  return (
    <div className="narrative-list">
      {items.map((item, index) => (
        <div key={`${item.acid}-${item.perspective ?? index}`} className="narrative-card">
          <div className="narrative-topline">
            <strong>{item.acid}</strong>
            {item.perspective ? <span>{item.perspective}</span> : null}
          </div>
          <p>{item.narrative}</p>
        </div>
      ))}
    </div>
  )
}

function EmptyState({ copy }) {
  return <p className="empty-state">{copy}</p>
}

function filterItems(items, query, formatter) {
  if (!query) {
    return items
  }
  return items.filter((item) => formatter(item).includes(query))
}

function materialMoverText(item) {
  return `${item.acid} ${item.acid_type} ${item.narrative}`.toLowerCase()
}

function sizingText(item) {
  return `${item.acid} ${item.perspective ?? ''} ${item.narrative}`.toLowerCase()
}

function challengeText(item) {
  return `${item.acid} ${item.trigger_type} ${item.challenge} ${item.disagreement_statement}`.toLowerCase()
}

function toneForNumber(value) {
  if (value == null) {
    return ''
  }
  if (value > 0) {
    return 'is-positive'
  }
  if (value < 0) {
    return 'is-negative'
  }
  return ''
}

function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return '—'
  }
  return Number(value).toFixed(4)
}

function formatInteger(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return '—'
  }
  return String(Math.round(Number(value)))
}

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return '—'
  }
  return `${(Number(value) * 100).toFixed(1)}%`
}
