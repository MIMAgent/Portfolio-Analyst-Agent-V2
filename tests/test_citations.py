"""Citation resolver and enforcement tests."""

from __future__ import annotations

import csv
import json
from zipfile import ZipFile

import pytest

from portfolio_analyst_agent.citations import CitationError, enforce_payload_citations, extract_tokens, resolve_token
from portfolio_analyst_agent.evidence import stable_row_id


def _csv_with_row(path, row_id="row_1"):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "value"])
        writer.writeheader()
        writer.writerow({"row_id": row_id, "value": "42"})


def test_resolves_csv_and_derivation_tokens(tmp_path):
    csv_path = tmp_path / "rows.csv"
    _csv_with_row(csv_path)
    token = f"csv:{csv_path.as_posix()}#row_id=row_1"

    assert resolve_token(token)
    assert resolve_token(f"deriv:active_weight_check?inputs={token}")


def test_resolves_trigger_tokens():
    assert resolve_token("trigger:evaluate_challenge_triggers_v1#trig_abc123")


def test_resolves_memory_token(tmp_path):
    memory_path = tmp_path / "memory_records.json"
    memory_path.write_text(
        json.dumps(
            {
                "tables": {
                    "thesis_ledger": [{"thesis_id": "ths_1"}],
                    "open_challenges": [],
                    "exceptions": [],
                    "watch_items": [],
                }
            }
        ),
        encoding="utf-8",
    )

    assert resolve_token("mem:thesis_ledger#ths_1", memory_path=memory_path)


def test_enforce_payload_rejects_uncited_narrative(tmp_path):
    csv_path = tmp_path / "rows.csv"
    _csv_with_row(csv_path)
    payload = {
        "executive_summary": "This claim has no citation.",
        "material_movers": [
            {
                "narrative": f"This one is cited csv:{csv_path.as_posix()}#row_id=row_1",
            }
        ],
    }

    with pytest.raises(CitationError, match="missing citation"):
        enforce_payload_citations(payload)


def test_enforce_payload_accepts_resolvable_narrative(tmp_path):
    csv_path = tmp_path / "rows.csv"
    _csv_with_row(csv_path)
    token = f"csv:{csv_path.as_posix()}#row_id=row_1"
    payload = {
        "executive_summary": f"This claim is cited {token}",
        "material_movers": [{"narrative": f"This one is cited too {token}"}],
    }

    enforce_payload_citations(payload)


def test_extract_tokens_strips_trailing_sentence_punctuation(tmp_path):
    csv_path = tmp_path / "rows.csv"
    _csv_with_row(csv_path, row_id="row_abc")
    token = f"csv:{csv_path.as_posix()}#row_id=row_abc"

    assert extract_tokens(f"Claim {token};") == [token]
    assert resolve_token(f"{token};")


def test_resolves_explicit_zip_csv_token(tmp_path):
    csv_path = tmp_path / "rows.csv"
    zip_path = tmp_path / "rows.csv.zip"
    csv_payload = "row_id,value\nrow_zip,42\n"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr(csv_path.name, csv_payload)

    assert resolve_token(f"csv:{zip_path.as_posix()}#row_id=row_zip")


def test_resolves_generated_stable_row_id_for_csv_without_row_id(tmp_path):
    csv_path = tmp_path / "history.csv"
    row = {"acid": "US LRG EQ", "snapshot_date": "2026-04-06", "vir_stf": "-0.04"}
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    generated_id = stable_row_id(row, namespace=csv_path.as_posix())

    assert resolve_token(f"csv:{csv_path.as_posix()}#row_id={generated_id}")
