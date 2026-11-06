"""Halaman Admin -> Pengaturan Akun (/account-settings)."""

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables import ColumnDef, reusable_data_table
from itam_pro.components.ui.tabs import app_tabs
from itam_pro.states.account_state import AccountState
from itam_pro.states.auth_state import AuthState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size

USER_COLUMNS: list[ColumnDef] = [
    {"key": "full_name", "header": "Nama Lengkap", "width": "220px", "render_type": "bold"},
    {"key": "username", "header": "Username", "width": "160px", "render_type": "text"},
    {"key": "role", "header": "Peran", "width": "150px", "render_type": "chip"},
    {"key": "status", "header": "Status", "width": "130px", "render_type": "status_badge"},
]


def _input_style() -> rx.Style:
    return rx.Style(
        {
            "width": "100%",
            "height": Size.FILTER_CONTROL_H,
            "padding": "0 12px",
            "background_color": Color.SURFACE,
            "color": Color.TEXT,
            "border": f"1px solid {Color.INPUT_BORDER}",
            "border_radius": Radius.CONTROL,
            "font_family": FONT_FAMILY,
            "font_size": FontSize.SM,
        }
    )


def _akun_saya_tab() -> rx.Component:
    return rx.grid(
        # Kartu Profil
        rx.box(
            rx.vstack(
                rx.heading("Profil Akun Saya", font_size=FontSize.SUBTITLE, color=Color.TEXT),
                rx.text(
                    "Informasi identitas dan peran akses Anda.",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
                rx.cond(
                    AccountState.profile_error != "",
                    rx.text(
                        AccountState.profile_error,
                        color=Color.DANGER_FG,
                        font_size=FontSize.SM,
                    ),
                ),
                rx.cond(
                    AccountState.profile_msg != "",
                    rx.text(
                        AccountState.profile_msg,
                        color=Color.SUCCESS_FG,
                        font_size=FontSize.SM,
                    ),
                ),
                rx.text(
                    "Username",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.text(
                    AuthState.user_display_name,
                    font_size=FontSize.BASE,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    "Peran Sistem",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.text(AuthState.user_role_label, font_size=FontSize.SM, color=Color.ACCENT),
                rx.text(
                    "Nama Lengkap",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                rx.el.input(
                    type="text",
                    value=AccountState.full_name_input,
                    on_change=AccountState.set_full_name_input,
                    style=_input_style(),
                ),
                rx.el.button(
                    "Simpan Profil",
                    type="button",
                    on_click=AccountState.save_profile,
                    style=rx.Style(
                        {
                            "height": Size.BUTTON_MD_H,
                            "padding": "0 18px",
                            "background_color": Color.ACCENT,
                            "color": Color.WHITE,
                            "border": "none",
                            "border_radius": Radius.CONTROL,
                            "font_weight": FontWeight.BOLD,
                            "cursor": "pointer",
                        }
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            padding="24px",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        # Kartu Ganti Password
        rx.box(
            rx.vstack(
                rx.heading("Ganti Password", font_size=FontSize.SUBTITLE, color=Color.TEXT),
                rx.text(
                    "Minimal 12 karakter, tidak memuat username, dan bukan password umum.",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
                rx.cond(
                    AccountState.pwd_error != "",
                    rx.text(AccountState.pwd_error, color=Color.DANGER_FG, font_size=FontSize.SM),
                ),
                rx.cond(
                    AccountState.pwd_msg != "",
                    rx.text(AccountState.pwd_msg, color=Color.SUCCESS_FG, font_size=FontSize.SM),
                ),
                rx.text(
                    "Password Saat Ini",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                rx.el.input(
                    type="password",
                    value=AccountState.current_password,
                    on_change=AccountState.set_current_password,
                    style=_input_style(),
                ),
                rx.text(
                    "Password Baru (12-128 karakter)",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                rx.el.input(
                    type="password",
                    value=AccountState.new_password,
                    on_change=AccountState.set_new_password,
                    style=_input_style(),
                ),
                rx.text(
                    "Ulangi Password Baru",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                rx.el.input(
                    type="password",
                    value=AccountState.confirm_password,
                    on_change=AccountState.set_confirm_password,
                    style=_input_style(),
                ),
                rx.el.button(
                    "Perbarui Password",
                    type="button",
                    on_click=AccountState.submit_change_password,
                    style=rx.Style(
                        {
                            "height": Size.BUTTON_MD_H,
                            "padding": "0 18px",
                            "background_color": Color.ACCENT,
                            "color": Color.WHITE,
                            "border": "none",
                            "border_radius": Radius.CONTROL,
                            "font_weight": FontWeight.BOLD,
                            "cursor": "pointer",
                        }
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            padding="24px",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        columns="2",
        spacing="4",
        width="100%",
    )


def _manajemen_pengguna_tab() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading("Tambah Pengguna Baru", font_size=FontSize.SUBTITLE, color=Color.TEXT),
                rx.cond(
                    AccountState.user_form_error != "",
                    rx.text(
                        AccountState.user_form_error,
                        color=Color.DANGER_FG,
                        font_size=FontSize.SM,
                    ),
                ),
                rx.cond(
                    AccountState.generated_temp_password != "",
                    rx.box(
                        rx.hstack(
                            rx.text(
                                f"Password Sementara (Tampil Sekali): "
                                f"{AccountState.generated_temp_password}",
                                font_weight=FontWeight.BOLD,
                                color=Color.WARNING_FG,
                            ),
                            rx.el.button(
                                "Salin & Tutup",
                                type="button",
                                on_click=[
                                    rx.set_clipboard(AccountState.generated_temp_password),
                                    AccountState.close_temp_password_modal,
                                ],
                                style=rx.Style(
                                    {
                                        "padding": "4px 12px",
                                        "background_color": Color.SURFACE,
                                        "border": f"1px solid {Color.WARNING_FG}",
                                        "border_radius": Radius.CONTROL,
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            justify="between",
                            width="100%",
                        ),
                        padding="12px 16px",
                        width="100%",
                        style=rx.Style(
                            {
                                "background_color": Color.WARNING_BG,
                                "border": f"1px solid {Color.WARNING_BAR}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                ),
                rx.grid(
                    rx.el.input(
                        placeholder="Nama Lengkap",
                        value=AccountState.new_user_fullname,
                        on_change=AccountState.set_new_user_fullname,
                        style=_input_style(),
                    ),
                    rx.el.input(
                        placeholder="Username (3-32 karakter)",
                        value=AccountState.new_user_username,
                        on_change=AccountState.set_new_user_username,
                        style=_input_style(),
                    ),
                    rx.el.select(
                        rx.el.option("Administrator", value="Administrator"),
                        rx.el.option("Member", value="Member"),
                        rx.el.option("Viewer", value="Viewer"),
                        value=AccountState.new_user_role,
                        on_change=AccountState.set_new_user_role,
                        style=_input_style(),
                    ),
                    rx.el.button(
                        "+ Buat Pengguna",
                        type="button",
                        on_click=AccountState.create_new_user,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "background_color": Color.ACCENT,
                                "color": Color.WHITE,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    columns="4",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            padding="20px",
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        rx.box(
            reusable_data_table(
                columns=USER_COLUMNS,
                rows=AccountState.users_list,
                id_key="id",
                show_action_header=False,
            ),
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                    "overflow": "hidden",
                }
            ),
        ),
        spacing="4",
        width="100%",
    )


def account_settings_page() -> rx.Component:
    return base_layout(
        content=rx.vstack(
            rx.vstack(
                rx.heading(
                    "Pengaturan Akun",
                    font_size=FontSize.TITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    "Kelola profil pribadi, pembaruan password, dan akun pengguna internal.",
                    font_size=FontSize.BASE,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            app_tabs(
                items=[
                    {"label": "Akun Saya", "value": "akun"},
                    {"label": "Manajemen Pengguna", "value": "pengguna"},
                ],
                active_value=AccountState.active_tab,
                on_change=AccountState.set_tab,
            ),
            rx.cond(
                AccountState.active_tab == "pengguna",
                _manajemen_pengguna_tab(),
                _akun_saya_tab(),
            ),
            spacing="4",
            width="100%",
        ),
        breadcrumb=("Admin", "Pengaturan Akun"),
    )


__all__ = ["account_settings_page"]
