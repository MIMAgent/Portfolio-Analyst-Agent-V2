import { useEffect, useMemo, useState } from 'react'
import bundle from './data/monthlyReviewBundle.json'
import exposureLineage from './data/exposureLineage.json'
import fundWeightsVirAlgo from './data/fundWeightsVirAlgo.json'

const tabs = [
  { id: 'dashboard', label: 'Overview' },
  { id: 'challenges', label: 'Challenge Brief' },
  { id: 'decomp', label: 'VIR Decomp' },
  { id: 'fof', label: 'Fund of Funds' },
  { id: 'ic-prep', label: 'IC Prep' },
  { id: 'memory', label: 'Agent Memory' },
]

const categoryOrder = [
  'Eq Size / Style',
  'Eq Sector',
  'Country',
  'Region',
  'Fixed Income',
  'Cash',
  'Alternatives',
  'Other',
]

const acidTypeLabels = {
  acid_bond: 'Bond',
  acid_country: 'Country',
  acid_region_sector: 'Sector',
}

const presetQuestions = [
  'What are the biggest position-signal gaps right now?',
  'Which tensions should go into next month watch list?',
  'Where are active weights concentrated by source sleeve?',
]

export default function App() {
  const fundDirectory = useMemo(() => buildFundDirectory(bundle.funds, fundWeightsVirAlgo), [])
  const [selectedSlug, setSelectedSlug] = useState(fundDirectory[0]?.slug ?? '')
  const [activeTab, setActiveTab] = useState('dashboard')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedAcid, setSelectedAcid] = useState('')
  const [portfolioView, setPortfolioView] = useState('new')

  const selectedFund = fundDirectory.find((fund) => fund.slug === selectedSlug) ?? fundDirectory[0]
  const model = useMemo(() => buildFundModel(selectedFund), [selectedFund])
  const filteredModel = useMemo(() => filterModelByCategory(model, selectedCategory), [model, selectedCategory])
  const pageTitle = tabs.find((tab) => tab.id === activeTab)?.label ?? 'Overview'

  useEffect(() => {
    if (!filteredModel.exposures.length) {
      return
    }
    if (!filteredModel.exposureByAcid.has(selectedAcid)) {
      setSelectedAcid(filteredModel.exposures[0].acid)
    }
  }, [filteredModel.exposureByAcid, filteredModel.exposures, selectedAcid])

  const focusedRow =
    filteredModel.exposureByAcid.get(selectedAcid) ??
    filteredModel.tensionRows[0] ??
    filteredModel.signalRows[0] ??
    filteredModel.exposures[0] ??
    null

  const focusAcid = (acid, nextTab = null) => {
    if (acid) {
      setSelectedAcid(acid)
    }
    if (nextTab) {
      setActiveTab(nextTab)
    }
  }

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <div className="viewport-guard">
        <strong>Best viewed on a wider screen.</strong>
        <span>This workspace is tuned for desktop review and committee prep.</span>
      </div>

      <div className="shell">
        <div className="topbar">
          <div className="logo">
            <div className="logo-mark">PM</div>
            Analyst Agent
          </div>
          <div className="tb-sep" />
          <span className="tb-chip live">Live</span>
          <span className="tb-chip">{monthYear(bundle.snapshot_date || model.snapshotMatrix.review)}</span>
          <span className="tb-chip">{fundDirectory.length} Funds</span>
          <div className="tb-sep" />
          <span className="tb-fund-name">{selectedFund?.fund ?? 'No fund selected'}</span>
          <div className="tb-right">
            <button type="button" className="tb-btn primary" onClick={() => setActiveTab('decomp')}>Run Review</button>
            <button type="button" className="tb-btn" onClick={() => setActiveTab('ic-prep')}>IC Prep</button>
          </div>
        </div>

        <aside className="sidebar">
          <div className="sb-header">
            <div className="sb-header-title">PM Analyst Platform</div>
            <div className="sb-header-subtitle">VIR / Algo / Positioning</div>
          </div>

          <div className="sb-label">Navigate</div>
          <nav className="sidebar-nav" aria-label="Workspace sections">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`nav-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>

          <div className="sb-label">Funds</div>
          <div className="sb-scroll">
            {fundDirectory.map((fund) => (
              <button
                key={fund.slug}
                type="button"
                className={`fund-btn ${selectedSlug === fund.slug ? 'active' : ''}`}
                onClick={() => setSelectedSlug(fund.slug)}
              >
                <div className={`fund-dot ${fund.statusDot}`} />
                <span className="fund-btn-name">{fund.fund}</span>
                <span className={`fund-type ${fund.typeClass}`}>{fund.typeLabel}</span>
              </button>
            ))}
          </div>

          <div className="sidebar-footer">
            <SidebarMeta label="Review" value={model.snapshotMatrix.review} />
            <SidebarMeta label="VIR" value={model.snapshotMatrix.vir} />
            <SidebarMeta label="Algo" value={model.snapshotMatrix.algo} />
            <SidebarMeta label="Bundle built" value={formatDateTime(bundle.bundle_generated_at)} />
          </div>
        </aside>

        <div className="main-col">
          <div className="fund-tabs">
            {[
              { id: 'new', label: 'New Portfolio' },
              { id: 'target', label: 'Target Portfolio' },
              { id: 'bench', label: 'Benchmark' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`ftab ${portfolioView === tab.id ? 'active' : ''}`}
                onClick={() => setPortfolioView(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="sec-tabs">
            {tabs.map((tab) => {
              const badge = tabBadgeForModel(tab.id, filteredModel)
              return (
                <button
                  key={tab.id}
                  type="button"
                  className={`stab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                  {badge ? <span className={`stab-badge ${badge.info ? 'info' : ''}`}>{badge.label}</span> : null}
                </button>
              )
            })}
          </div>

          <main id="main-content" className="content">
            <div className="page-header">
              <div>
                <div className="page-title">{pageTitle}</div>
                <div className="page-subtitle">
                  {selectedFund?.fund} | review {model.snapshotMatrix.review || '-'} | positions {model.snapshotMatrix.positioning || '-'} | VIR {model.snapshotMatrix.vir || '-'} | algo {model.snapshotMatrix.algo || '-'}
                </div>
              </div>
              <div className="page-flags">
                <StatusBadge tone={filteredModel.summary.urgentCount ? 'amber' : 'green'}>
                  {filteredModel.summary.urgentCount ? `${filteredModel.summary.urgentCount} urgent` : 'No urgent flags'}
                </StatusBadge>
                {filteredModel.snapshotMatrix.hasMismatch ? (
                  <StatusBadge tone="blue">Snapshot mismatch</StatusBadge>
                ) : null}
              </div>
            </div>

            <div className="filter-row">
              <span className="mini-label">CATEGORY</span>
              <div className="chip-row">
                {['All', ...model.availableCategories].map((category) => (
                  <button
                    key={category}
                    type="button"
                    className={`filter-chip ${selectedCategory === category ? 'is-active' : ''}`}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {activeTab === 'dashboard' ? (
              <DashboardTab model={filteredModel} onFocusAcid={focusAcid} portfolioView={portfolioView} />
            ) : null}
            {activeTab === 'challenges' ? (
              <ChallengeBriefTab model={filteredModel} onOpenReview={(acid) => focusAcid(acid, 'ic-prep')} />
            ) : null}
            {activeTab === 'decomp' ? (
              <SignalLensTab model={filteredModel} focusedRow={focusedRow} onFocusAcid={focusAcid} />
            ) : null}
            {activeTab === 'fof' ? <LookThroughTab model={filteredModel} /> : null}
            {activeTab === 'ic-prep' ? <ICPrepTab model={filteredModel} focusedAcid={focusedRow?.acid ?? ''} /> : null}
            {activeTab === 'memory' ? <MemoryTab model={filteredModel} /> : null}
          </main>
        </div>
      </div>
    </>
  )
}

function DashboardTab({ model, onFocusAcid, portfolioView }) {
  const portfolio = getPortfolioViewMeta(model, portfolioView)
  const rows = model.exposures
    .filter((row) => Math.abs(numberOrNull(row[portfolio.field]) ?? 0) >= portfolio.minimum)
    .slice(0, 18)

  return (
    <div className="page-grid">
      <div className="metric-grid">
        <MetricTile label="POSITIONS" value={String(model.summary.positionCount)} sublabel={`${model.summary.equityCount} eq | ${model.summary.bondCount} bond`} />
        <MetricTile label="MISALIGNED" value={String(model.summary.misalignedCount)} sublabel="vs VIR signal" tone="red" />
        <MetricTile label="ALIGNED" value={String(model.summary.alignedCount)} sublabel="confirmed" tone="green" />
        <MetricTile label="URGENT" value={String(model.summary.urgentCount)} sublabel="needs IC" tone="amber" />
        <MetricTile label={portfolio.kpiLabel} value={portfolio.kpiValue} sublabel={portfolio.kpiSublabel} tone="blue" />
      </div>

      <div className="split-grid split-dashboard">
        <Card title={portfolio.cardTitle} subtitle={`${model.fundName} | ${portfolio.snapshotLabel}`}>
          {rows.length ? (
            <div className="bar-list" role="img" aria-label="Top active weights vs benchmark">
              {rows.map((row) => (
                <button key={row.acid} type="button" className="bar-row" onClick={() => onFocusAcid(row.acid, 'decomp')}>
                  <div className="bar-row-label">
                    <strong>{truncate(row.acid, 22)}</strong>
                    <span>{portfolio.detail(row)}</span>
                  </div>
                  <div className="bar-track">
                    {portfolio.mode === 'centered' ? <div className="bar-zero" /> : null}
                    <span
                      className={`bar-fill ${portfolio.fillClass(row[portfolio.field])}`}
                      style={portfolio.style(row[portfolio.field])}
                    />
                  </div>
                  <code className={portfolio.tone(row[portfolio.field])}>{formatWeight(row[portfolio.field])}</code>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState copy={portfolio.emptyCopy} />
          )}
        </Card>

        <Card title="SIGNAL COVERAGE" subtitle="VIR / algo join status">
          <CoverageBlock title="VIR join status" counts={model.coverageBreakdown.vir} />
          <CoverageBlock title="Algo join status" counts={model.coverageBreakdown.algo} />
          <p className="card-note">
            Bond ACIDs can legitimately show missing VIR or missing algo when the source snapshot only carries rolled exposure detail.
          </p>
        </Card>
      </div>

      <Card title="TOP MISALIGNMENTS" subtitle="position vs VIR direction">
        {model.tensionRows.length ? (
          <div className="data-table">
            <div className="table-row is-head">
              <span>ACID</span>
              <span>Type</span>
              <span className="align-right">Active</span>
              <span className="align-right">VIR STF</span>
              <span className="align-right">Δ VIR</span>
              <span className="align-right">Status</span>
            </div>
            {model.tensionRows.slice(0, 10).map((row) => {
              const status = classifyAlignment(row)
              return (
                <button key={row.acid} type="button" className="table-row table-button" onClick={() => onFocusAcid(row.acid, 'decomp')}>
                  <strong>{row.acid}</strong>
                  <span>{acidTypeLabels[row.acid_type] ?? humanizeKey(row.acid_type)}</span>
                  <code className={`align-right ${toneClass(row.active_rolled_exposure)}`}>{formatWeight(row.active_rolled_exposure)}</code>
                  <code className="align-right">{formatMaybe(row.vir_stf)}</code>
                  <code className={`align-right ${toneClass(row.vir_delta_stf)}`}>{formatSignedMaybe(row.vir_delta_stf)}</code>
                  <span className="align-right">
                    <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                  </span>
                </button>
              )
            })}
          </div>
        ) : (
          <EmptyState copy="No misalignments flagged for this fund." />
        )}
      </Card>

      <div className="split-grid split-dashboard">
        <Card title="SAVED PM REVIEW" subtitle="latest detailed agent narrative">
          {model.reviewSections.length ? (
            <div className="review-preview">
              {model.reviewSections.slice(0, 2).map((section) => (
                <article key={section.title} className="preview-section">
                  <h4>{section.title}</h4>
                  {section.preview.length ? section.preview.map((line, index) => <p key={`${section.title}-${index}`}>{line}</p>) : <p>No preview text available.</p>}
                </article>
              ))}
            </div>
          ) : (
            <EmptyState copy="No saved PM review is available for this run." />
          )}
        </Card>

        <Card title="DATA TIMING" subtitle="actual bundle sources">
          <div className="timing-list">
            <TimingRow label="Review snapshot" value={model.snapshotMatrix.review} />
            <TimingRow label="Positioning layer" value={model.snapshotMatrix.positioning} />
            <TimingRow label="VIR layer" value={model.snapshotMatrix.vir} />
            <TimingRow label="Algo layer" value={model.snapshotMatrix.algo} />
            <TimingRow label="Bundle built" value={formatDateTime(bundle.bundle_generated_at)} />
          </div>
          {model.snapshotMatrix.hasMismatch ? (
            <div className="inline-note tone-blue">
              The saved PM review and the structured exposure layer are not from the same snapshot. The narrative is current to the review run; the tables reflect the latest structured positioning file currently bundled into the app.
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  )
}

function ChallengeBriefTab({ model, onOpenReview }) {
  const cards = buildChallengeCards(model)
  const groups = {
    urgent: cards.filter((card) => card.severity === 'urgent'),
    watch: cards.filter((card) => card.severity === 'watch'),
    review: cards.filter((card) => card.severity === 'review'),
  }

  if (!cards.length) {
    return <EmptyState copy="No active challenge cards are available for this fund." />
  }

  return (
    <div className="page-grid">
      <Card title="CHALLENGE BRIEF" subtitle="severity blends active size with signal drift">
        <p className="card-note">
          Severity is anchored to active weight, signal opposition, and month-over-month VIR movement. Where the saved bundle has no explicit challenge rows, the app synthesizes a review queue from the strongest current position-signal tensions.
        </p>
      </Card>

      {[
        ['urgent', 'URGENT', 'red'],
        ['watch', 'WATCH', 'amber'],
        ['review', 'REVIEW', 'blue'],
      ].map(([key, label, tone]) => (
        <section key={key} className="severity-section">
          <div className={`severity-label tone-${tone}`}>{label} · {groups[key].length}</div>
          {groups[key].length ? (
            <div className="challenge-stack">
              {groups[key].map((card) => (
                <article key={card.id} className={`challenge-card tone-${tone}`}>
                  <div className="challenge-top">
                    <div>
                      <div className="challenge-title">{card.acid}</div>
                      <div className="challenge-meta">{model.fundName}</div>
                    </div>
                    <div className="challenge-actions">
                      <StatusBadge tone={tone}>{label}</StatusBadge>
                      <button type="button" className="btn btn-primary" onClick={() => onOpenReview(card.acid)}>
                        Saved review
                      </button>
                    </div>
                  </div>

                  <p className="challenge-summary">{card.summary}</p>

                  <div className="challenge-numbers">
                    <span>
                      <label>Active</label>
                      <code className={toneClass(card.row.active_rolled_exposure)}>{formatWeight(card.row.active_rolled_exposure)}</code>
                    </span>
                    <span>
                      <label>VIR STF</label>
                      <code>{formatMaybe(card.row.vir_stf)}</code>
                    </span>
                    <span>
                      <label>Δ VIR</label>
                      <code className={toneClass(card.row.vir_delta_stf)}>{formatSignedMaybe(card.row.vir_delta_stf)}</code>
                    </span>
                    <span>
                      <label>Algo active</label>
                      <code>{formatMaybe(card.row.algo_active_weight)}</code>
                    </span>
                  </div>

                  <p className="challenge-detail">{card.detail}</p>

                  {card.sources.length ? (
                    <div className="source-line">
                      <span>Sourced from:</span>
                      <strong>{card.sources.join('; ')}</strong>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <EmptyState copy={`No ${label.toLowerCase()} items for this fund.`} />
          )}
        </section>
      ))}
    </div>
  )
}

function SignalLensTab({ model, focusedRow, onFocusAcid }) {
  if (!model.signalRows.length) {
    return <EmptyState copy="This fund does not have enough VIR or algo-linked rows to build a signal lens." />
  }

  const movers = [...model.signalRows]
    .filter((row) => row.vir_delta_stf != null)
    .sort((a, b) => Math.abs(numberOrNull(b.vir_delta_stf) ?? 0) - Math.abs(numberOrNull(a.vir_delta_stf) ?? 0))
    .slice(0, 15)

  const selected = model.signalRows.find((row) => row.acid === focusedRow?.acid) ?? movers[0] ?? model.signalRows[0]
  const previousVir = previousValue(selected?.vir_stf, selected?.vir_delta_stf)
  const previousAlgo = previousValue(selected?.algo_active_weight, selected?.algo_active_weight_mom)
  const rowStatus = classifyAlignment(selected)
  const moverNarrative = model.moverByAcid.get(selected?.acid)?.narrative
  const moverTakeaway = model.moverByAcid.get(selected?.acid)?.pm_takeaway

  return (
    <div className="page-grid">
      <Card title="VIR TOP MOVERS" subtitle={`Delta STF | ${model.snapshotMatrix.review}`}>
        {movers.length ? (
          <div className="mover-bars" role="img" aria-label="Top VIR movers">
            {movers.map((row) => (
              <button key={row.acid} type="button" className={`mover-bar ${selected?.acid === row.acid ? 'is-selected' : ''}`} onClick={() => onFocusAcid(row.acid)}>
                <span>{truncate(row.acid, 18)}</span>
                <div className="mini-track">
                  <span className={`mini-fill ${numberOrNull(row.vir_delta_stf) >= 0 ? 'is-positive' : 'is-negative'}`} style={centeredBarStyle(row.vir_delta_stf, model.maxVirDelta)} />
                </div>
                <code className={toneClass(row.vir_delta_stf)}>{formatSignedMaybe(row.vir_delta_stf)}</code>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState copy="No VIR movers were captured for this fund." />
        )}
      </Card>

      <div className="split-grid split-signal">
        <Card title="SELECTED SIGNAL" subtitle={selected?.acid || 'No ACID selected'}>
          {selected ? (
            <>
              <div className="metric-grid compact">
                <MetricTile label="ACTIVE" value={formatWeight(selected.active_rolled_exposure)} tone={toneFromNumber(selected.active_rolled_exposure)} compact />
                <MetricTile label="TARGET" value={formatWeight(selected.fund_target_rolled_exposure)} compact />
                <MetricTile label="BENCH" value={formatWeight(selected.fund_benchmark_rolled_exposure)} compact />
                <MetricTile label="VIR STF" value={formatMaybe(selected.vir_stf)} compact />
                <MetricTile label="DELTA VIR" value={formatSignedMaybe(selected.vir_delta_stf)} tone={toneFromNumber(selected.vir_delta_stf)} compact />
                <MetricTile label="ALGO" value={formatMaybe(selected.algo_active_weight)} compact />
              </div>

              <div className="stacked-meters">
                <MeterRow label="Position vs benchmark" value={selected.active_rolled_exposure} maxValue={model.maxExposureActive} />
                <MeterRow label="VIR now" value={selected.vir_stf} maxValue={signalScale(model.signalRows, 'vir_stf')} />
                <MeterRow label="Algo active" value={selected.algo_active_weight} maxValue={signalScale(model.signalRows, 'algo_active_weight')} />
              </div>

              <div className="inline-note tone-neutral">{describeSignalRow(selected)}</div>
            </>
          ) : (
            <EmptyState copy="Choose a mover to inspect its current signal state." />
          )}
        </Card>

        <Card title="NOW VS PRIOR" subtitle="derived from current values plus MoM deltas">
          {selected ? (
            <>
              <div className="now-prior-table">
                <NowPriorRow label="VIR STF" previous={previousVir} current={selected.vir_stf} />
                <NowPriorRow label="Algo active" previous={previousAlgo} current={selected.algo_active_weight} />
                <NowPriorRow label="Rank change" previous={null} current={selected.vir_rank_change_by_stf} suffix="" signed />
                <NowPriorRow label="Join status" previous={selected.vir_join_status || '-'} current={selected.algo_join_status || '-'} text />
              </div>

              <div className={`inline-note tone-${rowStatus.tone}`}>{rowStatus.explanation}</div>

              <div className="context-list">
                {model.categoryTrendRows.slice(0, 5).map((row) => (
                  <div key={row.category} className="context-row">
                    <strong>{row.category}</strong>
                    <span>{row.relationshipLabel}</span>
                    <code className={toneClass(row.positionNet)}>{formatWeight(row.positionNet)}</code>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <EmptyState copy="No signal row selected." />
          )}
        </Card>
      </div>

      <Card title="AGENT DIRECTIONAL VIEW" subtitle="saved review text + structured exposure read">
        {selected ? (
          <div className="directional-view">
            <p>{moverTakeaway || moverNarrative || describeSignalRow(selected)}</p>
            {selected.signalOpposed ? (
              <div className="inline-note tone-amber">
                Positioning and VIR still point in opposite directions. That does not automatically make the exposure wrong, but it does mean the PM rationale should be explicit.
              </div>
            ) : null}
            <div className="preset-grid">
              {presetQuestions.map((question) => (
                <button key={question} type="button" className="btn btn-default">
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <EmptyState copy="No directional view is available." />
        )}
      </Card>
    </div>
  )
}

function LookThroughTab({ model }) {
  const rows = model.exposures.filter((row) => model.lineageByAcid[row.acid] && Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0.3)

  if (!rows.length) {
    return <EmptyState copy="No expandable look-through rows are available for this fund." />
  }

  return (
    <div className="page-grid">
      <Card title="FUND OF FUNDS LOOK-THROUGH" subtitle="active weights explained by underlying sleeves and names">
        <p className="card-note">
          These active weights are rolled from underlying sources. Expand a row to see the names and sleeve paths contributing to the exposure.
        </p>
      </Card>

      <div className="accordion-stack">
        {rows.map((row) => (
          <LookThroughRow key={row.acid} row={row} lineage={model.lineageByAcid[row.acid]} />
        ))}
      </div>
    </div>
  )
}

function ICPrepTab({ model, focusedAcid }) {
  const prepItems = buildIcPrepItems(model)

  return (
    <div className="page-grid">
      <Card title="IC PREP" subtitle="committee-ready talking points and saved PM review context">
        <div className="meta-ribbon">
          <span>Fund {model.fundName}</span>
          <span>Snapshot {model.snapshotMatrix.review}</span>
          <span>Run {model.metadata.review_run_id || model.reviewRunId || '-'}</span>
          {focusedAcid ? <span>Focus {focusedAcid}</span> : null}
        </div>
      </Card>

      {prepItems.length ? (
        <Card title="KEY DISCUSSION POINTS" subtitle="auto-built from positioning, VIR, and saved review signals">
          <div className="ic-stack">
            {prepItems.map((item, index) => (
              <article key={`${item.acid}-${index}`} className="ic-card">
                <div className="ic-header">
                  <div className="ic-num">{String(index + 1).padStart(2, '0')}</div>
                  <div>
                    <div className="ic-title">{item.title}</div>
                    <StatusBadge tone={item.tone}>{item.label}</StatusBadge>
                  </div>
                </div>
                <div className="ic-body">{item.body}</div>
                <div className="ic-evidence">
                  {item.evidence.map((chip) => (
                    <span key={chip} className="ic-ev-chip">{chip}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </Card>
      ) : null}

      {model.reviewSections.length ? (
        model.reviewSections.map((section) => (
          <Card key={section.title} title={section.title.toUpperCase()} subtitle={section.subtitle || ''}>
            <ReviewSectionBlocks section={section} focusAcid={focusedAcid} />
          </Card>
        ))
      ) : (
        <EmptyState copy="No saved PM review is available for this run." />
      )}

      <Card title="ARTIFACT PATHS" subtitle="repo locations saved with this run">
        <div className="artifact-table">
          {Object.entries(model.artifactPaths).map(([key, value]) => (
            <div key={key} className="artifact-row">
              <span>{humanizeKey(key)}</span>
              <code>{value || '-'}</code>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function MemoryTab({ model }) {
  const memoryUpdates = model.changeBrief.memory_updates_summary ?? {}
  const evidence = model.changeBrief.evidence_index ?? []

  return (
    <div className="page-grid">
      <div className="split-grid split-memory">
        <Card title="ACTIVE BELIEFS" subtitle="bundle memory summary">
          <div className="memory-summary-grid">
            <MiniStat label="Theses" value={String(memoryUpdates.thesis_ledger_entries ?? model.memorySummary.thesis_ledger_count ?? 0)} />
            <MiniStat label="Exceptions" value={String(memoryUpdates.approved_exceptions ?? model.memorySummary.exceptions_count ?? 0)} />
            <MiniStat label="Watch items" value={String(memoryUpdates.watch_items ?? model.memorySummary.watch_items_count ?? 0)} />
            <MiniStat label="Proposed" value={String(memoryUpdates.proposed_count_from_prior_run ?? model.memorySummary.proposed_count ?? 0)} />
          </div>
          <div className="inline-note tone-neutral">
            This bundle carries summary-level memory counts rather than the full persistent ledger rows. The current app surfaces what is available without inventing detail that is not in the saved run.
          </div>
        </Card>

        <Card title="OPEN CHALLENGES" subtitle="run-level pressure points">
          <div className="memory-summary-grid">
            <MiniStat label="Fired triggers" value={String(model.triggerSummary.fired_count ?? model.changeBrief.triggers_fired_summary?.fired_count ?? 0)} tone="red" />
            <MiniStat label="Borderline" value={String(model.triggerSummary.borderline_count ?? 0)} tone="amber" />
            <MiniStat label="Challenge rows" value={String(model.challenges.length)} tone="blue" />
            <MiniStat label="Evidence rows" value={String(evidence.length)} />
          </div>
          <div className="inline-note tone-blue">
            When the bundle includes full challenge objects, they appear in Challenge Brief. When it does not, the evidence index and signal tables still show where the agent pulled support.
          </div>
        </Card>
      </div>

      <Card title="EVIDENCE INDEX" subtitle="saved sources cited by the run">
        {evidence.length ? (
          <div className="data-table">
            <div className="table-row is-head">
              <span>Artifact</span>
              <span>Row ID</span>
            </div>
            {evidence.map((item, index) => (
              <div key={`${item.artifact_path}-${item.row_id}-${index}`} className="table-row">
                <code>{item.artifact_path}</code>
                <code>{item.row_id}</code>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState copy="No evidence index was saved for this run." />
        )}
      </Card>
    </div>
  )
}

function LookThroughRow({ row, lineage }) {
  const [open, setOpen] = useState(false)

  return (
    <article className="lookthrough-card">
      <button type="button" className="lookthrough-head" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <div className="lookthrough-left">
          <span className="chevron">{open ? '▼' : '▶'}</span>
          <div>
            <strong>{row.acid}</strong>
            <span>{acidTypeLabels[row.acid_type] ?? humanizeKey(row.acid_type)}</span>
          </div>
        </div>

        <div className="lookthrough-right">
          <span>{lineage?.securityCount ?? 0} securities</span>
          <span>tgt {formatWeight(row.fund_target_rolled_exposure)}</span>
          <span>bmk {formatWeight(row.fund_benchmark_rolled_exposure)}</span>
          <code className={toneClass(row.active_rolled_exposure)}>{formatWeight(row.active_rolled_exposure)}</code>
        </div>
      </button>

      {open ? (
        <div className="lookthrough-body">
          {lineage?.securities?.length ? (
            <div className="detail-table">
              <div className="table-row is-head">
                <span>Security</span>
                <span>Account</span>
                <span>Path</span>
                <span className="align-right">Target</span>
                <span className="align-right">Contribution</span>
              </div>
              {lineage.securities.slice(0, 30).map((security) => {
                const source = security.sources?.[0] ?? {}
                return (
                  <div key={security.identifier} className="table-row">
                    <strong>{security.securityName}</strong>
                    <span>{source.portcode || '-'}</span>
                    <span>{source.path || '-'}</span>
                    <code className="align-right">{formatWeight(security.targetContribution)}</code>
                    <code className={`align-right ${toneClass(security.activeContribution)}`}>{formatWeight(security.activeContribution)}</code>
                  </div>
                )
              })}
            </div>
          ) : (
            <EmptyState copy="No underlying security detail was saved for this exposure." />
          )}
        </div>
      ) : null}
    </article>
  )
}

function buildFundDirectory(reviewFunds = [], exposureRows = []) {
  const reviewByFund = new Map(reviewFunds.map((fund) => [fund.fund, fund]))
  const fundNames = [...new Set([...reviewFunds.map((fund) => fund.fund), ...exposureRows.map((row) => row.fund)])].sort()

  return fundNames.map((fundName) => {
    const reviewFund = reviewByFund.get(fundName) ?? { fund: fundName }
    const rows = exposureRows.filter((row) => row.fund === fundName).map(normalizeExposureRow)
    const urgentCount = rows.filter((row) => classifyAlignment(row).key === 'opposite').length
    const watchCount = rows.filter((row) => classifyAlignment(row).key === 'drifting').length
    const fundType = inferFundType(fundName)

    return {
      ...reviewFund,
      fund: fundName,
      slug: slugify(fundName),
      typeLabel: fundType.label,
      typeClass: fundType.className,
      statusDot: urgentCount ? 'dot-red' : watchCount ? 'dot-amber' : reviewByFund.has(fundName) ? 'dot-green' : 'dot-muted',
    }
  })
}

function inferFundType(fundName = '') {
  if (/Bond|Municipal|Total Return/i.test(fundName)) {
    return { label: 'FI', className: 'ft-fi' }
  }
  if (/Income|Alternatives/i.test(fundName)) {
    return { label: 'MA', className: 'ft-ma' }
  }
  return { label: 'EQ', className: 'ft-eq' }
}

function tabBadgeForModel(tabId, model) {
  if (tabId === 'challenges') {
    const count = buildChallengeCards(model).length
    return count ? { label: String(count) } : null
  }
  if (tabId === 'ic-prep') {
    const count = buildIcPrepItems(model).length
    return count ? { label: String(count), info: true } : null
  }
  return null
}

function getPortfolioViewMeta(model, portfolioView) {
  if (portfolioView === 'target') {
    const maxValue = Math.max(...model.exposures.map((row) => Math.abs(numberOrNull(row.fund_target_rolled_exposure) ?? 0)), 1)
    const topName = model.exposures
      .slice()
      .sort((a, b) => (numberOrNull(b.fund_target_rolled_exposure) ?? 0) - (numberOrNull(a.fund_target_rolled_exposure) ?? 0))[0]?.acid

    return {
      field: 'fund_target_rolled_exposure',
      mode: 'linear',
      minimum: 0.5,
      cardTitle: 'TARGET PORTFOLIO WEIGHTS',
      snapshotLabel: model.snapshotMatrix.positioning,
      kpiLabel: 'TOP TARGET',
      kpiValue: topName ? truncate(topName, 13) : '-',
      kpiSublabel: 'largest target sleeve',
      emptyCopy: 'No target weights >= 0.5% for this fund.',
      detail: (row) => `Bench ${formatWeight(row.fund_benchmark_rolled_exposure)}`,
      style: (value) => linearBarStyle(value, maxValue),
      fillClass: () => 'is-reference',
      tone: () => 'tone-text-blue',
    }
  }

  if (portfolioView === 'bench') {
    const maxValue = Math.max(...model.exposures.map((row) => Math.abs(numberOrNull(row.fund_benchmark_rolled_exposure) ?? 0)), 1)
    const topName = model.exposures
      .slice()
      .sort((a, b) => (numberOrNull(b.fund_benchmark_rolled_exposure) ?? 0) - (numberOrNull(a.fund_benchmark_rolled_exposure) ?? 0))[0]?.acid

    return {
      field: 'fund_benchmark_rolled_exposure',
      mode: 'linear',
      minimum: 0.5,
      cardTitle: 'BENCHMARK WEIGHTS',
      snapshotLabel: model.snapshotMatrix.positioning,
      kpiLabel: 'TOP BENCH',
      kpiValue: topName ? truncate(topName, 13) : '-',
      kpiSublabel: 'largest benchmark sleeve',
      emptyCopy: 'No benchmark weights >= 0.5% for this fund.',
      detail: (row) => `Target ${formatWeight(row.fund_target_rolled_exposure)}`,
      style: (value) => linearBarStyle(value, maxValue),
      fillClass: () => 'is-benchmark',
      tone: () => 'tone-text-green',
    }
  }

  return {
    field: 'active_rolled_exposure',
    mode: 'centered',
    minimum: 0.3,
    cardTitle: 'ACTIVE WEIGHTS VS BENCHMARK',
    snapshotLabel: model.snapshotMatrix.positioning,
    kpiLabel: 'WATCH',
    kpiValue: String(model.summary.watchCount),
    kpiSublabel: 'monitor',
    emptyCopy: 'No active positions >= 0.3% for this fund.',
    detail: (row) => (row.vir_stf != null ? `VIR ${formatMaybe(row.vir_stf)}` : 'No VIR'),
    style: (value) => centeredBarStyle(value, model.maxExposureActive),
    fillClass: (value) => (numberOrNull(value) >= 0 ? 'is-positive' : 'is-negative'),
    tone: toneClass,
  }
}

function buildIcPrepItems(model) {
  return model.tensionRows.slice(0, 4).map((row) => {
    const status = classifyAlignment(row)
    const sources = sourceNamesForAcid(model, row.acid)

    return {
      acid: row.acid,
      title: `${row.acid} | ${status.label}`,
      label: status.key === 'aligned' ? 'Support' : status.label,
      tone: status.tone,
      body: model.moverByAcid.get(row.acid)?.pm_takeaway || model.moverByAcid.get(row.acid)?.narrative || describeSignalRow(row),
      evidence: [
        `Active ${formatWeight(row.active_rolled_exposure)}`,
        `VIR ${formatMaybe(row.vir_stf)}`,
        `Delta ${formatSignedMaybe(row.vir_delta_stf)}`,
        row.category,
        ...(sources.length ? sources.slice(0, 2) : []),
      ],
    }
  })
}

function Card({ title, subtitle, children }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>{title}</h2>
        {subtitle ? <span>{subtitle}</span> : null}
      </div>
      <div className="card-body">{children}</div>
    </section>
  )
}

function MetricTile({ label, value, sublabel, tone = 'neutral', compact = false }) {
  return (
    <article className={`metric-tile tone-${tone} ${compact ? 'is-compact' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {sublabel ? <small>{sublabel}</small> : null}
    </article>
  )
}

function MiniStat({ label, value, tone = 'neutral' }) {
  return (
    <div className={`mini-stat tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function StatusBadge({ children, tone = 'neutral' }) {
  return <span className={`status-badge tone-${tone}`}>{children}</span>
}

function SidebarMeta({ label, value }) {
  return (
    <div className="sidebar-meta-row">
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  )
}

function NavCount({ tabId, model }) {
  const value =
    tabId === 'dashboard'
      ? model.summary.misalignedCount
      : tabId === 'challenges'
        ? buildChallengeCards(model).length
        : tabId === 'decomp'
          ? model.signalRows.length
          : tabId === 'fof'
            ? model.exposures.filter((row) => model.lineageByAcid[row.acid]).length
            : tabId === 'ic-prep'
              ? model.reviewSections.length
              : model.changeBrief.evidence_index?.length ?? 0

  return <span className="nav-count">{value}</span>
}

function CoverageBlock({ title, counts }) {
  return (
    <div className="coverage-block">
      <div className="subhead">{title}</div>
      {Object.entries(counts).length ? (
        <div className="coverage-list">
          {Object.entries(counts).map(([key, value]) => {
            const tone = key.includes('missing') ? 'red' : key.includes('not_applicable') ? 'neutral' : 'green'
            return (
              <div key={key} className="coverage-row">
                <span>{humanizeKey(key)}</span>
                <code className={`tone-text-${tone}`}>{value}</code>
              </div>
            )
          })}
        </div>
      ) : (
        <EmptyState copy="No coverage rows available." />
      )}
    </div>
  )
}

function EmptyState({ copy }) {
  return <div className="empty-state">{copy}</div>
}

function TimingRow({ label, value }) {
  return (
    <div className="timing-row">
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  )
}

function NowPriorRow({ label, previous, current, suffix = '', signed = false, text = false }) {
  const previousText = text ? previous || '-' : signed ? formatSignedMaybe(previous) : `${formatMaybe(previous)}${suffix}`
  const currentText = text ? current || '-' : signed ? formatSignedMaybe(current) : `${formatMaybe(current)}${suffix}`
  return (
    <div className="now-prior-row">
      <span>{label}</span>
      <div>
        <small>Prev</small>
        <code>{previousText}</code>
      </div>
      <div>
        <small>Now</small>
        <code>{currentText}</code>
      </div>
    </div>
  )
}

function MeterRow({ label, value, maxValue }) {
  return (
    <div className="meter-row">
      <span>{label}</span>
      <div className="bar-track">
        <div className="bar-zero" />
        <span
          className={`bar-fill ${numberOrNull(value) >= 0 ? 'is-positive' : 'is-negative'}`}
          style={centeredBarStyle(value, maxValue)}
        />
      </div>
      <code className={toneClass(value)}>{formatMaybe(value)}</code>
    </div>
  )
}

function ReviewSectionBlocks({ section, focusAcid }) {
  return (
    <div className="markdown-blocks">
      {section.blocks.map((block, index) => {
        if (block.type === 'subheading') {
          const active = focusAcid && block.value.includes(focusAcid)
          return (
            <h3 key={`${section.title}-${index}`} className={active ? 'is-focused' : ''}>
              {block.value}
            </h3>
          )
        }
        if (block.type === 'list') {
          return (
            <ul key={`${section.title}-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${section.title}-${index}-${itemIndex}`}>{item}</li>
              ))}
            </ul>
          )
        }
        return <p key={`${section.title}-${index}`}>{block.value}</p>
      })}
    </div>
  )
}

function buildFundModel(fund) {
  const payload = fund?.run_payload ?? {}
  const metadata = payload.review_run_metadata ?? {}
  const snapshot = payload.fund_snapshot_summary ?? {}
  const coverage = snapshot.coverage ?? {}
  const memorySummary = snapshot.memory_summary ?? {}
  const triggerSummary = snapshot.trigger_summary ?? {}
  const changeBrief = payload.change_brief ?? {}
  const challengeBrief = payload.challenge_brief ?? {}
  const fundName = fund?.fund ?? ''

  const exposures = buildExposureRows(fundName)
  const exposureByAcid = new Map(exposures.map((row) => [row.acid, row]))
  const movers = sortMaterialMovers((changeBrief.material_movers ?? []).map((row) => ({ ...exposureByAcid.get(row.acid), ...row })))
  const moverByAcid = new Map(movers.map((row) => [row.acid, row]))
  const challenges = challengeBrief.items ?? []
  const signalRows = exposures
    .filter((row) => row.vir_stf != null || row.algo_active_weight != null)
    .map((row) => {
      const status = classifyAlignment(row)
      const active = numberOrNull(row.active_rolled_exposure) ?? 0
      const algo = numberOrNull(row.algo_active_weight) ?? 0
      return {
        ...row,
        signalGap: active - algo,
        signalOpposed: status.key === 'opposite',
        alignmentLabel: status.label,
        alignmentTone: status.tone,
      }
    })

  const tensionRows = buildTensionRows(signalRows)
  const coverageBreakdown = {
    vir: summarizeStatuses(exposures, 'vir_join_status'),
    algo: summarizeStatuses(exposures, 'algo_join_status'),
  }
  const reviewMarkdown = fund?.detailed_review_markdown || fund?.run_summary_markdown || ''
  const reviewSections = parseReviewMarkdown(reviewMarkdown)
  const snapshotMatrix = {
    review: metadata.snapshot_date || fund?.snapshot_date || bundle.snapshot_date,
    positioning: mostCommon(exposures.map((row) => row.snapshot_date)),
    vir: mostCommon(exposures.map((row) => row.vir_snapshot_date)),
    algo: mostCommon(exposures.map((row) => row.algo_snapshot_date)),
  }
  snapshotMatrix.hasMismatch = [snapshotMatrix.positioning, snapshotMatrix.vir, snapshotMatrix.algo]
    .filter(Boolean)
    .some((value) => value !== snapshotMatrix.review)

  const equityCount = exposures.filter((row) => row.acid_type !== 'acid_bond').length
  const bondCount = exposures.filter((row) => row.acid_type === 'acid_bond').length
  const misalignedRows = signalRows.filter((row) => ['opposite', 'drifting'].includes(classifyAlignment(row).key))
  const alignedRows = signalRows.filter((row) => classifyAlignment(row).key === 'aligned')
  const urgentCount = signalRows.filter((row) => classifyAlignment(row).key === 'opposite').length
  const watchCount = signalRows.filter((row) => classifyAlignment(row).key === 'drifting').length

  return {
    fundName,
    reviewRunId: fund?.review_run_id || metadata.review_run_id || '',
    metadata,
    coverage,
    memorySummary,
    triggerSummary,
    changeBrief,
    challenges,
    exposures,
    exposureByAcid,
    movers,
    moverByAcid,
    signalRows,
    tensionRows,
    maxExposureActive: Math.max(...exposures.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 1),
    maxVirDelta: Math.max(...signalRows.map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 1),
    availableCategories: categoryOrder.filter((category) => exposures.some((row) => row.category === category)),
    lineages: exposureLineage[fundName] ?? {},
    lineageByAcid: exposureLineage[fundName] ?? {},
    coverageBreakdown,
    reviewMarkdown,
    reviewSections,
    artifactPaths: fund?.artifact_paths ?? {},
    summary: {
      positionCount: exposures.length,
      equityCount,
      bondCount,
      misalignedCount: misalignedRows.length,
      alignedCount: alignedRows.length,
      urgentCount,
      watchCount,
    },
    snapshotMatrix,
    evidenceIndex: changeBrief.evidence_index ?? [],
    categoryTrendRows: buildCategoryTrendRows(signalRows),
  }
}

function buildExposureRows(fundName) {
  return fundWeightsVirAlgo
    .filter((row) => row.fund === fundName)
    .map(normalizeExposureRow)
    .sort(compareExposureRows)
}

function normalizeExposureRow(row) {
  return {
    ...row,
    active_rolled_exposure: numberOrNull(row.active_rolled_exposure),
    fund_target_rolled_exposure: numberOrNull(row.fund_target_rolled_exposure),
    fund_benchmark_rolled_exposure: numberOrNull(row.fund_benchmark_rolled_exposure),
    vir_stf: numberOrNull(row.vir_stf),
    vir_delta_stf: numberOrNull(row.vir_delta_stf),
    vir_rank_change_by_stf: numberOrNull(row.vir_rank_change_by_stf),
    algo_active_weight: numberOrNull(row.algo_active_weight),
    algo_active_weight_mom: numberOrNull(row.algo_active_weight_mom),
    category: classifyExposure(row),
  }
}

function filterModelByCategory(model, selectedCategory) {
  if (selectedCategory === 'All') {
    return model
  }

  const exposures = model.exposures.filter((row) => row.category === selectedCategory)
  const allowed = new Set(exposures.map((row) => row.acid))

  return {
    ...model,
    exposures,
    exposureByAcid: new Map(exposures.map((row) => [row.acid, row])),
    movers: model.movers.filter((row) => allowed.has(row.acid)),
    moverByAcid: new Map(model.movers.filter((row) => allowed.has(row.acid)).map((row) => [row.acid, row])),
    challenges: model.challenges.filter((row) => allowed.has(row.acid)),
    signalRows: model.signalRows.filter((row) => allowed.has(row.acid)),
    tensionRows: model.tensionRows.filter((row) => allowed.has(row.acid)),
    lineages: Object.fromEntries(exposures.map((row) => [row.acid, model.lineageByAcid[row.acid]])),
    lineageByAcid: Object.fromEntries(exposures.map((row) => [row.acid, model.lineageByAcid[row.acid]])),
    summary: {
      ...model.summary,
      positionCount: exposures.length,
      equityCount: exposures.filter((row) => row.acid_type !== 'acid_bond').length,
      bondCount: exposures.filter((row) => row.acid_type === 'acid_bond').length,
      misalignedCount: model.signalRows.filter((row) => allowed.has(row.acid) && ['opposite', 'drifting'].includes(classifyAlignment(row).key)).length,
      alignedCount: model.signalRows.filter((row) => allowed.has(row.acid) && classifyAlignment(row).key === 'aligned').length,
      urgentCount: model.signalRows.filter((row) => allowed.has(row.acid) && classifyAlignment(row).key === 'opposite').length,
      watchCount: model.signalRows.filter((row) => allowed.has(row.acid) && classifyAlignment(row).key === 'drifting').length,
    },
    maxExposureActive: Math.max(...exposures.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 1),
    maxVirDelta: Math.max(...model.signalRows.filter((row) => allowed.has(row.acid)).map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 1),
    categoryTrendRows: buildCategoryTrendRows(model.signalRows.filter((row) => allowed.has(row.acid))),
  }
}

function buildTensionRows(rows) {
  const maxGap = Math.max(...rows.map((row) => Math.abs(numberOrNull(row.signalGap) ?? 0)), 1)
  const maxVirMove = Math.max(...rows.map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 0.1)

  return [...rows]
    .map((row) => ({
      ...row,
      tensionScore:
        Math.abs(numberOrNull(row.signalGap) ?? 0) / maxGap +
        Math.abs(numberOrNull(row.vir_delta_stf) ?? 0) / maxVirMove +
        (row.signalOpposed ? 1 : 0),
    }))
    .sort((a, b) => b.tensionScore - a.tensionScore)
}

function sortMaterialMovers(movers) {
  return [...movers].sort(
    (a, b) => Math.abs(numberOrNull(b?.active_rolled_exposure) ?? 0) - Math.abs(numberOrNull(a?.active_rolled_exposure) ?? 0),
  )
}

function buildCategoryTrendRows(rows) {
  return categoryOrder
    .map((category) => {
      const bucket = rows.filter((row) => row.category === category)
      if (!bucket.length) {
        return null
      }
      const positionNet = bucket.reduce((sum, row) => sum + (numberOrNull(row.active_rolled_exposure) ?? 0), 0)
      const virCurrent = average(bucket.map((row) => row.vir_stf))
      const algoCurrent = average(bucket.map((row) => row.algo_active_weight))
      return {
        category,
        positionNet,
        virCurrent,
        algoCurrent,
        relationshipLabel: classifyCategoryRelation(positionNet, virCurrent, algoCurrent),
      }
    })
    .filter(Boolean)
}

function buildChallengeCards(model) {
  if (model.challenges.length) {
    return model.challenges.map((challenge) => {
      const row = model.exposureByAcid.get(challenge.acid) ?? model.moverByAcid.get(challenge.acid) ?? {}
      return {
        id: challenge.trigger_candidate_id || challenge.acid,
        acid: challenge.acid,
        severity: 'urgent',
        row,
        summary: challenge.disagreement_statement || 'Structured challenge raised by the saved bundle.',
        detail: challenge.challenge || describeSignalRow(row),
        sources: sourceNamesForAcid(model, challenge.acid),
      }
    })
  }

  return model.tensionRows.slice(0, 9).map((row, index) => {
    const alignment = classifyAlignment(row)
    return {
      id: `${row.acid}-${index}`,
      acid: row.acid,
      severity: alignment.key === 'opposite' ? 'urgent' : alignment.key === 'drifting' ? 'watch' : 'review',
      row,
      summary: alignment.explanation,
      detail: model.moverByAcid.get(row.acid)?.narrative || describeSignalRow(row),
      sources: sourceNamesForAcid(model, row.acid),
    }
  })
}

function parseReviewMarkdown(markdown) {
  if (!markdown) {
    return []
  }

  const chunks = markdown.split(/\n##\s+/).map((chunk) => chunk.trim()).filter(Boolean)
  return chunks.map((chunk, index) => {
    const normalized = index === 0 ? chunk.replace(/^#\s+.*?\n/, '').trim() : chunk
    const lines = normalized.split('\n').filter((line) => line.trim().length)
    const title = lines.shift() || `Section ${index + 1}`
    const blocks = []
    let pendingList = []

    const flushList = () => {
      if (pendingList.length) {
        blocks.push({ type: 'list', items: pendingList })
        pendingList = []
      }
    }

    for (const line of lines) {
      if (line.startsWith('### ')) {
        flushList()
        blocks.push({ type: 'subheading', value: line.replace(/^###\s+/, '') })
      } else if (line.startsWith('- ')) {
        pendingList.push(line.replace(/^- /, ''))
      } else {
        flushList()
        blocks.push({ type: 'paragraph', value: line })
      }
    }
    flushList()

    const preview = blocks.filter((block) => block.type === 'paragraph').map((block) => block.value).slice(0, 2)
    return { title, blocks, preview }
  })
}

function classifyAlignment(row) {
  const active = numberOrNull(row?.active_rolled_exposure) ?? 0
  const vir = numberOrNull(row?.vir_stf)
  const delta = numberOrNull(row?.vir_delta_stf) ?? 0

  if (vir == null) {
    return {
      key: 'no_signal',
      label: 'No signal',
      tone: 'neutral',
      explanation: 'No VIR signal is available for this row.',
    }
  }
  if (active !== 0 && active * vir < 0) {
    return {
      key: 'opposite',
      label: 'Opposite signal',
      tone: 'red',
      explanation: 'Positioning and VIR are pointing in opposite directions.',
    }
  }
  if ((active > 0 && delta < 0) || (active < 0 && delta > 0)) {
    return {
      key: 'drifting',
      label: active > 0 ? 'OW · falling VIR' : 'UW · rising VIR',
      tone: 'amber',
      explanation: 'The position still lines up directionally, but the signal is moving against the current sizing.',
    }
  }
  if (active === 0 || vir === 0) {
    return {
      key: 'neutral',
      label: 'Neutral',
      tone: 'neutral',
      explanation: 'Neither the position nor the signal is expressing a strong directional view.',
    }
  }
  return {
    key: 'aligned',
    label: 'Aligned',
    tone: 'green',
    explanation: 'Positioning and VIR are broadly moving the same way.',
  }
}

function classifyExposure(row) {
  const acid = row.acid ?? ''
  if (acid === 'USD Cash') {
    return 'Cash'
  }
  if (acid === 'Alts') {
    return 'Alternatives'
  }
  if (row.acid_type === 'acid_bond') {
    return 'Fixed Income'
  }
  if (row.acid_type === 'acid_region_sector') {
    return 'Eq Sector'
  }
  if (row.acid_type === 'acid_country') {
    if (/^US (LRG|MID|SML)/.test(acid)) {
      return 'Eq Size / Style'
    }
    if (acid === 'EM EQ' || acid === 'ARAB EQ') {
      return 'Region'
    }
    return 'Country'
  }
  return 'Other'
}

function compareExposureRows(a, b) {
  const categoryDelta = categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category)
  if (categoryDelta !== 0) {
    return categoryDelta
  }
  return Math.abs(numberOrNull(b.active_rolled_exposure) ?? 0) - Math.abs(numberOrNull(a.active_rolled_exposure) ?? 0)
}

function sourceNamesForAcid(model, acid) {
  const lineage = model.lineageByAcid[acid]
  if (!lineage?.securities?.length) {
    return []
  }
  return lineage.securities.slice(0, 3).map((item) => item.securityName)
}

function summarizeStatuses(rows, field) {
  return rows.reduce((accumulator, row) => {
    const key = row[field] || 'unknown'
    accumulator[key] = (accumulator[key] ?? 0) + 1
    return accumulator
  }, {})
}

function classifyCategoryRelation(positionNet, virCurrent, algoCurrent) {
  const position = numberOrNull(positionNet) ?? 0
  const vir = numberOrNull(virCurrent) ?? 0
  const algo = numberOrNull(algoCurrent) ?? 0
  if (position === 0) {
    return 'Neutral position'
  }
  if ((position > 0 && vir < 0) || (position < 0 && vir > 0)) {
    return 'Against VIR'
  }
  if ((position > 0 && algo < 0) || (position < 0 && algo > 0)) {
    return 'Against algo'
  }
  return 'With signal'
}

function average(values) {
  const valid = values.map(numberOrNull).filter((value) => value != null)
  if (!valid.length) {
    return null
  }
  return valid.reduce((sum, value) => sum + value, 0) / valid.length
}

function mostCommon(values) {
  const counts = new Map()
  for (const value of values.filter(Boolean)) {
    counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? ''
}

function previousValue(currentValue, deltaValue) {
  const current = numberOrNull(currentValue)
  if (current == null) {
    return null
  }
  return current - (numberOrNull(deltaValue) ?? 0)
}

function signalScale(rows, field) {
  return Math.max(...rows.map((row) => Math.abs(numberOrNull(row[field]) ?? 0)), 1)
}

function centeredBarStyle(value, maxValue) {
  const width = `${getRelativeWidth(value, maxValue, 100)}%`
  return numberOrNull(value) >= 0 ? { left: '50%', width } : { right: '50%', width }
}

function linearBarStyle(value, maxValue) {
  return { left: 0, width: `${getRelativeWidth(value, maxValue, 100)}%` }
}

function describeSignalRow(row) {
  if (!row) {
    return 'No signal row is available.'
  }
  const active = numberOrNull(row.active_rolled_exposure) ?? 0
  const vir = numberOrNull(row.vir_stf)
  const delta = numberOrNull(row.vir_delta_stf)
  const algo = numberOrNull(row.algo_active_weight)
  const algoMom = numberOrNull(row.algo_active_weight_mom)
  const fragments = []

  if (active > 0) {
    fragments.push(`The fund is overweight ${row.acid}.`)
  } else if (active < 0) {
    fragments.push(`The fund is underweight ${row.acid}.`)
  } else {
    fragments.push(`The fund is roughly neutral in ${row.acid}.`)
  }

  if (vir != null) {
    fragments.push(`VIR sits at ${formatMaybe(vir)}${delta != null ? ` after a ${formatSignedMaybe(delta)} move month over month` : ''}.`)
  }
  if (algo != null) {
    fragments.push(`Algo active weight is ${formatMaybe(algo)}${algoMom != null ? ` with ${formatSignedMaybe(algoMom)} month over month` : ''}.`)
  }
  if (vir != null && active * vir < 0) {
    fragments.push('Positioning and VIR are still pointing in opposite directions.')
  }
  return fragments.join(' ')
}

function truncate(value, length) {
  const text = String(value ?? '')
  return text.length > length ? `${text.slice(0, length - 1)}…` : text
}

function toneClass(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'tone-text-neutral'
  }
  return numeric > 0 ? 'tone-text-green' : 'tone-text-red'
}

function toneFromNumber(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'neutral'
  }
  return numeric > 0 ? 'green' : 'red'
}

function numberOrNull(value) {
  if (value == null || value === '') {
    return null
  }
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function formatMaybe(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '—'
  }
  return numeric.toFixed(2)
}

function formatSignedMaybe(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '—'
  }
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)}`
}

function formatWeight(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '—'
  }
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)}%`
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function monthYear(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
}

function getRelativeWidth(value, maxValue, maxWidth) {
  const numeric = Math.abs(numberOrNull(value) ?? 0)
  if (!numeric || !maxValue) {
    return 0
  }
  return Math.max(4, Math.min(maxWidth, (numeric / maxValue) * maxWidth))
}

function humanizeKey(value = '') {
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function slugify(value = '') {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
