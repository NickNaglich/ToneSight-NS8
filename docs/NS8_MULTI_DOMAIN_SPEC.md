# NS8 Multi-Domain Signal Spec (v0.2.6)

Status:
- execution target: `v0.2.6`
- implementation state: `planned`

Purpose:
- define additive deterministic contracts for mapping multi-domain discrete telemetry into NS8-compatible anchor artifacts.
- preserve NS8 core math and strict-validation behavior defined in `docs/SPEC_NS8.md`.

Normative boundaries:
- NS8 core formulas/transforms are unchanged in this draft.
- this spec defines signal-layer contracts only (observation/profile/anchor/quarantine artifacts).
- no stochastic behavior, no hidden fallback, no silent imputation.

## Canonical Contracts (v1)

- `ns8.signal.observation.v1`
- `ns8.mapping.profile.v1`
- `ns8.signal.anchor_event.v1`
- `ns8.signal.quarantine_event.v1`

Authoritative schema files:
- `schemas/signal_observation.schema.json`
- `schemas/mapping_profile.schema.json`
- `schemas/anchor_event.schema.json`
- `schemas/signal_quarantine_event.schema.json`

## Determinism Rules

- same observations + mapping profile + parameters -> identical artifact content.
- mapping profiles are versioned and hash-addressable in receipts.
- missing required channels must fail deterministically (error/quarantine only).
- out-of-range channel values must fail deterministically (error/quarantine only).

## Quarantine Artifact Contract

Artifact path:
- `runs/<run_id>/quarantine.jsonl`

Required fields per row:
- `schema` (`ns8.signal.quarantine_event.v1`)
- `reason_code` (`MISSING_CHANNEL|OUT_OF_RANGE|PROFILE_MISMATCH`)
- `reason_detail`
- `observation_hash`
- `t`
- `entity_id`
- `mapping_profile`
- `mapping_profile_hash`
- `domain_pack`
- `domain_pack_hash`
- `run_id`

Privacy boundary:
- quarantine rows are metadata-only and deterministic.
- no raw payload expansion beyond schema-defined safe fields.

## Receipt Additions (Additive)

Signal-layer receipts may include:
- `mapping_profile`
- `mapping_profile_hash`
- `domain_pack`
- `domain_pack_hash`
- `quarantine_count_total`
- `quarantine_counts_by_reason`
- `quarantine_artifact_path`
- `quarantine_artifact_hash`

These are additive and must not break existing receipt consumers.
