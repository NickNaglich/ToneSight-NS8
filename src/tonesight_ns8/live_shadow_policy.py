"""Shadow strictness policy handlers for live-event validation outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def apply_shadow_policy(
    *,
    mode: str,
    valid_events: list[dict[str, Any]],
    invalid_events: list[dict[str, Any]],
    quarantine_path: str | None = None,
) -> dict[str, Any]:
    """Apply fail/drop/quarantine handling to invalid live events."""
    selected_mode = str(mode).strip().lower()
    if selected_mode not in {"fail", "drop", "quarantine"}:
        raise ValueError("mode must be one of: fail, drop, quarantine")

    result = {
        "mode": selected_mode,
        "accepted_count": len(valid_events),
        "invalid_count": len(invalid_events),
        "quarantined_count": 0,
        "quarantine_path": None,
    }

    if selected_mode == "fail" and invalid_events:
        first = invalid_events[0]
        code = first.get("error", {}).get("code", "invalid_event")
        message = first.get("error", {}).get("message", "invalid event encountered")
        raise ValueError(f"shadow policy fail: {code}: {message}")

    if selected_mode == "quarantine":
        target = Path(quarantine_path) if quarantine_path else Path("runs/live_quarantine/quarantine.jsonl")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(json.dumps(row, ensure_ascii=True) for row in invalid_events) + ("\n" if invalid_events else "")
        target.write_text(payload, encoding="utf-8")
        result["quarantined_count"] = len(invalid_events)
        result["quarantine_path"] = str(target)

    return result

