# ToneSight NS8 `0.2.2` Release Notes

Release date: `2026-02-23`

This release delivers the adoption and pipeline-integration track defined in v0.2.2 Phases 1-4.

## Highlights

- Added zero-friction batch adapters for pipeline ingestion:
  - `tonesight_from_vad_batch(...)`
  - `tonesight_from_llm_labels(...)`
  - deterministic ordering and repeatability tests
- Added MLflow helper hardening and deterministic report diagnostics:
  - one-call helper `log_eval_to_mlflow(...)` with no-op/failed-safe behavior
  - deterministic transition heatmap JSON artifacts for static reports
- Added incremental stream-state support and monitoring recipe:
  - `new_stream_state(...)`, `snapshot_stream_state(...)`, `run_stream_update(...)`
  - CLI `stream-update` command
  - operator recipe in `docs/RECIPES/drift_monitoring.md`
- Added robustness HTML benchmark summary:
  - `runs/benchmarks/killer_stability/robustness_report.html`
- Expanded evidence diversity:
  - new deterministic profile `phase_flip_cycle`
  - pseudo-real public-safe fixture `data/pseudo_real_trace.jsonl`
  - updated scenario-family evidence map docs

## Artifact and Contract Notes

- New report artifact paths:
  - `runs/<runB>/reports/transition_heatmap_<runB>.json`
  - `runs/<runB>/reports/transition_heatmap_<runA>_to_<runB>.json`
- New killer benchmark artifact:
  - `runs/benchmarks/killer_stability/robustness_report.html`
- Stream mode remains deterministic for fixed input order and config.
- Claim boundaries remain unchanged: benchmark outputs are controlled protocol evidence, not inference-quality claims.

## Version metadata updates

- Package version set to `0.2.2` in `pyproject.toml`.
- Observability API app version set to `0.2.2`.
- README version target updated to `0.2.2`.

## Validation

- `python -m pytest -q test_receipts_api.py`
- `python -m pytest -q tests/test_report_runner.py tests/test_eval_mlflow_helper.py test_cli.py::test_cli_report`
- `python -m pytest -q tests/test_stream_runner.py tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py test_cli.py::test_cli_stream_update`
- `python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py`
