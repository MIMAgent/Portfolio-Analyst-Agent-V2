"""Approved market-context source registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_APPROVED_SOURCES_PATH = Path("config/approved_market_context_sources.json")


def load_approved_market_context_sources(
    path: str | Path = DEFAULT_APPROVED_SOURCES_PATH,
) -> dict[str, Any]:
    """Load and lightly validate approved market-context sources."""

    source_path = Path(path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "approved_market_context_sources_v1":
        raise ValueError("Unsupported approved market-context source schema.")
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("approved market-context sources must be a list.")
    for index, source in enumerate(sources):
        _validate_source(source, index=index)
    return payload


def approved_source_domains(path: str | Path = DEFAULT_APPROVED_SOURCES_PATH) -> set[str]:
    payload = load_approved_market_context_sources(path)
    return {source["domain"] for source in payload["sources"]}


def _validate_source(source: Any, *, index: int) -> None:
    if not isinstance(source, dict):
        raise ValueError(f"source[{index}] must be an object.")
    required = ("source_id", "source_name", "publisher", "domain", "url", "approved_use")
    for field in required:
        if source.get(field) in (None, "", []):
            raise ValueError(f"source[{index}] missing required field: {field}")
    parsed = urlparse(str(source["url"]))
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"source[{index}] url must be an https URL.")
    if source["domain"] not in parsed.netloc:
        raise ValueError(f"source[{index}] domain must match url host.")
    if not isinstance(source.get("approved_use"), list):
        raise ValueError(f"source[{index}] approved_use must be a list.")


__all__ = ["DEFAULT_APPROVED_SOURCES_PATH", "approved_source_domains", "load_approved_market_context_sources"]
