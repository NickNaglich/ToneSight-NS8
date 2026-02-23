# ToneSight NS8 `0.2.1` Release Notes

Release date: `2026-02-23`

This release delivers the killer-stability benchmark track and associated operations hardening completed across v0.2.0/v0.2.1 phases.

## Highlights

- Added deterministic killer-stability benchmark protocol and artifacts:
  - fixed `C1/C2/C3/C4` condition matrix
  - false-drift vs true-drift separation reporting
  - deterministic evidence at `runs/benchmarks/killer_stability/evidence.json`
- Added baseline comparators and robustness reporting:
  - `equal_width`, `quantile`, `raw_jsd_hist16`
  - multi-profile/seed robustness sweep with distribution stats (`mean/std/min/max/p10/p50/p90`)
  - absolute pass-rate metrics and ToneSight loss-tag attribution
- Added topology-oriented robustness profiles and fixed-weight policy documentation.
- Added optional larger-N deterministic scaling path (`sample_multiplier` and derived fixture workflow).
- Added benchmark CLI overrides for reproducible experimentation:
  - `--killer-profiles`
  - `--killer-seeds`
  - `--killer-primary-strength`
  - `--killer-sweep-strengths`
  - `--killer-sample-multiplier`

## Artifact and Contract Notes

- Benchmark outputs remain deterministic for fixed inputs/config.
- `N=1000` derived benchmark examples are scaling checks and are explicitly scoped as non-independent-distribution evidence.

## Version metadata updates

- Package version set to `0.2.1` in `pyproject.toml`.
- Observability API app version set to `0.2.1`.
- README version target updated to `0.2.1`.

## Validation

- `python -m pytest -q tests/test_benchmark_killer_stability.py tests/test_benchmark_cli.py`
- `python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl`
- CI checks green on `main` (test matrix, observability, security scan, bandit).
