"""
Halaman Tunggal Generik Inventaris Aset ITAM Pro (Tahap 6c-1).
Melayani route `/assets` (Semua Aset) dan `/assets/c/[slug]` (View per Kategori).
"""
from typing import cast

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
    app_tabs,
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
MONITOR_VIEW_COLUMNS = build_table_columns_for_slug("monitor")

ALL_ASSETS_COL_OPTIONS = build_column_toggle_options("")
PC_COL_OPTIONS = build_column_toggle_options("pc")
MONITOR_COL_OPTIONS = build_column_toggle_options("monitor")


def _inventory_header() -> rx.Component:
    return rx.box(
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
                AssetState.page_subtitle,
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.hstack(
            secondary_button(
                label="Export",
                on_click=rx.toast.info("Fitur Export sedang disiapkan"),
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
    """Render `reusable_data_table` tunggal dengan preset kolom dari `category_config`."""

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
            ("monitor", _build_table(MONITOR_VIEW_COLUMNS)),
            _build_table(ALL_ASSETS_COLUMNS),
        ),
    )


def assets_view_page() -> rx.Component:
    """Halaman generik untuk `/assets` dan `/assets/c/[slug]`."""
    content = rx.vstack(
        _inventory_header(),
        rx.box(
            rx.cond(
                AssetState.has_tabs,
                app_tabs(
                    tabs=AssetState.current_tabs,
                    active_tab=AssetState.active_tab,
                    on_change=AssetState.set_tab,
                ),
                rx.fragment(),
            ),
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
