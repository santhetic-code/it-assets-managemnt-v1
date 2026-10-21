"""
Halaman Inventory -> Assets Inventory (/assets).
Sesuai struktur spreadsheet asli: 10 kolom data (Nama Aset sticky di kiri) + aksi,
5 dropdown filter dari master data, Detail Drawer 2 grup, dan Form Modal Tambah/Edit/Duplikat.
"""
import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import asset_form_modal
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui import action_primary_button, detail_drawer, secondary_button
from itam_pro.states.asset_state import AssetState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space

# Urutan kolom sesuai spreadsheet asli:
# Nama Aset (sticky di kiri) | Kategori | SN/PID | Tgl Masuk Gudang | Tgl Keluar Gudang |
# Kepemilikan | Lokasi | Kondisi | Status | Digunakan Oleh | aksi
ASSET_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "id_aset",
        "header": "ID Aset",
        "width": "125px",
        "render_type": "bold_blue",
        "sticky_left": True,
    },
    {
        "key": "nama_aset",
        "header": "Nama Aset",
        "width": "220px",
        "render_type": "text",
    },
    {
        "key": "kategori",
        "header": "Kategori",
        "width": "130px",
        "render_type": "badge",
    },
    {
        "key": "sn_pid",
        "header": "SN/PID",
        "width": "155px",
        "render_type": "text",
    },
    {
        "key": "tanggal_masuk_gudang",
        "header": "Tgl Masuk Gudang",
        "width": "150px",
        "render_type": "date",
    },
    {
        "key": "tanggal_keluar_gudang",
        "header": "Tgl Keluar Gudang",
        "width": "150px",
        "render_type": "date",
    },
    {
        "key": "kepemilikan",
        "header": "Kepemilikan",
        "width": "115px",
        "render_type": "badge",
    },
    {
        "key": "lokasi",
        "header": "Lokasi",
        "width": "170px",
        "render_type": "text",
    },
    {
        "key": "kondisi",
        "header": "Kondisi",
        "width": "185px",
        "render_type": "condition_badge",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "150px",
        "render_type": "status_badge",
    },
    {
        "key": "digunakan_oleh",
        "header": "Digunakan Oleh",
        "width": "165px",
        "render_type": "text",
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
                "Rekapitulasi seluruh unit fisik perangkat IT berdasarkan lokasi, kondisi, "
                "dan status pemakaian.",
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
                on_click=AssetState.trigger_coming_soon("Export Spreadsheet"),
            ),
            action_primary_button(
                label="+ Tambah Aset",
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


def _assets_table_card() -> rx.Component:
    """Kartu pembungkus Filter Bar (5 dropdown dari master) + Data Table + Pagination."""
    dropdown_configs: list[FilterDropdownConfig] = [
        {
            "label": "Semua Kategori",
            "value": AssetState.kategori_filter,
            "options": AssetState.master_kategori_options,
            "on_change": AssetState.set_kategori_filter,
        },
        {
            "label": "Semua Kepemilikan",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
        {
            "label": "Semua Lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "label": "Semua Kondisi",
            "value": AssetState.kondisi_filter,
            "options": AssetState.master_kondisi_options,
            "on_change": AssetState.set_kondisi_filter,
        },
        {
            "label": "Semua Status",
            "value": AssetState.status_filter,
            "options": AssetState.master_status_options,
            "on_change": AssetState.set_status_filter,
        },
    ]

    return rx.box(
        table_filter_bar(
            search_value=AssetState.search_query,
            on_search_change=AssetState.set_search_query,
            search_placeholder="Cari nama aset, SN/PID, digunakan oleh...",
            dropdowns=dropdown_configs,
            on_reset=AssetState.reset_filters,
            result_count_text=AssetState.result_count_label,
        ),
        reusable_data_table(
            columns=ASSET_TABLE_COLUMNS,
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
            condition_var=AssetState.active_condition,
            status_var=AssetState.active_status,
            active_tab=AssetState.drawer_tab,
            on_tab_change=AssetState.set_drawer_tab,
            general_items=AssetState.active_general_info,
            usage_items=AssetState.active_usage_info,
            history_items=AssetState.active_history_info,
            on_edit=lambda: AssetState.open_edit_modal(""),
            on_duplicate=lambda: AssetState.open_duplicate_modal(""),
            on_delete=lambda: AssetState.confirm_delete_asset(""),
        ),
        asset_form_modal(),
        confirm_delete_dialog(
            is_open=AssetState.delete_dialog_open,
            title="Hapus Unit Aset?",
            description=(
                f"Apakah Anda yakin ingin menghapus '{AssetState.asset_to_delete_name}' "
                f"({AssetState.asset_to_delete})? Tindakan ini akan dicatat pada Audit Log."
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


__all__ = [
    "ASSET_TABLE_COLUMNS",
    "assets_inventory_page",
]
