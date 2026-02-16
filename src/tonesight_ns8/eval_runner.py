"""Deterministic goldset evaluation runner."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .defaults import EVAL_DEFAULTS
from .taxonomy import get_vad, load_taxonomy


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def _l1(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(round(0.95 * (len(sorted_vals) - 1)))
    return float(sorted_vals[idx])


def _dataset_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:12]


def _load_calibration(calibration_path: str | None) -> dict[str, tuple[int, int, int]]:
    if not calibration_path:
        return {}
    payload = json.loads(Path(calibration_path).read_text(encoding="utf-8"))
    overrides = payload.get("label_overrides", {})
    out: dict[str, tuple[int, int, int]] = {}
    for label, vad in overrides.items():
        out[str(label)] = (int(vad["V"]), int(vad["A"]), int(vad["D"]))
    return out


def _gpu_snapshot() -> dict[str, Any]:
    if shutil.which("nvidia-smi") is None:
        return {"available": False, "reason": "nvidia-smi not found"}
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return {"available": True, "rows": rows}
    except Exception as exc:  # pragma: no cover
        return {"available": False, "reason": str(exc)}


def _maybe_log_mlflow(
    *,
    tracking_uri: str | None,
    result: dict[str, Any],
    out_dir: Path,
    threshold_l1: int,
    taxonomy_path: str,
    calibration_path: str | None,
) -> dict[str, Any] | None:
    if not tracking_uri:
        return None
    try:
        import mlflow  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"enabled": False, "reason": f"mlflow import failed: {exc}"}

    mlflow.set_tracking_uri(tracking_uri)
    with mlflow.start_run() as run:
        mlflow.log_param("threshold_l1", threshold_l1)
        mlflow.log_param("taxonomy_path", taxonomy_path)
        mlflow.log_param("calibration_path", calibration_path or "")
        summary = result["summary"]
        mlflow.log_metric("pass_rate", float(summary["pass_rate"]))
        mlflow.log_metric("avg_l1", float(summary["avg_l1"]))
        mlflow.log_metric("p95_l1", float(summary["p95_l1"]))
        mlflow.log_artifact(str(out_dir / "out.jsonl"))
        mlflow.log_artifact(str(out_dir / "eval_summary.json"))
        mlflow.log_artifact(str(out_dir / "receipt.json"))
        return {"enabled": True, "run_id": run.info.run_id}


def run_eval(
    goldset_path: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    threshold_l1: int = EVAL_DEFAULTS["threshold_l1"],
    calibration_path: str | None = EVAL_DEFAULTS["calibration_path"],
    capture_gpu: bool = EVAL_DEFAULTS["capture_gpu"],
    mlflow_tracking_uri: str | None = EVAL_DEFAULTS["mlflow_tracking_uri"],
) -> dict[str, Any]:
    """Run deterministic eval and write out.jsonl, eval_summary.json, receipt.json."""
    gpath = Path(goldset_path)
    rows = _read_jsonl(gpath)
    taxonomy = load_taxonomy(taxonomy_path)
    calibration = _load_calibration(calibration_path)

    d_hash = _dataset_hash(gpath)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"run_{ts}_{d_hash}"

    out_dir = Path(out_root) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    gpu_before = _gpu_snapshot() if capture_gpu else None

    scored: list[dict[str, Any]] = []
    compliance_l1_values: list[float] = []
    accuracy_l1_values: list[float] = []
    pass_count = 0

    for row in rows:
        target = row["target_vad"]
        target_vad = (int(target["V"]), int(target["A"]), int(target["D"]))

        label = row.get("label")
        if label:
            pred_vad = calibration.get(str(label), get_vad(label, taxonomy))
        elif row.get("gold_vad"):
            g = row["gold_vad"]
            pred_vad = (int(g["V"]), int(g["A"]), int(g["D"]))
        else:
            pred_vad = target_vad

        c_l1 = _l1(pred_vad, target_vad)
        passed = c_l1 <= threshold_l1
        pass_count += 1 if passed else 0
        compliance_l1_values.append(float(c_l1))

        a_l1 = None
        if row.get("gold_vad"):
            g = row["gold_vad"]
            gold_vad = (int(g["V"]), int(g["A"]), int(g["D"]))
            a_l1 = _l1(pred_vad, gold_vad)
            accuracy_l1_values.append(float(a_l1))

        scored.append(
            {
                "id": row.get("id"),
                "label": label,
                "target_vad": {"V": target_vad[0], "A": target_vad[1], "D": target_vad[2]},
                "pred_vad": {"V": pred_vad[0], "A": pred_vad[1], "D": pred_vad[2]},
                "gold_vad": row.get("gold_vad"),
                "compliance_l1": c_l1,
                "accuracy_l1": a_l1,
                "pass": passed,
            }
        )

    total = len(scored)
    summary = {
        "run_id": run_id,
        "count_rows": total,
        "threshold_l1": threshold_l1,
        "pass_count": pass_count,
        "pass_rate": (pass_count / total) if total else 0.0,
        "avg_l1": (sum(compliance_l1_values) / total) if total else 0.0,
        "p95_l1": _p95(compliance_l1_values),
        "avg_accuracy_l1": (sum(accuracy_l1_values) / len(accuracy_l1_values)) if accuracy_l1_values else None,
    }

    receipt = {
        "spec_version": "1.0",
        "run_id": run_id,
        "dataset_path": str(gpath),
        "dataset_hash": d_hash,
        "row_count": total,
        "config": {
            "threshold_l1": threshold_l1,
            "taxonomy_path": taxonomy_path,
            "calibration_path": calibration_path,
            "capture_gpu": capture_gpu,
            "mlflow_tracking_uri": mlflow_tracking_uri,
        },
        "artifacts": {
            "out_jsonl": str(out_dir / "out.jsonl"),
            "eval_summary_json": str(out_dir / "eval_summary.json"),
            "receipt_json": str(out_dir / "receipt.json"),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if gpu_before is not None:
        receipt["artifacts"]["gpu_before_json"] = str(out_dir / "gpu_before.json")

    _write_jsonl(out_dir / "out.jsonl", scored)
    (out_dir / "eval_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if gpu_before is not None:
        (out_dir / "gpu_before.json").write_text(json.dumps(gpu_before, indent=2) + "\n", encoding="utf-8")
        gpu_after = _gpu_snapshot()
        (out_dir / "gpu_after.json").write_text(json.dumps(gpu_after, indent=2) + "\n", encoding="utf-8")
        receipt["artifacts"]["gpu_after_json"] = str(out_dir / "gpu_after.json")

    mlflow_info = _maybe_log_mlflow(
        tracking_uri=mlflow_tracking_uri,
        result={"summary": summary},
        out_dir=out_dir,
        threshold_l1=threshold_l1,
        taxonomy_path=taxonomy_path,
        calibration_path=calibration_path,
    )
    if mlflow_info is not None:
        receipt["mlflow"] = mlflow_info

    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    return {
        "run_id": run_id,
        "out_dir": str(out_dir),
        "summary": summary,
        "receipt": receipt,
    }
