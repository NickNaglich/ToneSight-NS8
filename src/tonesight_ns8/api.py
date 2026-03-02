"""High-level deterministic wrapper APIs and receipt builders."""

from __future__ import annotations

from dataclasses import asdict, replace
import warnings

from .mapping import get_mapping
from .schema import SegmentRecord, ToneReceipt
from .taxonomy import get_vad, load_taxonomy


SPEC_VERSION = "1.0"
_DEPRECATION_HINT = (
    "This function attaches VAD/label context to the receipt, but anchor A is computed from NS8 "
    "routing inputs (family,r,c,k). Use tonesight_receipt_from_vad_context / "
    "tonesight_receipt_from_label_context for explicit semantics."
)


def _validate_vad_triplet(V: int, A: int, D: int, *, context: str) -> tuple[int, int, int]:
    for key, value in (("V", V), ("A", A), ("D", D)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{context} {key} must be an integer in 1..8")
        if value < 1 or value > 8:
            raise ValueError(f"{context} {key} must be in 1..8")
    return (V, A, D)


def _build_receipt(
    family: str,
    r: int,
    c: int,
    k: int,
    *,
    label: str | None = None,
    vad: tuple[int, int, int] | None = None,
    mapping_id: str = "ns8",
) -> dict:
    mapping = get_mapping(mapping_id)
    seed_family, r_prime, c_prime, _ = mapping.resolve_to_seed(family, r, c, k, 8)
    anchor = mapping.compute_A(family, r, c, k, 8)

    input_obj = {"family": family, "r": r, "c": c, "k": k}
    if label is not None:
        input_obj["label"] = label
    if vad is not None:
        input_obj["vad"] = {"V": vad[0], "A": vad[1], "D": vad[2]}

    receipt = ToneReceipt(
        spec_version=SPEC_VERSION,
        input=input_obj,
        route={"seed_family": seed_family, "r_prime": r_prime, "c_prime": c_prime},
        output={"A": anchor},
    )
    return asdict(receipt)


def tonesight_receipt_from_label_context(
    label: str,
    family: str,
    r: int,
    c: int,
    k: int,
    taxonomy_path: str,
    mapping_id: str = "ns8",
) -> dict:
    """Resolve label to VAD context and return deterministic receipt."""
    taxonomy = load_taxonomy(taxonomy_path)
    vad = get_vad(label, taxonomy)
    return _build_receipt(family, r, c, k, label=label, vad=vad, mapping_id=mapping_id)


def tonesight_receipt_from_vad_context(
    V: int,
    A: int,
    D: int,
    family: str,
    r: int,
    c: int,
    k: int,
    mapping_id: str = "ns8",
) -> dict:
    """Attach explicit VAD context and return deterministic receipt."""
    vad = _validate_vad_triplet(V, A, D, context="input")
    return _build_receipt(family, r, c, k, vad=vad, mapping_id=mapping_id)


def tonesight_from_label(
    label: str,
    family: str,
    r: int,
    c: int,
    k: int,
    taxonomy_path: str,
    mapping_id: str = "ns8",
) -> dict:
    """Deprecated alias for tonesight_receipt_from_label_context."""
    warnings.warn(
        "tonesight_from_label is deprecated. "
        "Use tonesight_receipt_from_label_context instead. "
        + _DEPRECATION_HINT,
        DeprecationWarning,
        stacklevel=2,
    )
    return tonesight_receipt_from_label_context(
        label=label,
        family=family,
        r=r,
        c=c,
        k=k,
        taxonomy_path=taxonomy_path,
        mapping_id=mapping_id,
    )


def tonesight_from_vad(
    V: int,
    A: int,
    D: int,
    family: str,
    r: int,
    c: int,
    k: int,
    mapping_id: str = "ns8",
) -> dict:
    """Deprecated alias for tonesight_receipt_from_vad_context."""
    warnings.warn(
        "tonesight_from_vad is deprecated. "
        "Use tonesight_receipt_from_vad_context instead. "
        + _DEPRECATION_HINT,
        DeprecationWarning,
        stacklevel=2,
    )
    return tonesight_receipt_from_vad_context(
        V=V,
        A=A,
        D=D,
        family=family,
        r=r,
        c=c,
        k=k,
        mapping_id=mapping_id,
    )


def tonesight_from_vad_batch(
    rows: list[dict[str, int]],
    family: str,
    r: int,
    c: int,
    k: int,
    mapping_id: str = "ns8",
) -> list[dict]:
    """Map an ordered batch of VAD rows to deterministic receipts."""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list of {'V','A','D'} objects")
    receipts: list[dict] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{idx}] must be an object")
        if set(row.keys()) != {"V", "A", "D"}:
            raise ValueError(f"rows[{idx}] must define exactly V,A,D")
        v = row["V"]
        a = row["A"]
        d = row["D"]
        _validate_vad_triplet(v, a, d, context=f"rows[{idx}]")
        receipts.append(
            tonesight_receipt_from_vad_context(v, a, d, family, r, c, k, mapping_id=mapping_id)
        )
    return receipts


def tonesight_from_llm_labels(
    labels: list[str],
    family: str,
    r: int,
    c: int,
    k: int,
    taxonomy_path: str,
    mapping_id: str = "ns8",
) -> list[dict]:
    """Map an ordered batch of upstream labels to deterministic receipts."""
    if not isinstance(labels, list):
        raise ValueError("labels must be a list of strings")
    taxonomy = load_taxonomy(taxonomy_path)
    receipts: list[dict] = []
    for idx, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"labels[{idx}] must be a non-empty string")
        vad = get_vad(label, taxonomy)
        receipts.append(_build_receipt(family, r, c, k, label=label, vad=vad, mapping_id=mapping_id))
    return receipts


def tonesight_receipt_from_segment(
    segment: SegmentRecord,
    family: str,
    r: int,
    c: int,
    k: int,
    mapping_id: str = "ns8",
) -> dict:
    """Build receipt for a segment using segment VAD bins."""
    return _build_receipt(
        family,
        r,
        c,
        k,
        label=segment.tone_label,
        vad=(segment.V, segment.A, segment.D),
        mapping_id=mapping_id,
    )


def attach_tonesight_to_segment(
    segment: SegmentRecord,
    family: str,
    r: int,
    c: int,
    k: int,
    mapping_id: str = "ns8",
) -> SegmentRecord:
    """Return a copy of segment with NS8 route/anchor fields filled."""
    mapping = get_mapping(mapping_id)
    seed_family, r_prime, c_prime, _ = mapping.resolve_to_seed(family, r, c, k, 8)
    anchor = mapping.compute_A(family, r, c, k, 8)
    return replace(
        segment,
        ns8_family=family,
        ns8_r=r,
        ns8_c=c,
        ns8_k=k,
        ns8_seed_family=seed_family,
        ns8_r_prime=r_prime,
        ns8_c_prime=c_prime,
        ns8_A=anchor,
    )
