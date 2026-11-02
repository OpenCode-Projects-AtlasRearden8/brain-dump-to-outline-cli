"""Command-line interface for brain-dump-to-outline."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .config import DEFAULT_CONFIG_NAME, Config, load_config
from .gather import read_dump
from .llm import LLMError, draft_outline
from .offline import DEFAULT_NEXT_ACTIONS, Outline, organize
from .render import render, write_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bd2outline",
        description=(
            "Turn a messy brain-dump file or folder of notes into a tidy draft "
            "outline: heading hierarchy, decisions-to-make, next three actions. "
            "Uses any OpenAI-compatible endpoint when configured (Ollama works "
            "locally with no keys) and falls back to a rule-based offline pass."
        ),
        epilog=(
            "This tool drafts; you review. Every output opens with a "
            "review-first notice on purpose."
        ),
    )
    parser.add_argument("target", help="brain-dump file or folder of note files")
    parser.add_argument("-o", "--output", help="write to this file (default: stdout)")
    parser.add_argument(
        "-f", "--format", dest="fmt", choices=("markdown", "csv"),
        help="output format (overrides the config file)",
    )
    parser.add_argument("--config", help=f"config file path (default: ./{DEFAULT_CONFIG_NAME} if present)")
    parser.add_argument("--no-config", action="store_true", help="ignore any config file; run offline")
    parser.add_argument("--base-url", help="OpenAI-compatible base URL, e.g. http://localhost:11434/v1")
    parser.add_argument("--model", help="model name, e.g. llama3.2")
    parser.add_argument("--timeout", type=int, help="LLM request timeout in seconds")
    parser.add_argument("--offline", action="store_true", help="skip the LLM entirely; use the rule-based fallback")
    parser.add_argument("--llm", action="store_true", help="require the LLM; error instead of falling back")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _build_config(args: argparse.Namespace) -> Config:
    if args.no_config:
        cfg = Config()
    else:
        cfg = load_config(args.config)
    if args.base_url:
        cfg.base_url = args.base_url
    if args.model:
        cfg.model = args.model
    if args.timeout:
        cfg.timeout = args.timeout
    if args.fmt:
        cfg.fmt = args.fmt
    try:
        cfg.timeout = max(5, int(cfg.timeout or 90))
    except (TypeError, ValueError):
        cfg.timeout = 90
    return cfg


def _summary_for(target: str) -> str:
    if os.path.isdir(target):
        return f"all note files under {target}"
    return os.path.basename(target)


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = _build_config(args)

    try:
        text = read_dump(args.target)
    except (OSError, FileNotFoundError) as exc:
        parser.exit(2, f"bd2outline: error: {exc}\n")

    if not text.strip():
        parser.exit(2, f"bd2outline: no note text found in {args.target}\n")

    llm_wanted = not args.offline
    llm_possible = bool(cfg.base_url and cfg.model)
    if args.llm and not llm_possible:
        parser.exit(
            2,
            ("bd2outline: error: --llm needs an endpoint; set base_url and model "
             "in bd2outline.toml or pass --base-url/--model\n"),
        )

    outline: Outline
    if llm_wanted and llm_possible:
        try:
            outline = draft_outline(text, cfg, next_count=DEFAULT_NEXT_ACTIONS)
            print(
                f"Drafted with {cfg.model} at {cfg.base_url}. The endpoint saw your "
                "note text - only send to endpoints you trust.",
                file=sys.stderr,
            )
        except LLMError as exc:
            if args.llm:
                parser.exit(2, f"bd2outline: error: LLM path failed: {exc}\n")
            print(
                f"Endpoint not usable ({exc}); falling back to the offline "
                "rule-based organizer. [LLM online gives richer drafting]",
                file=sys.stderr,
            )
            outline = organize(text)
    else:
        if args.offline:
            print("Offline mode: sorting, deduplicating, and grouping with built-in rules.", file=sys.stderr)
        outline = organize(text)

    rendered = render(outline, cfg.fmt, summary=_summary_for(args.target))
    try:
        write_output(rendered, args.output)
    except OSError as exc:
        parser.exit(2, f"bd2outline: error: could not write output: {exc}\n")
    return 0


def main() -> None:  # pragma: no cover - thin wrapper for console script
    sys.exit(run())


if __name__ == "__main__":
    main()
