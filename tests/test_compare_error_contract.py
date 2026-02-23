import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.cli import main
from tonesight_ns8.compare_runner import CompareInputError, run_compare


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _mk_run(path: Path, *, run_id: str, dataset_hash: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    rows = [{"id": "id_1", "label": "calm", "compliance_l1": 0, "delta_v": 0, "delta_a": 0, "delta_d": 0, "pass": True}]
    _write_json(
        path / "eval_summary.json",
        {
            "run_id": run_id,
            "count_rows": 1,
            "threshold_l1": 3,
            "pass_count": 1,
            "pass_rate": 1.0,
            "avg_l1": 0.0,
            "p95_l1": 0.0,
        },
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": dataset_hash,
        },
    )
    _write_jsonl(path / "out.jsonl", rows)


def test_compare_missing_required_file_raises_actionable_error():
    root = _temp_dir("tmp_compare_err_missing")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(run_a, run_id="run_A", dataset_hash="ds123")
    run_b.mkdir(parents=True, exist_ok=True)

    try:
        run_compare(str(run_a), str(run_b))
        assert False, "Expected CompareInputError"
    except CompareInputError as exc:
        assert str(exc) == "missing_required_file:eval_summary.json"


def test_compare_malformed_jsonl_raises_actionable_error():
    root = _temp_dir("tmp_compare_err_jsonl")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(run_a, run_id="run_A", dataset_hash="ds123")
    _mk_run(run_b, run_id="run_B", dataset_hash="ds123")
    (run_b / "out.jsonl").write_text("{bad json}\n", encoding="utf-8")

    try:
        run_compare(str(run_a), str(run_b))
        assert False, "Expected CompareInputError"
    except CompareInputError as exc:
        assert str(exc).startswith("malformed_jsonl:out.jsonl:line=1:col=")


def test_compare_incompatible_receipts_raise_actionable_error():
    root = _temp_dir("tmp_compare_err_incompat")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(run_a, run_id="run_A", dataset_hash="ds123")
    _mk_run(run_b, run_id="run_B", dataset_hash="ds999")

    try:
        run_compare(str(run_a), str(run_b))
        assert False, "Expected CompareInputError"
    except CompareInputError as exc:
        assert str(exc) == "incompatible_receipts:dataset_hash:ds123!=ds999"


def test_cli_compare_error_payload_is_deterministic(capsys):
    root = _temp_dir("tmp_compare_err_cli")
    run_a = root / "run_A"
    run_b = root / "run_B"
    _mk_run(run_a, run_id="run_A", dataset_hash="ds123")
    _mk_run(run_b, run_id="run_B", dataset_hash="ds123")
    (run_b / "eval_summary.json").write_text("{bad", encoding="utf-8")

    rc = main(["compare", str(run_a), str(run_b)])
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert rc == 2
    assert payload["error"]["type"] == "CompareInputError"
    assert payload["error"]["message"].startswith("malformed_json:eval_summary.json:line=1:col=")
