"""Minimal read-only static artifact API for ToneSight runs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _json_error(status: int, code: str, message: str, path: str) -> tuple[int, dict[str, Any]]:
    return status, {
        "error": {
            "code": code,
            "message": message,
            "path": path,
        }
    }


def _is_safe_id(value: str) -> bool:
    if not value:
        return False
    forbidden = ("/", "\\")
    if any(ch in value for ch in forbidden):
        return False
    if value in (".", ".."):
        return False
    if ".." in value:
        return False
    return True


def _read_json_file(path: Path, request_path: str) -> tuple[int, dict[str, Any]]:
    if not path.exists():
        return _json_error(404, "artifact_not_found", f"Missing artifact: {path}", request_path)
    if not path.is_file():
        return _json_error(404, "artifact_not_found", f"Artifact is not a file: {path}", request_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _json_error(404, "malformed_artifact", f"Malformed JSON artifact at {path}: {exc.msg}", request_path)
    return 200, payload


def _json_success(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return 200, payload


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and value >= 0


def _read_request_json(handler: BaseHTTPRequestHandler) -> tuple[bool, dict[str, Any] | None]:
    raw_len = handler.headers.get("Content-Length", "0").strip()
    if not raw_len.isdigit():
        return False, None
    length = int(raw_len)
    if length <= 0:
        return False, None
    body = handler.rfile.read(length)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, None
    if not isinstance(payload, dict):
        return False, None
    return True, payload


def _run_cli_json_step(python_exe: str, argv: list[str], cwd: Path) -> dict[str, Any]:
    command = [python_exe, *argv]
    completed = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    payload: dict[str, Any] | None = None
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return {
        "command": command,
        "exit_code": int(completed.returncode),
        "payload": payload,
        "stdout": stdout,
        "stderr": stderr,
    }


def run_pipeline_request(request_payload: dict[str, Any], *, runs_root: str | Path, python_exe: str) -> tuple[int, dict[str, Any]]:
    events_path = str(request_payload.get("events_path", "")).strip()
    if not events_path:
        return _json_error(400, "invalid_request", "Missing required field: events_path", "/api/pipeline/run")
    events_file = Path(events_path)
    if not events_file.exists() or not events_file.is_file():
        return _json_error(400, "invalid_request", f"events_path is not a file: {events_file}", "/api/pipeline/run")

    threshold_l1 = request_payload.get("threshold_l1", 3)
    top_n = request_payload.get("top_n", 10)
    if not _is_non_negative_int(threshold_l1):
        return _json_error(400, "invalid_request", "threshold_l1 must be an integer >= 0", "/api/pipeline/run")
    if not _is_non_negative_int(top_n):
        return _json_error(400, "invalid_request", "top_n must be an integer >= 0", "/api/pipeline/run")

    out_root = str(request_payload.get("out_root") or runs_root).strip() or str(runs_root)
    taxonomy_path = str(request_payload.get("taxonomy_path", "taxonomy/tone_taxonomy.v1.json")).strip()
    shadow_strict = str(request_payload.get("shadow_strict", "quarantine")).strip() or "quarantine"
    adapter = str(request_payload.get("adapter", "coding_agent")).strip() or "coding_agent"
    gate_profile = str(request_payload.get("gate_profile", "coding_agent_drift")).strip() or "coding_agent_drift"
    require_pinned = bool(request_payload.get("require_pinned_model_identity", True))
    allow_dataset_mismatch = bool(request_payload.get("allow_dataset_mismatch", True))
    baseline_run_id = str(request_payload.get("baseline_run_id", "")).strip()
    if baseline_run_id and not _is_safe_id(baseline_run_id):
        return _json_error(400, "invalid_request", f"Invalid baseline_run_id: {baseline_run_id!r}", "/api/pipeline/run")

    repo_root = Path(__file__).resolve().parent.parent
    runs_dir = Path(out_root)
    steps: list[dict[str, Any]] = []

    validate_step = _run_cli_json_step(python_exe, ["tools/validate_live_event.py", str(events_file)], repo_root)
    steps.append({"name": "validate_live_event", **validate_step})
    if validate_step["exit_code"] != 0:
        return _json_error(400, "pipeline_step_failed", "Live event validation failed.", "/api/pipeline/run")

    capture_step = _run_cli_json_step(
        python_exe,
        ["-m", "tonesight_ns8.cli", "live-capture", "--events", str(events_file), "--out-root", str(runs_dir)],
        repo_root,
    )
    steps.append({"name": "live_capture", **capture_step})
    capture_payload = capture_step["payload"] or {}
    capture_dir = str(capture_payload.get("capture_dir", "")).strip()
    if capture_step["exit_code"] != 0 or not capture_dir:
        return _json_error(400, "pipeline_step_failed", "live-capture failed.", "/api/pipeline/run")

    replay_args = [
        "-m",
        "tonesight_ns8.cli",
        "live-replay",
        "--capture",
        capture_dir,
        "--out-root",
        str(runs_dir),
        "--taxonomy",
        taxonomy_path,
        "--threshold-l1",
        str(threshold_l1),
        "--shadow-strict",
        shadow_strict,
        "--adapter",
        adapter,
    ]
    if require_pinned:
        replay_args.append("--require-pinned-model-identity")
    replay_step = _run_cli_json_step(python_exe, replay_args, repo_root)
    steps.append({"name": "live_replay", **replay_step})
    replay_payload = replay_step["payload"] or {}
    run_dir = str(replay_payload.get("out_dir", "")).strip()
    run_id = str(replay_payload.get("run_id", "")).strip()
    if replay_step["exit_code"] != 0 or not run_dir:
        return _json_error(400, "pipeline_step_failed", "live-replay failed.", "/api/pipeline/run")

    compare_payload: dict[str, Any] | None = None
    gate_payload: dict[str, Any] | None = None
    gate_exit_code: int | None = None
    if baseline_run_id:
        run_a = runs_dir / baseline_run_id
        if not run_a.exists() or not run_a.is_dir():
            return _json_error(400, "invalid_request", f"Baseline run is missing: {run_a}", "/api/pipeline/run")
        compare_step = _run_cli_json_step(
            python_exe,
            [
                "-m",
                "tonesight_ns8.cli",
                "compare",
                str(run_a),
                run_dir,
                "--top-n",
                str(top_n),
                "--write",
            ],
            repo_root,
        )
        steps.append({"name": "compare", **compare_step})
        if compare_step["exit_code"] != 0:
            return _json_error(400, "pipeline_step_failed", "compare failed.", "/api/pipeline/run")
        compare_payload = compare_step.get("payload")

        gate_args = [
            "-m",
            "tonesight_ns8.cli",
            "gate",
            "--run-a",
            str(run_a),
            "--run-b",
            run_dir,
            "--profile",
            gate_profile,
            "--top-n",
            str(top_n),
        ]
        if allow_dataset_mismatch:
            gate_args.append("--allow-dataset-mismatch")
        gate_step = _run_cli_json_step(python_exe, gate_args, repo_root)
        steps.append({"name": "gate", **gate_step})
        if gate_step["exit_code"] not in (0, 2, 3):
            return _json_error(400, "pipeline_step_failed", "gate failed with unexpected exit code.", "/api/pipeline/run")
        gate_payload = gate_step.get("payload")
        gate_exit_code = gate_step["exit_code"]

    for index_step_name, index_args in (
        ("index_runs", ["-m", "tonesight_ns8.cli", "index-runs", "--out-root", str(runs_dir)]),
        ("index_runs_json", ["-m", "tonesight_ns8.cli", "index-runs-json", "--out-root", str(runs_dir)]),
    ):
        idx_step = _run_cli_json_step(python_exe, index_args, repo_root)
        steps.append({"name": index_step_name, **idx_step})
        if idx_step["exit_code"] != 0:
            return _json_error(400, "pipeline_step_failed", f"{index_step_name} failed.", "/api/pipeline/run")

    return _json_success(
        {
            "ok": True,
            "pipeline": "live_capture_replay_compare_gate",
            "events_path": str(events_file),
            "out_root": str(runs_dir),
            "capture_dir": capture_dir,
            "run_id": run_id,
            "run_dir": run_dir,
            "baseline_run_id": baseline_run_id or None,
            "compare": compare_payload,
            "gate": gate_payload,
            "gate_exit_code": gate_exit_code,
            "steps": steps,
        }
    )


def resolve_html_artifact_path(request_path: str, runs_root: str | Path = "runs") -> Path | None:
    """Resolve HTML artifact routes to concrete paths, or None for non-HTML routes."""
    parsed = urlparse(request_path)
    path = parsed.path
    parts = [part for part in path.split("/") if part]
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "run" and parts[3] == "report-html":
        run_id = parts[2]
        if not _is_safe_id(run_id):
            return None
        return Path(runs_root) / run_id / "report.html"
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "compare-report":
        run_a, run_b = parts[2], parts[3]
        if not _is_safe_id(run_a) or not _is_safe_id(run_b):
            return None
        return Path(runs_root) / run_b / "comparisons" / run_a / "compare_report.html"
    return None


def get_artifact_response(request_path: str, runs_root: str | Path = "runs") -> tuple[int, dict[str, Any]]:
    """Return deterministic JSON response tuple: (status_code, payload)."""
    parsed = urlparse(request_path)
    path = parsed.path
    runs_dir = Path(runs_root)

    if path == "/health":
        return 200, {"ok": True}

    if path == "/api/index":
        return _read_json_file(runs_dir / "index.json", path)

    parts = [part for part in path.split("/") if part]
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "run":
        run_id, artifact_name = parts[2], parts[3]
        if not _is_safe_id(run_id):
            return _json_error(400, "invalid_identifier", f"Invalid run_id: {run_id!r}", path)
        if artifact_name == "receipt":
            return _read_json_file(runs_dir / run_id / "receipt.json", path)
        if artifact_name == "summary":
            return _read_json_file(runs_dir / run_id / "eval_summary.json", path)
        if artifact_name == "report":
            return _read_json_file(runs_dir / run_id / "reports" / f"report_{run_id}.json", path)
        return _json_error(400, "invalid_route", f"Unsupported run artifact endpoint: {artifact_name}", path)

    if len(parts) == 4 and parts[0] == "api" and parts[1] in ("compare", "gate"):
        run_a, run_b = parts[2], parts[3]
        if not _is_safe_id(run_a) or not _is_safe_id(run_b):
            return _json_error(400, "invalid_identifier", "Invalid run identifier for compare/gate route.", path)
        base = runs_dir / run_b / "comparisons" / run_a
        if parts[1] == "compare":
            return _read_json_file(base / "compare_summary.json", path)
        return _read_json_file(base / "gate_result.json", path)

    return _json_error(400, "invalid_route", f"Unsupported endpoint: {path}", path)


class ArtifactRequestHandler(BaseHTTPRequestHandler):
    server_version = "ToneSightArtifactServer/0.2.6"

    def do_GET(self) -> None:  # noqa: N802 (stdlib method name)
        runs_root = getattr(self.server, "runs_root", "runs")
        html_artifact_path = resolve_html_artifact_path(self.path, runs_root=runs_root)
        if html_artifact_path is not None:
            if not html_artifact_path.exists() or not html_artifact_path.is_file():
                status, payload = _json_error(404, "artifact_not_found", f"Missing artifact: {html_artifact_path}", self.path)
                body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = html_artifact_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        status, payload = get_artifact_response(self.path, runs_root=runs_root)
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (stdlib method name)
        parsed = urlparse(self.path)
        runs_root = getattr(self.server, "runs_root", "runs")
        pipeline_enabled = bool(getattr(self.server, "enable_pipeline", False))
        python_exe = str(getattr(self.server, "python_exe", sys.executable))

        if parsed.path != "/api/pipeline/run":
            status, payload = _json_error(400, "invalid_route", f"Unsupported endpoint: {parsed.path}", parsed.path)
        elif not pipeline_enabled:
            status, payload = _json_error(
                403,
                "pipeline_disabled",
                "Pipeline endpoint is disabled. Restart server with --enable-pipeline to allow POST /api/pipeline/run.",
                parsed.path,
            )
        else:
            ok, request_payload = _read_request_json(self)
            if not ok or request_payload is None:
                status, payload = _json_error(400, "invalid_request", "Expected JSON object body.", parsed.path)
            else:
                status, payload = run_pipeline_request(
                    request_payload,
                    runs_root=runs_root,
                    python_exe=python_exe,
                )

        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib method name)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep server deterministic/quiet in local demos.
        _ = format
        _ = args


def run_server(
    host: str = "127.0.0.1",
    port: int = 8081,
    runs_root: str | Path = "runs",
    *,
    enable_pipeline: bool = False,
) -> None:
    server = ThreadingHTTPServer((host, port), ArtifactRequestHandler)
    setattr(server, "runs_root", str(runs_root))
    setattr(server, "enable_pipeline", bool(enable_pipeline))
    setattr(server, "python_exe", sys.executable)
    print(
        json.dumps(
            {
                "ok": True,
                "host": host,
                "port": port,
                "runs_root": str(runs_root),
                "enable_pipeline": bool(enable_pipeline),
            }
        )
    )
    server.serve_forever()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only ToneSight artifact API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument(
        "--enable-pipeline",
        action="store_true",
        help="Enable local POST /api/pipeline/run endpoint to trigger capture/replay/compare/gate pipeline.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port, runs_root=args.runs_root, enable_pipeline=args.enable_pipeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
