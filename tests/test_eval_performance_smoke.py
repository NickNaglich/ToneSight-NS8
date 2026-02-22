import shutil
import time
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


def test_eval_performance_smoke_under_conservative_threshold():
    out_root = _temp_dir("tmp_eval_perf_smoke")
    started = time.perf_counter()
    result = run_eval(
        "data/goldset.jsonl",
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
    )
    elapsed = time.perf_counter() - started

    # Conservative runtime threshold to avoid flaky CI while still catching major regressions.
    assert elapsed < 30.0
    assert Path(result["out_dir"]).joinpath("eval_summary.json").exists()
