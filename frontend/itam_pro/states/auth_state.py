"""
State Autentikasi ITAM Pro.
Mengelola form login, visibilitas password, loading state, dan sesi pengguna.
"""
from typing import Any

import reflex as rx

from itam_pro.services.api_client import AuthenticationError, api_client

GENERIC_AUTH_ERROR = "Username atau password salah"


class AuthState(rx.State):
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
        """Handler saat tombol Masuk ditekan."""
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
            # Nanti diarahkan ke rx.redirect("/dashboard") setelah halaman dashboard siap
        except AuthenticationError:
            self.error_message = GENERIC_AUTH_ERROR
            self.is_loading = False
        except Exception:
            self.error_message = GENERIC_AUTH_ERROR
            self.is_loading = False
