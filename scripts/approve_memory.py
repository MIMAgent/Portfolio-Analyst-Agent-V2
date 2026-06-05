"""List or approve proposed Portfolio Analyst Agent memory records."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.memory_approval import approve_memory_record, list_proposed_memory  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and approve proposed agent memory records.")
    parser.add_argument("--memory-path", default="artifacts/agent_memory/memory_records.json")
    parser.add_argument("--table", choices=["thesis_ledger", "open_challenges", "exceptions", "watch_items"])
    parser.add_argument("--record-id", help="Record ID to approve.")
    parser.add_argument("--approved-by", help="Name or email of the human approver.")
    parser.add_argument("--note", default="", help="Optional approval note.")
    parser.add_argument("--list", action="store_true", help="List latest proposed records.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list or not args.record_id:
        rows = list_proposed_memory(memory_path=args.memory_path, table=args.table)
        if not rows:
            print("No proposed memory records found.")
            return 0
        for row in rows:
            print(
                f"{row['table']}\t{row['record_id']}\t{row.get('fund', '')}\t"
                f"{row.get('acid', '')}\t{row.get('status', '')}\t{row.get('source_op_type', '')}"
            )
        return 0

    if not args.table:
        raise SystemExit("--table is required when approving a record.")
    if not args.approved_by:
        raise SystemExit("--approved-by is required when approving a record.")
    result = approve_memory_record(
        table=args.table,
        record_id=args.record_id,
        approved_by=args.approved_by,
        memory_path=args.memory_path,
        note=args.note,
    )
    print(f"approved {result['table']} {result['record_id']} by {result['approved_by']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
