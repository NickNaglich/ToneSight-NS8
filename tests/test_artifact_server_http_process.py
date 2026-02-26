import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from uuid import uuid4

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


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(url: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise AssertionError(f"artifact API did not become healthy: {url}")


def test_artifact_server_http_process_end_to_end():
    root = _temp_dir("tmp_artifact_server_http_process")
    _mk_run(root / "run_a", run_id="run_a")
    _mk_run(root / "run_b", run_id="run_b")
    compare_dir = root / "run_b" / "comparisons" / "run_a"
    _write_json(compare_dir / "compare_summary.json", {"delta_pass_rate": -0.1})
    _write_json(compare_dir / "gate_result.json", {"decision": "regressed", "exit_code": 2})
    (compare_dir / "compare_report.html").write_text("<html><body>compare report</body></html>\n", encoding="utf-8")
    run_index(str(root))
    run_index_json(str(root))

    port = _get_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "server/app.py",
            "--runs-root",
            str(root),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_health(f"http://127.0.0.1:{port}/health")

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/index", timeout=2) as resp:
            assert resp.status == 200
            payload = json.loads(resp.read().decode("utf-8"))
            assert isinstance(payload, list)
            assert [row["run_id"] for row in payload] == ["run_a", "run_b"]

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/run/run_b/report-html", timeout=2) as resp:
            assert resp.status == 200
            assert "text/html" in str(resp.headers.get("Content-Type", ""))

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/compare/run_a/run_b", timeout=2) as resp:
            assert resp.status == 200
            payload = json.loads(resp.read().decode("utf-8"))
            assert payload["delta_pass_rate"] == -0.1

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/compare-report/run_a/run_b", timeout=2) as resp:
            assert resp.status == 200
            assert "text/html" in str(resp.headers.get("Content-Type", ""))

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/gate/run_a/run_b", timeout=2) as resp:
            assert resp.status == 200
            payload = json.loads(resp.read().decode("utf-8"))
            assert int(payload["exit_code"]) == 2
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
