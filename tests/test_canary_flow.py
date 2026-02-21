import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.canary_runner import run_canary


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_canary_replays_same_capture_and_gates():
    root = _temp_dir("tmp_canary")
    baseline_root = root / "baseline"
    candidate_root = root / "candidate"

    payload = run_canary(
        "tests/fixtures/live_capture.small.jsonl",
        baseline_out_root=str(baseline_root),
        candidate_out_root=str(candidate_root),
        baseline_taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        candidate_taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        shadow_strict="quarantine",
        top_n=5,
    )

    assert payload["capture"]["same_capture_id"] is True
    assert Path(payload["baseline"]["out_dir"]).exists()
    assert Path(payload["candidate"]["out_dir"]).exists()
    assert payload["compare_summary"]["run_a"]["run_id"] == payload["baseline"]["run_id"]
    assert payload["compare_summary"]["run_b"]["run_id"] == payload["candidate"]["run_id"]
    assert payload["gate_result"]["decision"] in {"passed", "regressed", "incompatible"}
    assert payload["exit_code"] == payload["gate_result"]["exit_code"]
