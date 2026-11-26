"""
State Autentikasi ITAM Pro.
Mengelola state welcome/form kartu login, LocalStorage seen_welcome, dan sesi pengguna.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import reflex as rx

from itam_pro.services.api_client import (
    AuthenticationError,
    ServiceUnavailableError,
    api_client,
)
from itam_pro.services.router_utils import extract_client_origin_from_router

GENERIC_AUTH_ERROR = "Username atau password salah"


class AuthState(rx.State):
    # State Transisi Kartu (Welcome -> Form) & LocalStorage
    seen_welcome: str = rx.LocalStorage("false", name="seen_welcome")
    form_opened: bool = False

    # State Input Form
    username: str = ""
    password: str = ""
    remember_me: bool = False
    show_password: bool = False

    # State UI Feedback
    is_loading: bool = False
    error_message: str = ""

    # State Sesi Pengguna
    is_authenticated: bool = False
    access_token: str = ""
    current_user: dict[str, Any] = {}

    @rx.var(cache=True)
    def is_form_state(self) -> bool:
        """Bernilai True jika sudah pernah melihat welcome atau tombol Masuk diklik."""
        return self.form_opened or self.seen_welcome == "true"

    @rx.var(cache=True)
    def user_display_name(self) -> str:
        """Nama lengkap pengguna untuk ditampilkan di Topbar."""
        name = self.current_user.get("full_name")
        return str(name) if name else "Admin IT"

    @rx.var(cache=True)
    def user_username(self) -> str:
        """Username login asli pengguna (read-only pada Pengaturan Akun)."""
        uname = self.current_user.get("username")
        return str(uname) if uname else "admin"

    @rx.var(cache=True)
    def user_status_label(self) -> str:
        """Status aktif akun pengguna saat ini."""
        return "Aktif" if self.current_user.get("is_active", True) else "Nonaktif"

    @rx.var(cache=True)
    def user_role_label(self) -> str:
        """Nama role pengguna untuk ditampilkan di Topbar."""
        role = self.current_user.get("role")
        return str(role) if role else "Administrator"

    @rx.var(cache=True)
    def is_admin(self) -> bool:
        """Bernilai True hanya untuk peran Administrator."""
        return self.user_role_label.strip().lower() == "administrator"

    @rx.var(cache=True)
    def user_initials(self) -> str:
        """Inisial 2 huruf dari nama lengkap pengguna untuk Avatar bulat."""
        parts = [p for p in self.user_display_name.strip().split() if p]
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return "AI"

    def _sync_client_origin(self) -> None:
        client_ip, client_ua = extract_client_origin_from_router(self.router)
        api_client.set_client_origin(client_ip, client_ua)

    @rx.event
    def check_auth(self) -> Any:
        """Guard halaman terproteksi: arahkan ke /login jika belum autentikasi."""
        self._sync_client_origin()
        if not self.is_authenticated:
            return rx.redirect("/login")
        if self.access_token and api_client.token != self.access_token:
            api_client.set_token(self.access_token)

    @rx.event
    def require_admin(self) -> Any:
        """Guard khusus halaman Administrator (seperti /audit-log)."""
        self._sync_client_origin()
        if not self.is_authenticated:
            return rx.redirect("/login")
        if not self.is_admin:
            return [
                rx.toast.error(
                    "Halaman Audit Log hanya dapat diakses oleh Administrator.",
                    position="top-right",
                ),
                rx.redirect("/dashboard"),
            ]

    @rx.event
    def redirect_from_root(self) -> Any:
        """Route '/': ke /dashboard jika sudah login, selain itu ke /login."""
        if self.is_authenticated:
            return rx.redirect("/dashboard")
        return rx.redirect("/login")

    @rx.event
    def logout(self) -> Any:
        """Reset sesi pengguna dan kembali ke halaman /login."""
        api_client.clear_token()
        self.is_authenticated = False
        self.access_token = ""
        self.current_user = {}
        self.username = ""
        self.password = ""
        self.error_message = ""
        return rx.redirect("/login")

    @rx.event
    async def open_login_form(self) -> AsyncGenerator[Any, None]:
        """Transisi dari state welcome ke state form + fokus ke Username."""
        self.form_opened = True
        self.seen_welcome = "true"
        yield
        await asyncio.sleep(0.05)
        yield rx.set_focus("login-username-input")

    @rx.event
    def reset_welcome_state(self) -> None:
        """Helper jika ingin kembali melihat tampilan welcome saat klik logo."""
        self.form_opened = False
        self.seen_welcome = "false"
        self.error_message = ""

    @rx.event
    def set_username(self, value: str) -> None:
        self.username = value
        if self.error_message:
            self.error_message = ""

    @rx.event
    def set_password(self, value: str) -> None:
        self.password = value
        if self.error_message:
            self.error_message = ""

    @rx.event
    def set_remember_me(self, value: bool) -> None:
        self.remember_me = value

    @rx.event
    def toggle_password_visibility(self) -> None:
        self.show_password = not self.show_password

    @rx.event
    def handle_forgot_password(self) -> Any:
        return rx.toast.info(
            "Silakan hubungi Administrator IT untuk melakukan reset password akun Anda.",
            position="top-right",
        )

    @rx.event
    async def submit_login(self, form_data: dict[str, Any]):
        """Handler saat tombol Masuk pada form ditekan."""
        username_val = form_data.get("username") or self.username
        password_val = form_data.get("password") or self.password

        if not str(username_val).strip() or not password_val:
            self.error_message = GENERIC_AUTH_ERROR
            return

        self.is_loading = True
        self.error_message = ""
        yield

        self._sync_client_origin()
        try:
            auth_data = await api_client.login(
                username=str(username_val).strip(),
                password=str(password_val),
                remember_me=self.remember_me,
            )
            self.access_token = auth_data["access_token"]
            self.current_user = auth_data["user"]
            api_client.set_token(self.access_token)
            self.is_authenticated = True
            self.password = ""
            self.is_loading = False
            yield rx.redirect("/dashboard")
        except ServiceUnavailableError as exc:
            self.error_message = str(exc)
            self.is_loading = False
        except AuthenticationError as exc:
            self.error_message = str(exc) if str(exc) else GENERIC_AUTH_ERROR
            self.is_loading = False
        except Exception as exc:
            self.error_message = str(exc) if str(exc) else GENERIC_AUTH_ERROR
            self.is_loading = False
