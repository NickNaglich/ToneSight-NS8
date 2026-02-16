from ns8_ref import H, V, ns8_A


def test_invariant_trf_equals_tlf_hc():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("TRF", r, c, k) == ns8_A("TLF", r, H(c), k)


def test_invariant_blf_equals_tlf_vr():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("BLF", r, c, k) == ns8_A("TLF", V(r), c, k)


def test_invariant_brf_equals_tlf_vr_hc():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("BRF", r, c, k) == ns8_A("TLF", V(r), H(c), k)


def test_invariant_tlb_equals_trb_hc():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("TLB", r, c, k) == ns8_A("TRB", r, H(c), k)


def test_invariant_brb_equals_trb_vr():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("BRB", r, c, k) == ns8_A("TRB", V(r), c, k)


def test_invariant_blb_equals_trb_vr_hc():
    for r in range(1, 9):
        for c in range(1, 9):
            for k in range(1, 9):
                assert ns8_A("BLB", r, c, k) == ns8_A("TRB", V(r), H(c), k)


def test_invariant_double_mirrors_identity():
    for x in range(1, 9):
        assert H(H(x)) == x
        assert V(V(x)) == x
