"""Stable hybrid row IDs for generated analyst artifacts."""

from __future__ import annotations

import hashlib
from typing import Mapping


def generic_row_id(row: Mapping[str, object], namespace: str = "", prefix: str = "row") -> str:
    parts = [namespace]
    for key, value in sorted(row.items(), key=lambda item: str(item[0])):
        if key == "row_id":
            continue
        parts.append(str(key))
        parts.append(_normalize(value))
    return _hybrid_id(prefix, *parts)


def account_detail_row_id(
    *,
    snapshot_date: object,
    portcode: object,
    security_name: object,
    acid_type: object,
    acid: object,
) -> str:
    return _hybrid_id(
        "adet",
        snapshot_date,
        portcode,
        security_name,
        acid_type,
        acid,
    )


def account_summary_row_id(
    *,
    snapshot_date: object,
    portcode: object,
    acid_type: object,
    acid: object,
) -> str:
    return _hybrid_id(
        "asum",
        snapshot_date,
        portcode,
        acid_type,
        acid,
    )


def fund_detail_row_id(
    *,
    snapshot_date: object,
    fund: object,
    account_name: object,
    security_name: object,
    acid_type: object,
    acid: object,
) -> str:
    return _hybrid_id(
        "fdet",
        snapshot_date,
        fund,
        account_name,
        security_name,
        acid_type,
        acid,
    )


def fund_summary_row_id(
    *,
    snapshot_date: object,
    fund: object,
    acid_type: object,
    acid: object,
) -> str:
    return _hybrid_id(
        "fsum",
        snapshot_date,
        fund,
        acid_type,
        acid,
    )


def fund_multisignal_row_id(
    *,
    snapshot_date: object,
    fund: object,
    acid_type: object,
    acid: object,
    algo_perspective: object,
) -> str:
    return _hybrid_id(
        "fms",
        snapshot_date,
        fund,
        acid_type,
        acid,
        algo_perspective,
    )


def account_alignment_row_id(
    *,
    snapshot_date: object,
    portcode: object,
    acid_type: object,
    acid: object,
    algo_perspective: object = "",
) -> str:
    return _hybrid_id(
        "aalg",
        snapshot_date,
        portcode,
        acid_type,
        acid,
        algo_perspective,
    )


def fund_alignment_row_id(
    *,
    snapshot_date: object,
    fund: object,
    acid_type: object,
    acid: object,
    algo_perspective: object = "",
) -> str:
    prefix = "fms" if _normalize(algo_perspective) else "falg"
    return _hybrid_id(
        prefix,
        snapshot_date,
        fund,
        acid_type,
        acid,
        algo_perspective,
    )


def coverage_row_id(
    *,
    snapshot_date: object,
    fund: object,
) -> str:
    return _hybrid_id("fcov", snapshot_date, fund)


def definition_row_id(
    *,
    snapshot_date: object,
    fund: object,
) -> str:
    return _hybrid_id("fdef", snapshot_date, fund)


def fund_review_row_id(
    *,
    snapshot_date: object,
    fund: object,
) -> str:
    return _hybrid_id("frvw", snapshot_date, fund)


def trigger_candidate_id(
    *,
    snapshot_date: object,
    fund: object,
    acid: object,
    trigger_type: object,
) -> str:
    return _hybrid_id("trig", snapshot_date, fund, acid, trigger_type)


def _hybrid_id(prefix: str, *parts: object) -> str:
    canonical = "|".join(_normalize(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _normalize(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return str(value.isoformat())  # type: ignore[no-any-return]
    return str(value).strip()


__all__ = [
    "account_alignment_row_id",
    "account_detail_row_id",
    "account_summary_row_id",
    "coverage_row_id",
    "definition_row_id",
    "fund_alignment_row_id",
    "fund_detail_row_id",
    "fund_multisignal_row_id",
    "fund_review_row_id",
    "fund_summary_row_id",
    "generic_row_id",
    "trigger_candidate_id",
]
