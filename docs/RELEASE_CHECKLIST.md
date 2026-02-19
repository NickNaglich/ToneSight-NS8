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
python -m tonesight_ns8.cli bundle --run-b runs/<run_id>
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
- bundle command creates deterministic zip with `manifest.json`

## Release metadata checks

- `pyproject.toml` version is correct for release target
- `LICENSE` present and aligned with package metadata
- `docs/SPEC_NS8.md`/vectors/tests/docs are synchronized for any behavior changes
- project change log is updated with release-facing changes (path depends on repo policy)

## v1.1 Milestone Checklist (Concrete)

Scope: usability and operability polish while preserving deterministic NS8 core behavior.

### Milestone goals

- keep NS8 math/spec behavior unchanged (`spec_version` remains stable unless explicitly changed)
- improve CLI/eval/compare ergonomics without adding non-deterministic behavior
- keep observability path optional and non-blocking for core library users

### Deliverables

- [ ] CLI UX polish:
  - [ ] clarify command help text and error messages for common input mistakes
  - [ ] ensure `python -m tonesight_ns8.cli --help` and subcommand help are clear
- [ ] Eval/compare report polish:
  - [ ] ensure key run metrics are easy to read in `eval_summary.json`
  - [ ] ensure `compare_summary.json` highlights top deltas clearly and deterministically
- [ ] Docs polish:
  - [ ] keep README quickstart and troubleshooting in sync with actual commands
  - [ ] keep `docs/API_REFERENCE.md` and `docs/EVAL.md` aligned with runtime behavior
- [ ] CI/release hardening:
  - [ ] maintain matrix test pass on supported Python versions
  - [ ] keep optional observability tests green when dependencies are installed
  - [ ] verify fresh-clone editable install + eval smoke command

### v1.1 validation commands

```bash
python tools/validate_defaults.py
python tools/validate_defaults.py tests/fixtures/defaults.invalid.json && exit 1 || true
python -m pytest -q
python tools/regen_vectors.py
git diff --exit-code
python -m pip install -e ".[observability]"
python -m pytest -q test_observability_api.py
python -m tonesight_ns8.cli --help
python -m tonesight_ns8.cli eval
```

### v1.1 release gate

- [ ] all commands above pass on local clean workspace
- [ ] GitHub Actions checks are green on release candidate commit
- [ ] release notes summarize deterministic-impact vs docs-only changes
- [ ] version/tag chosen (`v1.1.0` or equivalent) and pushed

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
