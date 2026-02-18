"""Optional observability API (Path B) with Prometheus metrics."""

from __future__ import annotations

import time
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from .defaults import ARTIFACT_DEFAULTS, EVAL_DEFAULTS
from .eval_runner import run_eval

app = FastAPI(title="tonesight-ns8-observability", version="1.3.0")

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    labelnames=("route", "method", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("route", "method"),
)
TONE_EVAL_RUNS_TOTAL = Counter(
    "tone_eval_runs_total",
    "Total eval runs by status.",
    labelnames=("status",),
)
TONE_EVAL_DURATION_SECONDS = Histogram(
    "tone_eval_duration_seconds",
    "Eval run duration in seconds.",
)
LAST_EVAL_TIMESTAMP = Gauge(
    "last_eval_timestamp",
    "Unix timestamp of last successful eval completion.",
)
TONE_L1_MEAN = Gauge(
    "tone_l1_mean",
    "Mean L1 for most recent eval.",
)
TONE_PASS_RATE = Gauge(
    "tone_pass_rate",
    "Pass rate for most recent eval.",
)
TONE_P95_L1 = Gauge(
    "tone_p95_l1",
    "P95 L1 for most recent eval.",
)

_LAST_EVAL: dict[str, Any] | None = None


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    return value


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    route_label = request.url.path
    method_label = request.method
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    status_label = str(response.status_code)
    HTTP_REQUESTS_TOTAL.labels(route=route_label, method=method_label, status=status_label).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(route=route_label, method=method_label).observe(elapsed)
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tonesight-ns8-observability", "spec_version": "1.0"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/eval/last")
def eval_last() -> JSONResponse:
    if _LAST_EVAL is None:
        return JSONResponse({"status": "none", "message": "No eval has been run in this process yet."}, status_code=404)
    return JSONResponse(_to_jsonable(_LAST_EVAL))


@app.post("/eval/run")
def eval_run(payload: dict[str, Any]) -> JSONResponse:
    global _LAST_EVAL
    goldset_path = str(payload.get("goldset_path", ARTIFACT_DEFAULTS["goldset_path"]))
    out_root = str(payload.get("out_root", EVAL_DEFAULTS["out_root"]))
    taxonomy_path = str(payload.get("taxonomy_path", EVAL_DEFAULTS["taxonomy_path"]))
    threshold_l1 = int(payload.get("threshold_l1", EVAL_DEFAULTS["threshold_l1"]))
    calibration_path = payload.get("calibration_path")
    capture_gpu = bool(payload.get("capture_gpu", False))
    mlflow_tracking_uri = payload.get("mlflow_tracking_uri")

    started = time.perf_counter()
    try:
        result = run_eval(
            goldset_path=goldset_path,
            out_root=out_root,
            taxonomy_path=taxonomy_path,
            threshold_l1=threshold_l1,
            calibration_path=calibration_path,
            capture_gpu=capture_gpu,
            mlflow_tracking_uri=mlflow_tracking_uri,
        )
    except Exception as exc:  # pragma: no cover
        TONE_EVAL_RUNS_TOTAL.labels(status="fail").inc()
        raise HTTPException(status_code=400, detail=f"eval run failed: {exc}") from exc

    elapsed = time.perf_counter() - started
    TONE_EVAL_DURATION_SECONDS.observe(elapsed)
    TONE_EVAL_RUNS_TOTAL.labels(status="ok").inc()
    LAST_EVAL_TIMESTAMP.set(time.time())
    TONE_L1_MEAN.set(float(result["summary"].get("avg_l1", 0.0)))
    TONE_PASS_RATE.set(float(result["summary"].get("pass_rate", 0.0)))
    TONE_P95_L1.set(float(result["summary"].get("p95_l1", 0.0)))
    _LAST_EVAL = result
    return JSONResponse(_to_jsonable(result))
