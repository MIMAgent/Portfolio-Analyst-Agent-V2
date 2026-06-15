"""Validated write tools for Model 1 monthly review artifacts."""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from .citations import enforce_payload_citations
from .memory_ops import apply_ops
from .pm_review_renderer import render_pm_review_html, render_pm_review_markdown
from .schemas import (
    reject_prescriptive_sizing_language,
    validate_challenge_brief,
    validate_change_brief,
    validate_sizing_considerations,
)


DEFAULT_MONTHLY_REVIEW_ROOT = Path("artifacts/monthly_review")
PM_CHALLENGE_MARKDOWN_FIELDS = (
    ("challenge_headline", "Headline"),
    ("thesis_under_pressure", "Thesis Under Pressure"),
    ("positioning_tension", "Positioning Tension"),
    ("model_signal_tension", "Model Signal Tension"),
    ("vir_decomposition_readthrough", "VIR Decomposition Readthrough"),
    ("market_context_readthrough", "Market Context Readthrough"),
    ("pm_decision_fork", "PM Decision Fork"),
    ("primary_pm_question", "Primary PM Question"),
    ("evidence_needed_next", "Evidence Needed Next"),
    ("source_quality", "Source Quality"),
)


def write_change_brief(
    fund: str,
    content: dict[str, Any],
    *,
    output_root: str | Path = DEFAULT_MONTHLY_REVIEW_ROOT,
    memory_path: str | Path = "artifacts/agent_memory/memory_records.json",
) -> dict[str, str]:
    validate_change_brief(content, fund=fund)
    enforce_payload_citations(content, memory_path=memory_path)
    result = _persist_artifact(
        fund=fund,
        content=content,
        output_root=output_root,
        json_name="change_brief.json",
        markdown_name="change_brief.md",
        title="Change Brief",
    )
    result.update(_persist_pm_review(fund=fund, content=content, output_root=output_root))
    return result


def write_sizing_considerations(
    fund: str,
    content: dict[str, Any],
    *,
    output_root: str | Path = DEFAULT_MONTHLY_REVIEW_ROOT,
    memory_path: str | Path = "artifacts/agent_memory/memory_records.json",
) -> dict[str, str]:
    validate_sizing_considerations(content, fund=fund)
    reject_prescriptive_sizing_language(content)
    enforce_payload_citations(content, memory_path=memory_path)
    return _persist_artifact(
        fund=fund,
        content=content,
        output_root=output_root,
        json_name="sizing_considerations.json",
        markdown_name="sizing_considerations.md",
        title="Sizing Considerations",
    )


def write_challenge_brief(
    fund: str,
    content: dict[str, Any],
    *,
    fired_trigger_ids: set[str] | None = None,
    fired_trigger_types: dict[str, str] | None = None,
    output_root: str | Path = DEFAULT_MONTHLY_REVIEW_ROOT,
    memory_path: str | Path = "artifacts/agent_memory/memory_records.json",
) -> dict[str, str]:
    validate_challenge_brief(content, fund=fund, fired_trigger_ids=fired_trigger_ids, fired_trigger_types=fired_trigger_types)
    enforce_payload_citations(content, memory_path=memory_path)
    return _persist_artifact(
        fund=fund,
        content=content,
        output_root=output_root,
        json_name="challenge_brief.json",
        markdown_name="challenge_brief.md",
        title="Challenge Brief",
    )


def update_memory(
    fund: str,
    ops: list[dict[str, Any]],
    *,
    run_metadata: dict[str, Any],
    memory_path: str | Path = "artifacts/agent_memory/memory_records.json",
    governance_path: str | Path = "config/agent_governance.json",
) -> list[dict[str, Any]]:
    return apply_ops(
        fund=fund,
        ops=ops,
        run_metadata=run_metadata,
        memory_path=memory_path,
        governance_path=governance_path,
    )


def _persist_artifact(
    *,
    fund: str,
    content: dict[str, Any],
    output_root: str | Path,
    json_name: str,
    markdown_name: str,
    title: str,
) -> dict[str, str]:
    header = content["header"]
    review_dir = Path(output_root) / header["snapshot_date"] / _slugify(fund)
    review_dir.mkdir(parents=True, exist_ok=True)
    json_path = review_dir / json_name
    markdown_path = review_dir / markdown_name
    json_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(title=title, content=content), encoding="utf-8")
    return {
        "json_path": json_path.as_posix(),
        "markdown_path": markdown_path.as_posix(),
    }


def _persist_pm_review(
    *,
    fund: str,
    content: dict[str, Any],
    output_root: str | Path,
) -> dict[str, str]:
    header = content["header"]
    review_dir = Path(output_root) / header["snapshot_date"] / _slugify(fund)
    review_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = review_dir / "pm_review.md"
    html_path = review_dir / "pm_review.html"
    markdown_path.write_text(render_pm_review_markdown(content), encoding="utf-8")
    html_path.write_text(render_pm_review_html(content), encoding="utf-8")
    return {
        "pm_review_markdown_path": markdown_path.as_posix(),
        "pm_review_html_path": html_path.as_posix(),
    }


def _render_markdown(*, title: str, content: dict[str, Any]) -> str:
    header = content.get("header", {})
    lines = [
        f"# {title}",
        "",
        f"- Fund: {header.get('fund', '')}",
        f"- Snapshot: {header.get('snapshot_date', '')}",
        f"- As of: {header.get('as_of_date', '')}",
        f"- Review run: {header.get('review_run_id', '')}",
        "",
    ]
    if "executive_summary" in content:
        lines.extend(["## Executive Summary", "", str(content["executive_summary"]), ""])
    if "items" in content:
        _extend_challenge_markdown(lines, content)
    if "perspective_summary" in content:
        _extend_sizing_markdown(lines, content)
    return "\n".join(lines).rstrip() + "\n"


def _extend_challenge_markdown(lines: list[str], content: dict[str, Any]) -> None:
    lines.extend(["## Items", ""])
    for item in content.get("items", []):
        if not isinstance(item, dict):
            continue
        acid = item.get("acid", "")
        trigger_type = item.get("trigger_type", "")
        trigger_id = item.get("trigger_candidate_id", "")
        heading = acid
        if trigger_type:
            heading = f"{heading} ({trigger_type})" if heading else trigger_type
        lines.extend([f"### {heading}", ""])
        if trigger_id:
            lines.extend([f"- Trigger: {trigger_id}", ""])
        _extend_pm_challenge_fields(lines, item)
        if item.get("disagreement_statement"):
            lines.extend(["**Disagreement**", "", str(item["disagreement_statement"]), ""])
        if item.get("challenge"):
            lines.extend(["**Challenge**", "", str(item["challenge"]), ""])
        if item.get("next_review_checkpoint"):
            lines.extend([f"**Next Review Checkpoint:** {item['next_review_checkpoint']}", ""])


def _extend_pm_challenge_fields(lines: list[str], item: dict[str, Any]) -> None:
    emitted = False
    for field_name, label in PM_CHALLENGE_MARKDOWN_FIELDS:
        value = item.get(field_name)
        if value in (None, "", [], {}):
            continue
        if not emitted:
            lines.extend(["**PM Decision Card**", ""])
            emitted = True
        lines.extend([f"- **{label}:** {value}"])
    if emitted:
        lines.append("")


def _extend_sizing_markdown(lines: list[str], content: dict[str, Any]) -> None:
    summary = content.get("perspective_summary", {})
    if isinstance(summary, dict) and summary:
        lines.extend(["## Perspective Summary", ""])
        for key, value in summary.items():
            if value not in (None, "", [], {}):
                lines.append(f"- {key}: {value}")
        lines.append("")

    section_map = (
        ("algo_vs_positioning_agreement", "Algo vs Positioning Agreement"),
        ("algo_vs_positioning_disagreement", "Algo vs Positioning Disagreement"),
        ("largest_algo_mom_changes", "Largest Algo MoM Changes"),
    )
    for field, label in section_map:
        rows = content.get(field, [])
        if not isinstance(rows, list) or not rows:
            continue
        lines.extend([f"## {label}", ""])
        for row in rows:
            if not isinstance(row, dict):
                continue
            acid = row.get("acid", "")
            perspective = row.get("perspective", "")
            prefix = acid
            if perspective:
                prefix = f"{prefix} ({perspective})" if prefix else perspective
            narrative = row.get("narrative", "")
            if prefix and narrative:
                lines.append(f"- {prefix}: {narrative}")
            elif narrative:
                lines.append(f"- {narrative}")
            elif prefix:
                lines.append(f"- {prefix}")
        lines.append("")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "fund"


__all__ = ["update_memory", "write_challenge_brief", "write_change_brief", "write_sizing_considerations"]
