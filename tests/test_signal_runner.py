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


def test_run_signal_pipeline_writes_deterministic_artifacts():
    root = _temp_dir("tmp_signal_runner")
    profile_path = root / "profile.json"
    observations_path = root / "observations.jsonl"
    _write_json(profile_path, _profile())
    _write_jsonl(
        observations_path,
        [
            {
                "schema": "ns8.signal.observation.v1",
                "t": "2026-02-27T10:00:00Z",
                "domain": "tone",
                "entity_type": "speaker",
                "entity_id": "spk_1",
                "stream_id": "s_1",
                "channels": {"valence_bin": 3, "arousal_bin": 6, "dominance_bin": 4},
            },
            {
                "schema": "ns8.signal.observation.v1",
                "t": "2026-02-27T10:01:00Z",
                "domain": "tone",
                "entity_type": "speaker",
                "entity_id": "spk_1",
                "stream_id": "s_1",
                "channels": {"valence_bin": 4, "arousal_bin": 6, "dominance_bin": 4},
            },
        ],
    )
    payload = run_signal_pipeline(str(observations_path), mapping_profile_path=str(profile_path), out_root=str(root))
    out_dir = Path(payload["out_dir"])
    assert (out_dir / "anchor_events.jsonl").exists()
    assert (out_dir / "metrics_summary.json").exists()
    assert (out_dir / "transition_matrix.json").exists()
    assert (out_dir / "density_map.json").exists()
    assert (out_dir / "quarantine.jsonl").exists()
    assert (out_dir / "receipt.json").exists()
    summary = json.loads((out_dir / "metrics_summary.json").read_text(encoding="utf-8"))
    assert summary["count_anchor_events"] == 2
    assert summary["count_quarantine"] == 0
