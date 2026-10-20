"""
Halaman Inventory -> Rekap Monitor (/monitor).
Mengikuti referensi desain Rekap Monitor@2x.png dengan menggunakan komponen reusable.
"""
import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import monitor_form_modal
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
from itam_pro.states.monitor_state import MonitorState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space

# Definisi kolom sesuai artboard Rekap Monitor (tanpa scroll horizontal di desktop):
# [pilih] | ID Aset ↕ | Merk ↕ | Tipe / Model | Ukuran Layar ↕ | Resolusi Layar |
# Konektivitas (chip) | Status (badge) | aksi
MONITOR_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "id_aset",
        "header": "ID Aset",
        "width": "12%",
        "render_type": "bold_blue",
        "sortable": True,
        "sort_key": "id_aset",
    },
    {
        "key": "merk",
        "header": "Merk",
        "width": "11%",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "merk",
    },
    {
        "key": "tipe_model",
        "header": "Tipe / Model",
        "width": "18%",
        "render_type": "text",
    },
    {
        "key": "ukuran_layar",
        "header": "Ukuran Layar",
        "width": "13%",
        "render_type": "text",
        "sortable": True,
        "sort_key": "ukuran_layar",
    },
    {
        "key": "resolusi_layar",
        "header": "Resolusi Layar",
        "width": "14%",
        "render_type": "text",
    },
    {
        "key": "konektivitas",
        "header": "Konektivitas",
        "width": "20%",
        "render_type": "chips",
    },
    {
        "key": "status",
        "header": "Status",
        "width": "12%",
        "render_type": "status_badge",
    },
]


def _monitor_header() -> rx.Component:
    """Header halaman Rekap Monitor beserta tombol Export dan + Tambah Monitor."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Rekap Monitor",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Daftar monitor beserta ukuran, resolusi, dan konektivitasnya.",
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
                on_click=MonitorState.trigger_coming_soon("Export Rekap Monitor"),
            ),
            action_primary_button(
                label="+ Tambah Monitor",
                on_click=MonitorState.open_add_modal,
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


def _monitor_table_card() -> rx.Component:
    """Kartu pembungkus Tabs + Filter Bar (4 dropdown) + Data Table + Pagination."""
    tab_configs: list[TabItemConfig] = [
        {
            "key": "Semua",
            "label": "Semua",
            "count": MonitorState.count_semua,
        },
        {
            "key": "Digunakan",
            "label": "Digunakan",
            "count": MonitorState.count_digunakan,
        },
        {
            "key": "Backup",
            "label": "Backup",
            "count": MonitorState.count_backup,
        },
    ]

    dropdown_configs: list[FilterDropdownConfig] = [
        {
            "label": "Semua merk",
            "value": MonitorState.merk_filter,
            "options": MonitorState.master_merk_options,
            "on_change": MonitorState.set_merk_filter,
        },
        {
            "label": "Semua ukuran",
            "value": MonitorState.ukuran_filter,
            "options": MonitorState.master_ukuran_options,
            "on_change": MonitorState.set_ukuran_filter,
        },
        {
            "label": "Semua resolusi",
            "value": MonitorState.resolusi_filter,
            "options": MonitorState.master_resolusi_options,
            "on_change": MonitorState.set_resolusi_filter,
        },
        {
            "label": "Semua konektivitas",
            "value": MonitorState.konektivitas_filter,
            "options": MonitorState.master_konektivitas_options,
            "on_change": MonitorState.set_konektivitas_filter,
        },
    ]

    return rx.box(
        app_tabs(
            tabs=tab_configs,
            active_tab=MonitorState.active_status_tab,
            on_change=MonitorState.set_status_tab,
        ),
        table_filter_bar(
            search_value=MonitorState.search_query,
            on_search_change=MonitorState.set_search_query,
            search_placeholder="Cari ID aset, merk, tipe...",
            dropdowns=dropdown_configs,
            on_reset=MonitorState.reset_filters,
            result_count_text=MonitorState.result_count_label,
        ),
        reusable_data_table(
            columns=MONITOR_TABLE_COLUMNS,
            rows=MonitorState.items,
            id_key="id_aset",
            selected_ids=MonitorState.selected_ids,
            active_row_id=MonitorState.active_monitor_id,
            all_selected=MonitorState.all_current_selected,
            is_loading=MonitorState.is_loading,
            on_toggle_all=MonitorState.toggle_select_all,
            on_toggle_row=MonitorState.toggle_row_selection,
            on_row_click=MonitorState.open_drawer,
            on_edit_row=MonitorState.open_edit_modal,
            on_duplicate_row=MonitorState.open_duplicate_modal,
            duplicate_action_label="Duplikat",
            on_delete_row=MonitorState.confirm_delete_monitor,
            on_reset_filter=MonitorState.reset_filters,
            sort_by=MonitorState.sort_by,
            sort_dir=MonitorState.sort_dir,
            on_sort=MonitorState.toggle_sort,
            show_action_header=False,
            empty_message=MonitorState.empty_state_title,
            empty_subtitle=MonitorState.empty_state_subtitle,
            empty_action_label=MonitorState.empty_state_action_label,
            on_empty_action=MonitorState.handle_empty_state_action,
        ),
        table_pagination(
            summary_text=MonitorState.pagination_summary,
            current_page=MonitorState.page,
            current_page_str=MonitorState.current_page_str,
            total_pages=MonitorState.total_pages,
            page_tokens=MonitorState.page_tokens,
            on_prev=MonitorState.prev_page,
            on_next=MonitorState.next_page,
            on_page_select=MonitorState.select_page,
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


def monitor_list_page() -> rx.Component:
    """Halaman utama /monitor yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _monitor_header(),
        _monitor_table_card(),
        detail_drawer(
            is_open=MonitorState.drawer_open,
            on_close=MonitorState.close_drawer,
            code_var=MonitorState.active_code,
            title_var=MonitorState.active_title,
            status_var=MonitorState.active_status,
            active_tab=MonitorState.drawer_tab,
            on_tab_change=MonitorState.set_drawer_tab,
            section1_title="Identitas",
            general_items=MonitorState.active_identity_info,
            section2_title="Layar",
            usage_items=MonitorState.active_screen_info,
            chips_section_title="Konektivitas",
            chips_items=MonitorState.active_konektivitas_chips,
            section4_title="Status",
            section4_items=MonitorState.active_status_info,
            history_items=MonitorState.active_history_info,
            duplicate_label="Duplikat",
            on_edit=lambda: MonitorState.open_edit_modal(""),
            on_duplicate=lambda: MonitorState.open_duplicate_modal(""),
            on_delete=lambda: MonitorState.confirm_delete_monitor(""),
            tabs=(
                ("detail", "Rincian Monitor"),
                ("history", "Riwayat & Log"),
            ),
        ),
        monitor_form_modal(),
        confirm_delete_dialog(
            is_open=MonitorState.delete_dialog_open,
            title="Hapus Unit Monitor?",
            description=(
                f"Apakah Anda yakin ingin menghapus monitor {MonitorState.monitor_to_delete} "
                f"({MonitorState.monitor_to_delete_label})? "
                "Tindakan ini akan dicatat pada Audit Log."
            ),
            on_cancel=MonitorState.cancel_delete,
            on_confirm=MonitorState.execute_delete_monitor,
        ),
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Inventory", "Rekap Monitor"),
    )


__all__ = ["MONITOR_TABLE_COLUMNS", "monitor_list_page"]
