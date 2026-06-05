"""Market context ingestion tests."""

from __future__ import annotations

import csv

import pytest

from portfolio_analyst_agent.agent_tools import get_market_context
from portfolio_analyst_agent.market_context_ingest import IngestDefaults, ingest_market_context_documents


def test_ingests_front_matter_note_and_retrieves_by_acid(tmp_path):
    source_dir = tmp_path / "source_docs"
    source_dir.mkdir()
    note = source_dir / "industrials.md"
    note.write_text(
        """---
snapshot_date: 2026-04-06
as_of_date: 2026-04-06
scope_type: acid
scope_value: US ID EQ
priority: 1
headline: Industrials cyclical support weakened
source_label: Approved monthly note
source_date: 2026-04-05
fundamental_readthrough: This matters because the fund is overweight Industrials while signals are negative.
pm_question: Is the overweight idiosyncratic or cyclical?
---

Industrials entered the review with weaker cyclical support.
""",
        encoding="utf-8",
    )
    output_csv = tmp_path / "monthly_market_context.csv"

    result = ingest_market_context_documents(
        input_dir=source_dir,
        output_csv=output_csv,
        defaults=IngestDefaults(snapshot_date="2026-04-06", as_of_date="2026-04-06"),
    )
    context = get_market_context(
        snapshot_date="2026-04-06",
        as_of_date="2026-04-06",
        acid="US ID EQ",
        market_context_csv=output_csv,
    )

    assert result["row_count"] == 1
    assert context["context_status"] == "matched_context_rows"
    assert context["rows"][0]["headline"] == "Industrials cyclical support weakened"
    assert context["rows"][0]["citation_ref"].startswith(f"csv:{output_csv.as_posix()}#row_id=mctx_")


def test_ingest_rejects_future_source_date(tmp_path):
    source_dir = tmp_path / "source_docs"
    source_dir.mkdir()
    (source_dir / "future.md").write_text(
        """---
source_date: 2026-04-07
---

Future information.
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source_date may not be after as_of_date"):
        ingest_market_context_documents(
            input_dir=source_dir,
            output_csv=tmp_path / "monthly_market_context.csv",
            defaults=IngestDefaults(snapshot_date="2026-04-06", as_of_date="2026-04-06"),
        )


def test_ingest_uses_cli_defaults_for_plain_text_note(tmp_path):
    source_dir = tmp_path / "source_docs"
    source_dir.mkdir()
    (source_dir / "macro.txt").write_text("Rate-cut pricing moved lower into the review.", encoding="utf-8")
    output_csv = tmp_path / "monthly_market_context.csv"

    ingest_market_context_documents(
        input_dir=source_dir,
        output_csv=output_csv,
        defaults=IngestDefaults(
            snapshot_date="2026-04-06",
            as_of_date="2026-04-06",
            source_label="Desk note",
            source_date="2026-04-05",
            scope_type="macro",
            priority="2",
        ),
    )

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["scope_type"] == "macro"
    assert rows[0]["source_label"] == "Desk note"
    assert rows[0]["narrative"] == "Rate-cut pricing moved lower into the review."
