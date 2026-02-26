# UI Drift + Gate Failure Demo (2 Minutes)

This recipe creates a deterministic baseline/candidate pair, writes compare and gate artifacts, refreshes UI index artifacts, and starts local API/UI servers.

## Command

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1
```

Dry-run without long-running servers:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1 -SkipServers
```

## What it does

1. Runs baseline eval (`threshold_l1=3`)
2. Runs candidate eval (`threshold_l1=0`) to force a deterministic gate regression signal
3. Writes compare artifact (`compare --write`)
4. Runs gate and persists `gate_result.json` under run comparison artifacts
5. Generates `index.jsonl` and `index.json`
6. Starts:
   - static artifact API (`server/app.py`)
   - static UI server (`python -m http.server --directory ui`)

## Evidence endpoints

- `GET /api/index`
- `GET /api/run/{run_id}/report-html`
- `GET /api/compare/{run_a}/{run_b}`
- `GET /api/compare-report/{run_a}/{run_b}`
- `GET /api/gate/{run_a}/{run_b}`
- UI entry: `/index.html`

All values shown are read from existing artifacts; no UI-side scoring is computed.

## 2-Minute Screenshot Flow

After running the script, use the printed direct links in this order:

1. `UI:` dashboard scan view (`/index.html`) with mixed statuses.
2. `UI detail:` candidate run detail (`?run=<candidate>&panel=detail`) for provenance and eval summary.
3. `UI compare:` compare evidence view (`?run=<candidate>&panel=compare`) for drift deltas from `compare_summary.json`.
4. `UI gate:` gate evidence view (`?run=<candidate>&panel=gate`) for one-line failure explanation and evidence link.

Operator script:
- keep API and UI terminal windows visible
- capture each screen in the sequence above
- total walkthrough target: under 2 minutes
