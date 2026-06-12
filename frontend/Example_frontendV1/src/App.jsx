import { useEffect, useMemo, useState } from 'react'
import bundle from './data/monthlyReviewBundle.json'
import exposureLineage from './data/exposureLineage.json'
import fundWeightsVirAlgo from './data/fundWeightsVirAlgo.json'
import signalHistory from './data/signalHistory.json'
import agent2ReviewMstarUsequity from './data/agent2/mstar-us-equity-review.json'
import agent2ManifestMstarUsequity from './data/agent2/mstar-us-equity-manifest.json'
import agent2PacketMstarUsequity from './data/agent2/mstar-us-equity-packet.json'

const tabs = [
  { id: 'dashboard', navLabel: 'Dashboard', sectionLabel: 'Overview' },
  { id: 'decomp', navLabel: 'VIR / Algo', sectionLabel: 'VIR / Algo' },
  { id: 'challenge', navLabel: 'Challenge Brief', sectionLabel: 'Challenge Brief' },
  { id: 'fof', navLabel: 'Fund of Funds', sectionLabel: 'Fund of Funds' },
  { id: 'ic', navLabel: 'IC Prep', sectionLabel: 'IC Prep' },
  { id: 'memory', navLabel: 'Agent Memory', sectionLabel: 'Agent Memory' },
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

const agent2RunsByFund = {
  'MStar US Equity': {
    review: agent2ReviewMstarUsequity,
    manifest: agent2ManifestMstarUsequity,
    packet: agent2PacketMstarUsequity,
  },
}

const signalHistoryByFund = signalHistory.funds ?? {}
const defaultFundName = 'MStar US Equity'
const defaultTabId = 'decomp'
const defaultPortfolioView = 'new'
const defaultCategory = 'All'

export default function App() {
  const fundDirectory = useMemo(() => buildFundDirectory(bundle.funds, fundWeightsVirAlgo), [])
  const preferredSlug = fundDirectory.find((fund) => fund.fund === defaultFundName)?.slug ?? fundDirectory[0]?.slug ?? ''
  const initialViewState = useMemo(() => readViewStateFromUrl(fundDirectory, preferredSlug), [fundDirectory, preferredSlug])
  const [selectedSlug, setSelectedSlug] = useState(initialViewState.selectedSlug)
  const [activeTab, setActiveTab] = useState(initialViewState.activeTab)
  const [selectedCategory, setSelectedCategory] = useState(initialViewState.selectedCategory)
  const [selectedAcid, setSelectedAcid] = useState(initialViewState.selectedAcid)
  const [portfolioView, setPortfolioView] = useState(initialViewState.portfolioView)

  const selectedFund = fundDirectory.find((fund) => fund.slug === selectedSlug) ?? fundDirectory[0]
  const model = useMemo(() => buildFundModel(selectedFund), [selectedFund])
  const filteredModel = useMemo(() => filterModelByCategory(model, selectedCategory), [model, selectedCategory])
  const activeTabConfig = tabs.find((tab) => tab.id === activeTab)
  const pageTitle = activeTabConfig?.sectionLabel ?? 'Overview'

  useEffect(() => {
    if (!selectedFund) {
      return
    }
    const nextCategory =
      selectedCategory === defaultCategory || model.availableCategories.includes(selectedCategory)
        ? selectedCategory
        : defaultCategory
    const nextSearch = buildViewSearchParams({
      fundSlug: selectedFund.slug,
      activeTab,
      selectedCategory: nextCategory,
      selectedAcid,
      portfolioView,
    })
    const nextUrl = `${window.location.pathname}?${nextSearch.toString()}`
    if (`${window.location.pathname}${window.location.search}` !== nextUrl) {
      window.history.replaceState({}, '', nextUrl)
    }
  }, [activeTab, model.availableCategories, portfolioView, selectedAcid, selectedCategory, selectedFund])

  useEffect(() => {
    if (!filteredModel.exposures.length) {
      return
    }
    if (!filteredModel.exposureByAcid.has(selectedAcid)) {
      setSelectedAcid(filteredModel.exposures[0].acid)
    }
  }, [filteredModel.exposureByAcid, filteredModel.exposures, selectedAcid])

  useEffect(() => {
    if (!model.availableCategories.includes(selectedCategory) && selectedCategory !== defaultCategory) {
      setSelectedCategory(defaultCategory)
    }
  }, [model.availableCategories, selectedCategory])

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

      <div className="new-shell">
        <header className="new-header">
          <div className="new-header-top">
            <div className="new-brand">
              <div className="new-brand-mark">PM</div>
              <div>
                <div className="new-brand-title">PM Analyst Agent</div>
                <div className="new-brand-subtitle">Portfolio signals, look-through, and agent review in one place.</div>
              </div>
            </div>

            <div className="new-header-actions">
              <span className="new-chip is-live">Live</span>
              <span className="new-chip">{monthYear(bundle.snapshot_date || model.snapshotMatrix.review)}</span>
              <span className="new-chip">{fundDirectory.length} Funds</span>
              <button type="button" className="new-action primary" onClick={() => setActiveTab('challenge')}>Run Review</button>
              <button type="button" className="new-action" onClick={() => setActiveTab('ic')}>IC Prep</button>
            </div>
          </div>

          <div className="new-header-grid">
            <div className="new-header-main">
              <div className="new-page-title">{selectedFund?.fund ?? 'No fund selected'}</div>
              <div className="new-page-subtitle">
                Review {model.snapshotMatrix.review || '-'} | Positions {model.snapshotMatrix.positioning || '-'} | VIR {model.snapshotMatrix.vir || '-'} | Algo {model.snapshotMatrix.algo || '-'}
              </div>
            </div>

            <div className="new-header-stats">
              <MiniStat label="Positions" value={String(filteredModel.summary.positionCount)} />
              <MiniStat label="Misaligned" value={String(filteredModel.summary.misalignedCount)} tone="amber" />
              <MiniStat label="Urgent" value={String(filteredModel.summary.urgentCount)} tone="red" />
              <MiniStat label="Aligned" value={String(filteredModel.summary.alignedCount)} tone="green" />
            </div>
          </div>
        </header>

        <div className="new-app-body">
          <aside className="new-fund-panel">
            <div className="new-panel-head">
              <div className="new-strip-label">Funds</div>
              <div className="new-panel-meta">{fundDirectory.length} total</div>
            </div>

            <div className="new-fund-list" role="tablist" aria-label="Funds">
              {fundDirectory.map((fund) => (
                <button
                  key={fund.slug}
                  type="button"
                  className={`new-fund-card ${selectedSlug === fund.slug ? 'is-active' : ''}`}
                  onClick={() => setSelectedSlug(fund.slug)}
                >
                  <span className={`new-fund-dot ${fund.statusDot}`} />
                  <div className="new-fund-card-copy">
                    <strong>{fund.fund}</strong>
                    <span>{fund.typeLabel}</span>
                  </div>
                </button>
              ))}
            </div>

            <div className="new-fund-summary">
              <SidebarMeta label="Review" value={model.snapshotMatrix.review} />
              <SidebarMeta label="VIR" value={model.snapshotMatrix.vir} />
              <SidebarMeta label="Algo" value={model.snapshotMatrix.algo} />
              <SidebarMeta label="Bundle built" value={formatDateTime(bundle.bundle_generated_at)} />
            </div>
          </aside>

          <div className="new-workspace">
            <section className="new-control-bar">
              <div className="new-segmented" aria-label="Portfolio views">
                {[
                  { id: 'new', label: 'New Portfolio' },
                  { id: 'target', label: 'Target Portfolio' },
                  { id: 'bench', label: 'Benchmark' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`new-segment ${portfolioView === tab.id ? 'is-active' : ''}`}
                    onClick={() => setPortfolioView(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <nav className="new-tab-row" aria-label="Workspace sections">
                {tabs.map((tab) => {
                  const badge = tabBadgeForModel(tab.id, filteredModel)
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      className={`new-tab ${activeTab === tab.id ? 'is-active' : ''}`}
                      onClick={() => setActiveTab(tab.id)}
                    >
                      <span>{tab.sectionLabel}</span>
                      {badge ? <span className={`new-tab-badge ${badge.info ? 'is-info' : ''}`}>{badge.label}</span> : null}
                    </button>
                  )
                })}
              </nav>
            </section>

            <main id="main-content" className="new-main">
              <div className="new-section-head">
                <div>
                  <div className="page-title">{pageTitle}</div>
                  <div className="page-subtitle">
                    Agent review, positioning, and supporting research linked to the selected fund and category.
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

              <div className="filter-row new-filter-row">
                <span className="mini-label">Category</span>
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
                <ReferenceDashboardTab model={filteredModel} onFocusAcid={focusAcid} portfolioView={portfolioView} />
              ) : null}
              {activeTab === 'challenge' ? (
                <ReferenceChallengeTab model={filteredModel} onOpenReview={(acid) => focusAcid(acid, 'ic')} />
              ) : null}
              {activeTab === 'decomp' ? (
                <ReferenceDecompTab model={filteredModel} focusedRow={focusedRow} onFocusAcid={focusAcid} />
              ) : null}
              {activeTab === 'fof' ? <ReferenceFoFTab model={filteredModel} /> : null}
              {activeTab === 'ic' ? <ReferenceICTab model={filteredModel} focusedAcid={focusedRow?.acid ?? ''} /> : null}
              {activeTab === 'memory' ? <ReferenceMemoryTab model={filteredModel} /> : null}
            </main>
          </div>
        </div>
      </div>
    </>
  )
}

function DashboardTab({ model, onFocusAcid, portfolioView }) {
  const portfolio = getPortfolioViewMeta(model, portfolioView)
  const agentReview = model.agentReview
  const researchHighlights = agentReview?.sharepointHighlights ?? []
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
                <button key={row.acid} type="button" className="bar-row" onClick={() => onFocusAcid(row.acid, 'signals')}>
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
                <button key={row.acid} type="button" className="table-row table-button" onClick={() => onFocusAcid(row.acid, 'signals')}>
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
        <Card title="AGENT2 VIEW" subtitle={agentReview ? reviewRunSubtitle(agentReview) : 'No Bedrock review loaded'}>
          {agentReview ? (
            <div className="agent-review-stack">
              <p className="agent-summary">{agentReview.review.executive_summary}</p>
              <div className="agent-position-list">
                {agentReview.materialPositions.slice(0, 4).map((position) => (
                  <article key={position.position_id} className="agent-position-card">
                    <div className="agent-position-top">
                      <div>
                        <h4>{position.label}</h4>
                        <span>{position.category}</span>
                      </div>
                      <StatusBadge tone={alignmentToneForSignal(position.signal_alignment)}>{humanizeKey(position.signal_alignment)}</StatusBadge>
                    </div>
                    <div className="agent-position-metrics">
                      <span>
                        <label>Active</label>
                        <code className={toneClass(position.active_weight)}>{formatWeight(position.active_weight)}</code>
                      </span>
                      <span>
                        <label>VIR</label>
                        <code>{formatMaybe(position.vir_now)}</code>
                      </span>
                      <span>
                        <label>Algo</label>
                        <code>{formatMaybe(position.algo_active_weight)}</code>
                      </span>
                    </div>
                    <div className="agent-support-stack">
                      {position.sharepoint_research_summary ? (
                        <div className="agent-support-block">
                          <label>Research deck</label>
                          <p>{truncate(position.sharepoint_research_summary, 220)}</p>
                        </div>
                      ) : null}
                      {position.internal_history_excerpt ? (
                        <div className="agent-support-block">
                          <label>Prior internal note</label>
                          <p>{truncate(position.internal_history_excerpt, 220)}</p>
                        </div>
                      ) : null}
                      {!position.sharepoint_research_summary && !position.internal_history_excerpt ? (
                        <p>{position.sample_source_securities || 'No saved supporting context for this position.'}</p>
                      ) : null}
                    </div>
                    {position.sharepoint_research_path ? (
                      <div className="agent-support-meta">
                        <span>SharePoint deck</span>
                        <code>{fileNameFromPath(position.sharepoint_research_path)}</code>
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            </div>
          ) : model.reviewSections.length ? (
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

        <Card title="PM QUESTIONS" subtitle="what the live review wants answered">
          {agentReview ? (
            <div className="agent-review-stack">
              <div className="agent-question-list">
                {agentReview.review.pm_questions.slice(0, 4).map((item) => (
                  <article key={item.label} className="agent-question-card">
                    <h4>{item.label}</h4>
                    <p>{item.question}</p>
                    <div className="inline-note tone-neutral">{item.why_now}</div>
                  </article>
                ))}
              </div>

              <div className="memory-summary-grid run-stat-grid">
                <MiniStat label="Run cost" value={formatCurrency(agentReview.manifest.approx_cost_usd)} tone="blue" />
                <MiniStat label="Input tokens" value={formatInteger(agentReview.manifest.usage?.inputTokens)} />
                <MiniStat label="Output tokens" value={formatInteger(agentReview.manifest.usage?.outputTokens)} />
                <MiniStat label="Total tokens" value={formatInteger(agentReview.manifest.usage?.totalTokens)} />
              </div>

              <div className="inline-note tone-blue">
                Model {shortModelName(agentReview.manifest.model)} in {agentReview.manifest.region_name} | generated {formatDateTime(agentReview.manifest.generated_at)}
              </div>
            </div>
          ) : (
            <EmptyState copy="No structured PM questions are available for this fund yet." />
          )}
        </Card>
      </div>

      <div className="split-grid split-dashboard">
        <Card title="INTERNAL RESEARCH" subtitle={agentReview ? "synced SharePoint decks matched to the fund's active exposures" : 'SharePoint research appears when Agent2 packet data is loaded'}>
          {agentReview ? (
            <div className="agent-review-stack">
              <div className="memory-summary-grid">
                <MiniStat label="Matched decks" value={String(agentReview.matchedResearchCount ?? 0)} tone="blue" />
                <MiniStat label="Packet review" value={agentReview.packetReviewDate || '-'} />
                <MiniStat
                  label="Live narrative"
                  value={agentReview.manifest.review_date || '-'}
                  tone={agentReview.hasFreshNarrative ? 'green' : 'amber'}
                />
              </div>
              {researchHighlights.length ? (
                <div className="research-list">
                  {researchHighlights.slice(0, 4).map((item) => (
                    <article key={`${item.acid}-${item.file_name}`} className="research-card">
                      <div className="research-head">
                        <div>
                          <h4>{item.label || item.acid}</h4>
                          <span>{item.acid}</span>
                        </div>
                        {item.active_weight != null ? (
                          <code className={toneClass(item.active_weight)}>{formatWeight(item.active_weight)}</code>
                        ) : null}
                      </div>
                      <div className="research-meta">
                        <span>{item.file_name || fileNameFromPath(item.full_path)}</span>
                        <span>{item.matched_via || 'matched'}</span>
                      </div>
                      <p className="research-summary">{truncate(item.summary_text, 240)}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState copy="No matched SharePoint research summaries are available for this packet." />
              )}
            </div>
          ) : (
            <EmptyState copy="No Agent2 packet is loaded for this fund." />
          )}
        </Card>

        <Card title="DATA TIMING" subtitle="actual bundle sources">
          <div className="timing-list">
            <TimingRow label="Review snapshot" value={model.snapshotMatrix.review} />
            <TimingRow label="Positioning layer" value={model.snapshotMatrix.positioning} />
            <TimingRow label="VIR layer" value={model.snapshotMatrix.vir} />
            <TimingRow label="Algo layer" value={model.snapshotMatrix.algo} />
            <TimingRow label="Bundle built" value={formatDateTime(bundle.bundle_generated_at)} />
            {agentReview ? <TimingRow label="Packet refreshed" value={agentReview.packetReviewDate} /> : null}
            {agentReview ? <TimingRow label="Agent run" value={formatDateTime(agentReview.manifest.generated_at)} /> : null}
          </div>
          {agentReview && !agentReview.hasFreshNarrative ? (
            <div className="inline-note tone-amber">
              The structured packet is newer than the last live Bedrock run. This view is using packet-derived review text from current holdings, VIR, algo, and research matches so stale narrative does not leak into the dashboard.
            </div>
          ) : null}
          {agentReview?.dataQualityFlags?.length ? (
            <div className="agent-flag-stack">
              {agentReview.dataQualityFlags.slice(0, 2).map((flag) => (
                <div key={flag.flag} className={`inline-note ${flag.severity === 'medium' ? 'tone-amber' : 'tone-neutral'}`}>
                  {flag.message}
                </div>
              ))}
            </div>
          ) : model.snapshotMatrix.hasMismatch ? (
            <div className="inline-note tone-blue">
              The saved PM review and the structured exposure layer are not from the same snapshot. The narrative is current to the review run; the tables reflect the latest structured positioning file currently bundled into the app.
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  )
}

function PositioningTab({ model, onFocusAcid, portfolioView }) {
  const portfolio = getPortfolioViewMeta(model, portfolioView)
  const rows = model.exposures
    .filter((row) => Math.abs(numberOrNull(row[portfolio.field]) ?? 0) >= portfolio.minimum)
    .slice(0, 20)
  const leaderBook = buildExposureLeaders(model)
  const lookthroughRows = model.exposures.filter((row) => model.lineageByAcid[row.acid] && Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0.3)

  return (
    <div className="page-grid">
      <Card title="CATEGORY POSTURE" subtitle="where the fund is leaning by exposure bucket">
        <div className="category-posture-grid">
          {model.categoryTrendRows.map((row) => (
            <article key={row.category} className="category-posture-card">
              <div>
                <h4>{row.category}</h4>
                <span>{row.relationshipLabel}</span>
              </div>
              <div className="category-posture-metrics">
                <span>
                  <label>Net active</label>
                  <code className={toneClass(row.positionNet)}>{formatWeight(row.positionNet)}</code>
                </span>
                <span>
                  <label>Avg VIR</label>
                  <code>{formatMaybe(row.virCurrent)}</code>
                </span>
                <span>
                  <label>Avg algo</label>
                  <code>{formatMaybe(row.algoCurrent)}</code>
                </span>
              </div>
            </article>
          ))}
        </div>
      </Card>

      <div className="split-grid split-dashboard">
        <Card title={portfolio.cardTitle} subtitle={`${model.fundName} | ${portfolio.snapshotLabel}`}>
          {rows.length ? (
            <div className="bar-list" role="img" aria-label="Largest portfolio exposures">
              {rows.map((row) => (
                <button key={row.acid} type="button" className="bar-row" onClick={() => onFocusAcid(row.acid, 'signals')}>
                  <div className="bar-row-label">
                    <strong>{truncate(row.acid, 22)}</strong>
                    <span>{portfolio.detail(row)}</span>
                  </div>
                  <div className="bar-track">
                    {portfolio.mode === 'centered' ? <div className="bar-zero" /> : null}
                    <span className={`bar-fill ${portfolio.fillClass(row[portfolio.field])}`} style={portfolio.style(row[portfolio.field])} />
                  </div>
                  <code className={portfolio.tone(row[portfolio.field])}>{formatWeight(row[portfolio.field])}</code>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState copy="No material positions for this view." />
          )}
        </Card>

        <Card title="TOP BOOK TILTS" subtitle="largest overweights and underweights">
          <div className="split-grid split-tilts">
            <div className="mini-panel">
              <div className="subhead">Overweights</div>
              <div className="leader-list">
                {leaderBook.overweights.map((row) => (
                  <button key={`ow-${row.label}`} type="button" className="leader-row" onClick={() => row.acid && onFocusAcid(row.acid, 'signals')}>
                    <strong>{row.label}</strong>
                    <code className="tone-text-green">{formatWeight(row.active_weight)}</code>
                  </button>
                ))}
              </div>
            </div>
            <div className="mini-panel">
              <div className="subhead">Underweights</div>
              <div className="leader-list">
                {leaderBook.underweights.map((row) => (
                  <button key={`uw-${row.label}`} type="button" className="leader-row" onClick={() => row.acid && onFocusAcid(row.acid, 'signals')}>
                    <strong>{row.label}</strong>
                    <code className="tone-text-red">{formatWeight(row.active_weight)}</code>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card title="SOURCE LOOK-THROUGH" subtitle="how the active exposures are being created underneath the fund">
        {lookthroughRows.length ? (
          <div className="accordion-stack">
            {lookthroughRows.map((row) => (
              <LookThroughRow key={row.acid} row={row} lineage={model.lineageByAcid[row.acid]} />
            ))}
          </div>
        ) : (
          <EmptyState copy="No expandable look-through rows are available for this fund." />
        )}
      </Card>
    </div>
  )
}

function SignalsTab({ model, focusedRow, onFocusAcid }) {
  const agentReview = model.agentReview

  return (
    <div className="page-grid">
      <Card title="SIGNAL STORYLINE" subtitle="what shifted in VIR and where the position book is under pressure">
        <div className="split-grid split-agent">
          <AgentNarrativeSection title="What changed" items={agentReview?.review?.what_changed ?? []} tone="blue" />
          <AgentNarrativeSection title="Dashboard highlights" items={agentReview?.review?.dashboard_highlights ?? []} tone="amber" />
        </div>
      </Card>

      <SignalLensTab model={model} focusedRow={focusedRow} onFocusAcid={onFocusAcid} />

      <ChallengeBriefTab model={model} onOpenReview={(acid) => onFocusAcid(acid, 'review')} />
    </div>
  )
}

function ReviewTab({ model, focusedAcid }) {
  const agentReview = model.agentReview

  return (
    <div className="page-grid">
      {agentReview ? (
        <Card title="EXECUTIVE SUMMARY" subtitle="the agent's current read on the fund">
          <div className="review-hero">
            <p>{agentReview.review.executive_summary}</p>
            <div className="meta-ribbon">
              <span>Model {shortModelName(agentReview.manifest.model)}</span>
              <span>Cost {formatCurrency(agentReview.manifest.approx_cost_usd)}</span>
              <span>Snapshot {agentReview.manifest.logical_snapshot_date}</span>
              <span>Generated {formatDateTime(agentReview.manifest.generated_at)}</span>
            </div>
          </div>
        </Card>
      ) : null}

      {agentReview?.sharepointHighlights?.length ? (
        <Card title="RESEARCH BACKDROP" subtitle="internal research decks most relevant to the current active bets">
          <div className="research-list">
            {agentReview.sharepointHighlights.slice(0, 6).map((item) => (
              <article key={`${item.acid}-${item.file_name}`} className="research-card">
                <div className="research-head">
                  <div>
                    <h4>{item.label || item.acid}</h4>
                    <span>{item.file_name || fileNameFromPath(item.full_path)}</span>
                  </div>
                  {item.active_weight != null ? (
                    <code className={toneClass(item.active_weight)}>{formatWeight(item.active_weight)}</code>
                  ) : null}
                </div>
                <p className="research-summary">{truncate(item.summary_text, 320)}</p>
              </article>
            ))}
          </div>
        </Card>
      ) : null}

      <ICPrepTab model={model} focusedAcid={focusedAcid} />
    </div>
  )
}

function EvidenceTab({ model }) {
  const agentReview = model.agentReview
  const memoryUpdates = model.changeBrief.memory_updates_summary ?? {}
  const evidence = model.changeBrief.evidence_index ?? []

  return (
    <div className="page-grid">
      <div className="split-grid split-memory">
        <Card title="RUN HEALTH" subtitle="confidence, freshness, and saved run context">
          <div className="memory-summary-grid">
            <MiniStat label="Sources" value={String(agentReview?.packet?.source_index?.length ?? 0)} />
            <MiniStat label="Flags" value={String(agentReview?.dataQualityFlags?.length ?? 0)} tone="amber" />
            <MiniStat label="Evidence rows" value={String(evidence.length)} tone="blue" />
            <MiniStat label="Run cost" value={formatCurrency(agentReview?.manifest?.approx_cost_usd)} tone="green" />
          </div>
          {agentReview?.dataQualityFlags?.length ? (
            <div className="agent-flag-stack">
              {agentReview.dataQualityFlags.map((flag) => (
                <div key={flag.flag} className={`inline-note ${flag.severity === 'medium' ? 'tone-amber' : 'tone-neutral'}`}>
                  {flag.message}
                </div>
              ))}
            </div>
          ) : null}
        </Card>

        <Card title="AGENT MEMORY" subtitle="what prior review context is being carried in">
          <div className="memory-summary-grid">
            <MiniStat label="Theses" value={String(memoryUpdates.thesis_ledger_entries ?? model.memorySummary.thesis_ledger_count ?? 0)} />
            <MiniStat label="Exceptions" value={String(memoryUpdates.approved_exceptions ?? model.memorySummary.exceptions_count ?? 0)} />
            <MiniStat label="Watch items" value={String(memoryUpdates.watch_items ?? model.memorySummary.watch_items_count ?? 0)} />
            <MiniStat label="Proposed" value={String(memoryUpdates.proposed_count_from_prior_run ?? model.memorySummary.proposed_count ?? 0)} />
          </div>
          <div className="inline-note tone-neutral">
            This page is for trust and traceability: what fed the run, what may be stale, and what prior internal context the review is leaning on.
          </div>
        </Card>
      </div>

      <Card title="SHAREPOINT RESEARCH" subtitle="synced internal decks matched by ACID to the current fund exposures">
        {agentReview?.sharepointHighlights?.length ? (
          <div className="agent-review-stack">
            <div className="memory-summary-grid">
              <MiniStat label="Matched decks" value={String(agentReview.matchedResearchCount ?? agentReview.sharepointHighlights.length)} tone="blue" />
              <MiniStat label="Packet review" value={agentReview.packetReviewDate || '-'} />
              <MiniStat label="Research surfaced" value={String(agentReview.sharepointHighlights.length)} tone="green" />
            </div>
            <div className="research-list">
              {agentReview.sharepointHighlights.slice(0, 8).map((item) => (
                <article key={`${item.acid}-${item.file_name}`} className="research-card">
                  <div className="research-head">
                    <div>
                      <h4>{item.label || item.acid}</h4>
                      <span>{item.acid}</span>
                    </div>
                    {item.active_weight != null ? (
                      <code className={toneClass(item.active_weight)}>{formatWeight(item.active_weight)}</code>
                    ) : null}
                  </div>
                  <div className="research-meta">
                    <span>{item.file_name || fileNameFromPath(item.full_path)}</span>
                    <span>{item.matched_via || 'matched'}</span>
                  </div>
                  <p className="research-summary">{truncate(item.summary_text, 260)}</p>
                </article>
              ))}
            </div>
          </div>
        ) : (
          <EmptyState copy="No matched SharePoint research was surfaced for this run." />
        )}
      </Card>

      <Card title="SOURCE INDEX" subtitle="where the current review is pulling its evidence from">
        {agentReview?.packet?.source_index?.length ? (
          <div className="artifact-table">
            {agentReview.packet.source_index.map((source) => (
              <div key={`${source.source_type}-${source.artifact_path}`} className="artifact-row">
                <span>{humanizeKey(source.source_type)}</span>
                <code>{source.purpose}</code>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState copy="No structured source index is available for this fund." />
        )}
      </Card>

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
  const agentReview = model.agentReview

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

      {agentReview ? (
        <Card title="STRUCTURED AGENT CASE" subtitle="live Bedrock output anchored to holdings, VIR, algo, and internal history">
          <div className="agent-case-grid">
            <AgentNarrativeSection title="Current positioning" items={agentReview.review.current_positioning} tone="blue" />
            <AgentNarrativeSection title="Bull case" items={agentReview.review.bull_case} tone="green" />
            <AgentNarrativeSection title="Bear case" items={agentReview.review.bear_case} tone="red" />
            <AgentNarrativeSection title="Devil's advocate" items={agentReview.review.devils_advocate} tone="amber" />
          </div>
        </Card>
      ) : null}

      {agentReview ? (
        <Card title="FOLLOW-UP TRACKER" subtitle="what to ask now and what to do next">
          <div className="split-grid split-agent">
            <AgentNarrativeSection title="PM questions" items={agentReview.review.pm_questions} tone="blue" />
            <AgentNarrativeSection title="Follow-up actions" items={agentReview.review.follow_up} tone="amber" />
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
  const agentReview = model.agentReview
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

      <div className="split-grid split-memory">
        <Card title="RUN HEALTH" subtitle="freshness, model context, and current packet quality">
          <div className="memory-summary-grid">
            <MiniStat label="Sources" value={String(agentReview?.packet?.source_index?.length ?? 0)} />
            <MiniStat label="Flags" value={String(agentReview?.dataQualityFlags?.length ?? 0)} tone="amber" />
            <MiniStat label="Run cost" value={formatCurrency(agentReview?.manifest?.approx_cost_usd)} tone="green" />
            <MiniStat label="Packet review" value={agentReview?.packetReviewDate || '-'} tone="blue" />
          </div>
          {agentReview && !agentReview.hasFreshNarrative ? (
            <div className="inline-note tone-amber">
              This tab is using the latest rebuilt structured packet and packet-derived review text because the last live Bedrock narrative is older than the current packet.
            </div>
          ) : null}
          {agentReview?.dataQualityFlags?.length ? (
            <div className="agent-flag-stack">
              {agentReview.dataQualityFlags.slice(0, 3).map((flag) => (
                <div key={flag.flag} className={`inline-note ${flag.severity === 'medium' ? 'tone-amber' : 'tone-neutral'}`}>
                  {flag.message}
                </div>
              ))}
            </div>
          ) : null}
        </Card>

        <Card title="SOURCE INDEX" subtitle="where the current review is pulling evidence from">
          {agentReview?.packet?.source_index?.length ? (
            <div className="artifact-table">
              {agentReview.packet.source_index.map((source) => (
                <div key={`${source.source_type}-${source.artifact_path}`} className="artifact-row">
                  <span>{humanizeKey(source.source_type)}</span>
                  <code>{source.purpose}</code>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState copy="No structured source index is available for this fund." />
          )}
        </Card>
      </div>

      <Card title="INTERNAL RESEARCH DECKS" subtitle="synced SharePoint research matched to material ACIDs">
        {agentReview?.sharepointHighlights?.length ? (
          <div className="research-list">
            {agentReview.sharepointHighlights.slice(0, 10).map((item) => (
              <article key={`${item.acid}-${item.file_name}`} className="research-card">
                <div className="research-head">
                  <div>
                    <h4>{item.label || item.acid}</h4>
                    <span>{item.acid}</span>
                  </div>
                  {item.active_weight != null ? (
                    <code className={toneClass(item.active_weight)}>{formatWeight(item.active_weight)}</code>
                  ) : null}
                </div>
                <div className="research-meta">
                  <span>{item.file_name || fileNameFromPath(item.full_path)}</span>
                  <span>{item.matched_via || 'matched'}</span>
                </div>
                <p className="research-summary">{truncate(item.summary_text, 260)}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState copy="No matched SharePoint research was surfaced for this run." />
        )}
      </Card>

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
  if (tabId === 'challenge') {
    const count = buildChallengeCards(model).length
    return count ? { label: String(count) } : null
  }
  if (tabId === 'decomp') {
    return model.signalRows.length ? { label: String(model.signalRows.length), info: true } : null
  }
  if (tabId === 'fof') {
    const count = model.exposures.filter((row) => model.lineageByAcid[row.acid] && Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0.3).length
    return count ? { label: String(count), info: true } : null
  }
  if (tabId === 'ic') {
    const count = buildIcPrepItems(model).length
    return count ? { label: String(count), info: true } : null
  }
  if (tabId === 'memory') {
    const count = model.agentReview?.dataQualityFlags?.length ?? model.changeBrief.evidence_index?.length ?? 0
    return count ? { label: String(count) } : null
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

function ReferenceDashboardTab({ model, onFocusAcid, portfolioView }) {
  const portfolio = getPortfolioViewMeta(model, portfolioView)
  const coverageCount = model.exposures.filter((row) => row.vir_stf != null).length
  const coveragePct = model.exposures.length ? Math.round((coverageCount / model.exposures.length) * 100) : 0
  const scatterRows = [...model.signalRows]
    .filter((row) => row.vir_stf != null)
    .sort((a, b) => Math.abs(numberOrNull(b.active_rolled_exposure) ?? 0) - Math.abs(numberOrNull(a.active_rolled_exposure) ?? 0))
    .slice(0, 12)
  const movers = [...model.signalRows]
    .filter((row) => numberOrNull(row.vir_rank_change_by_stf) != null)
    .sort((a, b) => Math.abs(numberOrNull(b.vir_rank_change_by_stf) ?? 0) - Math.abs(numberOrNull(a.vir_rank_change_by_stf) ?? 0))
    .slice(0, 5)
  const waterfallRows = model.exposures
    .filter((row) => Math.abs(numberOrNull(row[portfolio.field]) ?? 0) >= portfolio.minimum)
    .slice(0, 12)
  const alignedCount = model.signalRows.filter((row) => classifyAlignment(row).key === 'aligned').length
  const conflictedCount = model.signalRows.filter((row) => classifyAlignment(row).key === 'opposite').length
  const noSignalCount = model.exposures.filter((row) => row.vir_stf == null).length
  const agentReview = model.agentReview
  const kpis = [
    { label: 'Positions', value: String(model.summary.positionCount), sublabel: `${model.summary.equityCount} eq | ${model.summary.bondCount} fi`, tone: 'blue' },
    { label: 'VIR Coverage', value: `${coveragePct}%`, sublabel: `${coverageCount} ACIDs matched`, tone: 'green' },
    { label: 'Conflicts', value: String(conflictedCount), sublabel: 'position vs signal', tone: 'red' },
    { label: 'Watch Items', value: String(model.summary.watchCount), sublabel: 'drifting momentum', tone: 'amber' },
    { label: 'IC Questions', value: String(agentReview?.review?.pm_questions?.length ?? buildChallengeCards(model).length), sublabel: 'saved for review', tone: 'violet' },
  ]

  return (
    <div>
      <div className="ref-kpi-row">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="ref-kpi">
            <div className="ref-kpi-label">{kpi.label}</div>
            <div className={`ref-kpi-value tone-text-${kpi.tone}`}>{kpi.value}</div>
            <div className="ref-kpi-sub">{kpi.sublabel}</div>
          </article>
        ))}
      </div>

      <div className="ref-two-col">
        <div>
          <div className="section-title">{portfolio.cardTitle}</div>
          <div className="ref-card ref-card-pad">
            <div className="ref-aw-head">
              <span>Position</span>
              <span>UW      0      OW</span>
              <span className="is-right">Active</span>
              <span className="is-right">VIR / Rank</span>
            </div>
            {waterfallRows.length ? (
              waterfallRows.map((row) => {
                const alignment = classifyAlignment(row)
                const absolute = numberOrNull(row[portfolio.field]) ?? 0
                const pct = Math.min((Math.abs(absolute) / Math.max(model.maxExposureActive, 0.01)) * 44, 44)
                const virDelta = numberOrNull(row.vir_delta_stf)
                const rankDelta = numberOrNull(row.vir_rank_change_by_stf)
                return (
                  <button key={row.acid} type="button" className="ref-aw-row" onClick={() => onFocusAcid(row.acid, 'decomp')}>
                    <div className={`ref-aw-name ${alignment.key === 'opposite' ? 'is-flagged' : ''}`}>{row.acid}</div>
                    <div className="ref-aw-bar-wrap">
                      <div className="ref-aw-side ref-aw-side-left">
                        {absolute < 0 ? (
                          <div className={`ref-aw-bar ${alignment.key === 'opposite' ? 'is-conflict' : 'is-neg'}`} style={{ width: `${pct}%` }} />
                        ) : null}
                      </div>
                      <div className="ref-aw-zero" />
                      <div className="ref-aw-side ref-aw-side-right">
                        {absolute >= 0 ? (
                          <div className={`ref-aw-bar ${alignment.key === 'opposite' ? 'is-conflict' : 'is-pos'}`} style={{ width: `${pct}%` }} />
                        ) : null}
                      </div>
                    </div>
                    <div className={`ref-aw-val ${toneClass(absolute)}`}>{formatWeight(absolute)}</div>
                    <div className="ref-aw-signal">
                      <span className={toneClass(virDelta)}>{virDelta == null ? '-' : `${virDelta > 0 ? '+' : ''}${(virDelta * 100).toFixed(2)}%`}</span>
                      <span className={toneClass(rankDelta)}>{rankDelta == null ? '-' : `${rankDelta > 0 ? '+' : ''}${Math.round(rankDelta)}`}</span>
                    </div>
                  </button>
                )
              })
            ) : (
              <EmptyState copy={portfolio.emptyCopy} />
            )}
          </div>
        </div>

        <div className="ref-right-stack">
          <div>
            <div className="section-title">VIR vs positioning - signal alignment</div>
            <div className="ref-card ref-card-pad">
              <div className="ref-align-stats">
                <div className="ref-align-box is-green">
                  <strong>{alignedCount}</strong>
                  <span>Aligned</span>
                </div>
                <div className="ref-align-box is-red">
                  <strong>{conflictedCount}</strong>
                  <span>Conflict</span>
                </div>
                <div className="ref-align-box">
                  <strong>{noSignalCount}</strong>
                  <span>No VIR</span>
                </div>
              </div>

              <div className="ref-scatter">
                <div className="ref-scatter-x" />
                <div className="ref-scatter-y" />
                {scatterRows.map((row) => (
                  <button
                    key={row.acid}
                    type="button"
                    className={`ref-scatter-point ${scatterPointClass(row)}`}
                    style={scatterPointStyle(row, model.maxExposureActive)}
                    title={`${row.acid} | VIR ${formatMaybe((numberOrNull(row.vir_stf) ?? 0) * 100)}% | Active ${formatWeight(row.active_rolled_exposure)}`}
                    onClick={() => onFocusAcid(row.acid, 'decomp')}
                  />
                ))}
              </div>
              <div className="ref-chart-caption">Active weight vs VIR STF - top-right means OW plus positive VIR.</div>
            </div>
          </div>

          <div>
            <div className="section-title">VIR rank movers this month</div>
            <div className="ref-card ref-card-pad">
              {movers.length ? (
                movers.map((row) => {
                  const rankDelta = numberOrNull(row.vir_rank_change_by_stf) ?? 0
                  const width = Math.min((Math.abs(rankDelta) / 100) * 100, 100)
                  return (
                    <button key={row.acid} type="button" className="ref-mover-row" onClick={() => onFocusAcid(row.acid, 'decomp')}>
                      <span>{row.acid}</span>
                      <div className="ref-mover-track">
                        <div className={`ref-mover-fill ${rankDelta >= 0 ? 'is-up' : 'is-down'}`} style={{ width: `${width}%` }} />
                      </div>
                      <code className={toneClass(rankDelta)}>{rankDelta >= 0 ? `+${Math.round(rankDelta)}` : `${Math.round(rankDelta)}`}</code>
                    </button>
                  )
                })
              ) : (
                <EmptyState copy="No VIR rank movers are available for this slice." />
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="ref-three-col">
        <div className="ref-card ref-card-pad">
          <div className="card-title">Challenge Queue</div>
          <div className="ref-mini-stack">
            {buildChallengeCards(model)
              .slice(0, 3)
              .map((item) => (
                <button key={item.id} type="button" className="ref-mini-row" onClick={() => onFocusAcid(item.acid, 'challenge')}>
                  <div>
                    <strong>{item.acid}</strong>
                    <p>{truncate(item.summary, 120)}</p>
                  </div>
                  <StatusBadge tone={item.severity === 'urgent' ? 'red' : item.severity === 'watch' ? 'amber' : 'blue'}>{humanizeKey(item.severity)}</StatusBadge>
                </button>
              ))}
          </div>
        </div>

        <div className="ref-card ref-card-pad ref-overview-research">
          <div className="card-title">SharePoint Research</div>
          <div className="ref-research-feed">
            {agentReview?.sharepointHighlights?.map((item) => (
              <article key={`${item.acid}-${item.file_name}`} className="ref-research-note">
                <strong>{item.label || item.acid}</strong>
                <span>{fileNameFromPath(item.full_path || item.file_name || '')}</span>
                <div className="ref-research-scroll">
                  <p>{item.summary_text}</p>
                </div>
              </article>
            ))}
            {!agentReview?.sharepointHighlights?.length ? <EmptyState copy="No matched research deck is saved for this fund yet." /> : null}
          </div>
        </div>

        <div className="ref-card ref-card-pad">
          <div className="card-title">Agent Run</div>
          <div className="ref-mini-stack">
            <div className="ref-run-stat">
              <span>Model</span>
              <code>{shortModelName(agentReview?.manifest?.model || '') || '-'}</code>
            </div>
            <div className="ref-run-stat">
              <span>Approx cost</span>
              <code>{formatCurrency(agentReview?.manifest?.approx_cost_usd)}</code>
            </div>
            <div className="ref-run-stat">
              <span>Generated</span>
              <code>{formatDateTime(agentReview?.manifest?.generated_at)}</code>
            </div>
            {agentReview?.dataQualityFlags?.[0] ? (
              <div className="inline-note tone-amber">{agentReview.dataQualityFlags[0].message}</div>
            ) : (
              <div className="inline-note tone-neutral">Bundle, review, and research details are all available in one place for this fund.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ReferenceChallengeTab({ model, onOpenReview }) {
  const cards = buildChallengeCards(model)
  const agentReview = model.agentReview

  return (
    <div>
      <div className="ref-banner">
        <span className="ref-banner-icon">!</span>
        <div>
          <strong>{cards.length} positions require PM review before the next IC.</strong>
          <p>The cards below combine active weights, fund positioning, VIR, algo direction, prior internal notes, and matched research context.</p>
        </div>
      </div>

      {cards.map((card, index) => {
        const row = card.row || {}
        const question = findRelevantNarrativeItem(agentReview?.review?.pm_questions ?? [], row, index)
        const position = agentReview?.positionByAcid?.get(card.acid)
        const sourceDecks = positionSourceDecks(position)
        const virValue = numberOrNull(row.vir_stf)
        const virDelta = numberOrNull(row.vir_delta_stf)
        return (
          <article key={card.id} className="ref-challenge-card">
            <div className="ref-cc-header">
              <span className="ref-cc-name">{card.acid}</span>
              <span className={`tag ${card.severity === 'urgent' ? 'tag-conflict' : card.severity === 'watch' ? 'tag-watch' : 'tag-aligned'}`}>{humanizeKey(card.severity)}</span>
              <span className={`tag ${(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0 ? 'tag-ow' : 'tag-uw'}`}>{(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0 ? 'OW' : 'UW'}</span>
              {virDelta != null ? (
                <span className={`tag ${virDelta >= 0 ? 'tag-aligned' : 'tag-watch'}`}>
                  VIR {virDelta >= 0 ? '+' : ''}
                  {(virDelta * 100).toFixed(2)}%
                </span>
              ) : null}
            </div>

            <div className="ref-cc-body">{card.summary}</div>

            <div className="ref-cc-grid">
              <MetricCell label="Active" value={formatWeight(row.active_rolled_exposure)} tone={toneClass(row.active_rolled_exposure)} />
              <MetricCell label="Portfolio" value={formatWeight(row.fund_target_rolled_exposure)} />
              <MetricCell label="Benchmark" value={formatWeight(row.fund_benchmark_rolled_exposure)} />
              <MetricCell label="VIR STF" value={virValue == null ? '-' : `${formatSignedMaybe(virValue * 100)}%`} tone={toneClass(virValue)} />
              <MetricCell label="VIR d MoM" value={virDelta == null ? '-' : `${formatSignedMaybe(virDelta * 100)}%`} tone={toneClass(virDelta)} />
              <MetricCell label="Rank d" value={formatSignedMaybe(row.vir_rank_change_by_stf)} tone={toneClass(row.vir_rank_change_by_stf)} />
            </div>

            <div className="ref-context-text">{position?.internal_history_excerpt ? truncate(position.internal_history_excerpt, 260) : card.detail}</div>

            {sourceDecks.length ? (
              <div className="ref-chip-line">
                {sourceDecks.slice(0, 3).map((deck) => (
                  <span key={deck} className="ref-data-chip">{deck}</span>
                ))}
              </div>
            ) : null}

            <div className="question-box">
              <div className="qb-label">Question for PM</div>
              <div className="qb-text">{question?.question || question?.statement || 'What is the live thesis for this position, and what would invalidate it over the next review cycle?'}</div>
            </div>

            <div className="ref-card-actions">
              <button type="button" className="tb-btn" onClick={() => onOpenReview(card.acid)}>
                Open IC Prep
              </button>
            </div>
          </article>
        )
      })}
    </div>
  )
}

function ReferenceDecompTab({ model, focusedRow, onFocusAcid }) {
  const agentReview = model.agentReview
  const materialPositions = [...(agentReview?.materialPositions ?? [])]
    .filter((position) => model.exposureByAcid.has(position.acid))
    .sort((a, b) => Math.abs(numberOrNull(b.active_weight) ?? 0) - Math.abs(numberOrNull(a.active_weight) ?? 0))
  const watchlist = buildVirAlgoWatchlist(model, materialPositions, focusedRow?.acid)
  const selectedAcid = focusedRow?.acid && watchlist.some((item) => item.acid === focusedRow.acid) ? focusedRow.acid : watchlist[0]?.acid
  const selectedExposure = selectedAcid ? model.exposureByAcid.get(selectedAcid) : null
  const selectedPosition = selectedAcid ? agentReview?.positionByAcid?.get(selectedAcid) : null
  const selectedHistory = selectedAcid ? model.signalHistoryByAcid?.[selectedAcid] : null
  const selectedSeries = selectedHistory?.series ?? []
  const trendSummary = buildTrendSummary(selectedSeries)
  const preferredItem = selectedPosition ?? selectedExposure ?? null
  const selectedIndex = watchlist.findIndex((item) => item.acid === selectedAcid)
  const overview = findRelevantNarrativeItem(agentReview?.review?.current_positioning ?? [], preferredItem, selectedIndex)
  const bull = findRelevantNarrativeItem(agentReview?.review?.bull_case ?? [], preferredItem, selectedIndex)
  const bear = findRelevantNarrativeItem(agentReview?.review?.bear_case ?? [], preferredItem, selectedIndex)
  const question = findRelevantNarrativeItem(agentReview?.review?.pm_questions ?? [], preferredItem, selectedIndex)
  const overviewText = buildPositionOverview(selectedPosition, selectedExposure, overview)
  const bullText = buildPositionBullCase(selectedPosition, bull)
  const bearText = buildPositionBearCase(selectedPosition, selectedExposure, bear)
  const pmQuestionText = buildPositionQuestion(selectedPosition, selectedExposure, question)
  const driverEntries = Object.entries(selectedPosition?.decomposition_values ?? {})
    .map(([label, value]) => ({ label, value: numberOrNull(value) ?? 0 }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 4)
  const totalDriverAbs = driverEntries.reduce((sum, item) => sum + Math.abs(item.value), 0) || 1
  const trustScore = trustScoreFromQuality(selectedPosition?.signal_quality)
  const monthlyRows = selectedSeries.filter((item) => item.vir_stf != null || item.algo_active_weight != null).slice(-6).reverse()

  return (
    <div className="ref-va-page">
      <div className="ref-va-toolbar">
        <div>
          <div className="card-title">Signal watchlist</div>
          <div className="ref-chart-caption">Largest current exposures with usable VIR or algo history.</div>
        </div>
        <div className="ref-va-watchlist">
          {watchlist.map((item) => (
            <button
              key={item.acid}
              type="button"
              className={`ref-va-pill ${item.acid === selectedAcid ? 'is-active' : ''}`}
              onClick={() => onFocusAcid(item.acid)}
            >
              <strong>{item.acid}</strong>
              <span>{formatWeight(item.active)}</span>
            </button>
          ))}
        </div>
      </div>

      {selectedAcid ? (
        <article className="ref-decomp-card ref-va-card">
          <div className="ref-dc-header">
            <div>
              <div className="ref-dc-title">{selectedAcid}</div>
              <div className="ref-dc-sub">
                {selectedExposure?.category || 'Signal view'} | active {formatWeight(selectedExposure?.active_rolled_exposure)} | VIR latest {formatAxisPercent(trendSummary.latestVir)} | algo latest {formatAxisPercent(trendSummary.latestAlgo)}
              </div>
            </div>
            <StatusBadge tone={selectedPosition ? alignmentToneForSignal(selectedPosition.signal_direction || selectedPosition.signal_alignment) : toneFromNumber(selectedExposure?.active_rolled_exposure)}>
              {selectedPosition ? humanizeKey(selectedPosition.signal_direction || selectedPosition.signal_alignment || 'unknown') : classifyAlignment(selectedExposure).label}
            </StatusBadge>
          </div>

          <div className="ref-va-main">
            <div className="ref-va-chart-card">
              <div className="ref-va-card-head">
                <div className="card-title">1 year signal path</div>
                <div className="ref-va-legend">
                  <span><i className="ref-dot vir" /> VIR STF</span>
                  <span><i className="ref-dot algo" /> Algo active weight</span>
                </div>
              </div>
              <SignalHistoryChart series={selectedSeries} />
              <div className="ref-path-caption">
                Window {monthYear(signalHistory.dateRange?.start)} to {monthYear(signalHistory.dateRange?.end)}. VIR currently loaded through {selectedHistory?.coverage?.vir_latest_date ? monthYear(selectedHistory.coverage.vir_latest_date) : '-'}.
              </div>
            </div>

            <aside className="ref-va-side">
              <div className="ref-va-side-grid">
                <MetricCell label="Current position" value={formatWeight(selectedExposure?.active_rolled_exposure)} tone={toneFromNumber(selectedExposure?.active_rolled_exposure)} />
                <MetricCell label="Latest VIR STF" value={formatAxisPercent(trendSummary.latestVir)} tone={toneFromNumber(trendSummary.latestVir)} />
                <MetricCell label="Latest algo" value={formatAxisPercent(trendSummary.latestAlgo)} tone={toneFromNumber(trendSummary.latestAlgo)} />
                <MetricCell label="VIR 3m" value={formatAxisPercent(trendSummary.vir3mDelta)} tone={toneFromNumber(trendSummary.vir3mDelta)} />
                <MetricCell label="Algo 3m" value={formatAxisPercent(trendSummary.algo3mDelta)} tone={toneFromNumber(trendSummary.algo3mDelta)} />
                <MetricCell label="History points" value={`${selectedHistory?.coverage?.vir_points ?? 0} VIR / ${selectedHistory?.coverage?.algo_points ?? 0} algo`} />
              </div>

              <div className="ref-va-compare">
                <div className="card-title">Current vs latest signals</div>
                <SignalCompareRow label="Position" value={selectedExposure?.active_rolled_exposure} format="weight" />
                <SignalCompareRow label="VIR STF" value={trendSummary.latestVir} format="signal" />
                <SignalCompareRow label="Algo active" value={trendSummary.latestAlgo} format="signal" />
              </div>

              <div className="ref-trust-row">
                <span>Signal quality</span>
                <div className="ref-trust-bar">
                  <div className={`ref-trust-fill tone-bg-${trustToneFromQuality(selectedPosition?.signal_quality)}`} style={{ width: `${trustScore}%` }} />
                </div>
                <code>{trustScore}%</code>
              </div>
            </aside>
          </div>

          <div className="ref-va-lower">
            <div className="ref-va-panel">
              <div className="card-title">Why it matters now</div>
              <div className="verdict-row">
                <span className="verdict-label">Read</span>
                <span className="verdict-text">{overviewText}</span>
              </div>

              {driverEntries.length ? (
                <div className="ref-driver-grid">
                  {driverEntries.map((driver) => (
                    <div key={driver.label} className={`ref-driver-block ${driver.label === selectedPosition?.decomposition_driver ? 'is-dominant' : ''}`}>
                      <div className="ref-driver-label">{humanizeKey(driver.label)}</div>
                      <div className={`ref-driver-val ${toneClass(driver.value)}`}>{formatMaybe(driver.value * 100)}%</div>
                      <div className="ref-driver-pct">{Math.round((Math.abs(driver.value) / totalDriverAbs) * 100)}%</div>
                    </div>
                  ))}
                </div>
              ) : null}

              <div className="question-box">
                <div className="qb-label">Question for PM</div>
                <div className="qb-text">{pmQuestionText}</div>
              </div>
            </div>

            <div className="ref-va-panel">
              <div className="ref-decomp-notes">
                <div className="bull-block ba-bull">
                  <div className="ba-title">Bull case</div>
                  <div className="ba-text">{bullText}</div>
                </div>
                <div className="bear-block ba-bear">
                  <div className="ba-title">Bear case</div>
                  <div className="ba-text">{bearText}</div>
                </div>
              </div>

              <div className="ref-va-monthly">
                <div className="card-title">Recent monthly values</div>
                {monthlyRows.length ? (
                  <div className="data-table compact">
                    <div className="table-row is-head">
                      <span>Month</span>
                      <span className="align-right">VIR STF</span>
                      <span className="align-right">Algo</span>
                    </div>
                    {monthlyRows.map((item) => (
                      <div key={item.date} className="table-row">
                        <span>{monthYear(item.date)}</span>
                        <code className={`align-right ${toneClass(item.vir_stf)}`}>{formatAxisPercent(item.vir_stf)}</code>
                        <code className={`align-right ${toneClass(item.algo_active_weight)}`}>{formatAxisPercent(item.algo_active_weight)}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState copy="No 12-month history was available for this ACID." />
                )}
              </div>
            </div>
          </div>
        </article>
      ) : (
        <EmptyState copy="No VIR / algo history is available for the current filter." />
      )}
    </div>
  )
}

function ReferenceFoFTab({ model }) {
  const [expanded, setExpanded] = useState(() => new Set())
  const rows = model.exposures
    .filter((row) => model.lineageByAcid[row.acid] && Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0.3)
    .slice(0, 12)

  const toggle = (acid) => {
    setExpanded((current) => {
      const next = new Set(current)
      if (next.has(acid)) {
        next.delete(acid)
      } else {
        next.add(acid)
      }
      return next
    })
  }

  const maxWeight = Math.max(
    1,
    ...rows.flatMap((row) => [Math.abs(numberOrNull(row.fund_target_rolled_exposure) ?? 0), Math.abs(numberOrNull(row.fund_benchmark_rolled_exposure) ?? 0)]),
  )

  return (
    <div className="ref-card">
      <div className="ref-card-pad">
        <div className="card-title">Look-through by exposure</div>
      </div>
      <div className="ref-fof-list">
        {rows.length ? (
          rows.map((row) => {
            const detail = model.lineageByAcid[row.acid]
            const isOpen = expanded.has(row.acid)
            return (
              <div key={row.acid}>
                <button type="button" className={`ref-fof-row ${isOpen ? 'is-open' : ''}`} onClick={() => toggle(row.acid)}>
                  <span className="ref-fof-acid">{row.acid}</span>
                  <div className="ref-fof-bars">
                    <div className="ref-fof-bar ref-fof-bar-bench" style={{ width: `${((numberOrNull(row.fund_benchmark_rolled_exposure) ?? 0) / maxWeight) * 100}%` }} />
                    <div className="ref-fof-bar ref-fof-bar-port" style={{ width: `${((numberOrNull(row.fund_target_rolled_exposure) ?? 0) / maxWeight) * 100}%` }} />
                  </div>
                  <div className="ref-fof-vals">
                    <code>{formatWeight(row.fund_target_rolled_exposure)}</code>
                    <code>{formatWeight(row.fund_benchmark_rolled_exposure)}</code>
                    <code className={toneClass(row.active_rolled_exposure)}>{formatWeight(row.active_rolled_exposure)}</code>
                  </div>
                </button>
                {isOpen ? (
                  <div className="ref-fof-detail">
                    <div className="ref-fof-meta">
                      <span>{detail.securityCount} securities contributing</span>
                      <span>{detail.byPath?.length ?? 0} sleeves / sources</span>
                    </div>
                    <div className="ref-fof-pill-wrap">
                      {(detail.securities ?? []).slice(0, 8).map((security) => (
                        <div key={security.identifier || security.securityName} className="ref-fof-pill">
                          <strong>{security.securityName}</strong>
                          <code>{formatWeight(security.activeContribution)}</code>
                          {(security.sources ?? []).slice(0, 3).map((source) => (
                            <span key={`${security.securityName}-${source.sourceName}`}>{source.sourceName} {formatWeight(source.activeContribution)}</span>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            )
          })
        ) : (
          <div className="ref-card-pad">
            <EmptyState copy="No look-through rows are available for the current fund filter." />
          </div>
        )}
      </div>
    </div>
  )
}

function ReferenceICTab({ model, focusedAcid }) {
  const items = buildReferenceICItems(model, focusedAcid)

  return (
    <div>
      {items.length ? (
        items.map((item, index) => (
          <article key={`${item.title}-${index}`} className="ref-ic-card">
            <div className="ref-ic-header">
              <div className="ref-ic-num">{index + 1}</div>
              <div>
                <div className="ref-ic-title">{item.title}</div>
                <div className="ref-ic-body">{item.body}</div>
              </div>
            </div>
            {item.evidence?.length ? (
              <div className="ref-ic-evidence">
                {item.evidence.map((evidence) => (
                  <span key={`${item.title}-${evidence}`} className="ref-ic-chip">{evidence}</span>
                ))}
              </div>
            ) : null}
          </article>
        ))
      ) : (
        <EmptyState copy="No IC prep items are available for this fund." />
      )}
    </div>
  )
}

function ReferenceMemoryTab({ model }) {
  const items = buildReferenceMemoryItems(model)

  return (
    <div className="ref-card ref-card-pad">
      {items.length ? (
        items.map((item, index) => (
          <article key={`${item.category}-${index}`} className="ref-mem-item">
            <div className={`ref-mem-dot tone-bg-${item.tone || 'neutral'}`} />
            <div className="ref-mem-content">
              <div className="ref-mem-category">{item.category}</div>
              <div className="ref-mem-text">{item.text}</div>
              <div className="ref-mem-meta">{item.meta}</div>
            </div>
          </article>
        ))
      ) : (
        <EmptyState copy="No agent memory entries are saved for this fund yet." />
      )}
    </div>
  )
}

function MetricCell({ label, value, tone = '' }) {
  return (
    <div className="ref-cc-cell">
      <div className="ref-cc-cell-label">{label}</div>
      <div className={`ref-cc-cell-val ${tone ? toneClassToText(tone) : ''}`}>{value || '-'}</div>
    </div>
  )
}

function MiniTrendLine({ current, delta }) {
  const prior = previousValue(current, delta)
  const values = [prior, current].map((value) => numberOrNull(value) ?? 0)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const points = values.map((value, index) => ({
    cx: index === 0 ? 10 : 90,
    cy: 90 - (((value - min) / range) * 70 + 10),
  }))

  return (
    <div className="ref-mini-line">
      <div className="ref-mini-axis" />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none">
        <line x1={points[0].cx} y1={points[0].cy} x2={points[1].cx} y2={points[1].cy} className="ref-mini-path" />
        {points.map((point, index) => (
          <circle key={`${point.cx}-${index}`} cx={point.cx} cy={point.cy} r="3.2" className="ref-mini-dot" />
        ))}
      </svg>
      <div className="ref-mini-label ref-mini-left">Prev {formatMaybe((prior ?? 0) * 100)}%</div>
      <div className="ref-mini-label ref-mini-right">Now {formatMaybe((numberOrNull(current) ?? 0) * 100)}%</div>
    </div>
  )
}

function SignalHistoryChart({ series }) {
  const width = 760
  const height = 260
  const padTop = 18
  const padRight = 14
  const padBottom = 34
  const padLeft = 52
  const plotted = series.filter((item) => item.vir_stf != null || item.algo_active_weight != null)

  if (!plotted.length) {
    return <EmptyState copy="No 12-month signal history is available for this ACID." />
  }

  const values = plotted.flatMap((item) => [numberOrNull(item.vir_stf), numberOrNull(item.algo_active_weight)]).filter((value) => value != null)
  const maxAbs = Math.max(...values.map((value) => Math.abs(value)), 0.01)
  const yMax = Math.max(maxAbs * 1.2, 0.02)
  const yMin = -yMax
  const plotWidth = width - padLeft - padRight
  const plotHeight = height - padTop - padBottom
  const zeroY = padTop + ((yMax - 0) / (yMax - yMin)) * plotHeight
  const xStep = plotted.length > 1 ? plotWidth / (plotted.length - 1) : 0

  const xForIndex = (index) => padLeft + index * xStep
  const yForValue = (value) => padTop + ((yMax - value) / (yMax - yMin)) * plotHeight
  const virPath = buildLinePath(plotted, 'vir_stf', xForIndex, yForValue)
  const algoPath = buildLinePath(plotted, 'algo_active_weight', xForIndex, yForValue)
  const tickValues = [yMax, yMax / 2, 0, yMin / 2, yMin]

  return (
    <div className="ref-signal-chart">
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-label="One year VIR and algo time series">
        {tickValues.map((tick) => (
          <g key={tick}>
            <line x1={padLeft} x2={width - padRight} y1={yForValue(tick)} y2={yForValue(tick)} className="ref-signal-grid" />
            <text x={padLeft - 10} y={yForValue(tick) + 4} className="ref-signal-y-label">
              {formatAxisPercent(tick)}
            </text>
          </g>
        ))}

        {plotted.map((item, index) => (
          <g key={item.date}>
            <line x1={xForIndex(index)} x2={xForIndex(index)} y1={padTop} y2={height - padBottom} className="ref-signal-vgrid" />
            <text x={xForIndex(index)} y={height - 12} textAnchor="middle" className="ref-signal-x-label">
              {shortMonth(item.date)}
            </text>
          </g>
        ))}

        <line x1={padLeft} x2={width - padRight} y1={zeroY} y2={zeroY} className="ref-signal-zero" />
        {virPath ? <path d={virPath} className="ref-signal-path vir" /> : null}
        {algoPath ? <path d={algoPath} className="ref-signal-path algo" /> : null}

        {plotted.map((item, index) => (
          <g key={`${item.date}-dots`}>
            {item.vir_stf != null ? <circle cx={xForIndex(index)} cy={yForValue(item.vir_stf)} r="3.5" className="ref-signal-dot vir" /> : null}
            {item.algo_active_weight != null ? <circle cx={xForIndex(index)} cy={yForValue(item.algo_active_weight)} r="3.5" className="ref-signal-dot algo" /> : null}
          </g>
        ))}

        <text x={18} y={height / 2} className="ref-signal-axis-title" transform={`rotate(-90 18 ${height / 2})`}>
          Signal value
        </text>
      </svg>
    </div>
  )
}

function SignalCompareRow({ label, value, format = 'weight' }) {
  const scale = 0.12
  const width = `${clamp((Math.abs(numberOrNull(value) ?? 0) / scale) * 100, 0, 100)}%`
  return (
    <div className="ref-compare-row">
      <span>{label}</span>
      <div className="ref-compare-track">
        <div className={`ref-compare-fill ${toneFromNumber(value)}`} style={{ width }} />
      </div>
      <code className={toneClass(value)}>{format === 'signal' ? formatAxisPercent(value) : formatWeight(value)}</code>
    </div>
  )
}

function buildVirAlgoWatchlist(model, materialPositions, focusedAcid) {
  const seed = []
  if (focusedAcid && model.exposureByAcid.has(focusedAcid)) {
    seed.push(model.exposureByAcid.get(focusedAcid))
  }
  for (const position of materialPositions) {
    seed.push(model.exposureByAcid.get(position.acid))
  }
  for (const row of model.signalRows) {
    seed.push(row)
  }

  const seen = new Set()
  return seed
    .filter(Boolean)
    .filter((row) => {
      if (!row?.acid || seen.has(row.acid)) {
        return false
      }
      seen.add(row.acid)
      return true
    })
    .map((row) => ({
      acid: row.acid,
      active: numberOrNull(row.active_rolled_exposure) ?? numberOrNull(row.active_weight) ?? 0,
    }))
    .filter((row) => model.signalHistoryByAcid?.[row.acid]?.coverage?.vir_points || model.signalHistoryByAcid?.[row.acid]?.coverage?.algo_points)
    .sort((a, b) => Math.abs(b.active) - Math.abs(a.active))
    .slice(0, 8)
}

function buildTrendSummary(series = []) {
  const latestVirIndex = findLatestSeriesIndex(series, 'vir_stf')
  const latestAlgoIndex = findLatestSeriesIndex(series, 'algo_active_weight')

  return {
    latestVir: latestVirIndex >= 0 ? numberOrNull(series[latestVirIndex]?.vir_stf) : null,
    latestAlgo: latestAlgoIndex >= 0 ? numberOrNull(series[latestAlgoIndex]?.algo_active_weight) : null,
    vir3mDelta: latestVirIndex >= 3 ? deltaBetweenSeriesPoints(series, latestVirIndex, latestVirIndex - 3, 'vir_stf') : null,
    algo3mDelta: latestAlgoIndex >= 3 ? deltaBetweenSeriesPoints(series, latestAlgoIndex, latestAlgoIndex - 3, 'algo_active_weight') : null,
  }
}

function findLatestSeriesIndex(series = [], field) {
  for (let index = series.length - 1; index >= 0; index -= 1) {
    if (numberOrNull(series[index]?.[field]) != null) {
      return index
    }
  }
  return -1
}

function deltaBetweenSeriesPoints(series = [], currentIndex, priorIndex, field) {
  const current = numberOrNull(series[currentIndex]?.[field])
  const prior = numberOrNull(series[priorIndex]?.[field])
  if (current == null || prior == null) {
    return null
  }
  return current - prior
}

function buildLinePath(series, field, xForIndex, yForValue) {
  const points = series
    .map((item, index) => {
      const value = numberOrNull(item[field])
      return value == null ? null : { x: xForIndex(index), y: yForValue(value) }
    })
    .filter(Boolean)

  if (!points.length) {
    return ''
  }

  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
}

function shortMonth(value) {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('en-US', {
    month: 'short',
  })
}

function formatAxisPercent(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return `${numeric > 0 ? '+' : ''}${(numeric * 100).toFixed(1)}%`
}

function scatterPointClass(row) {
  const alignment = classifyAlignment(row)
  if (alignment.key === 'opposite') {
    return 'is-conflict'
  }
  if (alignment.key === 'aligned') {
    return 'is-aligned'
  }
  return 'is-neutral'
}

function scatterPointStyle(row, maxActive) {
  const vir = numberOrNull(row.vir_stf) ?? 0
  const active = numberOrNull(row.active_rolled_exposure) ?? 0
  const left = clamp(((vir + 0.08) / 0.16) * 100, 5, 95)
  const top = clamp(50 - (active / Math.max(maxActive, 0.01)) * 40, 6, 94)
  return {
    left: `${left}%`,
    top: `${top}%`,
  }
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function toneClassToText(tone) {
  return tone === 'green' || tone === 'red' || tone === 'blue' || tone === 'amber' || tone === 'violet' ? `tone-text-${tone}` : ''
}

function trustScoreFromQuality(value = '') {
  if (value === 'improving') {
    return 74
  }
  if (value === 'stable') {
    return 61
  }
  if (value === 'weakening') {
    return 37
  }
  return 18
}

function trustToneFromQuality(value = '') {
  if (value === 'improving') {
    return 'green'
  }
  if (value === 'stable') {
    return 'blue'
  }
  if (value === 'weakening') {
    return 'amber'
  }
  return 'neutral'
}

function positionSourceDecks(position) {
  return (position?.source_refs ?? [])
    .map((item) => fileNameFromPath(item.artifact_path))
    .filter((name) => name && !name.endsWith('.csv') && !name.endsWith('.json'))
}

function findRelevantNarrativeItem(items = [], row = {}, fallbackIndex = 0) {
  if (!items.length) {
    return null
  }
  const aliases = narrativeAliases(row)
  const scored = items.map((item, index) => {
    const labelText = normalizeNarrativeText(item.label || '')
    const bodyText = normalizeNarrativeText(`${item.question || ''} ${item.statement || ''} ${item.view || ''} ${item.change || ''}`)
    const labelMatches = aliases.filter((alias) => labelText.includes(alias)).length
    const bodyMatches = aliases.filter((alias) => bodyText.includes(alias)).length
    const score = labelMatches * 100 + bodyMatches * 15 - Math.abs(index - fallbackIndex)
    return { item, labelMatches, bodyMatches, score, distance: Math.abs(index - fallbackIndex) }
  })

  scored.sort((a, b) => b.score - a.score || a.distance - b.distance)
  const best = scored[0]

  if (!best || best.score < 80) {
    return null
  }

  return best.item
}

function narrativeTokens(value = '') {
  return new Set(
    String(value)
      .toLowerCase()
      .replace(/united states/g, 'us')
      .replace(/information technology/g, 'tech')
      .split(/[^a-z0-9]+/)
      .filter((token) => token.length >= 2),
  )
}

function narrativeAliases(row = {}) {
  const aliases = new Set()
  const acid = String(row.acid || '')
  const label = String(row.label || '')
  const category = String(row.category || '')
  const mapping = row.mapping || {}

  addAliasVariants(aliases, acid)
  addAliasVariants(aliases, label)
  addAliasVariants(aliases, mapping.sector)
  addAliasVariants(aliases, mapping.style)
  addAliasVariants(aliases, mapping.asset_class_name)
  addAliasVariants(aliases, category)

  if (/\bUS IT EQ\b/.test(acid) || /technology/i.test(label)) {
    ;['it', 'tech', 'technology', 'information technology', 'us technology'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS FN EQ\b/.test(acid) || /financial/i.test(label)) {
    ;['financials', 'financial services', 'financial'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS ID EQ\b/.test(acid) || /industrial/i.test(label)) {
    ;['industrials', 'industrial'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS CD EQ\b/.test(acid) || /consumer discretionary/i.test(label)) {
    ;['consumer discretionary', 'consumer cyclical'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS HC EQ\b/.test(acid) || /health care/i.test(label)) {
    ;['health care', 'healthcare'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS LRG G EQ\b/.test(acid) || /lrg growth|large growth/i.test(label)) {
    ;['large growth', 'lrg growth'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS LRG V EQ\b/.test(acid) || /lrg value|large value/i.test(label)) {
    ;['large value', 'lrg value'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS MID V EQ\b/.test(acid) || /mid value/i.test(label)) {
    addAliasVariants(aliases, 'mid value')
  }
  if (/\bUS MID G EQ\b/.test(acid) || /mid growth/i.test(label)) {
    addAliasVariants(aliases, 'mid growth')
  }
  if (/\bUS SML G EQ\b/.test(acid) || /small growth|sml growth/i.test(label)) {
    ;['small growth', 'sml growth'].forEach((value) => addAliasVariants(aliases, value))
  }
  if (/\bUS SML V EQ\b/.test(acid) || /small value|sml value/i.test(label)) {
    ;['small value', 'sml value'].forEach((value) => addAliasVariants(aliases, value))
  }

  return [...aliases].filter((value) => value.length >= 2)
}

function addAliasVariants(target, value = '') {
  const normalized = normalizeNarrativeText(value)
  if (!normalized) {
    return
  }
  target.add(normalized)
  const compact = normalized.replace(/\s+/g, ' ')
  if (compact) {
    target.add(compact)
  }
}

function normalizeNarrativeText(value = '') {
  return String(value)
    .toLowerCase()
    .replace(/united states/g, 'us')
    .replace(/information technology/g, 'tech')
    .replace(/consumer discretionary/g, 'consumer cyclical')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function buildReferenceICItems(model, focusedAcid) {
  const agentReview = model.agentReview
  if (agentReview?.review?.follow_up?.length) {
    return agentReview.review.follow_up.map((item, index) => ({
      title: item.label || `Follow up ${index + 1}`,
      body: item.action,
      evidence: [
        focusedAcid && index === 0 ? focusedAcid : null,
        agentReview.packetReviewDate ? `Packet ${agentReview.packetReviewDate}` : null,
        model.snapshotMatrix.review ? `Review ${model.snapshotMatrix.review}` : null,
      ].filter(Boolean),
    }))
  }

  return model.reviewSections.map((section) => ({
    title: section.title,
    body: section.preview.join(' '),
    evidence: [focusedAcid || null].filter(Boolean),
  }))
}

function buildReferenceMemoryItems(model) {
  const agentReview = model.agentReview
  const items = []

  for (const flag of agentReview?.dataQualityFlags ?? []) {
    items.push({
      category: 'Data Quality',
      text: flag.message,
      meta: `${flag.severity || 'info'} | ${agentReview.packetReviewDate || model.snapshotMatrix.review || '-'}`,
      tone: flag.severity === 'medium' ? 'amber' : 'blue',
    })
  }

  for (const item of agentReview?.review?.dashboard_highlights ?? []) {
    items.push({
      category: item.label || 'Highlight',
      text: item.highlight,
      meta: `Review ${agentReview.manifest.review_date || model.snapshotMatrix.review || '-'}`,
      tone: item.label?.includes('DATA QUALITY') ? 'amber' : 'blue',
    })
  }

  for (const item of (agentReview?.sharepointHighlights ?? []).slice(0, 4)) {
    items.push({
      category: 'SharePoint Research',
      text: truncate(item.summary_text, 220),
      meta: `${item.label || item.acid} | ${fileNameFromPath(item.full_path || item.file_name || '')}`,
      tone: 'green',
    })
  }

  return items.slice(0, 10)
}

function buildPositionOverview(selectedPosition, selectedExposure, overview) {
  const parts = []
  if (selectedExposure?.active_rolled_exposure != null && selectedExposure?.fund_benchmark_rolled_exposure != null) {
    parts.push(`Active weight ${formatWeight(selectedExposure.active_rolled_exposure)} vs benchmark ${formatWeight(selectedExposure.fund_benchmark_rolled_exposure)}.`)
  }
  if (selectedPosition?.vir_now != null || selectedPosition?.algo_active_weight != null) {
    parts.push(`VIR ${formatAxisPercent(selectedPosition?.vir_now)} and algo ${formatAxisPercent(selectedPosition?.algo_active_weight)}.`)
  }
  if (selectedPosition?.decomposition_driver) {
    parts.push(`Primary decomposition driver: ${humanizeKey(selectedPosition.decomposition_driver)}.`)
  }
  if (selectedPosition?.sample_source_securities) {
    parts.push(`Main holdings include ${truncate(selectedPosition.sample_source_securities, 160)}.`)
  }
  return parts.join(' ') || overview?.evidence || overview?.view || describeSignalRow(selectedExposure)
}

function buildPositionBullCase(selectedPosition, bull) {
  if (selectedPosition?.sharepoint_research_summary) {
    return selectedPosition.sharepoint_research_summary
  }
  if (selectedPosition?.decomposition_assessment === 'broad_based' && selectedPosition?.vir_now != null) {
    return `The signal is broad-based rather than narrowly mechanical, with VIR at ${formatAxisPercent(selectedPosition.vir_now)} and supporting decomposition breadth.`
  }
  return bull?.statement || 'Matched research and current positioning offer a constructive read, but it still needs to be weighed against live pricing.'
}

function buildPositionBearCase(selectedPosition, selectedExposure, bear) {
  if (selectedPosition?.decomposition_assessment && ['valuation_led', 'currency_led'].includes(selectedPosition.decomposition_assessment)) {
    return `The current signal leans heavily on ${humanizeKey(selectedPosition.decomposition_driver)}, which makes the setup less durable if that driver fades.`
  }
  if (selectedPosition?.internal_history_excerpt) {
    return selectedPosition.internal_history_excerpt
  }
  if (selectedExposure?.active_rolled_exposure != null) {
    return `At ${formatWeight(selectedExposure.active_rolled_exposure)}, this remains a meaningful active bet that can hurt relative performance if the current thesis is wrong.`
  }
  return bear?.statement || 'The saved internal history does not fully eliminate the risk that this remains a stale or crowded thesis.'
}

function buildPositionQuestion(selectedPosition, selectedExposure, question) {
  if (question?.question) {
    return question.question
  }
  if (selectedPosition?.decomposition_assessment && ['valuation_led', 'currency_led'].includes(selectedPosition.decomposition_assessment)) {
    return `Does the team still want this exposure at ${formatWeight(selectedExposure?.active_rolled_exposure)} if the current signal is being carried mostly by ${humanizeKey(selectedPosition.decomposition_driver)}?`
  }
  return 'How should this position be sized given the current VIR direction, algo stance, and the internal thesis carried over from prior reviews?'
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
      : tabId === 'challenge'
        ? buildChallengeCards(model).length
        : tabId === 'decomp'
          ? model.signalRows.length
          : tabId === 'fof'
            ? model.exposures.filter((row) => model.lineageByAcid[row.acid] && Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0) >= 0.3).length
        : tabId === 'ic'
          ? model.reviewSections.length
          : model.agentReview?.dataQualityFlags?.length ?? model.changeBrief.evidence_index?.length ?? 0

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

function AgentNarrativeSection({ title, items, tone = 'neutral' }) {
  if (!items?.length) {
    return <EmptyState copy={`No ${title.toLowerCase()} available.`} />
  }

  return (
    <div className="agent-narrative-section">
      <div className="agent-section-head">
        <h3>{title}</h3>
        <StatusBadge tone={tone}>{items.length}</StatusBadge>
      </div>
      <div className="agent-narrative-list">
        {items.map((item, index) => {
          const primary = item.view || item.statement || item.question || item.action || item.change || item.highlight || ''
          const secondary = item.evidence || item.why_now || item.why_it_matters || ''

          return (
            <article key={`${title}-${item.label || index}`} className="agent-narrative-card">
              <h4>{item.label || `${title} ${index + 1}`}</h4>
              {primary ? <p>{primary}</p> : null}
              {secondary ? <div className="inline-note tone-neutral">{secondary}</div> : null}
            </article>
          )
        })}
      </div>
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
  const agentReview = buildAgentReview(agent2RunsByFund[fundName] ?? null)

  const exposures = buildExposureRows(fundName)
  const exposureByAcid = new Map(exposures.map((row) => [row.acid, row]))
  const signalHistoryByAcid = signalHistoryByFund[fundName]?.acids ?? {}
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
    signalHistoryByAcid,
    coverageBreakdown,
    reviewMarkdown,
    reviewSections,
    agentReview,
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
    label: row.acid,
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

function buildAgentReview(agentPayload) {
  if (!agentPayload?.review || !agentPayload?.manifest || !agentPayload?.packet) {
    return null
  }

  const materialPositions = (agentPayload.packet.material_positions ?? [])
    .map((position) => ({
      ...position,
      active_weight: numberOrNull(position.active_weight),
      portfolio_weight: numberOrNull(position.portfolio_weight),
      benchmark_weight: numberOrNull(position.benchmark_weight),
      vir_now: numberOrNull(position.vir_now),
      algo_active_weight: numberOrNull(position.algo_active_weight),
      importance_score: numberOrNull(position.importance_score),
    }))
    .sort((a, b) => Math.abs(numberOrNull(b.active_weight) ?? 0) - Math.abs(numberOrNull(a.active_weight) ?? 0))

  const packetReviewDate = agentPayload.packet.run_metadata?.review_date || agentPayload.packet.header?.review_date || ''
  const sharepointHighlights = buildResearchHighlights(agentPayload.packet.sharepoint_research_summary ?? [], materialPositions)
  const matchedResearchCount = numberOrNull(agentPayload.packet.run_metadata?.matched_sharepoint_research_count) ?? sharepointHighlights.length
  const hasFreshNarrative = !packetReviewDate || !agentPayload.manifest.review_date || packetReviewDate === agentPayload.manifest.review_date

  return {
    review: hasFreshNarrative ? agentPayload.review : buildPacketDrivenReview(agentPayload.packet, materialPositions, sharepointHighlights),
    manifest: agentPayload.manifest,
    packet: agentPayload.packet,
    materialPositions,
    positionByAcid: new Map(materialPositions.map((position) => [position.acid, position])),
    dataQualityFlags: agentPayload.packet.data_quality_flags ?? [],
    packetReviewDate,
    matchedResearchCount,
    sharepointHighlights,
    hasFreshNarrative,
  }
}

function buildPacketDrivenReview(packet, materialPositions, sharepointHighlights) {
  const signalSummary = packet?.signal_summary ?? {}
  const fundSnapshot = packet?.fund_snapshot ?? {}
  const challengeBook = packet?.challenge_book ?? []
  const topMovers = packet?.top_movers ?? []
  const portfolioImplications = packet?.portfolio_implications ?? []
  const roadmap = packet?.roadmap ?? []
  const pmQuestions = packet?.pm_questions ?? []
  const qualityFlags = packet?.data_quality_flags ?? []
  const aligned = signalSummary.aligned_positions ?? []
  const diverging = signalSummary.diverging_positions ?? []
  const headlineSummary = fundSnapshot.headline_summary ?? []
  const largestOverweights = fundSnapshot.largest_overweights ?? []
  const largestUnderweights = fundSnapshot.largest_underweights ?? []
  const improvingMovers = topMovers.filter((item) => (numberOrNull(item.vir_delta_mom) ?? 0) > 0).slice(0, 3)
  const weakeningMovers = topMovers.filter((item) => (numberOrNull(item.vir_delta_mom) ?? 0) < 0).slice(0, 3)
  const highPriorityChallenges = challengeBook.filter((item) => item.priority === 'high').slice(0, 4)
  const mediumChallenges = challengeBook.filter((item) => item.priority !== 'high').slice(0, 3)

  const executiveSummaryParts = [
    ...headlineSummary,
    ...(signalSummary.fund_level_observations ?? []).slice(0, 2),
  ].filter(Boolean)

  return {
    executive_summary:
      executiveSummaryParts.join(' ') ||
      'The latest structured packet is loaded, but no current live narrative is available for this review month yet.',
    current_positioning: [
      ...largestUnderweights.slice(0, 2).map((item) => ({
        label: `${item.label} underweight`,
        statement: `${item.label} is a ${formatWeight(item.active_weight)} active underweight versus the benchmark.`,
        evidence: buildPositionEvidence(item, materialPositions),
      })),
      ...largestOverweights.slice(0, 2).map((item) => ({
        label: `${item.label} overweight`,
        statement: `${item.label} is a ${formatWeight(item.active_weight)} active overweight versus the benchmark.`,
        evidence: buildPositionEvidence(item, materialPositions),
      })),
    ],
    bull_case: [
      ...aligned.slice(0, 3).map((item) => ({
        label: `${item.label} aligned`,
        statement: `${item.label} is ${formatWeight(item.active_weight)} active and the current positioning direction is aligned with both VIR and algo.`,
        evidence: `${item.category} | alignment ${item.signal_alignment}`,
      })),
      ...improvingMovers.map((item) => ({
        label: `${item.label} improving`,
        statement: `${item.label} moved by ${formatSignal(item.vir_delta_mom)} month over month, with ${humanizeDriver(item.decomposition_driver)} as the main driver.`,
        evidence: `${item.category} | VIR now ${formatSignal(item.vir_now)} | active ${formatWeight(item.active_weight)}`,
      })),
    ].slice(0, 5),
    bear_case: [
      ...highPriorityChallenges.map((item) => ({
        label: item.label,
        statement: item.reason,
        evidence: item.question,
      })),
      ...weakeningMovers.map((item) => ({
        label: `${item.label} weakening`,
        statement: `${item.label} moved by ${formatSignal(item.vir_delta_mom)} month over month, which weakens the current signal backdrop.`,
        evidence: `${item.category} | VIR now ${formatSignal(item.vir_now)} | active ${formatWeight(item.active_weight)}`,
      })),
    ].slice(0, 5),
    devils_advocate: [
      ...portfolioImplications.slice(0, 3).map((item, index) => ({
        label: humanizeKey(item.type || `counterpoint_${index + 1}`),
        statement: item.statement,
      })),
      ...mediumChallenges.slice(0, 2).map((item) => ({
        label: `${item.label} follow-through`,
        statement: item.reason,
        evidence: item.question,
      })),
    ].slice(0, 5),
    pm_questions: pmQuestions.slice(0, 7),
    follow_up: [
      ...roadmap.slice(0, 5).map((item) => ({
        label: item.acid || 'Next step',
        action: item.step,
      })),
      ...qualityFlags.slice(0, 2).map((item) => ({
        label: humanizeKey(item.flag || 'data_quality'),
        action: item.message,
      })),
    ],
    dashboard_highlights: [
      ...headlineSummary.map((highlight, index) => ({
        label: `Packet highlight ${index + 1}`,
        highlight,
      })),
      ...sharepointHighlights.slice(0, 2).map((item) => ({
        label: item.label || item.acid,
        highlight: `${item.file_name || fileNameFromPath(item.full_path)} matched to ${item.acid}.`,
      })),
    ],
  }
}

function buildPositionEvidence(item, materialPositions) {
  const matched = materialPositions.find((position) => position.label === item.label || position.acid === item.acid)
  if (!matched) {
    return `${item.category || item.group || 'Exposure'} | benchmark ${formatWeight(item.benchmark_weight)} | portfolio ${formatWeight(item.portfolio_weight)}`
  }
  return `${matched.category} | benchmark ${formatWeight(matched.benchmark_weight)} | portfolio ${formatWeight(matched.portfolio_weight)} | VIR ${formatSignal(matched.vir_now)} | algo ${formatWeight(matched.algo_active_weight)}`
}

function humanizeDriver(value = '') {
  return humanizeKey(String(value || '').replace(/_/g, ' ')).replace(/\bUsd\b/g, 'USD')
}

function buildResearchHighlights(rows, materialPositions) {
  const positionsByAcid = new Map(materialPositions.map((position) => [position.acid, position]))

  return [...rows]
    .map((item) => {
      const position = positionsByAcid.get(item.acid)
      return {
        ...item,
        active_weight: numberOrNull(position?.active_weight),
        category: position?.category ?? '',
      }
    })
    .sort((a, b) => {
      const activeDelta = Math.abs(numberOrNull(b.active_weight) ?? 0) - Math.abs(numberOrNull(a.active_weight) ?? 0)
      if (activeDelta !== 0) {
        return activeDelta
      }
      return (numberOrNull(b.confidence) ?? 0) - (numberOrNull(a.confidence) ?? 0)
    })
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
    signalHistoryByAcid: Object.fromEntries(exposures.map((row) => [row.acid, model.signalHistoryByAcid[row.acid]]).filter(([, value]) => value)),
    agentReview: filterAgentReview(model.agentReview, allowed),
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

function filterAgentReview(agentReview, allowed) {
  if (!agentReview) {
    return null
  }

  const materialPositions = agentReview.materialPositions.filter((position) => allowed.has(position.acid))

  return {
    ...agentReview,
    materialPositions,
    positionByAcid: new Map(materialPositions.map((position) => [position.acid, position])),
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

function buildExposureLeaders(model) {
  if (model.agentReview?.packet?.fund_snapshot) {
    const snapshot = model.agentReview.packet.fund_snapshot
    return {
      overweights: (snapshot.largest_overweights ?? []).map((row) => ({
        acid: findExposureAcid(model, row.label),
        label: row.label,
        active_weight: numberOrNull(row.active_weight),
      })),
      underweights: (snapshot.largest_underweights ?? []).map((row) => ({
        acid: findExposureAcid(model, row.label),
        label: row.label,
        active_weight: numberOrNull(row.active_weight),
      })),
    }
  }

  const sorted = [...model.exposures].sort((a, b) => Math.abs(numberOrNull(b.active_rolled_exposure) ?? 0) - Math.abs(numberOrNull(a.active_rolled_exposure) ?? 0))
  return {
    overweights: sorted
      .filter((row) => (numberOrNull(row.active_rolled_exposure) ?? 0) > 0)
      .slice(0, 5)
      .map((row) => ({ acid: row.acid, label: row.acid, active_weight: row.active_rolled_exposure })),
    underweights: sorted
      .filter((row) => (numberOrNull(row.active_rolled_exposure) ?? 0) < 0)
      .slice(0, 5)
      .map((row) => ({ acid: row.acid, label: row.acid, active_weight: row.active_rolled_exposure })),
  }
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

function findExposureAcid(model, label) {
  const match = model.exposures.find((row) => normalizeLabel(row.acid) === normalizeLabel(label) || normalizeLabel(row.label) === normalizeLabel(label))
  return match?.acid ?? ''
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

function alignmentToneForSignal(value = '') {
  if (value === 'aligned') {
    return 'green'
  }
  if (value === 'diverging') {
    return 'red'
  }
  if (value === 'partially_aligned') {
    return 'amber'
  }
  return 'neutral'
}

function readViewStateFromUrl(fundDirectory, preferredSlug) {
  const allowedTabIds = new Set(tabs.map((tab) => tab.id))
  const allowedPortfolioViews = new Set(['new', 'target', 'bench'])
  const allowedCategories = new Set([defaultCategory, ...categoryOrder])

  if (typeof window === 'undefined') {
    return {
      selectedSlug: preferredSlug,
      activeTab: defaultTabId,
      selectedCategory: defaultCategory,
      selectedAcid: '',
      portfolioView: defaultPortfolioView,
    }
  }

  const params = new URLSearchParams(window.location.search)
  const requestedSlug = params.get('fund') || ''
  const selectedSlug = fundDirectory.some((fund) => fund.slug === requestedSlug) ? requestedSlug : preferredSlug
  const requestedTab = params.get('tab') || ''
  const requestedCategory = params.get('category') || ''
  const requestedPortfolioView = params.get('view') || ''

  return {
    selectedSlug,
    activeTab: allowedTabIds.has(requestedTab) ? requestedTab : defaultTabId,
    selectedCategory: allowedCategories.has(requestedCategory) ? requestedCategory : defaultCategory,
    selectedAcid: params.get('acid') || '',
    portfolioView: allowedPortfolioViews.has(requestedPortfolioView) ? requestedPortfolioView : defaultPortfolioView,
  }
}

function buildViewSearchParams({ fundSlug, activeTab, selectedCategory, selectedAcid, portfolioView }) {
  const params = new URLSearchParams()
  params.set('fund', fundSlug || '')
  params.set('tab', activeTab || defaultTabId)
  params.set('category', selectedCategory || defaultCategory)
  params.set('view', portfolioView || defaultPortfolioView)
  if (selectedAcid) {
    params.set('acid', selectedAcid)
  }
  return params
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

function formatCurrency(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return numeric.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatInteger(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return Math.round(numeric).toLocaleString('en-US')
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

function shortModelName(value = '') {
  const parts = String(value).split('.')
  return parts[parts.length - 1] || value || '-'
}

function reviewRunSubtitle(agentReview) {
  if (!agentReview) {
    return 'No Bedrock review loaded'
  }
  if (agentReview.hasFreshNarrative) {
    return `Live Bedrock review | ${monthYear(agentReview.manifest.logical_snapshot_date)}`
  }
  return `Packet-derived review | refreshed ${agentReview.packetReviewDate || '-'} | last live run ${agentReview.manifest.review_date || '-'}`
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

function normalizeLabel(value = '') {
  return String(value)
    .toLowerCase()
    .replace(/united states/g, 'us')
    .replace(/information technology/g, 'it')
    .replace(/[^a-z0-9]+/g, '')
}

function slugify(value = '') {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function fileNameFromPath(value = '') {
  const normalized = String(value).replaceAll('\\', '/')
  return normalized.split('/').pop() || value || '-'
}
