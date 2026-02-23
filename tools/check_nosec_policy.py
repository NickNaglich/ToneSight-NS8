"""Enforce # nosec suppression policy for src/ Python files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
ALLOWLIST_PATH = ROOT / "tools" / "nosec_allowlist.json"

NOSEC_RE = re.compile(r"#\s*nosec\b", re.IGNORECASE)
REQUIRED_FORMAT_RE = re.compile(
    r"#\s*nosec(?:\s+B\d+(?:,\s*B\d+)*)?\s*-\s+.+\s+\[ref:\s*#\d+\]\s*$",
    re.IGNORECASE,
)


def _load_allowlist() -> set[tuple[str, str]]:
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    out: set[tuple[str, str]] = set()
    for entry in entries:
        path = str(entry["path"]).replace("\\", "/")
        line = str(entry["line"]).strip()
        out.add((path, line))
    return out


def _scan_nosec_lines() -> list[tuple[str, int, str]]:
    matches: list[tuple[str, int, str]] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, raw in enumerate(lines, start=1):
            line = raw.strip()
            if NOSEC_RE.search(line):
                matches.append((rel, idx, line))
    return matches


def main() -> int:
    allowlist = _load_allowlist()
    current = _scan_nosec_lines()

    failures: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    for rel, lineno, line in current:
        pair = (rel, line)
        seen_pairs.add(pair)
        if pair in allowlist:
            continue
        if REQUIRED_FORMAT_RE.search(line):
            continue
        failures.append(
            f"{rel}:{lineno}: new # nosec requires format "
            "'# nosec BXXX - <rationale> [ref:#<issue>]'"
        )

    stale_entries = sorted(allowlist.difference(seen_pairs))
    for rel, line in stale_entries:
        failures.append(f"{rel}: stale allowlist entry no longer present: {line}")

    if failures:
        print("NOSEC policy check failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("NOSEC policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
