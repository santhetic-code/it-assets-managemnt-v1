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


def _ip_detail_drawer(
    is_open: Any,
    on_close: Any,
    code_var: Any,
    title_var: Any,
    category_var: Any,
    status_var: Any,
    active_tab: Any,
    on_tab_change: Any,
    general_items: Any,
    usage_items: Any,
    history_items: Any,
    on_edit: Any,
    on_duplicate: Any,
    on_delete: Any,
    tabs: tuple[tuple[str, str], ...],
) -> rx.Component:
    from itam_pro.states.ip_state import IPState

    tab1_key, tab1_label = tabs[0]
    tab2_key, tab2_label = tabs[1] if len(tabs) > 1 else ("", "")

    return rx.cond(
        is_open,
        rx.box(
            rx.box(
                on_click=on_close,
                aria_hidden="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM_DARK,
                        "z_index": "60",
                    }
                ),
            ),
            rx.box(
                # 1. Header Tetap
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.text(
                                "DETAIL ENTRI IP · ID ",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            rx.text(
                                IPState.active_entry_id,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.05em",
                            ),
                            spacing="1",
                            align="center",
                        ),
                        rx.el.button(
                            rx.icon(tag="x", size=18, color=Color.MUTED),
                            type="button",
                            on_click=on_close,
                            id="drawer-close-btn",
                            aria_label="Tutup Panel",
                            style=rx.Style(
                                {
                                    "width": "34px",
                                    "height": "34px",
                                    "border_radius": Radius.CONTROL,
                                    "border": f"1px solid {Color.BORDER}",
                                    "background_color": Color.SURFACE,
                                    "display": "flex",
                                    "align_items": "center",
                                    "justify_content": "center",
                                    "cursor": "pointer",
                                }
                            ),
                            _hover=rx.Style({"background_color": Color.SLATE_100}),
                        ),
                        width="100%",
                        justify="between",
                        align="center",
                    ),
                    rx.hstack(
                        rx.center(
                            rx.cond(
                                IPState.active_is_vm,
                                rx.icon(tag="layers", size=24, color=Color.WHITE, stroke_width=2),
                                rx.icon(tag="monitor", size=24, color=Color.WHITE, stroke_width=2),
                            ),
                            width="52px",
                            height="52px",
                            border_radius="15px",
                            background=rx.cond(
                                IPState.active_is_vm,
                                Color.GRADIENT_PURPLE,
                                Color.GRADIENT_BLUE,
                            ),
                            flex_shrink="0",
                        ),
                        rx.text(
                            title_var,
                            font_size="22px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                            line_height="1.2",
                            style=rx.Style({"word_break": "break-word"}),
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text(
                            code_var,
                            font_family="monospace",
                            font_size="14px",
                            font_weight=FontWeight.BOLD,
                            color=Color.BLUE_700,
                        ),
                        rx.el.button(
                            rx.icon(tag="copy", size=13, color=Color.MUTED),
                            type="button",
                            on_click=[
                                rx.set_clipboard(code_var),
                                rx.toast.info("IP disalin ke clipboard", position="top-right"),
                            ],
                            aria_label="Salin IP",
                            style=rx.Style(
                                {
                                    "width": "28px",
                                    "height": "28px",
                                    "border_radius": Radius.CONTROL,
                                    "border": f"1px solid {Color.BORDER}",
                                    "background_color": Color.SURFACE,
                                    "display": "flex",
                                    "align_items": "center",
                                    "justify_content": "center",
                                    "cursor": "pointer",
                                }
                            ),
                            _hover=rx.Style({"background_color": Color.SLATE_100}),
                        ),
                        rx.cond(
                            IPState.active_is_vm,
                            rx.box(
                                rx.text(
                                    "VM",
                                    font_size="12px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.BLUE_700,
                                ),
                                padding="3px 10px",
                                border_radius="9999px",
                                background_color=Color.BLUE_100,
                                border=f"1px solid {Color.BLUE_BORDER}",
                            ),
                            rx.box(
                                rx.text(
                                    "Fisik",
                                    font_size="12px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.SLATE_700,
                                ),
                                padding="3px 10px",
                                border_radius="9999px",
                                background_color=Color.SLATE_100,
                                border=f"1px solid {Color.SLATE_300}",
                            ),
                        ),
                        rx.cond(
                            status_var == "Nonaktif",
                            rx.hstack(
                                rx.box(
                                    width="6px",
                                    height="6px",
                                    border_radius="50%",
                                    background_color=Color.RED_700,
                                ),
                                rx.text(
                                    "Nonaktif",
                                    font_size="12px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.RED_700,
                                ),
                                padding="3px 10px",
                                border_radius="9999px",
                                background_color=Color.RED_100,
                                border=f"1px solid {Color.DANGER_BORDER}",
                                align="center",
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.box(
                                    width="6px",
                                    height="6px",
                                    border_radius="50%",
                                    background_color=Color.GREEN_700,
                                ),
                                rx.text(
                                    "Aktif",
                                    font_size="12px",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.GREEN_700,
                                ),
                                padding="3px 10px",
                                border_radius="9999px",
                                background_color=Color.GREEN_100,
                                border=f"1px solid {Color.GREEN_BORDER}",
                                align="center",
                                spacing="1",
                            ),
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                        flex_wrap="wrap",
                    ),
                    spacing="3",
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
                    )
                    if len(tabs) > 1
                    else rx.fragment(),
                    spacing="2",
                    width="100%",
                    padding_x="24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # 3. Konten Scrollable
                rx.box(
                    rx.cond(
                        active_tab == tab1_key,
                        rx.vstack(
                            rx.cond(
                                IPState.drawer_has_kendala,
                                rx.hstack(
                                    rx.icon(
                                        tag="triangle-alert",
                                        size=20,
                                        color=Color.AMBER_700,
                                        flex_shrink="0",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "ADA KENDALA / CATATAN KHUSUS",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.AMBER_900,
                                            letter_spacing="0.05em",
                                        ),
                                        rx.text(
                                            IPState.active_general_items[-1]["value"],
                                            font_size="13px",
                                            color=Color.AMBER_800,
                                            line_height="1.4",
                                            style=rx.Style({"word_break": "break-word"}),
                                        ),
                                        spacing="1",
                                        align="start",
                                    ),
                                    width="100%",
                                    padding="12px 14px",
                                    border_radius="10px",
                                    background_color=Color.AMBER_50,
                                    border=f"1px solid {Color.AMBER_BORDER}",
                                    spacing="3",
                                    align="start",
                                ),
                            ),
                            rx.vstack(
                                rx.text(
                                    "DATA ENTRI IP",
                                    font_size=FontSize.GROUP_LABEL,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.MUTED,
                                    letter_spacing="0.06em",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.text(
                                            "IP ADDRESS",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.text(
                                            code_var,
                                            font_size="14px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                            font_family="monospace",
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "PENGGUNA",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.text(
                                            title_var,
                                            font_size="14px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                            style=rx.Style({"word_break": "break-word"}),
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "OPERATING SYSTEM",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.text(
                                            IPState.active_general_items[7]["value"],
                                            font_size="14px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                            style=rx.Style({"word_break": "break-word"}),
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "KATEGORI",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.text(
                                            category_var,
                                            font_size="14px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "HOST SERVER FISIK",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.cond(
                                            IPState.active_is_vm,
                                            rx.el.button(
                                                rx.hstack(
                                                    rx.icon(
                                                        tag="server",
                                                        size=14,
                                                        color=Color.BLUE_600,
                                                    ),
                                                    rx.text(
                                                        IPState.active_host_name,
                                                        font_size="14px",
                                                        font_weight=FontWeight.BOLD,
                                                        color=Color.BLUE_600,
                                                    ),
                                                    rx.icon(
                                                        tag="external-link",
                                                        size=12,
                                                        color=Color.BLUE_600,
                                                    ),
                                                    spacing="2",
                                                    align="center",
                                                ),
                                                type="button",
                                                on_click=lambda: IPState.open_host_drawer_by_code(
                                                    IPState.active_host_name
                                                ),
                                                style=rx.Style(
                                                    {
                                                        "background": "transparent",
                                                        "border": "none",
                                                        "cursor": "pointer",
                                                        "padding": "0",
                                                    }
                                                ),
                                                _hover=rx.Style({"text_decoration": "underline"}),
                                            ),
                                            rx.text(
                                                "Tidak ada (standalone)",
                                                font_size="14px",
                                                color=Color.MUTED,
                                            ),
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        style=rx.Style({"grid_column": "span 2"}),
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            "FUNGSI",
                                            font_size="11px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                            letter_spacing="0.04em",
                                        ),
                                        rx.text(
                                            IPState.active_general_items[6]["value"],
                                            font_size="14px",
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                            style=rx.Style({"word_break": "break-word"}),
                                        ),
                                        spacing="1",
                                        align="start",
                                        padding="10px 14px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.TABLE_HEADER_BG,
                                        style=rx.Style({"grid_column": "span 2"}),
                                        width="100%",
                                    ),
                                    style=rx.Style(
                                        {
                                            "display": "grid",
                                            "grid_template_columns": "1fr 1fr",
                                            "gap": "10px",
                                            "width": "100%",
                                        }
                                    ),
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text(
                                    "ASET FISIK & VM",
                                    font_size=FontSize.GROUP_LABEL,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.MUTED,
                                    letter_spacing="0.06em",
                                ),
                                rx.cond(
                                    IPState.active_is_vm,
                                    rx.box(
                                        rx.hstack(
                                            rx.center(
                                                rx.icon(
                                                    tag="server", size=20, color=Color.BLUE_700
                                                ),
                                                width="40px",
                                                height="40px",
                                                border_radius="10px",
                                                background_color=Color.BLUE_100,
                                                flex_shrink="0",
                                            ),
                                            rx.vstack(
                                                rx.text(
                                                    "Berjalan di Host Server",
                                                    font_size="12px",
                                                    color=Color.MUTED,
                                                ),
                                                rx.text(
                                                    IPState.active_host_name,
                                                    font_size="14px",
                                                    font_weight=FontWeight.BOLD,
                                                    color=Color.TEXT,
                                                ),
                                                spacing="1",
                                                align="start",
                                            ),
                                            rx.spacer(),
                                            rx.el.button(
                                                rx.hstack(
                                                    rx.text(
                                                        "Lihat host",
                                                        font_size="13px",
                                                        font_weight=FontWeight.BOLD,
                                                        color=Color.BLUE_600,
                                                    ),
                                                    rx.icon(
                                                        tag="chevron-right",
                                                        size=14,
                                                        color=Color.BLUE_600,
                                                    ),
                                                    spacing="1",
                                                    align="center",
                                                ),
                                                type="button",
                                                on_click=lambda: IPState.open_host_drawer_by_code(
                                                    IPState.active_host_name
                                                ),
                                                style=rx.Style(
                                                    {
                                                        "background": "transparent",
                                                        "border": "none",
                                                        "cursor": "pointer",
                                                        "padding": "4px 8px",
                                                    }
                                                ),
                                            ),
                                            width="100%",
                                            align="center",
                                        ),
                                        padding="14px 16px",
                                        border=f"1px solid {Color.BORDER}",
                                        border_radius="10px",
                                        background_color=Color.SURFACE,
                                        width="100%",
                                    ),
                                    rx.cond(
                                        IPState.active_has_child_vms,
                                        rx.vstack(
                                            rx.hstack(
                                                rx.text(
                                                    f"{IPState.active_child_vms.length()} "
                                                    "VM berjalan di host ini",
                                                    font_size="13px",
                                                    font_weight=FontWeight.BOLD,
                                                    color=Color.TEXT,
                                                ),
                                                rx.spacer(),
                                                rx.el.button(
                                                    "+ Tambah VM",
                                                    type="button",
                                                    on_click=IPState.open_add_modal,
                                                    style=rx.Style(
                                                        {
                                                            "font_size": "12px",
                                                            "font_weight": FontWeight.BOLD,
                                                            "color": Color.ACCENT,
                                                            "background": "transparent",
                                                            "border": "none",
                                                            "cursor": "pointer",
                                                        }
                                                    ),
                                                    _hover=rx.Style(
                                                        {"text_decoration": "underline"}
                                                    ),
                                                ),
                                                width="100%",
                                                align="center",
                                            ),
                                            rx.vstack(
                                                rx.foreach(
                                                    IPState.active_child_vms,
                                                    lambda vm: rx.box(
                                                        rx.hstack(
                                                            rx.center(
                                                                rx.icon(
                                                                    tag="layers",
                                                                    size=14,
                                                                    color=Color.PURPLE_600,
                                                                ),
                                                                width="28px",
                                                                height="28px",
                                                                border_radius="6px",
                                                                background_color=Color.PURPLE_100,
                                                                flex_shrink="0",
                                                            ),
                                                            rx.vstack(
                                                                rx.text(
                                                                    vm["value"],
                                                                    font_size="13px",
                                                                    font_weight=FontWeight.BOLD,
                                                                    color=Color.TEXT,
                                                                ),
                                                                rx.text(
                                                                    vm["label"],
                                                                    font_size="11px",
                                                                    color=Color.MUTED,
                                                                    font_family="monospace",
                                                                ),
                                                                spacing="0",
                                                                align="start",
                                                            ),
                                                            rx.spacer(),
                                                            rx.icon(
                                                                tag="chevron-right",
                                                                size=14,
                                                                color=Color.MUTED,
                                                            ),
                                                            width="100%",
                                                            align="center",
                                                        ),
                                                        padding="10px 12px",
                                                        border=f"1px solid {Color.BORDER}",
                                                        border_radius="8px",
                                                        background_color=Color.SURFACE,
                                                        width="100%",
                                                        cursor="pointer",
                                                        on_click=lambda: (
                                                            IPState.open_detail_drawer_by_id(
                                                                vm["id"]
                                                            )
                                                        ),
                                                        _hover=rx.Style(
                                                            {
                                                                "border_color": Color.ACCENT,
                                                                "background_color": Color.SLATE_50,
                                                            }
                                                        ),
                                                    ),
                                                ),
                                                spacing="2",
                                                width="100%",
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        rx.box(
                                            rx.vstack(
                                                rx.text(
                                                    "Aset Fisik Standalone",
                                                    font_size="14px",
                                                    font_weight=FontWeight.BOLD,
                                                    color=Color.TEXT,
                                                ),
                                                rx.text(
                                                    "Belum ada Virtual Machine (VM) yang "
                                                    "dialokasikan berjalan di host fisik ini.",
                                                    font_size="13px",
                                                    color=Color.MUTED,
                                                    line_height="1.4",
                                                ),
                                                rx.el.button(
                                                    "+ Tambah VM",
                                                    type="button",
                                                    on_click=IPState.open_add_modal,
                                                    style=rx.Style(
                                                        {
                                                            "margin_top": "6px",
                                                            "height": "32px",
                                                            "padding": "0 14px",
                                                            "background_color": Color.INFO_BG,
                                                            "color": Color.ACCENT,
                                                            "border": (
                                                                f"1px solid {Color.BLUE_BORDER}"
                                                            ),
                                                            "border_radius": Radius.CONTROL,
                                                            "font_size": "12px",
                                                            "font_weight": FontWeight.BOLD,
                                                            "cursor": "pointer",
                                                        }
                                                    ),
                                                    _hover=rx.Style(
                                                        {"background_color": Color.BLUE_100}
                                                    ),
                                                ),
                                                spacing="1",
                                                align="start",
                                            ),
                                            padding="16px",
                                            border=f"1px solid {Color.BORDER}",
                                            border_radius="10px",
                                            background_color=Color.SURFACE,
                                            width="100%",
                                        ),
                                    ),
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            spacing="4",
                            width="100%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "RIWAYAT AKTIVITAS",
                                font_size=FontSize.GROUP_LABEL,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                letter_spacing="0.06em",
                            ),
                            rx.foreach(history_items, _history_row)
                            if history_items is not None
                            else rx.fragment(),
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
                # 4. Sticky Footer Tombol Aksi
                rx.hstack(
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="pencil", size=Size.ICON_SM, color=Color.WHITE),
                            rx.text(
                                "Edit",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.WHITE,
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
                                "background_color": Color.ACCENT,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                        _hover=rx.Style({"background_color": Color.ACCENT_BRIGHT}),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="copy", size=Size.ICON_SM, color=Color.ACCENT),
                            rx.text(
                                "Duplikat",
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
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": Radius.CONTROL,
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
                                "padding": "0 18px",
                                "background_color": Color.DANGER_BG,
                                "border": f"1px solid {Color.DANGER_BORDER}",
                                "border_radius": Radius.CONTROL,
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
                id="ip-detail-drawer",
                role="dialog",
                aria_modal="true",
                aria_label="Rincian IP & Server",
                tab_index=-1,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "0",
                        "right": "0",
                        "bottom": "0",
                        "width": "520px",
                        "background_color": Color.SURFACE,
                        "box_shadow": Shadow.DRAWER,
                        "display": "flex",
                        "flex_direction": "column",
                        "z_index": "70",
                        "outline": "none",
                        "@media (max-width: 639px)": {
                            "width": "100%",
                        },
                    }
                ),
            ),
            style=rx.Style({"position": "relative", "z_index": "60"}),
        ),
        rx.fragment(),
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
    history_items: Any = None,
    on_edit: Any = None,
    on_duplicate: Any = None,
    on_delete: Any = None,
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
    if section1_title == "Data entri IP":
        return _ip_detail_drawer(
            is_open=is_open,
            on_close=on_close,
            code_var=code_var,
            title_var=title_var,
            category_var=category_var,
            status_var=status_var,
            active_tab=active_tab,
            on_tab_change=on_tab_change,
            general_items=general_items,
            usage_items=usage_items,
            history_items=history_items,
            on_edit=on_edit,
            on_duplicate=on_duplicate,
            on_delete=on_delete,
            tabs=tabs,
        )

    tab1_key, tab1_label = tabs[0]
    tab2_key, tab2_label = tabs[1] if len(tabs) > 1 else ("", "")

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
                    )
                    if len(tabs) > 1
                    else rx.fragment(),
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
                            rx.foreach(history_items, _history_row)
                            if history_items is not None
                            else rx.fragment(),
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
