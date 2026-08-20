from app.services.abacus import represent


def test_abacus_place_values():
    rep = represent(2047)
    assert [c["digit"] for c in rep["columns"]] == [2, 0, 4, 7]
