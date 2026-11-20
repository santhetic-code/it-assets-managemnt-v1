"""Pengujian Modul Audit Log dan Pengaturan Akun."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from itam_pro.pages.admin.account_settings import account_settings_page
from itam_pro.pages.security.audit_view import audit_view_page
from itam_pro.services.mock.audit_mock import (
    MOCK_AUDIT_LOGS,
    compute_mock_severity,
    delete_audit_event,
    export_mock_audit_csv,
    format_mock_timestamps,
    query_audit_logs,
    record_audit_event,
    sanitize_csv_cell,
    update_audit_event,
)
from itam_pro.services.router_utils import extract_client_origin_from_router
from itam_pro.states.account_state import AccountState
from itam_pro.states.audit_state import AuditState


def test_audit_logs_query_and_record():
    initial_count = len(MOCK_AUDIT_LOGS)
    record_audit_event("Tester", "user.login", "USR-99", "Login uji coba")
    assert len(MOCK_AUDIT_LOGS) == initial_count + 1
    assert MOCK_AUDIT_LOGS[0]["actor"] == "Tester"

    res = query_audit_logs({"search": "Tester"}, page=1, page_size=10)
    assert res["total"] >= 1
    assert any(item["actor"] == "Tester" for item in res["items"])

    res_module = query_audit_logs({"module": "user"}, page=1, page_size=10)
    assert all("USER" in item["module_badge"] for item in res_module["items"])


def test_audit_view_page_compilation():
    comp = audit_view_page()
    assert comp is not None


def test_account_settings_page_compilation():
    comp = account_settings_page()
    assert comp is not None


@pytest.mark.anyio
async def test_audit_state_flow():
    state = AuditState()
    res = state.set_search_query("SRV-0001")
    if hasattr(res, "__await__"):
        await res
    if not state.logs and hasattr(state, "load_page"):
        load_res = state.load_page()
        if hasattr(load_res, "__await__"):
            await load_res
    assert state.search_query == "SRV-0001"
    assert len(state.logs) >= 1
    assert any("SRV-0001" in item["target_id"] for item in state.logs)

    rst = state.reset_filters()
    if hasattr(rst, "__await__"):
        await rst
    assert state.search_query == ""
    assert state.module_filter == ""


@pytest.mark.anyio
async def test_account_state_password_validation(monkeypatch):
    mock_auth = MagicMock()
    mock_auth.current_user = {"username": "admin", "full_name": "Admin IT"}
    monkeypatch.setattr(AccountState, "get_state", AsyncMock(return_value=mock_auth))

    state = AccountState()
    state.current_password = "wrongpassword"
    state.new_password = "NewValidPassword2026!"
    state.confirm_password = "NewValidPassword2026!"
    await state.submit_change_password()
    assert state.pwd_error == "Password saat ini salah."

    # Test short password (< 12)
    state.current_password = "password123"  # default admin di mock
    state.new_password = "short"
    state.confirm_password = "short"
    await state.submit_change_password()
    assert "12 hingga 128 karakter" in state.pwd_error


def test_frontend_audit_severity_wib_append_only_and_csv_injection():
    assert compute_mock_severity("login_gagal") == "Peringatan"
    assert compute_mock_severity("reveal_ditolak") == "Peringatan"
    assert compute_mock_severity("audit_diekspor") == "Penting"
    assert compute_mock_severity("asset.update") == "Info"

    # UTC -> WIB
    ts = format_mock_timestamps("2026-11-18T21:29:00+00:00")
    assert ts["tanggal_wib"] == "19 Nov 2026"
    assert ts["jam_wib"] == "04:29 WIB"

    # Append-only guard
    with pytest.raises(ValueError, match="append-only"):
        update_audit_event("AUD-000731")
    with pytest.raises(ValueError, match="append-only"):
        delete_audit_event("AUD-000731")

    # Anti CSV-injection + event audit_diekspor
    assert sanitize_csv_cell("=CMD|'calc'!A0").startswith("'")
    assert sanitize_csv_cell("+1+1").startswith("'")
    assert sanitize_csv_cell("-2+3").startswith("'")
    assert sanitize_csv_cell("@SUM(1,2)").startswith("'")

    record_audit_event("Tester", "asset.update", "=MALICIOUS", "password=Secret123")
    csv_text = export_mock_audit_csv({"search": "MALICIOUS"}, actor="Admin IT").decode(
        "utf-8-sig"
    )
    assert "'=MALICIOUS" in csv_text
    assert "Secret123" not in csv_text
    assert MOCK_AUDIT_LOGS[0]["action"] == "audit_diekspor"


def test_extract_client_origin_from_reflex_router():
    fake_router = SimpleNamespace(
        headers=SimpleNamespace(
            raw_headers={
                "X-Forwarded-For": "10.20.5.41, 172.20.0.4",
                "User-Agent": "Mozilla/5.0 Chrome/130.0.0.0 Windows NT 10.0",
            },
            x_forwarded_for="10.20.5.41, 172.20.0.4",
            user_agent="Mozilla/5.0 Chrome/130.0.0.0 Windows NT 10.0",
        ),
        session=SimpleNamespace(client_ip="172.20.0.4"),
    )
    ip, ua = extract_client_origin_from_router(fake_router)
    assert ip == "10.20.5.41"
    assert "Chrome/130" in ua
    assert "python-httpx" not in ua
