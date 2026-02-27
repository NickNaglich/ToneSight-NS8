import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.signal_runner import run_signal_pipeline


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _profile() -> dict:
    return {
        "schema": "ns8.mapping.profile.v1",
        "name": "tone_vad",
        "version": "v1",
        "n": 8,
        "channels": {
            "valence_bin": {"required": True, "range": [1, 8]},
            "arousal_bin": {"required": True, "range": [1, 8]},
            "dominance_bin": {"required": True, "range": [1, 8]},
        },
        "compose": {
            "mode": "multi_channel_fold",
            "channel_order": ["valence_bin", "arousal_bin", "dominance_bin"],
        },
        "validation": {"reject_on_out_of_range": True, "missing_channel_policy": "quarantine"},
    }


def test_signal_metrics_constant_state_has_zero_volatility():
    root = _temp_dir("tmp_signal_metrics_constant")
    profile_path = root / "profile.json"
    observations_path = root / "observations.jsonl"
    _write_json(profile_path, _profile())
    rows = []
    for i in range(4):
        rows.append(
            {
                "schema": "ns8.signal.observation.v1",
                "t": f"2026-02-27T10:0{i}:00Z",
                "domain": "tone",
                "entity_type": "speaker",
                "entity_id": "spk_1",
                "stream_id": "s_1",
                "channels": {"valence_bin": 3, "arousal_bin": 6, "dominance_bin": 4},
            }
        )
    _write_jsonl(observations_path, rows)
    payload = run_signal_pipeline(str(observations_path), mapping_profile_path=str(profile_path), out_root=str(root))
    summary = payload["metrics_summary"]
    assert summary["volatility_mean_step_distance"] == 0.0
    assert summary["adjacency_ratio"] == 1.0
    assert summary["spike_rate"] == 0.0
    assert summary["persistence_mean_dwell"] == 4.0
