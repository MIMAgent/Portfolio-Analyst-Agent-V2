from __future__ import annotations

from datetime import date
from pathlib import Path

from portfolio_analyst_agent.equity_history import (
    EquityHistoryParseResult,
    EquityHistoryRecord,
    build_equity_vir_dataset,
    discover_equity_model_workbooks,
    load_equity_history_records_from_csv,
    write_equity_history_csv,
)


def _record(snapshot_date: date, *, acid: str = "US IT EQ", stf: float = 0.1) -> EquityHistoryRecord:
    return EquityHistoryRecord(
        snapshot_date=snapshot_date,
        ingested_at="2026-06-15T00:00:00Z",
        parser_version="equity_history_v1",
        workbook_type="equity_model",
        acid=acid,
        asset_class_name="United States Information Technology Equity",
        local_real_vir=stf + 0.05,
        local_nominal_vir=stf + 0.06,
        usd_hedged_vir=None,
        unconditional_vir=0.05,
        stf=stf,
        price_to_fair_value=1.0,
        inflation=0.02,
        currency_usd=0.01,
        yield_=0.03,
        growth=0.04,
        valuation_adjustment_top_down=-0.02,
        valuation_adjustment_combined=-0.01,
        valuation_adjustment_bottom_up=0.0,
        prior_stf=None,
        delta_stf=None,
        delta_local_real_vir=None,
        delta_local_nominal_vir=None,
        delta_usd_hedged_vir=None,
        delta_unconditional_vir=None,
        delta_price_to_fair_value=None,
        prior_rank_in_category_by_stf=None,
        rank_in_category_by_stf=1,
        rank_change_by_stf=None,
        raw_row="{}",
        raw_headers="{}",
    )


def test_discover_equity_model_workbooks_returns_sorted_matches(tmp_path: Path):
    (tmp_path / "2026-04-30").mkdir()
    (tmp_path / "2026-05-31").mkdir()
    april = tmp_path / "2026-04-30" / "202604-Equity Model.xlsx"
    may = tmp_path / "2026-05-31" / "202605-Equity Model.xlsx"
    april.write_text("", encoding="utf-8")
    may.write_text("", encoding="utf-8")

    discovered = discover_equity_model_workbooks(tmp_path)

    assert discovered == [april.resolve(), may.resolve()]


def test_build_equity_vir_dataset_merges_base_existing_and_new_workbook(tmp_path: Path, monkeypatch):
    base_csv = tmp_path / "equity_vir_history.csv"
    output_csv = tmp_path / "vir" / "equity_vir_dataset.csv"
    monthly_workbook = tmp_path / "2026-04-30" / "202604-Equity Model.xlsx"
    monthly_workbook.parent.mkdir(parents=True)
    monthly_workbook.write_text("", encoding="utf-8")

    write_equity_history_csv([_record(date(2026, 2, 28), stf=0.11)], base_csv)
    write_equity_history_csv([_record(date(2026, 3, 31), stf=0.22)], output_csv)

    def fake_parse(workbook_path: str | Path) -> EquityHistoryParseResult:
        assert Path(workbook_path) == monthly_workbook.resolve()
        return EquityHistoryParseResult(
            workbook_path=Path(workbook_path),
            row_count=1,
            snapshot_dates=[date(2026, 4, 30)],
            records=[_record(date(2026, 4, 30), stf=0.33)],
        )

    monkeypatch.setattr(
        "portfolio_analyst_agent.equity_history.parse_equity_history_workbook",
        fake_parse,
    )

    built_path, records = build_equity_vir_dataset(
        base_history_csv=base_csv,
        monthly_workbooks=[monthly_workbook],
        output_csv=output_csv,
        include_existing_output=True,
    )

    reloaded = load_equity_history_records_from_csv(built_path)
    snapshot_dates = [record.snapshot_date for record in reloaded]

    assert built_path == output_csv
    assert output_csv.with_name("equity_vir_dataset.csv.zip").exists()
    assert snapshot_dates == [date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]
    assert records[-1].snapshot_date == date(2026, 4, 30)
    assert reloaded[-1].stf == 0.33
