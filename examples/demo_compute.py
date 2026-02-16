"""Minimal deterministic demo using the public API."""

from __future__ import annotations

import json

from tonesight_ns8 import tonesight_from_label


def main() -> None:
    receipt = tonesight_from_label(
        label="empathetic",
        family="TRF",
        r=6,
        c=4,
        k=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
