import { startTransition, useEffect, useMemo, useState } from 'react'
import bundle from './data/monthlyReviewBundle.json'
import exposureLineage from './data/exposureLineage.json'
import fundWeightsVirAlgo from './data/fundWeightsVirAlgo.json'

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'stf-vir', label: 'STF / VIR' },
  { id: 'positions', label: 'Positions' },
  { id: 'pm-review', label: 'PM Review' },
  { id: 'signals', label: 'Signals' },
  { id: 'challenges', label: 'Challenges' },
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

const sectorCodeLabels = {
  CD: 'Consumer Defensive',
  CS: 'Consumer Cyclical',
  EN: 'Energy',
  FN: 'Financials',
  HC: 'Healthcare',
  ID: 'Industrials',
  IT: 'Technology',
  MT: 'Basic Materials',
  RE: 'Real Estate',
  TL: 'Communication Services',
  UT: 'Utilities',
}

export default function App() {
  const [selectedSlug, setSelectedSlug] = useState(bundle.funds[0]?.slug ?? '')
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedExposureAcid, setSelectedExposureAcid] = useState('')
  const [openPositionAcids, setOpenPositionAcids] = useState(() => new Set())

  const selectedFund = bundle.funds.find((fund) => fund.slug === selectedSlug) ?? bundle.funds[0]
  const model = useMemo(() => buildFundModel(selectedFund), [selectedFund])
  const visibleModel = useMemo(() => filterModelByCategory(model, selectedCategory), [model, selectedCategory])

  useEffect(() => {
    if (!visibleModel.exposures.length) {
      return
    }
    const exists = visibleModel.exposureByAcid.has(selectedExposureAcid)
    if (!exists) {
      setSelectedExposureAcid(visibleModel.exposures[0].acid)
    }
  }, [visibleModel.exposureByAcid, visibleModel.exposures, selectedExposureAcid])

  const selectedExposure =
    visibleModel.exposureByAcid.get(selectedExposureAcid) ??
    visibleModel.exposures[0] ??
    null

  const changeFund = (slug) => {
    startTransition(() => {
      setSelectedSlug(slug)
      setOpenPositionAcids(new Set())
      setSelectedExposureAcid('')
      setSelectedCategory('All')
    })
  }

  const changeTab = (tabId) => {
    startTransition(() => setActiveTab(tabId))
  }

  const selectExposure = (acid) => {
    startTransition(() => setSelectedExposureAcid(acid))
  }

  const togglePosition = (acid) => {
    setOpenPositionAcids((current) => {
      const next = new Set(current)
      if (next.has(acid)) {
        next.delete(acid)
      } else {
        next.add(acid)
      }
      return next
    })
  }

  return (
    <div className="pm-shell">
      <header className="topbar">
        <div className="topbar-product">
          <span className="brand-mark">PM</span>
          <span className="product-name">Review Workspace</span>
        </div>

        <h1 title={selectedFund.fund}>{selectedFund.fund}</h1>

        <div className="topbar-meta" aria-label="Run metadata">
          <MetaChip label="Snapshot" value={bundle.snapshot_date} />
          <MetaChip label="As of" value={bundle.as_of_date} />
          <MetaChip label="Run ID" value={selectedFund.review_run_id || model.metadata.review_run_id || '-'} />
          <StatusChip firedCount={model.triggerSummary.fired_count ?? 0} challengeCount={model.challenges.length} />
        </div>
      </header>

      <div className="workspace-body">
        <aside className="sidebar">
          <section className="bundle-header">
            <span className="section-kicker">Bundle</span>
            <div className="bundle-stats">
              <MetricPair label="Snapshot" value={bundle.snapshot_date} />
              <MetricPair label="Funds" value={String(bundle.funds.length)} />
              <MetricPair label="Generated" value={formatDateTime(bundle.bundle_generated_at)} />
            </div>
          </section>

          <section className="fund-section">
            <div className="sidebar-heading">
              <span className="section-kicker">Funds</span>
              <strong>{bundle.funds.length}</strong>
            </div>
            <div className="fund-list">
              {bundle.funds.map((fund) => {
                const counts = getFundCounts(fund)
                const active = fund.slug === selectedFund.slug
                return (
                  <button
                    key={fund.slug}
                    type="button"
                    className={`fund-entry ${active ? 'is-active' : ''}`}
                    onClick={() => changeFund(fund.slug)}
                    aria-pressed={active}
                  >
                    <span className="fund-abbr">{fundAbbreviation(fund.fund)}</span>
                    <span className="fund-copy">
                      <strong>{fund.fund}</strong>
                      <span className="fund-pills">{renderFundPills(counts)}</span>
                    </span>
                  </button>
                )
              })}
            </div>
          </section>
        </aside>

        <main className="main-column">
          <nav className="tabbar" role="tablist" aria-label="PM review workspace views">
            {tabs.map((tab) => {
              const badge = getTabBadge(tab.id, model)
              return (
                <button
                  key={tab.id}
                  type="button"
                  className={`tab-button ${activeTab === tab.id ? 'is-active' : ''}`}
                  onClick={() => changeTab(tab.id)}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                >
                  <span>{tab.label}</span>
                  {badge ? <span className={`tab-badge ${badge.tone}`}>{badge.label}</span> : null}
                </button>
              )
            })}
          </nav>

          <div className="filterbar" aria-label="Category filters">
            <span className="filterbar-label">Category</span>
            <div className="filter-chip-row">
              {['All', ...model.availableCategories].map((category) => (
                <button
                  key={category}
                  type="button"
                  className={`filter-chip ${selectedCategory === category ? 'is-active' : ''}`}
                  onClick={() => startTransition(() => setSelectedCategory(category))}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          <div className="content-scroll">
            {activeTab === 'overview' ? (
              <OverviewTab
                model={visibleModel}
                selectedExposure={selectedExposure}
                onSelectExposure={selectExposure}
                selectedCategory={selectedCategory}
              />
            ) : null}
            {activeTab === 'stf-vir' ? (
              <STFVIRTab
                model={visibleModel}
                selectedExposure={selectedExposure}
                onSelectExposure={selectExposure}
                selectedCategory={selectedCategory}
              />
            ) : null}
            {activeTab === 'positions' ? (
              <PositionsTab
                movers={visibleModel.movers}
                maxMoverActive={visibleModel.maxMoverActive}
                challengeByAcid={visibleModel.challengeByAcid}
                openPositionAcids={openPositionAcids}
                onToggle={togglePosition}
              />
            ) : null}
            {activeTab === 'pm-review' ? <PMReviewTab model={visibleModel} /> : null}
            {activeTab === 'signals' ? <SignalsTab model={visibleModel} /> : null}
            {activeTab === 'challenges' ? <ChallengesTab model={visibleModel} /> : null}
          </div>
        </main>
      </div>
    </div>
  )
}

function OverviewTab({ model, selectedExposure, onSelectExposure }) {
  const signalAlignment = model.signalAlignment

  return (
    <div className="overview-view">
      <section className="review-summary">
        <PanelHeader kicker="Review Summary" title="Current State" />
        <p>{model.changeBrief.executive_summary || 'No executive summary is available for this fund.'}</p>
      </section>

      <section className="kpi-strip" aria-label="Fund review statistics">
        <KpiTile label="Coverage" value={formatPercent(model.coverage.target_match_pct)} subLabel="target match" tone="info" />
        <KpiTile
          label="Triggers Fired"
          value={String(model.triggerSummary.fired_count ?? 0)}
          subLabel={`of ${model.triggerSummary.candidate_count ?? model.exposures.length} candidates`}
          tone="warning"
        />
        <KpiTile
          label="Challenges"
          value={String(model.challenges.length)}
          subLabel={model.challenges.length ? 'active review items' : 'no active items'}
          tone={model.challenges.length ? 'alert' : 'quiet'}
        />
        <KpiTile
          label="Theses"
          value={String(model.memorySummary.thesis_ledger_count ?? 0)}
          subLabel="ledger entries"
          tone="neutral"
        />
        <KpiTile
          label="Signal Alignment"
          value={signalAlignment ? formatPercent(signalAlignment.ratio) : '-'}
          subLabel={signalAlignment ? `${signalAlignment.agree}/${signalAlignment.total} unique ACIDs` : 'no signal rows'}
          tone="positive"
        />
        <KpiTile
          label="Borderline"
          value={String(model.triggerSummary.borderline_count ?? 0)}
          subLabel="near trigger"
          tone="info"
        />
      </section>

      <section className="overview-grid overview-grid-explorer">
        <div className="section-panel waterfall-panel">
          <PanelHeader kicker="Active Exposure Explorer" title="Sorted by Category" meta={`${model.exposures.length} exposures`} />
          <div className="grouped-waterfall">
            {model.exposureGroups.map((group) => (
              <section key={group.category} className="exposure-group">
                <div className="group-header">
                  <h3>{group.category}</h3>
                  <span>{formatWeight(group.totalActive)}</span>
                </div>
                <div className="waterfall-list">
                  {group.items.map((item) => (
                    <button
                      key={item.acid}
                      type="button"
                      className={`waterfall-row is-clickable ${selectedExposure?.acid === item.acid ? 'is-selected' : ''} ${model.challengeByAcid.has(item.acid) ? 'is-challenge' : ''} ${item.acid_type === 'acid_bond' ? 'is-bond' : ''}`}
                      onClick={() => onSelectExposure(item.acid)}
                    >
                      <div className="waterfall-name">
                        <strong>{item.acid}</strong>
                        <span>{exposureSubtitle(item)}</span>
                      </div>
                      <div className="waterfall-bar" style={{ '--bar-width': `${getRelativeWidth(item.active_rolled_exposure, model.maxExposureActive, 48)}%` }}>
                        <span className={`bar-fill ${numberOrNull(item.active_rolled_exposure) >= 0 ? 'is-positive' : 'is-negative'}`} />
                      </div>
                      <strong className={toneForNumber(item.active_rolled_exposure)}>{formatWeight(item.active_rolled_exposure)}</strong>
                      <span className="waterfall-vir">
                        VIR {formatMaybe(item.vir_stf)} / Algo {formatMaybe(item.algo_active_weight)}
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>

        <div className="overview-side overview-side-rich">
          <ExposureLineagePanel exposure={selectedExposure} lineage={selectedExposure ? model.lineageByAcid[selectedExposure.acid] : null} />
          <ExposureSplit exposures={model.exposures} />
          {model.virRows.length ? <VirDirection rows={model.virRows} /> : null}
          <MemoryState memorySummary={model.memorySummary} triggerSummary={model.triggerSummary} />
        </div>
      </section>

      {model.challenges.length ? <ChallengeCallout challenges={model.challenges} moverByAcid={model.moverByAcid} /> : null}

      {hasContent(model.changeBrief.decomposition_narrative) ? (
        <section className="decomposition-note">
          <PanelHeader kicker="Decomposition Note" title="Context" />
          <p>{model.changeBrief.decomposition_narrative}</p>
        </section>
      ) : null}
    </div>
  )
}

function ExposureLineagePanel({ exposure, lineage }) {
  if (!exposure) {
    return <EmptyMiniPanel title="Exposure Lineage" copy="Select an exposure to inspect the underlying names and paths." />
  }

  return (
    <section className="section-panel side-panel lineage-panel">
      <PanelHeader kicker="Exposure Drilldown" title={exposure.acid} meta={classifyExposure(exposure)} />
      <div className="lineage-header">
        <div className="tag-row">
          <Tag label={exposureLabel(exposure.active_rolled_exposure)} tone={exposureTone(exposure.active_rolled_exposure)} />
          {lineage ? <Tag label={`${lineage.securities.length} aggregated names`} tone="neutral" /> : null}
          {exposure.sample_source_securities ? <Tag label={`${exposure.source_security_count || '?'} source rows`} tone="neutral" /> : null}
        </div>
        <p>{buildExposureSummary(exposure, lineage)}</p>
      </div>

      {lineage ? (
        <>
          <div className="lineage-top-grid">
            <MetricPair label="Security rows" value={String(lineage.securityCount)} />
            <MetricPair label="Path buckets" value={String(lineage.byPath.length)} />
          </div>

          <div className="lineage-section">
            <div className="subsection-head">
              <h3>Security Totals</h3>
              <span>Same name summed across sleeves</span>
            </div>
            <div className="driver-list">
              {lineage.securities.slice(0, 6).map((item) => (
                <article key={`${item.securityName}-${item.identifier}`} className="driver-row">
                  <div className="driver-main">
                    <strong>{item.securityName}</strong>
                    <p>{item.identifier || 'No identifier'}</p>
                    <div className="source-breakdown">
                      {item.sources.map((source) => (
                        <div key={`${item.securityName}-${source.sourceName}-${source.portcode}`} className="source-row">
                          <span>{source.sourceName}</span>
                          <b className={toneForNumber(source.activeContribution)}>{formatWeight(source.activeContribution)}</b>
                        </div>
                      ))}
                    </div>
                  </div>
                  <b className={toneForNumber(item.activeContribution)}>{formatWeight(item.activeContribution)}</b>
                </article>
              ))}
            </div>
          </div>

          <div className="lineage-section">
            <div className="subsection-head">
              <h3>Where It Is Coming From</h3>
              <span>Path clusters inside the fund</span>
            </div>
            <div className="micro-bars">
              {lineage.byPath.slice(0, 5).map((item) => (
                <MicroBar key={item.path} label={item.path} value={item.activeContribution} maxValue={lineage.totalActiveContribution || 1} detail={`${item.rows} source rows`} compact />
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="lineage-fallback">
          <p>No full lineage rows are available for this exposure, so the panel falls back to the sampled source names from the summary layer.</p>
          {exposure.sample_source_securities ? (
            <div className="fallback-chip-list">
              {exposure.sample_source_securities.split(';').slice(0, 8).map((name) => (
                <span key={name.trim()} className="fallback-chip">
                  {name.trim()}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}

function PositionsTab({ movers, maxMoverActive, challengeByAcid, openPositionAcids, onToggle }) {
  if (!movers.length) {
    return <EmptyPanel title="No Material Movers" copy="No material mover rows are available for this fund." />
  }

  return (
    <div className="positions-view">
      {movers.map((mover) => (
        <PositionCard
          key={mover.acid}
          mover={mover}
          challenge={challengeByAcid.get(mover.acid)}
          maxActive={maxMoverActive}
          isOpen={openPositionAcids.has(mover.acid)}
          onToggle={() => onToggle(mover.acid)}
        />
      ))}
    </div>
  )
}

function PMReviewTab({ model }) {
  const hasReview = model.reviewPositions.length || model.reviewQuestions.length
  if (!hasReview) {
    return (
      <EmptyPanel
        title="PM Review Pending"
        copy="PM Review is generated by the live agent flow. This deterministic bundle does not include per-position review fields yet."
      />
    )
  }

  return (
    <div className="pm-review-view">
      <section className="context-block">
        <PanelHeader kicker="Review Context" title="Structured Agent Review" />
        <p>Per-position takeaways, view-change tests, and PM questions from the live agent output.</p>
      </section>

      <section className="review-card-list">
        {model.reviewPositions.map((mover, index) => (
          <article key={mover.acid} className="review-card">
            <div className="review-card-head">
              <span className="position-index">{index + 1}</span>
              <div>
                <h2>{mover.acid}</h2>
                <div className="tag-row">
                  <Tag tone={exposureTone(mover.active_rolled_exposure)} label={exposureLabel(mover.active_rolled_exposure)} />
                  <Tag tone={rankTone(mover.vir_rank_change_by_stf)} label={`Rank ${formatRank(mover.vir_rank_change_by_stf)}`} />
                </div>
              </div>
            </div>

            <MetricRibbon
              items={[
                ['Target', formatWeight(mover.target_rolled_exposure)],
                ['Bench', formatWeight(mover.benchmark_rolled_exposure)],
                ['VIR', formatMaybe(mover.vir_stf)],
                ['VIR Delta', formatSignedMaybe(mover.vir_delta_stf)],
              ]}
            />

            {hasContent(mover.pm_takeaway) ? (
              <ReviewSection label="PM Takeaway" tone="positive" body={mover.pm_takeaway} />
            ) : null}
            {hasContent(mover.what_would_change_view) ? (
              <ReviewSection label="What Would Change the View" tone="info" body={mover.what_would_change_view} />
            ) : null}
          </article>
        ))}
      </section>

      {model.reviewQuestions.length ? (
        <section className="question-block">
          <PanelHeader kicker="Questions for PM Review" title={`${model.reviewQuestions.length} Questions`} />
          <ol>
            {model.reviewQuestions.map((question, index) => (
              <li key={`${question}-${index}`}>
                <span>{index + 1}</span>
                <p>{question}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </div>
  )
}

function SignalsTab({ model }) {
  const perspectiveEntries = Object.entries(model.sizing.perspective_summary ?? {})
  return (
    <div className="signals-view">
      {perspectiveEntries.length ? (
        <section className="perspective-strip">
          {perspectiveEntries.map(([key, value]) => (
            <div key={key} className="perspective-chip">
              <strong>{humanizeKey(key)}</strong>
              <span>{value}</span>
            </div>
          ))}
        </section>
      ) : null}

      <section className="signal-columns">
        <SignalColumn title="Signal Agreement" items={model.uniqueAgreements} tone="positive" />
        <SignalColumn title="Signal Disagreement" items={model.uniqueDisagreements} tone="alert" />
      </section>

      {model.momChanges.length ? (
        <section className="section-panel">
          <PanelHeader kicker="Largest Algo MoM Changes" title="Momentum Table" meta={`${model.momChanges.length} rows`} />
          <div className="mom-table" role="table" aria-label="Largest algorithm month over month changes">
            <div className="mom-row is-head" role="row">
              <span>Position</span>
              <span>Perspective</span>
              <span>MoM Change</span>
              <span>Narrative</span>
            </div>
            {model.momChanges.map((item, index) => (
              <div key={`${item.acid}-${item.perspective}-${index}`} className="mom-row" role="row">
                <strong>{item.acid}</strong>
                <span>{item.perspective || '-'}</span>
                <code className={toneForNumber(item.value)}>{formatSignedMaybe(item.value)}</code>
                <p>{item.narrative}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}

function ChallengesTab({ model }) {
  if (!model.challenges.length) {
    return (
      <EmptyPanel
        title="No Active Challenges"
        copy="No active challenges - all positions are within current model parameters."
      />
    )
  }

  return (
    <div className="challenges-view">
      {model.challenges.map((challenge) => {
        const mover = model.moverByAcid.get(challenge.acid)
        return <ChallengeCard key={challenge.trigger_candidate_id || challenge.acid} challenge={challenge} mover={mover} />
      })}
    </div>
  )
}

function STFVIRTab({ model, selectedExposure, onSelectExposure, selectedCategory }) {
  if (!model.signalRows.length) {
    return (
      <EmptyPanel
        title="No STF / VIR Rows"
        copy="This fund does not have enough VIR or algo-linked rows to build the STF and positioning analysis view."
      />
    )
  }

  const focusRows = model.signalRows.slice(0, 12)
  const largestGap = focusRows[0] ?? null
  const signalHighlights = buildSignalHighlights(model.categoryTrendRows)
  const focusedRow =
    model.signalRows.find((row) => row.acid === selectedExposure?.acid) ??
    model.tensionRows[0] ??
    model.signalRows[0] ??
    null

  return (
    <div className="stf-vir-view">
      <section className="stf-summary-grid">
        <KpiTile label="Signal Rows" value={String(model.signalRows.length)} subLabel="rows with VIR or algo" tone="info" />
        <KpiTile label="Opposed" value={String(model.opposedCount)} subLabel="active vs VIR direction" tone={model.opposedCount ? 'alert' : 'quiet'} />
        <KpiTile label="Largest Gap" value={largestGap ? formatWeight(largestGap.signalGap) : '-'} subLabel={largestGap ? largestGap.acid : 'no gap rows'} tone="warning" />
        <KpiTile label="Fastest Algo Move" value={model.fastestAlgoMove ? formatSignedMaybe(model.fastestAlgoMove.algo_active_weight_mom) : '-'} subLabel={model.fastestAlgoMove ? model.fastestAlgoMove.acid : 'no move rows'} tone="positive" />
      </section>

      <section className="trend-charts-grid">
        <section className="section-panel">
          <PanelHeader kicker="Signal Trend" title="VIR Then vs Now" meta={selectedCategory === 'All' ? 'Previous snapshot vs current' : selectedCategory} />
          <SignalTrendChart rows={model.categoryTrendRows} previousKey="virPrevious" currentKey="virCurrent" />
        </section>

        <section className="section-panel">
          <PanelHeader kicker="Signal Trend" title="Algo Then vs Now" meta={selectedCategory === 'All' ? 'Previous snapshot vs current' : selectedCategory} />
          <SignalTrendChart rows={model.categoryTrendRows} previousKey="algoPrevious" currentKey="algoCurrent" />
        </section>
      </section>

      <section className="section-panel">
        <PanelHeader
          kicker="What Moved Most"
          title="Signal Readout"
          meta={selectedCategory === 'All' ? 'Irrespective of positioning' : selectedCategory}
        />
        <div className="highlight-strip">
          {signalHighlights.map((item) => (
            <article key={item.title} className="highlight-card">
              <span>{item.title}</span>
              <strong>{item.headline}</strong>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-panel">
        <PanelHeader
          kicker="Positioning Context"
          title="How The Fund Is Positioned Against Those Signals"
          meta={selectedCategory === 'All' ? 'Current fund' : selectedCategory}
        />
        <div className="category-story-grid">
          {model.categoryTrendRows.map((row) => (
            <article key={row.category} className="category-story-card">
              <div className="category-story-head">
                <strong>{row.category}</strong>
                <Tag label={row.relationshipLabel} tone={row.relationshipTone} />
              </div>
              <div className="category-story-metrics">
                <MetricMini label="Portfolio" value={formatWeight(row.positionNet)} />
                <MetricMini label="VIR Now" value={formatMaybe(row.virCurrent)} />
                <MetricMini label="Algo Now" value={formatMaybe(row.algoCurrent)} />
              </div>
              <div className="category-story-shifts">
                <div className="story-shift">
                  <span>VIR</span>
                  <strong>{formatMaybe(row.virPrevious)} to {formatMaybe(row.virCurrent)}</strong>
                </div>
                <div className="story-shift">
                  <span>Algo</span>
                  <strong>{formatMaybe(row.algoPrevious)} to {formatMaybe(row.algoCurrent)}</strong>
                </div>
              </div>
              <p className="panel-insight">{row.positionRead}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="stf-context-grid">
        <div className="section-panel motion-panel">
          <PanelHeader kicker="Line Explorer" title={focusedRow?.acid ?? 'Signal Detail'} meta={focusedRow ? classifyExposure(focusedRow) : ''} />
          {focusedRow ? (
            <div className="selected-signal-card">
              <div className="motion-metrics">
                <MetricMini label="Active" value={formatWeight(focusedRow.active_rolled_exposure)} />
                <MetricMini label="VIR Now" value={formatMaybe(focusedRow.vir_stf)} />
                <MetricMini label="VIR Then" value={formatMaybe(previousValue(focusedRow.vir_stf, focusedRow.vir_delta_stf))} />
                <MetricMini label="Algo Now" value={formatMaybe(focusedRow.algo_active_weight)} />
                <MetricMini label="Algo Then" value={formatMaybe(previousValue(focusedRow.algo_active_weight, focusedRow.algo_active_weight_mom))} />
                <MetricMini label="Signal Gap" value={formatWeight((numberOrNull(focusedRow.active_rolled_exposure) ?? 0) - (numberOrNull(focusedRow.algo_active_weight) ?? 0))} />
              </div>
              <p className="panel-insight">{describeSignalRow(focusedRow)}</p>
            </div>
          ) : null}
          <PanelHeader kicker="Inside This Fund" title="Most Meaningful Lines" meta={`${focusRows.length} rows`} />
          <div className="motion-list">
            {model.tensionRows.slice(0, 8).map((row) => (
              <button
                key={row.acid}
                type="button"
                className={`motion-row ${focusedRow?.acid === row.acid ? 'is-selected' : ''}`}
                onClick={() => onSelectExposure(row.acid)}
              >
                <div className="motion-title">
                  <strong>{row.acid}</strong>
                  <span>{classifyExposure(row)}</span>
                </div>
                <div className="motion-metrics">
                  <MetricMini label="Active" value={formatWeight(row.active_rolled_exposure)} />
                  <MetricMini label="Algo" value={formatMaybe(row.algo_active_weight)} />
                  <MetricMini label="MoM" value={formatSignedMaybe(row.algo_active_weight_mom)} />
                  <MetricMini label="VIR" value={formatMaybe(row.vir_stf)} />
                </div>
                <SignalGapBar value={row.signalGap} maxValue={model.maxSignalGap} />
              </button>
            ))}
          </div>
        </div>

        <div className="section-panel chart-panel">
          <PanelHeader kicker="Supporting View" title="Portfolio vs VIR Map" meta="click a point to inspect" />
          <QuadrantChart rows={model.signalRows} selectedAcid={focusedRow?.acid} onSelectExposure={onSelectExposure} />
          <p className="panel-insight">
            Bigger circles mean the algo moved more this month. Red points are still positioned against the current VIR direction.
          </p>
        </div>
      </section>

      <section className="signal-columns">
        <section className="section-panel">
          <PanelHeader kicker="Portfolio Tension" title="Biggest Position vs Signal Gaps" />
          <div className="micro-bars">
            {model.signalGapLeaders.slice(0, 8).map((row) => (
              <MicroBar
                key={`${row.acid}-gap`}
                label={row.acid}
                value={row.signalGap}
                maxValue={model.maxSignalGap || 1}
                detail={`Algo ${formatMaybe(row.algo_active_weight)} vs active ${formatWeight(row.active_rolled_exposure)}`}
              />
            ))}
          </div>
        </section>

        <section className="section-panel">
          <PanelHeader kicker="Outside The Fund" title="Where These Same Lines Moved Most Elsewhere" />
          <div className="micro-bars">
            {model.externalRelevantShifts.length ? (
              model.externalRelevantShifts.slice(0, 8).map((row) => (
                <MicroBar
                  key={`${row.fund}-${row.acid}`}
                  label={`${row.acid} - ${row.fund}`}
                  value={row.relevanceScore}
                  maxValue={model.maxExternalShift || 1}
                  detail={`VIR ${formatSignedMaybe(row.vir_delta_stf)} / Algo ${formatSignedMaybe(row.algo_active_weight_mom)} / Active ${formatWeight(row.active_rolled_exposure)}`}
                />
              ))
            ) : (
              <p className="empty-copy">No relevant external shifts were found for the currently filtered lines.</p>
            )}
          </div>
        </section>
      </section>
    </div>
  )
}

function QuadrantChart({ rows, selectedAcid, onSelectExposure }) {
  const chartRows = rows.filter((row) => row.vir_stf != null && row.active_rolled_exposure != null)
  if (!chartRows.length) {
    return <p className="empty-copy">Not enough VIR rows to draw the quadrant chart.</p>
  }

  const width = 420
  const height = 240
  const pad = 34
  const xDomain = Math.max(...chartRows.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 1)
  const yDomain = Math.max(...chartRows.map((row) => Math.abs(numberOrNull(row.vir_stf) ?? 0)), 0.05)
  const sizeDomain = Math.max(...chartRows.map((row) => Math.abs(numberOrNull(row.algo_active_weight_mom) ?? 0)), 0.01)
  const scaleX = (value) => pad + ((value + xDomain) / (xDomain * 2)) * (width - pad * 2)
  const scaleY = (value) => height - pad - ((value + yDomain) / (yDomain * 2)) * (height - pad * 2)

  return (
    <div className="quadrant-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Quadrant chart of active exposure against VIR STF">
        <rect x="0" y="0" width={width} height={height} rx="8" fill="#f8faf9" />
        <rect x={pad} y={pad} width={(width - pad * 2) / 2} height={(height - pad * 2) / 2} fill="#eef8f1" />
        <rect x={width / 2} y={pad} width={(width - pad * 2) / 2} height={(height - pad * 2) / 2} fill="#f3fbf8" />
        <rect x={pad} y={height / 2} width={(width - pad * 2) / 2} height={(height - pad * 2) / 2} fill="#fff4f1" />
        <rect x={width / 2} y={height / 2} width={(width - pad * 2) / 2} height={(height - pad * 2) / 2} fill="#fff8f3" />
        <line x1={width / 2} y1={pad} x2={width / 2} y2={height - pad} stroke="#aebbb7" strokeWidth="1" />
        <line x1={pad} y1={height / 2} x2={width - pad} y2={height / 2} stroke="#aebbb7" strokeWidth="1" />
        {chartRows.map((row) => {
          const x = scaleX(numberOrNull(row.active_rolled_exposure) ?? 0)
          const y = scaleY(numberOrNull(row.vir_stf) ?? 0)
          const radius = 5 + ((Math.abs(numberOrNull(row.algo_active_weight_mom) ?? 0) / sizeDomain) * 9)
          const selected = row.acid === selectedAcid
          return (
            <g key={row.acid}>
              <circle
                cx={x}
                cy={y}
                r={radius}
                fill={row.signalOpposed ? '#9a3f35' : '#276b4f'}
                stroke={selected ? '#16211f' : '#ffffff'}
                strokeWidth={selected ? 3 : 1.5}
                opacity="0.86"
                onClick={() => onSelectExposure(row.acid)}
              />
              {selected ? (
                <text x={x + 10} y={y - 10} fontSize="11" fill="#16211f">
                  {row.acid}
                </text>
              ) : null}
            </g>
          )
        })}
        <text x={pad} y={18} fontSize="11" fill="#63706d">Positive STF</text>
        <text x={width - pad - 74} y={height - 10} fontSize="11" fill="#63706d">Overweight</text>
        <text x={pad} y={height - 10} fontSize="11" fill="#63706d">Underweight</text>
        <text x={width / 2 - 60} y={height - 4} fontSize="11" fill="#44514e">Portfolio active exposure (%)</text>
        <text transform={`translate(12 ${height / 2 + 30}) rotate(-90)`} fontSize="11" fill="#44514e">VIR STF</text>
      </svg>
    </div>
  )
}

function SignalTrendChart({ rows, previousKey, currentKey }) {
  const chartRows = rows.filter((row) => row[previousKey] != null || row[currentKey] != null)
  if (!chartRows.length) {
    return <p className="empty-copy">No trend rows are available for this view.</p>
  }

  const width = 520
  const rowHeight = 48
  const padLeft = 126
  const padRight = 28
  const height = chartRows.length * rowHeight + 26
  const domain = Math.max(
    ...chartRows.flatMap((row) => [Math.abs(numberOrNull(row[previousKey]) ?? 0), Math.abs(numberOrNull(row[currentKey]) ?? 0)]),
    0.05,
  )
  const scaleX = (value) => padLeft + ((value + domain) / (domain * 2)) * (width - padLeft - padRight)

  return (
    <div className="trend-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Previous versus current trend chart">
        <line x1={scaleX(0)} y1="10" x2={scaleX(0)} y2={height - 10} stroke="#aebbb7" strokeWidth="1" />
        {chartRows.map((row, index) => {
          const y = 24 + index * rowHeight
          const previous = numberOrNull(row[previousKey])
          const current = numberOrNull(row[currentKey])
          return (
            <g key={`${row.category}-${previousKey}`}>
              <text x="0" y={y + 4} fontSize="12" fill="#16211f">{row.category}</text>
              {previous != null && current != null ? (
                <>
                  <line x1={scaleX(previous)} y1={y} x2={scaleX(current)} y2={y} stroke="#94a7a2" strokeWidth="3" />
                  <circle cx={scaleX(previous)} cy={y} r="5" fill="#385d95" />
                  <circle cx={scaleX(current)} cy={y} r="6" fill="#2f6f73" />
                  <text x={width - 78} y={y + 4} fontSize="11" fill="#63706d">
                    {formatMaybe(previous)} to {formatMaybe(current)}
                  </text>
                </>
              ) : current != null ? (
                <>
                  <circle cx={scaleX(current)} cy={y} r="6" fill="#2f6f73" />
                  <text x={width - 52} y={y + 4} fontSize="11" fill="#63706d">{formatMaybe(current)}</text>
                </>
              ) : null}
            </g>
          )
        })}
      </svg>
      <div className="trend-legend">
        <span><i className="legend-dot is-previous" /> Previous</span>
        <span><i className="legend-dot is-current" /> Current</span>
      </div>
    </div>
  )
}

function buildSignalHighlights(rows) {
  const largestVirMove = [...rows]
    .filter((row) => row.virMove != null)
    .sort((a, b) => Math.abs(b.virMove) - Math.abs(a.virMove))[0]
  const largestAlgoMove = [...rows]
    .filter((row) => row.algoMove != null)
    .sort((a, b) => Math.abs(b.algoMove) - Math.abs(a.algoMove))[0]
  const largestMismatch = [...rows]
    .filter((row) => row.signalNet != null)
    .sort((a, b) => Math.abs(b.positionVsSignalGap) - Math.abs(a.positionVsSignalGap))[0]

  return [
    largestVirMove
      ? {
          title: 'Biggest VIR shift',
          headline: largestVirMove.category,
          detail: `${formatSignedMaybe(largestVirMove.virMove)} to ${formatMaybe(largestVirMove.virCurrent)}`,
        }
      : null,
    largestAlgoMove
      ? {
          title: 'Biggest algo shift',
          headline: largestAlgoMove.category,
          detail: `${formatSignedMaybe(largestAlgoMove.algoMove)} to ${formatMaybe(largestAlgoMove.algoCurrent)}`,
        }
      : null,
    largestMismatch
      ? {
          title: 'Largest portfolio mismatch',
          headline: largestMismatch.category,
          detail: `Portfolio ${formatWeight(largestMismatch.positionNet)} while composite signals sit at ${formatMaybe(largestMismatch.signalNet)}`,
        }
      : null,
  ].filter(Boolean)
}

function ExposureSplit({ exposures }) {
  const overweight = exposures.filter((row) => numberOrNull(row.active_rolled_exposure) > 0)
  const underweight = exposures.filter((row) => numberOrNull(row.active_rolled_exposure) < 0)
  const largestOw = maxByAbs(overweight)
  const largestUw = maxByAbs(underweight)
  const total = overweight.length + underweight.length
  const slice = total ? `${(overweight.length / total) * 100}%` : '0%'

  return (
    <section className="section-panel side-panel">
      <PanelHeader kicker="Exposure Split" title="OW vs UW" />
      <div className="split-layout">
        <div className="donut" style={{ '--ow-slice': slice }}>
          <span>{total}</span>
        </div>
        <div className="split-stats">
          <MetricPair label="Overweight" value={String(overweight.length)} />
          <MetricPair label="Underweight" value={String(underweight.length)} />
          <MetricPair label="Largest OW" value={largestOw ? `${largestOw.acid} ${formatWeight(largestOw.active_rolled_exposure)}` : '-'} />
          <MetricPair label="Largest UW" value={largestUw ? `${largestUw.acid} ${formatWeight(largestUw.active_rolled_exposure)}` : '-'} />
        </div>
      </div>
    </section>
  )
}

function VirDirection({ rows }) {
  const improving = rows.filter((row) => numberOrNull(row.vir_delta_stf) > 0).length
  const declining = rows.filter((row) => numberOrNull(row.vir_delta_stf) < 0).length
  const total = improving + declining
  const improvingUw = rows.filter(
    (row) => numberOrNull(row.vir_delta_stf) > 0 && numberOrNull(row.active_rolled_exposure) < 0,
  ).length
  const ratio = total ? (improving / total) * 100 : 0

  return (
    <section className="section-panel side-panel">
      <PanelHeader kicker="VIR Direction" title="Signal Drift" />
      <div className="vir-progress">
        <div className="progress-labels">
          <span>{improving} improving</span>
          <span>{declining} declining</span>
        </div>
        <div className="progress-track">
          <span style={{ width: `${ratio}%` }} />
        </div>
      </div>
      <p className="panel-insight">
        {improvingUw
          ? `${improvingUw} improving VIR rows are still held as underweights.`
          : `${improving} improving and ${declining} declining VIR rows in the fund.`}
      </p>
    </section>
  )
}

function MemoryState({ memorySummary, triggerSummary }) {
  const rows = [
    ['Theses', memorySummary.thesis_ledger_count],
    ['Exceptions', memorySummary.exceptions_count],
    ['Watch items', memorySummary.watch_items_count],
    ['Approved', memorySummary.approved_count],
    ['Proposed', memorySummary.proposed_count],
    ['Borderline', triggerSummary.borderline_count],
  ]

  return (
    <section className="section-panel side-panel">
      <PanelHeader kicker="Memory State" title="Ledger Snapshot" />
      <div className="memory-grid">
        {rows.map(([label, value]) => (
          <div key={label} className={numberOrNull(value) ? 'is-emphasized' : ''}>
            <span>{label}</span>
            <strong>{value ?? 0}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

function ChallengeCallout({ challenges, moverByAcid }) {
  return (
    <section className="challenge-callout">
      <PanelHeader kicker="Active Challenges" title={`${challenges.length} Review Items`} />
      <div className="callout-list">
        {challenges.map((item) => {
          const mover = moverByAcid.get(item.acid)
          const active = item.position_summary?.active_rolled_exposure ?? mover?.active_rolled_exposure
          return (
            <article key={item.trigger_candidate_id || item.acid} className="callout-row">
              <strong>{item.acid}</strong>
              <p>{item.challenge || item.disagreement_statement}</p>
              <span>{formatWeight(active)}</span>
            </article>
          )
        })}
      </div>
    </section>
  )
}

function PositionCard({ mover, challenge, maxActive, isOpen, onToggle }) {
  const active = numberOrNull(mover.active_rolled_exposure)
  const barWidth = getRelativeWidth(active, maxActive, 100)

  return (
    <article className={`position-card ${isOpen ? 'is-open' : ''}`}>
      <button type="button" className="position-main" onClick={onToggle} aria-expanded={isOpen}>
        <div className="position-title-row">
          <div>
            <h2>{mover.acid}</h2>
            <div className="tag-row">
              <Tag label={acidTypeLabels[mover.acid_type] ?? humanizeKey(mover.acid_type)} tone={mover.acid_type === 'acid_bond' ? 'info' : 'neutral'} />
              <Tag label={exposureLabel(active)} tone={exposureTone(active)} />
              {challenge ? <Tag label="Challenge" tone="alert" /> : null}
            </div>
          </div>
          <strong className={`active-value ${toneForNumber(active)}`}>{formatWeight(active)}</strong>
        </div>

        <p>{mover.narrative || 'No narrative is available for this position.'}</p>

        <div className="position-weight-row">
          <div className="position-track">
            <span className={active >= 0 ? 'is-positive' : 'is-negative'} style={{ width: `${barWidth}%` }} />
          </div>
          <div className="position-metrics">
            <span>Target {formatWeight(mover.target_rolled_exposure)}</span>
            <span>Bench {formatWeight(mover.benchmark_rolled_exposure)}</span>
            {mover.vir_stf != null ? <span>VIR {formatMaybe(mover.vir_stf)}</span> : null}
            {mover.vir_delta_stf != null ? <span>Delta {formatSignedMaybe(mover.vir_delta_stf)}</span> : null}
            {mover.vir_rank_change_by_stf != null ? <span>Rank {formatRank(mover.vir_rank_change_by_stf)}</span> : null}
          </div>
        </div>
      </button>

      {isOpen ? (
        <div className="position-expanded">
          <MetricGrid
            items={[
              ['Active', formatDecimal(mover.active_rolled_exposure, 4)],
              ['Target', formatDecimal(mover.target_rolled_exposure, 4)],
              ['Benchmark', formatDecimal(mover.benchmark_rolled_exposure, 4)],
              ['VIR', formatDecimal(mover.vir_stf, 4)],
              ['VIR Delta', formatDecimal(mover.vir_delta_stf, 4)],
              ['Rank Change', formatDecimal(mover.vir_rank_change_by_stf, 4)],
            ]}
          />
          {challenge ? (
            <div className="inline-challenge">
              <strong>{challenge.challenge}</strong>
              <p>{challenge.disagreement_statement}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

function SignalColumn({ title, items, tone }) {
  return (
    <section className={`section-panel signal-panel tone-${tone}`}>
      <PanelHeader kicker={title} title={`${items.length} Positions`} />
      {items.length ? (
        <div className="signal-list">
          {items.map((item) => (
            <article key={`${item.acid}-${item.perspective}`} className="signal-row">
              <div>
                <strong>{item.acid}</strong>
                <span>{item.perspective || 'all perspectives'}</span>
              </div>
              <p>{item.narrative}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty-copy">No signal rows are available.</p>
      )}
    </section>
  )
}

function ChallengeCard({ challenge, mover }) {
  const active = challenge.position_summary?.active_rolled_exposure ?? mover?.active_rolled_exposure
  const target = challenge.position_summary?.target_rolled_exposure ?? mover?.target_rolled_exposure
  const benchmark = challenge.position_summary?.benchmark_rolled_exposure ?? mover?.benchmark_rolled_exposure

  return (
    <article className="challenge-card">
      <div className="challenge-head">
        <div>
          <h2>{challenge.acid}</h2>
          <div className="tag-row">
            <Tag label={challenge.trigger_type || 'trigger'} tone="alert" />
            <Tag label={exposureLabel(active)} tone={exposureTone(active)} />
            {mover?.vir_delta_stf != null ? <Tag label={`VIR Delta ${formatSignedMaybe(mover.vir_delta_stf)}`} tone={rankTone(mover.vir_delta_stf)} /> : null}
            {mover?.vir_rank_change_by_stf != null ? <Tag label={`Rank ${formatRank(mover.vir_rank_change_by_stf)}`} tone={rankTone(mover.vir_rank_change_by_stf)} /> : null}
          </div>
        </div>
      </div>

      <p className="disagreement-statement">{challenge.disagreement_statement || 'No disagreement statement is available.'}</p>
      <p className="challenge-body">{challenge.challenge || 'No challenge text is available.'}</p>

      <MetricGrid
        columns={3}
        items={[
          ['Active', formatWeight(active)],
          ['Target', formatWeight(target)],
          ['Benchmark', formatWeight(benchmark)],
          ['VIR', formatMaybe(mover?.vir_stf)],
          ['VIR Delta', formatSignedMaybe(mover?.vir_delta_stf)],
          ['Rank Change', formatRank(mover?.vir_rank_change_by_stf)],
        ]}
      />

      <div className="pm-question">
        <span>Question for PM</span>
        <p>{challenge.review_question || buildChallengeQuestion(challenge, mover)}</p>
      </div>
    </article>
  )
}

function PanelHeader({ kicker, title, meta }) {
  return (
    <div className="panel-header">
      <div>
        <span className="section-kicker">{kicker}</span>
        <h2>{title}</h2>
      </div>
      {meta ? <span className="panel-meta">{meta}</span> : null}
    </div>
  )
}

function KpiTile({ label, value, subLabel, tone }) {
  return (
    <article className={`kpi-tile tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{subLabel}</small>
    </article>
  )
}

function MetaChip({ label, value }) {
  return (
    <span className="meta-chip">
      <span>{label}</span>
      <strong title={value}>{value}</strong>
    </span>
  )
}

function StatusChip({ firedCount, challengeCount }) {
  const needsReview = firedCount > 0 || challengeCount > 0
  return (
    <span className={`status-chip ${needsReview ? 'needs-review' : 'is-clean'}`}>
      <span />
      {needsReview ? 'Review' : 'Clean'}
    </span>
  )
}

function MetricPair({ label, value }) {
  return (
    <div className="metric-pair">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function MetricMini({ label, value }) {
  return (
    <div className="metric-mini">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Tag({ label, tone = 'neutral' }) {
  return <span className={`tag tone-${tone}`}>{label}</span>
}

function MetricRibbon({ items }) {
  return (
    <div className="metric-ribbon">
      {items.map(([label, value]) => (
        <MetricPair key={label} label={label} value={value} />
      ))}
    </div>
  )
}

function MetricGrid({ items, columns = 2 }) {
  return (
    <div className="metric-grid" style={{ '--metric-columns': columns }}>
      {items.map(([label, value]) => (
        <MetricPair key={label} label={label} value={value} />
      ))}
    </div>
  )
}

function ReviewSection({ label, body, tone }) {
  return (
    <section className={`review-section tone-${tone}`}>
      <span>{label}</span>
      <p>{body}</p>
    </section>
  )
}

function MicroBar({ label, value, maxValue, detail, compact = false }) {
  const width = getRelativeWidth(value, Math.abs(maxValue) || 1, 100)
  return (
    <div className={`micro-bar ${compact ? 'is-compact' : ''}`}>
      <div className="micro-bar-copy">
        <strong>{label}</strong>
        <span>{detail}</span>
      </div>
      <div className="micro-bar-track">
        <span className={numberOrNull(value) >= 0 ? 'is-positive' : 'is-negative'} style={{ width: `${width}%` }} />
      </div>
      <b className={toneForNumber(value)}>{formatWeight(value)}</b>
    </div>
  )
}

function SignalGapBar({ value, maxValue }) {
  const width = getRelativeWidth(value, maxValue || 1, 100)
  return (
    <div className="signal-gap-bar">
      <div className="signal-gap-track">
        <span className={numberOrNull(value) >= 0 ? 'is-positive' : 'is-negative'} style={{ width: `${width}%` }} />
      </div>
      <b className={toneForNumber(value)}>{formatWeight(value)}</b>
    </div>
  )
}

function EmptyPanel({ title, copy }) {
  return (
    <section className="empty-panel">
      <h2>{title}</h2>
      <p>{copy}</p>
    </section>
  )
}

function EmptyMiniPanel({ title, copy }) {
  return (
    <section className="section-panel side-panel">
      <PanelHeader kicker={title} title="Waiting for selection" />
      <p className="empty-copy">{copy}</p>
    </section>
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
  const sizing = payload.sizing_considerations ?? {}
  const challengeBrief = payload.challenge_brief ?? {}
  const fundName = fund?.fund ?? ''

  const exposures = buildExposureRows(fundName)
  const exposureGroups = groupExposures(exposures)
  const exposureByAcid = new Map(exposures.map((row) => [row.acid, row]))
  const challenges = challengeBrief.items ?? []
  const challengeByAcid = new Map(challenges.map((item) => [item.acid, item]))
  const movers = sortMaterialMovers(changeBrief.material_movers ?? [])
  const moverByAcid = new Map(movers.map((row) => [row.acid, row]))
  const virRows = exposures.filter((row) => row.vir_delta_stf != null && row.vir_stf != null)
  const uniqueAgreements = dedupeSignalRows(sizing.algo_vs_positioning_agreement ?? [])
  const uniqueDisagreements = dedupeSignalRows(sizing.algo_vs_positioning_disagreement ?? [])
  const reviewPositions = movers.filter(hasReviewOutput)
  const signalRows = exposures
    .filter((row) => row.vir_stf != null || row.algo_active_weight != null || row.algo_active_weight_mom != null)
    .map((row) => {
      const active = numberOrNull(row.active_rolled_exposure) ?? 0
      const algo = numberOrNull(row.algo_active_weight) ?? 0
      const vir = numberOrNull(row.vir_stf)
      const signalOpposed = vir == null ? false : active * vir < 0
      const signalGap = active - algo
      return {
        ...row,
        signalOpposed,
        signalGap,
      }
    })
    .sort((a, b) => Math.abs(b.signalGap) - Math.abs(a.signalGap))
  const currentAcids = new Set(signalRows.map((row) => row.acid))
  const externalRelevantShifts = fundWeightsVirAlgo
    .filter((row) => row.fund !== fundName && currentAcids.has(row.acid))
    .map((row) => {
      const normalized = normalizeExposureRow(row)
      return {
        ...normalized,
        relevanceScore: Math.abs(numberOrNull(normalized.vir_delta_stf) ?? 0) + Math.abs(numberOrNull(normalized.algo_active_weight_mom) ?? 0),
      }
    })
    .filter((row) => row.relevanceScore > 0)
    .sort((a, b) => b.relevanceScore - a.relevanceScore)
  const categoryTrendRows = buildCategoryTrendRows(signalRows)
  const tensionRows = buildTensionRows(signalRows)

  return {
    metadata,
    coverage,
    memorySummary,
    triggerSummary,
    changeBrief,
    sizing,
    challenges,
    challengeByAcid,
    exposures,
    exposureGroups,
    exposureByAcid,
    lineages: exposureLineage[fundName] ?? {},
    lineageByAcid: exposureLineage[fundName] ?? {},
    movers,
    moverByAcid,
    virRows,
    reviewPositions,
    reviewQuestions: movers.map((mover) => mover.review_question).filter(hasContent),
    uniqueAgreements,
    uniqueDisagreements,
    momChanges: sizing.largest_algo_mom_changes ?? [],
    availableCategories: exposureGroups.map((group) => group.category),
    signalAlignment: getSignalAlignment(uniqueAgreements, uniqueDisagreements),
    maxExposureActive: Math.max(...exposures.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 0),
    maxMoverActive: Math.max(...movers.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 0),
    signalRows,
    tensionRows,
    opposedCount: signalRows.filter((row) => row.signalOpposed).length,
    fastestAlgoMove: maxByField(signalRows, 'algo_active_weight_mom'),
    signalGapLeaders: [...signalRows].sort((a, b) => Math.abs(b.signalGap) - Math.abs(a.signalGap)),
    externalRelevantShifts,
    categoryTrendRows,
    maxSignalGap: Math.max(...signalRows.map((row) => Math.abs(numberOrNull(row.signalGap) ?? 0)), 0),
    maxVirDelta: Math.max(...signalRows.map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 0),
    maxExternalShift: Math.max(...externalRelevantShifts.map((row) => Math.abs(numberOrNull(row.relevanceScore) ?? 0)), 0),
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

function groupExposures(exposures) {
  return categoryOrder
    .map((category) => ({
      category,
      items: exposures.filter((row) => row.category === category),
    }))
    .filter((group) => group.items.length)
    .map((group) => ({
      ...group,
      totalActive: group.items.reduce((sum, row) => sum + (numberOrNull(row.active_rolled_exposure) ?? 0), 0),
    }))
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

function dedupeSignalRows(rows) {
  const seen = new Set()
  const unique = []
  for (const row of rows) {
    if (!row.acid || seen.has(row.acid)) {
      continue
    }
    seen.add(row.acid)
    unique.push(row)
  }
  return unique
}

function filterModelByCategory(model, selectedCategory) {
  if (selectedCategory === 'All') {
    return model
  }

  const exposures = model.exposures.filter((row) => row.category === selectedCategory)
  const exposureByAcid = new Map(exposures.map((row) => [row.acid, row]))
  const allowAcid = (acid) => exposureByAcid.has(acid)
  const movers = model.movers.filter((row) => allowAcid(row.acid) || classifyExposure(row) === selectedCategory)
  const challenges = model.challenges.filter((row) => allowAcid(row.acid))
  const signalRows = model.signalRows.filter((row) => allowAcid(row.acid))
  const tensionRows = buildTensionRows(signalRows)
  const uniqueAgreements = model.uniqueAgreements.filter((row) => allowAcid(row.acid))
  const uniqueDisagreements = model.uniqueDisagreements.filter((row) => allowAcid(row.acid))
  const externalRelevantShifts = model.externalRelevantShifts.filter((row) => classifyExposure(row) === selectedCategory)

  return {
    ...model,
    exposures,
    exposureGroups: groupExposures(exposures),
    exposureByAcid,
    lineages: Object.fromEntries(exposures.map((row) => [row.acid, model.lineageByAcid[row.acid]])),
    lineageByAcid: Object.fromEntries(exposures.map((row) => [row.acid, model.lineageByAcid[row.acid]])),
    movers,
    moverByAcid: new Map(movers.map((row) => [row.acid, row])),
    challenges,
    challengeByAcid: new Map(challenges.map((row) => [row.acid, row])),
    virRows: model.virRows.filter((row) => allowAcid(row.acid)),
    reviewPositions: model.reviewPositions.filter((row) => allowAcid(row.acid)),
    reviewQuestions: model.reviewPositions.filter((row) => allowAcid(row.acid)).map((row) => row.review_question).filter(hasContent),
    uniqueAgreements,
    uniqueDisagreements,
    momChanges: model.momChanges.filter((row) => allowAcid(row.acid)),
    signalAlignment: getSignalAlignment(uniqueAgreements, uniqueDisagreements),
    maxExposureActive: Math.max(...exposures.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 0),
    maxMoverActive: Math.max(...movers.map((row) => Math.abs(numberOrNull(row.active_rolled_exposure) ?? 0)), 0),
    signalRows,
    tensionRows,
    opposedCount: signalRows.filter((row) => row.signalOpposed).length,
    fastestAlgoMove: maxByField(signalRows, 'algo_active_weight_mom'),
    signalGapLeaders: [...signalRows].sort((a, b) => Math.abs(b.signalGap) - Math.abs(a.signalGap)),
    externalRelevantShifts,
    categoryTrendRows: buildCategoryTrendRows(signalRows),
    maxSignalGap: Math.max(...signalRows.map((row) => Math.abs(numberOrNull(row.signalGap) ?? 0)), 0),
    maxVirDelta: Math.max(...signalRows.map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 0),
    maxExternalShift: Math.max(...externalRelevantShifts.map((row) => Math.abs(numberOrNull(row.relevanceScore) ?? 0)), 0),
  }
}

function buildCategoryTrendRows(rows) {
  const categories = ['Country', 'Eq Sector', 'Region', 'Eq Size / Style', 'Fixed Income']
  return categories
    .map((category) => {
      const bucketRows = rows.filter((row) => row.category === category)
      if (!bucketRows.length) {
        return null
      }
      const virRows = bucketRows.filter((row) => row.vir_stf != null)
      const algoRows = bucketRows.filter((row) => row.algo_active_weight != null)
      const virCurrent = average(virRows.map((row) => row.vir_stf))
      const virPrevious = average(virRows.map((row) => (numberOrNull(row.vir_stf) ?? 0) - (numberOrNull(row.vir_delta_stf) ?? 0)))
      const algoCurrent = average(algoRows.map((row) => row.algo_active_weight))
      const algoPrevious = average(algoRows.map((row) => (numberOrNull(row.algo_active_weight) ?? 0) - (numberOrNull(row.algo_active_weight_mom) ?? 0)))
      const positionNet = bucketRows.reduce((sum, row) => sum + (numberOrNull(row.active_rolled_exposure) ?? 0), 0)
      const signalNet = average([virCurrent, algoCurrent])
      const positionVsSignalGap = positionNet - (signalNet ?? 0)
      return {
        category,
        count: bucketRows.length,
        positionNet,
        virCurrent,
        virPrevious,
        virMove: virCurrent != null && virPrevious != null ? virCurrent - virPrevious : null,
        algoCurrent,
        algoPrevious,
        algoMove: algoCurrent != null && algoPrevious != null ? algoCurrent - algoPrevious : null,
        signalNet,
        positionVsSignalGap,
        relationshipLabel: categoryRelationshipLabel(positionNet, virCurrent, algoCurrent),
        relationshipTone: categoryRelationshipTone(positionNet, virCurrent, algoCurrent),
        positionRead: describeCategoryPosition(positionNet, virCurrent, algoCurrent),
      }
    })
    .filter(Boolean)
}

function buildTensionRows(rows) {
  const maxGap = Math.max(...rows.map((row) => Math.abs(numberOrNull(row.signalGap) ?? 0)), 1)
  const maxVirMove = Math.max(...rows.map((row) => Math.abs(numberOrNull(row.vir_delta_stf) ?? 0)), 0.01)
  const maxAlgoMove = Math.max(...rows.map((row) => Math.abs(numberOrNull(row.algo_active_weight_mom) ?? 0)), 0.01)

  return [...rows]
    .map((row) => ({
      ...row,
      tensionScore:
        Math.abs(numberOrNull(row.signalGap) ?? 0) / maxGap +
        Math.abs(numberOrNull(row.vir_delta_stf) ?? 0) / maxVirMove +
        Math.abs(numberOrNull(row.algo_active_weight_mom) ?? 0) / maxAlgoMove +
        (row.signalOpposed ? 0.75 : 0),
    }))
    .sort((a, b) => b.tensionScore - a.tensionScore)
}

function getSignalAlignment(agreements, disagreements) {
  const agreeSet = new Set(agreements.map((row) => row.acid).filter(Boolean))
  const totalSet = new Set([...agreements, ...disagreements].map((row) => row.acid).filter(Boolean))
  if (!totalSet.size) {
    return null
  }
  return {
    agree: agreeSet.size,
    total: totalSet.size,
    ratio: agreeSet.size / totalSet.size,
  }
}

function sortMaterialMovers(movers) {
  return [...movers].sort(
    (a, b) => Math.abs(numberOrNull(b.active_rolled_exposure) ?? 0) - Math.abs(numberOrNull(a.active_rolled_exposure) ?? 0),
  )
}

function getTabBadge(tabId, model) {
  if (tabId === 'positions') {
    return { label: String(model.movers.length), tone: 'neutral' }
  }
  if (tabId === 'pm-review') {
    return { label: String(model.reviewPositions.length || model.reviewQuestions.length), tone: model.reviewPositions.length || model.reviewQuestions.length ? 'ready' : 'neutral' }
  }
  if (tabId === 'challenges') {
    return { label: String(model.challenges.length), tone: model.challenges.length ? 'alert' : 'neutral' }
  }
  if (tabId === 'stf-vir') {
    return { label: String(model.signalRows.length), tone: 'ready' }
  }
  return null
}

function getFundCounts(fund) {
  const payload = fund?.run_payload ?? {}
  const triggerSummary = payload.fund_snapshot_summary?.trigger_summary ?? {}
  return {
    fired: triggerSummary.fired_count ?? 0,
    borderline: triggerSummary.borderline_count ?? 0,
    challenges: payload.challenge_brief?.items?.length ?? 0,
  }
}

function renderFundPills(counts) {
  const pills = []
  if (counts.fired > 0) {
    pills.push(<span key="fired" className="fund-pill is-fired">Fired {counts.fired}</span>)
  }
  if (counts.challenges > 0) {
    pills.push(<span key="challenges" className="fund-pill is-alert">Challenge {counts.challenges}</span>)
  }
  if (counts.borderline > 0) {
    pills.push(<span key="borderline" className="fund-pill is-borderline">~ {counts.borderline}</span>)
  }
  if (!pills.length) {
    pills.push(<span key="clean" className="fund-pill is-clean">Clean</span>)
  }
  return pills
}

function fundAbbreviation(name) {
  const lowered = name.toLowerCase()
  if (lowered.includes('alternative')) {
    return 'ALT'
  }
  if (lowered.includes('bond') || lowered.includes('income') || lowered.includes('municipal')) {
    return 'FI'
  }
  if (lowered.includes('allocation') || lowered.includes('multi-asset')) {
    return 'MA'
  }
  return 'EQ'
}

function buildChallengeQuestion(challenge, mover) {
  const active = formatWeight(challenge.position_summary?.active_rolled_exposure ?? mover?.active_rolled_exposure)
  const vir = mover?.vir_stf != null ? ` with VIR at ${formatMaybe(mover.vir_stf)}` : ''
  return `For ${challenge.acid}, should the current ${active} active exposure remain in place${vir}, or should the PM adjust the position?`
}

function buildExposureSummary(exposure, lineage) {
  const signalText = exposure.algo_active_weight != null ? `algo active weight ${formatMaybe(exposure.algo_active_weight)}` : 'no algo link'
  if (lineage) {
    return `${exposure.acid} aggregates into ${lineage.securities.length} named holdings in this view, with ${signalText}.`
  }
  return `${exposure.acid} is available in the summary layer with ${signalText}.`
}

function exposureSubtitle(exposure) {
  const sectorLabel = sectorLabelFromAcid(exposure.acid)
  if (exposure.category === 'Eq Sector' && sectorLabel) {
    return sectorLabel
  }
  return `${acidTypeLabels[exposure.acid_type] ?? humanizeKey(exposure.acid_type)}`
}

function sectorLabelFromAcid(acid = '') {
  const match = acid.match(/\b([A-Z]{2}) EQ$/)
  if (!match) {
    return null
  }
  return sectorCodeLabels[match[1]] ?? null
}

function hasReviewOutput(mover) {
  return hasContent(mover.pm_takeaway) || hasContent(mover.what_would_change_view) || hasContent(mover.review_question)
}

function hasContent(value) {
  return typeof value === 'string' && value.trim().length > 0
}

function maxByAbs(items) {
  return items.reduce((best, item) => {
    if (!best) {
      return item
    }
    return Math.abs(numberOrNull(item.active_rolled_exposure) ?? 0) > Math.abs(numberOrNull(best.active_rolled_exposure) ?? 0)
      ? item
      : best
  }, null)
}

function maxByField(items, field) {
  const valid = items.filter((item) => item[field] != null)
  if (!valid.length) {
    return null
  }
  return [...valid].sort((a, b) => Math.abs(numberOrNull(b[field]) ?? 0) - Math.abs(numberOrNull(a[field]) ?? 0))[0]
}

function average(values) {
  const valid = values.map(numberOrNull).filter((value) => value != null)
  if (!valid.length) {
    return null
  }
  return valid.reduce((sum, value) => sum + value, 0) / valid.length
}

function previousValue(currentValue, deltaValue) {
  const current = numberOrNull(currentValue)
  if (current == null) {
    return null
  }
  return current - (numberOrNull(deltaValue) ?? 0)
}

function getRelativeWidth(value, maxValue, maxWidth) {
  const numeric = Math.abs(numberOrNull(value) ?? 0)
  if (!maxValue || !numeric) {
    return 0
  }
  return Math.max(6, Math.min(maxWidth, (numeric / maxValue) * maxWidth))
}

function describeCategoryPosition(positionNet, virCurrent, algoCurrent) {
  const position = numberOrNull(positionNet) ?? 0
  const vir = numberOrNull(virCurrent) ?? 0
  const algo = numberOrNull(algoCurrent) ?? 0
  if (position === 0) {
    return 'Positioning is roughly neutral here.'
  }
  if (position > 0 && vir < 0) {
    return 'The fund is overweight while VIR leans negative.'
  }
  if (position < 0 && vir > 0) {
    return 'The fund is underweight while VIR leans positive.'
  }
  if (position > 0 && algo < 0) {
    return 'The overweight is still leaning against the algo.'
  }
  if (position < 0 && algo > 0) {
    return 'The underweight is still leaning against the algo.'
  }
  return 'Signals and positioning are broadly pointing the same way.'
}

function categoryRelationshipLabel(positionNet, virCurrent, algoCurrent) {
  const position = numberOrNull(positionNet) ?? 0
  const vir = numberOrNull(virCurrent)
  const algo = numberOrNull(algoCurrent)
  if (position === 0) {
    return 'Neutral position'
  }
  const reads = [vir, algo]
    .filter((value) => value != null && value !== 0)
    .map((value) => position * value > 0)
  if (!reads.length) {
    return 'Signal is neutral'
  }
  if (reads.some(Boolean) && reads.some((aligned) => !aligned)) {
    return 'Mixed read'
  }
  return reads.every(Boolean) ? 'With signal' : 'Against signal'
}

function categoryRelationshipTone(positionNet, virCurrent, algoCurrent) {
  const position = numberOrNull(positionNet) ?? 0
  const vir = numberOrNull(virCurrent)
  const algo = numberOrNull(algoCurrent)
  const reads = [vir, algo]
    .filter((value) => value != null && value !== 0)
    .map((value) => position * value > 0)
  if (position === 0 || !reads.length) {
    return 'neutral'
  }
  if (reads.some(Boolean) && reads.some((aligned) => !aligned)) {
    return 'warning'
  }
  return reads.every(Boolean) ? 'positive' : 'alert'
}

function describeSignalRow(row) {
  const active = numberOrNull(row.active_rolled_exposure) ?? 0
  const vir = numberOrNull(row.vir_stf)
  const algo = numberOrNull(row.algo_active_weight)
  const virDelta = numberOrNull(row.vir_delta_stf)
  const algoMom = numberOrNull(row.algo_active_weight_mom)
  const parts = []
  if (active > 0) {
    parts.push('The fund is overweight this line.')
  } else if (active < 0) {
    parts.push('The fund is underweight this line.')
  }
  if (vir != null) {
    parts.push(`VIR now sits at ${formatMaybe(vir)}${virDelta != null ? ` after a ${formatSignedMaybe(virDelta)} move` : ''}.`)
  }
  if (algo != null) {
    parts.push(`Algo active weight is ${formatMaybe(algo)}${algoMom != null ? ` with ${formatSignedMaybe(algoMom)} month over month` : ''}.`)
  }
  if (vir != null && active * vir < 0) {
    parts.push('Position and VIR are still pointing in opposite directions.')
  }
  return parts.join(' ')
}

function exposureLabel(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'Neutral'
  }
  return numeric > 0 ? 'OW' : 'UW'
}

function exposureTone(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'neutral'
  }
  return numeric > 0 ? 'positive' : 'warning'
}

function rankTone(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'neutral'
  }
  return numeric > 0 ? 'positive' : 'warning'
}

function toneForNumber(value) {
  const numeric = numberOrNull(value)
  if (numeric == null || numeric === 0) {
    return 'is-neutral'
  }
  return numeric > 0 ? 'is-positive' : 'is-negative'
}

function numberOrNull(value) {
  if (value == null || value === '') {
    return null
  }
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function formatDecimal(value, digits = 2) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return numeric.toFixed(digits)
}

function formatMaybe(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return numeric.toFixed(2)
}

function formatWeight(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)}%`
}

function formatSignedMaybe(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(2)}`
}

function formatRank(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(0)}`
}

function formatPercent(value) {
  const numeric = numberOrNull(value)
  if (numeric == null) {
    return '-'
  }
  return `${(numeric * 100).toFixed(1)}%`
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

function humanizeKey(value = '') {
  return String(value)
    .replace(/^acid_/, '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}
