import importlib
import json
import inspect
import os
import re
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
import tonesight_ns8.cli as cli_module
import tonesight_ns8.defaults as defaults_module
import tonesight_ns8.eval_compare_runner as eval_compare_module
import tonesight_ns8.eval_runner as eval_runner_module
from tonesight_ns8.defaults import ARTIFACT_DEFAULTS, EVAL_DEFAULTS

def test_defaults_config_exists_and_is_stable():
    path = Path("config/defaults.json")
    assert path.exists()

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["spec_version"] == "1.0"

    eval_defaults = payload["eval_defaults"]
    assert eval_defaults["out_root"] == "runs"
    assert eval_defaults["taxonomy_path"] == "taxonomy/tone_taxonomy.v1.json"
    assert eval_defaults["threshold_l1"] == 3

    artifact_defaults = payload["artifact_defaults"]
    assert artifact_defaults["vectors_path"] == "vectors/ns8_test_vectors.json"
    assert artifact_defaults["taxonomy_path"] == "taxonomy/tone_taxonomy.v1.json"
    assert artifact_defaults["goldset_path"] == "data/goldset.jsonl"


def test_runtime_defaults_are_loaded_from_config():
    assert EVAL_DEFAULTS["out_root"] == "runs"
    assert EVAL_DEFAULTS["taxonomy_path"] == "taxonomy/tone_taxonomy.v1.json"
    assert EVAL_DEFAULTS["threshold_l1"] == 3
    assert EVAL_DEFAULTS["calibration_path"] is None
    assert EVAL_DEFAULTS["capture_gpu"] is False
    assert EVAL_DEFAULTS["mlflow_tracking_uri"] is None
    assert ARTIFACT_DEFAULTS["goldset_path"] == "data/goldset.jsonl"


def test_cli_eval_defaults_follow_config_defaults():
    parser = cli_module.build_parser()
    args = parser.parse_args(["eval"])
    assert args.goldset == ARTIFACT_DEFAULTS["goldset_path"]
    assert args.out_root == EVAL_DEFAULTS["out_root"]
    assert args.taxonomy == EVAL_DEFAULTS["taxonomy_path"]
    assert args.threshold_l1 == EVAL_DEFAULTS["threshold_l1"]
    assert args.calibration == EVAL_DEFAULTS["calibration_path"]


def test_eval_function_defaults_follow_config_defaults():
    eval_defaults = inspect.signature(eval_runner_module.run_eval).parameters
    assert eval_defaults["out_root"].default == EVAL_DEFAULTS["out_root"]
    assert eval_defaults["taxonomy_path"].default == EVAL_DEFAULTS["taxonomy_path"]
    assert eval_defaults["threshold_l1"].default == EVAL_DEFAULTS["threshold_l1"]
    assert eval_defaults["calibration_path"].default == EVAL_DEFAULTS["calibration_path"]
    assert eval_defaults["capture_gpu"].default == EVAL_DEFAULTS["capture_gpu"]
    assert eval_defaults["mlflow_tracking_uri"].default == EVAL_DEFAULTS["mlflow_tracking_uri"]

    compare_defaults = inspect.signature(eval_compare_module.run_eval_compare).parameters
    assert compare_defaults["out_root"].default == EVAL_DEFAULTS["out_root"]
    assert compare_defaults["taxonomy_path"].default == EVAL_DEFAULTS["taxonomy_path"]
    assert compare_defaults["threshold_l1"].default == EVAL_DEFAULTS["threshold_l1"]


def test_override_defaults_propagates_to_cli_and_eval(monkeypatch):
    custom_out_root = "runs_custom"
    custom_taxonomy = "taxonomy/custom_taxonomy.json"
    custom_goldset = "data/custom_goldset.jsonl"
    custom_threshold = 5

    with monkeypatch.context() as m:
        m.setitem(defaults_module.EVAL_DEFAULTS, "out_root", custom_out_root)
        m.setitem(defaults_module.EVAL_DEFAULTS, "taxonomy_path", custom_taxonomy)
        m.setitem(defaults_module.EVAL_DEFAULTS, "threshold_l1", custom_threshold)
        m.setitem(defaults_module.ARTIFACT_DEFAULTS, "goldset_path", custom_goldset)

        importlib.reload(cli_module)
        importlib.reload(eval_runner_module)

        args = cli_module.build_parser().parse_args(["eval"])
        assert args.out_root == custom_out_root
        assert args.taxonomy == custom_taxonomy
        assert args.threshold_l1 == custom_threshold
        assert args.goldset == custom_goldset

        eval_defaults = inspect.signature(eval_runner_module.run_eval).parameters
        assert eval_defaults["out_root"].default == custom_out_root
        assert eval_defaults["taxonomy_path"].default == custom_taxonomy
        assert eval_defaults["threshold_l1"].default == custom_threshold

    importlib.reload(cli_module)
    importlib.reload(eval_runner_module)


def _local_test_dir(prefix: str) -> Path:
    root = Path(".tmp") / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_load_defaults_missing_file_fails_fast():
    missing = _local_test_dir("tmp_defaults_missing") / "does_not_exist.json"
    with pytest.raises(RuntimeError, match="Missing defaults config"):
        defaults_module._load_defaults(missing)


def test_load_defaults_invalid_json_fails_fast():
    bad_json = _local_test_dir("tmp_defaults_bad_json") / "defaults.json"
    bad_json.write_text("{", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid defaults config JSON"):
        defaults_module._load_defaults(bad_json)


def test_load_defaults_invalid_schema_fails_fast():
    bad_schema = _local_test_dir("tmp_defaults_bad_schema") / "defaults.json"
    bad_schema.write_text(
        json.dumps(
            {
                "spec_version": "1.0",
                "eval_defaults": {"out_root": "runs"},
                "artifact_defaults": {"goldset_path": "data/goldset.jsonl"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="Invalid defaults config schema"):
        defaults_module._load_defaults(bad_schema)


def _run_import_with_defaults(module_name: str, defaults_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["TONESIGHT_DEFAULTS_PATH"] = str(defaults_path.resolve())
    env["PYTHONPATH"] = str(Path("src").resolve())
    return subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_import_fails_fast_with_invalid_defaults_json():
    bad_json = _local_test_dir("tmp_defaults_cli_bad_json") / "defaults.json"
    bad_json.write_text("{", encoding="utf-8")
    proc = _run_import_with_defaults("tonesight_ns8.cli", bad_json)
    assert proc.returncode != 0
    assert "Invalid defaults config JSON" in (proc.stderr + proc.stdout)


def test_observability_import_fails_fast_with_invalid_defaults_schema():
    bad_schema = _local_test_dir("tmp_defaults_obs_bad_schema") / "defaults.json"
    bad_schema.write_text(
        json.dumps(
            {
                "spec_version": "1.0",
                "eval_defaults": {"out_root": "runs"},
                "artifact_defaults": {"goldset_path": "data/goldset.jsonl"},
            }
        ),
        encoding="utf-8",
    )
    proc = _run_import_with_defaults("tonesight_ns8.observability_api", bad_schema)
    assert proc.returncode != 0
    assert "Invalid defaults config schema" in (proc.stderr + proc.stdout)


def test_docs_defaults_examples_match_config_defaults():
    defaults = json.loads(Path("config/defaults.json").read_text(encoding="utf-8"))
    eval_defaults = defaults["eval_defaults"]
    artifact_defaults = defaults["artifact_defaults"]

    readme = Path("README.md").read_text(encoding="utf-8")
    api_ref = Path("docs/API_REFERENCE.md").read_text(encoding="utf-8")
    merged = readme + "\n" + api_ref

    assert artifact_defaults["goldset_path"] in merged
    assert eval_defaults["out_root"] in merged
    assert eval_defaults["taxonomy_path"] in merged
    assert re.search(rf"--threshold-l1\s+{eval_defaults['threshold_l1']}\b", readme)
    assert "out_root: str = \"runs\"" in api_ref
    assert "taxonomy_path: str = \"taxonomy/tone_taxonomy.v1.json\"" in api_ref
    assert "threshold_l1: int = 3" in api_ref


def test_validate_defaults_script_fails_on_bad_fixture():
    bad_path = Path("tests/fixtures/defaults.invalid.json")

    proc = subprocess.run(
        [sys.executable, "tools/validate_defaults.py", str(bad_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "must be" in (proc.stderr + proc.stdout)
