"""Shared compatibility checks for run artifact receipts."""

from __future__ import annotations

import json
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


def _canonical_generation_identity(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


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
    provider = _as_str(receipt.get("provider") or config.get("provider"))
    model_tag = _as_str(receipt.get("model_tag") or config.get("model_tag"))
    model_identity = _as_str(
        receipt.get("model_digest")
        or config.get("model_digest")
        or receipt.get("model_version")
        or config.get("model_version")
    )
    generation_identity = _canonical_generation_identity(
        receipt.get("generation_settings") or config.get("generation_settings")
    )
    return {
        "spec_version": spec_version,
        "mapping_id": mapping_id,
        "mapping_version": mapping_version,
        "taxonomy_identity": taxonomy_identity,
        "calibration_identity": calibration_identity,
        "defaults_schema_version": defaults_schema_version,
        "dataset_hash": dataset_hash,
        "provider": provider,
        "model_tag": model_tag,
        "model_identity": model_identity,
        "generation_identity": generation_identity,
    }


def compatibility_issues(
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    require_dataset_match: bool = True,
    require_pinned_model_identity: bool = False,
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

    if require_pinned_model_identity:
        for field in ("provider", "model_tag", "model_identity", "generation_identity"):
            if not fields_expected[field] or not fields_actual[field]:
                issues.append(
                    {
                        "reason": "pinned_model_identity_missing",
                        "field": field,
                        "expected": fields_expected[field],
                        "actual": fields_actual[field],
                    }
                )
        if fields_expected["provider"] and fields_actual["provider"] and fields_expected["provider"] != fields_actual["provider"]:
            issues.append(
                {
                    "reason": "provider_mismatch",
                    "field": "provider",
                    "expected": fields_expected["provider"],
                    "actual": fields_actual["provider"],
                }
            )
        if (
            fields_expected["model_identity"]
            and fields_actual["model_identity"]
            and fields_expected["model_identity"] != fields_actual["model_identity"]
        ):
            issues.append(
                {
                    "reason": "model_identity_mismatch",
                    "field": "model_identity",
                    "expected": fields_expected["model_identity"],
                    "actual": fields_actual["model_identity"],
                }
            )
        if (
            fields_expected["generation_identity"]
            and fields_actual["generation_identity"]
            and fields_expected["generation_identity"] != fields_actual["generation_identity"]
        ):
            issues.append(
                {
                    "reason": "generation_identity_mismatch",
                    "field": "generation_identity",
                    "expected": fields_expected["generation_identity"],
                    "actual": fields_actual["generation_identity"],
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
