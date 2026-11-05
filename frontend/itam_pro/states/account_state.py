"""State Controller untuk Halaman Pengaturan Akun (/account-settings)."""
import secrets
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.audit_mock import record_audit_event
from itam_pro.services.mock.auth_mock import MOCK_USERS
from itam_pro.services.router_utils import get_current_params
from itam_pro.states.auth_state import AuthState

COMMON_PASSWORDS = {
    "password123",
    "admin123",
    "12345678",
    "123456789012",
    "qwerty123456",
    "itampro12345",
}


class AccountState(rx.State):
    active_tab: str = "akun"
    full_name_input: str = ""
    profile_msg: str = ""
    profile_error: str = ""

    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    pwd_msg: str = ""
    pwd_error: str = ""

    users_list: list[dict[str, Any]] = []
    new_user_fullname: str = ""
    new_user_username: str = ""
    new_user_role: str = "Member"
    user_form_error: str = ""
    generated_temp_password: str = ""

    @rx.event
    async def load_page(self) -> None:
        params = get_current_params(self.router)
        tab = str(params.get("tab", "akun"))
        auth = await self.get_state(AuthState)
        role = auth.current_user.get("role", "Administrator")
        if tab == "pengguna" and role != "Administrator":
            tab = "akun"
        self.active_tab = tab
        self.full_name_input = str(auth.current_user.get("full_name", "Admin IT"))
        self.profile_msg = ""
        self.profile_error = ""
        self.pwd_msg = ""
        self.pwd_error = ""
        await self._refresh_users()

    async def _refresh_users(self) -> None:
        if not USE_MOCK:
            try:
                res = await api_client.get_users(page=1, page_size=50)
                items = list(res.get("items", []))
                self.users_list = [
                    {
                        "id": str(u.get("id", u.get("username", ""))),
                        "username": str(u.get("username", "")),
                        "full_name": str(u.get("full_name", "")),
                        "role": str(u.get("role", "Member")),
                        "status": str(
                            u.get("status")
                            or ("Aktif" if u.get("is_active", True) else "Nonaktif")
                        ),
                    }
                    for u in items
                ]
                return
            except Exception:
                pass

        rows: list[dict[str, Any]] = []
        for uname, rec in MOCK_USERS.items():
            u = rec["user"]
            rows.append(
                {
                    "id": str(u.get("id", uname)),
                    "username": str(u.get("username", uname)),
                    "full_name": str(u.get("full_name", "")),
                    "role": str(u.get("role", "Member")),
                    "status": "Aktif" if u.get("is_active", True) else "Nonaktif",
                }
            )
        self.users_list = rows

    @rx.event
    def set_tab(self, tab: str) -> Any:
        self.active_tab = tab
        return rx.redirect(f"/account-settings?tab={tab}")

    @rx.event
    def set_full_name_input(self, val: str) -> None:
        self.full_name_input = val

    @rx.event
    async def save_profile(self) -> None:
        cleaned = self.full_name_input.strip()
        if not cleaned or len(cleaned) > 100:
            self.profile_error = "Nama lengkap wajib diisi (maksimal 100 karakter)."
            self.profile_msg = ""
            return
        auth = await self.get_state(AuthState)
        uname = str(auth.current_user.get("username", "admin")).lower()
        if uname in MOCK_USERS:
            MOCK_USERS[uname]["user"]["full_name"] = cleaned
        auth.current_user["full_name"] = cleaned
        self.profile_error = ""
        self.profile_msg = "Nama lengkap berhasil diperbarui."

    @rx.event
    def set_current_password(self, val: str) -> None:
        self.current_password = val

    @rx.event
    def set_new_password(self, val: str) -> None:
        self.new_password = val

    @rx.event
    def set_confirm_password(self, val: str) -> None:
        self.confirm_password = val

    @rx.event
    async def submit_change_password(self) -> None:
        auth = await self.get_state(AuthState)
        uname = str(auth.current_user.get("username", "admin")).lower()
        actor = str(auth.current_user.get("full_name", "Admin IT"))
        rec = MOCK_USERS.get(uname)

        cur_pw = self.current_password
        new_pw = self.new_password
        cnf_pw = self.confirm_password

        # Kosongkan password dari state segera setelah dibaca (Aturan K3/B1)
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""

        if USE_MOCK and (not rec or rec.get("password") != cur_pw):
            self.pwd_error = "Password saat ini salah."
            self.pwd_msg = ""
            return
        if len(new_pw) < 12 or len(new_pw) > 128:
            self.pwd_error = "Password baru wajib memiliki panjang 12 hingga 128 karakter."
            self.pwd_msg = ""
            return
        if uname in new_pw.lower():
            self.pwd_error = "Password baru tidak boleh memuat username Anda."
            self.pwd_msg = ""
            return
        if new_pw == cur_pw:
            self.pwd_error = "Password baru tidak boleh sama dengan password saat ini."
            self.pwd_msg = ""
            return
        if new_pw.lower() in COMMON_PASSWORDS:
            self.pwd_error = "Password terlalu umum. Gunakan kombinasi yang lebih unik."
            self.pwd_msg = ""
            return
        if new_pw != cnf_pw:
            self.pwd_error = "Konfirmasi password baru tidak cocok."
            self.pwd_msg = ""
            return

        if not USE_MOCK:
            try:
                await api_client.change_password(cur_pw, new_pw)
            except Exception as exc:
                self.pwd_error = str(exc)
                self.pwd_msg = ""
                return
        elif rec:
            rec["password"] = new_pw
            record_audit_event(actor, "user.password_diubah", uname, "Pengguna mengganti password")

        self.pwd_error = ""
        self.pwd_msg = "Password berhasil diperbarui."

    @rx.event
    def set_new_user_fullname(self, val: str) -> None:
        self.new_user_fullname = val

    @rx.event
    def set_new_user_username(self, val: str) -> None:
        self.new_user_username = val

    @rx.event
    def set_new_user_role(self, val: str) -> None:
        self.new_user_role = val

    @rx.event
    def close_temp_password_modal(self) -> None:
        self.generated_temp_password = ""

    @rx.event
    async def create_new_user(self) -> None:
        auth = await self.get_state(AuthState)
        if auth.current_user.get("role") != "Administrator":
            self.user_form_error = "Hanya Administrator yang dapat menambah pengguna."
            return

        uname = self.new_user_username.strip().lower()
        fname = self.new_user_fullname.strip()
        if not fname or len(uname) < 3 or len(uname) > 32:
            self.user_form_error = "Nama lengkap wajib diisi dan username harus 3-32 karakter."
            return
        if USE_MOCK and uname in MOCK_USERS:
            self.user_form_error = "Username sudah digunakan."
            return

        temp_pw = f"Tmp-{secrets.token_urlsafe(12)}"
        if not USE_MOCK:
            try:
                await api_client.create_user(
                    {
                        "username": uname,
                        "full_name": fname,
                        "role": self.new_user_role,
                        "password": temp_pw,
                        "is_active": True,
                    }
                )
            except Exception as exc:
                self.user_form_error = str(exc)
                return
        else:
            MOCK_USERS[uname] = {
                "password": temp_pw,
                "user": {
                    "id": len(MOCK_USERS) + 1,
                    "username": uname,
                    "full_name": fname,
                    "role": self.new_user_role,
                    "is_active": True,
                },
                "access_token": f"mock-token-{uname}",
            }
            actor = str(auth.current_user.get("full_name", "Admin IT"))
            record_audit_event(actor, "user.pengguna_dibuat", uname, f"Peran: {self.new_user_role}")

        self.new_user_fullname = ""
        self.new_user_username = ""
        self.user_form_error = ""
        self.generated_temp_password = temp_pw
        await self._refresh_users()


__all__ = ["AccountState"]

