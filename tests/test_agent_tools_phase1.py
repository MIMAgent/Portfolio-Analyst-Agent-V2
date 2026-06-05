"""Phase 1 read-tool coverage: mapping, lineage, peer context, and memory authority."""

from __future__ import annotations

from datetime import date
import csv
import json

from portfolio_analyst_agent.agent_tools import get_exposure_lineage, get_fund_snapshot, get_market_context, get_peer_context
from portfolio_analyst_agent.memory_store import recall_memory_store


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _mapping_row(acid, group="g", *, investable="true"):
    return {
        "acid": acid,
        "asset_class_name": acid,
        "model_family": "equity",
        "family": "Equity",
        "comparison_group": group,
        "relative_value_group": group,
        "interpretation_type": "sector_relative_value",
        "investable_flag": investable,
        "subtype": "",
        "market_scope": "",
        "region": "",
        "country": "",
        "sector": "",
        "style": "",
        "currency_exposure_type": "",
        "maturity_bucket": "",
        "curve_aware": "false",
        "parent_family": "",
        "index_provider": "",
        "benchmark_role": "",
        "notes": "",
    }


def test_get_fund_snapshot_enriches_acid_rows_with_mapping(tmp_path):
    alignment = tmp_path / "alignment.csv"
    mapping = tmp_path / "mapping.csv"
    _write_csv(
        alignment,
        [
            {
                "snapshot_date": "2026-04-06",
                "fund": "Fund",
                "acid": "US IT EQ",
                "acid_type": "acid_region_sector",
                "vir_snapshot_date": "2026-04-06",
                "algo_snapshot_date": "",
            }
        ],
    )
    _write_csv(mapping, [_mapping_row("US IT EQ")])

    snapshot = get_fund_snapshot(
        "Fund",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        alignment_csv=alignment,
        mapping_csv=mapping,
    )

    assert snapshot["acid_rows"][0]["mapping_status"] == "matched_to_mapping"
    assert snapshot["acid_rows"][0]["mapping_interpretation_type"] == "sector_relative_value"


def test_get_exposure_lineage_returns_largest_contributors_first(tmp_path):
    detail = tmp_path / "detail.csv"
    _write_csv(
        detail,
        [
            {
                "snapshot_date": "2026-04-06",
                "fund": "Fund",
                "acid": "US LRG EQ",
                "security_name": "Small",
                "fund_target_security_contribution": "1.0",
            },
            {
                "snapshot_date": "2026-04-06",
                "fund": "Fund",
                "acid": "US LRG EQ",
                "security_name": "Large",
                "fund_target_security_contribution": "5.0",
            },
        ],
    )

    lineage = get_exposure_lineage(
        "Fund",
        "US LRG EQ",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        detail_csv=detail,
        limit=1,
    )

    assert lineage["row_count"] == 2
    assert lineage["rows"][0]["security_name"] == "Large"


def test_get_peer_context_uses_mapping_groups(tmp_path):
    alignment = tmp_path / "alignment.csv"
    mapping = tmp_path / "mapping.csv"
    _write_csv(
        alignment,
        [
            {
                "snapshot_date": "2026-04-06",
                "fund": "Fund",
                "acid": "US IT EQ",
                "acid_type": "acid_region_sector",
                "vir_snapshot_date": "2026-04-06",
                "algo_snapshot_date": "",
            },
            {
                "snapshot_date": "2026-04-06",
                "fund": "Fund",
                "acid": "US CD EQ",
                "acid_type": "acid_region_sector",
                "vir_snapshot_date": "2026-04-06",
                "algo_snapshot_date": "",
            },
        ],
    )
    _write_csv(mapping, [_mapping_row("US IT EQ", "sectors"), _mapping_row("US CD EQ", "sectors")])

    context = get_peer_context(
        "US IT EQ",
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        alignment_csv=alignment,
        mapping_csv=mapping,
    )

    assert context["peer_count"] == 1
    assert context["peers"][0]["acid"] == "US CD EQ"
    assert context["peers"][0]["citation_ref"].startswith(f"csv:{mapping.as_posix()}#row_id=")
    assert context["mapping"]["citation_ref"].startswith(f"csv:{mapping.as_posix()}#row_id=")
    assert context["current_snapshot_row_count"] == 2


def test_get_market_context_filters_replay_safe_context_and_adds_citations(tmp_path):
    market_context = tmp_path / "monthly_market_context.csv"
    _write_csv(
        market_context,
        [
            {
                "snapshot_date": "2026-04-06",
                "as_of_date": "2026-04-06",
                "scope_type": "acid",
                "scope_value": "US IT EQ",
                "priority": "1",
                "headline": "Earnings revisions softened",
                "narrative": "Technology earnings revision breadth weakened.",
                "fundamental_readthrough": "Underweight review should consider earnings risk.",
                "pm_question": "Is the underweight valuation-led or earnings-risk-led?",
                "source_label": "Monthly deck",
                "source_date": "2026-04-05",
            },
            {
                "snapshot_date": "2026-04-07",
                "as_of_date": "2026-04-07",
                "scope_type": "acid",
                "scope_value": "US IT EQ",
                "priority": "1",
                "headline": "Future context",
                "narrative": "This should not be visible.",
                "fundamental_readthrough": "",
                "pm_question": "",
                "source_label": "Future deck",
                "source_date": "2026-04-07",
            },
        ],
    )

    context = get_market_context(
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        acid="US IT EQ",
        market_context_csv=market_context,
    )

    assert context["context_status"] == "matched_context_rows"
    assert context["row_count"] == 1
    assert context["rows"][0]["headline"] == "Earnings revisions softened"
    assert context["rows"][0]["citation_ref"].startswith(f"csv:{market_context.as_posix()}#row_id=")


def test_get_market_context_prefers_exact_acid_rows_over_broad_market_rows(tmp_path):
    market_context = tmp_path / "monthly_market_context.csv"
    _write_csv(
        market_context,
        [
            {
                "snapshot_date": "2026-06-04",
                "as_of_date": "2026-06-04",
                "scope_type": "market",
                "scope_value": "US equity earnings",
                "priority": "1",
                "headline": "Broad S&P 500 earnings scorecard",
                "narrative": "S&P 500 companies reported broad earnings growth.",
                "fundamental_readthrough": "",
                "pm_question": "",
                "source_label": "FactSet",
                "source_date": "2026-05-29",
            },
            {
                "snapshot_date": "2026-06-04",
                "as_of_date": "2026-06-04",
                "scope_type": "acid",
                "scope_value": "US IT EQ",
                "priority": "3",
                "headline": "Information Technology revenue surprise",
                "narrative": "Information Technology reported positive revenue surprises and AI capex support.",
                "fundamental_readthrough": "",
                "pm_question": "",
                "source_label": "FactSet",
                "source_date": "2026-05-29",
            },
        ],
    )

    context = get_market_context(
        snapshot_date="2026-06-04",
        as_of_date="2026-06-04",
        acid="US IT EQ",
        market_context_csv=market_context,
    )

    assert context["rows"][0]["headline"] == "Information Technology revenue surprise"


def test_get_market_context_prefers_acid_specific_language_within_same_scope(tmp_path):
    market_context = tmp_path / "monthly_market_context.csv"
    _write_csv(
        market_context,
        [
            {
                "snapshot_date": "2026-06-04",
                "as_of_date": "2026-06-04",
                "scope_type": "acid",
                "scope_value": "US IT EQ",
                "priority": "1",
                "headline": "Generic scorecard",
                "narrative": "Earnings scorecard: companies reporting actual results showed broad S&P 500 EPS beats.",
                "fundamental_readthrough": "",
                "pm_question": "",
                "source_label": "FactSet",
                "source_date": "2026-05-29",
            },
            {
                "snapshot_date": "2026-06-04",
                "as_of_date": "2026-06-04",
                "scope_type": "acid",
                "scope_value": "US IT EQ",
                "priority": "2",
                "headline": "IT-specific revisions",
                "narrative": "Information Technology revenue growth improved with AI and data center capital spending support.",
                "fundamental_readthrough": "",
                "pm_question": "",
                "source_label": "FactSet",
                "source_date": "2026-05-29",
            },
        ],
    )

    context = get_market_context(
        snapshot_date="2026-06-04",
        as_of_date="2026-06-04",
        acid="US IT EQ",
        market_context_csv=market_context,
    )

    assert context["rows"][0]["headline"] == "IT-specific revisions"


def test_recall_memory_excludes_proposed_from_authoritative_rows_but_counts_it(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    memory_path.write_text(
        json.dumps(
            {
                "schema_version": "agent_memory_v1",
                "tables": {
                    "thesis_ledger": [
                        {
                            "fund": "Fund",
                            "acid": "US IT EQ",
                            "review_state": "proposed",
                            "status": "active",
                            "thesis_id": "proposed",
                        },
                        {
                            "fund": "Fund",
                            "acid": "US IT EQ",
                            "review_state": "approved",
                            "status": "active",
                            "thesis_id": "approved",
                        },
                    ],
                    "open_challenges": [],
                    "exceptions": [],
                    "watch_items": [],
                },
            }
        ),
        encoding="utf-8",
    )

    memory = recall_memory_store(
        fund="Fund",
        snapshot_date=date(2026, 4, 6),
        as_of_date=date(2026, 4, 6),
        memory_path=memory_path,
    )

    assert [row["thesis_id"] for row in memory["thesis_ledger"]] == ["approved"]
    assert memory["summary"]["proposed_count"] == 1
    assert memory["summary"]["authority_rule"] == "approved_applied_only"
