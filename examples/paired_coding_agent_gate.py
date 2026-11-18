"""Portable synthetic coding-agent gate example: positive0, negative2, no model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

# Keep this checkout's public APIs and resource files together; no installation
# or machine-specific path is required to run the repository example.
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from tonesight_ns8 import run_compare, run_live_capture, run_live_replay
from tonesight_ns8.live_identity import stable_event_hash

FIXTURES = PROJECT / "examples" / "paired_coding_agent_gate"
TRACES = ("baseline", "positive", "negative")


def _save(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _gate(output: Path, candidate: str, baseline: str, run: str) -> tuple[int, dict | None]:
    args = [sys.executable, "-I", "-B", "-c",
            "import sys;sys.path.insert(0,sys.argv.pop(1));from tonesight_ns8.cli import main;raise SystemExit(main())",
            str(PROJECT / "src"), "gate", "--run-a", baseline, "--run-b", run,
            "--profile", "coding_agent_drift", "--gate-profiles", str(PROJECT / "config/gate_profiles.json"),
            "--allow-dataset-mismatch"]
    result = subprocess.run(args, cwd=PROJECT, capture_output=True)
    (output / f"{candidate}.gate.stdout.bin").write_bytes(result.stdout)
    (output / f"{candidate}.gate.stderr.bin").write_bytes(result.stderr)
    _save(output / f"{candidate}.gate.command.json", {"argv": args, "cwd": str(PROJECT), "exit": result.returncode})
    try:
        payload = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        payload = None
    return result.returncode, payload


def _verify_pair(candidate: str, comparison: dict, code: int, gate: dict | None) -> None:
    _require(isinstance(gate, dict), "Native gate did not return a JSON object; see raw streams")
    expected_code = 0 if candidate == "positive" else 2
    _require(code == expected_code, f"Unexpected {candidate} native gate exit: {code}")
    _require(gate["decision"] == ("passed" if candidate == "positive" else "regressed"), "Unexpected gate decision")
    _require(gate["incompatibilities"] == [], "Incompatibility is not behavioral regression")
    _require(gate["thresholds"]["require_pinned_model_identity"] is True, "Pinned identity enforcement required")
    _require(gate["require_dataset_match"] is False, "Expected documented live dataset allowance")
    _require(comparison["compare_summary"]["rows"] == {
        "count_a": 2, "count_b": 2, "count_common_ids": 2, "count_only_in_a": 0, "count_only_in_b": 0}, "Expected exactly two paired IDs")
    expected_delta = {"language_mismatch_rate": float(candidate == "negative"),
                      "verbosity_bin_mean": 0.0, "tests_presence_rate": 0.0, "tool_call_rate": 0.0}
    _require(gate["coding_agent_metrics"]["delta"] == expected_delta, "Unexpected behavioral deltas")
    _require(gate["metrics"] == {"delta_pass_rate": 0.0, "delta_avg_l1": 0.0, "delta_p95_l1": 0.0}, "Unexpected compliance deltas")
    violations = [] if candidate == "positive" else [{"metric": "delta_language_mismatch_rate", "actual": 1.0,
                                                       "threshold": 0.1, "operator": "<="}]
    _require(gate["violations"] == violations, "Unexpected threshold violation(s)")


def run_example(output: Path) -> dict:
    requested = Path(output)
    if requested.exists() or requested.is_symlink():
        raise FileExistsError(f"Output path already exists: {requested}")
    # Create the requested path exclusively BEFORE resolving symlinks; mkdir is
    # also the race guard if another writer creates the final path after check.
    requested.mkdir(parents=True, exist_ok=False)
    output = requested.resolve()
    stage, native_exit = "snapshot authored fixtures", None
    try:
        inputs = output / "inputs"
        inputs.mkdir()
        manifest = {}
        for trace in TRACES:
            raw = (FIXTURES / f"{trace}.jsonl").read_bytes()
            (inputs / f"{trace}.jsonl").write_bytes(raw)
            events = [json.loads(line) for line in raw.splitlines() if line.strip()]
            manifest[trace] = {"input_sha256": hashlib.sha256(raw).hexdigest(),
                               "event_ids": [e["event_id"] for e in events],
                               "event_hashes": [stable_event_hash(e) for e in events]}
        ids = manifest["baseline"]["event_ids"]
        _require(len(ids) == len(set(ids)) == 2 and all(manifest[t]["event_ids"] == ids for t in TRACES), "Authored traces must share two unique IDs")
        _require(manifest["positive"]["event_hashes"] == manifest["baseline"]["event_hashes"], "Positive control canonical content changed")
        _require(all(a != b for a, b in zip(manifest["negative"]["event_hashes"], manifest["baseline"]["event_hashes"])), "Changed negative content needs distinct hashes")
        _save(output / "inputs.json", manifest)
        replays = {}
        for trace in TRACES:
            trace_output = output / trace
            trace_output.mkdir()
            stage = f"{trace} capture"
            capture = run_live_capture(str(inputs / f"{trace}.jsonl"), out_root=str(trace_output))
            stage = f"{trace} replay"
            replay = run_live_replay(capture["capture_dir"], out_root=str(trace_output),
                                     taxonomy_path=str(PROJECT / "taxonomy/tone_taxonomy.v1.json"),
                                     threshold_l1=3, adapter="coding_agent", require_pinned_model_identity=True)
            _save(output / f"{trace}.pipeline.json", {"capture": capture, "replay": replay})
            _require(capture["event_count"] == replay["summary"]["count_rows"] == replay["summary"]["accepted_count"] == 2, "Expected two accepted events")
            _require(replay["summary"]["invalid_count"] == replay["summary"]["quarantined_count"] == 0, "Unexpected invalid/quarantined events")
            replays[trace] = replay
        outcomes = {}
        for candidate in ("positive", "negative"):
            native_exit = None
            baseline, run = replays["baseline"]["out_dir"], replays[candidate]["out_dir"]
            stage = f"{candidate} compare"
            comparison = run_compare(baseline, run, write_artifact=True, require_dataset_match=False,
                                     require_pinned_model_identity=True)
            _save(output / f"{candidate}.compare.json", comparison)
            stage = f"{candidate} gate"
            native_exit, gate = _gate(output, candidate, baseline, run)
            _save(output / f"{candidate}.gate.json", {"native_exit": native_exit, "payload": gate})
            _verify_pair(candidate, comparison, native_exit, gate)
            outcomes[candidate] = {"native_exit": native_exit, "decision": gate["decision"],
                                   "matched_ids": 2, "deltas": gate["coding_agent_metrics"]["delta"],
                                   "violations": gate["violations"]}
        result = {"status": "accepted_synthetic_controls", "example_exit_code": 0, "outcomes": outcomes,
                  "inputs": manifest, "scope": "Synthetic file workflow; self-target conformance is not accuracy or real-model attestation."}
        _save(output / "summary.json", result)
        return result
    except Exception as exc:
        failure = {"status": "failed", "stage": stage, "native_gate_exit": native_exit,
                   "example_exit_code": native_exit if native_exit else 1,
                   "error": {"type": type(exc).__name__, "message": str(exc)}}
        _save(output / "failure.json", failure)
        return failure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="NEW output directory; existing paths are refused.")
    args = parser.parse_args(argv)
    try:
        result = run_example(args.out)
    except OSError as exc:
        print(json.dumps({"status": "refused_output", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return result["example_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
