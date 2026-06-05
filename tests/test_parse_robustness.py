"""H3/H4: a single bad cell must not abort the parse.

H3: non-numeric text ("NA", "#N/A") routed to a warning instead of raising.
H4: Excel error cells (t="e") in the workbook reader are treated as missing so the
error literal never reaches a numeric parse or a string field.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from portfolio_analyst_agent.parse_utils import safe_float
from portfolio_analyst_agent.workbook_xml import MAIN_NS, XlsxWorkbook


# --- H3: tolerant numeric coercion -------------------------------------------

def test_safe_float_parses_numbers_and_blanks():
    assert safe_float("3.14") == 3.14
    assert safe_float("") is None
    assert safe_float(None) is None
    assert safe_float("  42 ") == 42.0


@pytest.mark.parametrize("bad", ["NA", "#N/A", "#REF!", "n/a", "—", "TBD"])
def test_safe_float_warns_and_returns_none_on_non_numeric(bad):
    with pytest.warns(UserWarning, match="treated as missing"):
        assert safe_float(bad) is None


def test_safe_float_context_appears_in_warning():
    with pytest.warns(UserWarning, match=r"row 7 col D"):
        safe_float("oops", context="algo US LRG EQ row 7 col D")


# --- H4: workbook error cells treated as missing -----------------------------

def _cell(ref, *, t=None, v=None, f=None):
    attrib = {"r": ref}
    if t is not None:
        attrib["t"] = t
    el = ET.Element(f"{{{MAIN_NS}}}c", attrib)
    if f is not None:
        fe = ET.SubElement(el, f"{{{MAIN_NS}}}f")
        fe.text = f
    if v is not None:
        ve = ET.SubElement(el, f"{{{MAIN_NS}}}v")
        ve.text = v
    return el


def test_error_cell_returns_empty():
    wb = XlsxWorkbook.__new__(XlsxWorkbook)  # bypass __init__ (no file needed)
    wb._shared_strings = []
    # A formula cell whose cached value is an error literal.
    assert wb._cell_value(_cell("A1", t="e", v="#REF!", f="1/0")) == ""
    # A plain error cell.
    assert wb._cell_value(_cell("A2", t="e", v="#DIV/0!")) == ""


def test_normal_numeric_and_formula_cells_unaffected():
    wb = XlsxWorkbook.__new__(XlsxWorkbook)
    wb._shared_strings = []
    assert wb._cell_value(_cell("A1", v="123.5")) == "123.5"
    assert wb._cell_value(_cell("A2", v="7", f="3+4")) == "7"  # cached formula value


def test_error_cell_then_safe_float_is_missing_not_crash():
    wb = XlsxWorkbook.__new__(XlsxWorkbook)
    wb._shared_strings = []
    raw = wb._cell_value(_cell("A1", t="e", v="#VALUE!"))
    assert safe_float(raw) is None  # no warning, no crash: empty string path
