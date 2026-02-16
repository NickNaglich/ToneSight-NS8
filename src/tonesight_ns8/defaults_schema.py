"""Shared schema validation for config/defaults.json."""

from __future__ import annotations

from typing import Any


def _expect_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be object")
    return value


def _expect_str(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be string")
    return value


def _expect_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be int")
    return value


def _expect_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be bool")
    return value


def _expect_nullable_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be string or null")
    return value


def validate_defaults_payload(payload: Any) -> dict[str, dict[str, Any]]:
    _expect_str(payload.get("spec_version"), "spec_version")
    eval_defaults = _expect_dict(payload.get("eval_defaults"), "eval_defaults")
    artifact_defaults = _expect_dict(payload.get("artifact_defaults"), "artifact_defaults")

    return {
        "eval": {
            "out_root": _expect_str(eval_defaults.get("out_root"), "eval_defaults.out_root"),
            "taxonomy_path": _expect_str(eval_defaults.get("taxonomy_path"), "eval_defaults.taxonomy_path"),
            "threshold_l1": _expect_int(eval_defaults.get("threshold_l1"), "eval_defaults.threshold_l1"),
            "calibration_path": _expect_nullable_str(eval_defaults.get("calibration_path"), "eval_defaults.calibration_path"),
            "capture_gpu": _expect_bool(eval_defaults.get("capture_gpu"), "eval_defaults.capture_gpu"),
            "mlflow_tracking_uri": _expect_nullable_str(
                eval_defaults.get("mlflow_tracking_uri"), "eval_defaults.mlflow_tracking_uri"
            ),
        },
        "artifacts": {
            "vectors_path": _expect_str(artifact_defaults.get("vectors_path"), "artifact_defaults.vectors_path"),
            "taxonomy_path": _expect_str(artifact_defaults.get("taxonomy_path"), "artifact_defaults.taxonomy_path"),
            "goldset_path": _expect_str(artifact_defaults.get("goldset_path"), "artifact_defaults.goldset_path"),
        },
    }
