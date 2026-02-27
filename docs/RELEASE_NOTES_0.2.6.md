# ToneSight NS8 `0.2.6` Release Notes

Date: `2026-02-27`

This release delivers the v0.2.6 multi-domain signal layer as an additive, deterministic extension while keeping NS8 core math/spec unchanged (`spec_version: 1.0`).

## Scope Delivered

### Phase 1 - Canonical contracts and domain-pack docs

- Added canonical signal-layer schemas:
  - `schemas/signal_observation.schema.json`
  - `schemas/mapping_profile.schema.json`
  - `schemas/anchor_event.schema.json`
  - `schemas/signal_quarantine_event.schema.json`
- Added spec/docs:
  - `docs/NS8_MULTI_DOMAIN_SPEC.md`
  - `docs/DOMAIN_PACKS.md`
- Established explicit deterministic quarantine contract with reason codes:
  - `MISSING_CHANNEL`
  - `OUT_OF_RANGE`
  - `PROFILE_MISMATCH`

### Phase 2 - Deterministic profile loader and signal mapping engine

- Added deterministic domain-pack/profile loading:
  - `src/tonesight_ns8/domainpacks.py`
  - built-in profiles under `src/tonesight_ns8/domainpacks_data/`
- Added deterministic signal mapping engine:
  - `src/tonesight_ns8/signal_mapping.py`
- Implemented v0.2.6 composition mode:
  - `multi_channel_fold` only

### Phase 3 - Anchor events, metrics, and quarantine artifacts

- Added deterministic signal runner:
  - `src/tonesight_ns8/signal_runner.py`
- Signal runs now write additive artifacts:
  - `anchor_events.jsonl`
  - `metrics_summary.json`
  - `transition_matrix.json`
  - `density_map.json`
  - `quarantine.jsonl` (when rejects exist)
- Added additive receipt quarantine rollups:
  - `quarantine_count_total`
  - `quarantine_counts_by_reason`
  - `quarantine_artifact_path`
  - `quarantine_artifact_hash`

### Phase 4 - Domain pack v1 rollout and vectors

- Added built-in packs:
  - `tone_vad_v1`
  - `kasbah_env_v1`
- Added deterministic vectors and tests:
  - `tests/vectors/domainpacks/...`
  - `tests/test_domainpack_vectors.py`

### Phase 5 - CLI, receipts, and UI-safe artifact integration

- Added signal CLI commands:
  - `signal-map`
  - `signal-run`
- Extended run index/report integration for signal-mode runs as additive fields.
- Extended UI allowlists for signal-layer and quarantine summary metadata:
  - `ui/src/contracts.ts`
  - `docs/UI_ALLOWED_CONTRACTS.md`
- Preserved UI read-only contract and no UI-side recomputation boundary.

## Claim Boundary

- NS8 core formulas/transforms were not changed.
- Signal layer is additive and deterministic.
- Quarantine reporting is contract-safe and summary-oriented for UI surfaces.
- Compare/gate compatibility for existing eval mode remains preserved.

## Version Sync

- Package version in `pyproject.toml`: `0.2.6`
- Observability API app version: `0.2.6`
- README version target updated to `0.2.6`

## Validation Snapshot

- `python -m pytest -q` (`260 passed`)
- Targeted signal-layer suites passed during implementation:
  - mapping/domainpack vectors
  - signal runner + quarantine contract
  - CLI/index/report/UI allowlist integration
