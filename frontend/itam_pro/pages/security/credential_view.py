"""
Halaman Credential Manager ITAM Pro (Tahap 12).
Brankas penyimpanan kredensial terenkripsi dengan proteksi reveal timer 30 detik.
"""

from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.pagination import table_pagination
from itam_pro.states.credential_state import CredentialState
from itam_pro.styles import Color, FontSize, FontWeight, Radius


def _credential_header() -> rx.Component:
    """E: Header Artboard 7 dengan ikon gembok, chip Akses Anda, & tombol aksi."""
    return rx.hstack(
        rx.hstack(
            rx.center(
                rx.icon(tag="lock", size=24, color=Color.WHITE, stroke_width=2),
                width="52px",
                height="52px",
                border_radius="15px",
                flex_shrink="0",
                style=rx.Style(
                    {
                        "background": Color.GRADIENT_BLUE,
                        "box_shadow": "0 6px 16px rgba(37, 99, 235, 0.24)",
                    }
                ),
            ),
            rx.vstack(
                rx.heading(
                    "Credential Manager",
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.15",
                ),
                rx.text(
                    (
                        "Brankas kredensial terenkripsi. Akses dibatasi menurut "
                        "jenis, tingkat posisi, dan divisi."
                    ),
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
        ),
        rx.hstack(
            # Chip Akses Anda: <peran> · N dari 8 jenis
            rx.hstack(
                rx.icon(tag="shield", size=15, color=Color.BLUE_700),
                rx.text(
                    CredentialState.access_badge_text,
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.BLUE_700,
                ),
                spacing="2",
                align="center",
                padding="8px 14px",
                border_radius=Radius.FULL,
                background_color=Color.BLUE_50,
                border=f"1px solid {Color.BLUE_BORDER}",
            ),
            rx.el.button(
                "Aturan Akses",
                type="button",
                on_click=CredentialState.open_rules_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 18px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "11px",
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "color": Color.TEXT,
                        "cursor": "pointer",
                    }
                ),
            ),
            rx.el.button(
                "+ Tambah Kredensial",
                type="button",
                on_click=CredentialState.open_add_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 20px",
                        "background": Color.GRADIENT_PRIMARY,
                        "color": Color.WHITE,
                        "border": "none",
                        "border_radius": "11px",
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "box_shadow": "0 6px 16px rgba(29, 78, 216, 0.25)",
                    }
                ),
            ),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        margin_bottom="18px",
    )


def _kpi_cards() -> rx.Component:
    """E: 4 Kartu Ringkasan Interaktif (Artboard 7)."""
    is_all = CredentialState.active_kpi_card == "all"
    is_exp = CredentialState.active_kpi_card == "expiring"
    is_old = CredentialState.active_kpi_card == "old_password"

    def _white_card(
        key: str,
        title: str,
        icon_tag: str,
        icon_bg: str,
        icon_fg: str,
        val_var: Any,
        sub_text: str,
        action_text: str,
        active_cond: Any,
    ) -> rx.Component:
        return rx.el.button(
            rx.vstack(
                rx.hstack(
                    rx.center(
                        rx.icon(tag=icon_tag, size=16, color=icon_fg),
                        width="32px",
                        height="32px",
                        border_radius="9px",
                        background_color=icon_bg,
                    ),
                    rx.text(
                        title,
                        font_size="11px",
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    val_var,
                    font_size="32px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.1",
                    margin_top="4px",
                ),
                rx.text(sub_text, font_size=FontSize.XS, color=Color.MUTED),
                rx.text(
                    action_text,
                    font_size="12px",
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT,
                    margin_top="4px",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            type="button",
            on_click=CredentialState.click_kpi_card(key),
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": rx.cond(
                        active_cond,
                        f"2px solid {Color.ACCENT}",
                        f"1px solid {Color.BORDER}",
                    ),
                    "border_radius": "16px",
                    "padding": "18px 20px",
                    "text_align": "left",
                    "cursor": "pointer",
                    "width": "100%",
                    "transition": "all 0.15s ease",
                }
            ),
        )

    return rx.box(
        # 1. Kartu Hero Navy: BISA ANDA AKSES
        rx.el.button(
            rx.vstack(
                rx.hstack(
                    rx.center(
                        rx.icon(tag="key-round", size=16, color=Color.WHITE),
                        width="32px",
                        height="32px",
                        border_radius="9px",
                        style=rx.Style({"background_color": "rgba(255,255,255,0.16)"}),
                    ),
                    rx.text(
                        "BISA ANDA AKSES",
                        font_size="11px",
                        font_weight=FontWeight.BOLD,
                        color="rgba(255,255,255,0.85)",
                        letter_spacing="0.06em",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    CredentialState.kpi_bisa_diakses,
                    font_size="34px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.WHITE,
                    line_height="1.1",
                    margin_top="4px",
                ),
                rx.text(
                    f"dari {CredentialState.kpi_unlocked_types} jenis kredensial",
                    font_size=FontSize.XS,
                    color="rgba(255,255,255,0.8)",
                ),
                rx.text(
                    "Lihat semua ->",
                    font_size="12px",
                    font_weight=FontWeight.BOLD,
                    color=Color.WHITE,
                    margin_top="4px",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            type="button",
            on_click=CredentialState.click_kpi_card("all"),
            style=rx.Style(
                {
                    "background": Color.GRADIENT_NAVY,
                    "border": rx.cond(
                        is_all, f"2px solid {Color.CHART_MONITOR}", "1px solid transparent"
                    ),
                    "border_radius": "16px",
                    "padding": "18px 20px",
                    "text_align": "left",
                    "cursor": "pointer",
                    "width": "100%",
                }
            ),
        ),
        _white_card(
            "expiring",
            "SEGERA KEDALUWARSA",
            "clock",
            Color.AMBER_100,
            Color.AMBER_600,
            CredentialState.kpi_segera_kedaluwarsa,
            "Domain/hosting <= 30 hari",
            "Lihat daftar ->",
            is_exp,
        ),
        _white_card(
            "old_password",
            "PASSWORD LAMA",
            "key",
            Color.RED_100,
            Color.RED_600,
            CredentialState.kpi_password_lama,
            "Belum diganti > 90 hari",
            "Lihat daftar ->",
            is_old,
        ),
        _white_card(
            "revealed_today",
            "DIBUKA HARI INI",
            "eye",
            Color.SKY_100,
            Color.SKY_600,
            CredentialState.kpi_dibuka_hari_ini,
            "kali password ditampilkan",
            "Buka Audit Log ->",
            False,
        ),
        style=rx.Style(
            {
                "display": "grid",
                "grid_template_columns": "repeat(4, minmax(0, 1fr))",
                "gap": "16px",
                "width": "100%",
                "margin_bottom": "18px",
                "@media (max-width: 1024px)": {"grid_template_columns": "repeat(2, 1fr)"},
                "@media (max-width: 600px)": {"grid_template_columns": "1fr"},
            }
        ),
    )


def _type_tiles_row() -> rx.Component:
    """E: Baris jenis 'Semua' + 8 jenis (jenis tanpa izin Lapis 1 tampil 'Terkunci')."""
    is_all_active = CredentialState.active_type_code == "all"

    def _render_tile(tile: dict[str, Any]) -> rx.Component:
        kode = tile["kode"].to(str)
        locked = tile["locked"] == True  # noqa: E712
        is_active = CredentialState.active_type_code == kode
        return rx.el.button(
            rx.hstack(
                rx.center(
                    rx.icon(
                        tag=rx.cond(locked, "lock", tile["ikon"].to(str)),
                        size=16,
                        color=rx.cond(locked, Color.MUTED, Color.ACCENT),
                    ),
                    width="34px",
                    height="34px",
                    border_radius="10px",
                    background_color=rx.cond(locked, Color.SLATE_100, Color.BLUE_50),
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(
                        tile["nama"],
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(locked, Color.MUTED, Color.TEXT),
                        line_height="1.2",
                    ),
                    rx.text(
                        rx.cond(locked, "Terkunci", f"{tile['count']} entri"),
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            type="button",
            disabled=locked,
            on_click=CredentialState.select_type_tile(kode, locked),
            style=rx.Style(
                {
                    "padding": "12px 14px",
                    "border_radius": "14px",
                    "background_color": rx.cond(locked, Color.SLATE_50, Color.SURFACE),
                    "border": rx.cond(
                        is_active,
                        f"2px solid {Color.ACCENT}",
                        rx.cond(
                            locked,
                            f"1.5px dashed {Color.SLATE_300}",
                            f"1px solid {Color.BORDER}",
                        ),
                    ),
                    "cursor": rx.cond(locked, "not-allowed", "pointer"),
                    "opacity": rx.cond(locked, "0.65", "1"),
                    "text_align": "left",
                    "min_width": "132px",
                }
            ),
        )

    return rx.hstack(
        rx.el.button(
            rx.hstack(
                rx.center(
                    rx.icon(tag="key-round", size=16, color=Color.ACCENT),
                    width="34px",
                    height="34px",
                    border_radius="10px",
                    background_color=Color.BLUE_50,
                ),
                rx.vstack(
                    rx.text(
                        "Semua",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        f"{CredentialState.kpi_bisa_diakses} kredensial",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            type="button",
            on_click=CredentialState.select_type_tile("all", False),
            style=rx.Style(
                {
                    "padding": "12px 14px",
                    "border_radius": "14px",
                    "background_color": Color.SURFACE,
                    "border": rx.cond(
                        is_all_active,
                        f"2px solid {Color.ACCENT}",
                        f"1px solid {Color.BORDER}",
                    ),
                    "cursor": "pointer",
                    "text_align": "left",
                    "min_width": "136px",
                }
            ),
        ),
        rx.foreach(CredentialState.type_tiles, _render_tile),
        spacing="2",
        width="100%",
        overflow_x="auto",
        padding_bottom="4px",
        margin_bottom="14px",
    )


def _credential_filter_bar() -> rx.Component:
    """E: Filter bar Artboard 7 (Pencarian, Divisi, Status, Masa berlaku, Hanya divisi saya)."""
    select_style = rx.Style(
        {
            "height": "38px",
            "padding": "0 12px",
            "background_color": Color.SURFACE,
            "border": f"1px solid {Color.BORDER}",
            "border_radius": "10px",
            "font_size": FontSize.SM,
            "font_weight": FontWeight.MEDIUM,
            "color": Color.TEXT,
            "cursor": "pointer",
        }
    )
    return rx.hstack(
        rx.debounce_input(
            rx.el.input(
                placeholder="Cari nama, target, username...",
                value=CredentialState.search_query,
                on_change=CredentialState.set_search,
                style=rx.Style(
                    {
                        "width": "260px",
                        "height": "38px",
                        "padding": "0 14px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "10px",
                        "font_size": FontSize.SM,
                        "outline": "none",
                    }
                ),
            ),
            debounce_timeout=300,
        ),
        rx.el.select(
            rx.foreach(
                CredentialState.division_options,
                lambda d: rx.el.option(d, value=d),
            ),
            value=CredentialState.divisi_filter,
            on_change=CredentialState.set_divisi_filter,
            style=select_style,
        ),
        rx.el.select(
            rx.el.option("Semua status", value="Semua status"),
            rx.el.option("Aktif", value="Aktif"),
            rx.el.option("Nonaktif", value="Nonaktif"),
            rx.el.option("Kedaluwarsa", value="Kedaluwarsa"),
            value=CredentialState.status_filter,
            on_change=CredentialState.set_status_filter,
            style=select_style,
        ),
        rx.el.select(
            rx.el.option("Semua masa berlaku", value="Semua masa berlaku"),
            rx.el.option("<= 30 hari", value="<= 30 hari"),
            rx.el.option("> 90 hari (Password lama)", value="> 90 hari"),
            value=CredentialState.masa_berlaku_filter,
            on_change=CredentialState.set_masa_berlaku_filter,
            style=select_style,
        ),
        rx.hstack(
            rx.el.input(
                type="checkbox",
                checked=CredentialState.only_my_division,
                on_change=CredentialState.toggle_only_my_division,
                style=rx.Style({"cursor": "pointer", "accent_color": Color.ACCENT}),
            ),
            rx.text("Hanya divisi saya", font_size=FontSize.SM, color=Color.TEXT),
            spacing="2",
            align="center",
        ),
        rx.el.button(
            "Reset filter",
            type="button",
            on_click=CredentialState.reset_filters,
            style=rx.Style(
                {
                    "background": "transparent",
                    "border": "none",
                    "color": Color.ACCENT,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.BOLD,
                    "cursor": "pointer",
                }
            ),
        ),
        rx.spacer(),
        rx.text(
            f"{CredentialState.total_items} entri",
            font_size=FontSize.SM,
            color=Color.MUTED,
        ),
        width="100%",
        spacing="3",
        align="center",
        wrap="wrap",
        padding="14px 18px",
        style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
    )


def _password_cell(row: dict[str, Any]) -> rx.Component:
    """E & B: Kolom Password (•••••••• + ikon mata + ikon salin)."""
    crd_id = row["id"]
    can_rev = row["can_reveal"] == True  # noqa: E712
    is_row_open = (
        (CredentialState.revealed_crd_id == crd_id)
        & (CredentialState.revealed_field == "secret")
        & (CredentialState.revealed_value != "")
    )
    return rx.hstack(
        rx.cond(
            is_row_open,
            rx.text(
                CredentialState.revealed_value,
                font_family="monospace",
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.DANGER_FG,
            ),
            rx.text(
                "••••••••",
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                letter_spacing="0.12em",
            ),
        ),
        rx.cond(
            can_rev,
            rx.hstack(
                rx.el.button(
                    rx.icon(
                        tag=rx.cond(is_row_open, "eye-off", "eye"),
                        size=14,
                        color=Color.MUTED,
                    ),
                    type="button",
                    title="Tampilkan Password (30 detik)",
                    on_click=rx.cond(
                        is_row_open,
                        CredentialState.hide_revealed,
                        CredentialState.fetch_and_reveal(crd_id, "secret"),
                    ),
                    style=rx.Style(
                        {
                            "background": "transparent",
                            "border": "none",
                            "cursor": "pointer",
                            "padding": "2px",
                        }
                    ),
                ),
                rx.el.button(
                    rx.icon(tag="copy", size=14, color=Color.MUTED),
                    type="button",
                    title="Salin Password",
                    on_click=CredentialState.copy_secret(crd_id, "secret"),
                    style=rx.Style(
                        {
                            "background": "transparent",
                            "border": "none",
                            "cursor": "pointer",
                            "padding": "2px",
                        }
                    ),
                ),
                spacing="1",
                align="center",
            ),
            rx.icon(tag="eye-off", size=14, color=Color.SLATE_300),
        ),
        spacing="2",
        align="center",
    )


def _action_buttons(item: dict[str, Any]) -> rx.Component:
    """Tombol aksi pada baris tabel untuk melihat detail dan salin secret."""
    crd_id = item.get("id", "")
    has_sec = item.get("secret_ada", False)
    return rx.hstack(
        rx.button(
            rx.icon(tag="eye", size=14),
            "Detail",
            size="1",
            variant="soft",
            on_click=CredentialState.open_detail(item),
        ),
        rx.cond(
            has_sec,
            rx.button(
                rx.icon(tag="copy", size=14),
                size="1",
                variant="ghost",
                title="Salin Password",
                on_click=CredentialState.copy_secret(crd_id, "secret"),
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


def _detail_drawer() -> rx.Component:
    """Drawer detail satu entri kredensial dengan timer buka rahasia 30 detik."""
    crd = CredentialState.selected_crd
    crd_id = crd.get("id", "")
    has_secret = crd.get("secret_ada", False)
    is_revealed = (
        (CredentialState.revealed_crd_id == crd_id)
        & (CredentialState.revealed_field == "secret")
        & (CredentialState.revealed_value != "")
    )

    return rx.cond(
        CredentialState.is_detail_open,
        rx.box(
            # Backdrop scrim
            rx.box(
                on_click=CredentialState.close_detail,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            # Panel modal/drawer
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                crd.get("induk", "Detail Kredensial"),
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            rx.hstack(
                                rx.badge(
                                    crd.get("jenis_label", "Umum"),
                                    variant="soft",
                                    color_scheme="blue",
                                ),
                                rx.text(
                                    f"Peran: {crd.get('peran', '—')}",
                                    font_size=FontSize.SM,
                                    color=Color.MUTED,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                        ),
                        rx.icon(
                            tag="x",
                            size=20,
                            cursor="pointer",
                            color=Color.MUTED,
                            on_click=CredentialState.close_detail,
                        ),
                        justify="between",
                        width="100%",
                        align="start",
                    ),
                    rx.divider(color=Color.BORDER),
                    # Target / URL
                    rx.cond(
                        crd.get("target") != "",
                        rx.vstack(
                            rx.text(
                                "Target / Host / URL",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.hstack(
                                rx.text(
                                    crd.get("target", "—"),
                                    font_size=FontSize.SM,
                                    color=Color.ACCENT,
                                ),
                                rx.icon(
                                    tag="copy",
                                    size=14,
                                    cursor="pointer",
                                    color=Color.MUTED,
                                    title="Salin Target",
                                    on_click=rx.set_clipboard(crd.get("target", "")),
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Username
                    rx.cond(
                        crd.get("username") != "",
                        rx.vstack(
                            rx.text(
                                "Username / Akun",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.hstack(
                                rx.text(
                                    crd.get("username", "—"),
                                    font_size=FontSize.SM,
                                    color=Color.TEXT,
                                    font_weight=FontWeight.MEDIUM,
                                ),
                                rx.icon(
                                    tag="copy",
                                    size=14,
                                    cursor="pointer",
                                    color=Color.MUTED,
                                    title="Salin Username",
                                    on_click=rx.set_clipboard(crd.get("username", "")),
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Password / Secret Section
                    rx.vstack(
                        rx.text(
                            "Password / Secret",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.MUTED,
                        ),
                        rx.cond(
                            has_secret,
                            rx.cond(
                                is_revealed,
                                rx.box(
                                    rx.hstack(
                                        rx.text(
                                            CredentialState.revealed_value,
                                            font_size=FontSize.BASE,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.DANGER_FG,
                                            letter_spacing="0.05em",
                                        ),
                                        rx.hstack(
                                            rx.button(
                                                rx.icon(tag="copy", size=14),
                                                "Salin",
                                                size="1",
                                                variant="soft",
                                                on_click=CredentialState.copy_secret(
                                                    crd_id, "secret"
                                                ),
                                            ),
                                            rx.button(
                                                "Sembunyikan",
                                                size="1",
                                                variant="ghost",
                                                on_click=CredentialState.hide_revealed,
                                            ),
                                            spacing="2",
                                        ),
                                        justify="between",
                                        align="center",
                                        width="100%",
                                    ),
                                    rx.text(
                                        f"Otomatis disembunyikan dalam "
                                        f"{CredentialState.reveal_countdown} detik",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                        margin_top="4px",
                                    ),
                                    padding="10px 14px",
                                    background_color=Color.APP_BG,
                                    border=f"1px solid {Color.BORDER}",
                                    border_radius=Radius.CONTROL,
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.text(
                                        "••••••••",
                                        font_size=FontSize.BASE,
                                        font_weight=FontWeight.BOLD,
                                        letter_spacing="0.1em",
                                        color=Color.MUTED,
                                    ),
                                    rx.hstack(
                                        rx.button(
                                            rx.icon(tag="eye", size=14),
                                            "Buka (30s)",
                                            size="1",
                                            variant="soft",
                                            on_click=CredentialState.fetch_and_reveal(
                                                crd_id, "secret"
                                            ),
                                        ),
                                        rx.button(
                                            rx.icon(tag="copy", size=14),
                                            "Salin",
                                            size="1",
                                            variant="ghost",
                                            on_click=CredentialState.copy_secret(crd_id, "secret"),
                                        ),
                                        spacing="2",
                                    ),
                                    justify="between",
                                    align="center",
                                    width="100%",
                                ),
                            ),
                            rx.text("—", color=Color.MUTED, font_size=FontSize.SM),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    # Catatan & Terakhir Diganti
                    rx.cond(
                        crd.get("catatan") != "",
                        rx.vstack(
                            rx.text(
                                "Catatan Tambahan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                crd.get("catatan", "—"),
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.hstack(
                        rx.text(
                            f"ID: {crd.get('id', '—')} · Terakhir diganti: "
                            f"{crd.get('terakhir_diganti', '—')}",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        justify="start",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "background_color": Color.CARD_BG,
                        "padding": "24px",
                        "border_radius": Radius.CARD,
                        "width": "460px",
                        "max_width": "90vw",
                        "z_index": "90",
                        "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
                        "border": f"1px solid {Color.BORDER}",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _reveal_modal() -> rx.Component:
    """Modal kompatibilitas untuk verifikasi PIN reveal kredensial."""
    return rx.cond(
        CredentialState.is_reveal_modal_open,
        rx.box(
            rx.box(
                on_click=CredentialState.close_reveal_modal,
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
                    rx.hstack(
                        rx.text(
                            "Verifikasi Keamanan Kredensial",
                            weight="bold",
                            size="4",
                            color=Color.TEXT,
                        ),
                        rx.icon(
                            tag="x",
                            cursor="pointer",
                            on_click=CredentialState.close_reveal_modal,
                        ),
                        justify="between",
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        "Masukkan PIN master Anda untuk melihat kredensial rahasia ini.",
                        color=Color.MUTED,
                        size="2",
                    ),
                    rx.input(
                        placeholder="PIN Master...",
                        type="password",
                        value=CredentialState.reveal_pin,
                        on_change=CredentialState.set_reveal_pin,
                    ),
                    rx.cond(
                        CredentialState.revealed_password != "",
                        rx.box(
                            rx.text("Password Dekripsi:", size="1", color=Color.MUTED),
                            rx.text(
                                CredentialState.revealed_password,
                                weight="bold",
                                size="4",
                                color=Color.TEXT,
                                margin_top="2px",
                            ),
                            padding="12px",
                            background_color=Color.APP_BG,
                            border_radius=Radius.CONTROL,
                            width="100%",
                            margin_top="10px",
                            border=f"1px solid {Color.BORDER}",
                        ),
                        rx.button(
                            "Dekripsi Password",
                            on_click=CredentialState.submit_reveal_pin,
                            width="100%",
                            margin_top="10px",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "background_color": Color.CARD_BG,
                        "padding": "24px",
                        "border_radius": Radius.CARD,
                        "width": "400px",
                        "z_index": "90",
                        "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
                        "border": f"1px solid {Color.BORDER}",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _dynamic_form_modal() -> rx.Component:
    """F: Form Tambah/Ubah Kredensial (Artboard 8 Kiri) dari Schema JSON dengan grup lipat."""
    field_input_style = rx.Style(
        {
            "width": "100%",
            "height": "38px",
            "padding": "0 12px",
            "border": f"1px solid {Color.BORDER}",
            "border_radius": "9px",
            "font_size": FontSize.SM,
        }
    )
    return rx.cond(
        CredentialState.form_modal_open,
        rx.box(
            rx.box(
                on_click=CredentialState.close_form_modal,
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
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            "Tambah Kredensial",
                            font_size="20px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Pilih jenis, kolom di bawah menyesuaikan otomatis.",
                            font_size=FontSize.SM,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.icon(
                        tag="x",
                        size=20,
                        cursor="pointer",
                        color=Color.MUTED,
                        on_click=CredentialState.close_form_modal,
                    ),
                    width="100%",
                    justify="between",
                    align="start",
                    padding="20px 24px 14px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body Scrollable
                rx.box(
                    rx.vstack(
                        rx.cond(
                            CredentialState.form_error != "",
                            rx.box(
                                rx.text(
                                    CredentialState.form_error,
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.DANGER_FG,
                                ),
                                padding="10px 14px",
                                background_color=Color.DANGER_BG,
                                border_radius="10px",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        # Pilihan 8 Chip Jenis Kredensial
                        rx.vstack(
                            rx.text(
                                "Jenis kredensial",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            rx.hstack(
                                rx.foreach(
                                    CredentialState.credential_type_chips,
                                    lambda ch: rx.el.button(
                                        rx.hstack(
                                            rx.icon(tag=ch["ikon"].to(str), size=14),
                                            rx.text(
                                                ch["nama"],
                                                font_size=FontSize.XS,
                                                font_weight=FontWeight.BOLD,
                                            ),
                                            spacing="2",
                                            align="center",
                                        ),
                                        type="button",
                                        on_click=CredentialState.select_form_type(ch["kode"]),
                                        style=rx.Style(
                                            {
                                                "padding": "7px 12px",
                                                "border_radius": "10px",
                                                "border": rx.cond(
                                                    CredentialState.form_type_code == ch["kode"],
                                                    f"1.5px solid {Color.ACCENT}",
                                                    f"1px solid {Color.BORDER}",
                                                ),
                                                "background_color": rx.cond(
                                                    CredentialState.form_type_code == ch["kode"],
                                                    Color.BLUE_50,
                                                    Color.SURFACE,
                                                ),
                                                "color": rx.cond(
                                                    CredentialState.form_type_code == ch["kode"],
                                                    Color.ACCENT,
                                                    Color.TEXT,
                                                ),
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                ),
                                spacing="2",
                                wrap="wrap",
                            ),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        # Grup Field Dinamis dari Schema JSON (Lipat / Collapsible)
                        rx.foreach(
                            CredentialState.current_form_groups,
                            lambda grp: rx.box(
                                rx.hstack(
                                    rx.hstack(
                                        rx.text(
                                            grp["grup"],
                                            font_size=FontSize.SM,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                        ),
                                        rx.cond(
                                            grp["is_optional"],
                                            rx.text(
                                                "opsional",
                                                font_size=FontSize.XS,
                                                color=Color.MUTED,
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.icon(
                                        tag=rx.cond(grp["is_open"], "chevron-up", "chevron-down"),
                                        size=16,
                                        color=Color.MUTED,
                                    ),
                                    width="100%",
                                    justify="between",
                                    align="center",
                                    cursor="pointer",
                                    on_click=CredentialState.toggle_form_group(grp["grup"]),
                                ),
                                rx.cond(
                                    grp["is_open"],
                                    rx.vstack(
                                        rx.foreach(
                                            grp["fields"].to(list[dict[str, Any]]),
                                            lambda f: rx.vstack(
                                                rx.hstack(
                                                    rx.text(
                                                        f["label"],
                                                        font_size=FontSize.XS,
                                                        font_weight=FontWeight.BOLD,
                                                        color=Color.TEXT,
                                                    ),
                                                    rx.cond(
                                                        f["wajib"],
                                                        rx.text(
                                                            "*",
                                                            color=Color.DANGER_FG,
                                                            font_weight=FontWeight.BOLD,
                                                        ),
                                                        rx.fragment(),
                                                    ),
                                                    spacing="1",
                                                ),
                                                rx.cond(
                                                    f["key"] == "linked_asset_id",
                                                    rx.el.select(
                                                        rx.el.option("Pilih PC / IP...", value=""),
                                                        rx.foreach(
                                                            CredentialState.pc_link_options,
                                                            lambda opt: rx.el.option(
                                                                opt, value=opt
                                                            ),
                                                        ),
                                                        on_change=CredentialState.set_form_linked_asset_id,
                                                        style=field_input_style,
                                                    ),
                                                    rx.el.input(
                                                        type=rx.cond(
                                                            f["rahasia"]
                                                            & (~CredentialState.form_show_password),
                                                            "password",
                                                            rx.cond(
                                                                f["tipe"] == "date",
                                                                "date",
                                                                "text",
                                                            ),
                                                        ),
                                                        auto_complete="new-password",
                                                        value=f["value"],
                                                        on_change=lambda v: (
                                                            CredentialState.set_form_field_value(
                                                                f["key"].to(str), v
                                                            )
                                                        ),
                                                        style=field_input_style,
                                                    ),
                                                ),
                                                spacing="1",
                                                align="start",
                                                width="100%",
                                            ),
                                        ),
                                        spacing="3",
                                        width="100%",
                                        margin_top="10px",
                                    ),
                                    rx.fragment(),
                                ),
                                padding="14px 16px",
                                border=f"1px solid {Color.BORDER}",
                                border_radius="12px",
                                width="100%",
                            ),
                        ),
                        # Indikator Kekuatan Password (B)
                        rx.hstack(
                            rx.text(
                                "Kekuatan password: "
                                f"{CredentialState.password_strength_info['label']}",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=CredentialState.password_strength_info["color"],
                            ),
                            rx.el.button(
                                rx.cond(
                                    CredentialState.form_show_password,
                                    "Sembunyikan input password",
                                    "Tampilkan input password",
                                ),
                                type="button",
                                on_click=CredentialState.toggle_form_show_password,
                                style=rx.Style(
                                    {
                                        "background": "transparent",
                                        "border": "none",
                                        "color": Color.ACCENT,
                                        "font_size": FontSize.XS,
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            width="100%",
                            justify="between",
                        ),
                        # Bagian "Siapa boleh melihat?" (F - Artboard 8 Kiri Bawah)
                        rx.vstack(
                            rx.hstack(
                                rx.icon(tag="shield-check", size=16, color=Color.ACCENT),
                                rx.text(
                                    "Siapa boleh melihat?",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "Divisi pemilik",
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.MUTED,
                                    ),
                                    rx.el.select(
                                        rx.foreach(
                                            CredentialState.form_division_options,
                                            lambda d: rx.el.option(d, value=d),
                                        ),
                                        value=CredentialState.form_divisi,
                                        on_change=CredentialState.set_form_divisi,
                                        style=rx.Style(
                                            {
                                                "width": "100%",
                                                "height": "38px",
                                                "padding": "0 10px",
                                                "border": f"1px solid {Color.BORDER}",
                                                "border_radius": "8px",
                                            }
                                        ),
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Tingkat minimum",
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.MUTED,
                                    ),
                                    rx.el.select(
                                        rx.el.option("Staff (0)", value="Staff (0)"),
                                        rx.el.option(
                                            "SPV Operasional (20)",
                                            value="SPV Operasional (20)",
                                        ),
                                        rx.el.option("Direktur (40)", value="Direktur (40)"),
                                        value=CredentialState.form_min_rank_label,
                                        on_change=CredentialState.set_form_min_rank_label,
                                        style=rx.Style(
                                            {
                                                "width": "100%",
                                                "height": "38px",
                                                "padding": "0 10px",
                                                "border": f"1px solid {Color.BORDER}",
                                                "border_radius": "8px",
                                            }
                                        ),
                                    ),
                                    spacing="1",
                                    align="start",
                                ),
                                style=rx.Style(
                                    {
                                        "display": "grid",
                                        "grid_template_columns": "1fr 1fr",
                                        "gap": "12px",
                                        "width": "100%",
                                    }
                                ),
                            ),
                            rx.hstack(
                                rx.el.input(
                                    type="checkbox",
                                    checked=CredentialState.form_peer_access,
                                    on_change=CredentialState.toggle_form_peer_access,
                                ),
                                rx.text(
                                    "Rekan satu divisi boleh melihat",
                                    font_size=FontSize.XS,
                                    color=Color.TEXT,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(
                                f"Terlihat oleh: {CredentialState.form_visibility_preview_text}",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.BLUE_700,
                            ),
                            spacing="2",
                            align="start",
                            padding="14px 16px",
                            background_color=Color.BLUE_50,
                            border=f"1px solid {Color.BLUE_BORDER}",
                            border_radius="12px",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "18px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 140px)",
                        }
                    ),
                ),
                # Footer
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=CredentialState.close_form_modal,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": "10px",
                                "background": Color.SURFACE,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.el.button(
                        "Simpan Kredensial",
                        type="button",
                        on_click=CredentialState.save_credential_form,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 20px",
                                "border": "none",
                                "border_radius": "10px",
                                "background": Color.ACCENT,
                                "color": Color.WHITE,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                    padding="14px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SLATE_50,
                        }
                    ),
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "94%",
                        "max_width": "620px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border_radius": "16px",
                        "z_index": "90",
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _access_rules_modal() -> rx.Component:
    """D: Modal Aturan Akses 2 Lapis & Simulasi 'Lihat sebagai pengguna' (Artboard 8 Kanan)."""

    def _matrix_cell_btn(role_str: Any, t_code: str, val_var: Any) -> rx.Component:
        symbol = rx.match(val_var, ("full", "●"), ("view", "◐"), "–")
        fg = rx.match(val_var, ("full", Color.ACCENT), ("view", Color.AMBER_600), Color.MUTED)
        return rx.table.cell(
            rx.el.button(
                symbol,
                type="button",
                on_click=CredentialState.cycle_lapis1_cell(role_str, t_code),
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "color": fg,
                        "font_size": "15px",
                        "font_weight": FontWeight.EXTRABOLD,
                        "cursor": "pointer",
                        "width": "28px",
                        "height": "28px",
                    }
                ),
            )
        )

    return rx.cond(
        CredentialState.rules_modal_open,
        rx.box(
            rx.box(
                on_click=CredentialState.close_rules_modal,
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
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            "Aturan Akses",
                            font_size="20px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Lapis 1: jenis kredensial per peran (klik sel untuk mengubah).",
                            font_size=FontSize.SM,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.hstack(
                        rx.text(
                            "Lihat sebagai:",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.MUTED,
                        ),
                        rx.el.select(
                            rx.el.option("SPV Operasional", value="SPV Operasional"),
                            rx.el.option("Owner", value="Owner"),
                            rx.el.option("Direktur", value="Direktur"),
                            rx.el.option("General Manager", value="General Manager"),
                            rx.el.option("Lead IT", value="Lead IT"),
                            rx.el.option("HRD", value="HRD"),
                            rx.el.option("Head Marketing", value="Head Marketing"),
                            rx.el.option("Staff Operator & CS", value="Staff Operator & CS"),
                            rx.el.option("Staff Accounting", value="Staff Accounting"),
                            rx.el.option("Staff Voucher", value="Staff Voucher"),
                            rx.el.option("Staff Kreatif", value="Staff Kreatif"),
                            rx.el.option("Programmer / QA", value="Programmer / QA"),
                            value=CredentialState.effective_role,
                            on_change=CredentialState.set_impersonated_role,
                            style=rx.Style(
                                {
                                    "height": "34px",
                                    "padding": "0 10px",
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": "8px",
                                    "font_size": FontSize.XS,
                                }
                            ),
                        ),
                        rx.icon(
                            tag="x",
                            size=20,
                            cursor="pointer",
                            color=Color.MUTED,
                            on_click=CredentialState.close_rules_modal,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    padding="20px 24px 14px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                rx.box(
                    rx.vstack(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("PERAN"),
                                    rx.table.column_header_cell("WEB"),
                                    rx.table.column_header_cell("PC"),
                                    rx.table.column_header_cell("EMAIL"),
                                    rx.table.column_header_cell("SQL"),
                                    rx.table.column_header_cell("TELE"),
                                    rx.table.column_header_cell("RADMIN"),
                                    rx.table.column_header_cell("MIKR."),
                                    rx.table.column_header_cell("CCTV"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    CredentialState.lapis1_matrix_rows,
                                    lambda r: rx.table.row(
                                        rx.table.cell(
                                            rx.text(
                                                r["role"],
                                                font_weight=FontWeight.BOLD,
                                                font_size=FontSize.XS,
                                            )
                                        ),
                                        _matrix_cell_btn(r["role"], "website", r["website"]),
                                        _matrix_cell_btn(r["role"], "pc", r["pc"]),
                                        _matrix_cell_btn(r["role"], "email", r["email"]),
                                        _matrix_cell_btn(r["role"], "sql_server", r["sql_server"]),
                                        _matrix_cell_btn(r["role"], "telegram", r["telegram"]),
                                        _matrix_cell_btn(r["role"], "radmin", r["radmin"]),
                                        _matrix_cell_btn(r["role"], "mikrotik", r["mikrotik"]),
                                        _matrix_cell_btn(r["role"], "cctv_wifi", r["cctv_wifi"]),
                                    ),
                                )
                            ),
                            size="1",
                            width="100%",
                        ),
                        rx.text(
                            (
                                "● lihat + password   ◐ lihat saja, password "
                                "disembunyikan   – tidak ada akses"
                            ),
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        rx.divider(color=Color.BORDER),
                        rx.text(
                            "LAPIS 2: LINGKUP DIVISI & TINGKAT",
                            font_size="11px",
                            font_weight=FontWeight.BOLD,
                            color=Color.MUTED,
                            letter_spacing="0.06em",
                        ),
                        rx.vstack(
                            rx.text(
                                (
                                    "1. Atasan -> bawahan. Tingkat lebih tinggi boleh melihat "
                                    "tingkat di bawahnya (Direktur > GM > SPV > Staff), "
                                    "tidak sebaliknya."
                                ),
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                (
                                    "2. Satu divisi. Rekan satu divisi saling melihat. "
                                    "Divisi lain tidak."
                                ),
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                (
                                    "3. Divisi sensitif (Accounting). GM dan SPV tidak ikut. "
                                    "Hanya Owner, Direktur, dan IT."
                                ),
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                (
                                    "4. Pengecualian. HRD -> Operator & CS, "
                                    "Head Marketing -> Kreatif, IT -> semua."
                                ),
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "18px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 90px)",
                        }
                    ),
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "95%",
                        "max_width": "740px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border_radius": "16px",
                        "z_index": "90",
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.2)",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def credential_view_page() -> rx.Component:
    """E: Halaman utama Credential Manager ITAM Pro (Artboard 7 & 8) dengan breadcrumb."""
    columns_def = [
        {"key": "jenis_label", "header": "JENIS", "render_type": "chip", "width": "150px"},
        {
            "key": "induk",
            "header": "NAMA",
            "render_type": "bold",
            "width": "210px",
        },
        {"key": "target", "header": "TARGET / DETAIL", "render_type": "text", "width": "210px"},
        {"key": "divisi", "header": "DIVISI", "render_type": "text", "width": "135px"},
        {"header": "PASSWORD", "accessor": lambda row: _password_cell(row), "width": "155px"},
        {
            "key": "status",
            "header": "STATUS",
            "render_type": "badge",
            "badge_variant_key": "status_variant",
            "width": "145px",
        },
        {"key": "akses_label", "header": "AKSES", "render_type": "text", "width": "150px"},
        {"header": "AKSI", "accessor": lambda row: _action_buttons(row), "width": "110px"},
    ]

    return base_layout(
        rx.vstack(
            _credential_header(),
            _kpi_cards(),
            _type_tiles_row(),
            rx.box(
                _credential_filter_bar(),
                reusable_data_table(
                    items=CredentialState.credentials,
                    columns=columns_def,
                    is_loading=CredentialState.is_loading,
                    empty_message="Tidak ada kredensial di lingkup Anda",
                    empty_subtitle=(
                        "Entri di luar lingkup akses Anda tidak ditampilkan "
                        "atau ubah filter pencarian."
                    ),
                    on_reset_filter=CredentialState.reset_filters,
                ),
                table_pagination(
                    summary_text=CredentialState.pagination_footer_text,
                    page=CredentialState.page,
                    current_page=CredentialState.page,
                    current_page_str=CredentialState.current_page_str,
                    total_pages=CredentialState.total_pages,
                    page_tokens=CredentialState.page_tokens,
                    total_items=CredentialState.total_items,
                    page_size=CredentialState.page_size,
                    on_prev=CredentialState.prev_page,
                    on_next=CredentialState.next_page,
                    on_page_select=CredentialState.select_page,
                ),
                width="100%",
                style=rx.Style(
                    {
                        "background_color": Color.CARD_BG,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "overflow": "hidden",
                    }
                ),
            ),
            _detail_drawer(),
            _reveal_modal(),
            _dynamic_form_modal(),
            _access_rules_modal(),
            spacing="0",
            width="100%",
        ),
        breadcrumb=("Security", "Credential Manager"),
    )


__all__ = ["credential_view_page"]
