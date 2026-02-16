"""Run eval and compare against previous compatible run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare
from .defaults import EVAL_DEFAULTS
from .eval_runner import run_eval


def _find_previous_run(out_root: Path, dataset_hash: str, current_run_id: str) -> Path | None:
    candidates: list[Path] = []
    for child in out_root.iterdir():
        if not child.is_dir():
            continue
        if child.name == current_run_id:
            continue
        receipt = child / "receipt.json"
        if not receipt.exists():
            continue
        try:
            payload = json.loads(receipt.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("dataset_hash") == dataset_hash:
            candidates.append(child)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def run_eval_compare(
    goldset_path: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    threshold_l1: int = EVAL_DEFAULTS["threshold_l1"],
    calibration_path: str | None = EVAL_DEFAULTS["calibration_path"],
    capture_gpu: bool = EVAL_DEFAULTS["capture_gpu"],
    mlflow_tracking_uri: str | None = EVAL_DEFAULTS["mlflow_tracking_uri"],
    top_n: int = 10,
) -> dict[str, Any]:
    eval_result = run_eval(
        goldset_path=goldset_path,
        out_root=out_root,
        taxonomy_path=taxonomy_path,
        threshold_l1=threshold_l1,
        calibration_path=calibration_path,
        capture_gpu=capture_gpu,
        mlflow_tracking_uri=mlflow_tracking_uri,
    )
    dataset_hash = eval_result["receipt"]["dataset_hash"]
    run_id = eval_result["run_id"]
    out_root_path = Path(out_root)
    current_run_path = out_root_path / run_id
    previous = _find_previous_run(out_root_path, dataset_hash, run_id)
    compare_result = None
    if previous is not None:
        compare_result = run_compare(str(previous), str(current_run_path), top_n=top_n, write_artifact=True)
    return {
        "eval": eval_result,
        "previous_run": str(previous) if previous is not None else None,
        "compare": compare_result,
    }
