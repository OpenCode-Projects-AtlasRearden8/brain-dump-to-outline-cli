"""Render an Outline as review-first Markdown or a task CSV."""

from __future__ import annotations

import csv
import io

from . import __version__
from .offline import Outline

_REVIEW_NOTICE = (
    "Review before using: this draft was auto-generated and can be wrong, "
    "incomplete, or oddly phrased. Read it, fix it, then act."
)


def _header_lines(tool: str, summary: str | None) -> list[str]:
    lines = [f"DRAFT OUTLINE - {tool} v{__version__}"]
    if summary:
        lines.append(f"Source: {summary}")
    lines.append(_REVIEW_NOTICE)
    return lines


def render_markdown(outline: Outline, summary: str | None = None) -> str:
    blocks = ["# Brain-Dump Outline", ""]
    for line in _header_lines("review-first drafts made easy", summary):
        if line.startswith("DRAFT"):
            continue
        blocks.append(f"> {line}" if line.startswith("Review") else line)
    blocks.append("")

    blocks.append("## Topics")
    blocks.append("")
    for group in outline.groups:
        blocks.append(f"### {group.title}")
        blocks.append("")
        for item in group.items:
            blocks.append(f"- {item}")
        blocks.append("")

    blocks.append("## Decisions to Make")
    blocks.append("")
    if outline.decisions:
        for item in outline.decisions:
            blocks.append(f"- [ ] {item}")
    else:
        blocks.append("_No decisions spotted in the dump._")
    blocks.append("")

    blocks.append("## Next Three Actions")
    blocks.append("")
    if outline.next_actions:
        blocks.extend(f"{n}. {item}" for n, item in enumerate(outline.next_actions, start=1))
    else:
        blocks.append("_Nothing picked yet - review the topics and pick three._")
    blocks.append("")
    blocks.append("<!-- DRAFT: this outline was machine-drafted; review every line before trusting it -->")
    blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def render_csv(outline: Outline) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["section", "order", "item", "type", "done"])
    for n, item in enumerate(outline.groups):
        for m, entry in enumerate(item.items, start=1):
            writer.writerow([item.title, m, entry, "topic", ""])
    for n, item in enumerate(outline.decisions, start=1):
        writer.writerow(["Decisions to Make", n, item, "decision", ""])
    for n, item in enumerate(outline.next_actions, start=1):
        writer.writerow(["Next Three Actions", n, item, "action", ""])
    return buffer.getvalue()


def render(outline: Outline, fmt: str, summary: str | None = None) -> str:
    if fmt == "csv":
        return render_csv(outline)
    return render_markdown(outline, summary)


def write_output(text: str, destination: str | None = None) -> None:
    if destination:
        with open(destination, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        import sys

        sys.stdout.write(text)
