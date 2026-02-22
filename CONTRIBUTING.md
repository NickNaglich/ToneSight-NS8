# Contributing

## Development Setup

Requirements:
- Python 3.11+

Install:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

## Run Tests

```bash
python tools/validate_defaults.py
python -m pytest -q
```

## Optional Security Checks

```bash
python -m pip install pip-audit bandit
pip-audit
bandit -r src
```

If installed:

```bash
gitleaks detect --source . --redact --no-git
```

## Pull Request Guidelines

- Keep changes deterministic and JSON-serializable where applicable.
- Include tests for behavioral changes.
- Update docs when interfaces/outputs change.
- Do not commit secrets, local credentials, or sensitive data artifacts.

## Benchmark Contributions

When adding or updating benchmark modules:
- keep scripts deterministic for fixed inputs (no nondeterministic sampling)
- write artifacts with stable key order and deterministic path conventions
- include at least one test asserting repeatability of outputs/artifact schema
- compare against baseline methods using the same fixture inputs
- document claim-to-artifact mapping in `docs/WHY_NS8.md` when adding new metrics

Recommended local checks:

```bash
python -m tonesight_ns8.cli benchmark --suite core
python -m pytest -q tests/test_benchmark_cli.py
```
