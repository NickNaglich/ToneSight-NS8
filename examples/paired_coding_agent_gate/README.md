# Paired coding-agent gate example

From a project checkout with Python 3.11+:

```sh
python examples/paired_coding_agent_gate.py --out runs/paired-gate-example
```

The script uses this checkout's public APIs and repository-relative resources;
there are no host paths, model services or new dependencies. `--out` is required.
**Any existing output file or directory is refused before capture.** Use a new
directory for an explicitly selected repetition; the example never deletes or
repairs previous evidence. Paths are resolved from the script, so an absolute
script path also works from a different working directory.

## Declared synthetic controls

The three adjacent JSONL files contain two authored events each. They are
synthetic fixtures, with declared `synthetic_file_fixture` provider and
`fixture-only-v1` model version metadata; no real model ran or is attested.
They reuse comparison event IDs and pinned generation/spec/mapping/taxonomy/
no-calibration identities. Positive changes only received timestamps; negative
changes the one-line Python function responses to JavaScript, retaining expected
Python language, line count, absent tests/error markers and tool-call metadata.

Expected native gates:

| Pair | Matched IDs | Decision | Native exit | Violation |
|---|---:|---|---:|---|
| Baseline → positive | 2 | passed | 0 | none |
| Baseline → negative | 2 | regressed | 2 | `delta_language_mismatch_rate=1.0 > 0.1` |

Other gated behavioral and compliance deltas must stay zero. No thresholds or
identity policy are tuned. Live receipts lack `dataset_hash`, so comparison uses
the documented per-call dataset allowance while explicitly requiring pinned
identity. Gate uses unchanged `coding_agent_drift`, its pinned enforcement, and
`--allow-dataset-mismatch`. Incompatibility exit 3 is a failure of this example,
not a behavioral regression. Calibration-content compatibility remains native.

## Evidence and exits

The example snapshots fixture bytes before capture. `inputs.json` records exact
file SHA-256 values, comparison IDs and canonical event hashes. Received
timestamps are excluded only from canonical identity; changed negative texts
have different content hashes. Checkout line endings may change file hashes,
while logical canonical hashes remain stable.

Each trace has a separate native capture/replay directory. The output retains
pipeline results, comparisons, complete gate payloads, native CLI stdout/stderr
and command/exit records. `summary.json` is written only when both expected
outcomes pass. The **example process exits 0** for that accepted control pair;
the expected negative native gate exit 2 remains in its raw receipt.

Unexpected results preserve partial artifacts plus `failure.json`; the example
exits nonzero. An available unexpected native gate exit is preserved (including
3), while exceptions or an unexpected native exit 0 yield example exit 1.
Do not alter fixtures or thresholds to seek a pass after failure.

Replay sets target equal to derived VAD and has no gold labels: 100% compliance
is not predictive accuracy, emotion validity or real-consumer benefit. This is
a small deterministic library-consumer acceptance example, not a benchmark,
new metric, production classifier or general NS8 mathematical claim.
