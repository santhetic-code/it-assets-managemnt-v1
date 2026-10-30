"""
Halaman Credential Manager ITAM Pro (Tahap 12).
Brankas penyimpanan kredensial terenkripsi dengan proteksi reveal timer 30 detik.
"""
from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.filter_bar import table_filter_bar
from itam_pro.components.tables.pagination import table_pagination
from itam_pro.components.ui.stat_card import stat_card
from itam_pro.components.ui.tabs import app_tabs
from itam_pro.services.credential_config import CREDENTIAL_TABS
from itam_pro.states.credential_state import CredentialState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space


def _kpi_cards() -> rx.Component:
    """Tampilkan ringkasan metrik status kredensial."""
    return rx.grid(
        stat_card(
            "Total Kredensial Tersimpan",
            CredentialState.total_items,
            "lock",
            description="dalam brankas terenkripsi",
        ),
        stat_card(
            "Website & Aplikasi",
            CredentialState.tab_counts.get("Website & Aplikasi", 0),
            "globe",
            description="cPanel, WordPress, CMS",
        ),
        stat_card(
            "Perangkat & Server",
            CredentialState.tab_counts.get("Perangkat", 0),
            "server",
            description="Mikrotik, SQL Server, PC",
        ),
        columns="3",
        spacing="4",
        width="100%",
        margin_bottom=Space.SECTION,
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
                                            on_click=CredentialState.copy_secret(
                                                crd_id, "secret"
                                            ),
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


def credential_view_page() -> rx.Component:
    """Halaman utama Credential Manager ITAM Pro."""
    columns_def = [
        {"key": "jenis_label", "header": "Jenis", "render_type": "chip", "width": "180px"},
        {
            "key": "induk",
            "header": "Nama Akun",
            "render_type": "name_with_sub",
            "sub_key": "peran",
            "width": "220px",
        },
        {"key": "target", "header": "Target", "render_type": "text", "width": "200px"},
        {"key": "username", "header": "Username", "render_type": "text", "width": "180px"},
        {"key": "secret", "header": "Password", "render_type": "secret_mask", "width": "140px"},
        {
            "key": "status",
            "header": "Status",
            "render_type": "badge",
            "badge_variant_key": "status_variant",
            "width": "150px",
        },
        {"header": "Aksi", "accessor": lambda row: _action_buttons(row), "width": "140px"},
    ]

    tab_items = [{"label": tab, "value": tab} for tab in CREDENTIAL_TABS]

    return base_layout(
        rx.vstack(
            _kpi_cards(),
            app_tabs(
                items=tab_items,
                active_value=CredentialState.active_tab,
                on_change=CredentialState.set_tab,
            ),
            rx.box(
                table_filter_bar(
                    search_placeholder="Cari akun, target, username...",
                    on_search=CredentialState.set_search,
                ),
                reusable_data_table(
                    items=CredentialState.credentials,
                    columns=columns_def,
                ),
                table_pagination(
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
                margin_top="16px",
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
            spacing="0",
            width="100%",
        )
    )


__all__ = ["credential_view_page"]
