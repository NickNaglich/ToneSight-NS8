import json
import math
import re
import warnings
from pathlib import Path


TAXONOMY_PATH = Path("taxonomy/tone_taxonomy.v1.json")
LABEL_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def load_taxonomy():
    with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_taxonomy_schema_and_domain():
    data = load_taxonomy()
    assert data["spec_version"] == "1.0"
    assert data["N"] == 8
    assert data["vad_scale"] == "1..8"
    tones = data["tones"]
    assert isinstance(tones, dict)
    assert 8 <= len(tones) <= 15

    for label, vad in tones.items():
        assert LABEL_RE.match(label), f"Label must be lowercase snake_case: {label}"
        assert set(vad.keys()) == {"V", "A", "D"}, f"Tone {label} must include exactly V,A,D"
        for dim in ("V", "A", "D"):
            value = vad[dim]
            assert isinstance(value, int), f"{label}.{dim} must be int"
            assert 1 <= value <= 8, f"{label}.{dim} must be in 1..8"


def test_taxonomy_distance_sanity_warnings():
    data = load_taxonomy()
    tones = data["tones"]
    items = list(tones.items())

    for i in range(len(items)):
        label_a, a = items[i]
        vec_a = (a["V"], a["A"], a["D"])
        for j in range(i + 1, len(items)):
            label_b, b = items[j]
            vec_b = (b["V"], b["A"], b["D"])

            if vec_a == vec_b:
                warnings.warn(
                    f"Duplicate tone vectors: {label_a} and {label_b} both map to {vec_a}",
                    UserWarning,
                )

            dist = math.dist(vec_a, vec_b)
            if dist < 1.5:
                warnings.warn(
                    (
                        f"Very close tone vectors: {label_a}={vec_a} and "
                        f"{label_b}={vec_b} (distance={dist:.3f})"
                    ),
                    UserWarning,
                )
