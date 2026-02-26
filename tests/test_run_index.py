import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.run_index import run_index, run_index_json


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _mk_run(path: Path, *, run_id: str, source: str, source_mode: str) -> None:
    rows = [{"id": "r1", "source": source, "compliance_l1": 0, "pass": True}]
    path.mkdir(parents=True, exist_ok=True)
    _write_json(
        path / "eval_summary.json",
        {"run_id": run_id, "count_rows": 1, "pass_rate": 1.0, "avg_l1": 0.0, "p95_l1": 0.0},
    )
    _write_json(
        path / "receipt.json",
        {
            "spec_version": "1.0",
            "run_id": run_id,
            "dataset_hash": "ds123",
            "taxonomy_hash": "tax123",
            "defaults_hash": "def123",
            "mapping_id": "ns8",
            "mapping_version": "1.0",
            "artifacts": {
                "out_jsonl": str(path / "out.jsonl"),
                "eval_summary_json": str(path / "eval_summary.json"),
                "report_html": str(path / "report.html"),
                "receipt_json": str(path / "receipt.json"),
            },
            "config": {"source_mode": source_mode},
        },
    )
    _write_jsonl(path / "out.jsonl", rows)
    (path / "report.html").write_text("<html></html>\n", encoding="utf-8")


def test_run_index_stable_order_and_schema():
    root = _temp_dir("tmp_run_index")
    _mk_run(root / "run_b", run_id="run_002", source="chat", source_mode="eval")
    _mk_run(root / "run_a", run_id="run_001", source="live", source_mode="live_replay")

    payload = run_index(str(root))
    index_path = Path(payload["index_path"])
    assert index_path.exists()
    lines = index_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["run_id"] == "run_001"
    assert second["run_id"] == "run_002"
    assert first["source_label"] == "live_replay"
    assert second["source_label"] == "eval"
    assert first["source_labels"] == ["live"]
    assert second["source_labels"] == ["chat"]
    assert set(first["artifacts"]) == {"eval_summary_json", "out_jsonl", "receipt_json", "report_html"}


def test_run_index_idempotent_for_unchanged_runs():
    root = _temp_dir("tmp_run_index_idempotent")
    _mk_run(root / "run_1", run_id="run_001", source="chat", source_mode="eval")
    _mk_run(root / "run_2", run_id="run_002", source="chat", source_mode="eval")

    first = run_index(str(root))
    first_bytes = Path(first["index_path"]).read_bytes()
    second = run_index(str(root))
    second_bytes = Path(second["index_path"]).read_bytes()
    assert first_bytes == second_bytes


def test_run_index_json_is_generated_from_index_jsonl():
    root = _temp_dir("tmp_run_index_json")
    _mk_run(root / "run_b", run_id="run_002", source="chat", source_mode="eval")
    _mk_run(root / "run_a", run_id="run_001", source="live", source_mode="live_replay")

    jsonl_payload = run_index(str(root))
    json_payload = run_index_json(str(root))

    jsonl_path = Path(jsonl_payload["index_path"])
    json_path = Path(json_payload["index_json_path"])
    assert jsonl_path.exists()
    assert json_path.exists()

    json_rows = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(json_rows, list)
    assert len(json_rows) == 2
    assert json_rows[0]["run_id"] == "run_001"
    assert json_rows[1]["run_id"] == "run_002"


def test_run_index_json_idempotent_for_unchanged_runs():
    root = _temp_dir("tmp_run_index_json_idempotent")
    _mk_run(root / "run_1", run_id="run_001", source="chat", source_mode="eval")
    _mk_run(root / "run_2", run_id="run_002", source="chat", source_mode="eval")
    run_index(str(root))

    first = run_index_json(str(root))
    first_bytes = Path(first["index_json_path"]).read_bytes()
    second = run_index_json(str(root))
    second_bytes = Path(second["index_json_path"]).read_bytes()
    assert first_bytes == second_bytes
