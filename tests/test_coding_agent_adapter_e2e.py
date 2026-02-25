import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.compare_runner import run_compare
from tonesight_ns8.gate_runner import run_gate
from tonesight_ns8.live_runner import run_live_capture, run_live_replay
from tonesight_ns8.report_runner import run_report


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_events(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_coding_agent_adapter_compare_gate_report_flow():
    out_root = _temp_dir("tmp_coding_agent_e2e")
    baseline_events = out_root / "baseline.events.jsonl"
    candidate_events = out_root / "candidate.events.jsonl"

    _write_events(
        baseline_events,
        [
            {
                "event_id": "evt_a_1",
                "source": "coding_agent",
                "timestamp_received": "2026-02-25T12:00:00Z",
                "text": "import os\n\ndef solve(x: int) -> int:\n    return x\n",
                "meta": {
                    "session_id": "s1",
                    "expected_language": "python",
                    "provider": "ollama",
                    "model_tag": "qwen3-coder:latest",
                    "model_digest": "sha256:flow1",
                    "generation_settings": {"temperature": 0, "top_p": 1, "seed": 1},
                },
                "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
            }
        ],
    )
    _write_events(
        candidate_events,
        [
            {
                "event_id": "evt_a_1",
                "source": "coding_agent",
                "timestamp_received": "2026-02-25T12:00:00Z",
                "text": "const solve = (x: number): number => { return x; };\n",
                "meta": {
                    "session_id": "s1",
                    "expected_language": "python",
                    "provider": "ollama",
                    "model_tag": "qwen3-coder:latest",
                    "model_digest": "sha256:flow2",
                    "generation_settings": {"temperature": 0, "top_p": 1, "seed": 1},
                },
                "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
            }
        ],
    )

    baseline_capture = run_live_capture(str(baseline_events), out_root=str(out_root))
    candidate_capture = run_live_capture(str(candidate_events), out_root=str(out_root))
    baseline = run_live_replay(
        baseline_capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        adapter="coding_agent",
    )
    candidate = run_live_replay(
        candidate_capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        adapter="coding_agent",
    )

    compare = run_compare(
        baseline["out_dir"],
        candidate["out_dir"],
        require_dataset_match=False,
        require_pinned_model_identity=False,
    )
    assert compare["compare_summary"]["run_a"]["run_id"] == baseline["run_id"]

    gate = run_gate(
        baseline["out_dir"],
        candidate["out_dir"],
        require_dataset_match=False,
        profile="coding_agent_drift",
    )
    assert gate["decision"] == "incompatible"
    reasons = {item["reason"] for item in gate["incompatibilities"]}
    assert "model_identity_mismatch" in reasons

    report = run_report(
        candidate["out_dir"],
        run_a=baseline["out_dir"],
        require_dataset_match=False,
        profile="coding_agent_drift",
    )
    assert Path(report["report_path"]).exists()
    assert report["report"]["compare_highlights"]["available"] is True
    assert report["report"]["gate_summary"]["available"] is True

