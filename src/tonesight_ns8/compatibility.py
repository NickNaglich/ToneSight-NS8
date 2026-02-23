"""Shared compatibility checks for run artifact receipts."""

from __future__ import annotations

from typing import Any


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _receipt_config(receipt: dict[str, Any]) -> dict[str, Any]:
    raw = receipt.get("config")
    if isinstance(raw, dict):
        return raw
    return {}


def identity_fields(receipt: dict[str, Any]) -> dict[str, str]:
    """Extract normalized identity fields used by compare/gate/eval-compare."""
    config = _receipt_config(receipt)
    spec_version = _as_str(receipt.get("spec_version"))
    mapping_id = _as_str(receipt.get("mapping_id") or config.get("mapping_id") or "ns8")
    mapping_version = _as_str(receipt.get("mapping_version") or config.get("mapping_version") or spec_version)
    taxonomy_identity = _as_str(receipt.get("taxonomy_hash") or config.get("taxonomy_path"))
    calibration_identity = _as_str(config.get("calibration_path"))
    defaults_schema_version = _as_str(
        receipt.get("defaults_spec_version") or config.get("defaults_spec_version") or receipt.get("defaults_hash")
    )
    dataset_hash = _as_str(receipt.get("dataset_hash"))
    return {
        "spec_version": spec_version,
        "mapping_id": mapping_id,
        "mapping_version": mapping_version,
        "taxonomy_identity": taxonomy_identity,
        "calibration_identity": calibration_identity,
        "defaults_schema_version": defaults_schema_version,
        "dataset_hash": dataset_hash,
    }


def compatibility_issues(
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    require_dataset_match: bool = True,
) -> list[dict[str, str]]:
    """Return deterministic compatibility mismatch payloads."""
    fields_expected = identity_fields(expected)
    fields_actual = identity_fields(actual)
    issues: list[dict[str, str]] = []

    if require_dataset_match and fields_expected["dataset_hash"] != fields_actual["dataset_hash"]:
        issues.append(
            {
                "reason": "dataset_hash_mismatch",
                "expected_dataset_hash": fields_expected["dataset_hash"],
                "actual_dataset_hash": fields_actual["dataset_hash"],
            }
        )

    reason_by_field = {
        "spec_version": "spec_version_mismatch",
        "mapping_id": "mapping_id_mismatch",
        "mapping_version": "mapping_version_mismatch",
        "taxonomy_identity": "taxonomy_identity_mismatch",
        "calibration_identity": "calibration_identity_mismatch",
        "defaults_schema_version": "defaults_schema_version_mismatch",
    }
    for field in (
        "spec_version",
        "mapping_id",
        "mapping_version",
        "taxonomy_identity",
        "calibration_identity",
        "defaults_schema_version",
    ):
        if fields_expected[field] != fields_actual[field]:
            issues.append(
                {
                    "reason": reason_by_field[field],
                    "field": field,
                    "expected": fields_expected[field],
                    "actual": fields_actual[field],
                }
            )
    return issues

