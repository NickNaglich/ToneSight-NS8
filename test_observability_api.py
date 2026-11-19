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


@pytest.fixture
def isolated_metrics_api(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("prometheus_client")
    from fastapi.testclient import TestClient
    from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
    import tonesight_ns8.observability_api as api

    registry = CollectorRegistry()
    monkeypatch.setattr(api, "HTTP_REQUESTS_TOTAL", Counter(
        "http_requests_total", "Test requests.", ("route", "method", "status"), registry=registry
    ))
    monkeypatch.setattr(api, "HTTP_REQUEST_DURATION_SECONDS", Histogram(
        "http_request_duration_seconds", "Test durations.", ("route", "method"), registry=registry
    ))
    monkeypatch.setattr(api, "generate_latest", lambda: generate_latest(registry))
    monkeypatch.setattr(api, "_RATE_LIMIT_STATE", {})
    monkeypatch.setattr(api, "_LAST_EVAL", None)
    monkeypatch.setattr(api.app.router, "routes", list(api.app.router.routes))
    monkeypatch.setenv("TONESIGHT_API_TOKEN", "test-token")
    monkeypatch.setenv("TONESIGHT_ALLOWED_PATHS", str(tmp_path))
    monkeypatch.setenv("TONESIGHT_RATE_LIMIT_PER_MINUTE", "60")
    eval_calls = []

    def forbidden_eval(*args, **kwargs):
        eval_calls.append((args, kwargs))
        raise AssertionError("These metrics tests must not run evaluation or providers")

    monkeypatch.setattr(api, "run_eval", forbidden_eval)
    with TestClient(api.app) as client:
        yield client, registry, api
    assert eval_calls == []


def _metric_values(registry, name):
    return {
        tuple(sorted(sample.labels.items())): sample.value
        for family in registry.collect()
        for sample in family.samples
        if sample.name == name
    }


def test_unknown_paths_share_metric_labels_and_keep_all_observations(isolated_metrics_api):
    client, registry, _ = isolated_metrics_api
    assert _metric_values(registry, "http_requests_total") == {}
    assert _metric_values(registry, "http_request_duration_seconds_count") == {}
    for index in range(5):
        response = client.get(f"/unknown-{index}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
    assert _metric_values(registry, "http_requests_total") == {
        (("method", "GET"), ("route", "__unmatched__"), ("status", "404")): 5.0
    }
    assert _metric_values(registry, "http_request_duration_seconds_count") == {
        (("method", "GET"), ("route", "__unmatched__")): 5.0
    }


def test_route_templates_and_unknown_methods_preserve_http_results(isolated_metrics_api):
    client, registry, api = isolated_metrics_api

    def item(item_id: str):
        return {"id": item_id}

    api.app.add_api_route("/metric-items/{item_id}", item, methods=["GET"])
    for item_id in ("first", "second"):
        response = client.get(f"/metric-items/{item_id}")
        assert response.status_code == 200
        assert response.json() == {"id": item_id}
    assert client.request("CUSTOM", "/health").status_code == 405
    assert client.request("CUSTOM", "/absent").status_code == 404
    assert _metric_values(registry, "http_requests_total") == {
        (("method", "GET"), ("route", "/metric-items/{item_id}"), ("status", "200")): 2.0,
        (("method", "OTHER"), ("route", "/health"), ("status", "405")): 1.0,
        (("method", "OTHER"), ("route", "__unmatched__"), ("status", "404")): 1.0,
    }
    assert _metric_values(registry, "http_request_duration_seconds_count") == {
        (("method", "GET"), ("route", "/metric-items/{item_id}")): 2.0,
        (("method", "OTHER"), ("route", "/health")): 1.0,
        (("method", "OTHER"), ("route", "__unmatched__")): 1.0,
    }


def test_metrics_scrape_timing_auth_rate_limit_and_allowlist(isolated_metrics_api, monkeypatch, tmp_path):
    client, registry, _ = isolated_metrics_api
    monkeypatch.setenv("TONESIGHT_RATE_LIMIT_PER_MINUTE", "1")
    headers = {"Authorization": "Bearer test-token"}
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 401
    scrape = client.get("/metrics", headers=headers)
    assert scrape.status_code == 200
    assert 'http_requests_total{method="GET",route="/metrics",status="401"} 1.0' in scrape.text
    assert 'http_requests_total{method="GET",route="/metrics",status="200"}' not in scrape.text
    assert client.get("/metrics", headers=headers).status_code == 429
    denied = client.post("/eval/run", headers=headers, json={"goldset_path": str(tmp_path.parent / "outside.jsonl")})
    assert denied.status_code == 400
    assert denied.json()["detail"].startswith("path not allowed:")
    assert _metric_values(registry, "http_requests_total") == {
        (("method", "GET"), ("route", "/health"), ("status", "200")): 1.0,
        (("method", "GET"), ("route", "/metrics"), ("status", "401")): 1.0,
        (("method", "GET"), ("route", "/metrics"), ("status", "200")): 1.0,
        (("method", "GET"), ("route", "/metrics"), ("status", "429")): 1.0,
        (("method", "POST"), ("route", "/eval/run"), ("status", "400")): 1.0,
    }
    assert _metric_values(registry, "http_request_duration_seconds_count") == {
        (("method", "GET"), ("route", "/health")): 1.0,
        (("method", "GET"), ("route", "/metrics")): 3.0,
        (("method", "POST"), ("route", "/eval/run")): 1.0,
    }
