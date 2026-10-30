"""Unit tests untuk Modul Credential Manager ITAM Pro (Tahap 12).

Menguji master config, keamanan mock (prefix CONTOH-, pembuangan secret asli),
hak akses permission, audit log, serta integrasi state dan UI.
"""
import pytest

from itam_pro.pages.security.credential_view import credential_view_page
from itam_pro.services.api_client import api_client
from itam_pro.services.credential_config import CREDENTIAL_CATEGORIES, CREDENTIAL_TABS
from itam_pro.services.mock.audit_mock import MOCK_AUDIT_LOGS
from itam_pro.services.mock.credential_mock import (
    MOCK_CREDENTIALS,
    get_filtered_credentials,
    reveal_mock_credential,
)
from itam_pro.states.credential_state import CredentialState


def test_config_categories_and_tabs() -> None:
    """1. Uji keabsahan konfigurasi master kredensial."""
    assert CREDENTIAL_TABS == [
        "Semua",
        "Website & Aplikasi",
        "Perangkat",
        "Akun Online",
    ]
    expected_categories = {
        "website",
        "detail_pc",
        "sql_server",
        "mikrotik",
        "internet_kantor",
        "email",
        "sosmed",
        "lainnya",
    }
    assert expected_categories.issubset(CREDENTIAL_CATEGORIES.keys())
    for slug, cat in CREDENTIAL_CATEGORIES.items():
        assert cat["slug"] == slug
        assert cat["tab"] in CREDENTIAL_TABS
        assert isinstance(cat["roles"], list)
        assert isinstance(cat["fields"], list)


def test_mock_credentials_security_and_structure() -> None:
    """2. Uji aturan keamanan mock: semua secret wajib berawalan 'CONTOH-'."""
    assert len(MOCK_CREDENTIALS) >= 4
    for item in MOCK_CREDENTIALS:
        assert item["id"].startswith("CRD-")
        assert item["jenis"] in CREDENTIAL_CATEGORIES
        # Cek secret root
        sec = item.get("secret", "")
        if sec:
            assert str(sec).startswith("CONTOH-"), (
                f"Kredensial {item['id']} memiliki secret non-mock!"
            )

        # Cek field_tambahan jika is_secret
        for f in item.get("field_tambahan", []):
            if f.get("is_secret") and f.get("value"):
                for val_line in str(f["value"]).splitlines():
                    if val_line.strip():
                        assert val_line.strip().startswith("CONTOH-"), (
                            f"Field rahasia {f['name']} pada {item['id']} tidak berawalan CONTOH-!"
                        )


def test_security_sanitization_strips_secret() -> None:
    """3. Uji pembuangan kunci 'secret' dan samaran 'value' saat di-query."""
    perms = {k: "edit" for k in CREDENTIAL_CATEGORIES}
    result = get_filtered_credentials(perms, {"tab": "Semua"})
    assert result["total"] > 0

    for row in result["items"]:
        # Kunci 'secret' WAJIB sudah dibuang
        assert "secret" not in row, f"Secret bocor pada row {row.get('id')}"
        assert "secret_ada" in row
        assert isinstance(row["secret_ada"], bool)

        # Samarkan field_tambahan yang bersifat rahasia
        for f in row.get("field_tambahan", []):
            if f.get("is_secret"):
                assert "value" not in f, f"Field rahasia {f['name']} bocor pada row {row['id']}"
                assert "value_ada" in f


def test_permission_filtering_per_role() -> None:
    """4. Uji filter hak akses berdasarkan permissions token."""
    # Skenario 1: Admin memiliki akses ke semua jenis
    admin_perms = {k: "edit" for k in CREDENTIAL_CATEGORIES}
    res_admin = get_filtered_credentials(admin_perms, {"tab": "Semua"})
    assert res_admin["total"] == len(MOCK_CREDENTIALS)

    # Skenario 2: Member hanya punya hak website dan mikrotik
    member_perms = {"website": "reveal", "mikrotik": "view"}
    res_member = get_filtered_credentials(member_perms, {"tab": "Semua"})
    assert res_member["total"] > 0
    for row in res_member["items"]:
        assert row["jenis"] in ("website", "mikrotik")

    # Skenario 3: Viewer tanpa hak akses kredensial (none)
    viewer_perms: dict[str, str] = {}
    res_viewer = get_filtered_credentials(viewer_perms, {"tab": "Semua"})
    assert res_viewer["total"] == 0
    assert len(res_viewer["items"]) == 0


def test_filter_tab_and_search() -> None:
    """5. Uji filter tab dan pencarian teks."""
    perms = {k: "edit" for k in CREDENTIAL_CATEGORIES}

    # Filter Tab Perangkat
    res_perangkat = get_filtered_credentials(perms, {"tab": "Perangkat"})
    for row in res_perangkat["items"]:
        cat = CREDENTIAL_CATEGORIES[row["jenis"]]
        assert cat["tab"] == "Perangkat"

    # Filter Pencarian kata kunci
    res_search = get_filtered_credentials(perms, {"tab": "Semua", "search": "Mikrotik"})
    assert res_search["total"] >= 1
    for row in res_search["items"]:
        haystack = (
            f"{row['induk']} {row['peran']} {row.get('jenis_label', '')} "
            f"{row['target']} {row['catatan']}"
        ).lower()
        assert "mikrotik" in haystack


@pytest.mark.anyio
async def test_audit_event_and_reveal_credential() -> None:
    """6. Uji reveal password kredensial dan pencatatan audit log."""
    initial_log_count = len(MOCK_AUDIT_LOGS)
    target_crd = MOCK_CREDENTIALS[0]["id"]

    # 1. Reveal action
    reveal_res = await reveal_mock_credential(target_crd, "secret", actor="Admin IT")
    assert reveal_res["value"].startswith("CONTOH-")
    assert reveal_res["expires_in"] == 30
    assert len(MOCK_AUDIT_LOGS) == initial_log_count + 1

    last_log = MOCK_AUDIT_LOGS[0]
    assert last_log["actor"] == "Admin IT"
    assert last_log["action"] == "credential.reveal"
    assert last_log["target_id"] == target_crd

    # 2. Copy action
    copy_res = await reveal_mock_credential(target_crd, "secret_copy", actor="Admin IT")
    assert copy_res["value"] == reveal_res["value"]
    assert len(MOCK_AUDIT_LOGS) == initial_log_count + 2
    assert MOCK_AUDIT_LOGS[0]["action"] == "credential.copy"


@pytest.mark.anyio
async def test_api_client_credentials_integration() -> None:
    """7. Uji integrasi APIClient get_credentials dan reveal_credential."""
    # Token admin default
    res = await api_client.get_credentials({"tab": "Semua"})
    assert "items" in res
    assert "total" in res
    assert res["total"] > 0

    # Token member terbatas
    res_member = await api_client.get_credentials({"tab": "Semua"}, token="mock-token-member")
    for item in res_member["items"]:
        assert item["jenis"] in ("website", "mikrotik")

    # Reveal via API client
    rev = await api_client.reveal_credential("CRD-0001", "secret", actor="Admin IT")
    assert rev["value"].startswith("CONTOH-")


def test_credential_state_and_ui_compilation() -> None:
    """8. Uji inisialisasi state, event handlers, dan rendering halaman UI."""
    state = CredentialState()
    assert state.active_tab == "Semua"
    assert state.search_query == ""
    assert not state.is_detail_open
    assert state.revealed_value == ""

    # Uji buka detail
    dummy_item = {"id": "CRD-0001", "induk": "Test Site", "secret_ada": True}
    state.open_detail(dummy_item)
    assert state.is_detail_open
    assert state.selected_crd["id"] == "CRD-0001"

    # Uji sembunyikan rahasia
    state.revealed_value = "CONTOH-Pass123"
    state.hide_revealed()
    assert state.revealed_value == ""

    state.close_detail()
    assert not state.is_detail_open

    # Uji kompilasi UI
    page = credential_view_page()
    assert page is not None
