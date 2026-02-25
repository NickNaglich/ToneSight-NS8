"""Deterministic coding-agent feature extraction from LiveEvent payloads."""

from __future__ import annotations

import re
from typing import Any

_COMMENT_RE = re.compile(r"^\s*(#|//|/\*|\*|--)\b")
_IMPORT_RE = re.compile(r"^\s*(import |from .* import |require\(|use |#include )")
_TEST_MARKER_RE = re.compile(r"\b(pytest|unittest|jest|vitest|go test|cargo test|test_)\b", re.IGNORECASE)
_ERROR_MARKER_RE = re.compile(r"\b(except|catch|finally|result<|err\(|panic!|raise)\b", re.IGNORECASE)
_DIFF_RE = re.compile(r"(^diff --git|^@@|^\+\+\+ |^--- )", re.MULTILINE)


def _event_text(event: dict[str, Any]) -> str:
    text = event.get("text")
    if isinstance(text, str) and text.strip():
        return text
    segments = event.get("segments")
    if isinstance(segments, list) and segments:
        parts = [str(seg.get("text", "")).strip() for seg in segments if isinstance(seg, dict)]
        merged = " ".join(part for part in parts if part)
        if merged:
            return merged
    raise ValueError("coding_agent adapter requires non-empty text or segments[].text")


def _normalize_language(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    raw = value.strip().lower()
    aliases = {
        "py": "python",
        "python": "python",
        "ts": "typescript",
        "tsx": "typescript",
        "typescript": "typescript",
        "js": "javascript",
        "javascript": "javascript",
        "rs": "rust",
        "rust": "rust",
        "go": "go",
        "golang": "go",
    }
    return aliases.get(raw, raw)


def detect_language(text: str) -> str:
    lower = text.lower()
    scores = {
        "python": 0,
        "typescript": 0,
        "javascript": 0,
        "rust": 0,
        "go": 0,
    }
    if "def " in lower or "import " in lower or "except " in lower:
        scores["python"] += 2
    if "async def " in lower or "dataclass" in lower:
        scores["python"] += 1
    if "interface " in lower or "type " in lower or ": string" in lower:
        scores["typescript"] += 2
    if "const " in lower or "let " in lower or "=>" in lower:
        scores["typescript"] += 1
        scores["javascript"] += 1
    if "function " in lower and "{" in lower:
        scores["javascript"] += 1
    if "fn " in lower or "let mut " in lower or "-> result" in lower:
        scores["rust"] += 2
    if "match " in lower or "serde" in lower:
        scores["rust"] += 1
    if "func " in lower or "package " in lower:
        scores["go"] += 2
    if "fmt." in lower or "go test" in lower:
        scores["go"] += 1

    winner = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0]
    if winner[1] <= 0:
        return "unknown"
    return winner[0]


def extract_coding_agent_features(event: dict[str, Any]) -> dict[str, Any]:
    text = _event_text(event)
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]

    meta = event.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    expected_language = _normalize_language(meta.get("expected_language") or meta.get("lang_expected"))
    detected_language = detect_language(text)
    mismatch = int(bool(expected_language) and detected_language != "unknown" and detected_language != expected_language)

    tool_calls = meta.get("tool_calls")
    if isinstance(tool_calls, list):
        tool_call_count = len(tool_calls)
    elif isinstance(tool_calls, int):
        tool_call_count = max(0, int(tool_calls))
    else:
        tool_call_count = 0

    comment_lines = [line for line in non_empty_lines if _COMMENT_RE.search(line)]
    comment_ratio = (len(comment_lines) / len(non_empty_lines)) if non_empty_lines else 0.0

    return {
        "response_lines": len(non_empty_lines),
        "code_fence_count": text.count("```"),
        "diff_present": int(bool(_DIFF_RE.search(text))),
        "imports_count": sum(1 for line in non_empty_lines if _IMPORT_RE.search(line)),
        "test_markers": len(_TEST_MARKER_RE.findall(text)),
        "error_handling_markers": len(_ERROR_MARKER_RE.findall(text)),
        "comment_ratio_approx": round(comment_ratio, 4),
        "lang_detected": detected_language,
        "lang_expected": expected_language,
        "lang_mismatch": mismatch,
        "tool_call_count": tool_call_count,
    }

