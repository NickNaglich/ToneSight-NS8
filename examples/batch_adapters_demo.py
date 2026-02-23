"""Deterministic pipeline-style demo for Phase 1 batch adapters."""

from __future__ import annotations

import json

from tonesight_ns8 import tonesight_from_llm_labels, tonesight_from_vad_batch


def main() -> None:
    vad_rows = [
        {"V": 7, "A": 3, "D": 3},
        {"V": 2, "A": 7, "D": 4},
        {"V": 5, "A": 4, "D": 5},
    ]
    label_rows = ["empathetic", "reassuring", "neutral"]

    vad_receipts = tonesight_from_vad_batch(vad_rows, family="TRF", r=6, c=4, k=3)
    label_receipts = tonesight_from_llm_labels(
        label_rows,
        family="TRF",
        r=6,
        c=4,
        k=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
    )

    payload = {
        "vad_batch_count": len(vad_receipts),
        "label_batch_count": len(label_receipts),
        "first_vad_anchor": vad_receipts[0]["output"]["A"],
        "first_label_anchor": label_receipts[0]["output"]["A"],
        "first_label_route": label_receipts[0]["route"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
