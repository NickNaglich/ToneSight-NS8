# Monitoring & Observability

Current implemented stack (Path B):
- FastAPI observability service
- Prometheus scrape and basic metrics
- Grafana provisioning + baseline dashboard
- Optional MLflow run logging from eval
- Optional GPU before/after snapshots from eval (`nvidia-smi` if available)

Defaults config override:
- Runtime defaults are loaded from `config/defaults.json`.
- To point the service at a different defaults file, set `TONESIGHT_DEFAULTS_PATH=/path/to/defaults.json` before starting the API/CLI process.

Examples:

```bash
TONESIGHT_DEFAULTS_PATH=config/defaults.json uvicorn tonesight_ns8.observability_api:app --host 0.0.0.0 --port 8080
```

```powershell
$env:TONESIGHT_DEFAULTS_PATH = "config/defaults.json"
uvicorn tonesight_ns8.observability_api:app --host 0.0.0.0 --port 8080
```

```cmd
set TONESIGHT_DEFAULTS_PATH=config\defaults.json
uvicorn tonesight_ns8.observability_api:app --host 0.0.0.0 --port 8080
```

## 1) Services
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- API: `http://localhost:8080`

Required environment for secure local startup:
- `TONESIGHT_API_TOKEN` (bearer auth for `/metrics`, `/eval/run`, `/eval/last`)
- `TONESIGHT_ALLOWED_PATHS` (path allowlist for eval payload paths; defaults to current working directory)
- `TONESIGHT_RATE_LIMIT_PER_MINUTE` (default `60`)
- `GF_SECURITY_ADMIN_USER`
- `GF_SECURITY_ADMIN_PASSWORD`

Example:

```bash
export TONESIGHT_API_TOKEN="<strong-random-token>"
export GF_SECURITY_ADMIN_USER="<grafana-admin-user>"
export GF_SECURITY_ADMIN_PASSWORD="<strong-grafana-password>"
docker compose up --build
```

## 2) Prometheus metrics (API)

### Operational
- `http_requests_total{route,method,status}`
- `http_request_duration_seconds_bucket{route,method}`
- `http_request_duration_seconds_count{route,method}`
- `http_request_duration_seconds_sum{route,method}`

### Model behavior (low-cardinality)
(Do NOT label with run_id.)
- `tone_score_requests_total{backend,decision}`  (`decision=pass|fail`)
- `tone_l1_mean` (gauge updated periodically or via summary exporter)
- `tone_l1_bucket{backend}` (histogram)
- `tone_dim_abs_error_bucket{dim,backend}`  (`dim=V|A|D`)
- `tone_quality_total{q,backend}`  (`q=0..3`)

### Batch/Eval operational
- `tone_batch_runs_total{status}`
- `tone_batch_duration_seconds_bucket`
- `tone_eval_runs_total{status}`
- `tone_eval_duration_seconds_bucket`
- `last_eval_timestamp` (gauge; Unix time of most recent completed eval)

Recommendation:
- Use `prometheus_client` Histogram and Counter.
- Keep labels to `{route, method, status, backend, decision, dim, q}`.
- Do not label metrics with `run_id` or request IDs.
- Treat tone metrics as operational proxy signals for conformance/drift, not as direct emotion ground truth.
- For longitudinal trend views without live providers, prefer artifact rollups via `python -m tonesight_ns8.cli trend --out-root runs` and publish `trend_summary.json`.

## 3) Grafana dashboards (recommended panels)

### Dashboard: Service Health
- RPS (rate of `http_requests_total`)
- p95 latency (`histogram_quantile`)
- error rate (`status >= 500`)
- CPU/RAM (if node/container metrics available; optional)

### Dashboard: Model Health
- pass rate over time
- mean/p95 L1
- V/A/D MAE
- quality tier distribution
- backend usage share (rule vs ollama)
- last eval freshness (`time() - last_eval_timestamp`)
- optional backend comparison table: pass_rate, avg L1, latency/item

### Dashboard: Runs (Batch/Eval)
- batch runs count + failures
- eval runs count + failures
- durations p50/p95
- last eval timestamp (from eval metric or log scrape)

## 4) MLflow tracking

Status:
- implemented as optional `run_eval(..., mlflow_tracking_uri=...)`
- if `mlflow` is unavailable, receipt records a non-fatal disabled reason

Log for every batch/eval:
- Params:
  - backend_id, thresholds, ns8 family selection, calibration version
  - dataset hash + row count
  - code version (git SHA if available)
- Metrics:
  - pass_rate, avg_l1, median_l1, p95_l1
  - per-dim MAE (V/A/D)
  - confusion matrix summaries
- Artifacts:
  - receipt.json
  - out.jsonl
  - confusion matrices (csv or json)
  - optional report.html
  - gpu_before.json / gpu_after.json

## 5) GPU monitoring

### A) Live GPU utilization (Prometheus)
Recommended: NVIDIA DCGM exporter.

- Compose profile: `gpu`
- Prometheus scrapes `dcgm-exporter:9400`

Example DCGM metrics (names depend on exporter config):
- `DCGM_FI_DEV_GPU_UTIL` (GPU utilization %)
- `DCGM_FI_DEV_MEM_COPY_UTIL`
- `DCGM_FI_DEV_FB_USED` / `DCGM_FI_DEV_FB_TOTAL`
- `DCGM_FI_DEV_POWER_USAGE`
- `DCGM_FI_DEV_GPU_TEMP`

Grafana panels:
- GPU utilization per GPU
- GPU memory used/total
- GPU temp / power usage

### B) Per-run GPU snapshots (required)
Implemented as optional `run_eval(..., capture_gpu=True)`.
Even if scorer is CPU-only, eval can capture GPU snapshots per run:
- `gpu_before.json`, `gpu_after.json`
- included in run receipt + logged to MLflow

Implementation notes:
- Prefer `nvidia-smi --query-gpu=...` if present.
- If not present, mark unavailable.
- Do not attempt to attribute GPU usage to a single request in Prometheus (label explosion).
  Use receipts + MLflow for per-run attribution.

## 6) Optional: logs and traces
- Loki: aggregate JSON logs; view in Grafana Explore
- OpenTelemetry: traces for `/v1/score`, `/v1/batch`, `/v1/eval`

Keep optional and behind compose profiles.
