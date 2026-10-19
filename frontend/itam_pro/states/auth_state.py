"""
State Autentikasi ITAM Pro.
Mengelola state welcome/form kartu login, LocalStorage seen_welcome, dan sesi pengguna.
"""
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import reflex as rx

from itam_pro.services.api_client import AuthenticationError, api_client

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

    @rx.var
    def is_form_state(self) -> bool:
        """Bernilai True jika sudah pernah melihat welcome atau tombol Masuk diklik."""
        return self.form_opened or self.seen_welcome == "true"

    @rx.event
    async def open_login_form(self) -> AsyncGenerator[Any, None]:
        """Transisi dari state welcome ke state form + fokus ke Username."""
        self.form_opened = True
        self.seen_welcome = "true"
        yield
        await asyncio.sleep(0.35)
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

        try:
            auth_data = await api_client.login(
                username=str(username_val).strip(),
                password=str(password_val),
                remember_me=self.remember_me,
            )
            self.access_token = auth_data["access_token"]
            self.current_user = auth_data["user"]
            self.is_authenticated = True
            self.password = ""
            self.is_loading = False
            yield rx.toast.success(
                f"Selamat datang, {self.current_user.get('full_name', username_val)}!",
                position="top-right",
            )
        except AuthenticationError:
            self.error_message = GENERIC_AUTH_ERROR
            self.is_loading = False
        except Exception:
            self.error_message = GENERIC_AUTH_ERROR
            self.is_loading = False
