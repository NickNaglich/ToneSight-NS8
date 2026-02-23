"""Provenance helpers for deterministic artifact receipts."""

from __future__ import annotations

import subprocess  # nosec B404


def get_code_revision() -> str | None:
    """Return short git revision for current workspace, or None when unavailable."""
    try:
        proc = subprocess.run(  # nosec B603
            ["git", "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    revision = proc.stdout.strip()
    return revision or None

