"""Provenance helpers for deterministic artifact receipts."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404


def get_code_revision() -> str | None:
    """Return short git revision for current workspace, or None when unavailable."""
    git_executable = shutil.which("git")
    if not git_executable:
        return None
    try:
        proc = subprocess.run(  # nosec B603
            [git_executable, "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    revision = proc.stdout.strip()
    return revision or None
