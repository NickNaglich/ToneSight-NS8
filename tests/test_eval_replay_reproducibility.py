import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.eval_runner import run_eval


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_eval_summary(summary: dict) -> dict:
    payload = dict(summary)
    payload.pop("run_id", None)
    payload.pop("eval_duration_seconds", None)
    return payload


def test_eval_replay_is_reproducible_from_receipt_config():
    root = _temp_dir("tmp_eval_replay")
    first = run_eval(
        "data/goldset.jsonl",
        out_root=str(root / "runs_a"),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    first_out_dir = Path(first["out_dir"])
    first_receipt = _load_json(first_out_dir / "receipt.json")

    first_config = first_receipt["config"]
    second = run_eval(
        first_receipt["dataset_path"],
        out_root=str(root / "runs_b"),
        taxonomy_path=first_config["taxonomy_path"],
        threshold_l1=int(first_config["threshold_l1"]),
        calibration_path=first_config["calibration_path"],
        capture_gpu=bool(first_config["capture_gpu"]),
        mlflow_tracking_uri=first_config["mlflow_tracking_uri"],
    )
    second_out_dir = Path(second["out_dir"])
    second_receipt = _load_json(second_out_dir / "receipt.json")

    assert first["run_id"] != second["run_id"]
    assert first_receipt["dataset_hash"] == second_receipt["dataset_hash"]
    assert first_receipt["taxonomy_hash"] == second_receipt["taxonomy_hash"]
    assert first_receipt["defaults_hash"] == second_receipt["defaults_hash"]

    first_out_hash = _sha256(first_out_dir / "out.jsonl")
    second_out_hash = _sha256(second_out_dir / "out.jsonl")
    assert first_out_hash == second_out_hash
    assert (first_out_dir / "out.jsonl").read_bytes() == (second_out_dir / "out.jsonl").read_bytes()

    first_summary = _load_json(first_out_dir / "eval_summary.json")
    second_summary = _load_json(second_out_dir / "eval_summary.json")
    assert _canonical_eval_summary(first_summary) == _canonical_eval_summary(second_summary)
    assert isinstance(first_summary["eval_duration_seconds"], float)
    assert isinstance(second_summary["eval_duration_seconds"], float)

