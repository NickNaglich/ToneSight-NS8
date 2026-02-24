# Release Checklist (Pre-1.0)

Use this checklist before tagging or publishing a pre-1.0 release candidate.

## Validation commands

Run from repository root:

```bash
python tools/validate_defaults.py
python tools/validate_defaults.py tests/fixtures/defaults.invalid.json && exit 1 || true
python tools/check_nosec_policy.py
python -m bandit -r src
python -m tonesight_ns8.cli release-check --goldset data/goldset.jsonl --taxonomy taxonomy/tone_taxonomy.v1.json
python -m tonesight_ns8.cli benchmark --suite killer_stability --out-root runs --goldset data/goldset.jsonl
python -m pytest -q
python tools/regen_vectors.py
git diff --exit-code
```

Observability dependency check:

```bash
python -m pip install -e ".[observability]"
python -m pytest -q test_observability_api.py
```

CLI smoke:

```bash
tonesight-ns8 --help
python -m tonesight_ns8.cli eval
python -m tonesight_ns8.cli bundle --run-b runs/<run_id>
```

## Expected outcomes

- defaults validator passes for `config/defaults.json`
- defaults validator fails for `tests/fixtures/defaults.invalid.json`
- nosec policy checker passes (or reports actionable violations)
- Bandit security scan reports no findings for `src/`
- release-check orchestration command returns `decision=passed` (`exit_code=0`)
- killer benchmark evidence artifact is generated at `runs/benchmarks/killer_stability/evidence.json`
- killer robustness artifacts are generated at:
  - `runs/benchmarks/killer_stability/robustness_summary.json`
  - `runs/benchmarks/killer_stability/robustness_report.html`
- release review includes false/true drift separation ratio comparison across ToneSight and baselines
- full test suite passes
- warnings are triaged/documented; no unexpected warnings are introduced
- vector regeneration produces no diff
- observability API tests pass when optional dependencies are installed
- CLI entrypoint is installed and operational
- eval smoke command returns a JSON payload with `run_id` and writes run artifacts
- bundle command creates deterministic zip with `manifest.json`
- determinism matrix job is green across configured OS targets in `.github/workflows/ci.yml`
- required `security-bandit` job is green in `.github/workflows/ci.yml`

## Release metadata checks

- `pyproject.toml` version is correct for release target
- `LICENSE` present and aligned with package metadata
- `docs/SPEC_NS8.md`/vectors/tests/docs are synchronized for any behavior changes
- project change log is updated with release-facing changes (path depends on repo policy)

## CHANGE_LOG Entry Format (Required)

Use this exact structure in `.agent/LOGS/CHANGE_LOG.md` (append-only):

```text
[YYYY-MM-DDTHH:MM:SSZ] <short action summary>
Files: <comma-separated file paths>
Reason: <why this change was needed>
Validation: <commands run, or "docs-only (no code-path changes)">
```

Example:

```text
[2026-02-16T21:00:00Z] Improve CLI help wording for eval and compare
Files: src/tonesight_ns8/cli.py, docs/API_REFERENCE.md
Reason: Reduce operator ambiguity and align CLI behavior with docs.
Validation: python -m pytest -q; python -m tonesight_ns8.cli --help
```
