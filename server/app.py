"""Minimal read-only static artifact API for ToneSight runs."""

from __future__ import annotations

import argparse
import json
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
    server_version = "ToneSightArtifactServer/0.1"

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
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = html_artifact_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
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
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib method name)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep server deterministic/quiet in local demos.
        _ = format
        _ = args


def run_server(host: str = "127.0.0.1", port: int = 8081, runs_root: str | Path = "runs") -> None:
    server = ThreadingHTTPServer((host, port), ArtifactRequestHandler)
    setattr(server, "runs_root", str(runs_root))
    print(json.dumps({"ok": True, "host": host, "port": port, "runs_root": str(runs_root)}))
    server.serve_forever()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only ToneSight artifact API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--runs-root", default="runs")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port, runs_root=args.runs_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
