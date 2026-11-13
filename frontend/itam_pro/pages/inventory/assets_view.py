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
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Space

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
                label="Stock Opname QR",
                on_click=AssetState.open_opname_modal,
            ),
            secondary_button(
                label="Gabungkan Aset",
                on_click=AssetState.open_merge_modal,
            ),
            secondary_button(
                label="Export",
                on_click=AssetState.export_active_filtered_csv,
            ),
            secondary_button(
                label="Import",
                on_click=AssetState.open_import_modal,
            ),
            action_primary_button(
                label=AssetState.add_button_label,
                on_click=AssetState.open_add_modal,
            ),
            spacing="2",
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
    count_val: Any,
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


def _category_group_chip(
    group_key: str, label: str, icon_tag: str, count_key: str
) -> rx.Component:
    is_active = AssetState.active_group == group_key
    safe_count = rx.cond(
        AssetState.sidebar_counts[count_key],
        AssetState.sidebar_counts[count_key],
        0,
    )
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
                    f"{safe_count} aset",
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
    safe_count = (
        rx.cond(count_var, count_var, 0)
        if isinstance(count_var, rx.Var)
        else count_var
    )
    return rx.box(
        rx.text(
            f"{label} {safe_count}".strip(),
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
        rx.cond(
            AssetState.active_group == "kendaraan",
            rx.hstack(
                rx.text(
                    "Kendaraan ›",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.MUTED,
                ),
                _subcategory_pill("", "Semua Kendaraan", AssetState.sidebar_counts["kendaraan"]),
                _subcategory_pill("mobil", "Mobil", ""),
                _subcategory_pill("motor", "Motor", ""),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            rx.cond(
                AssetState.active_group == "peralatan-kantor",
                rx.hstack(
                    rx.text(
                        "Peralatan Kantor ›",
                        font_size=FontSize.XS,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.MUTED,
                    ),
                    _subcategory_pill("ac", "AC", AssetState.sidebar_counts["peralatan-kantor"]),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    AssetState.active_group == "furnitur",
                    rx.hstack(
                        rx.text(
                            "Furnitur ›",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.MUTED,
                        ),
                        _subcategory_pill(
                            "", "Semua Furnitur", AssetState.sidebar_counts["furnitur"]
                        ),
                        _subcategory_pill("meja", "Meja", ""),
                        _subcategory_pill("kursi", "Kursi", ""),
                        _subcategory_pill("lemari", "Lemari", ""),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                    ),
                    rx.fragment(),
                ),
            ),
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
            on_row_click=AssetState.open_asset_detail_page,
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
        _stock_opname_modal(),
        _import_assets_modal(),
        _merge_assets_modal(),
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


def _detail_field_card(label: str, value: Any, is_mono_blue: bool = False) -> rx.Component:
    return rx.vstack(
        rx.text(
            label.upper(),
            font_size="11px",
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.05em",
        ),
        rx.text(
            value,
            font_size=FontSize.BASE,
            font_weight=FontWeight.EXTRABOLD if is_mono_blue else FontWeight.BOLD,
            font_family="monospace" if is_mono_blue else "inherit",
            color=Color.ACCENT_BRIGHT if is_mono_blue else Color.TEXT,
        ),
        spacing="1",
        align="start",
        width="100%",
        padding="14px 18px",
        style=rx.Style(
            {
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
            }
        ),
    )


def _connected_card(
    icon_tag: str,
    icon_bg: str,
    icon_color: str,
    title: str,
    subtitle: Any,
    action_label: str,
    href: str,
    is_dashed: Any = False,
) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.center(
                rx.icon(tag=icon_tag, size=18, color=icon_color),
                width="38px",
                height="38px",
                border_radius="10px",
                background_color=icon_bg,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    title,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    subtitle,
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        rx.link(
            rx.text(
                action_label,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT_BRIGHT,
            ),
            href=href,
            underline="none",
        ),
        width="100%",
        justify="between",
        align="center",
        padding="14px 18px",
        style=rx.Style(
            {
                "background_color": rx.cond(is_dashed, Color.AMBER_50, Color.SURFACE),
                "border": rx.cond(
                    is_dashed,
                    f"1.5px dashed {Color.WARNING_BAR}",
                    f"1px solid {Color.BORDER}",
                ),
                "border_radius": Radius.CARD,
            }
        ),
    )


def _detail_tab_btn(tab_key: str, label: str) -> rx.Component:
    is_active = AssetState.detail_tab == tab_key
    return rx.el.button(
        label,
        type="button",
        on_click=AssetState.set_detail_tab(tab_key),
        style=rx.Style(
            {
                "padding": "10px 4px",
                "margin_right": "22px",
                "background": "transparent",
                "border": "none",
                "border_bottom": rx.cond(
                    is_active,
                    f"2.5px solid {Color.ACCENT_BRIGHT}",
                    "2.5px solid transparent",
                ),
                "color": rx.cond(is_active, Color.ACCENT_BRIGHT, Color.MUTED),
                "font_size": FontSize.SM,
                "font_weight": rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                "cursor": "pointer",
            }
        ),
    )


def _handover_modal() -> rx.Component:
    return rx.cond(
        AssetState.handover_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_handover_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            f"Serahkan / Pindahkan · {AssetState.detail_asset['id_aset']}",
                            font_size=FontSize.SUBTITLE,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=16, color=Color.MUTED),
                            type="button",
                            on_click=AssetState.close_handover_modal,
                            style=rx.Style(
                                {
                                    "background": "transparent",
                                    "border": "none",
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        "Perubahan pengguna atau lokasi otomatis tercatat di tabel mutasi "
                        "(asset_movements) dan tab Riwayat.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.vstack(
                        rx.text(
                            "Pengguna / Penempatan Baru *",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.input(
                            value=AssetState.handover_pengguna,
                            on_change=AssetState.set_handover_pengguna,
                            placeholder="Nama pengguna / jabatan / divisi",
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "38px",
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        rx.text(
                            "Lokasi Baru *",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.select(
                            rx.foreach(
                                AssetState.master_lokasi_options,
                                lambda loc: rx.el.option(loc, value=loc),
                            ),
                            value=AssetState.handover_lokasi,
                            on_change=AssetState.set_handover_lokasi,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "38px",
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    "Tanggal",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                ),
                                rx.el.input(
                                    type="date",
                                    value=AssetState.handover_tanggal,
                                    on_change=AssetState.set_handover_tanggal,
                                    style=rx.Style(
                                        {
                                            "width": "100%",
                                            "height": "38px",
                                            "padding": "0 12px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                width="50%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Status Aset",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                ),
                                rx.el.select(
                                    rx.el.option("Digunakan", value="Digunakan"),
                                    rx.el.option("Cadangan", value="Cadangan"),
                                    rx.el.option("Dalam Perbaikan", value="Dalam Perbaikan"),
                                    value=AssetState.handover_status,
                                    on_change=AssetState.set_handover_status,
                                    style=rx.Style(
                                        {
                                            "width": "100%",
                                            "height": "38px",
                                            "padding": "0 12px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                width="50%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.text(
                            "Catatan Serah Terima",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.input(
                            value=AssetState.handover_catatan,
                            on_change=AssetState.set_handover_catatan,
                            placeholder="Mis. diserahkan lengkap dengan monitor & kabel power",
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "38px",
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        align="start",
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AssetState.close_handover_modal),
                        action_primary_button(
                            "Simpan Serah Terima",
                            on_click=AssetState.submit_handover,
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                        padding_top="8px",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "480px",
                        "max_width": "94vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _qr_label_modal() -> rx.Component:
    return rx.cond(
        AssetState.qr_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_qr_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            "Cetak Label QR Aset",
                            font_size=FontSize.SUBTITLE,
                            font_weight=FontWeight.EXTRABOLD,
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=16, color=Color.MUTED),
                            type="button",
                            on_click=AssetState.close_qr_modal,
                            style=rx.Style(
                                {
                                    "background": "transparent",
                                    "border": "none",
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.image(src=AssetState.detail_qr_url, width="150px", height="150px"),
                            rx.text(
                                AssetState.detail_asset["id_aset"],
                                font_family="monospace",
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                AssetState.detail_asset["nama_aset"],
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                                text_align="center",
                            ),
                            rx.text(
                                "PT XML TRONIK · ITAM Pro",
                                font_size="10px",
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="center",
                            padding="16px",
                            style=rx.Style(
                                {
                                    "border": f"2px dashed {Color.BORDER}",
                                    "border_radius": Radius.CARD,
                                    "width": "100%",
                                }
                            ),
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        secondary_button("Tutup", on_click=AssetState.close_qr_modal),
                        action_primary_button(
                            "Cetak Label",
                            on_click=rx.call_script("window.print()"),
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "360px",
                        "max_width": "92vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _component_move_modal() -> rx.Component:
    """Modal Pindahkan / Pasang / Lepas Komponen sesuai Artboard 12 (Kanan)."""
    return rx.cond(
        AssetState.comp_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_comp_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.heading(
                                "Pindahkan komponen",
                                font_size="20px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                AssetState.comp_modal_subtitle,
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=18, color=Color.MUTED),
                            type="button",
                            on_click=AssetState.close_comp_modal,
                            style=rx.Style(
                                {"background": "transparent", "border": "none", "cursor": "pointer"}
                            ),
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.cond(
                        AssetState.comp_modal_error != "",
                        rx.box(
                            rx.text(
                                AssetState.comp_modal_error,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.DANGER_FG,
                            ),
                            padding="10px 12px",
                            width="100%",
                            style=rx.Style(
                                {
                                    "background_color": Color.DANGER_BG,
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                    ),
                    # Pilihan Tindakan (Pindah ke PC lain | Lepas ke Cadangan | Tandai Rusak)
                    rx.vstack(
                        rx.text(
                            "Tindakan",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.TEXT,
                        ),
                        rx.hstack(
                            rx.el.button(
                                "Pindah ke PC lain",
                                type="button",
                                on_click=AssetState.set_comp_modal_action("pindah"),
                                style=rx.Style(
                                    {
                                        "padding": "7px 14px",
                                        "border_radius": Radius.CONTROL,
                                        "font_size": FontSize.XS,
                                        "font_weight": FontWeight.BOLD,
                                        "background_color": rx.cond(
                                            AssetState.comp_modal_action == "pindah",
                                            Color.SURFACE,
                                            "transparent",
                                        ),
                                        "color": rx.cond(
                                            AssetState.comp_modal_action == "pindah",
                                            Color.ACCENT_BRIGHT,
                                            Color.TEXT,
                                        ),
                                        "border": "none",
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.el.button(
                                "Lepas ke Cadangan",
                                type="button",
                                on_click=AssetState.set_comp_modal_action("lepas"),
                                style=rx.Style(
                                    {
                                        "padding": "7px 14px",
                                        "border_radius": Radius.CONTROL,
                                        "font_size": FontSize.XS,
                                        "font_weight": FontWeight.BOLD,
                                        "background_color": rx.cond(
                                            AssetState.comp_modal_action == "lepas",
                                            Color.SURFACE,
                                            "transparent",
                                        ),
                                        "color": rx.cond(
                                            AssetState.comp_modal_action == "lepas",
                                            Color.ACCENT_BRIGHT,
                                            Color.TEXT,
                                        ),
                                        "border": "none",
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.el.button(
                                "Tandai Rusak",
                                type="button",
                                on_click=AssetState.set_comp_modal_action("rusak"),
                                style=rx.Style(
                                    {
                                        "padding": "7px 14px",
                                        "border_radius": Radius.CONTROL,
                                        "font_size": FontSize.XS,
                                        "font_weight": FontWeight.BOLD,
                                        "background_color": rx.cond(
                                            AssetState.comp_modal_action == "rusak",
                                            Color.SURFACE,
                                            "transparent",
                                        ),
                                        "color": rx.cond(
                                            AssetState.comp_modal_action == "rusak",
                                            Color.DANGER_FG,
                                            Color.TEXT,
                                        ),
                                        "border": "none",
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            spacing="1",
                            padding="4px",
                            style=rx.Style(
                                {
                                    "background_color": Color.TABLE_HEADER_BG,
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    # Baris PC tujuan & Slot
                    rx.cond(
                        (AssetState.comp_modal_action == "pindah")
                        | (AssetState.comp_modal_action == "pasang"),
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    "PC tujuan *",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                ),
                                rx.el.select(
                                    rx.foreach(
                                        AssetState.comp_pc_targets,
                                        lambda opt: rx.el.option(opt, value=opt),
                                    ),
                                    value=AssetState.comp_modal_target_pc,
                                    on_change=AssetState.set_comp_modal_target_pc,
                                    style=rx.Style(
                                        {
                                            "width": "100%",
                                            "height": "38px",
                                            "padding": "0 12px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                width="60%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Slot", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                                rx.el.select(
                                    rx.foreach(
                                        AssetState.comp_slot_options,
                                        lambda s: rx.el.option(s, value=s),
                                    ),
                                    value=AssetState.comp_modal_slot,
                                    on_change=AssetState.set_comp_modal_slot,
                                    style=rx.Style(
                                        {
                                            "width": "100%",
                                            "height": "38px",
                                            "padding": "0 12px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                width="40%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Baris Alasan & Tanggal
                    rx.hstack(
                        rx.vstack(
                            rx.text("Alasan *", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                            rx.el.select(
                                rx.foreach(
                                    AssetState.comp_alasan_options,
                                    lambda a: rx.el.option(a, value=a),
                                ),
                                value=AssetState.comp_modal_alasan,
                                on_change=AssetState.set_comp_modal_alasan,
                                style=rx.Style(
                                    {
                                        "width": "100%",
                                        "height": "38px",
                                        "padding": "0 12px",
                                        "border": f"1px solid {Color.INPUT_BORDER}",
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                            width="60%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text("Tanggal", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                            rx.el.input(
                                type="date",
                                value=AssetState.comp_modal_tanggal,
                                on_change=AssetState.set_comp_modal_tanggal,
                                style=rx.Style(
                                    {
                                        "width": "100%",
                                        "height": "38px",
                                        "padding": "0 12px",
                                        "border": f"1px solid {Color.INPUT_BORDER}",
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                            width="40%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Catatan Tambahan
                    rx.vstack(
                        rx.text(
                            "Catatan (opsional)",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.textarea(
                            value=AssetState.comp_modal_catatan,
                            on_change=AssetState.set_comp_modal_catatan,
                            placeholder="Alasan mutasi atau instruksi tambahan...",
                            rows=2,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "padding": "8px 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                }
                            ),
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    # Kartu Biru: DAMPAK PADA SPESIFIKASI (Artboard 12)
                    rx.vstack(
                        rx.text(
                            "DAMPAK PADA SPESIFIKASI",
                            font_size="11px",
                            font_weight=FontWeight.BOLD,
                            color=Color.ACCENT_BRIGHT,
                            letter_spacing="0.05em",
                        ),
                        rx.foreach(
                            AssetState.comp_modal_impacts,
                            lambda imp: rx.hstack(
                                rx.text(imp["label"], font_size=FontSize.SM, color=Color.TEXT),
                                rx.spacer(),
                                rx.text(
                                    imp["change"],
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.EXTRABOLD,
                                    color=Color.TEXT,
                                ),
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        padding="12px 16px",
                        style=rx.Style(
                            {
                                "background_color": Color.BLUE_50,
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": Radius.CARD,
                            }
                        ),
                    ),
                    # Checkbox Wipe Disk SSD/HDD
                    rx.el.label(
                        rx.hstack(
                            rx.el.input(
                                type="checkbox",
                                checked=AssetState.comp_modal_confirm_wipe,
                                on_change=AssetState.toggle_comp_modal_wipe,
                            ),
                            rx.text(
                                "Khusus SSD/HDD: data pada disk sudah dihapus (wipe) "
                                "atau akan dipindah dengan aman",
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            spacing="2",
                            align="start",
                        ),
                        style=rx.Style({"cursor": "pointer", "width": "100%"}),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AssetState.close_comp_modal),
                        action_primary_button(
                            "→ Simpan pemindahan",
                            on_click=AssetState.submit_component_mutation,
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                        padding_top="6px",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "480px",
                        "max_width": "94vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _stock_opname_modal() -> rx.Component:
    """Modal Stock Opname QR & Laporan Selisih (Seksi 14 & 18)."""
    return rx.cond(
        AssetState.opname_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_opname_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            "Stock Opname (Pindai QR & Laporan Selisih)",
                            font_size=FontSize.SUBTITLE,
                            font_weight=FontWeight.EXTRABOLD,
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=16, color=Color.MUTED),
                            type="button",
                            on_click=AssetState.close_opname_modal,
                            style=rx.Style(
                                {
                                    "background": "transparent",
                                    "border": "none",
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.hstack(
                        _detail_field_card(
                            "TERDAFTAR", AssetState.opname_summary["total_terdaftar"]
                        ),
                        _detail_field_card(
                            "DITEMUKAN", AssetState.opname_summary["ditemukan"]
                        ),
                        _detail_field_card(
                            "TIDAK DITEMUKAN", AssetState.opname_summary["tidak_ditemukan"]
                        ),
                        _detail_field_card(
                            "SELISIH / BELUM SCAN", AssetState.opname_summary["selisih"]
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.cond(
                        AssetState.opname_error != "",
                        rx.text(
                            AssetState.opname_error,
                            font_size=FontSize.XS,
                            color=Color.DANGER_FG,
                            font_weight=FontWeight.BOLD,
                        ),
                    ),
                    rx.cond(
                        AssetState.opname_feedback != "",
                        rx.text(
                            AssetState.opname_feedback,
                            font_size=FontSize.XS,
                            color=Color.SUCCESS_FG,
                            font_weight=FontWeight.BOLD,
                        ),
                    ),
                    rx.hstack(
                        rx.el.input(
                            value=AssetState.opname_qr_input,
                            on_change=AssetState.set_opname_qr_input,
                            placeholder="Pindai URL QR atau ketik Aset ID (mis. PC-003)...",
                            style=rx.Style(
                                {
                                    "flex": "1",
                                    "height": "38px",
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        rx.el.select(
                            rx.el.option("Ditemukan", value="Ditemukan"),
                            rx.el.option("Tidak ditemukan", value="Tidak ditemukan"),
                            value=AssetState.opname_status_choice,
                            on_change=AssetState.set_opname_status_choice,
                            style=rx.Style(
                                {
                                    "height": "38px",
                                    "padding": "0 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        action_primary_button("Tandai", on_click=AssetState.submit_opname_scan),
                        spacing="2",
                        width="100%",
                    ),
                    rx.hstack(
                        secondary_button("Tutup", on_click=AssetState.close_opname_modal),
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "620px",
                        "max_width": "94vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _import_assets_modal() -> rx.Component:
    """Modal Import CSV Aset Lama dengan Pratinjau Validasi (Seksi 14 & 18)."""
    return rx.cond(
        AssetState.import_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_import_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            "Import Aset Lama (CSV / Excel)",
                            font_size=FontSize.SUBTITLE,
                            font_weight=FontWeight.EXTRABOLD,
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=16, color=Color.MUTED),
                            type="button",
                            on_click=AssetState.close_import_modal,
                            style=rx.Style(
                                {
                                    "background": "transparent",
                                    "border": "none",
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        "Format kolom: Nama Aset, Kategori, Pengguna, Lokasi, Status, Kondisi,"
                        " Serial Number",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.el.textarea(
                        value=AssetState.import_csv_text,
                        on_change=AssetState.set_import_csv_text,
                        rows=5,
                        style=rx.Style(
                            {
                                "width": "100%",
                                "padding": "10px",
                                "font_family": "monospace",
                                "font_size": FontSize.XS,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    rx.cond(
                        AssetState.import_preview_done,
                        rx.text(
                            AssetState.import_validation_summary,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.ACCENT,
                        ),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AssetState.close_import_modal),
                        secondary_button(
                            "Validasi & Pratinjau", on_click=AssetState.run_import_preview
                        ),
                        action_primary_button(
                            "Simpan Baris Valid", on_click=AssetState.execute_import_commit
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "560px",
                        "max_width": "94vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _merge_assets_modal() -> rx.Component:
    """Modal Gabungkan Aset Duplikat untuk Admin (Seksi 13)."""
    return rx.cond(
        AssetState.merge_modal_open,
        rx.box(
            rx.box(
                on_click=AssetState.close_merge_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Gabungkan Aset Duplikat",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.text(
                        "Seluruh relasi komponen, IP, kredensial, dan jadwal maintenance dari Aset"
                        " Duplikat akan dipindahkan ke Aset Induk.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.cond(
                        AssetState.merge_error != "",
                        rx.text(
                            AssetState.merge_error,
                            font_size=FontSize.XS,
                            color=Color.DANGER_FG,
                            font_weight=FontWeight.BOLD,
                        ),
                    ),
                    rx.text(
                        "ID Aset Duplikat (Sumber yang akan dinonaktifkan) *",
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                    ),
                    rx.el.input(
                        value=AssetState.merge_source_id,
                        on_change=AssetState.set_merge_source_id,
                        placeholder="Contoh: PC-034",
                        style=rx.Style(
                            {
                                "width": "100%",
                                "height": "38px",
                                "padding": "0 12px",
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    rx.text(
                        "ID Aset Utama (Tujuan penggabungan) *",
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                    ),
                    rx.el.input(
                        value=AssetState.merge_target_id,
                        on_change=AssetState.set_merge_target_id,
                        placeholder="Contoh: PC-003",
                        style=rx.Style(
                            {
                                "width": "100%",
                                "height": "38px",
                                "padding": "0 12px",
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AssetState.close_merge_modal),
                        action_primary_button(
                            "Gabungkan Aset", on_click=AssetState.submit_merge_assets
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "440px",
                        "max_width": "94vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _component_tab_view() -> rx.Component:
    """Isi Tab Komponen pada Detail PC / Server sesuai Artboard 12 (Kiri)."""
    return rx.vstack(
        # Strip Total RAM & Storage + Tombol + Pasang Komponen / Konversi
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.text(
                        AssetState.comp_ram_summary_chip,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    padding="6px 12px",
                    border_radius=Radius.FULL,
                    background_color=Color.TABLE_HEADER_BG,
                ),
                rx.box(
                    rx.text(
                        AssetState.comp_storage_summary_chip,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    padding="6px 12px",
                    border_radius=Radius.FULL,
                    background_color=Color.TABLE_HEADER_BG,
                ),
                rx.cond(
                    AssetState.comp_is_tracked,
                    rx.text(
                        "dihitung otomatis dari komponen terpasang",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.hstack(
                        rx.box(
                            rx.text(
                                "Belum dilacak per komponen",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.WARNING_FG,
                            ),
                            padding="4px 10px",
                            border_radius=Radius.FULL,
                            background_color=Color.WARNING_BG,
                        ),
                        secondary_button(
                            "Konversi spesifikasi ke komponen",
                            on_click=AssetState.execute_component_wizard,
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                spacing="3",
                align="center",
                wrap="wrap",
            ),
            action_primary_button(
                "+ Pasang komponen",
                on_click=lambda: AssetState.open_install_spare_modal("RAM-021"),
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
        ),
        # Tabel Komponen Terpasang
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("ASET ID"),
                        rx.table.column_header_cell("KOMPONEN"),
                        rx.table.column_header_cell("SPESIFIKASI"),
                        rx.table.column_header_cell("SLOT"),
                        rx.table.column_header_cell("DIPASANG SEJAK"),
                        rx.table.column_header_cell("AKSI"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        AssetState.comp_installed_list,
                        lambda c: rx.table.row(
                            rx.table.cell(
                                rx.text(
                                    c["id_aset"],
                                    font_family="monospace",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.ACCENT_BRIGHT,
                                )
                            ),
                            rx.table.cell(rx.text(c["komponen"], font_weight=FontWeight.BOLD)),
                            rx.table.cell(c["spesifikasi"]),
                            rx.table.cell(c["slot"]),
                            rx.table.cell(c["dipasang_sejak"]),
                            rx.table.cell(
                                rx.hstack(
                                    rx.el.button(
                                        "Pindahkan",
                                        type="button",
                                        on_click=AssetState.open_move_component_modal(
                                            c["id_aset"], "pindah"
                                        ),
                                        style=rx.Style(
                                            {
                                                "background": "transparent",
                                                "border": "none",
                                                "color": Color.ACCENT_BRIGHT,
                                                "font_weight": FontWeight.BOLD,
                                                "font_size": FontSize.XS,
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                    rx.el.button(
                                        "Lepas",
                                        type="button",
                                        on_click=AssetState.open_move_component_modal(
                                            c["id_aset"], "lepas"
                                        ),
                                        style=rx.Style(
                                            {
                                                "background": "transparent",
                                                "border": "none",
                                                "color": Color.ACCENT_BRIGHT,
                                                "font_weight": FontWeight.BOLD,
                                                "font_size": FontSize.XS,
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                    spacing="3",
                                )
                            ),
                        ),
                    )
                ),
                variant="surface",
                width="100%",
            ),
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                    "overflow": "hidden",
                }
            ),
        ),
        # Tabel Stok Komponen Cadangan (Bisa Dipasang)
        rx.text(
            "STOK KOMPONEN CADANGAN (BISA DIPASANG)",
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
            padding_top="8px",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("ASET ID"),
                        rx.table.column_header_cell("KOMPONEN"),
                        rx.table.column_header_cell("LOKASI"),
                        rx.table.column_header_cell("CATATAN"),
                        rx.table.column_header_cell("AKSI"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        AssetState.comp_spare_list,
                        lambda s: rx.table.row(
                            rx.table.cell(
                                rx.text(
                                    s["id_aset"],
                                    font_family="monospace",
                                    font_weight=FontWeight.BOLD,
                                    color=Color.ACCENT_BRIGHT,
                                )
                            ),
                            rx.table.cell(
                                rx.text(
                                    f"{s['komponen']} {s['spesifikasi']}",
                                    font_weight=FontWeight.SEMIBOLD,
                                )
                            ),
                            rx.table.cell(s["lokasi"]),
                            rx.table.cell(
                                rx.box(
                                    rx.text(
                                        s["catatan_chip"],
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=rx.cond(
                                            s["needs_wipe"],
                                            Color.WARNING_FG,
                                            Color.SUCCESS_FG,
                                        ),
                                    ),
                                    padding="3px 10px",
                                    border_radius=Radius.FULL,
                                    background_color=rx.cond(
                                        s["needs_wipe"],
                                        Color.WARNING_BG,
                                        Color.SUCCESS_BG,
                                    ),
                                    display="inline-block",
                                )
                            ),
                            rx.table.cell(
                                rx.el.button(
                                    "Pasang ke PC",
                                    type="button",
                                    on_click=AssetState.open_install_spare_modal(s["id_aset"]),
                                    style=rx.Style(
                                        {
                                            "background": "transparent",
                                            "border": "none",
                                            "color": Color.ACCENT_BRIGHT,
                                            "font_weight": FontWeight.BOLD,
                                            "font_size": FontSize.XS,
                                            "cursor": "pointer",
                                        }
                                    ),
                                )
                            ),
                        ),
                    )
                ),
                variant="surface",
                width="100%",
            ),
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                    "overflow": "hidden",
                }
            ),
        ),
        rx.text(
            "Satu komponen hanya bisa terpasang di satu PC. "
            "Setiap pasang, lepas, dan pindah tercatat di tab Riwayat.",
            font_size=FontSize.XS,
            color=Color.MUTED,
        ),
        spacing="3",
        width="100%",
    )


def asset_detail_page() -> rx.Component:
    """Halaman Detail Aset (/assets/[id]) sesuai Artboard 11."""
    content = rx.vstack(
        rx.link(
            rx.text(
                "← Kembali ke Semua Aset",
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.MUTED,
            ),
            href="/assets",
            underline="none",
        ),
        # Kartu Header Utama + Tab Bar (Artboard 11)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.center(
                            rx.icon(tag="monitor", size=26, color=Color.WHITE),
                            width="56px",
                            height="56px",
                            border_radius="14px",
                            background_color=Color.ACCENT_BRIGHT,
                            flex_shrink="0",
                        ),
                        rx.vstack(
                            rx.heading(
                                AssetState.detail_asset["nama_aset"],
                                font_size="22px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                                line_height="1.2",
                            ),
                            rx.hstack(
                                rx.text(
                                    AssetState.detail_asset["id_aset"],
                                    font_family="monospace",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.EXTRABOLD,
                                    color=Color.ACCENT_BRIGHT,
                                ),
                                rx.box(
                                    rx.text(
                                        AssetState.detail_asset["kategori"],
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    padding="2px 10px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.TABLE_HEADER_BG,
                                    border=f"1px solid {Color.BORDER}",
                                ),
                                rx.box(
                                    rx.text(
                                        AssetState.detail_asset["status"],
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.SUCCESS_FG,
                                    ),
                                    padding="2px 10px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.SUCCESS_BG,
                                ),
                                rx.box(
                                    rx.text(
                                        f"Kondisi: {AssetState.detail_asset['kondisi']}",
                                        font_size=FontSize.XS,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.ACCENT,
                                    ),
                                    padding="2px 10px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.INFO_BG,
                                ),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="4",
                        align="center",
                    ),
                    rx.hstack(
                        secondary_button("Cetak Label", on_click=AssetState.open_qr_modal),
                        secondary_button(
                            "Serahkan / Pindahkan",
                            on_click=AssetState.open_handover_modal,
                        ),
                        action_primary_button("Edit", on_click=AssetState.open_edit_from_detail),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    wrap="wrap",
                    padding="22px 24px 12px 24px",
                ),
                rx.hstack(
                    _detail_tab_btn("ringkasan", "Ringkasan"),
                    _detail_tab_btn("spesifikasi", "Spesifikasi"),
                    rx.cond(
                        AssetState.detail_is_pc_or_server,
                        _detail_tab_btn("komponen", "Komponen"),
                        rx.fragment(),
                    ),
                    _detail_tab_btn("relasi", "Relasi"),
                    _detail_tab_btn("pembelian", "Pembelian & Garansi"),
                    _detail_tab_btn("maintenance", "Maintenance"),
                    _detail_tab_btn("riwayat", "Riwayat"),
                    spacing="0",
                    width="100%",
                    padding_x="24px",
                    style=rx.Style({"border_top": f"1px solid {Color.DIVIDER}"}),
                ),
                spacing="2",
                width="100%",
            ),
            width="100%",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        # Konten Tab Dinamis
        rx.match(
            AssetState.detail_tab,
            ("komponen", _component_tab_view()),
            (
                "spesifikasi",
                rx.vstack(
                    rx.text(
                        "SPESIFIKASI TEKNIS PERANGKAT",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    rx.cond(
                        AssetState.detail_asset["kategori"] == "UPS",
                        rx.vstack(
                            rx.box(
                                _detail_field_card(
                                    "KAPASITAS (VA)",
                                    f"{AssetState.detail_asset['kapasitas_va']} VA",
                                ),
                                _detail_field_card(
                                    "KAPASITAS WATT (DATASHEET)",
                                    rx.cond(
                                        AssetState.detail_asset["kapasitas_watt"] != "—",
                                        (
                                            f"{AssetState.detail_asset['kapasitas_watt']} W "
                                            "(Datasheet)"
                                        ),
                                        "Belum diisi (memakai Perkiraan VA × 0,6)",
                                    ),
                                ),
                                _detail_field_card(
                                    "JENIS AKI",
                                    AssetState.detail_asset["jenis_aki"],
                                ),
                                _detail_field_card(
                                    "BEBAN PERANGKAT",
                                    AssetState.detail_asset["digunakan_oleh"],
                                ),
                                style=rx.Style(
                                    {
                                        "display": "grid",
                                        "grid_template_columns": "1fr 1fr",
                                        "gap": "12px",
                                        "width": "100%",
                                    }
                                ),
                            ),
                            rx.hstack(
                                rx.text(
                                    "Isi / Ubah Kapasitas Real dari Datasheet (W):",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="number",
                                    placeholder="Contoh: 390 / 420",
                                    value=AssetState.ups_inline_watt_input,
                                    on_change=AssetState.set_ups_inline_watt_input,
                                    style=rx.Style(
                                        {
                                            "width": "160px",
                                            "height": "36px",
                                            "padding": "0 12px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                action_primary_button(
                                    "Simpan Kapasitas (W)",
                                    on_click=lambda: AssetState.save_ups_capacity_inline(
                                        AssetState.detail_asset["id_aset"],
                                        AssetState.ups_inline_watt_input,
                                    ),
                                ),
                                spacing="3",
                                align="center",
                                padding="14px 18px",
                                width="100%",
                                style=rx.Style(
                                    {
                                        "background_color": Color.SURFACE,
                                        "border": f"1px solid {Color.BORDER}",
                                        "border_radius": Radius.CARD,
                                    }
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.box(
                            _detail_field_card("CPU", AssetState.detail_asset["cpu"]),
                            _detail_field_card("RAM", AssetState.detail_asset["ram"]),
                            _detail_field_card("VGA", AssetState.detail_asset["vga"]),
                            _detail_field_card("STORAGE", AssetState.detail_asset["hdd_ssd"]),
                            _detail_field_card("OPERASI SYSTEM", AssetState.detail_asset["os"]),
                            _detail_field_card("MONITOR", AssetState.detail_monitor_display),
                            style=rx.Style(
                                {
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": "12px",
                                    "width": "100%",
                                }
                            ),
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            (
                "riwayat",
                rx.vstack(
                    rx.text(
                        "RIWAYAT SERAH TERIMA, MUTASI & PERUBAHAN",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    rx.foreach(
                        AssetState.detail_movements,
                        lambda mv: rx.box(
                            rx.hstack(
                                rx.text(
                                    mv["jenis"],
                                    font_weight=FontWeight.BOLD,
                                    font_size=FontSize.SM,
                                    color=Color.ACCENT,
                                ),
                                rx.text(
                                    f"{mv['dari']} → {mv['ke']}",
                                    font_weight=FontWeight.BOLD,
                                    font_size=FontSize.SM,
                                ),
                                rx.spacer(),
                                rx.text(mv["tanggal"], font_size=FontSize.XS, color=Color.MUTED),
                                width="100%",
                            ),
                            rx.text(
                                f"Alasan: {mv['alasan']} · Oleh: {mv['oleh']} · {mv['catatan']}",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            padding="14px 18px",
                            width="100%",
                            style=rx.Style(
                                {
                                    "background_color": Color.SURFACE,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": Radius.CARD,
                                }
                            ),
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            # Default: Tab Ringkasan (2 Kolom sesuai Artboard 11)
            rx.box(
                # Kolom Kiri: IDENTITAS & PENEMPATAN + SPESIFIKASI
                rx.vstack(
                    rx.text(
                        "IDENTITAS & PENEMPATAN",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    rx.box(
                        _detail_field_card(
                            "ASET ID",
                            AssetState.detail_asset["id_aset"],
                            is_mono_blue=True,
                        ),
                        _detail_field_card("KATEGORI", AssetState.detail_category_hierarchy),
                        _detail_field_card("PENGGUNA", AssetState.detail_asset["digunakan_oleh"]),
                        _detail_field_card("LOKASI", AssetState.detail_asset["lokasi"]),
                        _detail_field_card("STATUS", AssetState.detail_asset["status"]),
                        _detail_field_card("KONDISI", AssetState.detail_asset["kondisi"]),
                        style=rx.Style(
                            {
                                "display": "grid",
                                "grid_template_columns": "1fr 1fr",
                                "gap": "12px",
                                "width": "100%",
                            }
                        ),
                    ),
                    rx.text(
                        "SPESIFIKASI (KHUSUS KATEGORI PC)",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                        padding_top="8px",
                    ),
                    rx.box(
                        _detail_field_card("CPU", AssetState.detail_asset["cpu"]),
                        _detail_field_card("RAM", AssetState.detail_asset["ram"]),
                        _detail_field_card("VGA", AssetState.detail_asset["vga"]),
                        _detail_field_card("STORAGE", AssetState.detail_asset["hdd_ssd"]),
                        _detail_field_card("OPERASI SYSTEM", AssetState.detail_asset["os"]),
                        _detail_field_card("MONITOR", AssetState.detail_monitor_display),
                        style=rx.Style(
                            {
                                "display": "grid",
                                "grid_template_columns": "1fr 1fr",
                                "gap": "12px",
                                "width": "100%",
                            }
                        ),
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                # Kolom Kanan: TERHUBUNG KE ASET INI (Artboard 11)
                rx.vstack(
                    rx.text(
                        "TERHUBUNG KE ASET INI",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                        letter_spacing="0.06em",
                    ),
                    rx.cond(
                        AssetState.detail_has_monitors,
                        rx.foreach(
                            AssetState.detail_monitors,
                            lambda m: _connected_card(
                                "monitor",
                                Color.TABLE_HEADER_BG,
                                Color.TEXT,
                                "Monitor",
                                m["summary"],
                                "Buka →",
                                f"/assets/{m['id_aset']}",
                            ),
                        ),
                        _connected_card(
                            "monitor",
                            Color.TABLE_HEADER_BG,
                            Color.MUTED,
                            "Monitor",
                            "Belum ada monitor tertaut",
                            "Tautkan →",
                            "/assets?category=monitor",
                        ),
                    ),
                    _connected_card(
                        "network",
                        Color.GREEN_100,
                        Color.GREEN_700,
                        "Jaringan (IP & Server)",
                        AssetState.detail_primary_ip_summary,
                        "Buka →",
                        "/infrastructure/ip",
                    ),
                    _connected_card(
                        "lock",
                        Color.PURPLE_100,
                        Color.PURPLE_700,
                        "Kredensial",
                        AssetState.detail_credentials_summary,
                        "Buka →",
                        "/security/credentials",
                    ),
                    rx.cond(
                        AssetState.detail_has_purchase,
                        _connected_card(
                            "receipt",
                            Color.INFO_BG,
                            Color.ACCENT,
                            "Pembelian & garansi",
                            f"{AssetState.detail_purchase['nomor_invoice']} · "
                            f"{AssetState.detail_purchase['vendor']}",
                            "Buka →",
                            "/finance/purchases",
                        ),
                        _connected_card(
                            "receipt",
                            Color.AMBER_100,
                            Color.AMBER_700,
                            "Pembelian & garansi",
                            "Belum terhubung ke invoice",
                            "Hubungkan →",
                            "/finance/purchases",
                            is_dashed=True,
                        ),
                    ),
                    rx.cond(
                        AssetState.detail_has_maintenances,
                        _connected_card(
                            "wrench",
                            Color.INFO_BG,
                            Color.ACCENT,
                            "Maintenance",
                            AssetState.detail_maintenances_summary,
                            "Buka →",
                            "/operations/maintenance",
                        ),
                        _connected_card(
                            "wrench",
                            Color.INFO_BG,
                            Color.ACCENT,
                            "Maintenance",
                            "Belum ada jadwal",
                            "Jadwalkan →",
                            "/operations/maintenance",
                        ),
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "display": "grid",
                        "grid_template_columns": "1.55fr 1fr",
                        "gap": "24px",
                        "width": "100%",
                    }
                ),
            ),
        ),
        _handover_modal(),
        _qr_label_modal(),
        _component_move_modal(),
        asset_form_modal(),
        _stock_opname_modal(),
        _import_assets_modal(),
        _merge_assets_modal(),
        spacing="4",
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Inventory", "Semua Aset"),
    )


__all__ = ["asset_detail_page", "assets_view_page"]
