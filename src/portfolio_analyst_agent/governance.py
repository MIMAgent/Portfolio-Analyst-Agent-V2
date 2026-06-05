"""Versioned governance parameter loading for the agent harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

from .evidence import file_sha256


DEFAULT_GOVERNANCE_PATH = Path("config/agent_governance.json")


@dataclass(frozen=True)
class GovernanceConfig:
    governance_version: str
    effective_from: date
    parameters: dict[str, Any]
    source_path: Path
    source_file_hash: str | None

    def float_param(self, name: str) -> float:
        value = self.parameters.get(name)
        if value is None:
            raise KeyError(f"Missing governance parameter: {name}")
        return float(value)

    def int_param(self, name: str) -> int:
        value = self.parameters.get(name)
        if value is None:
            raise KeyError(f"Missing governance parameter: {name}")
        return int(value)

    def bool_param(self, name: str) -> bool:
        value = self.parameters.get(name)
        if value is None:
            raise KeyError(f"Missing governance parameter: {name}")
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y"}

    def source_hashes(self) -> dict[str, str]:
        if self.source_file_hash is None:
            return {}
        return {self.source_path.as_posix(): self.source_file_hash}


def load_governance(
    as_of_date: str | date,
    governance_path: str | Path = DEFAULT_GOVERNANCE_PATH,
) -> GovernanceConfig:
    """Return the governance event effective on `as_of_date`."""

    as_of = _require_date(as_of_date)
    path = Path(governance_path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    events = payload.get("events", [])
    if not isinstance(events, list) or not events:
        raise ValueError("Governance config must contain at least one event.")

    eligible = []
    for event in events:
        effective_from = _require_date(event.get("effective_from"))
        if effective_from <= as_of:
            eligible.append((effective_from, event))
    if not eligible:
        raise ValueError(f"No governance event is effective on or before {as_of.isoformat()}.")

    effective_from, selected = max(eligible, key=lambda item: item[0])
    parameters = selected.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("Governance event parameters must be an object.")

    return GovernanceConfig(
        governance_version=str(selected.get("governance_version", "")),
        effective_from=effective_from,
        parameters=parameters,
        source_path=path,
        source_file_hash=file_sha256(path) if path.exists() else None,
    )


def _require_date(raw_value: str | date | None) -> date:
    if raw_value is None:
        raise ValueError("Date is required.")
    if isinstance(raw_value, date):
        return raw_value
    return date.fromisoformat(str(raw_value))


__all__ = ["DEFAULT_GOVERNANCE_PATH", "GovernanceConfig", "load_governance"]
