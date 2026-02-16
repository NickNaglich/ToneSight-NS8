# Release Checklist (v1)

Use this checklist before tagging or publishing a `v1` release candidate.

## Validation commands

Run from repository root:

```bash
python tools/validate_defaults.py
python tools/validate_defaults.py tests/fixtures/defaults.invalid.json && exit 1 || true
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
```

## Expected outcomes

- defaults validator passes for `config/defaults.json`
- defaults validator fails for `tests/fixtures/defaults.invalid.json`
- full test suite passes
- warnings are triaged/documented; no unexpected warnings are introduced
- vector regeneration produces no diff
- observability API tests pass when optional dependencies are installed
- CLI entrypoint is installed and operational
- eval smoke command returns a JSON payload with `run_id` and writes run artifacts

## Release metadata checks

- `pyproject.toml` version is correct for release target
- `LICENSE` present and aligned with package metadata
- `SPEC_NS8.md`/vectors/tests/docs are synchronized for any behavior changes
- `.agent/LOGS/CHANGE_LOG.md` includes append-only entries for release changes
