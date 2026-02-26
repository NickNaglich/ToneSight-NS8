# ToneSight NS8 `0.2.5` Release Notes

Date: `2026-02-26`

This release completes the `v0.2.5` read-only artifact UI track while preserving deterministic NS8 core behavior and existing artifact contracts.

## Scope Delivered

### Phase 1 - File layout + run index JSON generator

- Added `ui/` and `server/` scaffolding for explicit UI/API boundaries.
- Added deterministic JSON index bridge from `runs/index.jsonl` to `runs/index.json`:
  - `run_index_json(...)`
  - CLI: `index-runs-json`
  - tool: `tools/generate_run_index_json.py`

### Phase 2 - Minimal static artifact API

- Added read-only local artifact API: `server/app.py`
- Routes:
  - `/health`
  - `/api/index`
  - `/api/run/{run_id}/receipt`
  - `/api/run/{run_id}/summary`
  - `/api/run/{run_id}/report`
  - `/api/compare/{run_a}/{run_b}`
  - `/api/gate/{run_a}/{run_b}`
- API serves existing artifacts only; no scoring/compare/gate recomputation.

### Phase 3 - UI contract allowlists

- Added contract policy doc: `docs/UI_ALLOWED_CONTRACTS.md`
- Added UI allowlist constants: `ui/src/contracts.ts`
- Added enforcement tests: `tests/test_ui_allowed_contracts.py`
- Updated privacy/retention docs with explicit UI exposure boundary.

### Phase 4 - 2-minute drift/gate demo

- Added demo script: `scripts/demo_ui_drift_gate_2min.ps1`
- Added recipe: `docs/RECIPES/ui_drift_gate_demo.md`
- Added minimal UI entry page: `ui/index.html`
- Added smoke test: `tests/test_ui_demo_script.py`

## Claim Boundary

- UI remains read-only over deterministic artifacts.
- No new NS8 formulas/transforms/validation semantics were introduced.
- No new model-quality claims were added; outputs remain conformance telemetry.

## Version Sync

- Package version in `pyproject.toml`: `0.2.5`
- Observability API app version: `0.2.5`
- README version target updated to `0.2.5`

## Validation Snapshot

- `python -m pytest -q`
- `python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json`
- `python -m tonesight_ns8.cli index-runs --out-root runs`
- `python -m tonesight_ns8.cli index-runs-json --out-root runs`
- `powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -SkipServers`
