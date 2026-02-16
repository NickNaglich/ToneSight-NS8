from pathlib import Path


def test_vectors_alias_matches_root():
    root = Path("ns8_test_vectors.json")
    alias = Path("vectors/ns8_test_vectors.json")
    assert root.exists()
    assert alias.exists()
    assert root.read_text(encoding="utf-8") == alias.read_text(encoding="utf-8")


def test_taxonomy_alias_matches_root():
    root = Path("tone_taxonomy.v1.json")
    alias = Path("taxonomy/tone_taxonomy.v1.json")
    assert root.exists()
    assert alias.exists()
    assert root.read_text(encoding="utf-8") == alias.read_text(encoding="utf-8")
