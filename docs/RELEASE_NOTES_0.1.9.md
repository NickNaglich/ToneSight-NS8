# ToneSight NS8 `0.1.9` Release Notes

Release date: `2026-02-23`

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
- Completed exhaustive full-domain NS8 invariant coverage:
  - full valid-domain loops for `family x r x c x k` with `N=8`
  - canonical seed-route and output-bound assertions across entire domain
- Added receipt-driven eval replay reproducibility checks:
  - replay from receipt/config context
  - `out.jsonl` byte/hash equality assertions
  - `eval_summary.json` stability assertions excluding documented variable fields
- Added compare pipeline error-contract enforcement:
  - deterministic actionable errors for missing/malformed/incompatible compare inputs
  - stable CLI error envelope assertions
- Added additive receipt provenance metadata:
  - optional `code_revision` field in eval/live receipts when git revision is available
  - compatibility tests for present/absent optional semantics
- Security hardening follow-up:
  - fixed Bandit `B607` in provenance helper by resolving absolute git executable path

## Version metadata updates

- Package version set to `0.1.9` in `pyproject.toml`
- Observability API app version set to `0.1.9`
- README version target updated to `0.1.9`

## Validation

- `python -m pytest -q` -> `161 passed`
- Targeted hardening suite:
  - `python -m pytest -q test_observability_api.py tests/test_ns8_property_invariants.py tests/test_artifact_schema_compatibility.py tests/test_eval_performance_smoke.py tests/test_canonical_id_policy.py tests/test_live_compare_compatibility.py`
  - `29 passed`
- Full-domain/phase-closure validation:
  - `python -m pytest -q test_ns8_vectors.py tests/test_invariants.py tests/test_strict_validation.py tests/test_ns8_property_invariants.py`
  - `39 passed`
- Compare error-contract validation:
  - `python -m pytest -q test_compare.py tests/test_compare_topology_distance.py tests/test_compare_error_contract.py`
  - `9 passed`
- Replay reproducibility validation:
  - `python -m pytest -q tests/test_eval_replay_reproducibility.py test_eval_runner.py`
  - `5 passed`
- Security scan:
  - `python -m bandit -r src` -> `No issues identified`

## GitHub issue closure

- Closed `#32` observability security tests
- Closed `#33` NS8 property/invariant coverage
- Closed `#34` artifact compatibility contract tests
- Closed `#35` deterministic performance smoke gate
- Closed `#36` exhaustive full-domain NS8 invariants
- Closed `#39` receipt-driven eval replay reproducibility
- Closed `#38` compare pipeline error-contract tests
- Closed `#37` receipt provenance code revision field
