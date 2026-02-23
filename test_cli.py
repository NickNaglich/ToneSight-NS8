import json
import os
import shutil
import time
from pathlib import Path
from uuid import uuid4

import pytest

from tonesight_ns8.cli import main


def test_cli_encode_vad(capsys):
    rc = main(["encode", "--family", "TRF", "--r", "6", "--c", "4", "--k", "3", "--V", "7", "--A", "3", "--D", "3"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 0
    assert payload["output"]["A"] == 2


def test_cli_decode(capsys):
    rc = main(["decode", "--family", "TRF", "--r", "6", "--c", "4", "--k", "3"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 0
    assert payload["route"] == {"seed_family": "TLF", "r_prime": 6, "c_prime": 5}


def test_cli_decode_with_mapping_flag(capsys):
    rc = main(["decode", "--family", "TRF", "--r", "6", "--c", "4", "--k", "3", "--mapping", "ns8"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["output"]["A"] == 2


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_cli_eval(capsys):
    out_root = _temp_dir("tmp_runs_cli")
    rc = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    run_dir = out_root / payload["run_id"]
    assert run_dir.exists()
    assert (run_dir / "out.jsonl").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "receipt.json").exists()
    assert payload["trace"]["spec_version"] == "1.0"
    assert payload["trace"]["dataset_hash"]
    assert payload["trace"]["taxonomy_hash"]
    assert payload["trace"]["defaults_hash"]


def test_cli_eval_compare(capsys):
    out_root = _temp_dir("tmp_runs_eval_compare")
    rc1 = main(
        [
            "eval-compare",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    payload1 = json.loads(capsys.readouterr().out)
    assert rc1 == 0
    assert payload1["previous_run"] is None

    rc2 = main(
        [
            "eval-compare",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    payload2 = json.loads(capsys.readouterr().out)
    assert rc2 == 0
    assert payload2["previous_run"] is not None
    assert payload2["compare"] is not None
    assert payload2["trace"]["spec_version"] == "1.0"
    assert payload2["trace"]["dataset_hash"]
    assert payload2["trace"]["taxonomy_hash"]
    assert payload2["trace"]["defaults_hash"]


def test_cli_triage(capsys):
    out_root = _temp_dir("tmp_runs_triage_cli")
    rc_eval = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    eval_payload = json.loads(capsys.readouterr().out)
    assert rc_eval == 0
    run_dir = out_root / eval_payload["run_id"]

    rc_triage = main(["triage", "--run-b", str(run_dir), "--top-n", "3", "--format", "jsonl"])
    triage_payload = json.loads(capsys.readouterr().out)
    assert rc_triage == 0
    assert triage_payload["mode"] == "single"
    assert triage_payload["top_n_returned"] == 3
    assert Path(triage_payload["output_path"]).exists()


def test_cli_bundle(capsys):
    out_root = _temp_dir("tmp_runs_bundle_cli")
    rc_eval = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    eval_payload = json.loads(capsys.readouterr().out)
    assert rc_eval == 0
    run_dir = out_root / eval_payload["run_id"]
    rc_bundle = main(["bundle", "--run-b", str(run_dir)])
    bundle_payload = json.loads(capsys.readouterr().out)
    assert rc_bundle == 0
    assert bundle_payload["mode"] == "run_only"
    assert bundle_payload["external_safe"] is True
    assert Path(bundle_payload["bundle_path"]).exists()


def test_cli_trend(capsys):
    out_root = _temp_dir("tmp_runs_trend_cli")
    rc_eval = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    _ = json.loads(capsys.readouterr().out)
    assert rc_eval == 0
    rc_trend = main(["trend", "--out-root", str(out_root), "--group-by", "source"])
    trend_payload = json.loads(capsys.readouterr().out)
    assert rc_trend == 0
    assert trend_payload["run_count"] == 1
    assert Path(trend_payload["trend_summary_path"]).exists()


def test_cli_encode_label_requires_taxonomy_returns_json_error(capsys):
    rc = main(["encode", "--family", "TRF", "--r", "6", "--c", "4", "--k", "3", "--label", "empathetic"])
    err = json.loads(capsys.readouterr().err)
    assert rc == 2
    assert err["error"]["type"] == "ValueError"
    assert "--taxonomy is required" in err["error"]["message"]


def test_cli_rejects_out_of_range_ns8_inputs():
    with pytest.raises(SystemExit):
        main(["decode", "--family", "TRF", "--r", "9", "--c", "4", "--k", "3"])


def test_cli_live_capture_and_replay(capsys):
    out_root = _temp_dir("tmp_live_cli")
    rc_capture = main(
        [
            "live-capture",
            "--events",
            "tests/fixtures/live_capture.small.jsonl",
            "--out-root",
            str(out_root),
        ]
    )
    capture_payload = json.loads(capsys.readouterr().out)
    assert rc_capture == 0
    assert Path(capture_payload["capture_dir"]).exists()

    rc_replay = main(
        [
            "live-replay",
            "--capture",
            capture_payload["capture_dir"],
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
            "--shadow-strict",
            "quarantine",
        ]
    )
    replay_payload = json.loads(capsys.readouterr().out)
    assert rc_replay == 0
    run_dir = Path(replay_payload["out_dir"])
    assert run_dir.exists()
    assert (run_dir / "out.jsonl").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "report.html").exists()
    assert (run_dir / "receipt.json").exists()


def test_cli_live_verify(capsys):
    out_root = _temp_dir("tmp_live_verify_cli")
    rc_capture = main(
        [
            "live-capture",
            "--events",
            "tests/fixtures/live_capture.small.jsonl",
            "--out-root",
            str(out_root),
        ]
    )
    capture_payload = json.loads(capsys.readouterr().out)
    assert rc_capture == 0

    rc_verify = main(
        [
            "live-verify",
            "--capture",
            capture_payload["capture_dir"],
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
            "--shadow-strict",
            "quarantine",
        ]
    )
    verify_payload = json.loads(capsys.readouterr().out)
    assert rc_verify == 0
    assert verify_payload["stable"] is True
    assert verify_payload["mismatched_artifacts"] == []


def test_cli_canary(capsys):
    root = _temp_dir("tmp_canary_cli")
    rc = main(
        [
            "canary",
            "--capture",
            "tests/fixtures/live_capture.small.jsonl",
            "--baseline-out-root",
            str(root / "baseline"),
            "--candidate-out-root",
            str(root / "candidate"),
            "--baseline-taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--candidate-taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--top-n",
            "5",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == payload["gate_result"]["exit_code"]
    assert payload["capture"]["same_capture_id"] is True
    assert "compare_summary" in payload
    assert "gate_result" in payload


def test_cli_incident(capsys):
    out_root = _temp_dir("tmp_incident_cli")
    rc_a = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    payload_a = json.loads(capsys.readouterr().out)
    assert rc_a == 0
    run_a = out_root / payload_a["run_id"]

    rc_b = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "2",
        ]
    )
    payload_b = json.loads(capsys.readouterr().out)
    assert rc_b == 0
    run_b = out_root / payload_b["run_id"]

    rc_incident = main(
        [
            "incident",
            "--run-a",
            str(run_a),
            "--run-b",
            str(run_b),
            "--top-n",
            "20",
        ]
    )
    incident_payload = json.loads(capsys.readouterr().out)
    assert rc_incident == 0
    assert Path(incident_payload["compare_summary_path"]).exists()
    assert Path(incident_payload["triage_output_path"]).exists()
    assert Path(incident_payload["bundle_path"]).exists()
    assert Path(incident_payload["incident_report_path"]).exists()


def test_cli_index_runs(capsys):
    out_root = _temp_dir("tmp_index_cli")
    rc_eval = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    _ = json.loads(capsys.readouterr().out)
    assert rc_eval == 0

    rc_index = main(["index-runs", "--out-root", str(out_root)])
    payload = json.loads(capsys.readouterr().out)
    assert rc_index == 0
    assert payload["run_count"] >= 1
    assert Path(payload["index_path"]).exists()


def test_cli_report(capsys):
    out_root = _temp_dir("tmp_report_cli")
    rc_a = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "3",
        ]
    )
    payload_a = json.loads(capsys.readouterr().out)
    assert rc_a == 0
    run_a = out_root / payload_a["run_id"]

    rc_b = main(
        [
            "eval",
            "--goldset",
            "data/goldset.jsonl",
            "--out-root",
            str(out_root),
            "--taxonomy",
            "taxonomy/tone_taxonomy.v1.json",
            "--threshold-l1",
            "2",
        ]
    )
    payload_b = json.loads(capsys.readouterr().out)
    assert rc_b == 0
    run_b = out_root / payload_b["run_id"]

    rc_report = main(["report", "--run-a", str(run_a), "--run-b", str(run_b), "--top-n", "5"])
    report_payload = json.loads(capsys.readouterr().out)
    assert rc_report == 0
    assert Path(report_payload["report_path"]).exists()
    assert report_payload["report"]["compare_highlights"]["available"] is True
    assert report_payload["report"]["gate_summary"]["available"] is True


def test_cli_data_lint(capsys):
    rc_clean = main(["data-lint", "--dataset", "data/goldset.jsonl"])
    clean_payload = json.loads(capsys.readouterr().out)
    assert rc_clean == 0
    assert clean_payload["passed"] is True
    assert clean_payload["violation_count"] == 0

    root = _temp_dir("tmp_cli_data_lint_bad")
    bad_path = root / "bad.jsonl"
    bad_path.write_text(
        "\n".join(
            [
                '{"id":"dup_1","target_vad":{"V":9,"A":3,"D":3},"tags":["ok"]}',
                '{"id":"dup_1","target_vad":{"V":7,"A":3,"D":3},"tags":["ok"]}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc_bad = main(["data-lint", "--dataset", str(bad_path)])
    bad_payload = json.loads(capsys.readouterr().out)
    assert rc_bad == 2
    assert bad_payload["passed"] is False
    assert bad_payload["violation_count"] >= 2


def test_cli_release_check(capsys):
    rc = main(["release-check", "--goldset", "data/goldset.jsonl", "--taxonomy", "taxonomy/tone_taxonomy.v1.json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["decision"] == "passed"
    assert payload["failed_checks"] == []

    root = _temp_dir("tmp_cli_release_check_bad")
    bad_path = root / "bad.jsonl"
    bad_path.write_text('{"id":"dup","target_vad":{"V":9,"A":3,"D":3},"tags":["ok"]}\n', encoding="utf-8")
    rc_bad = main(["release-check", "--goldset", str(bad_path), "--taxonomy", "taxonomy/tone_taxonomy.v1.json"])
    bad_payload = json.loads(capsys.readouterr().out)
    assert rc_bad == 2
    assert bad_payload["decision"] == "failed"
    assert "dataset_lint" in bad_payload["failed_checks"]


def test_cli_purge_dry_run_and_apply(capsys):
    out_root = _temp_dir("tmp_purge_cli")
    old_run = out_root / "run_old"
    old_run.mkdir(parents=True, exist_ok=True)
    (old_run / "out.jsonl").write_text("{}", encoding="utf-8")
    ts = time.time() - (40 * 86400)
    os.utime(old_run, (ts, ts))
    os.utime(old_run / "out.jsonl", (ts, ts))

    rc_dry = main(["purge", "--out-root", str(out_root), "--older-than-days", "30"])
    dry_payload = json.loads(capsys.readouterr().out)
    assert rc_dry == 0
    assert dry_payload["dry_run"] is True
    assert dry_payload["would_delete_count"] >= 1
    assert old_run.exists()

    rc_apply = main(["purge", "--out-root", str(out_root), "--older-than-days", "30", "--apply"])
    apply_payload = json.loads(capsys.readouterr().out)
    assert rc_apply == 0
    assert apply_payload["dry_run"] is False
    assert apply_payload["would_delete_count"] >= 1
    assert apply_payload["deleted_count"] + apply_payload["failed_count"] >= 1
