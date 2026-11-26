"""State Controller untuk Halaman Pengaturan Akun (/account-settings)."""

import secrets
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.audit_mock import query_audit_logs, record_audit_event
from itam_pro.services.mock.auth_mock import (
    MOCK_USERS,
    get_mock_active_sessions,
    revoke_other_mock_sessions,
    toggle_mock_user_active,
)
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

    # Identitas & info login terbaru
    current_username: str = "admin"
    last_login_display: str = "—"

    # Toggle tampil/sembunyi password
    show_current_password: bool = False
    show_new_password: bool = False
    show_confirm_password: bool = False

    # Sesi aktif & aktivitas terbaru (dari Audit Log)
    active_sessions: list[dict[str, Any]] = []
    session_msg: str = ""
    recent_account_activities: list[dict[str, str]] = []

    # Modal tambah pengguna & feedback manajemen pengguna
    is_add_user_modal_open: bool = False
    user_action_msg: str = ""

    # --- COMPUTED VARS: LIVE PASSWORD VALIDATION & METER 4 SEGMEN ---

    @rx.var(cache=True)
    def new_password_length(self) -> int:
        return len(self.new_password)

    @rx.var(cache=True)
    def pwd_len_counter(self) -> str:
        return f"{len(self.new_password)} / 12"

    @rx.var(cache=True)
    def pwd_rule_min_len(self) -> bool:
        return 12 <= len(self.new_password) <= 128

    @rx.var(cache=True)
    def pwd_rule_no_username(self) -> bool:
        if not self.new_password:
            return False
        uname = (self.current_username or "admin").strip().lower()
        return uname == "" or uname not in self.new_password.lower()

    @rx.var(cache=True)
    def pwd_rule_not_common(self) -> bool:
        if not self.new_password:
            return False
        return self.new_password.lower() not in COMMON_PASSWORDS

    @rx.var(cache=True)
    def pwd_rule_diff_from_old(self) -> bool:
        if not self.new_password:
            return False
        if not self.current_password:
            return True
        return self.new_password != self.current_password

    @rx.var(cache=True)
    def pwd_confirm_mismatch(self) -> bool:
        return bool(self.confirm_password) and self.confirm_password != self.new_password

    @rx.var(cache=True)
    def pwd_strength_score(self) -> int:
        """Skor 0..4 untuk meter kekuatan 4 segmen (tanpa aturan komposisi wajib)."""
        pw = self.new_password
        if not pw:
            return 0
        if pw.lower() in COMMON_PASSWORDS or not self.pwd_rule_no_username:
            return 1
        score = 1
        if len(pw) >= 8:
            score = 2
        if len(pw) >= 12:
            score = 3
        if len(pw) >= 16 and len(set(pw)) >= 8:
            score = 4
        return score

    @rx.var(cache=True)
    def pwd_strength_label(self) -> str:
        score = self.pwd_strength_score
        if score == 0:
            return ""
        if score == 1:
            return "Kekuatan: Lemah"
        if score == 2:
            return "Kekuatan: Sedang"
        if score == 3:
            return "Kekuatan: Kuat"
        return "Kekuatan: Sangat Kuat"

    @rx.var(cache=True)
    def can_submit_password(self) -> bool:
        return (
            bool(self.current_password)
            and self.pwd_rule_min_len
            and self.pwd_rule_no_username
            and self.pwd_rule_not_common
            and self.pwd_rule_diff_from_old
            and self.confirm_password == self.new_password
        )

    @rx.var(cache=True)
    def has_other_sessions(self) -> bool:
        return any(not s.get("is_current", False) for s in self.active_sessions)

    @rx.var(cache=True)
    def has_recent_account_activities(self) -> bool:
        return len(self.recent_account_activities) > 0

    # --- HELPERS & LIFECYCLE ---

    def _refresh_sessions_and_activities(self, username: str) -> None:
        """Muat sesi aktif (mock) dan 3 aktivitas akun terbaru dari Audit Log."""
        # TODO(backend): ganti dengan endpoint sesi aktif & audit log user saat tersedia.
        self.active_sessions = get_mock_active_sessions(username)

        res = query_audit_logs(
            filters={"pelaku": username, "hide_login_success": "false", "group": "false"},
            page=1,
            page_size=3,
        )
        items = res.get("items", [])
        activities: list[dict[str, str]] = []
        last_login = ""
        for item in items:
            tgl = str(item.get("tanggal_wib") or "")
            jam = str(item.get("jam_wib") or "").replace(" WIB", "")
            short_date = tgl.rsplit(" ", 1)[0] if tgl else ""
            waktu_singkat = f"{short_date} · {jam}".strip(" ·")
            activities.append(
                {
                    "id": str(item.get("kode_audit", "")),
                    "label": str(
                        item.get("aksi_label") or item.get("aksi") or "Aktivitas"
                    ),
                    "waktu": waktu_singkat or str(item.get("waktu_wib") or "—"),
                }
            )
            if not last_login and "login" in str(item.get("aksi", "")).lower():
                last_login = str(item.get("waktu_wib") or "")
        self.recent_account_activities = activities
        self.last_login_display = last_login or (
            str(items[0].get("waktu_wib", "—")) if items else "—"
        )

    @rx.event
    async def load_page(self) -> None:
        params = get_current_params(self.router)
        tab = str(params.get("tab", "akun"))
        auth = await self.get_state(AuthState)
        role = auth.current_user.get("role", "Administrator")
        if tab == "pengguna" and role != "Administrator":
            tab = "akun"
        uname = str(auth.current_user.get("username") or "admin").lower()
        self.active_tab = tab
        self.current_username = uname
        self.full_name_input = str(auth.current_user.get("full_name", "Admin IT"))
        self.profile_msg = ""
        self.profile_error = ""
        self.pwd_msg = ""
        self.pwd_error = ""
        self.session_msg = ""
        self.user_action_msg = ""
        self._refresh_sessions_and_activities(uname)
        await self._refresh_users()

    async def _refresh_users(self) -> None:
        if not USE_MOCK:
            try:
                res = await api_client.get_users(page=1, page_size=50)
                items = list(res.get("items", []))
                rows_api: list[dict[str, Any]] = []
                for u in items:
                    uname = str(u.get("username", ""))
                    status_str = str(
                        u.get("status")
                        or ("Aktif" if u.get("is_active", True) else "Nonaktif")
                    )
                    role_str = str(u.get("role", "Member"))
                    rows_api.append(
                        {
                            "id": str(u.get("id", uname)),
                            "username": uname,
                            "full_name": str(u.get("full_name", "")),
                            "role": role_str,
                            "role_variant": (
                                "info" if role_str == "Administrator" else "neutral"
                            ),
                            "status": status_str,
                            "status_variant": (
                                "success" if status_str == "Aktif" else "neutral"
                            ),
                            "toggle_label": (
                                "Nonaktifkan" if status_str == "Aktif" else "Aktifkan"
                            ),
                        }
                    )
                self.users_list = rows_api
                return
            except Exception:
                pass

        rows: list[dict[str, Any]] = []
        for uname, rec in MOCK_USERS.items():
            u = rec["user"]
            status_str = "Aktif" if u.get("is_active", True) else "Nonaktif"
            role_str = str(u.get("role", "Member"))
            rows.append(
                {
                    "id": str(u.get("id", uname)),
                    "username": str(u.get("username", uname)),
                    "full_name": str(u.get("full_name", "")),
                    "role": role_str,
                    "role_variant": "info" if role_str == "Administrator" else "neutral",
                    "status": status_str,
                    "status_variant": "success" if status_str == "Aktif" else "neutral",
                    "toggle_label": (
                        "Nonaktifkan" if status_str == "Aktif" else "Aktifkan"
                    ),
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
    def toggle_show_current_password(self) -> None:
        self.show_current_password = not self.show_current_password

    @rx.event
    def toggle_show_new_password(self) -> None:
        self.show_new_password = not self.show_new_password

    @rx.event
    def toggle_show_confirm_password(self) -> None:
        self.show_confirm_password = not self.show_confirm_password

    @rx.event
    async def revoke_other_sessions(self) -> None:
        """Keluarkan semua sesi lain selain sesi saat ini.
        TODO(backend): panggil DELETE /api/v1/auth/sessions/others saat endpoint tersedia.
        """
        auth = await self.get_state(AuthState)
        uname = str(
            auth.current_user.get("username") or self.current_username or "admin"
        ).lower()
        actor = str(auth.current_user.get("full_name") or "Admin IT")
        removed = revoke_other_mock_sessions(uname)
        self.active_sessions = get_mock_active_sessions(uname)
        if removed > 0:
            record_audit_event(
                actor,
                "user.sesi_dicabut",
                uname,
                f"Mengeluarkan {removed} sesi lain pada akun {uname}",
                username=uname,
                modul="Autentikasi",
            )
            self.session_msg = f"{removed} sesi lain berhasil dikeluarkan."
        else:
            self.session_msg = "Tidak ada sesi lain yang aktif."
        self._refresh_sessions_and_activities(uname)

    @rx.event
    def open_add_user_modal(self) -> None:
        self.new_user_fullname = ""
        self.new_user_username = ""
        self.new_user_role = "Member"
        self.user_form_error = ""
        self.is_add_user_modal_open = True

    @rx.event
    def close_add_user_modal(self) -> None:
        self.is_add_user_modal_open = False
        self.user_form_error = ""

    @rx.event
    async def toggle_user_status(self, username: str) -> None:
        """Aktifkan/nonaktifkan akun (Administrator aktif terakhir dilindungi)."""
        auth = await self.get_state(AuthState)
        if auth.current_user.get("role") != "Administrator":
            self.user_form_error = "Hanya Administrator yang dapat mengubah status pengguna."
            return
        ok, msg = toggle_mock_user_active(username)
        if not ok:
            self.user_form_error = msg
            self.user_action_msg = ""
            return
        actor = str(auth.current_user.get("full_name", "Admin IT"))
        action_name = (
            "user.pengguna_diaktifkan"
            if "diaktifkan" in msg
            else "user.pengguna_dinonaktifkan"
        )
        record_audit_event(actor, action_name, username, msg, modul="Pengguna")
        self.user_form_error = ""
        self.user_action_msg = msg
        await self._refresh_users()

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
            record_audit_event(
                actor, "user.password_diubah", uname, "Pengguna mengganti password"
            )

        self.pwd_error = ""
        self.pwd_msg = "Password berhasil diperbarui."
        self._refresh_sessions_and_activities(uname)

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
            self.user_form_error = (
                "Nama lengkap wajib diisi dan username harus 3-32 karakter."
            )
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
            record_audit_event(
                actor, "user.pengguna_dibuat", uname, f"Peran: {self.new_user_role}"
            )

        self.new_user_fullname = ""
        self.new_user_username = ""
        self.user_form_error = ""
        self.generated_temp_password = temp_pw
        self.is_add_user_modal_open = False
        await self._refresh_users()


__all__ = ["AccountState"]
