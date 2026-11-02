# STATUS - brain-dump-to-outline

Last updated: 2026-11-02

## What was built

`brain-dump-to-outline` - a local-first Python CLI (`bd2outline`) that takes a
brain-dump file or a folder of note files and returns a review-first draft:

- a **tidy heading hierarchy** grouping related thoughts into topic buckets
- a **decisions-to-make** list (question-shaped thoughts)
- **next three actions** (small, concrete, illegibility-proof)
- rendered as **Markdown or task CSV**, each with a manual review-first notice
  on purpose ("this draft can be wrong; read it, fix it, then act")

Drafting paths (in order):

1. **Any OpenAI-compatible endpoint** - configured in `bd2outline.toml`
   (`base_url`, `model`, optional `api_key_env` pointing at an environment
   variable; keys never live in files). Works with Ollama out of the box at
   `http://localhost:11434/v1`. Verified end-to-end against a real
   chat-completions server, including fenced-JSON replies.
2. **Offline rule-based fallback** - when no endpoint is running or the reply
   is unusable: bullet-marker stripping, dedupe (case/whitespace/punctuation
   insensitive, `update:`-prefixed dupes too), sorting into buckets (Health,
   Money, Home, Work & Writing, Errands & Ideas, Everything Else), decision
   detection, and next-three-action picking.

Deliberately distinct from our other note tools: `meeting-notes-summarizer`
tidies a meeting transcript into minutes; `folder-to-prompt` bundles files
into a context prompt for manual pasting; this tool organizes raw scattered
personal thoughts automatically (or with zero AI) and ends in actions.

## How to run

```bash
pip install .            # installs the `bd2outline` command
bd2outline dump.txt      # offline pass -> review-first Markdown
bd2outline notes/ -f csv -o tasks.csv
cp bd2outline.toml.example bd2outline.toml   # enables the Ollama path
bd2outline dump.txt      # tries your endpoint, falls back if down
bd2outline --help
```

Python 3.11+ (stdlib only; `tomllib` is built in). Dev extras: `pip install -e .[dev]` then `pytest`.

## Verification results

- `pytest`: **43 passed**, 0 failed - includes mocked LLM responses (success,
  HTTP 500, connection refused, fenced-JSON, empty/garbage payloads), config
  parsing from files, gathering from file/folder, offline organize pipeline,
  both renderers, and CLI end-to-end runs.
- `python -m build`: sdist + wheel built cleanly.
- Wheel installed into a fresh venv; `bd2outline` console script ran offline
  and produced the expected review-first Markdown.
- Live fallback verified: unreachable endpoint exits 0 with a friendly
  stderr notice and full offline output.
- Live LLM path verified against a scratch local OpenAI-compatible server.
- `python3 -m compileall` on package and tests: clean.

## Known gaps

- The offline bucketing is keyword-based; a thought with no keyword goes to
  "Everything Else", and the bucket list is English-only heuristics.
- Near-duplicate detection is normalization-based, not semantic ("get milk"
  vs "go to the store" are different items offline). The LLM path handles
  that when available.
- CSV has no `due`/`priority` columns yet; the `done` column is intentionally
  blank for human review and manual filling.
- No provider-agnostic `--api-key` flag by design; keys only come from
  environment variables named in the config, never files.
- Only one `--llm` strictness level; no retry/backoff on flaky endpoints.
