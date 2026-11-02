"""Config file loading (TOML, no API keys).

Default config file is ``bd2outline.toml`` in the current directory (or the
path given with ``--config``). Example::

    [llm]
    base_url = "http://localhost:11434/v1"   # Ollama's OpenAI-compatible endpoint
    model = "llama3.2"
    timeout = 120

    [output]
    format = "markdown"        # or "csv"

Keys never appear in the config file. If an endpoint needs one (most local
ones, including Ollama, do not), the file may name an *environment variable*:

    [llm]
    base_url = "https://api.example.com/v1"
    model = "whatever"
    api_key_env = "MY_ENDPOINT_KEY"

The key itself stays out of the repo and out of the file.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from typing import Any

DEFAULT_CONFIG_NAME = "bd2outline.toml"


@dataclass
class Config:
    base_url: str | None = None
    model: str | None = None
    timeout: int = 90
    api_key_env: str | None = None
    fmt: str = "markdown"

    @property
    def api_key(self) -> str | None:
        """Resolve the API key from the environment, if one is configured."""
        if not self.api_key_env:
            return None
        value = os.environ.get(self.api_key_env)
        return value if value else None


def _clean(value: Any) -> Any:
    return value if not isinstance(value, str) else value.strip()


def load_config(path: str | None = None) -> Config:
    """Load a config file; a missing/unreadable file is treated as empty."""
    location = path or (DEFAULT_CONFIG_NAME if os.path.exists(DEFAULT_CONFIG_NAME) else None)
    if not location or not os.path.exists(location):
        return Config()
    try:
        with open(location, "rb") as handle:
            data = tomllib.load(handle)
    except (tomllib.TOMLDecodeError, OSError):
        return Config()
    llm = data.get("llm") or {}
    output = data.get("output") or {}
    fmt = _clean(output.get("format", "markdown"))
    if fmt not in ("markdown", "csv"):
        fmt = "markdown"
    timeout = llm.get("timeout", 90)
    try:
        timeout = max(5, int(timeout))
    except (TypeError, ValueError):
        timeout = 90
    return Config(
        base_url=_clean(llm.get("base_url")) or None,
        model=_clean(llm.get("model")) or None,
        timeout=timeout,
        api_key_env=_clean(llm.get("api_key_env")) or None,
        fmt=fmt,
    )
