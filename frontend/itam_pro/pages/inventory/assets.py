"""
Halaman Inventory -> Assets Inventory (/assets).
Menggunakan komponen tabel, filter bar, pagination, dan detail drawer generik.
"""
import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui import action_primary_button, detail_drawer, secondary_button
from itam_pro.states.asset_state import (
    CATEGORY_OPTIONS,
    LOCATION_OPTIONS,
    STATUS_OPTIONS,
    AssetState,
)
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space

# Definisi kolom diberikan dari luar ke komponen reusable_data_table
ASSET_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "id",
        "header": "Kode Aset",
        "width": "120px",
        "render_type": "bold_blue",
    },
    {
        "key": "name",
        "header": "Nama Aset",
        "width": "230px",
        "render_type": "text",
    },
    {
        "key": "category",
        "header": "Kategori",
        "width": "110px",
        "render_type": "badge",
    },
    {
        "key": "serial",
        "header": "Serial Number",
        "width": "145px",
        "render_type": "text",
    },
    {
        "key": "location",
        "header": "Lokasi",
        "width": "185px",
        "render_type": "text",
    },
    {
        "key": "pic",
        "header": "PIC / Pengguna",
        "width": "150px",
        "render_type": "text",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "130px",
        "render_type": "status_badge",
    },
    {
        "key": "warranty",
        "header": "Garansi",
        "width": "165px",
        "render_type": "date",
        "date_tone_key": "warranty_tone",
    },
]


def _assets_header() -> rx.Component:
    """Header halaman Assets Inventory beserta tombol Import CSV, Export, dan + Tambah Aset."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Assets Inventory",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Daftar seluruh aset perangkat keras, server, dan UPS di semua lokasi.",
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
                icon_tag="upload",
                on_click=AssetState.trigger_coming_soon("Import CSV"),
            ),
            secondary_button(
                label="Export",
                icon_tag="download",
                on_click=AssetState.trigger_coming_soon("Export Data Aset"),
            ),
            action_primary_button(
                label="+ Tambah Aset",
                on_click=AssetState.trigger_coming_soon("Form Tambah Aset"),
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


def _assets_table_card() -> rx.Component:
    """Kartu pembungkus Filter Bar + Data Table + Pagination."""
    dropdown_configs: list[FilterDropdownConfig] = [
        {
            "label": "Semua Kategori",
            "value": AssetState.category_filter,
            "options": CATEGORY_OPTIONS,
            "on_change": AssetState.set_category_filter,
        },
        {
            "label": "Semua Status",
            "value": AssetState.status_filter,
            "options": STATUS_OPTIONS,
            "on_change": AssetState.set_status_filter,
        },
        {
            "label": "Semua Lokasi",
            "value": AssetState.location_filter,
            "options": LOCATION_OPTIONS,
            "on_change": AssetState.set_location_filter,
        },
    ]

    return rx.box(
        table_filter_bar(
            search_value=AssetState.search_query,
            on_search_change=AssetState.set_search_query,
            search_placeholder="Cari kode aset, nama, serial, PIC...",
            dropdowns=dropdown_configs,
            on_reset=AssetState.reset_filters,
            result_count_text=AssetState.result_count_label,
        ),
        reusable_data_table(
            columns=ASSET_TABLE_COLUMNS,
            rows=AssetState.items,
            id_key="id",
            selected_ids=AssetState.selected_ids,
            active_row_id=AssetState.active_asset_id,
            all_selected=AssetState.all_current_selected,
            is_loading=AssetState.is_loading,
            on_toggle_all=AssetState.toggle_select_all,
            on_toggle_row=AssetState.toggle_row_selection,
            on_row_click=AssetState.open_drawer,
            on_edit_row=AssetState.edit_asset,
            on_delete_row=AssetState.confirm_delete_asset,
            on_reset_filter=AssetState.reset_filters,
            empty_message="Tidak ada aset yang cocok",
        ),
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
    )


def assets_inventory_page() -> rx.Component:
    """Halaman utama /assets yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _assets_header(),
        _assets_table_card(),
        detail_drawer(
            is_open=AssetState.drawer_open,
            on_close=AssetState.close_drawer,
            on_key_down=AssetState.handle_drawer_key_down,
            code_var=AssetState.active_code,
            title_var=AssetState.active_name,
            category_var=AssetState.active_category,
            status_var=AssetState.active_status,
            active_tab=AssetState.drawer_tab,
            on_tab_change=AssetState.set_drawer_tab,
            general_items=AssetState.active_general_info,
            spec_items=AssetState.active_specs_info,
            related_items=AssetState.active_related_info,
            history_items=AssetState.active_history_info,
            on_edit=lambda: AssetState.edit_asset(""),
            on_delete=lambda: AssetState.confirm_delete_asset(""),
        ),
        confirm_delete_dialog(
            is_open=AssetState.delete_dialog_open,
            title="Hapus Aset?",
            description=(
                f"Apakah Anda yakin ingin menghapus aset {AssetState.asset_to_delete}? "
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
        breadcrumb=("Inventory", "Assets Inventory"),
    )
