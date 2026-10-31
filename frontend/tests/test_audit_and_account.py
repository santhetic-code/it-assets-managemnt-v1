"""Pengujian Modul Audit Log dan Pengaturan Akun."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from itam_pro.pages.admin.account_settings import account_settings_page
from itam_pro.pages.security.audit_view import audit_view_page
from itam_pro.services.mock.audit_mock import (
    MOCK_AUDIT_LOGS,
    query_audit_logs,
    record_audit_event,
)
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
    state.set_search_query("SRV-0001")
    assert state.search_query == "SRV-0001"
    assert len(state.logs) >= 1
    assert any("SRV-0001" in item["target_id"] for item in state.logs)

    state.reset_filters()
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
