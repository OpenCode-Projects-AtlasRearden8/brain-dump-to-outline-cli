# brain-dump-to-outline

Point it at a brain-dump file or a folder of messy notes and get a tidy draft:
a heading hierarchy that groups related thoughts, a **decisions-to-make** list,
and your **next three actions** - rendered as Markdown or a task CSV.

Every output opens with a review-first notice: this tool drafts, **you** review.
It is built for low-energy days when the thoughts are out of your head but not
yet organized, ADHD-friendly by design.

Made by **Asdale Dynamics, LLC** (Dylan Asdale's beginner-friendly AI company -
plain English, step by step, never condescending). MIT licensed.

## How it works

1. It reads your dump file (`.txt`, `.md`, `.markdown`, `.rst`) or every note
   file in a folder.
2. **If an LLM endpoint is configured and reachable** - any OpenAI-compatible
   endpoint, including **Ollama running locally** (config file, no API keys) -
   it drafts the outline with a model, asking the model to merge duplicates,
   clean up wording, and keep every idea's meaning. Nothing is invented;
   thoughts are reorganized, not fabricated.
3. **If no endpoint is running** (or the reply is unusable), it falls back to a
   built-in rule-based offline organizer that still does real work: it strips
   bullet markers, deduplicates near-identical lines, sorts items into topic
   buckets (Health, Money, Home, Work & Writing, Errands & Ideas, Everything
   Else), flags decisions marked with questions, and picks three concrete
   actions.
4. It renders the result as review-first Markdown or a task CSV.

All drafting happens where the text already is: standard input/output, your
local Ollama, or a single configured endpoint. No keys in files, no telemetry,
no personal data collected by the tool itself.

## Install

```bash
pip install .          # then use the bd2outline command
# or just run in place:
python3 -m brainDumpOutline --help
```

## Quick start (offline, no LLM)

```bash
bd2outline dump.txt                     # Markdown to stdout
bd2outline dump.txt -o outline.md       # write to a file
bd2outline notes/ -f csv -o tasks.csv   # folder of notes -> task CSV
```

The offline pass needs nothing installed but Python 3.11+.

## Quick start (with Ollama)

1. Install and start [Ollama](https://ollama.com), pull a small model:
   ```bash
   ollama pull llama3.2
   ```
2. Copy the example config into place and edit it:
   ```bash
   cp bd2outline.toml.example bd2outline.toml
   ```
3. Run it:
   ```bash
   bd2outline dump.txt
   ```

The default config (`bd2outline.toml` in the current folder) already points at
`http://localhost:11434/v1` - Ollama's OpenAI-compatible endpoint - with model
`llama3.2`. If Ollama isn't running, the tool quietly falls back to the offline
organizer and tells you so. Any other OpenAI-compatible server works the same
way (LM Studio, llama.cpp, vLLM, a hosted endpoint): change `base_url` and
`model`.

For endpoints that need a key, set `api_key_env` in the config to the name of
an environment variable holding the key. The key itself never lives in the
config file, in the repo, or in your notes. Local Ollama needs no key at all.

Example config:

```toml
[llm]
base_url = "http://localhost:11434/v1"
model = "llama3.2"
timeout = 120

[output]
format = "markdown"   # or "csv"
```

## What the output looks like (offline fallback)

```markdown
# Brain-Dump Outline

Source: brain-dump.txt
> Review before using: this draft was auto-generated and can be wrong,
> incomplete, or oddly phrased. Read it, fix it, then act.

## Topics
### Money
- pay the water bill
### Home
- clean the garage

## Decisions to Make
- [ ] keep or cancel the streaming bundle?

## Next Three Actions
1. buy new printer ink
2. write chapter 4 outline
3. pay the water bill
```

The CSV gives you one row per item (`section,order,item,type,done`) so you can
sort and check things off in a spreadsheet.

## CLI options

```
bd2outline TARGET [-o FILE] [-f markdown|csv] [--config FILE] [--no-config]
             [--base-url URL] [--model MODEL] [--timeout SECONDS]
             [--offline] [--llm] [--version]
```

- `TARGET` - a file or a folder of note files
- `--offline` - skip the LLM entirely
- `--llm` - require the LLM; stop with an error instead of falling back
- `--config PATH` - use a specific config file (defaults to `./bd2outline.toml`
  when it exists)

Exit codes: `0` success, `2` bad input or unusable LLM path.

## Privacy notes

- Offline mode never sends text anywhere.
- LLM mode sends your note text to the endpoint you configured. Prefer local
  Ollama for dumps containing anything personal or medical. The tool prints a
  one-line reminder to that effect whenever an endpoint is used.
- No API keys, secrets, or personal data are stored by this tool.

## How this differs from our other note tools

- **meeting-notes-summarizer** takes a transcript of a meeting and produces
  minutes, a summary, and action items for attendees. You already know what
  the meeting said; it tidies the record.
- **folder-to-prompt** bundles a folder of real files into one prompt you paste
  into an LLM by hand. It is about context prep, not organization.
- **brain-dump-to-outline** (this tool) takes raw, scattered personal thoughts -
  half-tasks, questions, stray notes jotted at 2am - and organizes them before
  they are a meeting record or a folder to share. That one file/folder of messy
  thoughts becomes an outline + decisions to make + next three actions you can
  act on today, and it works with no AI at all when none is running.

## Development

```bash
pip install -e .[dev]
pytest
```

The test suite includes mocked LLM responses, so everything runs offline.

## License

MIT - see `LICENSE`. Copyright (c) 2026 Asdale Dynamics, LLC.
