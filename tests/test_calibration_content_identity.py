"""Calibration replay and shared compatibility contracts; synthetic VAD only."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tonesight_ns8.compatibility import compatibility_issues, identity_fields
from tonesight_ns8.compare_runner import CompareInputError, run_compare
from tonesight_ns8.eval_compare_runner import run_eval_compare
from tonesight_ns8.eval_runner import run_eval
from tonesight_ns8.gate_runner import run_gate


def calibration_bytes(value=7):
    return (json.dumps({"label_overrides": {"calm": {"V": value, "A": value, "D": value}}}) + "\n").encode()


def fixture_paths(tmp_path):
    dataset = tmp_path / "toy.jsonl"
    rows = [
        {"id": "prediction", "label": "calm", "target_vad": {"V": 7, "A": 7, "D": 7}},
        {"id": "gold", "target_vad": {"V": 2, "A": 2, "D": 2}, "gold_vad": {"V": 3, "A": 3, "D": 3}},
        {"id": "self", "target_vad": {"V": 4, "A": 4, "D": 4}},
    ]
    dataset.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    calibration = tmp_path / "calibration.json"
    calibration.write_bytes(calibration_bytes())
    return dataset, calibration


def evaluate(tmp_path, dataset, calibration=None):
    return run_eval(str(dataset), out_root=str(tmp_path / "runs"),
                    taxonomy_path="taxonomy/tone_taxonomy.v1.json", threshold_l1=3,
                    calibration_path=str(calibration) if calibration is not None else None,
                    capture_gpu=False, mlflow_tracking_uri=None)


def test_same_path_changed_bytes_rejected_by_compare_and_gate(tmp_path):
    dataset, calibration = fixture_paths(tmp_path)
    before = calibration.read_bytes()
    first = evaluate(tmp_path, dataset, calibration)
    calibration.write_bytes(calibration_bytes(1))
    second = evaluate(tmp_path, dataset, calibration)
    assert first["receipt"]["calibration_hash"] == hashlib.sha256(before).hexdigest()
    assert first["receipt"]["calibration_hash"] != second["receipt"]["calibration_hash"]
    assert first["summary"]["avg_l1"] == 1.0
    assert second["summary"]["avg_l1"] == 7.0
    with pytest.raises(CompareInputError, match="calibration_identity_mismatch"):
        run_compare(first["out_dir"], second["out_dir"])
    gate = run_gate(first["out_dir"], second["out_dir"])
    assert gate["exit_code"] == 3 and gate["decision"] == "incompatible"
    assert "calibration_identity_mismatch" in {x["reason"] for x in gate["incompatibilities"]}


def test_identical_snapshot_relocated_replays_stably_and_is_compatible(tmp_path):
    dataset, calibration = fixture_paths(tmp_path)
    moved = tmp_path / "relocated.json"
    moved.write_bytes(calibration.read_bytes())
    first = evaluate(tmp_path, dataset, calibration)
    second = evaluate(tmp_path, dataset, moved)
    assert first["receipt"]["config"]["calibration_path"] != second["receipt"]["config"]["calibration_path"]
    assert first["receipt"]["calibration_hash"] == second["receipt"]["calibration_hash"]
    assert compatibility_issues(first["receipt"], second["receipt"]) == []
    assert (Path(first["out_dir"]) / "out.jsonl").read_bytes() == (Path(second["out_dir"]) / "out.jsonl").read_bytes()
    def stable(summary):
        return {k: v for k, v in summary.items() if k not in {"run_id", "eval_duration_seconds"}}
    assert stable(first["summary"]) == stable(second["summary"])
    assert run_compare(first["out_dir"], second["out_dir"])["compare_summary"]["metrics"]["delta_avg_l1"] == 0
    assert run_gate(first["out_dir"], second["out_dir"])["exit_code"] == 0


def test_snapshot_used_for_scoring_and_hash_even_if_path_changes_after_read(tmp_path, monkeypatch):
    dataset, calibration = fixture_paths(tmp_path)
    original = calibration.read_bytes()
    replacement = calibration_bytes(1)
    read_bytes = Path.read_bytes
    reads = []
    def racing_read(path):
        raw = read_bytes(path)
        if path == calibration:
            reads.append(raw)
            calibration.write_bytes(replacement)
        return raw
    monkeypatch.setattr(Path, "read_bytes", racing_read)
    result = evaluate(tmp_path, dataset, calibration)
    assert reads == [original]
    assert read_bytes(calibration) == replacement
    assert result["receipt"]["calibration_hash"] == hashlib.sha256(original).hexdigest()
    assert result["summary"]["avg_l1"] == 1.0


def test_no_calibration_and_uncalibrated_legacy_remain_compatible(tmp_path):
    dataset, _ = fixture_paths(tmp_path)
    first, second = evaluate(tmp_path, dataset), evaluate(tmp_path, dataset)
    assert first["receipt"]["calibration_hash"] is None
    legacy = copy.deepcopy(first["receipt"])
    del legacy["calibration_hash"]
    assert identity_fields(legacy)["calibration_identity_kind"] == "none"
    assert compatibility_issues(legacy, second["receipt"]) == []
    (Path(first["out_dir"]) / "receipt.json").write_text(json.dumps(legacy), encoding="utf-8")
    assert run_gate(first["out_dir"], second["out_dir"])["exit_code"] == 0
    assert run_compare(first["out_dir"], second["out_dir"])["compare_summary"]["metrics"]["delta_avg_l1"] == 0


def test_calibrated_legacy_receipts_are_explicitly_unverified(tmp_path):
    dataset, calibration = fixture_paths(tmp_path)
    first, second = evaluate(tmp_path, dataset, calibration), evaluate(tmp_path, dataset, calibration)
    legacy = copy.deepcopy(first["receipt"])
    del legacy["calibration_hash"]
    assert identity_fields(legacy)["calibration_identity_kind"] == "legacy_unverified"
    assert compatibility_issues(legacy, legacy)[0]["reason"] == "calibration_content_unverified"
    (Path(first["out_dir"]) / "receipt.json").write_text(json.dumps(legacy), encoding="utf-8")
    with pytest.raises(CompareInputError, match="calibration_content_unverified"):
        run_compare(first["out_dir"], second["out_dir"])
    gate = run_gate(first["out_dir"], second["out_dir"])
    assert gate["exit_code"] == 3
    assert "calibration_content_unverified" in {x["reason"] for x in gate["incompatibilities"]}


@pytest.mark.parametrize("digest", [None, "abc", "g" * 64, "A" * 64, True, [], {}])
def test_malformed_hash_never_compares_as_verified(digest):
    receipt = {"calibration_hash": digest, "config": {"calibration_path": "configured.json"}}
    assert compatibility_issues(receipt, receipt)[0]["reason"] == "calibration_hash_invalid"


@pytest.mark.parametrize("raw", [None, b"{broken", b"[]", b'{"label_overrides":[]}', b'{"label_overrides":{"calm":{}}}'])
def test_missing_malformed_calibration_fails_before_run_output(tmp_path, raw):
    dataset, calibration = fixture_paths(tmp_path)
    if raw is None:
        calibration.unlink()
    else:
        calibration.write_bytes(raw)
    with pytest.raises((FileNotFoundError, ValueError)):
        evaluate(tmp_path, dataset, calibration)
    assert not (tmp_path / "runs").exists()


def test_eval_compare_does_not_select_same_path_changed_content(tmp_path):
    dataset, calibration = fixture_paths(tmp_path)
    evaluate(tmp_path, dataset, calibration)
    calibration.write_bytes(calibration_bytes(1))
    result = run_eval_compare(str(dataset), out_root=str(tmp_path / "runs"),
                              taxonomy_path="taxonomy/tone_taxonomy.v1.json",
                              calibration_path=str(calibration), threshold_l1=3)
    assert result["previous_run"] is None and result["compare"] is None
    assert result["compare_skipped_reason"] == "no_compatible_prior_run"
    assert result["incompatible_previous_runs"][0]["reason"] == "calibration_identity_mismatch"


def test_existing_identities_still_gate_with_matching_calibration_hash(tmp_path):
    dataset, calibration = fixture_paths(tmp_path)
    receipt = evaluate(tmp_path, dataset, calibration)["receipt"]
    changed = copy.deepcopy(receipt)
    changed["spec_version"] = "other"
    changed["dataset_hash"] = "other"
    changed["taxonomy_hash"] = "other"
    reasons = {x["reason"] for x in compatibility_issues(receipt, changed)}
    assert {"spec_version_mismatch", "dataset_hash_mismatch", "taxonomy_identity_mismatch"} <= reasons
