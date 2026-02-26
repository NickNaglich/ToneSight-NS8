import json
import shutil
import threading
import urllib.request
from pathlib import Path
from uuid import uuid4

from server.app import ArtifactRequestHandler, ThreadingHTTPServer, get_artifact_response, resolve_html_artifact_path
from tonesight_ns8.run_index import run_index, run_index_json


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _mk_run(path: Path, *, run_id: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": "ds",
            "taxonomy_hash": "tx",
            "defaults_hash": "df",
            "mapping_id": "ns8",
            "mapping_version": "1.0",
        },
    )
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": 1,
            "pass_rate": 1.0,
            "avg_l1": 0.0,
            "p95_l1": 0.0,
            "max_l1": 0.0,
            "pass_count": 1,
            "fail_count": 0,
            "threshold_l1": 3,
        },
    )
    _write_jsonl(path / "out.jsonl", [{"id": "row_1", "pass": True, "compliance_l1": 0}])
    _write_json(path / "reports" / f"report_{run_id}.json", {"run_id": run_id, "summary": {"pass_rate": 1.0}})
    (path / "report.html").write_text(f"<html><body>{run_id}</body></html>\n", encoding="utf-8")


def test_artifact_server_health_and_index():
    root = _temp_dir("tmp_artifact_server_index")
    _mk_run(root / "run_a", run_id="run_a")
    _mk_run(root / "run_b", run_id="run_b")
    run_index(str(root))
    run_index_json(str(root))

    health_status, health_payload = get_artifact_response("/health", root)
    assert health_status == 200
    assert health_payload == {"ok": True}

    index_status, index_payload = get_artifact_response("/api/index", root)
    assert index_status == 200
    assert isinstance(index_payload, list)
    assert [row["run_id"] for row in index_payload] == ["run_a", "run_b"]


def test_artifact_server_run_routes():
    root = _temp_dir("tmp_artifact_server_run_routes")
    _mk_run(root / "run_001", run_id="run_001")
    run_index(str(root))
    run_index_json(str(root))

    receipt_status, receipt_payload = get_artifact_response("/api/run/run_001/receipt", root)
    assert receipt_status == 200
    assert receipt_payload["run_id"] == "run_001"

    summary_status, summary_payload = get_artifact_response("/api/run/run_001/summary", root)
    assert summary_status == 200
    assert summary_payload["run_id"] == "run_001"

    report_status, report_payload = get_artifact_response("/api/run/run_001/report", root)
    assert report_status == 200
    assert report_payload["run_id"] == "run_001"
    assert resolve_html_artifact_path("/api/run/run_001/report-html", root) == (root / "run_001" / "report.html")


def test_artifact_server_compare_and_gate_routes():
    root = _temp_dir("tmp_artifact_server_compare_gate")
    _mk_run(root / "run_a", run_id="run_a")
    _mk_run(root / "run_b", run_id="run_b")
    compare_dir = root / "run_b" / "comparisons" / "run_a"
    _write_json(compare_dir / "compare_summary.json", {"delta_pass_rate": -0.1})
    _write_json(compare_dir / "gate_result.json", {"decision": "regressed", "exit_code": 2})
    (compare_dir / "compare_report.html").write_text("<html><body>compare report</body></html>\n", encoding="utf-8")

    compare_status, compare_payload = get_artifact_response("/api/compare/run_a/run_b", root)
    assert compare_status == 200
    assert compare_payload["delta_pass_rate"] == -0.1

    gate_status, gate_payload = get_artifact_response("/api/gate/run_a/run_b", root)
    assert gate_status == 200
    assert gate_payload["exit_code"] == 2
    assert resolve_html_artifact_path("/api/compare-report/run_a/run_b", root) == (
        root / "run_b" / "comparisons" / "run_a" / "compare_report.html"
    )


def test_artifact_server_invalid_and_missing_routes():
    root = _temp_dir("tmp_artifact_server_errors")
    _mk_run(root / "run_001", run_id="run_001")
    run_index(str(root))
    run_index_json(str(root))

    invalid_status, invalid_payload = get_artifact_response("/api/run/../receipt", root)
    assert invalid_status == 400
    assert invalid_payload["error"]["code"] == "invalid_identifier"

    missing_status, missing_payload = get_artifact_response("/api/run/run_001/unknown", root)
    assert missing_status == 400
    assert missing_payload["error"]["code"] == "invalid_route"

    not_found_status, not_found_payload = get_artifact_response("/api/gate/run_001/run_001", root)
    assert not_found_status == 404
    assert not_found_payload["error"]["code"] == "artifact_not_found"

    bad_route_status, bad_route_payload = get_artifact_response("/api/not-real", root)
    assert bad_route_status == 400
    assert bad_route_payload["error"]["code"] == "invalid_route"


def test_artifact_server_http_includes_cors_headers():
    root = _temp_dir("tmp_artifact_server_cors")
    _mk_run(root / "run_a", run_id="run_a")
    _mk_run(root / "run_b", run_id="run_b")
    compare_dir = root / "run_b" / "comparisons" / "run_a"
    compare_dir.mkdir(parents=True, exist_ok=True)
    (compare_dir / "compare_report.html").write_text("<html><body>compare report</body></html>\n", encoding="utf-8")
    run_index(str(root))
    run_index_json(str(root))

    server = ThreadingHTTPServer(("127.0.0.1", 0), ArtifactRequestHandler)
    setattr(server, "runs_root", str(root))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/index", timeout=2) as resp:
            assert resp.status == 200
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
            assert "GET" in str(resp.headers.get("Access-Control-Allow-Methods", ""))
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/run/run_a/report-html", timeout=2) as resp:
            assert resp.status == 200
            assert "text/html" in str(resp.headers.get("Content-Type", ""))
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/compare-report/run_a/run_b", timeout=2) as resp:
            assert resp.status == 200
            assert "text/html" in str(resp.headers.get("Content-Type", ""))
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
