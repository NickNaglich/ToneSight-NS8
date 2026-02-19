"""Run eval and compare against previous compatible run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compare_runner import run_compare
from .defaults import EVAL_DEFAULTS
from .eval_runner import run_eval


def _find_previous_run(
    out_root: Path,
    dataset_hash: str,
    spec_version: str,
    current_run_id: str,
) -> tuple[Path | None, list[dict[str, str]], str | None]:
    candidates: list[tuple[Path, dict[str, Any]]] = []
    incompatible: list[dict[str, str]] = []
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
        candidates.append((child, payload))
    if not candidates:
        return None, incompatible, "no_prior_runs"

    candidates.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    for path, payload in candidates:
        receipt_dataset_hash = str(payload.get("dataset_hash", ""))
        receipt_spec_version = str(payload.get("spec_version", ""))
        if receipt_dataset_hash != dataset_hash:
            incompatible.append(
                {
                    "run_path": str(path),
                    "reason": "dataset_hash_mismatch",
                    "expected_dataset_hash": dataset_hash,
                    "actual_dataset_hash": receipt_dataset_hash,
                }
            )
            continue
        if receipt_spec_version != spec_version:
            incompatible.append(
                {
                    "run_path": str(path),
                    "reason": "spec_version_mismatch",
                    "expected_spec_version": spec_version,
                    "actual_spec_version": receipt_spec_version,
                }
            )
            continue
        return path, incompatible, None
    return None, incompatible, "no_compatible_prior_run"


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
    spec_version = str(eval_result["receipt"]["spec_version"])
    run_id = eval_result["run_id"]
    out_root_path = Path(out_root)
    current_run_path = out_root_path / run_id
    previous, incompatible_runs, compare_skipped_reason = _find_previous_run(
        out_root_path, dataset_hash, spec_version, run_id
    )
    compare_result = None
    if previous is not None:
        compare_result = run_compare(str(previous), str(current_run_path), top_n=top_n, write_artifact=True)
        compare_skipped_reason = None
    return {
        "eval": eval_result,
        "previous_run": str(previous) if previous is not None else None,
        "incompatible_previous_runs": incompatible_runs,
        "compare_skipped_reason": compare_skipped_reason,
        "compare": compare_result,
    }
