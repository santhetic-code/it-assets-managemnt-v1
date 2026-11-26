"""Halaman Admin -> Pengaturan Akun (/account-settings)."""

from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables import ColumnDef, reusable_data_table
from itam_pro.components.ui.badge import app_badge
from itam_pro.components.ui.button import action_primary_button, secondary_button
from itam_pro.components.ui.tabs import app_tabs
from itam_pro.states.account_state import AccountState
from itam_pro.states.auth_state import AuthState
from itam_pro.styles import (
    FONT_FAMILY,
    Color,
    FontSize,
    FontWeight,
    Radius,
    Shadow,
    Size,
    Space,
)

USER_COLUMNS: list[ColumnDef] = [
    {"key": "full_name", "header": "Nama Lengkap", "width": "220px", "render_type": "bold"},
    {"key": "username", "header": "Username", "width": "150px", "render_type": "text"},
    {
        "key": "role",
        "header": "Peran",
        "width": "150px",
        "render_type": "badge",
        "badge_variant_key": "role_variant",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "130px",
        "render_type": "badge",
        "badge_variant_key": "status_variant",
    },
]

_CARD_STYLE = rx.Style(
    {
        "background_color": Color.SURFACE,
        "border": f"1px solid {Color.BORDER}",
        "border_radius": Radius.CARD,
        "padding": Space.S6,
        "width": "100%",
    }
)

_TWO_COL_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "repeat(2, minmax(0, 1fr))",
        "gap": Space.S4,
        "align_items": "start",
        "@media (max-width: 899px)": {
            "grid_template_columns": "1fr",
        },
    }
)


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


def _readonly_input_style() -> rx.Style:
    return rx.Style(
        {
            "width": "100%",
            "height": Size.FILTER_CONTROL_H,
            "padding": "0 12px",
            "background_color": Color.SLATE_100,
            "color": Color.MUTED,
            "border": f"1px solid {Color.BORDER}",
            "border_radius": Radius.CONTROL,
            "font_family": FONT_FAMILY,
            "font_size": FontSize.SM,
            "cursor": "not-allowed",
        }
    )


def _password_input_with_toggle(
    value: Any,
    on_change: Any,
    is_visible: Any,
    on_toggle: Any,
    aria_label: str,
) -> rx.Component:
    return rx.box(
        rx.el.input(
            type=rx.cond(is_visible, "text", "password"),
            value=value,
            on_change=on_change,
            aria_label=aria_label,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 40px 0 12px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "box_sizing": "border-box",
                }
            ),
        ),
        rx.el.button(
            rx.cond(
                is_visible,
                rx.icon(tag="eye-off", size=16, color=Color.MUTED),
                rx.icon(tag="eye", size=16, color=Color.MUTED),
            ),
            type="button",
            aria_label=f"Tampilkan atau sembunyikan {aria_label}",
            on_click=on_toggle,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "6px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "width": "30px",
                    "height": "30px",
                    "background": "transparent",
                    "border": "none",
                    "cursor": "pointer",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "width": "100%"}),
    )


def _strength_segment(threshold: int) -> rx.Component:
    bar_color = rx.cond(
        AccountState.pwd_strength_score >= threshold,
        rx.match(
            AccountState.pwd_strength_score,
            (1, Color.DANGER_BAR),
            (2, Color.WARNING_BAR),
            (3, Color.ACCENT_BRIGHT),
            Color.SUCCESS_FG,
        ),
        Color.PROGRESS_TRACK,
    )
    return rx.box(
        style=rx.Style(
            {
                "flex": "1",
                "height": "6px",
                "border_radius": Radius.FULL,
                "background_color": bar_color,
                "transition": "background-color 0.2s ease",
            }
        )
    )


def _pwd_rule_row(label: str, passed: Any, counter_text: Any = None) -> rx.Component:
    right_elem = (
        rx.cond(
            passed,
            rx.text(
                "✓",
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.SUCCESS_FG,
            ),
            rx.text(
                counter_text,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=rx.cond(AccountState.new_password == "", Color.MUTED, Color.DANGER_FG),
                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
            ),
        )
        if counter_text is not None
        else rx.cond(
            AccountState.new_password == "",
            rx.text("—", font_size=FontSize.XS, color=Color.MUTED),
            rx.cond(
                passed,
                rx.text(
                    "✓",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.SUCCESS_FG,
                ),
                rx.text(
                    "✕",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.DANGER_FG,
                ),
            ),
        )
    )
    return rx.hstack(
        rx.text(label, font_size=FontSize.SM, color=Color.TEXT),
        right_elem,
        width="100%",
        justify="between",
        align="center",
    )


def _session_item_row(sess: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(
                    sess["device"],
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                rx.cond(
                    sess["is_current"],
                    app_badge(label="Sesi ini", variant="success"),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                f"IP {sess['ip_address']} · {sess['last_active']}",
                font_size=FontSize.XS,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.text("—", font_size=FontSize.SM, color=Color.MUTED),
        width="100%",
        justify="between",
        align="center",
        padding_y="10px",
        style=rx.Style({"border_top": f"1px solid {Color.DIVIDER}"}),
    )


def _active_sessions_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Sesi Aktif",
                    font_size=FontSize.SUBTITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                secondary_button(
                    "Keluarkan semua sesi lain",
                    on_click=AccountState.revoke_other_sessions,
                ),
                width="100%",
                justify="between",
                align="center",
                wrap="wrap",
                spacing="2",
            ),
            rx.cond(
                AccountState.session_msg != "",
                rx.text(
                    AccountState.session_msg,
                    font_size=FontSize.XS,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.SUCCESS_FG,
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.foreach(AccountState.active_sessions, _session_item_row),
                spacing="0",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        style=_CARD_STYLE,
    )


def _recent_activities_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Aktivitas Akun Terbaru",
                font_size=FontSize.SUBTITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
            ),
            rx.cond(
                AccountState.has_recent_account_activities,
                rx.vstack(
                    rx.foreach(
                        AccountState.recent_account_activities,
                        lambda act: rx.hstack(
                            rx.text(
                                act["label"],
                                font_size=FontSize.SM,
                                font_weight=FontWeight.MEDIUM,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                act["waktu"],
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
                            ),
                            width="100%",
                            justify="between",
                            align="center",
                            padding_y="10px",
                            style=rx.Style({"border_top": f"1px solid {Color.DIVIDER}"}),
                        ),
                    ),
                    spacing="0",
                    width="100%",
                ),
                rx.text(
                    "Belum ada aktivitas akun tercatat.",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
            ),
            rx.cond(
                AuthState.is_admin,
                rx.link(
                    "Lihat di Audit Log →",
                    href="/audit-log",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT,
                    underline="hover",
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        style=_CARD_STYLE,
    )


def _akun_saya_tab() -> rx.Component:
    profile_card = rx.box(
        rx.vstack(
            # Header Profil: Avatar inisial + Nama + Badge peran & Aktif + Login terakhir
            rx.hstack(
                rx.center(
                    rx.text(
                        AuthState.user_initials,
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.WHITE,
                    ),
                    width="56px",
                    height="56px",
                    border_radius=Radius.FULL,
                    flex_shrink="0",
                    style=rx.Style(
                        {
                            "background": Color.GRADIENT_BLUE,
                            "box_shadow": Shadow.AVATAR,
                        }
                    ),
                ),
                rx.vstack(
                    rx.heading(
                        AuthState.user_display_name,
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                        line_height="1.2",
                    ),
                    rx.hstack(
                        app_badge(label=AuthState.user_role_label, variant="info"),
                        app_badge(label=AuthState.user_status_label, variant="success"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        f"Login terakhir {AccountState.last_login_display}",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="center",
                width="100%",
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
            rx.vstack(
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
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                rx.text(
                    "Username",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                rx.el.input(
                    type="text",
                    value=AuthState.user_username,
                    read_only=True,
                    disabled=True,
                    style=_readonly_input_style(),
                ),
                rx.text(
                    "Username tidak dapat diubah. Peran diatur oleh Administrator.",
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            action_primary_button("Simpan Profil", on_click=AccountState.save_profile),
            spacing="4",
            align="start",
            width="100%",
        ),
        style=_CARD_STYLE,
    )

    password_card = rx.box(
        rx.vstack(
            rx.heading(
                "Ganti Password",
                font_size=FontSize.SUBTITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
            ),
            rx.cond(
                AccountState.pwd_error != "",
                rx.text(AccountState.pwd_error, color=Color.DANGER_FG, font_size=FontSize.SM),
            ),
            rx.cond(
                AccountState.pwd_msg != "",
                rx.text(AccountState.pwd_msg, color=Color.SUCCESS_FG, font_size=FontSize.SM),
            ),
            rx.vstack(
                rx.text(
                    "Password Saat Ini",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                _password_input_with_toggle(
                    value=AccountState.current_password,
                    on_change=AccountState.set_current_password,
                    is_visible=AccountState.show_current_password,
                    on_toggle=AccountState.toggle_show_current_password,
                    aria_label="Password Saat Ini",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                rx.text(
                    "Password Baru",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                _password_input_with_toggle(
                    value=AccountState.new_password,
                    on_change=AccountState.set_new_password,
                    is_visible=AccountState.show_new_password,
                    on_toggle=AccountState.toggle_show_new_password,
                    aria_label="Password Baru",
                ),
                # Meter kekuatan 4 segmen
                rx.hstack(
                    _strength_segment(1),
                    _strength_segment(2),
                    _strength_segment(3),
                    _strength_segment(4),
                    spacing="2",
                    width="100%",
                    padding_top="4px",
                ),
                rx.cond(
                    AccountState.pwd_strength_label != "",
                    rx.text(
                        AccountState.pwd_strength_label,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.MEDIUM,
                        color=Color.MUTED,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                rx.text(
                    "Ulangi Password Baru",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.TEXT,
                ),
                _password_input_with_toggle(
                    value=AccountState.confirm_password,
                    on_change=AccountState.set_confirm_password,
                    is_visible=AccountState.show_confirm_password,
                    on_toggle=AccountState.toggle_show_confirm_password,
                    aria_label="Ulangi Password Baru",
                ),
                rx.cond(
                    AccountState.pwd_confirm_mismatch,
                    rx.text(
                        "Konfirmasi password baru tidak cocok.",
                        font_size=FontSize.XS,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.DANGER_FG,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            # Daftar syarat live (4 aturan wajib)
            rx.vstack(
                _pwd_rule_row(
                    "Minimal 12 karakter",
                    AccountState.pwd_rule_min_len,
                    counter_text=AccountState.pwd_len_counter,
                ),
                _pwd_rule_row("Tidak memuat username", AccountState.pwd_rule_no_username),
                _pwd_rule_row("Bukan password umum", AccountState.pwd_rule_not_common),
                _pwd_rule_row("Berbeda dari password lama", AccountState.pwd_rule_diff_from_old),
                spacing="2",
                width="100%",
                padding="12px 14px",
                style=rx.Style(
                    {
                        "background_color": Color.TABLE_HEADER_BG,
                        "border": f"1px solid {Color.DIVIDER}",
                        "border_radius": Radius.CONTROL,
                    }
                ),
            ),
            rx.el.button(
                "Perbarui Password",
                type="button",
                disabled=~AccountState.can_submit_password,
                on_click=AccountState.submit_change_password,
                style=rx.Style(
                    {
                        "height": Size.BUTTON_MD_H,
                        "padding": "0 18px",
                        "background_color": rx.cond(
                            AccountState.can_submit_password, Color.ACCENT, Color.SLATE_200
                        ),
                        "color": rx.cond(
                            AccountState.can_submit_password, Color.WHITE, Color.MUTED
                        ),
                        "border": "none",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": rx.cond(
                            AccountState.can_submit_password, "pointer", "not-allowed"
                        ),
                    }
                ),
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        style=_CARD_STYLE,
    )

    return rx.box(
        rx.vstack(profile_card, _active_sessions_card(), spacing="4", width="100%"),
        rx.vstack(password_card, _recent_activities_card(), spacing="4", width="100%"),
        style=_TWO_COL_STYLE,
    )


def _add_user_modal() -> rx.Component:
    return rx.cond(
        AccountState.is_add_user_modal_open,
        rx.box(
            rx.box(
                on_click=AccountState.close_add_user_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Tambah Pengguna Baru",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Password sementara berlaku 72 jam dan wajib diganti saat login pertama.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.cond(
                        AccountState.user_form_error != "",
                        rx.text(
                            AccountState.user_form_error,
                            color=Color.DANGER_FG,
                            font_size=FontSize.SM,
                        ),
                    ),
                    rx.text(
                        "Nama Lengkap *",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                    ),
                    rx.el.input(
                        value=AccountState.new_user_fullname,
                        on_change=AccountState.set_new_user_fullname,
                        style=_input_style(),
                    ),
                    rx.text(
                        "Username (3-32 karakter) *",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                    ),
                    rx.el.input(
                        value=AccountState.new_user_username,
                        on_change=AccountState.set_new_user_username,
                        style=_input_style(),
                    ),
                    rx.text(
                        "Peran Sistem",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                    ),
                    rx.el.select(
                        rx.el.option("Administrator", value="Administrator"),
                        rx.el.option("Member", value="Member"),
                        rx.el.option("Viewer", value="Viewer"),
                        value=AccountState.new_user_role,
                        on_change=AccountState.set_new_user_role,
                        style=_input_style(),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AccountState.close_add_user_modal),
                        action_primary_button(
                            "Buat Pengguna", on_click=AccountState.create_new_user
                        ),
                        width="100%",
                        justify="end",
                        spacing="2",
                        padding_top="6px",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "92%",
                        "max_width": "460px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": Space.S6,
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _manajemen_pengguna_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            AccountState.generated_temp_password != "",
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            f"Password Sementara (Tampil Sekali): "
                            f"{AccountState.generated_temp_password}",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.BOLD,
                            color=Color.WARNING_FG,
                        ),
                        rx.text(
                            "Berlaku 72 jam · Wajib diganti saat login pertama.",
                            font_size=FontSize.XS,
                            color=Color.WARNING_FG,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    secondary_button(
                        "Salin & Tutup",
                        on_click=[
                            rx.set_clipboard(AccountState.generated_temp_password),
                            AccountState.close_temp_password_modal,
                        ],
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    wrap="wrap",
                    spacing="2",
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
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Daftar Pengguna Internal",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Peran: Administrator / Member / Viewer · 5× gagal login mengunci "
                        "akun 15 menit · Administrator aktif terakhir tidak dapat dinonaktifkan.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    spacing="1",
                    align="start",
                ),
                action_primary_button(
                    "+ Tambah Pengguna", on_click=AccountState.open_add_user_modal
                ),
                width="100%",
                justify="between",
                align="center",
                wrap="wrap",
                padding="16px 20px",
                style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
            ),
            rx.cond(
                AccountState.user_form_error != "",
                rx.box(
                    rx.text(
                        AccountState.user_form_error,
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.DANGER_FG,
                    ),
                    padding="10px 20px",
                    background_color=Color.DANGER_BG,
                    border_bottom=f"1px solid {Color.DANGER_BORDER}",
                ),
            ),
            rx.cond(
                AccountState.user_action_msg != "",
                rx.box(
                    rx.text(
                        AccountState.user_action_msg,
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.SUCCESS_FG,
                    ),
                    padding="10px 20px",
                    background_color=Color.SUCCESS_BG,
                    border_bottom=f"1px solid {Color.BORDER}",
                ),
            ),
            reusable_data_table(
                columns=USER_COLUMNS,
                rows=AccountState.users_list,
                id_key="username",
                on_duplicate_row=AccountState.toggle_user_status,
                duplicate_action_label="Aktifkan / Nonaktifkan",
                show_action_header=True,
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
        _add_user_modal(),
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
                    "Kelola profil pribadi, keamanan login, dan sesi aktif Anda.",
                    font_size=FontSize.BASE,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.cond(
                AuthState.is_admin,
                app_tabs(
                    items=[
                        {"label": "Akun Saya", "value": "akun"},
                        {"label": "Manajemen Pengguna", "value": "pengguna"},
                    ],
                    active_value=AccountState.active_tab,
                    on_change=AccountState.set_tab,
                ),
                app_tabs(
                    items=[{"label": "Akun Saya", "value": "akun"}],
                    active_value="akun",
                    on_change=AccountState.set_tab,
                ),
            ),
            rx.cond(
                AuthState.is_admin & (AccountState.active_tab == "pengguna"),
                _manajemen_pengguna_tab(),
                _akun_saya_tab(),
            ),
            spacing="4",
            width="100%",
        ),
        breadcrumb=("Admin", "Pengaturan Akun"),
    )


__all__ = ["account_settings_page"]
