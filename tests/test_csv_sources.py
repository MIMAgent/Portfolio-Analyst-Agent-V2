"""Regression coverage for large CSV artifacts tracked as ZIP mirrors."""

from __future__ import annotations

from zipfile import ZipFile

from portfolio_analyst_agent.alignment import load_vir_rows_from_csv
from portfolio_analyst_agent.csv_sources import resolve_existing_csv_source


def test_load_vir_rows_uses_zip_mirror_when_raw_csv_missing(tmp_path):
    csv_path = tmp_path / "equity_vir_history.csv"
    zip_path = tmp_path / "equity_vir_history.csv.zip"
    csv_payload = "\n".join(
        [
            "snapshot_date,acid,workbook_type,stf,delta_stf,rank_in_category_by_stf,rank_change_by_stf",
            "2026-04-30,US LRG EQ,equity_model,1.25,0.10,2,1",
        ]
    )

    with ZipFile(zip_path, "w") as archive:
        archive.writestr(csv_path.name, csv_payload)

    assert resolve_existing_csv_source(csv_path) == zip_path

    rows = load_vir_rows_from_csv(csv_path)

    assert len(rows) == 1
    assert rows[0].acid == "US LRG EQ"
    assert rows[0].stf == 1.25
