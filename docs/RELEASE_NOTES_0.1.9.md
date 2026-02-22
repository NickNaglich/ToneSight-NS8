# ToneSight NS8 `0.1.9` Release Notes

Release date: `2026-02-22`

This release closes the `v0.1.9` production-credibility hardening plan without changing NS8 core math/spec behavior.

## Highlights

- Completed observability security enforcement tests:
  - auth required on `/metrics`, `/eval/last`, `/eval/run`
  - allowlist rejection for disallowed eval paths
  - deterministic `429` behavior for rate-limit overflow
- Added deterministic property/fuzz-style NS8 invariant coverage:
  - output `A` domain checks (`1..8`)
  - canonical route constraints for seed family and transformed coordinates
  - strict invalid-input rejection checks
- Added artifact compatibility contract tests:
  - required field/type checks for `receipt.json`, `eval_summary.json`, and `out.jsonl` rows
  - additive-field tolerance checks
  - legacy receipt-shape compatibility behavior checks for gate workflows
- Added deterministic performance smoke gate:
  - conservative runtime threshold (`< 30s`) for eval on in-repo fixture

## Version metadata updates

- Package version set to `0.1.9` in `pyproject.toml`
- Observability API app version set to `0.1.9`
- README version target updated to `0.1.9`

## Validation

- `python -m pytest -q` -> `153 passed`
- Targeted hardening suite:
  - `python -m pytest -q test_observability_api.py tests/test_ns8_property_invariants.py tests/test_artifact_schema_compatibility.py tests/test_eval_performance_smoke.py tests/test_canonical_id_policy.py tests/test_live_compare_compatibility.py`
  - `29 passed`

## GitHub issue closure

- Closed `#32` observability security tests
- Closed `#33` NS8 property/invariant coverage
- Closed `#34` artifact compatibility contract tests
- Closed `#35` deterministic performance smoke gate
