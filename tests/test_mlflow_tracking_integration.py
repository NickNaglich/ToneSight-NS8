"""Optional real-client contracts using synthetic local artifacts, never a server."""
from __future__ import annotations

import importlib.util
import socket
from pathlib import Path

import pytest

from tonesight_ns8.eval_runner import log_eval_to_mlflow

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("mlflow") is None,
    reason="requires the optional observability tracking client",
)


@pytest.fixture
def local_tracking(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_DISABLE_TELEMETRY", "true")
    monkeypatch.setenv("DO_NOT_TRACK", "true")
    monkeypatch.delenv("MLFLOW_ALLOW_FILE_STORE", raising=False)
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append(args)
        raise AssertionError("outbound network forbidden in local tracking tests")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    out = tmp_path / "eval"
    out.mkdir()
    for name in ["out.jsonl", "eval_summary.json", "report.html", "receipt.json"]:
        (out / name).write_text("synthetic local tracking artifact: " + name, encoding="utf-8")
    yield tmp_path, out
    assert attempts == []


def log_synthetic(uri, out):
    return log_eval_to_mlflow(
        tracking_uri=uri,
        result={"summary": {"pass_rate": 0.75, "avg_l1": 1.25, "p95_l1": 3.0}},
        out_dir=out, threshold_l1=3, taxonomy_path="synthetic.json", calibration_path=None,
    )


def test_sqlite_client_preserves_params_metrics_and_artifact_bytes(local_tracking):
    root, out = local_tracking
    uri = "sqlite:///" + (root / "tracking.db").as_posix()
    payload = log_synthetic(uri, out)
    assert payload["enabled"] is True, payload
    from mlflow.telemetry import get_telemetry_client
    from mlflow.tracking import MlflowClient

    assert get_telemetry_client() is None
    client = MlflowClient(tracking_uri=uri)
    run = client.get_run(payload["run_id"])
    assert run.info.status == "FINISHED"
    assert run.data.params == {"threshold_l1": "3", "taxonomy_path": "synthetic.json", "calibration_path": ""}
    assert run.data.metrics == {"pass_rate": 0.75, "avg_l1": 1.25, "p95_l1": 3.0}
    names = sorted(p.name for p in out.iterdir())
    assert sorted(p.path for p in client.list_artifacts(payload["run_id"])) == names
    for name in names:
        downloaded = Path(client.download_artifacts(payload["run_id"], name))
        assert downloaded.read_bytes() == (out / name).read_bytes()


def test_legacy_file_store_rejection_remains_nonfatal(local_tracking):
    root, out = local_tracking
    payload = log_synthetic((root / "legacy-mlruns").as_uri(), out)
    assert payload["enabled"] is False
    assert "filesystem tracking backend" in payload["reason"].lower()
    assert "sqlite" in payload["reason"].lower()
    assert sorted(p.name for p in out.iterdir()) == ["eval_summary.json", "out.jsonl", "receipt.json", "report.html"]
