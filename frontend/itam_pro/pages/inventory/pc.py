"""
Halaman Inventory -> Daftar PC (/pc).
Menggunakan komponen reusable (app_tabs, table_filter_bar, reusable_data_table,
table_pagination, detail_drawer, confirm_delete_dialog, base_layout).
"""
import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.forms import pc_form_modal
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
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
from itam_pro.states.pc_state import PCState
from itam_pro.styles import Color, FontSize, FontWeight, Radius, Space

# Urutan kolom sesuai spesifikasi:
# Nama PC (sticky kiri, tebal biru) | User (dinamis: User / Fungsi di Server & Backup) |
# Operasi System | RAM | VGA | CPU | Mainboard | HDD/SSD | Monitor | Keyboard | Mouse | aksi
PC_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "nama_pc",
        "header": "Nama PC",
        "width": "180px",
        "render_type": "bold_blue",
        "sticky_left": True,
    },
    {
        "key": "user",
        "header": PCState.user_column_header,
        "width": "190px",
        "render_type": "text",
    },
    {
        "key": "operasi_system",
        "header": "Operasi System",
        "width": "185px",
        "render_type": "text",
    },
    {
        "key": "ram",
        "header": "RAM",
        "width": "175px",
        "render_type": "text",
    },
    {
        "key": "vga",
        "header": "VGA",
        "width": "175px",
        "render_type": "text",
    },
    {
        "key": "cpu",
        "header": "CPU",
        "width": "185px",
        "render_type": "text",
    },
    {
        "key": "mainboard",
        "header": "Mainboard",
        "width": "185px",
        "render_type": "text",
    },
    {
        "key": "hdd_ssd",
        "header": "HDD/SSD",
        "width": "210px",
        "render_type": "text",
    },
    {
        "key": "monitor",
        "header": "Monitor",
        "width": "170px",
        "render_type": "text",
    },
    {
        "key": "keyboard",
        "header": "Keyboard",
        "width": "165px",
        "render_type": "text",
    },
    {
        "key": "mouse",
        "header": "Mouse",
        "width": "165px",
        "render_type": "text",
    },
]


def _pc_header() -> rx.Component:
    """Header halaman Daftar PC beserta tombol Export dan + Tambah PC."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Daftar PC",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Spesifikasi PC operasional, server, dan backup.",
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
                icon_tag="download",
                on_click=PCState.trigger_coming_soon("Export Data PC"),
            ),
            action_primary_button(
                label="+ Tambah PC",
                on_click=PCState.open_add_modal,
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


def _pc_table_card() -> rx.Component:
    """Kartu tunggal pembungkus Tabs + Filter Bar + Data Table + Pagination."""
    tab_configs: list[TabItemConfig] = [
        {
            "key": "Operasional",
            "label": "Operasional",
            "count": PCState.count_operasional,
        },
        {
            "key": "Server",
            "label": "Server",
            "count": PCState.count_server,
        },
        {
            "key": "Backup",
            "label": "Backup",
            "count": PCState.count_backup,
        },
    ]

    return rx.box(
        app_tabs(
            tabs=tab_configs,
            active_tab=PCState.active_jenis_tab,
            on_change=PCState.set_jenis_tab,
        ),
        table_filter_bar(
            search_value=PCState.search_query,
            on_search_change=PCState.set_search_query,
            search_placeholder="Cari hostname, user, CPU, mainboard...",
            dropdowns=[],
            on_reset=PCState.reset_filters,
            result_count_text=PCState.result_count_label,
        ),
        reusable_data_table(
            columns=PC_TABLE_COLUMNS,
            rows=PCState.items,
            id_key="id",
            selected_ids=PCState.selected_ids,
            active_row_id=PCState.active_pc_id,
            all_selected=PCState.all_current_selected,
            is_loading=PCState.is_loading,
            on_toggle_all=PCState.toggle_select_all,
            on_toggle_row=PCState.toggle_row_selection,
            on_row_click=PCState.open_drawer,
            on_edit_row=PCState.open_edit_modal,
            on_duplicate_row=PCState.open_duplicate_modal,
            duplicate_action_label="Duplikat",
            on_delete_row=PCState.confirm_delete_pc,
            on_reset_filter=PCState.reset_filters,
            empty_message=PCState.empty_state_title,
            empty_subtitle=PCState.empty_state_subtitle,
            empty_action_label=PCState.empty_state_action_label,
            on_empty_action=PCState.handle_empty_state_action,
        ),
        table_pagination(
            summary_text=PCState.pagination_summary,
            current_page=PCState.page,
            current_page_str=PCState.current_page_str,
            total_pages=PCState.total_pages,
            page_tokens=PCState.page_tokens,
            on_prev=PCState.prev_page,
            on_next=PCState.next_page,
            on_page_select=PCState.select_page,
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


def pc_list_page() -> rx.Component:
    """Halaman utama /pc yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _pc_header(),
        _pc_table_card(),
        detail_drawer(
            is_open=PCState.drawer_open,
            on_close=PCState.close_drawer,
            code_var=PCState.active_code,
            title_var=PCState.active_hostname,
            category_var=PCState.active_jenis,
            active_tab=PCState.drawer_tab,
            on_tab_change=PCState.set_drawer_tab,
            section1_title="Identitas",
            general_items=PCState.active_identity_info,
            section2_title="Perangkat keras",
            usage_items=PCState.active_hardware_info,
            section3_title="Periferal",
            section3_items=PCState.active_peripheral_info,
            history_items=PCState.active_history_info,
            duplicate_label="Duplikat",
            on_edit=lambda: PCState.open_edit_modal(""),
            on_duplicate=lambda: PCState.open_duplicate_modal(""),
            on_delete=lambda: PCState.confirm_delete_pc(""),
            tabs=(
                ("detail", "Rincian PC"),
                ("history", "Riwayat & Log"),
            ),
        ),
        pc_form_modal(),
        confirm_delete_dialog(
            is_open=PCState.delete_dialog_open,
            title="Hapus Data PC?",
            description=(
                f"Apakah Anda yakin ingin menghapus PC '{PCState.pc_to_delete_name}' "
                f"({PCState.pc_to_delete})? Tindakan ini akan dicatat pada Audit Log."
            ),
            on_cancel=PCState.cancel_delete,
            on_confirm=PCState.execute_delete_pc,
        ),
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Inventory", "Daftar PC"),
    )


__all__ = ["pc_list_page"]
