# Post-Merge Verification (v0.2.5 UI)

Run this checklist after merge/deploy of the v0.2.5 UI centralization changes.

## 1) Test Suite

```bash
python -m pytest -q
```

Expected: all tests pass (`233 passed` at merge time).

## 2) Generate Demo Artifacts + Start Servers

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1
```

Expected:
- baseline + candidate runs generated
- compare + gate artifacts written
- API and UI server PIDs printed

## 3) UI Paths

Open and verify:
- `http://127.0.0.1:8090/index.html`
- deep links printed by script:
  - `?run=<candidate>&panel=detail`
  - `?run=<candidate>&panel=compare`
  - `?run=<candidate>&panel=gate`

Expected:
- dashboard loads without fetch errors
- status badges and filter controls visible
- run detail, compare, and gate panels populated

## 4) API Routes

Verify HTTP 200:
- `/health`
- `/api/index`
- `/api/run/<id>/report-html`
- `/api/compare/<run_a>/<run_b>`
- `/api/compare-report/<run_a>/<run_b>`
- `/api/gate/<run_a>/<run_b>`

## 5) Safety Boundary Checks

Confirm in UI:
- derived artifacts are linked in artifact table
- restricted artifacts (`events.raw.jsonl`, `quarantine.jsonl`) shown as non-link labels
- no default clickable links to raw artifacts

## 6) Generated Page Checks

Confirm:
- run `report.html` uses dashboard-aligned visual style
- `compare_report.html` shows status/KPIs/coverage/top regressions/per-label deltas

## 7) Documentation/Tracker Sync

Confirm:
- `.agent/LOGS/CHANGE_LOG.md` includes latest entries
- `.agent/TO-DO/PHASED_WORKFLOW.md` statuses reflect completed v0.2.5 addendum phases

## 8) Shutdown Demo Servers

Use script output PIDs:

```powershell
Stop-Process -Id <api_pid>,<ui_pid>
```
