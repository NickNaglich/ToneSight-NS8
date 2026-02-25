# ToneSight NS8 `0.2.3` Release Notes

Release date: `2026-02-25`

This release delivers deterministic coding-agent behavioral telemetry support and pinned-model compatibility gating across v0.2.3 Phases 1-4.

## Highlights

- Added coding-agent live adapter path for deterministic replay/verify:
  - `live-replay --adapter coding_agent`
  - `live-verify --adapter coding_agent`
  - deterministic event transform: `LiveEvent -> coding_agent_features -> 1..8 bins -> NS8-compatible VAD`
- Added coding-agent telemetry modules:
  - `coding_agent_features.py`
  - `coding_agent_discretize.py`
  - `coding_agent_adapter.py`
- Added pinned model identity support in receipts and compatibility checks:
  - receipt fields: `provider`, `model_tag`, `model_digest`/`model_version`, `generation_settings`, `capture_schema_version`
  - optional compare/gate enforcement via `require_pinned_model_identity`
  - new gate profile: `coding_agent_drift`
  - CLI flag: `gate --require-pinned-model-identity`
- Added deterministic coding-agent drift benchmark suite:
  - `benchmark --suite coding_agent_drift`
  - artifacts:
    - `runs/benchmarks/coding_agent_drift/evidence.json`
    - `runs/benchmarks/coding_agent_drift/report.json`
- Added pinned coding-agent fixture corpus and end-to-end compatibility tests for `compare/gate/report`.

## Claim Boundary Notes

- This release adds deterministic behavioral consistency telemetry for coding-agent outputs.
- It does not add code correctness scoring or cognition/emotion inference claims.

## Version metadata updates

- Package version set to `0.2.3` in `pyproject.toml`.
- Observability API app version set to `0.2.3`.
- README version target updated to `0.2.3`.

## Validation

- `python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json`
- `python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl`
- `python -m tonesight_ns8.cli benchmark --suite coding_agent_drift --out-root runs --coding-baseline-events tests/fixtures/live_event.coding_agent.python.jsonl --coding-candidate-events tests/fixtures/live_event.coding_agent.typescript.jsonl,tests/fixtures/live_event.coding_agent.mismatch.jsonl`
- `python -m pytest -q`
