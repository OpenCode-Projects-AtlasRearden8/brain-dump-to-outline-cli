"""Collect text from a brain-dump file or a folder of note files."""

from __future__ import annotations

import os

NOTE_EXTENSIONS = {".txt", ".md", ".markdown", ".rst"}


def _is_note_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in NOTE_EXTENSIONS


def read_dump(target: str) -> str:
    """Read a single file, or every note file in a folder, sorted by name.

    Folder files are joined with a small per-file heading so later sections
    still carry a hint of where each thought came from.
    """
    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    if not os.path.isdir(target):
        raise FileNotFoundError(f"not a file or folder: {target}")

    found = [
        os.path.join(root, name)
        for root, _dirs, names in os.walk(target)
        for name in names
        if _is_note_file(name)
    ]
    if not found:
        return ""
    found.sort()
    chunks = []
    for path in found:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            body = handle.read().strip()
        if not body:
            continue
        label = os.path.basename(path)
        chunks.append(f"[from note: {label}]\n{body}")
    return "\n\n".join(chunks)
