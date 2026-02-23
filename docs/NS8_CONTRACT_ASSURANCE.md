# NS8 Contract Assurance (v1)

This document explains how ToneSight NS8 operationalizes the mathematical contract in `docs/SPEC_NS8.md` and how that contract is verified in code/tests.

## Scope

This repository provides:
- a formalized discrete contract (`N=8`, strict domain, canonical seed routing, transform-only derived families)
- executable conformance evidence (vectors, invariants, strict-validation tests)
- runtime traceability (`spec_version`, dataset/config hashes in receipts and CLI trace)

This repository does not provide:
- machine-checked theorem proving (for example Coq/Isabelle/TLA+ model checking)
- psychological ground-truth claims about affect states

## Conformance vs Empirical Evidence

Conformance (guaranteed by contract/tests):
- behavior fixed by `docs/SPEC_NS8.md`
- vectors + invariants + strict validation must pass

Empirical evidence (benchmark outputs, not guarantees):
- operational comparisons vs baseline discretizations
- noise/drift/model-swap behavior measurements

Evidence entrypoint:
- `python -m tonesight_ns8.cli benchmark --suite core`
- see `docs/WHY_NS8.md` and artifacts under `runs/benchmarks/core/`

## Contract Model

Authoritative model:
- `docs/SPEC_NS8.md`

Reference oracle:
- `ns8_ref.py`

Package wrapper policy:
- `src/tonesight_ns8/ns8.py` delegates to the oracle and preserves oracle error semantics through `tonesight_ns8.errors.InvalidInput`.

## Axioms and Invariants

Core axioms (see `docs/SPEC_NS8.md`):
- fixed lattice size `N=8`
- strict domain: `r,c,k in {1..8}`, family in allowed family set
- canonical seed formulas:
  - `A_TLF = wrapN(c - r + k, N)`
  - `A_TRB = wrapN(r - c + k, N)`
- derived families are defined only via transforms to canonical seeds

Symmetry invariants validated by tests:
- double-mirror identity: `H(H(x)) = x`, `V(V(x)) = x`
- derived-family equivalences, for example:
  - `TRF(r,c,k) == TLF(r,H(c),k)`
  - `BRF(r,c,k) == TLF(V(r),H(c),k)`
  - `TLB(r,c,k) == TRB(r,H(c),k)`
  - `BLB(r,c,k) == TRB(V(r),H(c),k)`

Evidence:
- `tests/test_invariants.py`
- `tests/test_ns8_property_invariants.py` (exhaustive full-domain checks across `family x r x c x k`, `N=8`)

## Determinism Statement

For fixed `(family, r, c, k, N=8)` in-domain inputs, `ns8_A` is deterministic and side-effect free:
- repeated calls produce identical `A`
- output is always in `1..8`
- invalid inputs are rejected explicitly

Evidence:
- `test_ns8_vectors.py` (normative vector cases)
- `tests/test_strict_validation.py` (strict type/domain rejection)
- `tests/test_ns8_property_invariants.py` (output domain and canonical-route bounds over full valid domain)
- wrapper/registry conformance tests (`tests/test_mapping_registry.py`, `tests/test_mapping_conformance.py`)

Topology compare note:
- `compare --distance topology` is an analysis-layer option, not a change to NS8 core formulas.
- It derives deterministic distance from NS8 anchors over run artifacts and is validated by:
  - `tests/test_compare_topology_distance.py`

## Traceability Matrix

| Requirement | Artifact/Implementation | Verification |
|---|---|---|
| Fixed spec and formulas | `docs/SPEC_NS8.md`, `ns8_ref.py` | `test_ns8_vectors.py` |
| Derived families are transform-only | `ns8_ref.py:ns8_route` | `tests/test_invariants.py` |
| Strict input validation | `ns8_ref.py:_validate_inputs` | `tests/test_strict_validation.py` |
| Oracle-first parity policy | `src/tonesight_ns8/ns8.py` | wrapper/registry tests |
| Run comparability across versions | `spec_version` in receipts and compare gating | `test_eval_runner.py`, `test_compare.py` |
| Reproducible run tracing | receipt hashes + CLI `trace` metadata | `test_cli.py` |

## Equivalence Policy for Future Implementations

If an optimized NS8 implementation is introduced, it must be extensionally equivalent to the oracle for the v1 domain:
- same accepted/rejected input set
- same route resolution
- same anchor outputs

Minimum acceptance gate:
1. pass normative vector suite
2. pass invariants suite
3. pass strict-validation suite
4. preserve `spec_version` governance rules in `docs/SPEC_NS8.md`
