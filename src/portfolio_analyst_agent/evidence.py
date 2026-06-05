"""Evidence helpers for stable row IDs and source-file hashes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from .row_ids import generic_row_id


def stable_row_id(row: Mapping[str, object], namespace: str = "") -> str:
    """Return a deterministic fallback ID for non-core structured rows."""

    return generic_row_id(row, namespace=namespace, prefix="row")


def file_sha256(path: str | Path) -> str:
    """Hash a file without loading the whole thing into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["file_sha256", "stable_row_id"]
