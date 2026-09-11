"""Redact local filesystem paths before they reach shipped artifacts.

The research index carries absolute paths (needed to open the source files),
but those paths embed an employee profile directory and the internal research
folder taxonomy. Anything written to a packet/evidence JSON is bundled into the
browser build, so absolute paths must be reduced at the write boundary.

Relative repo paths (``artifacts/...``) are deliberately preserved -- they are
auditable references, not leaks.
"""

from __future__ import annotations

import re
from typing import Any

_BSLASH = chr(92)
# absolute path with either separator, or a UNC share
_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[" + re.escape(_BSLASH) + r"/]|^" + re.escape(_BSLASH * 2))
RESEARCH_ROOT_PLACEHOLDER = "sharepoint://MIM Global Research"


def redact_path(value: str) -> str:
    """Reduce an absolute path to its basename; opaque placeholder for directories."""
    normalized = value.replace(_BSLASH, "/").rstrip("/")
    segments = normalized.split("/")
    last = segments[-1] if segments else value
    # a directory root carries the folder taxonomy and no filename -- do not leak it
    if "." not in last:
        return RESEARCH_ROOT_PLACEHOLDER
    return last


def redact_paths(payload: Any) -> Any:
    """Recursively redact absolute filesystem paths in-place. Returns the payload."""
    if isinstance(payload, dict):
        for key, value in list(payload.items()):
            if isinstance(value, str) and _ABSOLUTE_PATH.search(value):
                payload[key] = redact_path(value)
            else:
                redact_paths(value)
    elif isinstance(payload, list):
        for item in payload:
            redact_paths(item)
    return payload
