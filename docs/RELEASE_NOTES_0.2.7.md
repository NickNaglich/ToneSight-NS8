# ToneSight NS8 `0.2.7` Release Notes

Date: `2026-03-02`

This release focuses on packaging robustness and API usability clarifications while preserving NS8 core math/spec behavior (`spec_version: 1.0`).

## Highlights

### 1) Installed-package portability hardening

- Added packaged defaults fallback:
  - `src/tonesight_ns8/defaults_data/defaults.json`
- Updated defaults resolution to prefer:
  - explicit path argument
  - `TONESIGHT_DEFAULTS_PATH`
  - repo `config/defaults.json` (when present)
  - packaged defaults fallback
- Included packaged JSON data in distribution artifacts:
  - `pyproject.toml` package-data for `defaults_data/*.json` and `domainpacks_data/*.json`

### 2) Vector-regeneration governance guardrails

- `tools/regen_vectors.py` now supports:
  - `--check` (non-mutating oracle drift validation for CI/release gates)
  - `--authorize` (required for mutation)
- Regeneration is blocked unless governance prerequisites are met
  (spec bump + change log + phase-plan authorization marker).
- CI switched to non-mutating vector stability checks using `--check`.

### 3) API usability and naming clarity

- Added explicit wrapper names:
  - `tonesight_receipt_from_vad_context(...)`
  - `tonesight_receipt_from_label_context(...)`
- Kept backward-compatible aliases:
  - `tonesight_from_vad(...)` (deprecated alias)
  - `tonesight_from_label(...)` (deprecated alias)
- CLI now uses explicit non-deprecated entrypoints.
- Docs now explicitly state:
  - anchor `A` is derived from NS8 route inputs (`family/r/c/k`)
  - VAD/label in these wrappers are receipt context fields

### 4) Packaging metadata cleanup

- Updated package version:
  - `pyproject.toml`: `0.2.7`
- Updated observability API app version:
  - `src/tonesight_ns8/observability_api.py`: `0.2.7`
- Updated `pyproject.toml` license metadata to SPDX string form (`"MIT"`) to avoid future setuptools deprecation breakage.

## Validation Snapshot

- `python tools/validate_defaults.py`
- `python tools/validate_defaults.py tests/fixtures/defaults.invalid.json` (expected failure)
- `python tools/check_nosec_policy.py`
- `python -m bandit -r src` (no issues identified)
- `python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json` (`decision=passed`)
- `python tools/regen_vectors.py --check`
- `python -m pytest -q` (`263 passed`)
- `python -m build`
- `python -m twine check dist/*` (passed)
- `python -m tonesight_ns8.cli --help`
