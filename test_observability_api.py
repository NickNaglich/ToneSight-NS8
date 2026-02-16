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
    from fastapi.testclient import TestClient
    from tonesight_ns8.observability_api import app

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["spec_version"] == "1.0"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert "tone_pass_rate" in metrics.text
    assert "tone_p95_l1" in metrics.text
