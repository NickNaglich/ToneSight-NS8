from pathlib import Path

import pytest


def test_observability_stack_files_exist():
    assert Path("docker-compose.yml").exists()
    assert Path("docker/api.Dockerfile").exists()
    assert Path("monitoring/prometheus/prometheus.yml").exists()
    assert Path("monitoring/grafana/provisioning/datasources/datasource.yml").exists()
    assert Path("monitoring/grafana/provisioning/dashboards/dashboards.yml").exists()
    assert Path("monitoring/grafana/dashboards/tonesight-overview.json").exists()


def test_observability_api_health_and_metrics():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["spec_version"] == "1.0"

    metrics = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert "tone_pass_rate" in metrics.text
    assert "tone_p95_l1" in metrics.text


def test_observability_api_metrics_requires_auth():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    client = TestClient(app)
    unauth = client.get("/metrics")
    assert unauth.status_code == 401


def test_observability_api_eval_last_requires_auth():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    client = TestClient(app)
    unauth = client.get("/eval/last")
    assert unauth.status_code == 401
    auth = client.get("/eval/last", headers={"Authorization": "Bearer test-token"})
    assert auth.status_code == 404


def test_observability_api_eval_run_path_allowlist_enforced():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    os.environ["TONESIGHT_ALLOWED_PATHS"] = str(Path.cwd())
    client = TestClient(app)
    resp = client.post(
        "/eval/run",
        headers={"Authorization": "Bearer test-token"},
        json={"goldset_path": "/tmp/not-allowed.jsonl"},
    )
    assert resp.status_code == 400


def test_observability_api_eval_run_requires_auth():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    client = TestClient(app)
    unauth = client.post("/eval/run", json={"goldset_path": "data/goldset.jsonl"})
    assert unauth.status_code == 401


def test_observability_api_rate_limit_returns_429():
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    import os
    from fastapi.testclient import TestClient
    import tonesight_ns8.observability_api as observability_api

    os.environ["TONESIGHT_API_TOKEN"] = "test-token"
    os.environ["TONESIGHT_RATE_LIMIT_PER_MINUTE"] = "1"
    observability_api._RATE_LIMIT_STATE.clear()

    client = TestClient(observability_api.app)
    first = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert first.status_code == 200

    second = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert second.status_code == 429
    assert second.json() == {"detail": "rate limit exceeded"}
