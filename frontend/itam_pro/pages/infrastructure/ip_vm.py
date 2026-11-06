"""
Halaman Infrastructure -> IP & Server (VM) (/infrastructure/ip).
Desain Baru:
- Tanpa kolom & tab Grup (Tab: Semua / Fisik / VM).
- 5 Kartu Statistik (Total IP gradasi navy->biru, Server Fisik & VM dengan bar proporsi,
  IP Bentrok & VM Tanpa Host dengan badge hijau 'Aman' bila 0).
- Modal Import 3 Langkah (.xlsx / .csv) & Dropdown Export (Excel .xlsx & PDF .pdf).
"""

from typing import Any

import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import ip_form_modal
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui import (
    TabItemConfig,
    app_tabs,
    detail_drawer,
)
from itam_pro.states.ip_state import IPState
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

IP_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "ip_address",
        "header": "IP Address",
        "width": "155px",
        "min_width": "145px",
        "render_type": "ip_address",
        "sticky_left": True,
        "sortable": True,
        "sort_key": "ip_address",
    },
    {
        "key": "nama",
        "header": "Nama Server / VM",
        "width": "225px",
        "min_width": "200px",
        "render_type": "name_with_sub",
        "sub_key": "sub_label",
        "sortable": True,
        "sort_key": "nama",
    },
    {
        "key": "jenis",
        "header": "Jenis",
        "width": "90px",
        "min_width": "85px",
        "render_type": "jenis_chip",
    },
    {
        "key": "host_display",
        "header": "Host",
        "width": "150px",
        "min_width": "130px",
        "render_type": "text",
    },
    {
        "key": "fungsi",
        "header": "Fungsi",
        "width": "250px",
        "min_width": "210px",
        "render_type": "text",
    },
    {
        "key": "os",
        "header": "OS",
        "width": "175px",
        "min_width": "155px",
        "render_type": "text",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "110px",
        "min_width": "100px",
        "render_type": "status_badge",
    },
]


def _ip_header() -> rx.Component:
    """Header halaman IP & Server (VM): ikon server 52x52,
    judul 28px, Import, Export, + Tambah IP."""
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(tag="server", size=26, color=Color.WHITE, stroke_width=2),
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
                    "IP & Server (VM)",
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.15",
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    (
                        "Pemetaan alamat IPv4 statis, server fisik, "
                        "dan mesin virtual (VM) lintas subnet."
                    ),
                    font_size=FontSize.BASE,
                    font_weight=FontWeight.REGULAR,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
        ),
        rx.hstack(
            # Tombol Import
            rx.el.button(
                rx.hstack(
                    rx.icon(tag="upload", size=16, color=Color.TEXT, stroke_width=2),
                    rx.text(
                        "Import",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                type="button",
                on_click=IPState.open_import_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 16px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "11px",
                        "font_family": FONT_FAMILY,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                        "transition": "all 0.15s ease",
                        "&:hover": {"background_color": Color.SURFACE_HOVER},
                    }
                ),
            ),
            # Menu Dropdown Export (Excel .xlsx & PDF .pdf)
            rx.menu.root(
                rx.menu.trigger(
                    rx.el.button(
                        rx.hstack(
                            rx.text(
                                "Export",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.TEXT,
                            ),
                            rx.icon(tag="chevron-down", size=16, color=Color.TEXT),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        style=rx.Style(
                            {
                                "height": "42px",
                                "padding": "0 16px",
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": "11px",
                                "font_family": FONT_FAMILY,
                                "cursor": "pointer",
                                "display": "inline-flex",
                                "align_items": "center",
                                "transition": "all 0.15s ease",
                                "&:hover": {"background_color": Color.SURFACE_HOVER},
                            }
                        ),
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        "Excel (.xlsx)",
                        on_click=IPState.export_excel,
                    ),
                    rx.menu.item(
                        "PDF (.pdf)",
                        on_click=IPState.export_pdf,
                    ),
                    align="end",
                ),
            ),
            # Tombol + Tambah IP
            rx.el.button(
                "+ Tambah IP",
                type="button",
                on_click=IPState.open_add_modal,
                style=rx.Style(
                    {
                        "height": "42px",
                        "padding": "0 20px",
                        "background": Color.GRADIENT_PRIMARY,
                        "color": Color.WHITE,
                        "border": "none",
                        "border_radius": "11px",
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "box_shadow": "0 6px 16px rgba(29, 78, 216, 0.28)",
                        "transition": "all 0.15s ease",
                    }
                ),
            ),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
            }
        ),
    )


def _total_ip_gradient_card() -> rx.Component:
    """Kartu 1: TOTAL IP (gradasi navy -> biru, teks putih)."""
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon(tag="globe", size=17, color=Color.WHITE, stroke_width=2),
                width="34px",
                height="34px",
                border_radius="10px",
                style=rx.Style({"background_color": "rgba(255, 255, 255, 0.16)"}),
            ),
            rx.text(
                "TOTAL IP",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color="rgba(255, 255, 255, 0.85)",
                letter_spacing="0.06em",
            ),
            spacing="3",
            align="center",
        ),
        rx.text(
            IPState.kpi_total_ip,
            font_size="34px",
            font_weight=FontWeight.EXTRABOLD,
            color=Color.WHITE,
            line_height="1.1",
            margin_top="6px",
        ),
        rx.text(
            "Seluruh entri terdaftar",
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color="rgba(255, 255, 255, 0.8)",
        ),
        spacing="2",
        align="start",
        padding="18px 20px",
        style=rx.Style(
            {
                "background": Color.GRADIENT_NAVY,
                "border_radius": "16px",
                "width": "100%",
                "box_shadow": "0 8px 20px rgba(15, 23, 42, 0.14)",
            }
        ),
    )


def _proportion_kpi_card(
    title: str,
    icon_tag: str,
    icon_bg: str,
    icon_color: str,
    value_var: Any,
    subtitle_var: Any,
    percent_var: Any,
    bar_color: str,
) -> rx.Component:
    """Kartu 2 & 3: Server Fisik & VM lengkap dengan bar proporsi."""
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon_tag, size=17, color=icon_color, stroke_width=2),
                width="34px",
                height="34px",
                background_color=icon_bg,
                border_radius="10px",
            ),
            rx.text(
                title,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            spacing="3",
            align="center",
        ),
        rx.text(
            value_var,
            font_size="34px",
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
            line_height="1.1",
            margin_top="4px",
        ),
        rx.text(
            subtitle_var,
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        # Bar proporsi
        rx.box(
            rx.box(
                style=rx.Style(
                    {
                        "width": f"{percent_var}%",
                        "height": "100%",
                        "background_color": bar_color,
                        "border_radius": Radius.FULL,
                        "transition": "width 0.3s ease",
                    }
                ),
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "6px",
                    "background_color": Color.SLATE_200,
                    "border_radius": Radius.FULL,
                    "overflow": "hidden",
                    "margin_top": "4px",
                }
            ),
        ),
        spacing="2",
        align="start",
        padding="18px 20px",
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "16px",
                "width": "100%",
            }
        ),
    )


def _health_kpi_card(
    title: str,
    icon_tag: str,
    icon_bg: str,
    icon_color: str,
    value_var: Any,
    subtitle: str,
    alert_label: str,
    alert_bg: str,
    alert_fg: str,
    on_click: Any = None,
) -> rx.Component:
    """Kartu 4 & 5: IP Bentrok & VM Tanpa Host dengan badge hijau 'Aman' jika nilai 0."""
    is_zero = value_var == 0
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon_tag, size=17, color=icon_color, stroke_width=2),
                width="34px",
                height="34px",
                background_color=icon_bg,
                border_radius="10px",
            ),
            rx.text(
                title,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            spacing="3",
            align="center",
        ),
        rx.hstack(
            rx.text(
                value_var,
                font_size="34px",
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.1",
            ),
            rx.box(
                rx.text(
                    rx.cond(is_zero, "Aman", alert_label),
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(is_zero, Color.GREEN_700, alert_fg),
                    line_height="1",
                ),
                style=rx.Style(
                    {
                        "padding": "4px 8px",
                        "border_radius": "6px",
                        "background_color": rx.cond(is_zero, Color.GREEN_100, alert_bg),
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
            ),
            spacing="3",
            align="center",
            margin_top="4px",
        ),
        rx.text(
            subtitle,
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        spacing="2",
        align="start",
        padding="18px 20px",
        on_click=on_click,
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "16px",
                "width": "100%",
                "cursor": "pointer" if on_click else "default",
            }
        ),
    )


def _ip_kpi_grid() -> rx.Component:
    """5 Kartu Statistik KPI (Grid 5 Kolom, Gap 16px)."""
    return rx.box(
        _total_ip_gradient_card(),
        _proportion_kpi_card(
            title="SERVER FISIK",
            icon_tag="monitor",
            icon_bg=Color.BLUE_50,
            icon_color=Color.BLUE_600,
            value_var=IPState.kpi_fisik,
            subtitle_var=IPState.fisik_subtitle,
            percent_var=IPState.fisik_percent,
            bar_color=Color.BLUE_600,
        ),
        _proportion_kpi_card(
            title="VM",
            icon_tag="layers",
            icon_bg=Color.PURPLE_50,
            icon_color=Color.PURPLE_600,
            value_var=IPState.kpi_vm,
            subtitle_var=IPState.vm_subtitle,
            percent_var=IPState.vm_percent,
            bar_color=Color.PURPLE_600,
        ),
        _health_kpi_card(
            title="IP BENTROK",
            icon_tag="triangle-alert",
            icon_bg=Color.RED_100,
            icon_color=Color.RED_600,
            value_var=IPState.kpi_bentrok,
            subtitle="Memakai IPv4 yang sama",
            alert_label="Perlu Cek",
            alert_bg=Color.RED_100,
            alert_fg=Color.RED_700,
            on_click=IPState.toggle_conflict_only,
        ),
        _health_kpi_card(
            title="VM TANPA HOST",
            icon_tag="unlink",
            icon_bg=Color.AMBER_100,
            icon_color=Color.AMBER_600,
            value_var=IPState.kpi_vm_tanpa_host,
            subtitle="Belum tertaut ke server fisik",
            alert_label="Perlu Tautan",
            alert_bg=Color.AMBER_100,
            alert_fg=Color.AMBER_700,
            on_click=IPState.toggle_orphan_vm_only,
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(5, 1fr)",
                "gap": "16px",
                "@media (max-width: 1200px)": {
                    "grid_template_columns": "repeat(3, 1fr)",
                },
                "@media (max-width: 768px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )


def _conflict_banner() -> rx.Component:
    """Banner informasi konflik IP jika ada alokasi bentrok."""
    return rx.cond(
        IPState.has_conflict_banner,
        rx.hstack(
            rx.icon(tag="triangle-alert", size=18, color=Color.DANGER_FG),
            rx.text(
                IPState.conflict_banner_text,
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.DANGER_FG,
            ),
            spacing="2",
            align="center",
            width="100%",
            padding="12px 16px",
            style=rx.Style(
                {
                    "background_color": Color.DANGER_BG,
                    "border": f"1px solid {Color.DANGER_BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        rx.fragment(),
    )


def _ip_tabs() -> rx.Component:
    """Tab filter utama: Semua, Fisik, VM."""
    return app_tabs(
        tabs=[
            TabItemConfig(
                key="Semua",
                label="Semua",
                count=IPState.kpi_total_ip,
            ),
            TabItemConfig(
                key="Fisik",
                label="Fisik",
                count=IPState.kpi_fisik,
            ),
            TabItemConfig(
                key="VM",
                label="VM",
                count=IPState.kpi_vm,
            ),
        ],
        active_tab=IPState.active_jenis_tab,
        on_change=IPState.set_jenis_tab,
    )


def _ip_filter_bar() -> rx.Component:
    """Bilah pencarian & dropdown filter: Jenis, Host, Subnet, Status."""
    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua jenis",
            "value": IPState.jenis_filter,
            "options": IPState.jenis_options,
            "on_change": IPState.set_jenis_filter,
        },
        {
            "label": "Semua host",
            "value": IPState.host_filter,
            "options": IPState.host_options,
            "on_change": IPState.set_host_filter,
        },
        {
            "label": "Semua subnet",
            "value": IPState.subnet_filter,
            "options": IPState.subnet_options,
            "on_change": IPState.set_subnet_filter,
        },
        {
            "label": "Semua status",
            "value": IPState.status_filter,
            "options": IPState.status_options,
            "on_change": IPState.set_status_filter,
        },
    ]
    return table_filter_bar(
        search_value=IPState.search_query,
        on_search_change=IPState.set_search_query,
        search_placeholder="Cari IP, nama, fungsi, OS, keterangan...",
        dropdowns=dropdowns,
        on_reset=IPState.reset_filters,
        result_count_text=IPState.result_count_label,
    )


def _ip_import_modal() -> rx.Component:
    """Modal Import 3 Langkah: Unduh template, Aturan pengisian, Dropzone upload + Preview."""
    return rx.cond(
        IPState.import_modal_open,
        rx.box(
            # Scrim
            rx.box(
                on_click=IPState.close_import_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            # Kartu Modal
            rx.box(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            "Import Data IP & Server (VM)",
                            font_size="20px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            (
                                "Unggah data inventaris alamat IP dan server "
                                "dalam format .xlsx atau .csv."
                            ),
                            font_size=FontSize.SM,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        on_click=IPState.close_import_modal,
                        style=rx.Style(
                            {
                                "width": "34px",
                                "height": "34px",
                                "background_color": Color.TABLE_HEADER_BG,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": Radius.CONTROL,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="start",
                    padding="22px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body 3 Langkah
                rx.box(
                    rx.vstack(
                        # Langkah 1: Unduh Template
                        rx.box(
                            rx.hstack(
                                rx.center(
                                    rx.text("1", font_weight=FontWeight.BOLD, color=Color.WHITE),
                                    width="28px",
                                    height="28px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.ACCENT,
                                    flex_shrink="0",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Unduh Template Resmi",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    rx.text(
                                        (
                                            "Gunakan file Excel (.xlsx) dengan "
                                            "dropdown validasi Jenis & Status."
                                        ),
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                rx.el.button(
                                    rx.hstack(
                                        rx.icon(tag="download", size=14, color=Color.ACCENT),
                                        rx.text(
                                            "Unduh Template .xlsx",
                                            font_size=FontSize.XS,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.ACCENT,
                                        ),
                                        spacing="1",
                                        align="center",
                                    ),
                                    type="button",
                                    on_click=IPState.download_import_template,
                                    style=rx.Style(
                                        {
                                            "padding": "6px 14px",
                                            "background_color": Color.BLUE_50,
                                            "border": f"1px solid {Color.BLUE_BORDER}",
                                            "border_radius": "8px",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                width="100%",
                                justify="between",
                                align="center",
                            ),
                            padding="14px 16px",
                            style=rx.Style(
                                {
                                    "background_color": Color.SLATE_50,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": "12px",
                                    "width": "100%",
                                }
                            ),
                        ),
                        # Langkah 2: Aturan Pengisian Data
                        rx.box(
                            rx.hstack(
                                rx.center(
                                    rx.text("2", font_weight=FontWeight.BOLD, color=Color.WHITE),
                                    width="28px",
                                    height="28px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.ACCENT,
                                    flex_shrink="0",
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Aturan Pengisian",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    rx.text(
                                        "• IPv4 valid & tidak boleh duplikat (statis).",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    rx.text(
                                        "• Jenis hanya 'Fisik' atau 'VM'.",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    rx.text(
                                        "• Host Server Fisik wajib diisi jika Jenis adalah VM.",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                spacing="3",
                                align="start",
                            ),
                            padding="14px 16px",
                            style=rx.Style(
                                {
                                    "background_color": Color.SLATE_50,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": "12px",
                                    "width": "100%",
                                }
                            ),
                        ),
                        # Langkah 3: Dropzone Upload
                        rx.box(
                            rx.hstack(
                                rx.center(
                                    rx.text("3", font_weight=FontWeight.BOLD, color=Color.WHITE),
                                    width="28px",
                                    height="28px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.ACCENT,
                                    flex_shrink="0",
                                ),
                                rx.text(
                                    "Unggah File .xlsx atau .csv (maks 5 MB)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                spacing="3",
                                align="center",
                            ),
                            rx.box(
                                rx.upload(
                                    rx.vstack(
                                        rx.icon(tag="cloud-upload", size=32, color=Color.ACCENT),
                                        rx.text(
                                            (
                                                "Klik atau seret file spreadsheet "
                                                "(.xlsx / .csv) ke sini"
                                            ),
                                            font_size=FontSize.SM,
                                            font_weight=FontWeight.MEDIUM,
                                            color=Color.TEXT,
                                        ),
                                        rx.text(
                                            "Batas ukuran file: 5 MB",
                                            font_size=FontSize.XS,
                                            color=Color.MUTED,
                                        ),
                                        spacing="1",
                                        align="center",
                                    ),
                                    id="ip_import_upload_box",
                                    border=f"2px dashed {Color.ACCENT}",
                                    padding="24px",
                                    border_radius="12px",
                                    background_color=Color.SLATE_50,
                                    cursor="pointer",
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.el.button(
                                        "Periksa & Validasi File",
                                        type="button",
                                        on_click=IPState.handle_import_upload(
                                            rx.upload_files(upload_id="ip_import_upload_box")
                                        ),
                                        style=rx.Style(
                                            {
                                                "height": "36px",
                                                "padding": "0 18px",
                                                "background_color": Color.ACCENT,
                                                "color": Color.WHITE,
                                                "border": "none",
                                                "border_radius": "8px",
                                                "font_family": FONT_FAMILY,
                                                "font_size": FontSize.SM,
                                                "font_weight": FontWeight.BOLD,
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                    justify="end",
                                    width="100%",
                                    margin_top="10px",
                                ),
                                width="100%",
                                margin_top="10px",
                            ),
                            padding="14px 16px",
                            style=rx.Style(
                                {
                                    "background_color": Color.SLATE_50,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": "12px",
                                    "width": "100%",
                                }
                            ),
                        ),
                        # Banner Hasil Validasi Preview
                        rx.cond(
                            IPState.import_has_preview,
                            rx.vstack(
                                rx.hstack(
                                    rx.icon(
                                        tag=rx.cond(
                                            IPState.import_error_count > 0,
                                            "triangle-alert",
                                            "check-circle-2",
                                        ),
                                        size=18,
                                        color=rx.cond(
                                            IPState.import_error_count > 0,
                                            Color.AMBER_700,
                                            Color.GREEN_700,
                                        ),
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            IPState.import_summary_text,
                                            font_size=FontSize.SM,
                                            font_weight=FontWeight.BOLD,
                                            color=rx.cond(
                                                IPState.import_error_count > 0,
                                                Color.AMBER_800,
                                                Color.GREEN_800,
                                            ),
                                        ),
                                        rx.text(
                                            IPState.import_error_detail_text,
                                            font_size=FontSize.XS,
                                            color=rx.cond(
                                                IPState.import_error_count > 0,
                                                Color.AMBER_700,
                                                Color.GREEN_700,
                                            ),
                                        ),
                                        spacing="0",
                                        align="start",
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.cond(
                                    IPState.import_error_count > 0,
                                    rx.el.button(
                                        "Unduh Laporan Error (.csv)",
                                        type="button",
                                        on_click=IPState.download_import_error_report,
                                        style=rx.Style(
                                            {
                                                "font_size": FontSize.XS,
                                                "font_weight": FontWeight.BOLD,
                                                "color": Color.AMBER_700,
                                                "background": "transparent",
                                                "border": "none",
                                                "cursor": "pointer",
                                                "padding": "0",
                                                "text_decoration": "underline",
                                            }
                                        ),
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                                padding="12px 16px",
                                style=rx.Style(
                                    {
                                        "background_color": rx.cond(
                                            IPState.import_error_count > 0,
                                            Color.AMBER_100,
                                            Color.GREEN_100,
                                        ),
                                        "border": rx.cond(
                                            IPState.import_error_count > 0,
                                            f"1px solid {Color.AMBER_BORDER}",
                                            f"1px solid {Color.GREEN_BORDER}",
                                        ),
                                        "border_radius": "10px",
                                    }
                                ),
                            ),
                            rx.fragment(),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 148px)",
                        }
                    ),
                ),
                # Footer Modal
                rx.hstack(
                    rx.el.button(
                        "Tutup",
                        type="button",
                        on_click=IPState.close_import_modal,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "background_color": Color.SURFACE,
                                "color": Color.TEXT,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": "10px",
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.cond(
                        IPState.import_valid_count > 0,
                        rx.el.button(
                            IPState.import_button_label,
                            type="button",
                            on_click=IPState.commit_import_data,
                            style=rx.Style(
                                {
                                    "height": "40px",
                                    "padding": "0 22px",
                                    "background": (Color.GRADIENT_PRIMARY),
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": "10px",
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                    "box_shadow": "0 4px 12px rgba(29, 78, 216, 0.25)",
                                }
                            ),
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    justify="end",
                    align="center",
                    width="100%",
                    padding="16px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SLATE_50,
                        }
                    ),
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "94%",
                        "max_width": "640px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": "16px",
                        "box_shadow": Shadow.POPOVER,
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def ip_vm_page() -> rx.Component:
    """Tampilan utama halaman `/infrastructure/ip` (IP & Server (VM))."""
    content = rx.vstack(
        _ip_header(),
        _ip_kpi_grid(),
        _conflict_banner(),
        # Kontainer Tabel Data
        rx.box(
            _ip_tabs(),
            _ip_filter_bar(),
            reusable_data_table(
                columns=IP_TABLE_COLUMNS,
                rows=IPState.items,
                id_key="id",
                selected_ids=IPState.selected_ids,
                active_row_id=IPState.active_entry_id,
                all_selected=IPState.all_current_selected,
                is_loading=IPState.is_loading,
                on_toggle_all=IPState.toggle_select_all,
                on_toggle_row=IPState.toggle_row_selection,
                on_row_click=IPState.open_drawer,
                on_edit_row=IPState.open_edit_modal,
                on_duplicate_row=IPState.open_duplicate_modal,
                on_delete_row=IPState.confirm_delete_entry,
                sort_by=IPState.sort_by,
                sort_dir=IPState.sort_dir,
                on_sort=IPState.toggle_sort,
                on_reset_filter=IPState.reset_filters,
                duplicate_action_label="Duplikat IP",
            ),
            table_pagination(
                summary_text=IPState.pagination_summary,
                current_page=IPState.page,
                current_page_str=IPState.current_page_str,
                total_pages=IPState.total_pages,
                page_tokens=IPState.page_tokens,
                on_prev=IPState.prev_page,
                on_next=IPState.next_page,
                on_page_select=IPState.select_page,
            ),
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": "16px",
                    "overflow": "hidden",
                    "width": "100%",
                }
            ),
        ),
        # Drawer Detail
        detail_drawer(
            is_open=IPState.drawer_open,
            on_close=IPState.close_drawer,
            code_var=IPState.active_ip_code,
            title_var=IPState.active_nama_title,
            category_var=IPState.active_jenis_badge,
            status_var=IPState.active_status_badge,
            active_tab=IPState.drawer_tab,
            on_tab_change=IPState.set_drawer_tab,
            section1_title="Data entri IP",
            general_items=IPState.active_general_items,
            section2_title="Aset fisik & daftar VM host",
            usage_items=IPState.active_relation_items,
            history_items=IPState.active_history_items,
            duplicate_label="Duplikat",
            on_edit=lambda: IPState.open_edit_modal(""),
            on_duplicate=lambda: IPState.open_duplicate_modal(""),
            on_delete=lambda: IPState.confirm_delete_entry(""),
            tabs=(
                ("detail", "Rincian IP & Host"),
                ("history", "Riwayat & Log"),
            ),
        ),
        # Modals
        ip_form_modal(),
        _ip_import_modal(),
        confirm_delete_dialog(
            is_open=IPState.delete_dialog_open,
            title="Hapus Entri IP?",
            description=(
                f"Apakah Anda yakin ingin menghapus entri {IPState.entry_to_delete_label}? "
                "Tindakan ini akan dicatat pada Audit Log."
            ),
            on_cancel=IPState.cancel_delete,
            on_confirm=IPState.execute_delete_entry,
        ),
        spacing="5",
        width="100%",
    )

    return base_layout(
        content=content,
        breadcrumb=("Infrastructure", "IP & Server (VM)"),
    )


__all__ = ["IP_TABLE_COLUMNS", "ip_vm_page"]
