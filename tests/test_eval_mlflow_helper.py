from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.eval_runner import log_eval_to_mlflow


class _FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = type("RunInfo", (), {"run_id": run_id})()


class _FakeRunContext:
    def __init__(self, run_id: str = "mlflow_run_123") -> None:
        self._run = _FakeRun(run_id)

    def __enter__(self) -> _FakeRun:
        return self._run

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeMlflowOk:
    def __init__(self) -> None:
        self.params: dict[str, str | int] = {}
        self.metrics: dict[str, float] = {}
        self.artifacts: list[str] = []
        self.tracking_uri: str | None = None

    def set_tracking_uri(self, uri: str) -> None:
        self.tracking_uri = uri

    def start_run(self) -> _FakeRunContext:
        return _FakeRunContext()

    def log_param(self, key: str, value: str | int) -> None:
        self.params[key] = value

    def log_metric(self, key: str, value: float) -> None:
        self.metrics[key] = value

    def log_artifact(self, path: str) -> None:
        self.artifacts.append(path)


class _FakeMlflowFail:
    def set_tracking_uri(self, uri: str) -> None:
        _ = uri

    def start_run(self) -> _FakeRunContext:
        raise RuntimeError("synthetic mlflow failure")


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_log_eval_to_mlflow_noop_when_tracking_uri_empty():
    out_dir = _temp_dir("tmp_mlflow_helper_noop")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = log_eval_to_mlflow(
        tracking_uri="",
        result={"summary": {"pass_rate": 1.0, "avg_l1": 0.0, "p95_l1": 0.0}},
        out_dir=out_dir,
        threshold_l1=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        calibration_path=None,
    )
    assert payload is None


def test_log_eval_to_mlflow_failure_is_non_fatal(monkeypatch):
    monkeypatch.setitem(sys.modules, "mlflow", _FakeMlflowFail())
    out_dir = _temp_dir("tmp_mlflow_helper_fail")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = log_eval_to_mlflow(
        tracking_uri="file:/tmp/mlruns",
        result={"summary": {"pass_rate": 0.8, "avg_l1": 1.0, "p95_l1": 2.0}},
        out_dir=out_dir,
        threshold_l1=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        calibration_path=None,
    )
    assert isinstance(payload, dict)
    assert payload["enabled"] is False
    assert "mlflow logging failed" in payload["reason"]


def test_log_eval_to_mlflow_success(monkeypatch):
    fake_mlflow = _FakeMlflowOk()
    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    out_dir = _temp_dir("tmp_mlflow_helper_ok")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = log_eval_to_mlflow(
        tracking_uri="file:/tmp/mlruns",
        result={"summary": {"pass_rate": 0.91, "avg_l1": 0.4, "p95_l1": 1.0}},
        out_dir=out_dir,
        threshold_l1=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        calibration_path=None,
    )
    assert payload == {"enabled": True, "run_id": "mlflow_run_123"}
    assert fake_mlflow.tracking_uri == "file:/tmp/mlruns"
    assert fake_mlflow.params["threshold_l1"] == 3
    assert "pass_rate" in fake_mlflow.metrics
    assert len(fake_mlflow.artifacts) == 4
