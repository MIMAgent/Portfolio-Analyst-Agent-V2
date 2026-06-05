"""C1 regression: cross-ACID-type double-counting in the fund summary.

acid_country and acid_region_sector are alternate taxonomies over the same
securities. Summing exposure across types reported ~199% for equity funds in the
IC-facing markdown. Exposure must be summed within each type.
"""

from __future__ import annotations

from portfolio_analyst_agent.fund_weights_summary import (
    FundCombinedRow,
    _exposure_by_acid_type,
    build_fund_weights_summary_markdown,
)


def _row(acid_type, acid, target, *, perspective_dupe=False):
    return FundCombinedRow(
        snapshot_date="2026-04-06",
        fund="MStar US Equity",
        acid_type=acid_type,
        acid=acid,
        fund_target_rolled_exposure=target,
        fund_benchmark_rolled_exposure=target,
        active_rolled_exposure=0.0,
        source_security_count=1,
        sample_source_securities="x",
        vir_stf=None,
        vir_delta_stf=None,
        algo_absolute_weight=None,
        algo_active_weight=None,
        algo_benchmark_weight=None,
        vir_join_status="matched_to_vir",
        algo_join_status="matched_to_algo" if perspective_dupe else "missing_in_algo",
    )


def _equity_fund_rows():
    # Two full taxonomies over the same fund, each summing to 100%.
    country = [_row("acid_country", "US LRG EQ", 60.0), _row("acid_country", "US SML EQ", 40.0)]
    region = [_row("acid_region_sector", "US IT EQ", 70.0), _row("acid_region_sector", "US FN EQ", 30.0)]
    return country + region


def test_exposure_summed_within_type_not_across():
    totals = _exposure_by_acid_type(_equity_fund_rows(), lambda r: r.fund_target_rolled_exposure)
    assert totals["acid_country"] == 100.0
    assert totals["acid_region_sector"] == 100.0
    # The bug summed across types -> 200. The per-type max must stay ~100.
    assert max(totals.values()) <= 101.0


def test_duplicate_acid_rows_counted_once():
    # Simulate the multisignal CSV's per-perspective duplication of the same acid.
    rows = [_row("acid_country", "US LRG EQ", 60.0), _row("acid_country", "US LRG EQ", 60.0, perspective_dupe=True)]
    totals = _exposure_by_acid_type(rows, lambda r: r.fund_target_rolled_exposure)
    assert totals["acid_country"] == 60.0  # counted once, not 120


def test_markdown_has_no_double_counted_total():
    md = build_fund_weights_summary_markdown(_equity_fund_rows())
    # Per-type breakdown present...
    assert "summed target rolled exposure by ACID type:" in md
    assert "acid_country: 100.0000" in md
    assert "acid_region_sector: 100.0000" in md
    # ...and the old single double-counted line is gone.
    assert "summed target rolled exposure: 199" not in md
    assert "summed target rolled exposure: 200" not in md
