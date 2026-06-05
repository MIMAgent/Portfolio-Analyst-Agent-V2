"""PM-readable rendering for live agent review artifacts."""

from __future__ import annotations

from html import escape
import re
from typing import Any

from .citations import extract_tokens


def render_pm_review_markdown(change_brief: dict[str, Any]) -> str:
    """Render a cleaner PM-facing Markdown review from a Change Brief JSON payload."""

    header = change_brief.get("header", {})
    summary, footnotes = _clean_with_footnotes(str(change_brief.get("executive_summary", "")))
    movers = change_brief.get("material_movers") or []

    lines = [
        f"# PM Review - {header.get('fund', 'Unknown Fund')}",
        "",
        "## Executive Summary",
        "",
        summary or "No executive summary was provided.",
        "",
        "## Key Positioning Tensions",
        "",
    ]
    if movers:
        lines.extend(_markdown_movers(movers, footnotes))
    else:
        lines.extend(["No material movers were included.", ""])

    lines.extend(["## Signal Alignment / Disagreement", ""])
    lines.extend(_markdown_signal_section(movers))
    lines.extend(["## Questions for PM Review", ""])
    lines.extend(_markdown_questions(movers))
    lines.extend(["## Evidence Footnotes", ""])
    lines.extend(_markdown_footnotes(footnotes))

    return "\n".join(lines).rstrip() + "\n"


def render_pm_review_html(change_brief: dict[str, Any]) -> str:
    """Render a PM-facing standalone HTML review from a Change Brief JSON payload."""

    header = change_brief.get("header", {})
    summary, footnotes = _clean_with_footnotes(str(change_brief.get("executive_summary", "")))
    movers = change_brief.get("material_movers") or []

    body = "\n".join(
        [
            _hero(header, summary),
            _section("Key Positioning Tensions", _html_movers(movers, footnotes)),
            _section("Signal Alignment / Disagreement", _html_signal_section(movers)),
            _section("Questions for PM Review", _html_questions(movers)),
            _section("Evidence Footnotes", _html_footnotes(footnotes)),
        ]
    )
    return _html_page(title=f"{header.get('fund', 'PM Review')} PM Review", body=body)


def _markdown_movers(movers: list[dict[str, Any]], footnotes: dict[str, int]) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(movers, 1):
        acid = item.get("acid", f"Mover {index}")
        narrative, _ = _clean_with_footnotes(str(item.get("narrative", "")), footnotes=footnotes)
        active = _fmt_metric(item.get("active_rolled_exposure"), _active_exposure(item), unit="%")
        target = _fmt_metric(item.get("target_rolled_exposure"), _target_exposure(item), unit="%")
        benchmark = _fmt_metric(item.get("benchmark_rolled_exposure"), _benchmark_exposure(item), unit="%")
        stf = _fmt_metric(item.get("vir_stf"), _stf_value(item))
        lines.extend(
            [
                f"### {index}. {acid}",
                "",
                *(_metric_block([("Active", active), ("Target", target), ("Benchmark", benchmark), ("STF", stf)])),
                narrative or "No narrative was provided.",
                "",
            ]
        )
        takeaway = item.get("pm_takeaway")
        if takeaway:
            cleaned_takeaway, _ = _clean_with_footnotes(str(takeaway), footnotes=footnotes)
            lines.extend(["**PM Takeaway:** " + cleaned_takeaway, ""])
        change_view = item.get("what_would_change_view")
        if change_view:
            cleaned_change_view, _ = _clean_with_footnotes(str(change_view), footnotes=footnotes)
            lines.extend(["**What Would Change the View:** " + cleaned_change_view, ""])
    return lines


def _markdown_signal_section(movers: list[dict[str, Any]]) -> list[str]:
    if not movers:
        return ["No signal alignment observations were available.", ""]

    lines = []
    for item in movers:
        acid = item.get("acid", "")
        narrative = str(item.get("narrative", "")).lower()
        active = _active_exposure(item)
        stf = _stf_value(item)
        if "sign_disagreement" in narrative or (active and stf and active * stf < 0):
            assessment = (
                f"Positioning and signal point in opposite directions: active exposure is {_direction(active)} "
                f"while STF is {_direction(stf)}."
            )
        elif stf < 0 and active < 0:
            assessment = "Underweight is directionally aligned with a negative STF, but PM should confirm whether the underweight remains sized appropriately."
        elif stf > 0 and active > 0:
            assessment = "Overweight is directionally aligned with a positive STF, but PM should confirm whether valuation/rank momentum still supports the exposure."
        elif stf:
            assessment = "Positioning should be reviewed against current VIR signal direction."
        else:
            assessment = "Signal context is limited in this artifact."
        lines.append(f"- **{acid}:** {assessment}")
    lines.append("")
    return lines


def _markdown_questions(movers: list[dict[str, Any]]) -> list[str]:
    if not movers:
        return ["- What additional evidence should be pulled before PM review?", ""]

    lines = []
    for item in movers[:5]:
        acid = item.get("acid", "this exposure")
        explicit = item.get("review_question")
        if explicit:
            lines.append(f"- {explicit}")
            continue
        active = _active_exposure(item)
        stf = _stf_value(item)
        narrative = str(item.get("narrative", "")).lower()
        if "sign_disagreement" in narrative or (active and stf and active * stf < 0):
            lines.append(
                f"- For {acid}, what is the PM's non-model rationale for holding exposure opposite the current VIR/algo signal, and what would invalidate that rationale?"
            )
        elif active < 0 and stf < 0:
            lines.append(
                f"- For {acid}, does the negative STF still justify the size of the underweight, or do improving MoM signal/rank details argue for narrowing the gap?"
            )
        elif active > 0 and stf > 0:
            lines.append(
                f"- For {acid}, does positive signal support justify the current overweight, or is the opportunity better expressed through a narrower peer ACID?"
            )
        else:
            lines.append(
                f"- For {acid}, which cited datapoint should drive the next PM discussion: exposure size, VIR rank, or month-over-month signal change?"
            )
    lines.append("- Which of these tensions should become a watch item for next month's review rather than remain a one-cycle observation?")
    lines.append("")
    return lines


def _markdown_footnotes(footnotes: dict[str, int]) -> list[str]:
    if not footnotes:
        return ["No citation tokens were found in the PM-facing text.", ""]
    ordered = sorted(footnotes.items(), key=lambda item: item[1])
    return [f"[{number}] `{token}`" for token, number in ordered] + [""]


def _html_movers(movers: list[dict[str, Any]], footnotes: dict[str, int]) -> str:
    if not movers:
        return "<p class=\"empty\">No material movers were included.</p>"
    cards = []
    for index, item in enumerate(movers, 1):
        acid = escape(str(item.get("acid", f"Mover {index}")))
        narrative, _ = _clean_with_footnotes(str(item.get("narrative", "")), footnotes=footnotes)
        metrics = [
            ("Active", _fmt_metric(item.get("active_rolled_exposure"), _active_exposure(item), unit="%")),
            ("Target", _fmt_metric(item.get("target_rolled_exposure"), _target_exposure(item), unit="%")),
            ("Benchmark", _fmt_metric(item.get("benchmark_rolled_exposure"), _benchmark_exposure(item), unit="%")),
            ("STF", _fmt_metric(item.get("vir_stf"), _stf_value(item))),
        ]
        populated_metrics = [(label, value) for label, value in metrics if value]
        metric_html = "".join(
            f"<span><b>{escape(label)}</b>{escape(value or 'N/A')}</span>"
            for label, value in populated_metrics
        )
        metric_block = f"<div class=\"metrics\">{metric_html}</div>" if populated_metrics else ""
        cards.append(
            f"""
            <article class="mover">
              <div class="mover-head">
                <span class="index">{index}</span>
                <h3>{acid}</h3>
              </div>
              {metric_block}
              <p>{escape(narrative or "No narrative was provided.")}</p>
              {_html_optional_note("PM Takeaway", item.get("pm_takeaway"), footnotes)}
              {_html_optional_note("What Would Change the View", item.get("what_would_change_view"), footnotes)}
            </article>
            """
        )
    return "\n".join(cards)


def _html_signal_section(movers: list[dict[str, Any]]) -> str:
    lines = _markdown_signal_section(movers)
    items = [line.removeprefix("- ").strip() for line in lines if line.startswith("- ")]
    if not items:
        return "<p class=\"empty\">No signal alignment observations were available.</p>"
    return "<ul>" + "".join(f"<li>{escape(_strip_markdown(item))}</li>" for item in items) + "</ul>"


def _html_questions(movers: list[dict[str, Any]]) -> str:
    lines = _markdown_questions(movers)
    items = [line.removeprefix("- ").strip() for line in lines if line.startswith("- ")]
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _html_optional_note(label: str, value: Any, footnotes: dict[str, int]) -> str:
    if not value:
        return ""
    cleaned, _ = _clean_with_footnotes(str(value), footnotes=footnotes)
    return f"<p class=\"note\"><strong>{escape(label)}:</strong> {escape(cleaned)}</p>"


def _html_footnotes(footnotes: dict[str, int]) -> str:
    if not footnotes:
        return "<p class=\"empty\">No citation tokens were found in the PM-facing text.</p>"
    ordered = sorted(footnotes.items(), key=lambda item: item[1])
    rows = "".join(
        f"<tr><td>[{number}]</td><td><code>{escape(token)}</code></td></tr>"
        for token, number in ordered
    )
    return f"<table><tbody>{rows}</tbody></table>"


def _hero(header: dict[str, Any], summary: str) -> str:
    return f"""
    <section class="hero">
      <p class="eyebrow">Live Bedrock agent review</p>
      <h1>{escape(str(header.get("fund", "Unknown Fund")))}</h1>
      <p>{escape(summary or "No executive summary was provided.")}</p>
      <div class="meta">
        <span>Snapshot {escape(str(header.get("snapshot_date", "")))}</span>
        <span>As of {escape(str(header.get("as_of_date", "")))}</span>
        <span>{escape(str(header.get("review_run_id", "")))}</span>
      </div>
    </section>
    """


def _section(title: str, body: str) -> str:
    return f"""
    <section class="panel">
      <h2>{escape(title)}</h2>
      {body}
    </section>
    """


def _clean_with_footnotes(text: str, *, footnotes: dict[str, int] | None = None) -> tuple[str, dict[str, int]]:
    current = footnotes if footnotes is not None else {}

    def replace(match: re.Match[str]) -> str:
        tokens = extract_tokens(match.group(0))
        token = tokens[0] if tokens else match.group(0).strip()
        if token not in current:
            current[token] = len(current) + 1
        return f"[{current[token]}]"

    cleaned = re.sub(
        r"(csv:[^\s\]\)]+|mem:[^\s\]\)]+|deriv:[^\s\]\)]+|trigger:[^\s\]\)]+)",
        replace,
        text,
    ).strip()
    cleaned = re.sub(r"\[\s*((?:\[\d+\]\s*)+)\]", lambda match: match.group(1).strip(), cleaned)
    return cleaned, current


def _metric_line(metrics: list[tuple[str, str]]) -> str:
    values = [f"**{label}:** {value}" for label, value in metrics if value]
    return " | ".join(values) if values else "**Metrics:** N/A"


def _metric_block(metrics: list[tuple[str, str]]) -> list[str]:
    line = _metric_line(metrics)
    if line == "**Metrics:** N/A":
        return []
    return [line, ""]


def _fmt(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _fmt_metric(raw_value: Any, inferred_value: float, *, unit: str = "") -> str:
    if raw_value not in (None, ""):
        value = _fmt(raw_value)
    elif inferred_value:
        value = f"{inferred_value:.2f}" if unit else f"{inferred_value:.4f}"
    else:
        return ""
    return f"{value}{unit}" if unit and not str(value).endswith(unit) else value


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _active_exposure(item: dict[str, Any]) -> float:
    direct = _safe_float(item.get("active_rolled_exposure"))
    if direct:
        return direct
    text = " ".join(str(item.get(field, "")) for field in ("narrative", "pm_takeaway", "review_question"))
    patterns = (
        r"([+-]?\d+(?:\.\d+)?)\s*pp\s+active\s+rolled\s+exposure",
        r"([+-]?\d+(?:\.\d+)?)\s*%\s+active\s+rolled\s+exposure",
        r"([+-]?\d+(?:\.\d+)?)\s*pp\s+active\s+rolled\s+(?:overweight|underweight)",
        r"([+-]?\d+(?:\.\d+)?)\s*%\s+active\s+rolled\s+(?:overweight|underweight)",
        r"active\s+rolled\s+(?:overweight|underweight|exposure)\s*(?:at|of|is)?\s*([+-]?\d+(?:\.\d+)?)\s*pp",
        r"active\s+rolled\s+(?:overweight|underweight|exposure)\s*(?:at|of|is)?\s*([+-]?\d+(?:\.\d+)?)\s*%",
        r"rolled\s+active\s+exposure\s+(?:at|of|is)?\s*([+-]?\d+(?:\.\d+)?)\s*pp",
        r"rolled\s+active\s+exposure\s+(?:at|of|is)?\s*([+-]?\d+(?:\.\d+)?)\s*%",
        r"active\s+deviation\s+at\s*([+-]?\d+(?:\.\d+)?)\s*pp",
        r"active\s+deviation\s+at\s*([+-]?\d+(?:\.\d+)?)\s*%",
    )
    value = _first_number_match(text, patterns)
    if value:
        return value
    if "active rolled overweight" in text.lower():
        return abs(_first_number_match(text, (r"active\s+rolled\s+overweight.*?([+-]?\d+(?:\.\d+)?)\s*(?:pp|%)",)))
    if "active rolled underweight" in text.lower():
        return -abs(_first_number_match(text, (r"active\s+rolled\s+underweight.*?([+-]?\d+(?:\.\d+)?)\s*(?:pp|%)",)))
    return 0.0


def _target_exposure(item: dict[str, Any]) -> float:
    direct = _safe_float(item.get("target_rolled_exposure"))
    if direct:
        return direct
    text = " ".join(str(item.get(field, "")) for field in ("narrative", "pm_takeaway", "review_question"))
    return _first_number_match(
        text,
        (
            r"fund\s+target\s+([+-]?\d+(?:\.\d+)?)\s*%",
            r"target\s+([+-]?\d+(?:\.\d+)?)\s*%",
            r"fund\s+target\s+([+-]?\d+(?:\.\d+)?)\s*pp",
            r"target\s+([+-]?\d+(?:\.\d+)?)\s*pp",
        ),
    )


def _benchmark_exposure(item: dict[str, Any]) -> float:
    direct = _safe_float(item.get("benchmark_rolled_exposure"))
    if direct:
        return direct
    text = " ".join(str(item.get(field, "")) for field in ("narrative", "pm_takeaway", "review_question"))
    return _first_number_match(
        text,
        (
            r"benchmark\s+([+-]?\d+(?:\.\d+)?)\s*%",
            r"benchmark\s+([+-]?\d+(?:\.\d+)?)\s*pp",
        ),
    )


def _stf_value(item: dict[str, Any]) -> float:
    direct = _safe_float(item.get("vir_stf"))
    if direct:
        return direct
    text = " ".join(str(item.get(field, "")) for field in ("narrative", "pm_takeaway", "review_question"))
    return _first_number_match(
        text,
        (
            r"VIR[-\s]+STF\s+(?:is|of)?\s*([+-]?\d+(?:\.\d+)?)",
            r"STF\s+(?:is|of)?\s*([+-]?\d+(?:\.\d+)?)",
        ),
    )


def _first_number_match(text: str, patterns: tuple[str, ...]) -> float:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _safe_float(match.group(1))
    return 0.0


def _direction(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _strip_markdown(value: str) -> str:
    return value.replace("**", "")


def _html_page(*, title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --ink: #17212b;
      --muted: #66717d;
      --paper: #f5f0e6;
      --panel: rgba(255, 255, 255, 0.82);
      --line: rgba(23, 33, 43, 0.14);
      --accent: #0f6c5d;
      --rust: #b05b38;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 10%, rgba(15, 108, 93, 0.20), transparent 30rem),
        radial-gradient(circle at 88% 5%, rgba(176, 91, 56, 0.18), transparent 28rem),
        linear-gradient(135deg, #f8f1e5 0%, #edf4ef 100%);
      font-family: Georgia, "Times New Roman", serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 44px 22px 72px;
    }}
    .hero, .panel {{
      border: 1px solid var(--line);
      border-radius: 28px;
      background: var(--panel);
      box-shadow: 0 24px 70px rgba(23, 33, 43, 0.12);
    }}
    .hero {{
      padding: 38px;
      margin-bottom: 20px;
    }}
    .eyebrow {{
      margin: 0 0 12px;
      color: var(--accent);
      font: 700 0.78rem "Trebuchet MS", sans-serif;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: clamp(2.4rem, 6vw, 5rem);
      line-height: 0.92;
      letter-spacing: -0.07em;
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: 1.45rem;
      letter-spacing: -0.03em;
    }}
    h3 {{
      margin: 0;
      font-size: 1.08rem;
    }}
    p, li, td, span {{
      font-family: "Trebuchet MS", sans-serif;
      line-height: 1.55;
    }}
    .hero p:not(.eyebrow) {{
      max-width: 850px;
      color: var(--muted);
      font-size: 1.02rem;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }}
    .meta span {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 9px 13px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.6);
    }}
    .panel {{
      margin-top: 18px;
      padding: 26px;
    }}
    .mover {{
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 18px;
      margin-top: 14px;
      background: rgba(255, 255, 255, 0.58);
    }}
    .mover-head {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .index {{
      display: inline-grid;
      place-items: center;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: var(--accent);
      color: white;
      font-weight: 700;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .metrics span {{
      border-radius: 16px;
      padding: 10px;
      background: rgba(15, 108, 93, 0.08);
      color: var(--muted);
    }}
    .metrics b {{
      display: block;
      color: var(--rust);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-family: "Trebuchet MS", sans-serif;
    }}
    td {{
      border-bottom: 1px solid var(--line);
      padding: 10px;
      vertical-align: top;
    }}
    code {{
      white-space: normal;
      word-break: break-word;
    }}
    .empty {{
      color: var(--muted);
      font-style: italic;
    }}
    @media (max-width: 760px) {{
      main {{ padding: 22px 12px 48px; }}
      .hero, .panel {{ padding: 20px; }}
      .metrics {{ grid-template-columns: 1fr; }}
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


__all__ = ["render_pm_review_html", "render_pm_review_markdown"]
