import json
import shutil
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
