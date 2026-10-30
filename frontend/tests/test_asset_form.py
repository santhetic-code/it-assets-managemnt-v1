from itam_pro.states.asset_state import AssetState


def test_duplicate_count_validation():
    # Simulasi instance state (untuk pengujian method)
    state = AssetState()

    # Harus di-cap ke 50
    state.set_duplicate_count("100")
    assert state.duplicate_count_form == 50

    # Harus di-cap ke 1 (minimal)
    state.set_duplicate_count("-5")
    assert state.duplicate_count_form == 1

    # Gagal parsing integer murni (misal karakter "²" dari isdigit() bypass)
    state.set_duplicate_count("2²")
    assert state.duplicate_count_form == 1

    # Input valid
    state.set_duplicate_count("15")
    assert state.duplicate_count_form == 15
