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
python -m pip install --upgrade "setuptools>=84.1.0"
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

## Observability dependency maintenance

Both observability dependency lists select FastAPI 0.137.x and Starlette 1.7.x.
Starlette 1.7 fixes deprecated AnyIO imports in TestClient; this permits current
AnyIO and pytest with the existing warnings-as-errors policy. The optional
TestClient transport moves from deprecated `httpx` fallback to `httpx2` as
required by the upgraded Starlette; both native dependency lists agree. These ranges also
exclude the inherited Starlette 0.46.2 versions with published advisories.
Future minor upgrades should retain the API tests and check current advisories.
No application API implementation, scoring, warnings policy or tests are changed.

The Security workflow upgrades runner setuptools to at least 84.1.0 before
auditing the complete installed tool environment. This is the patched floor for
[GHSA-xmj3-9gf7-h52w](https://github.com/pypa/setuptools/security/advisories/GHSA-xmj3-9gf7-h52w);
`pip-audit` still fails on any reported vulnerability. The tool-environment audit
is not an audit or security certification of all optional application dependencies.
In particular, the existing MLflow 2.x range has separate published advisories
and is unchanged by this repair. Do not infer whole-stack security from green CI.
