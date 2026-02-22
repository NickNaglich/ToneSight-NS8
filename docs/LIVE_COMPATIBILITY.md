# Live Compatibility Contract

This document defines deterministic compatibility checks for comparing two runs in live/shadow workflows.

## Purpose

Before comparing metrics, ToneSight must confirm both runs were produced under compatible contracts. If contracts differ, gate decisions are marked `incompatible`.

## Compatibility Fields

The gate/compare compatibility layer checks:

- `spec_version`
- `mapping_id`
- `mapping_version`
- taxonomy identity
- calibration identity
- defaults schema identity
- dataset identity (required by default; can be explicitly relaxed)

## Field Resolution Rules

### Taxonomy identity

Resolved from:

1. `receipt.taxonomy_hash` (preferred)
2. `receipt.taxonomy_path` fallback

### Calibration identity

Resolved from:

1. `receipt.calibration_hash` (preferred)
2. `receipt.config.calibration_hash`
3. `receipt.calibration_path`
4. `receipt.config.calibration_path`
5. empty string (treated as "no calibration")

### Defaults schema identity

Resolved from:

1. `receipt.defaults_spec_version` (preferred)
2. `receipt.config.defaults_spec_version`
3. empty string (legacy fallback)

## Dataset Identity

By default, dataset identity must match:

- `receipt.dataset_hash`

This can be relaxed when intentionally comparing different streams:

```bash
python -m tonesight_ns8.cli gate \
  --run runs/new \
  --baseline runs/base \
  --allow-dataset-mismatch
```

## Incompatibility Output

When compatibility fails, gate output includes:

- `decision: "incompatible"`
- `exit_code: 3`
- `incompatibilities`: deterministic reason list

Common reason codes:

- `spec_version_mismatch`
- `mapping_id_mismatch`
- `mapping_version_mismatch`
- `taxonomy_identity_mismatch`
- `calibration_identity_mismatch`
- `defaults_schema_version_mismatch`
- `dataset_hash_mismatch`

## Policy Reference

Canonical identity stability and migration rules are defined in:
- `docs/CANONICAL_ID_POLICY.md`
