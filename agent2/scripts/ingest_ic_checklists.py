"""CLI for ingesting old mutual fund checklist DOCX files into agent2 internal-history records."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "agent2" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent2.ic_checklist_ingest import ingest_many_checklists, write_ingestion_outputs  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest mutual fund checklist DOCX files into agent2 internal-history records.")
    parser.add_argument("--input", action="append", required=True, help="Path to a DOCX checklist file. Repeat for multiple files.")
    parser.add_argument("--output-json", required=True, help="Combined JSON output path.")
    parser.add_argument("--output-jsonl", required=True, help="Per-document JSONL output path.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = ingest_many_checklists(args.input)
    write_ingestion_outputs(payload, output_json=args.output_json, output_jsonl=args.output_jsonl)
    print(f"document_count={payload['document_count']}")
    print(f"output_json={Path(args.output_json).as_posix()}")
    print(f"output_jsonl={Path(args.output_jsonl).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
