"""Stability tests for the row-id backbone.

Row IDs are the audit/replay backbone: every generated artifact row carries one,
and citations reference them. If these hashes are not stable and deterministic,
nothing downstream is auditable. These tests pin that contract.
"""

from __future__ import annotations

from datetime import date

from portfolio_analyst_agent import row_ids


def test_hybrid_id_is_deterministic():
    a = row_ids.fund_summary_row_id(
        snapshot_date="2026-04-06", fund="MStar US Equity", acid_type="acid_country", acid="US LRG EQ"
    )
    b = row_ids.fund_summary_row_id(
        snapshot_date="2026-04-06", fund="MStar US Equity", acid_type="acid_country", acid="US LRG EQ"
    )
    assert a == b
    assert a.startswith("fsum_")
    # 12 hex chars of digest after the prefix.
    assert len(a.split("_", 1)[1]) == 12


def test_hybrid_id_is_sensitive_to_each_field():
    base = dict(
        snapshot_date="2026-04-06", fund="MStar US Equity", acid_type="acid_country", acid="US LRG EQ"
    )
    base_id = row_ids.fund_summary_row_id(**base)
    for field, changed in [
        ("snapshot_date", "2026-05-06"),
        ("fund", "MStar International Equity"),
        ("acid_type", "acid_region_sector"),
        ("acid", "US MID EQ"),
    ]:
        variant = {**base, field: changed}
        assert row_ids.fund_summary_row_id(**variant) != base_id, f"id should change when {field} changes"


def test_prefix_distinguishes_artifact_families():
    # Same logical coordinates, different artifact family => different namespace prefix.
    fsum = row_ids.fund_summary_row_id(
        snapshot_date="2026-04-06", fund="F", acid_type="acid_bond", acid="Alts"
    )
    fdet = row_ids.fund_detail_row_id(
        snapshot_date="2026-04-06", fund="F", account_name="A", security_name="S",
        acid_type="acid_bond", acid="Alts",
    )
    assert fsum.startswith("fsum_")
    assert fdet.startswith("fdet_")
    assert fsum.split("_")[1] != fdet.split("_")[1]


def test_normalize_handles_dates_and_none():
    iso_id = row_ids.coverage_row_id(snapshot_date=date(2026, 4, 6), fund="F")
    str_id = row_ids.coverage_row_id(snapshot_date="2026-04-06", fund="F")
    # date and its ISO string normalize identically.
    assert iso_id == str_id


def test_generic_row_id_ignores_existing_row_id_key():
    with_id = row_ids.generic_row_id({"a": 1, "b": 2, "row_id": "stale"}, namespace="ns")
    without_id = row_ids.generic_row_id({"a": 1, "b": 2}, namespace="ns")
    assert with_id == without_id


def test_fund_alignment_prefix_depends_on_perspective():
    with_persp = row_ids.fund_alignment_row_id(
        snapshot_date="2026-04-06", fund="F", acid_type="acid_country", acid="X", algo_perspective="local_real"
    )
    without_persp = row_ids.fund_alignment_row_id(
        snapshot_date="2026-04-06", fund="F", acid_type="acid_country", acid="X"
    )
    assert with_persp.startswith("fms_")
    assert without_persp.startswith("falg_")
