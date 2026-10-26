"""
Komponen Detail Drawer Generik ITAM Pro.
Mendukung grup informasi key-value, seksi chip konektivitas, tab 'Riwayat & Log',
serta aksi Edit, Duplikat, dan Hapus.
"""
from typing import Any

import reflex as rx

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

from .badge import app_badge, connector_chip
from .status_badge import asset_condition_badge, asset_status_badge


def _kv_row(item: dict[str, Any]) -> rx.Component:
    """Render satu baris pasangan Label - Nilai di dalam seksi drawer."""
    return rx.hstack(
        rx.text(
            item["label"],
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            style=rx.Style({"width": "42%", "flex_shrink": "0"}),
        ),
        rx.cond(
            item["label"] == "Aksi",
            rx.el.a(
                item["value"],
                href="/assets",
                style=rx.Style(
                    {
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "color": Color.ACCENT,
                        "text_decoration": "none",
                        "cursor": "pointer",
                        "text_align": "right",
                        "width": "58%",
                        "_hover": {"text_decoration": "underline"},
                    }
                ),
            ),
            rx.text(
                item["value"],
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.TEXT,
                text_align="right",
                style=rx.Style({"width": "58%", "word_break": "break-word"}),
            ),
        ),
        width="100%",
        justify="between",
        align="start",
        padding_y="8px",
        style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
    )


def _drawer_section(title: str, items_var: Any) -> rx.Component:
    """Bagian bergrup key-value di dalam drawer."""
    return rx.vstack(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
        ),
        rx.vstack(
            rx.foreach(items_var, _kv_row),
            spacing="0",
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.TABLE_HEADER_BG,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "padding": "4px 14px",
                }
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _drawer_chips_section(title: str, chips_var: Any) -> rx.Component:
    """Bagian bergrup khusus daftar chip (contoh: Konektivitas Monitor)."""
    return rx.vstack(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
        ),
        rx.hstack(
            rx.foreach(chips_var, connector_chip),
            spacing="2",
            wrap="wrap",
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.TABLE_HEADER_BG,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "padding": "12px 14px",
                }
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _history_row(item: dict[str, Any]) -> rx.Component:
    """Render satu baris riwayat/aktivitas pada tab kedua drawer."""
    return rx.vstack(
        rx.hstack(
            rx.text(
                item["event"],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            rx.text(
                item["date"],
                font_size=FontSize.XS,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        rx.text(
            item["note"],
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
        ),
        spacing="1",
        align="start",
        width="100%",
        padding="12px 14px",
        style=rx.Style(
            {
                "background_color": Color.TABLE_HEADER_BG,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CONTROL,
            }
        ),
    )


def _logs_mini_table(logs: Any) -> rx.Component:
    """Tabel mini log maintenance untuk tab Riwayat & Log di drawer."""
    return rx.vstack(
        rx.text(
            "LOG MAINTENANCE TERKAIT",
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Tgl"),
                        rx.table.column_header_cell("Kegiatan"),
                        rx.table.column_header_cell("Hasil"),
                        rx.table.column_header_cell("PIC"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        logs,
                        lambda log: rx.table.row(
                            rx.table.cell(log["tanggal_selesai"]),
                            rx.table.cell(log["kegiatan"]),
                            rx.table.cell(
                                app_badge(
                                    label=log["hasil"],
                                    variant=rx.match(
                                        log["hasil"],
                                        ("Normal", "success"),
                                        ("Perlu tindak lanjut", "warning"),
                                        "neutral",
                                    ),
                                )
                            ),
                            rx.table.cell(log["dikerjakan_oleh"]),
                        ),
                    )
                ),
                variant="surface",
                size="1",
                width="100%",
            ),
            style=rx.Style(
                {
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "overflow": "hidden",
                    "width": "100%",
                }
            ),
        ),
        spacing="2",
        width="100%",
        margin_bottom=Space.S3,
    )


def _drawer_tab_button(
    label: str,
    tab_key: str,
    active_tab: Any,
    on_tab_change: Any,
) -> rx.Component:
    """Tombol tab di dalam Detail Drawer."""
    is_active = active_tab == tab_key
    return rx.el.button(
        label,
        type="button",
        on_click=on_tab_change(tab_key),
        style=rx.Style(
            {
                "padding": "10px 16px",
                "background": "transparent",
                "border": "none",
                "border_bottom": rx.cond(
                    is_active,
                    f"2px solid {Color.ACCENT}",
                    "2px solid transparent",
                ),
                "color": rx.cond(is_active, Color.ACCENT, Color.MUTED),
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "font_weight": rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                "cursor": "pointer",
                "transition": "color 0.15s ease, border-color 0.15s ease",
            }
        ),
    )


def detail_drawer(
    is_open: Any,
    on_close: Any,
    code_var: Any,
    title_var: Any,
    active_tab: Any,
    on_tab_change: Any,
    general_items: Any,
    usage_items: Any,
    history_items: Any,
    on_edit: Any,
    on_duplicate: Any,
    on_delete: Any,
    category_var: Any | None = None,
    condition_var: Any | None = None,
    status_var: Any | None = None,
    section1_title: str = "Informasi umum",
    section2_title: str = "Penggunaan & lokasi",
    section3_title: str | None = None,
    section3_items: Any | None = None,
    chips_section_title: str | None = None,
    chips_items: Any | None = None,
    section4_title: str | None = None,
    section4_items: Any | None = None,
    duplicate_label: str = "Duplikat × N",
    on_key_down: Any | None = None,
    maintenance_logs: Any | None = None,
    tabs: tuple[tuple[str, str], tuple[str, str]] = (
        ("detail", "Rincian Aset"),
        ("history", "Riwayat & Log"),
    ),
) -> rx.Component:
    """
    Komponen Drawer Kanan Generik (440px).
    Mendukung grup key-value, grup chip konektor, serta tab Riwayat & Log.
    """
    tab1_key, tab1_label = tabs[0]
    tab2_key, tab2_label = tabs[1]

    return rx.cond(
        is_open,
        rx.box(
            rx.script(
                """
                if (!window._itamDrawerEscBound) {
                    window._itamDrawerEscBound = true;
                    window.addEventListener("keydown", function(e) {
                        if (e.key === "Escape") {
                            var closeBtn = document.getElementById("drawer-close-btn");
                            if (closeBtn) {
                                closeBtn.click();
                            }
                        }
                    });
                }
                """
            ),
            # Scrim rgba(10, 26, 68, 0.35)
            rx.box(
                on_click=on_close,
                aria_hidden="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "60",
                    }
                ),
            ),
            # Panel Drawer Kanan 440px (Layar penuh di <900px)
            rx.box(
                # 1. Header Drawer
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.text(
                                code_var,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.ACCENT,
                            ),
                            app_badge(label=category_var, variant="neutral")
                            if category_var is not None
                            else rx.fragment(),
                            asset_condition_badge(condition_var)
                            if condition_var is not None
                            else rx.fragment(),
                            asset_status_badge(status_var)
                            if status_var is not None
                            else rx.fragment(),
                            spacing="2",
                            align="center",
                            wrap="wrap",
                        ),
                        rx.el.button(
                            rx.hstack(
                                rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                                rx.text(
                                    "Tutup",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.MUTED,
                                ),
                                spacing="1",
                                align="center",
                            ),
                            id="drawer-close-btn",
                            type="button",
                            aria_label="Tutup panel detail",
                            on_click=on_close,
                            style=rx.Style(
                                {
                                    "padding": "6px 10px",
                                    "background_color": Color.TABLE_HEADER_BG,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "cursor": "pointer",
                                    "display": "inline-flex",
                                    "align_items": "center",
                                    "flex_shrink": "0",
                                }
                            ),
                            _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                    ),
                    rx.heading(
                        title_var,
                        font_size=FontSize.LOGO,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                        line_height="1.3",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                    padding="20px 24px 14px 24px",
                ),
                # 2. Baris Tab
                rx.hstack(
                    _drawer_tab_button(
                        label=tab1_label.strip(),
                        tab_key=tab1_key,
                        active_tab=active_tab,
                        on_tab_change=on_tab_change,
                    ),
                    _drawer_tab_button(
                        label=tab2_label.strip(),
                        tab_key=tab2_key,
                        active_tab=active_tab,
                        on_tab_change=on_tab_change,
                    ),
                    spacing="2",
                    width="100%",
                    padding_x="24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # 3. Body Drawer (Scrollable)
                rx.box(
                    rx.cond(
                        active_tab == tab1_key,
                        rx.vstack(
                            _drawer_section(section1_title, general_items),
                            _drawer_section(section2_title, usage_items),
                            _drawer_section(section3_title, section3_items)
                            if section3_title is not None and section3_items is not None
                            else rx.fragment(),
                            _drawer_chips_section(chips_section_title, chips_items)
                            if chips_section_title is not None and chips_items is not None
                            else rx.fragment(),
                            _drawer_section(section4_title, section4_items)
                            if section4_title is not None and section4_items is not None
                            else rx.fragment(),
                            spacing="5",
                            width="100%",
                            align="start",
                        ),
                        rx.vstack(
                            _logs_mini_table(maintenance_logs)
                            if maintenance_logs is not None
                            else rx.fragment(),
                            rx.text(
                                "RIWAYAT AKTIVITAS",
                                font_size=FontSize.GROUP_LABEL,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.06em",
                            ),
                            rx.foreach(history_items, _history_row),
                            spacing="3",
                            width="100%",
                            align="start",
                        ),
                    ),
                    style=rx.Style(
                        {
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "flex": "1",
                            "width": "100%",
                        }
                    ),
                ),
                # 4. Footer Tombol Aksi
                rx.hstack(
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="pencil", size=Size.ICON_SM, color=Color.TEXT),
                            rx.text(
                                "Edit",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=on_edit,
                        style=rx.Style(
                            {
                                "flex": "1",
                                "height": Size.FILTER_CONTROL_H,
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                        _hover=rx.Style({"background_color": Color.SURFACE_HOVER}),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="copy", size=Size.ICON_SM, color=Color.ACCENT),
                            rx.text(
                                duplicate_label,
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.ACCENT,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=on_duplicate,
                        style=rx.Style(
                            {
                                "flex": "1",
                                "height": Size.FILTER_CONTROL_H,
                                "background_color": Color.INFO_BG,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="trash-2", size=Size.ICON_SM, color=Color.DANGER_FG),
                            rx.text(
                                "Hapus",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.DANGER_FG,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=on_delete,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 16px",
                                "background_color": Color.DANGER_BG,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    padding="16px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SURFACE,
                        }
                    ),
                ),
                id="global-detail-drawer",
                role="dialog",
                aria_modal="true",
                aria_label="Rincian Item",
                tab_index=-1,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "0",
                        "right": "0",
                        "bottom": "0",
                        "width": Size.DRAWER_WIDTH,
                        "background_color": Color.SURFACE,
                        "box_shadow": Shadow.DRAWER,
                        "display": "flex",
                        "flex_direction": "column",
                        "z_index": "70",
                        "outline": "none",
                        "@media (max-width: 899px)": {
                            "width": "100%",
                        },
                    }
                ),
            ),
            style=rx.Style({"position": "relative", "z_index": "60"}),
        ),
        rx.fragment(),
    )


__all__ = ["detail_drawer"]
