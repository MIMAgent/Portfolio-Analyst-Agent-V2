"""Build account-level and fund-level rolled ACID exposures from lookthrough data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import csv
import re
import warnings
from typing import Iterable
from zipfile import ZipFile
import xml.etree.ElementTree as ET

# Lookthrough rows whose portcode matches no account are dropped from the join.
# Above this fraction of total rows, the drop is flagged as a likely join-key
# problem rather than incidental unmatched securities (audit H1).
LOOKTHROUGH_DROP_WARN_FRACTION = 0.01

from .row_ids import (
    account_detail_row_id,
    account_summary_row_id,
    coverage_row_id,
    definition_row_id,
    fund_detail_row_id,
    fund_summary_row_id,
)
from .parse_utils import safe_float
from .workbook_xml import NS, OFFICE_REL_NS, PACKAGE_REL_NS, Worksheet


US_EQ_SECURITY_ACID_OVERRIDES: dict[str, str] = {
    "Solstice Advanced Materials Inc": "US LRG EQ",
    "Liberty Live Holdings Inc Ordinary Shares (Liberty Live Group) Series C": "US MID EQ",
    "Millrose Properties Inc Class A": "US MID EQ",
    "Liberty Live Holdings Inc Ordinary Shares (Liberty Live Group) Series A": "US MID EQ",
}

US_EQ_ACCOUNT_OVERRIDES: dict[str, str] = {
    "SPDR® S&P 600 Small Cap Value ETF": "US SML EQ",
    "SPDR Portfolio S&P 600 Sm Cap ETF": "US SML EQ",
    "MS US EQ SYSTEMATIC SMID": "US SML EQ",
}


@dataclass(frozen=True)
class FundBlock:
    fund: str
    new_column: int
    target_column: int
    benchmark_column: int | None
    benchmark_available: bool


@dataclass(frozen=True)
class AccountRow:
    account_name: str
    secid: str
    target_weights: dict[str, float]
    benchmark_weights: dict[str, float]


@dataclass(frozen=True)
class LookthroughRow:
    portcode: str
    h_path: str
    security_name: str
    common_identifier: str
    security_weight: float
    asset_class_broad: str
    acid_country: str
    acid_region_sector: str
    acid_bond: str


def build_rolled_exposures(
    workbook_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    workbook_path = Path(workbook_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot_date = _snapshot_date_from_filename(workbook_path)
    worksheets = _read_selected_worksheets(workbook_path, ["Portfolio", "Full_lookthrough"])

    portfolio_sheet = worksheets["Portfolio"]
    lookthrough_sheet = worksheets["Full_lookthrough"]

    fund_blocks = _fund_blocks(portfolio_sheet)
    accounts = _account_rows(portfolio_sheet, fund_blocks)
    lookthrough_rows = _lookthrough_rows(lookthrough_sheet)

    account_by_secid = {account.secid: account for account in accounts}

    account_detail_rows: list[dict[str, object]] = []
    dropped_count = 0
    dropped_weight = 0.0
    dropped_portcodes: set[str] = set()
    for row in lookthrough_rows:
        account = account_by_secid.get(row.portcode)
        if account is None:
            # No matching account: this lookthrough row contributes to no fund. Track
            # it instead of discarding silently, so a join-key drift can't quietly
            # zero out exposures (audit H1).
            dropped_count += 1
            dropped_weight += row.security_weight or 0.0
            dropped_portcodes.add(row.portcode)
            continue

        acid_entries: list[tuple[str, str, str]] = []
        if row.acid_country:
            acid_entries.append(
                (
                    "acid_country",
                    _normalized_country_acid(
                        account_name=account.account_name,
                        security_name=row.security_name,
                        acid=row.acid_country,
                    ),
                    "V",
                )
            )
        if row.acid_region_sector:
            acid_entries.append(("acid_region_sector", row.acid_region_sector, "W"))
        if row.acid_bond:
            acid_entries.append(("acid_bond", row.acid_bond, "X"))

        for acid_type, acid, source_column in acid_entries:
            account_detail_rows.append(
                {
                    "row_id": account_detail_row_id(
                        snapshot_date=snapshot_date.isoformat(),
                        portcode=row.portcode,
                        security_name=row.security_name,
                        acid_type=acid_type,
                        acid=acid,
                    ),
                    "snapshot_date": snapshot_date.isoformat(),
                    "ingested_at": ingested_at,
                    "source_file": workbook_path.name,
                    "source_sheet": "Full_lookthrough",
                    "portcode": row.portcode,
                    "account_name": account.account_name,
                    "acid_type": acid_type,
                    "acid": acid,
                    "acid_source_column": source_column,
                    "security_name": row.security_name,
                    "common_identifier": row.common_identifier,
                    "h_path": row.h_path,
                    "asset_class_broad": row.asset_class_broad,
                    "security_weight": row.security_weight,
                    "account_security_contribution": row.security_weight,
                }
            )

    if dropped_count:
        total_rows = len(lookthrough_rows)
        fraction = dropped_count / total_rows if total_rows else 0.0
        sample = ", ".join(sorted(dropped_portcodes)[:10])
        message = (
            f"Dropped {dropped_count}/{total_rows} lookthrough rows ({fraction:.2%}) "
            f"with no matching account across {len(dropped_portcodes)} unmatched portcode(s); "
            f"total dropped security weight {dropped_weight:.4f}. Sample portcodes: {sample}"
        )
        if fraction > LOOKTHROUGH_DROP_WARN_FRACTION:
            message = "HIGH unmatched-lookthrough rate — possible join-key drift. " + message
        warnings.warn(message, stacklevel=2)

    account_summary_rows = _account_summary_rows(
        account_detail_rows=account_detail_rows,
        accounts=accounts,
        workbook_name=workbook_path.name,
        snapshot_date=snapshot_date,
        ingested_at=ingested_at,
        fund_blocks=fund_blocks,
    )
    fund_detail_rows = _fund_detail_rows(account_detail_rows, accounts, workbook_path.name, snapshot_date, ingested_at)
    coverage_rows = _coverage_rows(accounts, lookthrough_rows, workbook_path.name, snapshot_date, ingested_at, fund_blocks)
    fund_summary_rows = _fund_summary_rows(fund_detail_rows, coverage_rows)
    fund_definition_rows = _fund_definition_rows(fund_blocks, workbook_path.name, snapshot_date, ingested_at)

    outputs = {
        "account_detail": output_dir / "account_rolled_exposure_detail.csv",
        "account_summary": output_dir / "account_rolled_exposure_summary.csv",
        "fund_detail": output_dir / "fund_rolled_exposure_detail.csv",
        "fund_summary": output_dir / "fund_rolled_exposure_summary.csv",
        "coverage": output_dir / "fund_rollthrough_coverage.csv",
        "fund_definitions": output_dir / "fund_rollthrough_definitions.csv",
    }

    _write_csv(outputs["account_detail"], account_detail_rows)
    _write_csv(outputs["account_summary"], account_summary_rows)
    _write_csv(outputs["fund_detail"], fund_detail_rows)
    _write_csv(outputs["fund_summary"], fund_summary_rows)
    _write_csv(outputs["coverage"], coverage_rows)
    _write_csv(outputs["fund_definitions"], fund_definition_rows)

    return outputs


def _account_summary_rows(
    account_detail_rows: list[dict[str, object]],
    accounts: list[AccountRow],
    workbook_name: str,
    snapshot_date: date,
    ingested_at: str,
    fund_blocks: list[FundBlock],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, object]]] = {}
    for row in account_detail_rows:
        key = (str(row["portcode"]), str(row["account_name"]), str(row["acid_type"]), str(row["acid"]))
        grouped.setdefault(key, []).append(row)

    account_lookup = {account.secid: account for account in accounts}
    rows: list[dict[str, object]] = []
    for (portcode, account_name, acid_type, acid), group_rows in sorted(grouped.items()):
        account = account_lookup[portcode]
        row: dict[str, object] = {
            "row_id": account_summary_row_id(
                snapshot_date=snapshot_date.isoformat(),
                portcode=portcode,
                acid_type=acid_type,
                acid=acid,
            ),
            "snapshot_date": snapshot_date.isoformat(),
            "ingested_at": ingested_at,
            "source_file": workbook_name,
            "portcode": portcode,
            "account_name": account_name,
            "acid_type": acid_type,
            "acid": acid,
            "account_rolled_exposure": sum(float(item["account_security_contribution"]) for item in group_rows),
            "source_security_count": len({str(item["security_name"]) for item in group_rows if str(item["security_name"]).strip()}),
            "sample_source_securities": _sample_unique(str(item["security_name"]) for item in group_rows),
        }
        for fund_block in fund_blocks:
            row[f"{fund_block.fund} target_weight"] = account.target_weights[fund_block.fund]
            row[f"{fund_block.fund} benchmark_weight"] = account.benchmark_weights[fund_block.fund]
        rows.append(row)
    return rows


def _fund_detail_rows(
    account_detail_rows: list[dict[str, object]],
    accounts: list[AccountRow],
    workbook_name: str,
    snapshot_date: date,
    ingested_at: str,
) -> list[dict[str, object]]:
    account_lookup = {account.secid: account for account in accounts}
    rows: list[dict[str, object]] = []
    for detail_row in account_detail_rows:
        account = account_lookup[str(detail_row["portcode"])]
        for fund in sorted(account.target_weights):
            account_target_weight = account.target_weights[fund]
            account_benchmark_weight = account.benchmark_weights[fund]
            if account_target_weight == 0.0 and account_benchmark_weight == 0.0:
                continue

            account_contribution = float(detail_row["account_security_contribution"])
            rows.append(
                {
                    "row_id": fund_detail_row_id(
                        snapshot_date=snapshot_date.isoformat(),
                        fund=fund,
                        account_name=str(detail_row["account_name"]),
                        security_name=str(detail_row["security_name"]),
                        acid_type=str(detail_row["acid_type"]),
                        acid=str(detail_row["acid"]),
                    ),
                    "snapshot_date": snapshot_date.isoformat(),
                    "ingested_at": ingested_at,
                    "source_file": workbook_name,
                    "fund": fund,
                    "portcode": detail_row["portcode"],
                    "account_name": detail_row["account_name"],
                    "acid_type": detail_row["acid_type"],
                    "acid": detail_row["acid"],
                    "acid_source_column": detail_row["acid_source_column"],
                    "security_name": detail_row["security_name"],
                    "common_identifier": detail_row["common_identifier"],
                    "h_path": detail_row["h_path"],
                    "asset_class_broad": detail_row["asset_class_broad"],
                    "security_weight": detail_row["security_weight"],
                    "account_security_contribution": account_contribution,
                    "account_target_weight": account_target_weight,
                    "account_benchmark_weight": account_benchmark_weight,
                    "fund_target_security_contribution": account_target_weight * account_contribution,
                    "fund_benchmark_security_contribution": account_benchmark_weight * account_contribution,
                }
            )
    rows.sort(key=lambda row: (str(row["fund"]), str(row["acid_type"]), str(row["acid"]), -float(row["fund_target_security_contribution"])))
    return rows


def _coverage_rows(
    accounts: list[AccountRow],
    lookthrough_rows: list[LookthroughRow],
    workbook_name: str,
    snapshot_date: date,
    ingested_at: str,
    fund_blocks: list[FundBlock],
) -> list[dict[str, object]]:
    matched_portcodes = {row.portcode for row in lookthrough_rows}
    rows: list[dict[str, object]] = []
    for fund_block in fund_blocks:
        total_target_weight = sum(account.target_weights[fund_block.fund] for account in accounts)
        matched_target_weight = sum(
            account.target_weights[fund_block.fund]
            for account in accounts
            if account.secid in matched_portcodes
        )
        total_benchmark_weight = sum(account.benchmark_weights[fund_block.fund] for account in accounts)
        matched_benchmark_weight = sum(
            account.benchmark_weights[fund_block.fund]
            for account in accounts
            if account.secid in matched_portcodes
        )
        rows.append(
            {
                "row_id": coverage_row_id(
                    snapshot_date=snapshot_date.isoformat(),
                    fund=fund_block.fund,
                ),
                "snapshot_date": snapshot_date.isoformat(),
                "ingested_at": ingested_at,
                "source_file": workbook_name,
                "fund": fund_block.fund,
                "total_target_weight": total_target_weight,
                "matched_target_weight": matched_target_weight,
                "target_match_pct": (matched_target_weight / total_target_weight) if total_target_weight else "",
                "total_benchmark_weight": total_benchmark_weight,
                "matched_benchmark_weight": matched_benchmark_weight,
                "benchmark_match_pct": (matched_benchmark_weight / total_benchmark_weight) if total_benchmark_weight else "",
            }
        )
    return rows


def _fund_summary_rows(
    fund_detail_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in fund_detail_rows:
        key = (str(row["fund"]), str(row["acid_type"]), str(row["acid"]))
        grouped.setdefault(key, []).append(row)

    coverage_by_fund = {str(row["fund"]): row for row in coverage_rows}
    rows: list[dict[str, object]] = []
    for (fund, acid_type, acid), group_rows in sorted(grouped.items()):
        coverage = coverage_by_fund[fund]
        # Active exposure is only meaningful against a populated benchmark. When a fund
        # has no benchmark coverage at all (e.g. an unbenchmarked alternatives sleeve),
        # `active = target - 0 = target` would report the entire position as an active
        # overweight (audit C2). Flag fund-level coverage and null active in that case,
        # rather than computing a phantom bet. Note this is deliberately fund-level: a
        # single ACID with a zero benchmark weight inside a benchmarked fund is a real
        # active bet and must be preserved.
        benchmark_coverage_ok = _coverage_value(coverage.get("total_benchmark_weight")) > 0.0
        target = sum(float(row["fund_target_security_contribution"]) for row in group_rows)
        benchmark = sum(float(row["fund_benchmark_security_contribution"]) for row in group_rows)
        rows.append(
            {
                "row_id": fund_summary_row_id(
                    snapshot_date=str(coverage["snapshot_date"]),
                    fund=fund,
                    acid_type=acid_type,
                    acid=acid,
                ),
                "snapshot_date": coverage["snapshot_date"],
                "ingested_at": coverage["ingested_at"],
                "source_file": coverage["source_file"],
                "fund": fund,
                "acid_type": acid_type,
                "acid": acid,
                "fund_target_rolled_exposure": target,
                "fund_benchmark_rolled_exposure": benchmark,
                "active_rolled_exposure": (target - benchmark) if benchmark_coverage_ok else None,
                "benchmark_coverage_ok": benchmark_coverage_ok,
                "matched_target_weight": coverage["matched_target_weight"],
                "target_match_pct": coverage["target_match_pct"],
                "matched_benchmark_weight": coverage["matched_benchmark_weight"],
                "benchmark_match_pct": coverage["benchmark_match_pct"],
                "source_security_count": len({str(item["security_name"]) for item in group_rows if str(item["security_name"]).strip()}),
                "sample_source_securities": _sample_unique(str(item["security_name"]) for item in group_rows),
            }
        )
    return rows


def _fund_definition_rows(
    fund_blocks: list[FundBlock],
    workbook_name: str,
    snapshot_date: date,
    ingested_at: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for fund_block in fund_blocks:
        rows.append(
            {
                "row_id": definition_row_id(
                    snapshot_date=snapshot_date.isoformat(),
                    fund=fund_block.fund,
                ),
                "snapshot_date": snapshot_date.isoformat(),
                "ingested_at": ingested_at,
                "source_file": workbook_name,
                "fund": fund_block.fund,
                "portfolio_new_column": _column_letter(fund_block.new_column),
                "portfolio_target_column": _column_letter(fund_block.target_column),
                "portfolio_benchmark_column": _column_letter(fund_block.benchmark_column) if fund_block.benchmark_column else "",
                "benchmark_available_in_portfolio": "Yes" if fund_block.benchmark_available else "No",
                "benchmark_assumption_if_missing": "" if fund_block.benchmark_available else "0.0",
            }
        )
    return rows


def _fund_blocks(worksheet: Worksheet) -> list[FundBlock]:
    blocks: list[FundBlock] = []
    for new_column in range(7, 58, 6):
        fund_name = worksheet.get_cell(1, new_column).strip()
        if not fund_name:
            continue

        target_column = new_column + 1
        benchmark_column = new_column + 2
        benchmark_header = worksheet.get_cell(4, benchmark_column).strip()
        benchmark_available = benchmark_header.endswith("_bmk")
        blocks.append(
            FundBlock(
                fund=fund_name,
                new_column=new_column,
                target_column=target_column,
                benchmark_column=benchmark_column if benchmark_available else None,
                benchmark_available=benchmark_available,
            )
        )
    return blocks


# The account block starts at row 5. Older workbooks were contiguous, but newer
# monthly files can include banner rows with a blank secid inside the block, so we
# scan the full populated range and keep only rows with a secid.
ACCOUNT_BLOCK_FIRST_ROW = 5
# Minimum count of parsed account rows. A materially smaller result means the layout
# changed or the parse truncated, and the IC-facing numbers cannot be trusted.
ACCOUNT_BLOCK_MIN_ROW_COUNT = 70
# Minimum row the block must REACH. The bond benchmark accounts live at rows 83-88
# (audit C3). The count guard alone does not imply reaching them -- rows 5..74 satisfy
# a count of 70 while 83-88 are silently absent -- so both guards are required.
ACCOUNT_BLOCK_MIN_LAST_ROW = 88


def _account_rows(worksheet: Worksheet, fund_blocks: list[FundBlock]) -> list[AccountRow]:
    rows: list[AccountRow] = []
    last_sheet_row = max(worksheet.rows) if worksheet.rows else ACCOUNT_BLOCK_FIRST_ROW
    observed_last_row = ACCOUNT_BLOCK_FIRST_ROW - 1
    for row_number in range(ACCOUNT_BLOCK_FIRST_ROW, last_sheet_row + 1):
        secid = worksheet.get_cell(row_number, 2).strip()
        if not secid:
            # Newer monthly workbooks can carry section-header rows with a blank secid.
            # Ignore those rows rather than treating them as the end of the account block.
            continue
        observed_last_row = row_number

        account_name = worksheet.get_cell(row_number, 1).strip() or secid
        target_weights: dict[str, float] = {}
        benchmark_weights: dict[str, float] = {}
        for fund_block in fund_blocks:
            target_weights[fund_block.fund] = _to_float(worksheet.get_cell(row_number, fund_block.target_column)) or 0.0
            benchmark_weights[fund_block.fund] = (
                (_to_float(worksheet.get_cell(row_number, fund_block.benchmark_column)) or 0.0)
                if fund_block.benchmark_column
                else 0.0
            )

        rows.append(
            AccountRow(
                account_name=account_name,
                secid=secid,
                target_weights=target_weights,
                benchmark_weights=benchmark_weights,
            )
        )

    if len(rows) < ACCOUNT_BLOCK_MIN_ROW_COUNT:
        raise ValueError(
            f"Parsed only {len(rows)} account rows (last populated row {observed_last_row}), "
            f"below the expected minimum {ACCOUNT_BLOCK_MIN_ROW_COUNT}. The Portfolio sheet "
            f"layout may have changed or the parse truncated; refusing to emit possibly-"
            f"incomplete rolled exposures."
        )
    if observed_last_row < ACCOUNT_BLOCK_MIN_LAST_ROW:
        raise ValueError(
            f"Account block ended at row {observed_last_row}, before the expected minimum "
            f"extent {ACCOUNT_BLOCK_MIN_LAST_ROW}. The bond benchmark accounts at rows 83-88 "
            f"would be missing, producing phantom 100% active bets; refusing to emit "
            f"possibly-incomplete rolled exposures."
        )
    return rows


def _lookthrough_rows(worksheet: Worksheet) -> list[LookthroughRow]:
    rows: list[LookthroughRow] = []
    for row_number in sorted(worksheet.rows):
        if row_number == 1:
            continue

        portcode = worksheet.get_cell(row_number, 2).strip()
        if not portcode:
            continue

        security_weight = _to_float(worksheet.get_cell(row_number, 9))
        if security_weight is None:
            continue

        acid_country = worksheet.get_cell(row_number, 22).strip()
        acid_region_sector = worksheet.get_cell(row_number, 23).strip()
        acid_bond = worksheet.get_cell(row_number, 24).strip()
        if not (acid_country or acid_region_sector or acid_bond):
            continue

        rows.append(
            LookthroughRow(
                portcode=portcode,
                h_path=worksheet.get_cell(row_number, 4).strip(),
                security_name=worksheet.get_cell(row_number, 5).strip(),
                common_identifier=worksheet.get_cell(row_number, 6).strip(),
                security_weight=security_weight,
                asset_class_broad=worksheet.get_cell(row_number, 10).strip(),
                acid_country=acid_country,
                acid_region_sector=acid_region_sector,
                acid_bond=acid_bond,
            )
        )
    return rows


def _normalized_country_acid(account_name: str, security_name: str, acid: str) -> str:
    if acid != "US EQ":
        return acid

    security_override = US_EQ_SECURITY_ACID_OVERRIDES.get(security_name)
    if security_override is not None:
        return security_override

    account_override = US_EQ_ACCOUNT_OVERRIDES.get(account_name)
    if account_override is not None:
        return account_override

    return acid


def _read_selected_worksheets(workbook_path: str | Path, sheet_names: list[str]) -> dict[str, Worksheet]:
    workbook_path = Path(workbook_path)
    with ZipFile(workbook_path) as workbook_zip:
        shared_strings = _parse_shared_strings(workbook_zip)
        sheet_targets = _parse_sheet_targets(workbook_zip)
        worksheets: dict[str, Worksheet] = {}
        for sheet_name in sheet_names:
            target = sheet_targets[sheet_name]
            worksheets[sheet_name] = Worksheet(
                name=sheet_name,
                rows=_parse_sheet_rows(workbook_zip, target, shared_strings),
            )
        return worksheets


def _parse_shared_strings(workbook_zip: ZipFile) -> list[str]:
    shared_strings_path = "xl/sharedStrings.xml"
    if shared_strings_path not in workbook_zip.namelist():
        return []

    root = ET.fromstring(workbook_zip.read(shared_strings_path))
    shared_strings: list[str] = []
    for string_item in root.findall("main:si", NS):
        parts = [text_node.text or "" for text_node in string_item.iterfind(".//main:t", NS)]
        shared_strings.append("".join(parts))
    return shared_strings


def _parse_sheet_targets(workbook_zip: ZipFile) -> dict[str, str]:
    workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    relationships_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))

    relationship_targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships_root.findall("pkgrel:Relationship", {"pkgrel": PACKAGE_REL_NS})
    }

    sheet_targets: dict[str, str] = {}
    sheets_root = workbook_root.find("main:sheets", NS)
    if sheets_root is None:
        return sheet_targets

    for sheet in sheets_root:
        relationship_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
        target = relationship_targets[relationship_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        sheet_targets[sheet.attrib["name"]] = target
    return sheet_targets


def _parse_sheet_rows(workbook_zip: ZipFile, target: str, shared_strings: list[str]) -> dict[int, dict[int, str]]:
    root = ET.fromstring(workbook_zip.read(target))
    parsed_rows: dict[int, dict[int, str]] = {}

    for row_element in root.findall(".//main:sheetData/main:row", NS):
        row_number = int(row_element.attrib["r"])
        row_values: dict[int, str] = {}

        for cell in row_element.findall("main:c", NS):
            reference = cell.attrib.get("r", "")
            match = re.match(r"([A-Z]+)(\d+)", reference)
            if not match:
                continue

            column_number = _column_to_number(match.group(1))
            row_values[column_number] = _cell_value(cell, shared_strings)

        if row_values:
            parsed_rows[row_number] = row_values

    return parsed_rows


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    formula = cell.find("main:f", NS)
    value_node = cell.find("main:v", NS)
    inline_string = cell.find("main:is", NS)

    if formula is not None and value_node is not None and value_node.text is not None:
        return value_node.text

    if cell_type == "s" and value_node is not None and value_node.text is not None:
        index = int(value_node.text)
        return shared_strings[index] if index < len(shared_strings) else value_node.text

    if cell_type == "inlineStr" and inline_string is not None:
        parts = [text_node.text or "" for text_node in inline_string.iterfind(".//main:t", NS)]
        return "".join(parts)

    if value_node is not None and value_node.text is not None:
        return value_node.text

    return ""


def _column_to_number(column_name: str) -> int:
    value = 0
    for character in column_name:
        if character.isalpha():
            value = value * 26 + (ord(character.upper()) - 64)
    return value


def _column_letter(column_number: int | None) -> str:
    if column_number is None:
        return ""
    characters: list[str] = []
    current = column_number
    while current:
        current, remainder = divmod(current - 1, 26)
        characters.append(chr(65 + remainder))
    return "".join(reversed(characters))


def _snapshot_date_from_filename(path: Path) -> date:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    if not match:
        raise ValueError(f"Could not parse snapshot date from {path.name!r}.")
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _sample_unique(values: Iterable[str], limit: int = 25) -> str:
    seen: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.append(cleaned)
        if len(seen) >= limit:
            break
    return "; ".join(seen)


def _to_float(raw_value: str) -> float | None:
    return safe_float(raw_value)


def _coverage_value(raw_value: object) -> float:
    """Best-effort float for a coverage weight that may be float, "", or None."""
    if raw_value is None or raw_value == "":
        return 0.0
    return float(raw_value)


__all__ = [
    "build_rolled_exposures",
]
