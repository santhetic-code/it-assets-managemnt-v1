"""
Halaman Tunggal Generik Inventaris Aset ITAM Pro (Tahap 6c-1).
Melayani route `/assets` (Semua Aset) dan `/assets/c/[slug]` (View per Kategori).
"""

from typing import Any, cast

import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import asset_form_modal
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui import (
    action_primary_button,
    detail_drawer,
    secondary_button,
)
from itam_pro.services.category_config import (
    build_column_toggle_options,
    build_table_columns_for_slug,
)
from itam_pro.states.asset_state import AssetState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space

ALL_ASSETS_COLUMNS = build_table_columns_for_slug("")
PC_VIEW_COLUMNS = build_table_columns_for_slug("pc")
SERVER_VIEW_COLUMNS = build_table_columns_for_slug("server")
MONITOR_VIEW_COLUMNS = build_table_columns_for_slug("monitor")
UPS_VIEW_COLUMNS = build_table_columns_for_slug("ups")

ALL_ASSETS_COL_OPTIONS = build_column_toggle_options("")
PC_COL_OPTIONS = build_column_toggle_options("pc")
SERVER_COL_OPTIONS = build_column_toggle_options("server")
MONITOR_COL_OPTIONS = build_column_toggle_options("monitor")
UPS_COL_OPTIONS = build_column_toggle_options("ups")


def _inventory_header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(tag="layout-grid", size=24, color=Color.WHITE),
                width="48px",
                height="48px",
                background_color=Color.ACCENT_BRIGHT,
                border_radius=Radius.CARD,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.heading(
                    AssetState.page_title,
                    font_size=FontSize.TITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.2",
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    (
                        "Satu daftar induk untuk seluruh aset perusahaan. "
                        "Halaman kategori hanyalah filter dari sini."
                    ),
                    font_size=FontSize.BASE,
                    font_weight=FontWeight.REGULAR,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        rx.hstack(
            secondary_button(
                label="Export",
                on_click=rx.toast.info("Fitur Export sedang disiapkan"),
            ),
            secondary_button(
                label="Import",
                on_click=rx.toast.info("Fitur Import Aset sedang disiapkan"),
            ),
            action_primary_button(
                label=AssetState.add_button_label,
                on_click=AssetState.open_add_modal,
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


def _kpi_filter_card(
    card_key: str,
    title: str,
    count_val: rx.Var,
    subtitle: str,
    action_text: str,
    icon_tag: str,
    icon_color: str,
    icon_bg: str,
) -> rx.Component:
    is_selected = AssetState.active_kpi_card == card_key
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(
                        tag=icon_tag,
                        size=16,
                        color=rx.cond(is_selected, Color.WHITE, icon_color),
                    ),
                    width="30px",
                    height="30px",
                    border_radius="8px",
                    background_color=rx.cond(is_selected, "rgba(255,255,255,0.18)", icon_bg),
                ),
                rx.text(
                    title,
                    font_size=FontSize.GROUP_LABEL,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(is_selected, "rgba(255,255,255,0.85)", Color.MUTED),
                    letter_spacing="0.06em",
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                count_val,
                font_size="30px",
                font_weight=FontWeight.EXTRABOLD,
                color=rx.cond(is_selected, Color.WHITE, Color.TEXT),
                line_height="1.1",
            ),
            rx.text(
                subtitle,
                font_size=FontSize.XS,
                color=rx.cond(is_selected, "rgba(255,255,255,0.8)", Color.MUTED),
            ),
            rx.text(
                action_text,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=rx.cond(is_selected, Color.WHITE, Color.ACCENT),
                padding_top="4px",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        on_click=AssetState.select_kpi_card(card_key),
        style=rx.Style(
            {
                "padding": "18px 20px",
                "border_radius": Radius.CARD,
                "background_color": rx.cond(is_selected, Color.BACKUP_FG, Color.SURFACE),
                "border": rx.cond(
                    is_selected,
                    f"2px solid {Color.BACKUP_FG}",
                    f"1px solid {Color.BORDER}",
                ),
                "cursor": "pointer",
                "transition": "all 0.15s ease",
            }
        ),
    )


def _four_kpi_cards_row() -> rx.Component:
    """Empat kartu KPI yang bisa diklik sesuai Artboard 10."""
    return rx.box(
        _kpi_filter_card(
            "total",
            "TOTAL ASET",
            AssetState.summary_counts["total"],
            "di semua kategori",
            "Lihat semua →",
            "layout-grid",
            Color.ACCENT,
            Color.INFO_BG,
        ),
        _kpi_filter_card(
            "attention",
            "PERLU PERHATIAN",
            AssetState.summary_counts["perlu_perhatian"],
            "Rusak atau dalam perbaikan",
            "Lihat daftar →",
            "triangle-alert",
            Color.DANGER_FG,
            Color.DANGER_BG,
        ),
        _kpi_filter_card(
            "warranty",
            "GARANSI SEGERA HABIS",
            AssetState.summary_counts["garansi_segera_habis"],
            "Berakhir ≤ 30 hari",
            "Lihat daftar →",
            "clock",
            Color.WARNING_FG,
            Color.WARNING_BG,
        ),
        _kpi_filter_card(
            "no_purchase",
            "BELUM TERHUBUNG PEMBELIAN",
            AssetState.summary_counts["belum_terhubung_pembelian"],
            "Belum punya invoice sumber",
            "Lengkapi data →",
            "receipt",
            Color.ACCENT,
            Color.INFO_BG,
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(auto-fit, minmax(220px, 1fr))",
                "gap": Space.S4,
            }
        ),
    )


def _category_group_chip(group_key: str, label: str, icon_tag: str, count_key: str) -> rx.Component:
    is_active = AssetState.active_group == group_key
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon_tag, size=16, color=Color.ACCENT),
                width="32px",
                height="32px",
                border_radius="8px",
                background_color=Color.INFO_BG,
            ),
            rx.vstack(
                rx.text(
                    label,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                    line_height="1.15",
                ),
                rx.text(
                    f"{AssetState.sidebar_counts[count_key]} aset",
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        on_click=AssetState.select_category_group(group_key),
        style=rx.Style(
            {
                "padding": "10px 14px",
                "border_radius": Radius.CARD,
                "background_color": Color.SURFACE,
                "border": rx.cond(
                    is_active,
                    f"2px solid {Color.ACCENT_BRIGHT}",
                    f"1px solid {Color.BORDER}",
                ),
                "cursor": "pointer",
            }
        ),
    )


def _subcategory_pill(slug_val: str, label: str, count_var: Any) -> rx.Component:
    is_active = AssetState.current_slug == slug_val
    return rx.box(
        rx.text(
            f"{label} {count_var}",
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=rx.cond(is_active, Color.ACCENT, Color.TEXT),
        ),
        on_click=AssetState.select_subcategory(slug_val),
        style=rx.Style(
            {
                "padding": "6px 14px",
                "border_radius": Radius.FULL,
                "background_color": rx.cond(is_active, Color.INFO_BG, Color.SURFACE),
                "border": rx.cond(
                    is_active,
                    f"1px solid {Color.ACCENT}",
                    f"1px solid {Color.BORDER}",
                ),
                "cursor": "pointer",
            }
        ),
    )


def _category_hierarchy_bars() -> rx.Component:
    """Baris kategori utama dan subkategori sesuai Artboard 10."""
    return rx.vstack(
        rx.box(
            _category_group_chip("all", "Semua", "layout-grid", "all"),
            _category_group_chip("perangkat-it", "Perangkat IT", "monitor", "perangkat-it"),
            _category_group_chip(
                "komponen-periferal", "Komponen & Periferal", "cpu", "komponen-periferal"
            ),
            _category_group_chip("jaringan", "Jaringan", "network", "jaringan"),
            _category_group_chip("kendaraan", "Kendaraan", "car", "kendaraan"),
            _category_group_chip(
                "peralatan-kantor", "Peralatan Kantor", "air-vent", "peralatan-kantor"
            ),
            _category_group_chip("furnitur", "Furnitur", "armchair", "furnitur"),
            _category_group_chip("lainnya", "Lainnya", "box", "lainnya"),
            style=rx.Style(
                {
                    "width": "100%",
                    "display": "grid",
                    "grid_template_columns": "repeat(auto-fit, minmax(145px, 1fr))",
                    "gap": "10px",
                }
            ),
        ),
        rx.hstack(
            rx.text(
                "Perangkat IT ›",
                font_size=FontSize.XS,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.MUTED,
            ),
            _subcategory_pill("", "Semua Perangkat IT", AssetState.sidebar_counts["perangkat-it"]),
            _subcategory_pill("pc", "PC & Laptop", AssetState.sidebar_counts["pc"]),
            _subcategory_pill("server", "Server", AssetState.sidebar_counts["server"]),
            _subcategory_pill("monitor", "Monitor", AssetState.sidebar_counts["monitor"]),
            _subcategory_pill("ups", "UPS", AssetState.sidebar_counts["ups"]),
            spacing="2",
            align="center",
            wrap="wrap",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _filter_bar_by_slug() -> rx.Component:
    """Bangun Filter Bar dinamis dari field filterable kategori + Lokasi & Kepemilikan."""
    all_dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua kategori",
            "value": AssetState.kategori_filter,
            "options": AssetState.master_kategori_options,
            "on_change": AssetState.set_kategori_filter,
        },
        {
            "label": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
        {
            "label": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "label": "Semua kondisi",
            "value": AssetState.kondisi_filter,
            "options": AssetState.master_kondisi_options,
            "on_change": AssetState.set_kondisi_filter,
        },
        {
            "label": "Semua status",
            "value": AssetState.status_filter,
            "options": AssetState.master_status_options,
            "on_change": AssetState.set_status_filter,
        },
    ]

    pc_dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua OS",
            "value": AssetState.filter_os_value,
            "options": AssetState.os_filter_options,
            "on_change": lambda v: AssetState.set_attr_filter("os", v),
        },
        {
            "label": "Semua RAM",
            "value": AssetState.filter_ram_value,
            "options": AssetState.ram_filter_options,
            "on_change": lambda v: AssetState.set_attr_filter("ram", v),
        },
        {
            "label": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "label": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
    ]

    monitor_dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua merk",
            "value": AssetState.filter_merk_value,
            "options": AssetState.master_merk_options,
            "on_change": lambda v: AssetState.set_attr_filter("merk", v),
        },
        {
            "label": "Semua ukuran",
            "value": AssetState.filter_ukuran_value,
            "options": AssetState.master_ukuran_options,
            "on_change": lambda v: AssetState.set_attr_filter("ukuran_layar", v),
        },
        {
            "label": "Semua resolusi",
            "value": AssetState.filter_resolusi_value,
            "options": AssetState.master_resolusi_options,
            "on_change": lambda v: AssetState.set_attr_filter("resolusi_layar", v),
        },
        {
            "label": "Semua konektivitas",
            "value": AssetState.filter_konektivitas_value,
            "options": AssetState.master_konektivitas_options,
            "on_change": lambda v: AssetState.set_attr_filter("konektivitas", v),
        },
        {
            "label": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "label": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
    ]

    default_cat_dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "label": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
        {
            "label": "Semua kondisi",
            "value": AssetState.kondisi_filter,
            "options": AssetState.master_kondisi_options,
            "on_change": AssetState.set_kondisi_filter,
        },
        {
            "label": "Semua status",
            "value": AssetState.status_filter,
            "options": AssetState.master_status_options,
            "on_change": AssetState.set_status_filter,
        },
    ]

    return cast(
        rx.Component,
        rx.match(
            AssetState.current_slug,
            (
                "",
                table_filter_bar(
                    search_value=AssetState.search_query,
                    on_search_change=AssetState.set_search_query,
                    search_placeholder="Cari ID aset, nama aset, SN/PID, pemakai...",
                    dropdowns=all_dropdowns,
                    on_reset=AssetState.reset_filters,
                    result_count_text=AssetState.result_count_label,
                    column_options=ALL_ASSETS_COL_OPTIONS,
                    hidden_columns=AssetState.hidden_columns,
                    on_toggle_column=AssetState.toggle_column_visibility,
                    on_reset_columns=AssetState.reset_column_visibility,
                ),
            ),
            (
                "pc",
                table_filter_bar(
                    search_value=AssetState.search_query,
                    on_search_change=AssetState.set_search_query,
                    search_placeholder="Cari hostname PC, user, CPU, OS...",
                    dropdowns=pc_dropdowns,
                    on_reset=AssetState.reset_filters,
                    result_count_text=AssetState.result_count_label,
                    column_options=PC_COL_OPTIONS,
                    hidden_columns=AssetState.hidden_columns,
                    on_toggle_column=AssetState.toggle_column_visibility,
                    on_reset_columns=AssetState.reset_column_visibility,
                ),
            ),
            (
                "monitor",
                table_filter_bar(
                    search_value=AssetState.search_query,
                    on_search_change=AssetState.set_search_query,
                    search_placeholder="Cari ID aset, merk, tipe monitor...",
                    dropdowns=monitor_dropdowns,
                    on_reset=AssetState.reset_filters,
                    result_count_text=AssetState.result_count_label,
                    column_options=MONITOR_COL_OPTIONS,
                    hidden_columns=AssetState.hidden_columns,
                    on_toggle_column=AssetState.toggle_column_visibility,
                    on_reset_columns=AssetState.reset_column_visibility,
                ),
            ),
            table_filter_bar(
                search_value=AssetState.search_query,
                on_search_change=AssetState.set_search_query,
                search_placeholder="Cari ID aset, nama unit, SN/PID...",
                dropdowns=default_cat_dropdowns,
                on_reset=AssetState.reset_filters,
                result_count_text=AssetState.result_count_label,
                column_options=ALL_ASSETS_COL_OPTIONS,
                hidden_columns=AssetState.hidden_columns,
                on_toggle_column=AssetState.toggle_column_visibility,
                on_reset_columns=AssetState.reset_column_visibility,
            ),
        ),
    )


def _table_by_slug() -> rx.Component:
    """Render reusable_data_table dengan kolom dasar + kolom schema kategori."""

    def _build_table(cols: list) -> rx.Component:
        return reusable_data_table(
            columns=cols,
            rows=AssetState.items,
            id_key="id_aset",
            selected_ids=AssetState.selected_ids,
            active_row_id=AssetState.active_asset_id,
            all_selected=AssetState.all_current_selected,
            is_loading=AssetState.is_loading,
            on_toggle_all=AssetState.toggle_select_all,
            on_toggle_row=AssetState.toggle_row_selection,
            on_row_click=AssetState.open_drawer,
            on_edit_row=AssetState.open_edit_modal,
            on_duplicate_row=AssetState.open_duplicate_modal,
            on_delete_row=AssetState.confirm_delete_asset,
            on_reset_filter=AssetState.reset_filters,
            sort_by=AssetState.sort_by,
            sort_dir=AssetState.sort_dir,
            on_sort=AssetState.toggle_sort,
            hidden_columns=AssetState.hidden_columns,
            empty_message=AssetState.empty_state_title,
            empty_subtitle=AssetState.empty_state_subtitle,
            empty_action_label=AssetState.empty_state_action_label,
            on_empty_action=AssetState.reset_filters,
        )

    return cast(
        rx.Component,
        rx.match(
            AssetState.current_slug,
            ("pc", _build_table(PC_VIEW_COLUMNS)),
            ("server", _build_table(SERVER_VIEW_COLUMNS)),
            ("monitor", _build_table(MONITOR_VIEW_COLUMNS)),
            ("ups", _build_table(UPS_VIEW_COLUMNS)),
            _build_table(ALL_ASSETS_COLUMNS),
        ),
    )


def assets_view_page() -> rx.Component:
    """Halaman Semua Aset (/assets) dengan 4 Kartu KPI dan Tabel Satu Data Induk."""
    content = rx.vstack(
        _inventory_header(),
        _four_kpi_cards_row(),
        _category_hierarchy_bars(),
        rx.box(
            _filter_bar_by_slug(),
            _table_by_slug(),
            table_pagination(
                summary_text=AssetState.pagination_summary,
                current_page=AssetState.page,
                current_page_str=AssetState.current_page_str,
                total_pages=AssetState.total_pages,
                page_tokens=AssetState.page_tokens,
                on_prev=AssetState.prev_page,
                on_next=AssetState.next_page,
                on_page_select=AssetState.select_page,
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
        ),
        detail_drawer(
            is_open=AssetState.drawer_open,
            on_close=AssetState.close_drawer,
            code_var=AssetState.active_code,
            title_var=AssetState.active_title,
            category_var=AssetState.active_category,
            condition_var=AssetState.active_condition,
            status_var=AssetState.active_status,
            active_tab=AssetState.drawer_tab,
            on_tab_change=AssetState.set_drawer_tab,
            section1_title="Data aset",
            general_items=AssetState.active_asset_data_items,
            section2_title="Spesifikasi",
            usage_items=AssetState.active_spec_items,
            chips_section_title="Konektivitas",
            chips_items=AssetState.active_chips_items,
            history_items=AssetState.active_history_info,
            maintenance_logs=AssetState.active_maintenance_logs,
            on_edit=AssetState.edit_active_asset,
            on_duplicate=AssetState.duplicate_active_asset,
            on_delete=AssetState.delete_active_asset,
            tabs=(
                ("detail", "Rincian Aset"),
                ("history", "Riwayat & Log"),
            ),
        ),
        asset_form_modal(),
        confirm_delete_dialog(
            is_open=AssetState.delete_dialog_open,
            title="Hapus Unit Aset?",
            description=(
                f"Apakah Anda yakin ingin menghapus aset {AssetState.asset_to_delete} "
                f"({AssetState.asset_to_delete_label}) beserta seluruh spesifikasinya? "
                "Tindakan ini akan dicatat pada Audit Log."
            ),
            on_cancel=AssetState.cancel_delete,
            on_confirm=AssetState.execute_delete_asset,
        ),
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Inventory", AssetState.breadcrumb_title),
    )


__all__ = ["assets_view_page"]
