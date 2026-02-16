# ToneSight NS8 - Phased Workflow (Reworked + Hardened)

This workflow is based on the current repository state and adds pre-build safeguards to prevent drift: API stability, receipt schema discipline, vector regeneration tooling, and boundary stubs for future integration.

## Release scope bands

- `v1` (current): deterministic library + analytics
  - freeze NS8 + taxonomy + quantization boundary contract
  - provide segment/speaker/session analytics with schema + tests
  - provide receipt schema and generation rules
- `v1.1` (next): minimal runnable harness
  - add CLI for scoring/eval on JSONL
  - add run receipts written to disk
  - add optional MLflow logging
- `v1.2` (later): full-stack monitoring (explicitly out of current core scope unless reactivated)
  - add FastAPI + Prometheus metrics
  - add Grafana dashboards
  - add GPU snapshots per run (optional DCGM exporter profile)

## Current state snapshot

Already present:
- `SPEC_NS8.md`
- `ns8_ref.py`
- `ns8_test_vectors.json`
- `vectors/ns8_test_vectors.json`
- `test_ns8_vectors.py`
- `tone_taxonomy.v1.json`
- `taxonomy/tone_taxonomy.v1.json`
- `test_tone_taxonomy.py`
- `README.md`
- `API_REFERENCE.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `pytest.ini`
- `conftest.py`
- `docs/RECEIPT_SCHEMA.md`
- `docs/SEGMENT_INTERFACE.md`
- `docs/ANALYTICS.md`
- `config/vad_quantization.v1.json`
- `tools/regen_vectors.py`
- `src/tonesight_ns8/__init__.py`
- `src/tonesight_ns8/schema.py`
- `src/tonesight_ns8/analytics.py`
- `test_analytics.py`
- `tests/test_invariants.py`
- `examples/demo_compute.py`

Not present yet:
- none (non-formula path-a backlog closed)

## Critical cross-check note (must resolve before core changes)

There is a formula mismatch between current repo and the external phased plan:

- Current repo (`SPEC_NS8.md`, `ns8_ref.py`) uses:
  - `A_TLF = wrapN(c - r + k, N)`
  - `A_TRB = wrapN(r - c + k, N)`

- External phased plan proposes:
  - `A_TRB(r,c,k,N) = ((r - 1) * c + (k - 1)) % N + 1`
  - `A_TLF(r,c,k,N) = ((r - 1) * wrapN(c - 1, N) + (k - 1)) % N + 1`

Policy for this repo:
- Do not silently change formulas.
- If adopting new formulas, bump `spec_version`, regenerate vectors, and migrate tests in one atomic phase.
- Core math behavior is frozen to `SPEC_NS8.md` + `ns8_test_vectors.json` until mismatch resolution is explicitly approved.

Additional authority note:
- `ns8_ref.py` is the oracle until packaged implementation is proven equal by vectors + invariants.

## Phase 0 - Contract freeze (API + receipts + boundaries)

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T04:38:36Z]` (receipt schema, segment interface, quantization boundary, vector tooling)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:07:25Z]` (public wrappers + deterministic receipts + CLI thin wrapper)

Objective:
- Lock down interfaces and artifacts before package refactors.

Tasks:
- [x] Freeze public API names (v1) in `API_REFERENCE.md` and `README.md`:
  - `compute_A(...)`
  - `resolve_to_seed(...)`
  - `tonesight_from_label(...)`
  - `tonesight_from_vad(...)`
- [x] Freeze receipt schema in `docs/RECEIPT_SCHEMA.md`.
- [x] Freeze quantization boundary contract stub in `config/vad_quantization.v1.json` (no quantization implementation in v1 core).
- [x] Reserve upstream segment contract in `docs/SEGMENT_INTERFACE.md`.

Deliverable:
- API surface declared.
- Receipt shape frozen.
- Boundary stubs present.

## Phase 1 - Packaging + repo structure

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:28:38Z]` (pyproject, pytest config, CI, editable-install path)

Objective:
- Establish Python package foundation early.

Tasks:
- [x] Add `pyproject.toml` (Python 3.11+, pytest config).
- [x] Create package-oriented layout:
  - `src/tonesight_ns8/`
  - `tests/`
  - `taxonomy/`
  - `vectors/`
  - `examples/`
  - `tools/`
  - `docs/`
  - `config/`
- [x] Move/alias existing artifacts to package-oriented paths:
  - `vectors/ns8_test_vectors.json`
  - `taxonomy/tone_taxonomy.v1.json`

Deliverable:
- `pip install -e .` works.
- `pytest -q` runs from root.

## Phase 2 - Spec decision + immutable math contract

Status: `complete` (`Option A adopted`: keep current formulas under `spec_version 1.0`)
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T02:55:39Z]` (frozen NS8 spec + reference + vectors/tests)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T13:22:53Z]` (explicit core-math freeze policy in phased workflow)

Objective:
- Resolve formula mismatch and freeze spec version.

Tasks:
- [x] Keep `SPEC_NS8.md` as source of truth.
- [x] Resolve mismatch explicitly:
  - Option A: keep current formulas under `spec_version: 1.0`.
  - Option B: adopt new formulas under `spec_version: 2.0` (or `1.1`).
- [x] Explicitly document:
  - strict domains (`family`, `r,c,k`, `N`)
  - transform-only derived families
  - modulo semantics and integer-only expectations

Deliverable:
- immutable spec for chosen version.
- version string consistent across spec, vectors, and receipts.

## Phase 3 - NS8 packaged core module (reference oracle preserved)

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:07:25Z]` (packaged ns8 core/errors implementation + tests)

Objective:
- Implement core under `src/` while preserving oracle behavior.

Tasks:
- [x] Implement `src/tonesight_ns8/errors.py`:
  - `InvalidInput`, `UnknownFamily`, `InvalidTaxonomy`, `UnknownToneLabel`
- [x] Implement `src/tonesight_ns8/ns8.py`:
  - `validate_inputs(...)`
  - `resolve_to_seed(...)`
  - `compute_A(...)`
- [x] Enforce:
  - strict validation (no wrap for external invalid inputs)
  - integer-only inputs (`float` invalid)
  - arithmetic only in canonical seeds
  - derived families route through transforms only
- [x] Keep `ns8_ref.py` as oracle until parity proven.

Deliverable:
- packaged implementation matches oracle for valid vectors.

## Phase 4 - Vector discipline + regeneration tooling

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T04:38:36Z]` (regen tool + vector discipline hardening)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:28:38Z]` (CI vector regeneration diff check)

Objective:
- Make vector expectations reproducible.

Tasks:
- [x] Ensure canonical vectors at `vectors/ns8_test_vectors.json` in packaged layout.
- [x] Add `tools/regen_vectors.py`:
  - reads vector inputs
  - computes seed route and `A` from oracle
  - writes `expected_seed_family`, `expected_r_prime`, `expected_c_prime`, `expected_A`
- [x] Preserve strict invalid vectors with `expected_error: "InvalidInput"`.
- [x] Keep tests asserting route + output + strict invalid exceptions.

Deliverable:
- vectors reproducibly regenerated from oracle.

## Phase 5 - Invariant tests (separate hardening file)

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T02:55:39Z]` (vector/invariant checks present and passing in test suite)

Objective:
- Catch transform regressions independently from fixtures.

Tasks:
- [x] Create `tests/test_invariants.py`.
- [x] Add deterministic invariants:
  - `TRF(r,c,k) == TLF(r, H(c), k)`
  - `BLF(r,c,k) == TLF(V(r), c, k)`
  - `BRF(r,c,k) == TLF(V(r), H(c), k)`
  - `TLB(r,c,k) == TRB(r, H(c), k)`
  - `BRB(r,c,k) == TRB(V(r), c, k)`
  - `BLB(r,c,k) == TRB(V(r), H(c), k)`
  - `H(H(c)) == c`, `V(V(r)) == r`

Deliverable:
- transform drift detected independently of vector file.

## Phase 6 - Taxonomy module (packaged)

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T03:15:56Z]` (taxonomy contract + validation tests)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:07:25Z]` (packaged taxonomy module + API wiring)

Objective:
- Provide strict, versioned tone taxonomy loader.

Tasks:
- [x] Ensure taxonomy at `taxonomy/tone_taxonomy.v1.json` in packaged layout.
- [x] Implement `src/tonesight_ns8/taxonomy.py`:
  - `load_taxonomy(path)`
  - `validate_taxonomy(taxonomy)`
  - `get_vad(label, taxonomy)`
- [x] Enforce:
  - required `V/A/D`
  - integer-only
  - `1..8` domain
  - unknown label -> `UnknownToneLabel`

Deliverable:
- stable label->VAD mapping module.

## Phase 7 - Receipt-oriented ToneSight API

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:07:25Z]` (receipt-oriented wrappers + schema-compliant API)

Objective:
- Provide small integration surface returning normative receipts.

Tasks:
- [x] Implement `src/tonesight_ns8/schema.py` dataclasses:
  - `Route`
  - `ToneReceipt`
- [x] Expose in `src/tonesight_ns8/__init__.py`:
  - `tonesight_from_label(...)`
  - `tonesight_from_vad(...)`
- [x] Ensure receipts conform to `docs/RECEIPT_SCHEMA.md`.

Deliverable:
- deterministic JSON-serializable receipts.

## Phase 8 - CLI + demo (minimal)

Status: `complete`
Proof:
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T05:23:39Z]` (CLI eval + goldset + run artifacts)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T13:22:53Z]` (explicit 30-second acceptance criteria)
- `.agent/LOGS/CHANGE_LOG.md` `[2026-02-14T13:26:33Z]` (README demo path + artifact schema examples)

Objective:
- Provide 30-second local demo path.

Tasks:
- [x] Implement `src/tonesight_ns8/cli.py` commands:
  - `encode`
  - `decode`
  - `summarize`
  - `eval`
- [x] Add `examples/demo_compute.py` with deterministic examples.
- [x] Print JSON receipts to stdout for interactive commands.
- [x] Ensure eval writes run artifacts:
  - `runs/<run_id>/receipt.json`
  - `runs/<run_id>/eval_summary.json`
  - `runs/<run_id>/out.jsonl`
- [x] Keep scoring outputs deterministic:
  - avoid timestamps in scoring payload fields
  - use stable key ordering for JSON output
  - avoid filesystem-order-dependent iteration

Deliverable:
- local demo path runnable in ~30 seconds via `tonesight eval --goldset data/goldset.jsonl`.

Acceptance criteria:
- [x] `pip install -e .` (or equivalent environment setup) succeeds.
- [x] `tonesight eval --goldset data/goldset.jsonl` completes in under 30 seconds on laptop CPU.
- [x] Run artifacts are written under `runs/<run_id>/` with:
  - `receipt.json`
  - `eval_summary.json`
  - `out.jsonl`
- [x] Receipt artifacts conform to `docs/RECEIPT_SCHEMA.md`.
- [x] `python -m pytest -q` passes.
- [x] `.agent/LOGS/CHANGE_LOG.md` has an append-only entry for the change.

## Post-Phase Fork

After Phase 8 completion, choose one path explicitly.

Path A (`default`, library-first):
- deepen evaluation tooling while preserving deterministic core scope
- next additions:
  - Phase 9: `tonesight compare` deterministic run-to-run comparison
  - Phase 10 (optional): negative-anchor goldset expansion for stronger eval signal

Path B (`opt-in`, `v1.2` only):
- observability platform track: FastAPI + Prometheus + Grafana + optional GPU snapshots
- remains out of scope unless explicitly reactivated in plan/governance docs

## Path B - v1.2 Activation (Reactivated)

Status: `complete` (minimal observability stack implemented)

Tasks:
- [x] Reactivate Path B scope in phased workflow/governance docs.
- [x] Add Docker services for observability stack (`api`, `prometheus`, `grafana`).
- [x] Add minimal FastAPI observability layer (`/health`, `/metrics`, optional eval endpoints).
- [x] Add Prometheus scrape config and Grafana provisioning/dashboard baseline.
- [x] Add monitoring runbook docs (`docker compose up`, endpoints, expected metrics).
- [x] Add smoke tests for observability wiring and API baseline behavior.

Guardrails:
- Do not alter NS8 core formulas or deterministic mapping contract.
- Keep monitoring labels low-cardinality and avoid `run_id` labels in Prometheus metrics.

## Path A - Phase 9 (Recommended): `tonesight compare`

Status: `complete`

Goal:
- Compare two eval runs and summarize regressions deterministically.

CLI:
- `tonesight compare runs/<runA> runs/<runB>`

Inputs:
- [x] Two run directories containing:
  - `eval_summary.json`
  - `out.jsonl`
  - `receipt.json`

Outputs:
- [x] Print deterministic JSON compare receipt to stdout.
- [x] Optional artifact write:
  - `runs/<runB>/comparisons/<runA>/compare_summary.json`

Metrics:
- [x] delta `pass_rate`
- [x] delta `avg_l1`
- [x] delta `p95_l1`
- [x] per-label deltas (when label is present)
- [x] top N regressions by L1 increase (stable sort: delta desc, then `id`)

Determinism rules:
- [x] stable ordering
- [x] stable JSON key order
- [x] no timestamps in scoring fields (metadata allowed)

Tests:
- [x] add `test_compare.py` with tiny fixture runs

## Path A - Phase 10 (Optional): Negative Anchors + Goldset Expansion

Status: `complete`

Goal:
- Improve evaluation sensitivity with intentional mismatches.

Tasks:
- [x] Add 10-20 rows to `data/goldset.jsonl` where:
  - `target_vad` maps to one label
  - text content intentionally reflects a different label

Deliverable:
- richer eval signal for both baseline metrics and `tonesight compare` diffs

## Definition of done

- Spec/version decision documented and enforced.
- Package layout complete (`src/`, `tests/`, `pyproject.toml`).
- Vector + taxonomy + invariant tests passing.
- Vector generator exists and is normative for expected values.
- Receipt schema exists and wrapper APIs conform.
- Quantization + segment boundary stubs exist (no SER required).
- CLI outputs deterministic JSON receipts.
- Any formula/strictness change includes spec bump + regenerated vectors.

