"""Reference implementation for NS8 family scoring (spec v1.0)."""

from __future__ import annotations

from dataclasses import dataclass

N = 8
VALID_FAMILIES = {"TLF", "TRF", "BLF", "BRF", "TRB", "TLB", "BLB", "BRB"}


class InvalidInput(ValueError):
    """Raised when strict NS8 input validation fails."""


@dataclass(frozen=True)
class Route:
    seed_family: str
    r_prime: int
    c_prime: int


def wrapN(x: int, n: int = N) -> int:
    return ((x - 1) % n) + 1


def H(c: int, n: int = N) -> int:
    return n + 1 - c


def V(r: int, n: int = N) -> int:
    return n + 1 - r


def _validate_inputs(family: str, r: int, c: int, k: int, n: int = N) -> None:
    if not isinstance(n, int) or isinstance(n, bool):
        raise InvalidInput("N must be int")
    if n != N:
        raise InvalidInput(f"N must be {N}")
    if family not in VALID_FAMILIES:
        raise InvalidInput(f"Invalid family: {family}")
    if not isinstance(r, int) or isinstance(r, bool):
        raise InvalidInput("r must be int")
    if not isinstance(c, int) or isinstance(c, bool):
        raise InvalidInput("c must be int")
    if not isinstance(k, int) or isinstance(k, bool):
        raise InvalidInput("k must be int")
    if not (1 <= r <= n):
        raise InvalidInput("r must be in 1..8")
    if not (1 <= c <= n):
        raise InvalidInput("c must be in 1..8")
    if not (1 <= k <= n):
        raise InvalidInput("k must be in 1..8")


def _A_TLF(r: int, c: int, k: int, n: int = N) -> int:
    return wrapN(c - r + k, n)


def _A_TRB(r: int, c: int, k: int, n: int = N) -> int:
    return wrapN(r - c + k, n)


def ns8_route(family: str, r: int, c: int, k: int, n: int = N) -> Route:
    _validate_inputs(family, r, c, k, n)
    if family == "TLF":
        return Route("TLF", r, c)
    if family == "TRF":
        return Route("TLF", r, H(c, n))
    if family == "BLF":
        return Route("TLF", V(r, n), c)
    if family == "BRF":
        return Route("TLF", V(r, n), H(c, n))

    if family == "TRB":
        return Route("TRB", r, c)
    if family == "TLB":
        return Route("TRB", r, H(c, n))
    if family == "BLB":
        return Route("TRB", V(r, n), H(c, n))
    return Route("TRB", V(r, n), c)


def ns8_A(family: str, r: int, c: int, k: int, n: int = N) -> int:
    route = ns8_route(family, r, c, k, n)
    if route.seed_family == "TLF":
        return _A_TLF(route.r_prime, route.c_prime, k, n)
    return _A_TRB(route.r_prime, route.c_prime, k, n)
