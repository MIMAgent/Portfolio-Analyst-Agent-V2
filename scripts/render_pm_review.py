"""Render a PM-readable review from a live Change Brief JSON artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from portfolio_analyst_agent.pm_review_renderer import (  # noqa: E402
    render_pm_review_html,
    render_pm_review_markdown,
)


def render_pm_review(
    change_brief_json: str | Path,
    *,
    markdown_name: str = "pm_review.md",
    html_name: str = "pm_review.html",
) -> dict[str, str]:
    change_path = Path(change_brief_json)
    change_brief = json.loads(change_path.read_text(encoding="utf-8"))
    output_dir = change_path.parent
    markdown_path = output_dir / markdown_name
    html_path = output_dir / html_name

    markdown_path.write_text(render_pm_review_markdown(change_brief), encoding="utf-8")
    html_path.write_text(render_pm_review_html(change_brief), encoding="utf-8")
    return {
        "change_brief_json": change_path.as_posix(),
        "pm_review_markdown": markdown_path.as_posix(),
        "pm_review_html": html_path.as_posix(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render PM-readable Markdown and HTML from change_brief.json.")
    parser.add_argument("change_brief_json", help="Path to a live agent change_brief.json file.")
    parser.add_argument("--markdown-name", default="pm_review.md")
    parser.add_argument("--html-name", default="pm_review.html")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = render_pm_review(
        args.change_brief_json,
        markdown_name=args.markdown_name,
        html_name=args.html_name,
    )
    for key, value in paths.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
