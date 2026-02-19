# NS8 Specification (v1.0)

This file freezes the NS8 contract used in this repository.

For implementation assurance mapping (requirements -> tests/artifacts), see:
- `docs/NS8_CONTRACT_ASSURANCE.md`

## Constants

- `spec_version: "1.0"`
- `N = 8` (fixed)
- All indexing is 1-based.

## Strict input domain

Valid input:
- `r, c, k in {1..8}`
- `family in {TLF, TRF, BLF, BRF, TRB, TLB, BLB, BRB}`

Invalid input:
- Must raise `InvalidInput`.
- No silent wrapping for out-of-range `r`, `c`, or `k`.

## Helper definitions

### `wrapN(x, N)`

Maps any integer `x` to `1..N`:

`wrapN(x, N) = ((x - 1) mod N) + 1`

Notes:
- Uses mathematical modulo semantics.
- For negative values, modulo still yields a valid `1..N` result.
- Strict mode rejects invalid input before this is used for external inputs.

### `H(c, N)` and `V(r, N)`

- `H(c, N) = N + 1 - c` (horizontal mirror)
- `V(r, N) = N + 1 - r` (vertical mirror)

Properties:
- `H(H(c, N), N) = c`
- `V(V(r, N), N) = r`

## Canonical seed families

All family logic routes through one of two canonical seed formulas.

### `A_TLF(r, c, k, N)`

`A_TLF = wrapN(c - r + k, N)`

### `A_TRB(r, c, k, N)`

`A_TRB = wrapN(r - c + k, N)`

## Derived families (transform-only definitions)

Derived families must be implemented only as transforms into canonical seeds.
Do not duplicate arithmetic formulas per derived family.

- `TLF(r, c, k) = A_TLF(r, c, k, N)`
- `TRF(r, c, k) = A_TLF(r, H(c, N), k, N)`
- `BLF(r, c, k) = A_TLF(V(r, N), c, k, N)`
- `BRF(r, c, k) = A_TLF(V(r, N), H(c, N), k, N)`

- `TRB(r, c, k) = A_TRB(r, c, k, N)`
- `TLB(r, c, k) = A_TRB(r, H(c, N), k, N)`
- `BLB(r, c, k) = A_TRB(V(r, N), H(c, N), k, N)`
- `BRB(r, c, k) = A_TRB(V(r, N), c, k, N)`

## Output contract

- `A in {1..8}`

## Versioning rule

- Spec version is `1.0`.
- Any change to formulas, transforms, strictness, or helper semantics must:
  - bump `spec_version`
  - regenerate/extend vectors in `vectors/ns8_test_vectors.json`
  - keep old vectors for historical compatibility when appropriate

## Decision record

- 2026-02-14: Phase 2 formula decision resolved as Option A.
- Repository keeps current formulas (`A_TLF = wrapN(c - r + k, N)`, `A_TRB = wrapN(r - c + k, N)`) under `spec_version: "1.0"`.
- External multiplicative alternatives are not adopted in this version.
