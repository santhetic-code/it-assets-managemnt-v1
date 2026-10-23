"""
Halaman Infrastructure -> IP & Server (VM) (/infrastructure/ip).
Menggunakan komponen reusable generik tanpa membuat komponen tabel baru.
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
    action_primary_button,
    app_tabs,
    detail_drawer,
    secondary_button,
)
from itam_pro.states.ip_state import IPState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space

IP_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "ip_address",
        "header": "IP Address",
        "width": "175px",
        "min_width": "165px",
        "render_type": "ip_address",
        "sticky_left": True,
        "sortable": True,
        "sort_key": "ip_address",
    },
    {
        "key": "nama",
        "header": "Nama Server / VM",
        "width": "200px",
        "min_width": "185px",
        "render_type": "name_with_sub",
        "sub_key": "sub_label",
        "sortable": True,
        "sort_key": "nama",
    },
    {
        "key": "jenis",
        "header": "Jenis",
        "width": "95px",
        "min_width": "90px",
        "render_type": "chip",
    },
    {
        "key": "host_label",
        "header": "Host",
        "width": "205px",
        "min_width": "195px",
        "render_type": "chip",
    },
    {
        "key": "fungsi",
        "header": "Fungsi",
        "width": "220px",
        "min_width": "190px",
        "render_type": "text",
    },
    {
        "key": "os",
        "header": "OS",
        "width": "170px",
        "min_width": "150px",
        "render_type": "text",
    },
    {
        "key": "grup",
        "header": "Grup",
        "width": "130px",
        "min_width": "120px",
        "render_type": "badge",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "110px",
        "min_width": "105px",
        "render_type": "status_badge",
    },
]


def _ip_header() -> rx.Component:
    """Header halaman IP & Server (VM) dengan tombol Import CSV, Export, dan + Tambah IP."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "IP & Server (VM)",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Pemetaan alamat IPv4 statis, server fisik, dan mesin virtual (VM) lintas subnet.",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.hstack(
            secondary_button(
                label="Import CSV",
                on_click=rx.toast.info("Fitur Import CSV sedang disiapkan"),
            ),
            secondary_button(
                label="Export",
                on_click=rx.toast.info("Fitur Export sedang disiapkan"),
            ),
            action_primary_button(
                label="+ Tambah IP",
                on_click=IPState.open_add_modal,
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


def _kpi_mini_card(
    label: str,
    value_var: Any,
    subtitle: str,
    tone: str = "default",
) -> rx.Component:
    """Kartu ringkasan KPI untuk barisan 5 kolom di atas tabel IP."""
    val_color = {
        "danger": Color.DANGER_FG,
        "warning": Color.WARNING_FG,
        "accent": Color.ACCENT,
    }.get(tone, Color.TEXT)

    return rx.vstack(
        rx.text(
            label,
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            style=rx.Style({"text_transform": "uppercase", "letter_spacing": "0.04em"}),
        ),
        rx.text(
            value_var,
            font_size=FontSize.KPI_VALUE,
            font_weight=FontWeight.EXTRABOLD,
            color=val_color,
            line_height="1.15",
        ),
        rx.text(
            subtitle,
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.MEDIUM,
            color=Color.MUTED,
        ),
        spacing="1",
        align="start",
        padding="16px 20px",
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "width": "100%",
            }
        ),
    )


def _ip_kpi_row() -> rx.Component:
    """Baris 5 Kartu KPI: Total IP, Operasional, Addon (VM), IP bentrok, VM tanpa host."""
    return rx.box(
        _kpi_mini_card("Total IP", IPState.kpi_total_ip, "Seluruh entri terdaftar"),
        _kpi_mini_card(
            "Operasional",
            IPState.kpi_operasional,
            "Infrastruktur & produksi",
            tone="accent",
        ),
        _kpi_mini_card("Addon (VM)", IPState.kpi_addon, "Worker modul transaksi"),
        _kpi_mini_card(
            "IP Bentrok",
            IPState.kpi_bentrok,
            "Memakai IPv4 yang sama",
            tone="danger",
        ),
        _kpi_mini_card(
            "VM Tanpa Host",
            IPState.kpi_vm_tanpa_host,
            "Belum tertaut ke server fisik",
            tone="warning",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(5, minmax(0, 1fr))",
                "gap": Space.S4,
                "@media (max-width: 1100px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))",
                },
            }
        ),
    )


def _conflict_banner() -> rx.Component:
    """Banner merah peringatan IP bentrok di atas tabel dengan tombol filter 'Tampilkan'."""
    return rx.cond(
        IPState.has_conflict_banner,
        rx.hstack(
            rx.hstack(
                rx.icon(tag="triangle-alert", size=18, color=Color.DANGER_FG),
                rx.text(
                    IPState.conflict_banner_text,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.DANGER_FG,
                ),
                spacing="3",
                align="center",
            ),
            rx.el.button(
                rx.cond(
                    IPState.only_conflict_filter,
                    "Tampilkan Semua",
                    "Tampilkan",
                ),
                type="button",
                on_click=IPState.toggle_conflict_only,
                style=rx.Style(
                    {
                        "height": "34px",
                        "padding": "0 14px",
                        "background_color": Color.SURFACE,
                        "color": Color.DANGER_FG,
                        "border": f"1px solid {Color.DANGER_FG}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.XS,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
            ),
            width="100%",
            justify="between",
            align="center",
            padding="12px 18px",
            style=rx.Style(
                {
                    "background_color": Color.DANGER_BG,
                    "border": f"1px solid {Color.DANGER_FG}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        rx.fragment(),
    )


def _ip_table_card() -> rx.Component:
    """Kartu pembungkus Tabs + Filter Bar + Reusable Data Table + Pagination."""
    tabs_config: list[TabItemConfig] = [
        {"key": "Semua", "label": "Semua", "count": IPState.kpi_total_ip},
        {"key": "Operasional", "label": "Operasional", "count": IPState.kpi_operasional},
        {"key": "Addon (VM)", "label": "Addon (VM)", "count": IPState.kpi_addon},
    ]

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

    return rx.box(
        app_tabs(
            tabs=tabs_config,
            active_tab=IPState.active_grup_tab,
            on_change=IPState.set_grup_tab,
        ),
        table_filter_bar(
            search_value=IPState.search_query,
            on_search_change=IPState.set_search_query,
            search_placeholder="Cari IP address, nama server/VM, fungsi...",
            dropdowns=dropdowns,
            on_reset=IPState.reset_filters,
            result_count_text=IPState.result_count_label,
        ),
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
            duplicate_action_label="Duplikat",
            on_delete_row=IPState.confirm_delete_entry,
            on_reset_filter=IPState.reset_filters,
            sort_by=IPState.sort_by,
            sort_dir=IPState.sort_dir,
            on_sort=IPState.toggle_sort,
            empty_message="Tidak ada entri IP yang cocok",
            empty_subtitle="Coba ubah kata kunci pencarian atau reset filter subnet/host.",
            empty_action_label="Reset filter",
            on_empty_action=IPState.reset_filters,
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
                "width": "100%",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "overflow": "hidden",
            }
        ),
    )


def ip_vm_page() -> rx.Component:
    """Halaman utama `/infrastructure/ip`."""
    content = rx.vstack(
        _ip_header(),
        _ip_kpi_row(),
        _conflict_banner(),
        _ip_table_card(),
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
        ip_form_modal(),
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
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Infrastructure", "IP & Server (VM)"),
    )


__all__ = ["IP_TABLE_COLUMNS", "ip_vm_page"]
