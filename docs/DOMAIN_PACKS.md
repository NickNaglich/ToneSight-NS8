# Domain Packs (Draft for v0.2.6)

Purpose:
- define versioned deterministic bundles that map domain channels into NS8-compatible signal-layer artifacts.

A domain pack bundles:
- mapping profile definitions
- channel constraints
- deterministic composition mode configuration
- metric defaults
- vector fixtures

## v0.2.6 target packs

1. `tone_vad_v1`
- goal: preserve ToneSight VAD compatibility under signal-layer contracts.
- channel style: discrete V/A/D bins.

2. `kasbah_env_v1`
- goal: baseline environmental telemetry mapping (for example temperature/humidity/noise bins).
- channel style: bounded discrete bins.

## Pack Contract Requirements

- pack metadata includes stable `name`, `version`, and deterministic hash.
- profile references and channel definitions must be schema-valid.
- missing required channels and out-of-range values are deterministic rejects (no silent correction).

## Composition Mode (v0.2.6)

Supported:
- `multi_channel_fold`

Deferred:
- additional composition modes (for example weighted blend) to `v0.2.7+`.

## Validation Requirements

- vector tests for expected anchors and strict reject paths.
- replay reproducibility checks for identical input/profile/params.
- explicit quarantine reason coverage:
  - `MISSING_CHANNEL`
  - `OUT_OF_RANGE`
  - `PROFILE_MISMATCH`

## Artifact Expectations

Signal runs built from domain packs must produce deterministic artifacts:
- `anchor_events.jsonl`
- `metrics_summary.json`
- `transition_matrix.json`
- `density_map.json`
- `quarantine.jsonl` (when rejects occur)
- `receipt.json` with profile/pack hashes and quarantine rollups
