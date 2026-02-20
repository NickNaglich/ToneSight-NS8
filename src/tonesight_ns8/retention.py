"""Deterministic retention purge helpers for local run artifacts."""

from __future__ import annotations

import shutil
import time
import stat
from pathlib import Path
from typing import Any


def _latest_mtime(path: Path) -> float:
    latest = path.stat().st_mtime
    if path.is_dir():
        for child in path.rglob("*"):
            try:
                latest = max(latest, child.stat().st_mtime)
            except FileNotFoundError:
                continue
    return latest


def _iter_candidates(out_root: Path) -> list[Path]:
    candidates: list[Path] = []
    if not out_root.exists():
        return candidates
    for child in sorted(out_root.iterdir(), key=lambda p: p.name):
        if child.is_dir() and (child.name.startswith("run_") or child.name.startswith("run_live_")):
            candidates.append(child)
    captures = out_root / "captures"
    if captures.exists() and captures.is_dir():
        for capture_dir in sorted(captures.iterdir(), key=lambda p: p.name):
            if capture_dir.is_dir():
                candidates.append(capture_dir)
    return candidates


def _on_rmtree_error(func: Any, path: str, exc_info: Any) -> None:
    """Best-effort Windows-safe retry for read-only files."""
    try:
        os_path = Path(path)
        os_path.chmod(stat.S_IWRITE)
        func(path)
    except Exception:
        raise exc_info[1]


def run_retention_purge(
    *,
    out_root: str,
    older_than_days: int,
    dry_run: bool = True,
    include_bundles: bool = False,
    include_captures: bool = False,
) -> dict[str, Any]:
    """Purge old run/capture artifacts with explicit safety controls."""
    if older_than_days < 0:
        raise ValueError("older_than_days must be >= 0")

    root = Path(out_root)
    now = time.time()
    cutoff_seconds = older_than_days * 86400

    evaluated: list[dict[str, Any]] = []
    delete_targets: list[Path] = []

    for candidate in _iter_candidates(root):
        rel = candidate.relative_to(root).as_posix()
        is_capture = rel.startswith("captures/")
        if is_capture and not include_captures:
            evaluated.append({"path": str(candidate), "action": "skip", "reason": "capture_not_included"})
            continue

        if not include_bundles and (candidate / "bundles").exists():
            evaluated.append({"path": str(candidate), "action": "skip", "reason": "contains_bundles"})
            continue

        age_seconds = now - _latest_mtime(candidate)
        age_days = age_seconds / 86400.0
        if age_seconds < cutoff_seconds:
            evaluated.append({"path": str(candidate), "action": "keep", "age_days": age_days})
            continue

        evaluated.append({"path": str(candidate), "action": "delete", "age_days": age_days})
        delete_targets.append(candidate)

    deleted: list[str] = []
    failed: list[dict[str, str]] = []
    if not dry_run:
        for target in delete_targets:
            try:
                shutil.rmtree(target, onerror=_on_rmtree_error)
            except FileNotFoundError:
                pass
            except OSError as exc:
                failed.append({"path": str(target), "error": str(exc)})
                continue
            if not target.exists():
                deleted.append(str(target))
            else:
                failed.append({"path": str(target), "error": "path_still_exists_after_delete"})

    return {
        "out_root": str(root),
        "older_than_days": older_than_days,
        "dry_run": dry_run,
        "include_bundles": include_bundles,
        "include_captures": include_captures,
        "evaluated": evaluated,
        "would_delete_count": len(delete_targets),
        "deleted_count": len(deleted),
        "deleted_paths": deleted,
        "failed_count": len(failed),
        "failed_paths": failed,
    }
