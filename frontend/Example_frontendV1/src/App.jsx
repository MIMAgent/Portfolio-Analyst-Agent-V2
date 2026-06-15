import { useMemo, useState } from 'react'
import review from './data/agent2/mstar-us-equity-review.json'
import evidence from './data/agent2/mstar-us-equity-evidence.json'
import manifest from './data/agent2/mstar-us-equity-manifest.json'
import packet from './data/agent2/mstar-us-equity-packet.json'

const tabs = [
  { id: 'overview', label: 'Overview', count: 0 },
  { id: 'challenge', label: 'Challenge Cards', count: (evidence.top_challenges || []).length },
  { id: 'memo', label: 'Deep Memo', count: (review.challenge_brief || []).length },
  { id: 'risk', label: 'Risk', count: (evidence.risk_and_attribution?.likely_holdings_contributors || []).length },
  { id: 'holdings', label: 'Holdings', count: (packet.material_positions || []).length },
  { id: 'research', label: 'Research', count: (evidence.sharepoint_research_focus || []).length },
  { id: 'run', label: 'Run Detail', count: 0 },
]

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'n/a'
  }
  const numeric = Number(value)
  const sign = numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(digits)}%`
}

function formatPlainPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'n/a'
  }
  return `${Number(value).toFixed(digits)}%`
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'n/a'
  }
  return Number(value).toFixed(digits)
}

function formatDate(value) {
  if (!value) {
    return 'n/a'
  }
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function titleCase(value) {
  if (!value) {
    return 'n/a'
  }
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function simplifyModelName(value) {
  if (!value) {
    return 'n/a'
  }
  if (String(value).includes('claude-sonnet-4-6')) {
    return 'Claude Sonnet 4.6'
  }
  return String(value)
}

function normalizeKey(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
}

function shorten(value, maxLength = 220) {
  if (!value) {
    return 'n/a'
  }
  const text = String(value).trim()
  if (text.length <= maxLength) {
    return text
  }
  return `${text.slice(0, maxLength - 1).trim()}...`
}

function getPriorityClass(priority) {
  if (priority === 'high') {
    return 'urgent'
  }
  if (priority === 'medium') {
    return 'watch'
  }
  return 'monitor'
}

function getDirectionTone(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return ''
  }
  return Number(value) >= 0 ? 'pos' : 'neg'
}

function groupChallenges(challenges) {
  const grouped = new Map()
  for (const challenge of challenges) {
    const key = challenge.category || 'Other'
    if (!grouped.has(key)) {
      grouped.set(key, [])
    }
    grouped.get(key).push(challenge)
  }
  return Array.from(grouped.entries())
}

function topHoldings(holdings, count = 4) {
  return [...(holdings || [])]
    .sort((left, right) => Math.abs(Number(right.active_weight || 0)) - Math.abs(Number(left.active_weight || 0)))
    .slice(0, count)
}

function holdingChipLabel(holding) {
  if (!holding) {
    return 'n/a'
  }
  if (typeof holding === 'string') {
    return holding
  }
  if (typeof holding === 'object') {
    return holding.security_name || holding.label || holding.identifier || JSON.stringify(holding)
  }
  return String(holding)
}

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const compactChallenges = evidence.top_challenges || []
  const [selectedChallengeId, setSelectedChallengeId] = useState(compactChallenges[0]?.challenge_id || '')

  const deepByLabel = useMemo(() => {
    const entries = (review.challenge_brief || []).map((item) => [normalizeKey(item.label), item])
    return new Map(entries)
  }, [])

  const packetByAcid = useMemo(() => {
    const entries = (evidence.challenge_support_packets || []).map((item) => [item.acid, item])
    return new Map(entries)
  }, [])

  const researchByAcid = useMemo(() => {
    const entries = (evidence.sharepoint_research_focus || []).map((item) => [item.acid, item])
    return new Map(entries)
  }, [])

  const selectedCompact =
    compactChallenges.find((item) => item.challenge_id === selectedChallengeId) ||
    compactChallenges[0] ||
    null
  const selectedDeep = selectedCompact ? deepByLabel.get(normalizeKey(selectedCompact.label)) || null : null
  const selectedPacket = selectedCompact ? packetByAcid.get(selectedCompact.acid) || null : null
  const selectedResearch = selectedCompact ? researchByAcid.get(selectedCompact.acid) || null : null

  const groupedChallenges = useMemo(() => groupChallenges(compactChallenges), [compactChallenges])
  const riskSummary = evidence.risk_and_attribution?.summary || {}
  const returns = evidence.risk_and_attribution?.return_attribution_mtd || {}
  const selectedSignal = selectedPacket?.exact_vir_algo_decomp_explanation || {}
  const topInsights = review.key_insights || []

  return (
    <div className="shell">
      <aside className="sb">
        <div className="sb-head">
          <div className="sb-wordmark">PM Analyst</div>
          <div className="sb-sub">Challenge Review Workspace</div>
          <div className="sb-date">
            {formatDate(evidence.header.snapshot_date)} | {formatDate(evidence.header.review_date)}
          </div>
        </div>

        <div className="sb-section">Selected Fund</div>
        <div className="fund-item active">
          <div>
            <div className="fund-name">{evidence.header.fund}</div>
            <div className="fund-meta">{evidence.header.benchmark}</div>
          </div>
          <span className="fund-badge fb-red">{compactChallenges.length}</span>
        </div>

        <div className="sb-section">Challenge Queue</div>
        {groupedChallenges.map(([category, items]) => (
          <div key={category} className="sb-group">
            <div className="sb-group-title">{category}</div>
            {items.slice(0, 4).map((item) => (
              <button
                key={item.challenge_id}
                className={`fund-item challenge-item${item.challenge_id === selectedCompact?.challenge_id ? ' active' : ''}`}
                onClick={() => setSelectedChallengeId(item.challenge_id)}
              >
                <div>
                  <div className="fund-name">{item.label}</div>
                  <div className="fund-meta">{shorten(item.challenge_headline, 72)}</div>
                </div>
                <span className={`fund-badge ${item.priority === 'high' ? 'fb-red' : item.priority === 'medium' ? 'fb-amber' : 'fb-blue'}`}>
                  {formatNumber(item.challenge_score, 1)}
                </span>
              </button>
            ))}
          </div>
        ))}

        <div className="sb-section">Run Snapshot</div>
        <div className="sb-meta-list">
          <SidebarMeta label="Model" value={simplifyModelName(manifest.model)} />
          <SidebarMeta label="Output" value={titleCase(manifest.output_style)} />
          <SidebarMeta label="Cost" value={`$${formatNumber(manifest.approx_cost_usd, 4)}`} />
          <SidebarMeta label="Tokens" value={manifest.usage?.totalTokens?.toLocaleString?.() || 'n/a'} />
          <SidebarMeta label="Source snapshot" value={evidence.header.source_snapshot_date || 'n/a'} />
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="tb-fund">{evidence.header.fund}</div>
          <div className="tb-div" />
          <div className="tb-chip">Benchmark: {evidence.header.benchmark}</div>
          <div className="tb-chip tb-chip-red">Selected: {selectedCompact?.label || 'n/a'}</div>
          <div className="tb-chip tb-chip-blue">VIR date: {selectedSignal.vir_snapshot_date || selectedPacket?.vir_snapshot_date || evidence.header.snapshot_date}</div>
          <div className="tb-right">
            <div className="tb-btn">{(evidence.header.pm_names || []).join(', ')}</div>
            <div className="tb-btn tb-btn-red">{manifest.parsed_json_ok ? 'Validated run' : 'Review run'}</div>
          </div>
        </header>

        <nav className="section-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`s-tab${activeTab === tab.id ? ' active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span>{tab.label}</span>
              {tab.count ? <span className="s-tab-badge">{tab.count}</span> : null}
            </button>
          ))}
        </nav>

        <div className="content">
          {activeTab === 'overview' ? (
            <OverviewPage
              selectedCompact={selectedCompact}
              selectedDeep={selectedDeep}
              selectedPacket={selectedPacket}
              selectedResearch={selectedResearch}
              topInsights={topInsights}
              riskSummary={riskSummary}
              returns={returns}
            />
          ) : null}

          {activeTab === 'challenge' ? (
            <ChallengeCardsPage challenges={compactChallenges} packetByAcid={packetByAcid} deepByLabel={deepByLabel} />
          ) : null}

          {activeTab === 'memo' ? (
            <DeepMemoPage challenges={compactChallenges} packetByAcid={packetByAcid} deepByLabel={deepByLabel} />
          ) : null}

          {activeTab === 'risk' ? <RiskPage /> : null}

          {activeTab === 'holdings' ? (
            <HoldingsPage selectedCompact={selectedCompact} selectedPacket={selectedPacket} materialPositions={packet.material_positions || []} />
          ) : null}

          {activeTab === 'research' ? (
            <ResearchPage selectedCompact={selectedCompact} selectedPacket={selectedPacket} selectedDeep={selectedDeep} />
          ) : null}

          {activeTab === 'run' ? <RunPage /> : null}
        </div>
      </main>
    </div>
  )
}

function OverviewPage({ selectedCompact, selectedDeep, selectedPacket, selectedResearch, topInsights, riskSummary, returns }) {
  const signal = selectedPacket?.exact_vir_algo_decomp_explanation || {}
  const researchPath = selectedResearch?.research_path || selectedPacket?.sharepoint_research_path || null
  const externalContext = selectedPacket?.exact_external_market_context || []

  return (
    <div className="section-page active">
      <section className="kpi-row">
        <Kpi label="Active Weight" value={formatPercent(signal.active_weight)} tone={getDirectionTone(signal.active_weight)} sub="Selected challenge" />
        <Kpi label="Latest VIR" value={formatNumber(signal.vir_now, 3)} tone={getDirectionTone(signal.vir_now)} sub={`MoM ${formatNumber(signal.vir_delta_mom, 3)}`} />
        <Kpi label="Latest Algo" value={formatPercent(signal.algo_active_weight)} tone={getDirectionTone(signal.algo_active_weight)} sub={`MoM ${formatPercent(signal.algo_active_weight_mom)}`} />
        <Kpi label="Active Risk" value={formatPlainPercent(riskSummary.active_predicted_risk_pct)} tone="blue" sub="Risk workbook" />
        <Kpi label="MTD Active Return" value={formatPercent(returns.active_period_return)} tone={getDirectionTone(returns.active_period_return)} sub="Month to date" />
      </section>

      <section className="exec-sum">
        <div className="exec-sum-label">Executive Summary</div>
        {(topInsights || []).slice(0, 3).map((item) => (
          <div key={item.label} className="exec-bullet">
            <div className="exec-mark">•</div>
            <div>
              <strong>{item.label}.</strong> {item.why_it_matters}
            </div>
          </div>
        ))}
      </section>

      <section className="two-col">
        <article className="card card-red">
          <div className="card-title">Selected Challenge</div>
          <div className="card-sub">{selectedCompact?.category} | {selectedCompact?.priority} priority</div>

          <div className="signal-squares">
            <SignalSquare label={`Position ${formatPercent(signal.active_weight)}`} tone={getDirectionTone(signal.active_weight)} />
            <SignalSquare label={`VIR ${formatNumber(signal.vir_now, 3)}`} tone={getDirectionTone(signal.vir_now)} />
            <SignalSquare label={`Algo ${formatPercent(signal.algo_active_weight)}`} tone={getDirectionTone(signal.algo_active_weight)} />
            <SignalSquare label={titleCase(signal.signal_alignment)} tone={signal.signal_alignment === 'aligned' ? 'green' : 'amber'} />
            <SignalSquare label={titleCase(signal.decomposition_assessment)} tone="grey" />
          </div>

          <div className="cc-metrics">
            <MetricMini label="Headline" value={selectedCompact?.challenge_headline} />
            <MetricMini label="Primary PM Question" value={selectedCompact?.primary_pm_question} />
            <MetricMini label="Decision Fork" value={selectedDeep?.pm_decision_fork || selectedCompact?.pm_decision_fork} />
          </div>

          <div className="cc-question">
            <div className="cc-q-label">Why It Matters Now</div>
            <div className="cc-q-text">{selectedCompact?.measured_risk_readthrough || selectedCompact?.vir_decomposition_readthrough || 'n/a'}</div>
          </div>
        </article>

        <article className="card card-blue">
          <div className="card-title">Exposure Drilldown</div>
          <div className="card-sub">Aggregated security view, then source sleeves</div>
          <SecurityTable holdings={topHoldings(selectedPacket?.exact_holdings_causing_it, 6)} />
        </article>
      </section>

      <section className="two-col section-gap">
        <article className="card card-red">
          <div className="card-title">Challenge Support</div>
          <div className="card-sub">Thesis pressure, signal stack, and evidence need</div>
          <WaterfallList
            items={[
              ['Positioning tension', selectedCompact?.positioning_tension],
              ['Model tension', selectedCompact?.model_signal_tension],
              ['Risk readthrough', selectedCompact?.measured_risk_readthrough],
              ['Evidence needed next', selectedCompact?.evidence_needed_next],
            ]}
          />
        </article>

        <article className="card card-blue">
          <div className="card-title">Research and Market Context</div>
          <div className="card-sub">Internal deck plus trusted external context</div>
          <div className="research-block">
            <div className="research-label">SharePoint research</div>
            <p>{selectedResearch?.research_summary || selectedPacket?.sharepoint_research_summary || 'No matched SharePoint summary for this challenge.'}</p>
            {researchPath ? <code>{researchPath}</code> : null}
          </div>
          <div className="research-label top-gap">External context</div>
          <div className="context-list">
            {externalContext.slice(0, 2).map((item) => (
              <div key={`${item.source}-${item.headline}`} className="context-item">
                <strong>{item.headline}</strong>
                <p>{item.narrative}</p>
              </div>
            ))}
            {!externalContext.length ? <p>No saved external context on this challenge in the current run.</p> : null}
          </div>
        </article>
      </section>

      <section className="card card-red section-gap">
        <div className="card-title">Challenge Queue Snapshot</div>
        <div className="card-sub">All current challenge cards, sorted by score</div>
        <ChallengeSummaryRows rows={evidence.top_challenges || []} />
      </section>
    </div>
  )
}

function ChallengeCardsPage({ challenges, packetByAcid, deepByLabel }) {
  return (
    <div className="section-page active">
      {(challenges || []).map((challenge) => {
        const packetItem = packetByAcid.get(challenge.acid) || null
        const signal = packetItem?.exact_vir_algo_decomp_explanation || {}
        const deep = deepByLabel.get(normalizeKey(challenge.label)) || null

        return (
          <article key={challenge.challenge_id} className={`cc ${getPriorityClass(challenge.priority)}`}>
            <div className="cc-inner">
              <div className="cc-head">
                <div>
                  <div className="cc-title">{challenge.label}</div>
                  <div className="cc-fund-tag">{challenge.category} | {evidence.header.fund}</div>
                </div>
                <div>
                  <div className={`cc-weight ${Number(signal.active_weight || 0) >= 0 ? 'ow' : 'uw'}`}>{formatPercent(signal.active_weight)}</div>
                  <div className="cc-weight-label">active weight</div>
                </div>
              </div>

              <div className="signal-squares">
                <SignalSquare label={`VIR ${formatNumber(signal.vir_now, 3)}`} tone={getDirectionTone(signal.vir_now)} />
                <SignalSquare label={`Algo ${formatPercent(signal.algo_active_weight)}`} tone={getDirectionTone(signal.algo_active_weight)} />
                <SignalSquare label={titleCase(signal.signal_alignment)} tone={signal.signal_alignment === 'aligned' ? 'green' : 'amber'} />
                <SignalSquare label={titleCase(signal.decomposition_driver)} tone="grey" />
                <SignalSquare label={titleCase(challenge.priority)} tone={challenge.priority === 'high' ? 'red' : challenge.priority === 'medium' ? 'amber' : 'blue'} />
              </div>

              <div className="cc-metrics">
                <MetricMini label="Challenge headline" value={challenge.challenge_headline} />
                <MetricMini label="Positioning tension" value={challenge.positioning_tension} />
                <MetricMini label="Model tension" value={challenge.model_signal_tension} />
              </div>

              <div className="cc-question">
                <div className="cc-q-label">Primary PM Question</div>
                <div className="cc-q-text">{challenge.primary_pm_question}</div>
              </div>

              {deep ? (
                <div className="challenge-tail-grid">
                  <MemoSnippet title="Bull case" body={deep.bull_case} />
                  <MemoSnippet title="Bear case" body={deep.bear_case} />
                  <MemoSnippet title="What would change my mind" body={deep.what_would_change_my_mind} />
                </div>
              ) : null}
            </div>
          </article>
        )
      })}
    </div>
  )
}

function DeepMemoPage({ challenges, packetByAcid, deepByLabel }) {
  return (
    <div className="section-page active">
      {(challenges || []).map((challenge) => {
        const deep = deepByLabel.get(normalizeKey(challenge.label)) || null
        if (!deep) {
          return null
        }

        const packetItem = packetByAcid.get(challenge.acid) || null
        const holdings = topHoldings(packetItem?.exact_holdings_causing_it, 4)
        const signal = packetItem?.exact_vir_algo_decomp_explanation || {}

        return (
          <article key={challenge.challenge_id} className="dm">
            <div className={`dm-rule ${challenge.priority === 'high' ? '' : 'dm-rule-amber'}`} />
            <div className="dm-header">
              <div>
                <div className="dm-title">{challenge.label}</div>
                <div className="dm-sub">
                  {challenge.category} | active {formatPercent(signal.active_weight)} | VIR {formatNumber(signal.vir_now, 3)} | Algo {formatPercent(signal.algo_active_weight)}
                </div>
                <div className="dm-verdict-row">
                  <span className="dm-v-tag dm-v-red">{titleCase(challenge.priority)}</span>
                  <span className="dm-v-tag dm-v-blue">{titleCase(signal.signal_alignment)}</span>
                  <span className="dm-v-tag dm-v-amber">{titleCase(signal.decomposition_assessment)}</span>
                  <span className="dm-v-tag dm-v-green">{deep.source_quality || challenge.source_quality}</span>
                </div>
              </div>
              <div className="dm-weight">{formatPercent(signal.active_weight)}</div>
            </div>

            <div className="dm-body">
              <MemoSection title="Thesis Under Pressure" body={deep.thesis_under_pressure} />
              <MemoSection title="Positioning Tension" body={deep.positioning_tension} />
              <MemoSection title="Model Signal Tension" body={deep.model_signal_tension} />
              <MemoSection title="Bull Case" body={deep.bull_case} />
              <MemoSection title="Bear Case" body={deep.bear_case} />
              <MemoSection title="Devil's Advocate" body={deep.devils_advocate} />
              <MemoSection title="What Would Change My Mind" body={deep.what_would_change_my_mind} />
              <MemoSection title="PM Decision Fork" body={deep.pm_decision_fork} />

              <div className="dm-sec">
                <div className="dm-sec-title">Exact Holdings Causing It</div>
                {holdings.map((item) => (
                  <div key={`${challenge.challenge_id}-${item.security_name}`} className="dm-holding-row">
                    <div className="dm-holding-name">{item.security_name}</div>
                    <div className={`dm-holding-val ${Number(item.active_weight || 0) < 0 ? 'neg' : ''}`}>{formatPercent(item.active_weight)}</div>
                  </div>
                ))}
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}

function RiskPage() {
  const risk = evidence.risk_and_attribution || {}
  const summary = risk.summary || {}
  const returns = risk.return_attribution_mtd || {}

  return (
    <div className="section-page active">
      <section className="kpi-row">
        <Kpi label="Active Predicted Risk" value={formatPlainPercent(summary.active_predicted_risk_pct)} tone="red" sub="Total" />
        <Kpi label="Active Factor Risk" value={formatPlainPercent(summary.active_factor_risk_pct)} tone="blue" sub="Factor" />
        <Kpi label="Active Specific Risk" value={formatPlainPercent(summary.active_specific_risk_pct)} tone="amber" sub="Specific" />
        <Kpi label="Active Share" value={formatPlainPercent(summary.active_share_pct)} tone="blue" sub="Share" />
        <Kpi label="MTD Active Return" value={formatPercent(returns.active_period_return)} tone={getDirectionTone(returns.active_period_return)} sub="Risk workbook" />
      </section>

      <section className="two-col">
        <article className="card card-red">
          <div className="card-title">Top Style Risk Drivers</div>
          <div className="card-sub">Largest contributors to active style variance</div>
          <BarDriverList items={risk.top_style_risk_drivers || []} />
        </article>

        <article className="card card-blue">
          <div className="card-title">Top Industry Risk Drivers</div>
          <div className="card-sub">Largest contributors to active industry variance</div>
          <BarDriverList items={risk.top_industry_risk_drivers || []} />
        </article>
      </section>

      <section className="two-col section-gap">
        <article className="card card-red">
          <div className="card-title">Likely Holdings Contributors</div>
          <div className="card-sub">Mapped from the risk workbook into holdings</div>
          <RiskContributorList items={risk.likely_holdings_contributors || []} />
        </article>

        <article className="card card-blue">
          <div className="card-title">Specific-Risk Watchlist</div>
          <div className="card-sub">Flagged exposures from the risk workbook</div>
          <RiskWatchlist items={risk.specific_risk_watchlist || []} />
        </article>
      </section>
    </div>
  )
}

function HoldingsPage({ selectedCompact, selectedPacket, materialPositions }) {
  return (
    <div className="section-page active">
      <section className="card card-red">
        <div className="card-title">Selected Challenge Holdings</div>
        <div className="card-sub">
          {selectedCompact?.label || 'n/a'} | aggregated by security first, then split by source sleeve
        </div>
        <SecurityTable holdings={selectedPacket?.exact_holdings_causing_it || []} expanded />
      </section>

      <section className="two-col section-gap">
        <article className="card card-blue">
          <div className="card-title">Largest Overweights</div>
          <div className="card-sub">Material positions from the packet</div>
          <PositionRows rows={[...(materialPositions || [])].filter((item) => Number(item.active_weight || 0) > 0).slice(0, 10)} />
        </article>

        <article className="card card-red">
          <div className="card-title">Largest Underweights</div>
          <div className="card-sub">Material positions from the packet</div>
          <PositionRows rows={[...(materialPositions || [])].filter((item) => Number(item.active_weight || 0) < 0).slice(0, 10)} />
        </article>
      </section>
    </div>
  )
}

function ResearchPage({ selectedCompact, selectedPacket, selectedDeep }) {
  return (
    <div className="section-page active">
      <section className="two-col">
        <article className="card card-blue">
          <div className="card-title">SharePoint Research Map</div>
          <div className="card-sub">Files the agent matched for framing and sector context</div>
          <ResearchTileList items={evidence.sharepoint_research_focus || []} />
        </article>

        <article className="card card-red">
          <div className="card-title">Selected Challenge Framing</div>
          <div className="card-sub">{selectedCompact?.label || 'n/a'}</div>
          <WaterfallList
            items={[
              ['Internal research excerpt', selectedDeep?.exact_internal_research_excerpt || selectedPacket?.exact_internal_research_excerpt],
              ['What would change my mind', selectedDeep?.what_would_change_my_mind],
              ['Evidence needed next', selectedDeep?.evidence_needed_next || selectedCompact?.evidence_needed_next],
              ['Source quality', selectedDeep?.source_quality || selectedCompact?.source_quality],
            ]}
          />
        </article>
      </section>

      <section className="card card-red section-gap">
        <div className="card-title">PM Questions</div>
        <div className="card-sub">Questions the current run thinks matter most</div>
        <PmQuestionRows items={review.pm_questions || []} />
      </section>
    </div>
  )
}

function RunPage() {
  return (
    <div className="section-page active">
      <section className="kpi-row">
        <Kpi label="Model" value={simplifyModelName(manifest.model)} tone="blue" sub="Bedrock" />
        <Kpi label="Approx Cost" value={`$${formatNumber(manifest.approx_cost_usd, 4)}`} tone="amber" sub="Saved run" />
        <Kpi label="Total Tokens" value={manifest.usage?.totalTokens?.toLocaleString?.() || 'n/a'} tone="blue" sub="Prompt + output" />
        <Kpi label="Output Style" value={titleCase(manifest.output_style)} tone="red" sub="Review mode" />
        <Kpi label="JSON Status" value={manifest.parsed_json_ok ? 'Valid' : 'Check'} tone={manifest.parsed_json_ok ? 'blue' : 'red'} sub="Manifest" />
      </section>

      <section className="two-col">
        <article className="card card-blue">
          <div className="card-title">Artifacts</div>
          <div className="card-sub">Saved files from this run</div>
          <ArtifactRows items={Object.entries(manifest.artifacts || {})} />
        </article>

        <article className="card card-red">
          <div className="card-title">Data Quality Flags</div>
          <div className="card-sub">Saved packet checks and caveats</div>
          <WaterfallList
            items={Object.entries(packet.data_quality_flags || {}).map(([key, value]) => [titleCase(key), typeof value === 'string' ? value : JSON.stringify(value)])}
          />
        </article>
      </section>
    </div>
  )
}

function Kpi({ label, value, tone, sub }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-val ${tone || ''}`}>{value}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  )
}

function SignalSquare({ label, tone }) {
  const className =
    tone === 'neg'
      ? 'sq sq-red'
      : tone === 'pos'
        ? 'sq sq-blue'
        : tone === 'green'
          ? 'sq sq-green'
          : tone === 'amber'
            ? 'sq sq-amber'
            : 'sq sq-grey'
  return (
    <div className="sq-item">
      <span className={className} />
      <span>{label}</span>
    </div>
  )
}

function MetricMini({ label, value }) {
  return (
    <div className="cc-metric">
      <div className="cc-metric-label">{label}</div>
      <div className="cc-metric-val">{shorten(value, 160)}</div>
    </div>
  )
}

function MemoSection({ title, body }) {
  return (
    <div className="dm-sec">
      <div className="dm-sec-title">{title}</div>
      <div className="dm-text">{body || 'n/a'}</div>
    </div>
  )
}

function MemoSnippet({ title, body }) {
  return (
    <div className="memo-snippet">
      <div className="memo-snippet-title">{title}</div>
      <p>{shorten(body, 220)}</p>
    </div>
  )
}

function WaterfallList({ items }) {
  return (
    <div>
      {items.map(([label, value]) => (
        <div key={label} className="wf-row text-row">
          <div className="wf-name">{label}</div>
          <div className="wf-text">{value || 'n/a'}</div>
        </div>
      ))}
    </div>
  )
}

function ChallengeSummaryRows({ rows }) {
  const sorted = [...rows].sort((left, right) => Number(right.challenge_score || 0) - Number(left.challenge_score || 0))
  const maxScore = Math.max(...sorted.map((row) => Number(row.challenge_score || 0)), 1)

  return (
    <div>
      {sorted.map((row) => {
        const scorePct = (Number(row.challenge_score || 0) / maxScore) * 100
        return (
          <div key={row.challenge_id} className="wf-row">
            <div className={`wf-name ${row.priority === 'high' ? 'flag' : ''}`}>{row.label}</div>
            <div className="wf-bars">
              <div className="wf-track">
                <div className={`wf-bar ${row.priority === 'high' ? 'cf' : Number(row.challenge_score || 0) >= 0 ? 'ow' : 'uw'}`} style={{ width: `${scorePct}%` }} />
              </div>
            </div>
            <div className="wf-val">{formatNumber(row.challenge_score, 1)}</div>
            <div className="wf-vir">{titleCase(row.priority)}</div>
          </div>
        )
      })}
    </div>
  )
}

function SecurityTable({ holdings, expanded = false }) {
  return (
    <div>
      {(holdings || []).map((holding) => (
        <details key={`${holding.security_name}-${holding.identifier}`} className="security-detail" open={expanded}>
          <summary className="security-summary">
            <div className="security-name">{holding.security_name}</div>
            <div className="security-metrics">
              <span>{formatPlainPercent(holding.portfolio_weight)}</span>
              <span>{formatPlainPercent(holding.benchmark_weight)}</span>
              <span className={Number(holding.active_weight || 0) >= 0 ? 'ow-text' : 'uw-text'}>{formatPercent(holding.active_weight)}</span>
            </div>
          </summary>
          <div className="security-source-wrap">
            {(holding.sources || []).map((source) => (
              <div key={`${holding.security_name}-${source.source_name}`} className="security-source-row">
                <div>{source.source_name}</div>
                <div>{formatPlainPercent(source.portfolio_weight)}</div>
                <div>{formatPlainPercent(source.benchmark_weight)}</div>
                <div className={Number(source.active_weight || 0) >= 0 ? 'ow-text' : 'uw-text'}>{formatPercent(source.active_weight)}</div>
              </div>
            ))}
          </div>
        </details>
      ))}
      {!holdings?.length ? <div className="empty-note">No holding drilldown saved for this selection.</div> : null}
    </div>
  )
}

function BarDriverList({ items }) {
  const maxValue = Math.max(...(items || []).map((item) => Number(item.share_of_variance_pct || item.active_weight || 0)), 1)
  return (
    <div>
      {(items || []).map((item) => {
        const value = Number(item.share_of_variance_pct || item.active_weight || 0)
        const width = Math.max((Math.abs(value) / maxValue) * 100, 4)
        return (
          <div key={item.label || item.risk_driver} className="wf-row">
            <div className="wf-name">{item.label || item.risk_driver}</div>
            <div className="wf-bars">
              <div className="wf-track">
                <div className={`wf-bar ${value >= 0 ? 'ow' : 'uw'}`} style={{ width: `${width}%` }} />
              </div>
            </div>
            <div className="wf-val">{formatPlainPercent(value)}</div>
            <div className="wf-vir">{item.mapped_sector || item.signal_alignment || ''}</div>
          </div>
        )
      })}
    </div>
  )
}

function RiskContributorList({ items }) {
  return (
    <div className="stack-list">
      {(items || []).map((item) => (
        <article key={item.risk_driver} className="mini-card">
          <div className="mini-head">
            <strong>{item.risk_driver}</strong>
            <span>{formatPlainPercent(item.share_of_variance_pct)}</span>
          </div>
          <p>
            {item.mapped_sector} | active {formatPercent(item.active_weight)} | {titleCase(item.signal_alignment)}
          </p>
          <div className="mini-chip-row">
            {(item.top_sector_holdings || []).slice(0, 4).map((holding) => (
              <span key={`${item.risk_driver}-${holdingChipLabel(holding)}`} className="mini-chip">{holdingChipLabel(holding)}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  )
}

function RiskWatchlist({ items }) {
  return (
    <div className="stack-list">
      {(items || []).map((item) => (
        <article key={`${item.category}-${item.label}`} className="mini-card">
          <div className="mini-head">
            <strong>{item.label}</strong>
            <span>{formatPercent(item.active_weight)}</span>
          </div>
          <p>{item.category}</p>
          <div className="mini-chip-row">
            {(item.top_sector_holdings || []).slice(0, 4).map((holding) => (
              <span key={`${item.label}-${holdingChipLabel(holding)}`} className="mini-chip">{holdingChipLabel(holding)}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  )
}

function PositionRows({ rows }) {
  return (
    <div>
      {(rows || []).map((item) => (
        <div key={item.position_id} className="wf-row">
          <div className="wf-name">{item.label}</div>
          <div className="wf-bars">
            <div className="wf-track">
              <div
                className={`wf-bar ${Number(item.active_weight || 0) >= 0 ? 'ow' : 'uw'}`}
                style={{ width: `${Math.min(Math.abs(Number(item.active_weight || 0)) * 10, 100)}%` }}
              />
            </div>
          </div>
          <div className="wf-val">{formatPercent(item.active_weight)}</div>
          <div className="wf-vir">{formatNumber(item.vir_now, 3)}</div>
        </div>
      ))}
    </div>
  )
}

function ResearchTileList({ items }) {
  return (
    <div className="stack-list">
      {(items || []).map((item) => (
        <article key={`${item.acid}-${item.research_path}`} className="mini-card">
          <div className="mini-head">
            <strong>{item.label}</strong>
            <span>{item.category}</span>
          </div>
          <p>{item.research_summary}</p>
          <code>{item.research_path}</code>
        </article>
      ))}
    </div>
  )
}

function PmQuestionRows({ items }) {
  return (
    <div className="pm-question-list">
      {(items || []).map((item) => (
        <div key={item.label} className="pm-question-row">
          <div className="pm-question-title">{item.label}</div>
          <div className="pm-question-body">{item.question}</div>
          <div className="pm-question-why">{item.why_now}</div>
        </div>
      ))}
    </div>
  )
}

function ArtifactRows({ items }) {
  return (
    <div className="artifact-list">
      {(items || []).map(([label, value]) => (
        <div key={label} className="artifact-row">
          <div className="artifact-label">{label}</div>
          <code>{value}</code>
        </div>
      ))}
    </div>
  )
}

function SidebarMeta({ label, value }) {
  return (
    <div className="sb-meta-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
