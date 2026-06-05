"""Minimal XLSX reader built on the Python standard library.

This keeps the initial parser scaffold dependency-light so we can validate
against real workbook inputs without requiring openpyxl or pandas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {
    "main": MAIN_NS,
    "pkgrel": PACKAGE_REL_NS,
}


def _column_to_number(column_name: str) -> int:
    value = 0
    for character in column_name:
        if character.isalpha():
            value = value * 26 + (ord(character.upper()) - 64)
    return value


def _number_to_column(column_number: int) -> str:
    if column_number < 1:
        raise ValueError(f"Excel columns are 1-based, got {column_number}")

    characters: list[str] = []
    current = column_number
    while current:
        current, remainder = divmod(current - 1, 26)
        characters.append(chr(65 + remainder))
    return "".join(reversed(characters))


@dataclass(frozen=True)
class Worksheet:
    """In-memory representation of a parsed worksheet."""

    name: str
    rows: dict[int, dict[int, str]]

    def get_cell(self, row_number: int, column_number: int) -> str:
        return self.rows.get(row_number, {}).get(column_number, "")

    def row(self, row_number: int) -> dict[int, str]:
        return dict(self.rows.get(row_number, {}))

    def nonempty_cells(self, row_number: int, start_column: int = 1) -> list[tuple[int, str]]:
        row = self.rows.get(row_number, {})
        return [
            (column_number, value)
            for column_number, value in sorted(row.items())
            if column_number >= start_column and value != ""
        ]


class XlsxWorkbook:
    """Read workbook sheets and cells from a `.xlsx` archive."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._shared_strings: list[str] = []
        self._sheet_targets: dict[str, str] = {}
        self._worksheets: dict[str, Worksheet] = {}
        self._load()

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheet_targets.keys())

    def worksheet(self, sheet_name: str) -> Worksheet:
        try:
            return self._worksheets[sheet_name]
        except KeyError as exc:
            raise KeyError(f"Worksheet {sheet_name!r} not found in {self.path.name}") from exc

    def _load(self) -> None:
        with ZipFile(self.path) as workbook_zip:
            self._shared_strings = self._parse_shared_strings(workbook_zip)
            self._sheet_targets = self._parse_sheet_targets(workbook_zip)
            self._worksheets = {
                sheet_name: Worksheet(
                    name=sheet_name,
                    rows=self._parse_sheet_rows(workbook_zip, target),
                )
                for sheet_name, target in self._sheet_targets.items()
            }

    def _parse_shared_strings(self, workbook_zip: ZipFile) -> list[str]:
        shared_strings_path = "xl/sharedStrings.xml"
        if shared_strings_path not in workbook_zip.namelist():
            return []

        root = ET.fromstring(workbook_zip.read(shared_strings_path))
        shared_strings: list[str] = []
        for string_item in root.findall("main:si", NS):
            parts = [text_node.text or "" for text_node in string_item.iterfind(".//main:t", NS)]
            shared_strings.append("".join(parts))
        return shared_strings

    def _parse_sheet_targets(self, workbook_zip: ZipFile) -> dict[str, str]:
        workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        relationships_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))

        relationship_targets = {
            relationship.attrib["Id"]: relationship.attrib["Target"]
            for relationship in relationships_root.findall("pkgrel:Relationship", NS)
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

    def _parse_sheet_rows(self, workbook_zip: ZipFile, target: str) -> dict[int, dict[int, str]]:
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
                row_values[column_number] = self._cell_value(cell)

            if row_values:
                parsed_rows[row_number] = row_values

        return parsed_rows

    def _cell_value(self, cell: ET.Element) -> str:
        cell_type = cell.attrib.get("t")
        formula = cell.find("main:f", NS)
        value_node = cell.find("main:v", NS)
        inline_string = cell.find("main:is", NS)

        # Error cells (t="e": #REF!, #DIV/0!, #N/A, #VALUE!, ...) carry an error
        # literal in their cached <v>. Treat them as missing rather than leaking the
        # literal into a numeric parse (crash) or a string field (audit H4).
        if cell_type == "e":
            return ""

        if formula is not None and value_node is not None and value_node.text is not None:
            return value_node.text

        if cell_type == "s" and value_node is not None and value_node.text is not None:
            index = int(value_node.text)
            return self._shared_strings[index] if index < len(self._shared_strings) else value_node.text

        if cell_type == "inlineStr" and inline_string is not None:
            parts = [text_node.text or "" for text_node in inline_string.iterfind(".//main:t", NS)]
            return "".join(parts)

        if value_node is not None and value_node.text is not None:
            return value_node.text

        return ""


__all__ = [
    "Worksheet",
    "XlsxWorkbook",
    "_number_to_column",
]
