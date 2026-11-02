"""Offline, rule-based organizer: the fallback when no LLM is running.

It still does real work - sorting items into buckets, deduplicating
near-identical lines, and picking three concrete next actions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_BULLET = re.compile(r"^[-*•–—+>]+|\b\d+[.)]\s|\[[ xX]\]\s*|[·]+", re.IGNORECASE)
_OLD_PREFIX = re.compile(r"^(old|stale) (titles?|todos?|ideas?)\b[:\-]?", re.IGNORECASE)
_UPDATE_PREFIX = re.compile(r"^(updates?)\b[:\-]?\s*", re.IGNORECASE)
_TODO_PREFIX = re.compile(r"^todo:?\s*", re.IGNORECASE)
_PUNCT = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")

_DECISION_HINTS = re.compile(
    r"\?$|^should (i|we|the|a)\b|^is (it|i)\b|^do (i|we)\b|"
    r"^(which|whether|what if|decide|choose|pick|between|option|worth|keep or|go with)\b",
    re.IGNORECASE,
)
_ACTION_HINTS = re.compile(
    r"^todo\b|^(buy|email|call|pay|schedule|book|fix|write|file|renew|cancel|order|"
    r"sign|check|ask|clean|send|draft|get|drop|mail|pick|refill|review|try|find|"
    r"look|upgrade|replace|download|back ?up|sort|finish|start|read|set)\b",
    re.IGNORECASE,
)

_TOPIC_BUCKETS: list[tuple[str, re.Pattern]] = [
    ("Health", re.compile(r"\b(doctor|dental|dentist|medic|refill|rx|clinic|insurance|sleep|meds?|vaccin|therap)\w*\b", re.IGNORECASE)),
    ("Money", re.compile(r"\b(budget|bill|rent|tax|invoice|paycheck|bank|refund|price|costs?|spend\w*|fees?)\b", re.IGNORECASE)),
    ("Home", re.compile(r"\b(dish(es)?|laundry|closet|garage|yard|porch|repair|gutter|smoke alarm|filter|clean\w*)\b", re.IGNORECASE)),
    ("Work & Writing", re.compile(r"\b(book|chapter|draft|manuscript|blurb|kdp|launch|newsletter|blog|post|publish\w*|client)\b", re.IGNORECASE)),
    ("Errands & Ideas", re.compile(r"\b(buy|order|errand|store|grocer\w*|library|appointment|call|email)")),
]
_FALLBACK_BUCKET = "Everything Else"

DEFAULT_NEXT_ACTIONS = 3


@dataclass
class OutlineGroup:
    title: str
    items: list[str] = field(default_factory=list)


@dataclass
class Outline:
    groups: list[OutlineGroup] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    line = text.strip()
    while True:
        stripped = _BULLET.sub("", line, count=1).lstrip()
        if stripped == line:
            break
        line = stripped
    line = _OLD_PREFIX.sub("", line)
    line = _UPDATE_PREFIX.sub("", line)
    line = _TODO_PREFIX.sub("", line)
    line = _BULLET.sub("", line).strip()
    return _WHITESPACE.sub(" ", line)


def is_markdown_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+\S", line.strip()))


def parse_items(text: str) -> list[str]:
    items = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or is_markdown_heading(line):
            continue
        cleaned = normalize(line)
        if cleaned:
            items.append(cleaned)
    return items


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    kept = []
    for item in items:
        key = _PUNCT.sub("", item)
        key = _WHITESPACE.sub(" ", key).casefold().strip()
        if key in seen:
            continue
        seen.add(key)
        kept.append(item)
    return kept


def classify(item: str) -> str:
    if _DECISION_HINTS.search(item):
        return "decision"
    if _ACTION_HINTS.match(item):
        return "action"
    return "idea"


def bucket_for(item: str) -> str:
    for title, pattern in _TOPIC_BUCKETS:
        if pattern.search(item):
            return title
    return _FALLBACK_BUCKET


def group_into_buckets(items: list[str]) -> list[OutlineGroup]:
    groups: list[OutlineGroup] = []
    by_title: dict[str, OutlineGroup] = {}
    for item in items:
        title = bucket_for(item)
        group = by_title.get(title)
        if group is None:
            group = OutlineGroup(title=title)
            by_title[title] = group
            groups.append(group)
        group.items.append(item)
    return groups


def organize(text: str, next_count: int = DEFAULT_NEXT_ACTIONS) -> Outline:
    items = dedupe(parse_items(text))
    decisions: list[str] = []
    doable: list[str] = []
    for item in items:
        if classify(item) == "decision":
            decisions.append(item)
        else:
            doable.append(item)
    actions = [item for item in doable if classify(item) == "action"]
    outline = Outline(groups=group_into_buckets(doable), decisions=decisions)
    picked = actions[:next_count]
    if not picked:
        picked = items[:next_count]
    outline.next_actions = picked
    return outline
