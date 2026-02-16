import json
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


def test_cli_eval(capsys):
    out_root = Path(".agent") / f"tmp_runs_cli_{uuid4().hex}"
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


def test_cli_eval_compare(capsys):
    out_root = Path(".agent") / f"tmp_runs_eval_compare_{uuid4().hex}"
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


def test_cli_encode_label_requires_taxonomy_returns_json_error(capsys):
    rc = main(["encode", "--family", "TRF", "--r", "6", "--c", "4", "--k", "3", "--label", "empathetic"])
    err = json.loads(capsys.readouterr().err)
    assert rc == 2
    assert err["error"]["type"] == "ValueError"
    assert "--taxonomy is required" in err["error"]["message"]


def test_cli_rejects_out_of_range_ns8_inputs():
    with pytest.raises(SystemExit):
        main(["decode", "--family", "TRF", "--r", "9", "--c", "4", "--k", "3"])
