# Canonical Telemetry ID Policy

This document defines canonical identity fields for ToneSight run artifacts and the stability/compatibility rules used by compare and gate workflows.

## Scope

Applies to deterministic run receipts and compatibility checks across:
- `eval`
- `eval-compare`
- `compare`
- `gate`
- live replay/canary flows that emit standard receipt artifacts

## Canonical Identity Fields

Required identity fields in receipt-level compatibility:
- `spec_version`
- `dataset_hash` (required by default; optional bypass for live comparisons)
- `mapping_id`
- `mapping_version`
- taxonomy identity (`taxonomy_hash` preferred; `taxonomy_path` fallback)
- calibration identity (`config.calibration_path`, empty string when absent)
- defaults schema identity (`defaults_spec_version` preferred; `defaults_hash` fallback)

Operational trace fields (informational):
- `run_id`
- `created_at_utc`
- runtime metadata under `runtime.*`

## Stability Guarantees (Major Version)

Within a major release line:
- identity field names and compatibility semantics are contract-stable
- compatibility reason codes are stable for deterministic gate decisions
- the same pair of receipts yields the same incompatibility result

## Breaking Change Policy

A change is breaking if it modifies:
- required compatibility identity fields
- field-resolution precedence
- mismatch reason-code semantics

Breaking changes require:
1. explicit version update and release notes
2. compatibility migration guidance
3. test updates that codify new behavior

## Migration Guidance

When introducing a new identity field:
- keep previous fields accepted for at least one major compatibility window
- document precedence and fallback behavior
- add deterministic tests for mixed old/new receipt shapes

When deprecating a field:
- preserve deterministic fallback until next major version
- publish deprecation timeline in release docs

## Enforcement

Primary enforcement points:
- `src/tonesight_ns8/eval_runner.py` (identity emission in receipts)
- `src/tonesight_ns8/gate_runner.py` (compatibility checks and mismatch reasons)
- `src/tonesight_ns8/compare_runner.py` (run-level provenance in compare payloads)

Normative tests:
- `tests/test_canonical_id_policy.py`
- `tests/test_gate_runner.py`
- `tests/test_live_compare_compatibility.py`
