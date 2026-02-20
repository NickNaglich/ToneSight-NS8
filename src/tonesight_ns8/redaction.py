"""Deterministic text/event redaction helpers for live-mode artifacts."""

from __future__ import annotations

import re
from typing import Any


_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]*)?(?:\(?\d{3}\)?[-.\s]*)\d{3}[-.\s]*\d{4}\b"), "[PHONE]"),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
]


def redact_text(text: str | None) -> tuple[str | None, dict[str, int]]:
    """Redact configured token types from text with deterministic replacements."""
    if text is None:
        return None, {name: 0 for name, _, _ in _PATTERNS}

    redacted = str(text)
    counts = {name: 0 for name, _, _ in _PATTERNS}

    for name, pattern, replacement in _PATTERNS:
        def _repl(_: re.Match[str]) -> str:
            counts[name] += 1
            return replacement

        redacted = pattern.sub(_repl, redacted)

    return redacted, counts


def redact_live_event(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    """Return a redacted copy of a live event and aggregated token counts."""
    redacted_event = dict(event)
    total = {name: 0 for name, _, _ in _PATTERNS}

    text, counts = redact_text(event.get("text"))
    if text is not None:
        redacted_event["text"] = text
    for key, value in counts.items():
        total[key] += value

    if isinstance(event.get("segments"), list):
        new_segments: list[dict[str, Any]] = []
        for segment in event["segments"]:
            if not isinstance(segment, dict):
                new_segments.append(segment)
                continue
            seg_copy = dict(segment)
            seg_text, seg_counts = redact_text(segment.get("text"))
            if seg_text is not None:
                seg_copy["text"] = seg_text
            new_segments.append(seg_copy)
            for key, value in seg_counts.items():
                total[key] += value
        redacted_event["segments"] = new_segments

    return redacted_event, total

