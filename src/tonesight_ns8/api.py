"""High-level deterministic wrapper APIs and receipt builders."""

from __future__ import annotations

from dataclasses import asdict, replace

from .mapping import get_mapping
from .schema import SegmentRecord, ToneReceipt
from .taxonomy import get_vad, load_taxonomy


SPEC_VERSION = "1.0"


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


def tonesight_from_label(
    label: str,
    family: str,
    r: int,
    c: int,
    k: int,
    taxonomy_path: str,
    mapping_id: str = "ns8",
) -> dict:
    """Resolve tone label to VAD and return deterministic receipt."""
    taxonomy = load_taxonomy(taxonomy_path)
    vad = get_vad(label, taxonomy)
    return _build_receipt(family, r, c, k, label=label, vad=vad, mapping_id=mapping_id)


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
    """Use explicit VAD and return deterministic receipt."""
    return _build_receipt(family, r, c, k, vad=(V, A, D), mapping_id=mapping_id)


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
        if not isinstance(v, int) or not isinstance(a, int) or not isinstance(d, int):
            raise ValueError(f"rows[{idx}] V,A,D must be integers")
        receipts.append(tonesight_from_vad(v, a, d, family, r, c, k, mapping_id=mapping_id))
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
