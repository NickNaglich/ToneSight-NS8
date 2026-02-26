import json
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_ui_demo_script_skip_servers_writes_expected_artifacts():
    out_root = _temp_dir("tmp_ui_demo_script")
    script = Path("scripts/demo_ui_drift_gate_2min.ps1")
    assert script.exists()

    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-OutRoot",
        str(out_root),
        "-SkipServers",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert "UI detail:" in proc.stdout
    assert "UI compare:" in proc.stdout
    assert "UI gate:" in proc.stdout

    index_json = out_root / "index.json"
    assert index_json.exists()
    rows = json.loads(index_json.read_text(encoding="utf-8"))
    assert isinstance(rows, list)
    assert len(rows) >= 2

    run_dirs = sorted([p for p in out_root.iterdir() if p.is_dir() and p.name.startswith("run_")], key=lambda p: p.name)
    assert len(run_dirs) >= 2
    baseline = run_dirs[-2]
    candidate = run_dirs[-1]
    gate_artifact = candidate / "comparisons" / baseline.name / "gate_result.json"
    compare_artifact = candidate / "comparisons" / baseline.name / "compare_summary.json"
    assert gate_artifact.exists()
    assert compare_artifact.exists()

    gate_payload = json.loads(gate_artifact.read_text(encoding="utf-8"))
    assert gate_payload.get("decision") in ("regressed", "passed", "incompatible")
    assert int(gate_payload.get("exit_code")) in (0, 2, 3)

    shutil.rmtree(out_root, ignore_errors=True)
