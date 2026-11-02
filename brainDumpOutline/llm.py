"""Client for any OpenAI-compatible chat-completions endpoint.

Works with Ollama (``http://localhost:11434/v1``), LM Studio, llama.cpp,
or a hosted endpoint - whatever the config file points at. No API key is
required for local servers; hosted ones get one via an environment
variable named by ``api_key_env`` so keys never touch files.

The fallback path in ``cli.py`` keeps the tool useful even when no
endpoint is running.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .config import Config
from .offline import Outline, OutlineGroup

SYSTEM_PROMPT = (
    "You are a personal notebook organizer. The user hands you a messy "
    "brain dump. Return ONLY a JSON object with this exact shape: "
    '{"groups": [{"title": "short bucket name", "items": ["cleaned item"]}], '
    '"decisions": ["question still to decide"], '
    '"next_actions": ["concrete small action"]}. '
    "Clean up the wording, merge duplicates, and group related thoughts. "
    "Keep every thought's meaning; never invent new facts. "
    "Give 3 next_actions picked for being small and doable this week."
)

class LLMError(Exception):
    pass


def _headers(cfg: Config) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = cfg.api_key
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _build_payload(text: str, cfg: Config) -> bytes:
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    return json.dumps(payload).encode("utf-8")


def chat_completion(text: str, cfg: Config) -> str:
    """POST to the endpoint and return the assistant message content."""
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=_build_payload(text, cfg),
        headers=_headers(cfg),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=cfg.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise LLMError(f"endpoint returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise LLMError(f"could not reach endpoint: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"unexpected response shape: {body!r}") from exc


def extract_json(content: str) -> dict[str, Any]:
    """Parse the model's reply as JSON, tolerating ``` fences and prose."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3]
        cleaned = cleaned.strip()
    start, _end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or _end == -1 or _end < start:
        raise LLMError("no JSON object found in model output")
    try:
        data = json.loads(cleaned[start : _end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"model output was not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMError("model output did not contain a JSON object")
    return data


def outline_from_json(data: dict[str, Any], next_count: int = 3) -> Outline:
    outline = Outline()
    for raw_group in data.get("groups") or []:
        if not isinstance(raw_group, dict):
            continue
        title = str(raw_group.get("title") or "Notes").strip() or "Notes"
        members = [str(item).strip() for item in raw_group.get("items") or []]
        members = [item for item in members if item]
        if members:
            outline.groups.append(OutlineGroup(title=title, items=members))
    outline.decisions = [
        str(item).strip()
        for item in data.get("decisions") or []
        if str(item).strip()
    ]
    picks = [str(item).strip() for item in data.get("next_actions") or [] if str(item).strip()]
    outline.next_actions = picks[:next_count]
    if not outline.groups and not outline.decisions and not outline.next_actions:
        raise LLMError("model output had no usable groups, decisions, or actions")
    return outline


def draft_outline(text: str, cfg: Config, next_count: int = 3) -> Outline:
    content = chat_completion(text, cfg)
    return outline_from_json(extract_json(content), next_count=next_count)
