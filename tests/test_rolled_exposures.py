"""Regression tests for the rolled-exposure account-block detection (audit C3).

C3: a hardcoded `range(5, 83)` truncated the account block at row 82, silently
dropping the bond benchmark accounts at rows 83-88. That dropout zeroed benchmark
coverage for the bond funds and produced phantom 100% "active" bets downstream.
The block now extends dynamically to the first blank secid, with a hard assertion
that it reaches at least the known minimum extent.
"""

from __future__ import annotations

import pytest

from portfolio_analyst_agent.workbook_xml import Worksheet
from portfolio_analyst_agent import rolled_exposures
from portfolio_analyst_agent.rolled_exposures import (
    ACCOUNT_BLOCK_FIRST_ROW,
    ACCOUNT_BLOCK_MIN_LAST_ROW,
    _account_rows,
    _fund_blocks,
)


def _build_sheet(last_account_row: int) -> Worksheet:
    """Synthetic Portfolio sheet: one fund block + accounts on rows 5..last (inclusive).

    Row 1 col 7  : fund name        (FundBlock.new_column)
    Row 4 col 9  : benchmark header ending in "_bmk" (enables benchmark column)
    Account rows : col 2 secid, col 1 name, col 8 target weight, col 9 benchmark weight
    """
    rows: dict[int, dict[int, str]] = {
        1: {7: "Test Fund"},
        4: {9: "Test Fund_bmk"},
    }
    for r in range(ACCOUNT_BLOCK_FIRST_ROW, last_account_row + 1):
        rows[r] = {1: f"Account {r}", 2: f"SECID{r:05d}", 8: "1.0", 9: "0.5"}
    # A blank-secid row terminates the block.
    rows[last_account_row + 1] = {1: "", 2: ""}
    return Worksheet(name="Portfolio", rows=rows)


def test_account_block_includes_row_83_and_beyond():
    """The dropped accounts at rows 83-88 must now be read (regression for C3)."""
    sheet = _build_sheet(last_account_row=88)
    blocks = _fund_blocks(sheet)
    accounts = _account_rows(sheet, blocks)

    secids = {a.secid for a in accounts}
    assert "SECID00083" in secids, "row 83 account (previously dropped) must be included"
    for r in range(83, 89):
        assert f"SECID{r:05d}" in secids, f"row {r} account must be included"
    # Rows 5..88 inclusive => 84 accounts, none silently dropped.
    assert len(accounts) == 88 - ACCOUNT_BLOCK_FIRST_ROW + 1


def test_block_stops_at_first_blank_secid():
    sheet = _build_sheet(last_account_row=90)
    accounts = _account_rows(sheet, _fund_blocks(sheet))
    # Block ends at the blank row 91; nothing past it leaks in.
    assert max(int(a.secid.removeprefix("SECID")) for a in accounts) == 90


def test_truncated_block_raises_rather_than_emitting_partial_numbers():
    """A block that ends before the known minimum extent must fail loudly."""
    short = _build_sheet(last_account_row=ACCOUNT_BLOCK_MIN_LAST_ROW - 2)
    with pytest.raises(ValueError, match="Account block ended at row"):
        _account_rows(short, _fund_blocks(short))


def test_min_last_row_constant_covers_known_benchmark_accounts():
    # The real Portfolio sheet's bond benchmark accounts live at rows 83-88;
    # the guard must require reaching at least row 83.
    assert rolled_exposures.ACCOUNT_BLOCK_MIN_LAST_ROW >= 83


# --- C2: phantom active bets on empty benchmark coverage ---------------------

from portfolio_analyst_agent.rolled_exposures import _fund_summary_rows


def _detail_row(fund, acid_type, acid, target, benchmark):
    return {
        "fund": fund,
        "acid_type": acid_type,
        "acid": acid,
        "security_name": f"{acid} sec",
        "fund_target_security_contribution": target,
        "fund_benchmark_security_contribution": benchmark,
    }


def _coverage_row(fund, total_benchmark_weight):
    return {
        "fund": fund,
        "snapshot_date": "2026-04-06",
        "ingested_at": "2026-04-06T00:00:00Z",
        "source_file": "wb.xlsm",
        "matched_target_weight": 1.0,
        "target_match_pct": 1.0,
        "matched_benchmark_weight": total_benchmark_weight,
        "benchmark_match_pct": 1.0 if total_benchmark_weight else "",
        "total_benchmark_weight": total_benchmark_weight,
    }


def test_active_nulled_when_fund_has_no_benchmark_coverage():
    detail = [_detail_row("Alt Fund", "acid_bond", "Alts", 100.0, 0.0)]
    coverage = [_coverage_row("Alt Fund", total_benchmark_weight=0.0)]
    (row,) = _fund_summary_rows(detail, coverage)
    assert row["benchmark_coverage_ok"] is False
    # No phantom 100% active overweight against a non-existent benchmark.
    assert row["active_rolled_exposure"] is None


def test_active_preserved_when_benchmark_present_even_if_acid_benchmark_is_zero():
    # Fund HAS benchmark coverage, but this one ACID is absent from the benchmark.
    # That is a real active overweight and must be preserved (not nulled).
    detail = [
        _detail_row("Bench Fund", "acid_country", "US LRG EQ", 30.0, 25.0),
        _detail_row("Bench Fund", "acid_country", "Niche EQ", 5.0, 0.0),
    ]
    coverage = [_coverage_row("Bench Fund", total_benchmark_weight=1.0)]
    by_acid = {r["acid"]: r for r in _fund_summary_rows(detail, coverage)}
    assert by_acid["US LRG EQ"]["benchmark_coverage_ok"] is True
    assert by_acid["US LRG EQ"]["active_rolled_exposure"] == 30.0 - 25.0
    assert by_acid["Niche EQ"]["active_rolled_exposure"] == 5.0  # real bet, preserved
