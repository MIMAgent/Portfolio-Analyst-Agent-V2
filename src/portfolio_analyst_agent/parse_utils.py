"""Shared tolerant parsing helpers for the workbook boundary.

A single non-numeric cell ("NA", "#N/A", stray text, an Excel error literal that
slipped through) must not abort an entire monthly parse. These helpers coerce raw
cell values and route anything unparseable to a warning instead of raising (audit
H3), so the run completes and the bad input is surfaced rather than silently lost.
"""

from __future__ import annotations

import warnings


def safe_float(raw_value: object, *, context: str = "") -> float | None:
    """Coerce a raw cell value to float; blanks and non-numerics become None.

    `context` should identify where the value came from (file/sheet/row/col) so a
    warning points the operator at the offending cell.
    """
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        where = f" ({context})" if context else ""
        warnings.warn(f"Non-numeric value {text!r} treated as missing{where}.", stacklevel=2)
        return None


__all__ = ["safe_float"]
