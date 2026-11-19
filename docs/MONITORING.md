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

Security enforcement tests:
- `test_observability_api.py` asserts auth requirements on `/metrics`, `/eval/last`, and `/eval/run`
- `test_observability_api.py` asserts path allowlist rejection and deterministic `429` rate-limit responses

## 2) Prometheus metrics (API)

### Operational
- `http_requests_total{route,method,status}`
- `http_request_duration_seconds_bucket{route,method}`
- `http_request_duration_seconds_count{route,method}`
- `http_request_duration_seconds_sum{route,method}`

HTTP `route` labels use registered route templates after dispatch, never the raw
requested path. Unmatched requests use `__unmatched__`; for example, five
unknown URLs produce five 404 observations under that one route label.
`method` labels are `GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`,
`TRACE`, `PATCH`, or `OTHER`. This bounds label values for a fixed route table
without changing routing, response statuses, authentication or rate limiting.
A registered route rejected with 405 retains its template when the router
supplies it. Counter increments and duration observations occur after dispatch;
a `/metrics` scrape therefore includes earlier completed requests, not its own
observation (which appears on the next scrape).

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

Install the `observability` extra (or `requirements-observability.txt`). It uses
MLflow Skinny 3.17.2 or newer in the qualified 3.17.x series plus SQLAlchemy and
Alembic for local SQL tracking. SQLAlchemy stays on 2.0.x because this SDK
uses a loader strategy deprecated in 2.1 under the project's strict warning policy.
Lift the 2.1 ceiling after a patched SDK passes these same strict local-client
tests and dependency audit with SQLAlchemy 2.1 or newer. ToneSight needs tracking APIs, not an MLflow
server, UI, model loader or data-science stack. Merely renaming an unpatched
MLflow 2.x install to Skinny would not patch shared SDK code; this upgrade also
advances that code. Avoid co-installing conflicting full/skinny SDK versions.
Use a fresh environment when moving from the old extra: changing a requirement
does not uninstall previously installed full MLflow or PyArrow. Check the final
environment with `python -m pip check` and `python -m pip_audit`; resolve old
packages instead of assuming a new requirement removed them.

`run_eval(..., mlflow_tracking_uri=...)` and the equivalent CLI/API option log:

- params: `threshold_l1`, `taxonomy_path`, `calibration_path`;
- metrics: `pass_rate`, `avg_l1`, `p95_l1`;
- artifacts: `out.jsonl`, `eval_summary.json`, `report.html`, `receipt.json`.

Logging remains opt-in. An empty URI does nothing; missing SDK or logging errors
remain non-fatal and are reported in the receipt's `mlflow` block. The adapter
sets the process-local default `MLFLOW_DISABLE_TELEMETRY=true` **before SDK
import** when logging is requested. An explicitly configured caller value is
retained. This neither changes machine configuration nor undoes activity from
SDK imports a caller performed earlier. For strict local use, explicitly set
`MLFLOW_DISABLE_TELEMETRY=true` (or `DO_NOT_TRACK=true`) before starting Python.
Only send artifacts to tracking destinations for which you have authorization.

### Local SQLite and legacy file-store migration

For a new local run, pass an explicit SQLite URI, for example:

```text
tonesight-ns8 eval --mlflow-tracking-uri sqlite:///tracking.db
```

Use an absolute SQLite URI if the process working directory varies. Keep the
artifact directory as well as the database when moving or backing up runs.
This was checked using fresh synthetic records, local SQLite, exact retrieved
params/metrics/artifact bytes, and denied socket/DNS calls; no remote server or
model loading was exercised.

**Compatibility change:** MLflow 3.17.x disables its maintenance-mode legacy
file tracking backend by default. Old `file:` or directory tracking URIs can
therefore produce a non-fatal disabled logging receipt instead of a logged run.
ToneSight does not set `MLFLOW_ALLOW_FILE_STORE` to bypass that upstream default.
Inspect the receipt rather than assuming tracking succeeded.

For existing authorized file-store data, back it up and stop writers first.
The upstream migration command accepts a source directory and an empty SQLite
target, for example `mlflow migrate-filestore --source /path/to/mlruns --target
sqlite:///tracking.db`. Follow the [official migration guide](https://mlflow.org/docs/latest/self-hosting/migrate-from-file-store/),
then point ToneSight at that SQLite URI and verify your retained records.
Artifacts stay at their original locations; migration does not copy them.
No existing or private store was migrated by this change.

The observability CI job audits its installed optional dependencies and runs
real local-client tests. A clean advisory snapshot is not a proof of whole-stack
security, remote-server authorization or safety of loading untrusted models.

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
