"""Render monthly review JSON artifacts into human-readable review packets."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any


RUN_PAYLOAD_FILE = "run_payload.json"
CHANGE_BRIEF_FILE = "change_brief_draft.json"
SIZING_FILE = "sizing_considerations_draft.json"
CHALLENGE_FILE = "challenge_brief_draft.json"
DEFAULT_MARKDOWN_FILE = "run_review.md"
DEFAULT_HTML_FILE = "run_review.html"


def render_review_report(
    run_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    markdown_name: str = DEFAULT_MARKDOWN_FILE,
    html_name: str = DEFAULT_HTML_FILE,
    include_raw_json: bool = False,
) -> dict[str, str]:
    """Render one monthly review run directory or run_payload.json file."""

    payload_path = _resolve_payload_path(Path(run_path))
    run_dir = payload_path.parent
    destination = Path(output_dir) if output_dir else run_dir
    destination.mkdir(parents=True, exist_ok=True)

    bundle = _load_bundle(payload_path)
    markdown = _render_markdown(bundle, include_raw_json=include_raw_json)
    html = _render_html(bundle, include_raw_json=include_raw_json)

    markdown_path = destination / markdown_name
    html_path = destination / html_name
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    return {
        "run_payload_json": payload_path.as_posix(),
        "run_review_md": markdown_path.as_posix(),
        "run_review_html": html_path.as_posix(),
    }


def _resolve_payload_path(run_path: Path) -> Path:
    payload_path = run_path / RUN_PAYLOAD_FILE if run_path.is_dir() else run_path
    if payload_path.name != RUN_PAYLOAD_FILE:
        raise ValueError(f"Expected a run directory or {RUN_PAYLOAD_FILE}; got {run_path}")
    if not payload_path.exists():
        raise FileNotFoundError(f"Could not find {payload_path}")
    return payload_path


def _load_bundle(payload_path: Path) -> dict[str, Any]:
    run_dir = payload_path.parent
    payload = _read_json(payload_path)
    change_brief = payload.get("change_brief") or _read_optional_json(run_dir / CHANGE_BRIEF_FILE)
    sizing = payload.get("sizing_considerations") or _read_optional_json(run_dir / SIZING_FILE)
    challenge = payload.get("challenge_brief") or _read_optional_json(run_dir / CHALLENGE_FILE)
    return {
        "run_dir": run_dir.as_posix(),
        "payload_path": payload_path.as_posix(),
        "payload": payload,
        "change_brief": change_brief or {},
        "sizing_considerations": sizing or {},
        "challenge_brief": challenge,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _render_markdown(bundle: dict[str, Any], *, include_raw_json: bool) -> str:
    metadata = _metadata(bundle)
    payload = bundle["payload"]
    change = bundle["change_brief"]
    sizing = bundle["sizing_considerations"]
    challenge = bundle["challenge_brief"]
    coverage = _nested(payload, "fund_snapshot_summary", "coverage") or {}
    memory = _nested(payload, "fund_snapshot_summary", "memory_summary") or {}
    trigger_summary = _nested(payload, "fund_snapshot_summary", "trigger_summary") or {}

    lines = [
        f"# Monthly Review Packet - {_md(metadata.get('fund', 'Unknown Fund'))}",
        "",
        "## Run Snapshot",
        "",
        _markdown_table(
            ["Field", "Value"],
            [
                ["Snapshot date", metadata.get("snapshot_date", "")],
                ["Prior snapshot date", metadata.get("prior_snapshot_date", "") or "N/A"],
                ["As-of date", metadata.get("as_of_date", "")],
                ["Review run id", metadata.get("review_run_id", "")],
                ["Run mode", metadata.get("run_mode", "")],
                ["Mapping version", metadata.get("mapping_version", "")],
                ["Governance version", metadata.get("governance_version", "")],
            ],
        ),
        "",
        "## Executive Summary",
        "",
        _md(change.get("executive_summary") or "No executive summary was provided."),
        "",
        "## Data Coverage",
        "",
        _markdown_table(
            ["Metric", "Value"],
            [
                ["Target match", _fmt_value(coverage.get("target_match_pct"))],
                ["Benchmark match", _fmt_value(coverage.get("benchmark_match_pct"))],
                ["Benchmark status", coverage.get("benchmark_expected_status", "")],
                ["Thesis entries recalled", memory.get("thesis_ledger_count", 0)],
                ["Watch items recalled", memory.get("watch_items_count", 0)],
            ],
        ),
        "",
        "## Trigger Summary",
        "",
        _markdown_table(
            ["Status", "Count"],
            [
                ["Fired", trigger_summary.get("fired_count", 0)],
                ["Borderline", trigger_summary.get("borderline_count", 0)],
                ["Suppressed", trigger_summary.get("suppressed_count", 0)],
                ["Not triggered", trigger_summary.get("not_triggered_count", 0)],
                ["Not evaluable", trigger_summary.get("not_evaluable_count", 0)],
            ],
        ),
        "",
    ]

    lines.extend(_markdown_material_movers(change))
    lines.extend(_markdown_sizing(sizing))
    lines.extend(_markdown_challenges(challenge))
    lines.extend(_markdown_evidence(change, sizing, challenge))

    if include_raw_json:
        lines.extend(
            [
                "## Raw JSON Appendix",
                "",
                "```json",
                json.dumps(bundle["payload"], indent=2),
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _markdown_material_movers(change: dict[str, Any]) -> list[str]:
    movers = change.get("material_movers") or []
    lines = ["## Key Changes", ""]
    if not movers:
        return lines + ["No material movers were included in this run.", ""]
    rows = []
    for item in movers:
        rows.append(
            [
                item.get("acid_type", ""),
                item.get("acid", ""),
                _fmt_value(item.get("active_rolled_exposure")),
                _fmt_value(item.get("target_rolled_exposure")),
                _fmt_value(item.get("benchmark_rolled_exposure")),
                _fmt_value(item.get("vir_stf")),
                _fmt_value(item.get("vir_rank_change_by_stf")),
                item.get("narrative", ""),
            ]
        )
    return lines + [
        _markdown_table(
            [
                "ACID Type",
                "ACID",
                "Active",
                "Target",
                "Benchmark",
                "STF",
                "Rank Chg",
                "Narrative",
            ],
            rows,
        ),
        "",
    ]


def _markdown_sizing(sizing: dict[str, Any]) -> list[str]:
    lines = ["## Sizing Considerations", ""]
    if not sizing:
        return lines + ["No sizing considerations artifact was included in this run.", ""]

    perspective = sizing.get("perspective_summary") or {}
    if perspective:
        lines.append("### Perspective Coverage")
        lines.append("")
        for key, value in perspective.items():
            lines.append(f"- **{_md(key)}:** {_md(value)}")
        lines.append("")

    for title, field in [
        ("Algo / Positioning Agreement", "algo_vs_positioning_agreement"),
        ("Algo / Positioning Disagreement", "algo_vs_positioning_disagreement"),
        ("Largest Algo Month-over-Month Changes", "largest_algo_mom_changes"),
    ]:
        lines.append(f"### {title}")
        lines.append("")
        rows = sizing.get(field) or []
        if rows:
            lines.append(_markdown_table(["ACID", "Perspective", "Value", "Narrative"], _summary_rows(rows)))
        else:
            lines.append("No rows were included.")
        lines.append("")

    if sizing.get("coverage_notes"):
        lines.extend(["### Coverage Notes", "", _md(sizing["coverage_notes"]), ""])
    return lines


def _markdown_challenges(challenge: dict[str, Any] | None) -> list[str]:
    lines = ["## Challenge Brief", ""]
    if not challenge:
        return lines + ["No fired challenge brief was generated for this run.", ""]

    items = challenge.get("items") or []
    if not items:
        return lines + ["The challenge artifact exists, but it does not contain challenge items.", ""]

    rows = []
    for item in items:
        rows.append(
            [
                item.get("trigger_candidate_id", ""),
                item.get("acid", ""),
                item.get("trigger_type", ""),
                item.get("disagreement_statement", ""),
                item.get("challenge", ""),
            ]
        )
    return lines + [
        _markdown_table(
            ["Trigger Candidate", "ACID", "Type", "Reason", "Challenge"],
            rows,
        ),
        "",
    ]


def _markdown_evidence(
    change: dict[str, Any],
    sizing: dict[str, Any],
    challenge: dict[str, Any] | None,
) -> list[str]:
    evidence = _collect_evidence(change, sizing, challenge)
    lines = ["## Evidence Index", ""]
    if not evidence:
        return lines + ["No evidence pointers were included in this run.", ""]
    rows = [[item.get("artifact_path", ""), item.get("row_id", "")] for item in evidence[:50]]
    return lines + [_markdown_table(["Artifact", "Row ID"], rows), ""]


def _render_html(bundle: dict[str, Any], *, include_raw_json: bool) -> str:
    metadata = _metadata(bundle)
    payload = bundle["payload"]
    change = bundle["change_brief"]
    sizing = bundle["sizing_considerations"]
    challenge = bundle["challenge_brief"]
    coverage = _nested(payload, "fund_snapshot_summary", "coverage") or {}
    memory = _nested(payload, "fund_snapshot_summary", "memory_summary") or {}
    trigger_summary = _nested(payload, "fund_snapshot_summary", "trigger_summary") or {}

    sections = [
        _html_hero(metadata, change),
        _html_cards(
            [
                ("Target Match", _fmt_value(coverage.get("target_match_pct")), "Fund exposure mapped to trusted ACIDs."),
                ("Benchmark Match", _fmt_value(coverage.get("benchmark_match_pct")), "Benchmark exposure mapped to trusted ACIDs."),
                ("Fired Triggers", str(trigger_summary.get("fired_count", 0)), "Items requiring analyst challenge."),
                ("Theses Recalled", str(memory.get("thesis_ledger_count", 0)), "Prior memory available for this fund."),
            ]
        ),
        _html_section("Run Snapshot", _html_table(
            ["Field", "Value"],
            [
                ["Snapshot date", metadata.get("snapshot_date", "")],
                ["Prior snapshot date", metadata.get("prior_snapshot_date", "") or "N/A"],
                ["As-of date", metadata.get("as_of_date", "")],
                ["Review run id", metadata.get("review_run_id", "")],
                ["Run mode", metadata.get("run_mode", "")],
                ["Mapping version", metadata.get("mapping_version", "")],
                ["Governance version", metadata.get("governance_version", "")],
            ],
        )),
        _html_section("Trigger Summary", _html_table(
            ["Status", "Count"],
            [
                ["Fired", trigger_summary.get("fired_count", 0)],
                ["Borderline", trigger_summary.get("borderline_count", 0)],
                ["Suppressed", trigger_summary.get("suppressed_count", 0)],
                ["Not triggered", trigger_summary.get("not_triggered_count", 0)],
                ["Not evaluable", trigger_summary.get("not_evaluable_count", 0)],
            ],
        )),
        _html_material_movers(change),
        _html_sizing(sizing),
        _html_challenges(challenge),
        _html_section("Evidence Index", _html_evidence(change, sizing, challenge)),
    ]

    if include_raw_json:
        sections.append(_html_section("Raw JSON Appendix", f"<pre>{escape(json.dumps(payload, indent=2))}</pre>"))

    return _html_page(metadata.get("fund", "Monthly Review"), "\n".join(sections))


def _html_hero(metadata: dict[str, Any], change: dict[str, Any]) -> str:
    summary = change.get("executive_summary") or "No executive summary was provided."
    return f"""
    <section class="hero">
      <div>
        <p class="eyebrow">Monthly review packet</p>
        <h1>{escape(str(metadata.get("fund", "Unknown Fund")))}</h1>
        <p>{escape(str(summary))}</p>
      </div>
      <div class="hero-meta">
        <span>Snapshot {escape(str(metadata.get("snapshot_date", "")))}</span>
        <span>As-of {escape(str(metadata.get("as_of_date", "")))}</span>
        <span>{escape(str(metadata.get("run_mode", "")))}</span>
      </div>
    </section>
    """


def _html_cards(cards: list[tuple[str, str, str]]) -> str:
    items = []
    for label, value, note in cards:
        items.append(
            f"""
            <article class="card">
              <p>{escape(label)}</p>
              <strong>{escape(value)}</strong>
              <span>{escape(note)}</span>
            </article>
            """
        )
    return f"<section class=\"cards\">{''.join(items)}</section>"


def _html_material_movers(change: dict[str, Any]) -> str:
    movers = change.get("material_movers") or []
    if not movers:
        body = "<p class=\"empty\">No material movers were included in this run.</p>"
    else:
        rows = []
        for item in movers:
            rows.append(
                [
                    item.get("acid_type", ""),
                    item.get("acid", ""),
                    _fmt_value(item.get("active_rolled_exposure")),
                    _fmt_value(item.get("target_rolled_exposure")),
                    _fmt_value(item.get("benchmark_rolled_exposure")),
                    _fmt_value(item.get("vir_stf")),
                    _fmt_value(item.get("vir_rank_change_by_stf")),
                    item.get("narrative", ""),
                ]
            )
        body = _html_table(
            ["ACID Type", "ACID", "Active", "Target", "Benchmark", "STF", "Rank Chg", "Narrative"],
            rows,
        )
    return _html_section("Key Changes", body)


def _html_sizing(sizing: dict[str, Any]) -> str:
    if not sizing:
        return _html_section("Sizing Considerations", "<p class=\"empty\">No sizing artifact was included.</p>")

    parts = []
    perspective = sizing.get("perspective_summary") or {}
    if perspective:
        items = "".join(
            f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>"
            for key, value in perspective.items()
        )
        parts.append(f"<h3>Perspective Coverage</h3><ul>{items}</ul>")

    for title, field in [
        ("Algo / Positioning Agreement", "algo_vs_positioning_agreement"),
        ("Algo / Positioning Disagreement", "algo_vs_positioning_disagreement"),
        ("Largest Algo Month-over-Month Changes", "largest_algo_mom_changes"),
    ]:
        rows = sizing.get(field) or []
        if rows:
            table = _html_table(["ACID", "Perspective", "Value", "Narrative"], _summary_rows(rows))
        else:
            table = "<p class=\"empty\">No rows were included.</p>"
        parts.append(f"<h3>{escape(title)}</h3>{table}")

    if sizing.get("coverage_notes"):
        parts.append(f"<h3>Coverage Notes</h3><p>{escape(str(sizing['coverage_notes']))}</p>")
    return _html_section("Sizing Considerations", "\n".join(parts))


def _html_challenges(challenge: dict[str, Any] | None) -> str:
    if not challenge:
        return _html_section("Challenge Brief", "<p class=\"empty\">No fired challenge brief was generated.</p>")

    items = challenge.get("items") or []
    if not items:
        return _html_section("Challenge Brief", "<p class=\"empty\">The challenge artifact contains no items.</p>")

    rows = []
    for item in items:
        rows.append(
            [
                item.get("trigger_candidate_id", ""),
                item.get("acid", ""),
                item.get("trigger_type", ""),
                item.get("disagreement_statement", ""),
                item.get("challenge", ""),
            ]
        )
    return _html_section(
        "Challenge Brief",
        _html_table(["Trigger Candidate", "ACID", "Type", "Reason", "Challenge"], rows),
    )


def _html_evidence(
    change: dict[str, Any],
    sizing: dict[str, Any],
    challenge: dict[str, Any] | None,
) -> str:
    evidence = _collect_evidence(change, sizing, challenge)
    if not evidence:
        return "<p class=\"empty\">No evidence pointers were included in this run.</p>"
    rows = [[item.get("artifact_path", ""), item.get("row_id", "")] for item in evidence[:50]]
    return _html_table(["Artifact", "Row ID"], rows)


def _html_section(title: str, body: str) -> str:
    return f"""
    <section class="panel">
      <h2>{escape(title)}</h2>
      {body}
    </section>
    """


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
    header_html = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
    row_html = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        row_html.append(f"<tr>{cells}</tr>")
    return f"<div class=\"table-wrap\"><table><thead><tr>{header_html}</tr></thead><tbody>{''.join(row_html)}</tbody></table></div>"


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(title))} Monthly Review</title>
  <style>
    :root {{
      --ink: #15202b;
      --muted: #5d6b78;
      --paper: #f5f1e8;
      --panel: rgba(255, 255, 255, 0.82);
      --line: rgba(21, 32, 43, 0.14);
      --accent: #0e6f68;
      --accent-2: #b85c38;
      --shadow: 0 24px 70px rgba(29, 42, 54, 0.14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(14, 111, 104, 0.20), transparent 34rem),
        radial-gradient(circle at 85% 10%, rgba(184, 92, 56, 0.18), transparent 30rem),
        linear-gradient(135deg, #f7f2e8 0%, #edf3ef 100%);
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 48px 24px 72px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1fr minmax(220px, 320px);
      gap: 28px;
      align-items: end;
      padding: 40px;
      border: 1px solid var(--line);
      border-radius: 32px;
      background: rgba(255,255,255,0.58);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }}
    .eyebrow {{
      color: var(--accent);
      font-family: "Trebuchet MS", sans-serif;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      margin: 0 0 12px;
      text-transform: uppercase;
    }}
    h1 {{
      font-size: clamp(2.3rem, 6vw, 5.2rem);
      letter-spacing: -0.07em;
      line-height: 0.92;
      margin: 0 0 18px;
    }}
    h2 {{
      font-size: 1.45rem;
      letter-spacing: -0.03em;
      margin: 0 0 18px;
    }}
    h3 {{
      color: var(--accent);
      font-family: "Trebuchet MS", sans-serif;
      font-size: 0.9rem;
      letter-spacing: 0.04em;
      margin: 26px 0 10px;
      text-transform: uppercase;
    }}
    p, li, td, th, span {{
      font-family: "Trebuchet MS", sans-serif;
    }}
    .hero p:not(.eyebrow) {{
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
      max-width: 760px;
    }}
    .hero-meta {{
      display: grid;
      gap: 10px;
    }}
    .hero-meta span {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 10px 14px;
      background: rgba(255,255,255,0.58);
      color: var(--muted);
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin: 22px 0;
    }}
    .card, .panel {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--panel);
      box-shadow: 0 18px 42px rgba(29, 42, 54, 0.08);
    }}
    .card {{
      padding: 22px;
    }}
    .card p {{
      color: var(--muted);
      margin: 0 0 8px;
      text-transform: uppercase;
      font-size: 0.76rem;
      letter-spacing: 0.08em;
    }}
    .card strong {{
      display: block;
      color: var(--accent-2);
      font-size: 1.9rem;
      letter-spacing: -0.04em;
      margin-bottom: 8px;
    }}
    .card span {{
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.45;
    }}
    .panel {{
      margin-top: 22px;
      padding: 26px;
    }}
    .table-wrap {{
      width: 100%;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255,255,255,0.64);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 720px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
      font-size: 0.9rem;
      line-height: 1.45;
    }}
    th {{
      color: var(--accent);
      font-size: 0.75rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .empty {{
      color: var(--muted);
      font-style: italic;
    }}
    pre {{
      max-height: 520px;
      overflow: auto;
      border-radius: 18px;
      background: #102027;
      color: #f4eadb;
      padding: 18px;
    }}
    @media (max-width: 860px) {{
      main {{ padding: 24px 14px 48px; }}
      .hero {{ grid-template-columns: 1fr; padding: 28px; }}
      .cards {{ grid-template-columns: 1fr; }}
      .panel {{ padding: 18px; }}
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
"""


def _metadata(bundle: dict[str, Any]) -> dict[str, Any]:
    payload = bundle["payload"]
    change = bundle["change_brief"]
    sizing = bundle["sizing_considerations"]
    return (
        payload.get("review_run_metadata")
        or change.get("header")
        or sizing.get("header")
        or {}
    )


def _summary_rows(rows: list[dict[str, Any]]) -> list[list[Any]]:
    summarized = []
    for item in rows:
        summarized.append(
            [
                item.get("acid", ""),
                item.get("perspective", ""),
                _fmt_value(item.get("value")),
                item.get("narrative", ""),
            ]
        )
    return summarized


def _collect_evidence(
    change: dict[str, Any],
    sizing: dict[str, Any],
    challenge: dict[str, Any] | None,
) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    collected: list[dict[str, str]] = []
    sources = [change.get("evidence_index") or [], sizing.get("evidence_index") or []]
    if challenge:
        sources.append(challenge.get("evidence_index") or [])
    for source in sources:
        for pointer in source:
            artifact = str(pointer.get("artifact_path", ""))
            row_id = str(pointer.get("row_id", ""))
            key = (artifact, row_id)
            if artifact and row_id and key not in seen:
                seen.add(key)
                collected.append({"artifact_path": artifact, "row_id": row_id})
    return collected


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    header = "| " + " | ".join(_md(value) for value in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_md(_fmt_value(value)) for value in row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _fmt_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render monthly review JSON artifacts into Markdown and HTML."
    )
    parser.add_argument(
        "run_path",
        help="Path to a monthly review run directory or run_payload.json file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to the run directory.",
    )
    parser.add_argument(
        "--markdown-name",
        default=DEFAULT_MARKDOWN_FILE,
        help=f"Markdown output filename. Defaults to {DEFAULT_MARKDOWN_FILE}.",
    )
    parser.add_argument(
        "--html-name",
        default=DEFAULT_HTML_FILE,
        help=f"HTML output filename. Defaults to {DEFAULT_HTML_FILE}.",
    )
    parser.add_argument(
        "--include-raw-json",
        action="store_true",
        help="Append the raw run_payload.json to the report for audit review.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    paths = render_review_report(
        args.run_path,
        output_dir=args.output_dir,
        markdown_name=args.markdown_name,
        html_name=args.html_name,
        include_raw_json=args.include_raw_json,
    )
    for key, value in paths.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
