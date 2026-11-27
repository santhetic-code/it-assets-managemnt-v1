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
    reusable_data_table,
    table_pagination,
)
from itam_pro.components.tables.filter_bar import (
    ColumnToggleOption,
    column_visibility_popover,
)
from itam_pro.components.ui import (
    PillSelectConfig,
    action_primary_button,
    detail_drawer,
    hero_stat_card,
    page_header,
    pill_filter_bar,
    secondary_button,
    stat_card,
    tab_bar,
)
from itam_pro.services.category_config import (
    build_column_toggle_options,
    build_table_columns_for_slug,
)
from itam_pro.states.asset_state import AssetState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Space

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
    return page_header(
        icon="box",
        title=AssetState.page_title,
        subtitle=AssetState.page_subtitle,
        actions=[
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
        ],
    )


def _four_kpi_cards_row() -> rx.Component:
    """Baris 4 Kartu KPI interaktif: Hero Total Aset (donut % digunakan) + 3 kartu putih."""
    return rx.box(
        hero_stat_card(
            icon="box",
            label="TOTAL ASET",
            value=AssetState.summary_counts["total"],
            subtext="di semua kategori",
            percent=AssetState.in_use_percent,
            percent_caption="digunakan",
            link_text="Lihat detail →",
            on_click=AssetState.select_kpi_card("total"),
            is_active=AssetState.active_kpi_card == "total",
            glow_ring=True,
        ),
        stat_card(
            icon="circle-check",
            tone="purple",
            label="PERLU PERHATIAN",
            value=AssetState.summary_counts["perlu_perhatian"],
            subtext="rusak atau dalam perbaikan",
            link_text="Lihat detail →",
            is_active=AssetState.active_kpi_card == "attention",
            on_click=AssetState.select_kpi_card("attention"),
        ),
        stat_card(
            icon="clock",
            tone="success",
            label="GARANSI SEGERA HABIS",
            value=AssetState.summary_counts["garansi_segera_habis"],
            subtext="berakhir ≤ 30 hari",
            link_text="Lihat detail →",
            is_active=AssetState.active_kpi_card == "warranty",
            on_click=AssetState.select_kpi_card("warranty"),
        ),
        stat_card(
            icon="shield",
            tone="warning",
            label="BELUM TERHUBUNG PEMBELIAN",
            value=AssetState.summary_counts["belum_terhubung_pembelian"],
            value_tone=rx.cond(
                AssetState.summary_counts["belum_terhubung_pembelian"] > 0,
                "warning",
                "default",
            ),
            subtext="belum punya invoice sumber",
            link_text="Lihat detail →",
            is_active=AssetState.active_kpi_card == "no_purchase",
            on_click=AssetState.select_kpi_card("no_purchase"),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "1.35fr 1fr 1fr 1fr",
                "gap": Space.S4,
                "align_items": "stretch",
                "@media (max-width: 1099px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))",
                },
                "@media (max-width: 599px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )


def _category_tile(group_key: str, label: str, count_key: str) -> rx.Component:
    """Satu tile kelompok kategori ala _type_tiles_row Credential Manager."""
    is_active = AssetState.active_group == group_key
    safe_count = rx.cond(
        AssetState.sidebar_counts[count_key],
        AssetState.sidebar_counts[count_key],
        0,
    )
    return rx.el.button(
        rx.vstack(
            rx.text(
                label,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
                line_height="1.2",
                text_align="left",
            ),
            rx.text(
                f"{safe_count} aset",
                font_size=FontSize.XS,
                color=Color.MUTED,
                style=rx.Style({"font_variant_numeric": "tabular-nums"}),
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        type="button",
        aria_pressed=is_active,
        on_click=AssetState.select_category_group(group_key),
        style=rx.Style(
            {
                "padding": "12px 16px",
                "border_radius": Radius.CARD,
                "background_color": Color.SURFACE,
                "border": rx.cond(
                    is_active,
                    f"2px solid {Color.ACCENT}",
                    f"1px solid {Color.BORDER}",
                ),
                "box_shadow": rx.cond(is_active, Shadow.KPI_ACTIVE_RING, Shadow.TABLE_CARD),
                "cursor": "pointer",
                "text_align": "left",
                "font_family": FONT_FAMILY,
                "width": "100%",
                "transition": "all 0.15s ease",
                "_hover": {
                    "border_color": Color.ACCENT,
                    "transform": "translateY(-1px)",
                },
            }
        ),
    )


def _category_tiles_row() -> rx.Component:
    """Baris 8 tile kategori utama ala _type_tiles_row Kredensial."""
    return rx.box(
        _category_tile("all", "Semua", "all"),
        _category_tile("perangkat-it", "Perangkat IT", "perangkat-it"),
        _category_tile("komponen-periferal", "Komponen & Periferal", "komponen-periferal"),
        _category_tile("jaringan", "Jaringan", "jaringan"),
        _category_tile("kendaraan", "Kendaraan", "kendaraan"),
        _category_tile("peralatan-kantor", "Peralatan Kantor", "peralatan-kantor"),
        _category_tile("furnitur", "Furnitur", "furnitur"),
        _category_tile("lainnya", "Lainnya", "lainnya"),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(8, minmax(0, 1fr))",
                "gap": "10px",
                "@media (max-width: 1200px)": {
                    "grid_template_columns": "repeat(4, minmax(0, 1fr))",
                },
                "@media (max-width: 640px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))",
                },
            }
        ),
    )


def _subcategory_tab_bar() -> rx.Component:
    """Tab sub-kategori dengan badge hitungan di bagian atas kartu tabel."""
    it_tabs = [
        {
            "key": "",
            "label": "Semua Perangkat IT",
            "count": AssetState.sidebar_counts["perangkat-it"],
        },
        {"key": "pc", "label": "PC & Laptop", "count": AssetState.sidebar_counts["pc"]},
        {"key": "server", "label": "Server", "count": AssetState.sidebar_counts["server"]},
        {"key": "monitor", "label": "Monitor", "count": AssetState.sidebar_counts["monitor"]},
        {"key": "ups", "label": "UPS", "count": AssetState.sidebar_counts["ups"]},
    ]
    vehicle_tabs = [
        {"key": "", "label": "Semua Kendaraan", "count": AssetState.sidebar_counts["kendaraan"]},
        {"key": "mobil", "label": "Mobil"},
        {"key": "motor", "label": "Motor"},
    ]
    office_tabs = [
        {"key": "ac", "label": "AC", "count": AssetState.sidebar_counts["peralatan-kantor"]},
    ]
    furniture_tabs = [
        {"key": "", "label": "Semua Furnitur", "count": AssetState.sidebar_counts["furnitur"]},
        {"key": "meja", "label": "Meja"},
        {"key": "kursi", "label": "Kursi"},
        {"key": "lemari", "label": "Lemari"},
    ]

    return cast(
        rx.Component,
        rx.match(
            AssetState.active_group,
            (
                "kendaraan",
                tab_bar(
                    tabs_with_count=vehicle_tabs,
                    active=AssetState.current_slug,
                    on_change=AssetState.select_subcategory,
                ),
            ),
            (
                "peralatan-kantor",
                tab_bar(
                    tabs_with_count=office_tabs,
                    active=AssetState.current_slug,
                    on_change=AssetState.select_subcategory,
                ),
            ),
            (
                "furnitur",
                tab_bar(
                    tabs_with_count=furniture_tabs,
                    active=AssetState.current_slug,
                    on_change=AssetState.select_subcategory,
                ),
            ),
            tab_bar(
                tabs_with_count=it_tabs,
                active=AssetState.current_slug,
                on_change=AssetState.select_subcategory,
            ),
        ),
    )


def _filter_bar_by_slug() -> rx.Component:
    """Bangun Pill Filter Bar dinamis per kategori + popover Atur kolom di kanan."""

    def _build_bar(
        placeholder: str,
        selects: list[PillSelectConfig],
        col_options: list[ColumnToggleOption],
    ) -> rx.Component:
        return pill_filter_bar(
            search_placeholder=placeholder,
            search_value=AssetState.search_query,
            on_search_change=AssetState.set_search_query,
            search_width="270px",
            selects=selects,
            on_reset=AssetState.reset_filters,
            right_slot=rx.hstack(
                column_visibility_popover(
                    column_options=col_options,
                    hidden_columns=AssetState.hidden_columns,
                    on_toggle_column=AssetState.toggle_column_visibility,
                    on_reset_columns=AssetState.reset_column_visibility,
                ),
                rx.text(
                    AssetState.result_count_label,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                    white_space="nowrap",
                ),
                spacing="3",
                align="center",
            ),
        )

    all_selects: list[PillSelectConfig] = [
        {
            "placeholder": "Semua kategori",
            "value": AssetState.kategori_filter,
            "options": AssetState.master_kategori_options,
            "on_change": AssetState.set_kategori_filter,
        },
        {
            "placeholder": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
        {
            "placeholder": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "placeholder": "Semua kondisi",
            "value": AssetState.kondisi_filter,
            "options": AssetState.master_kondisi_options,
            "on_change": AssetState.set_kondisi_filter,
        },
        {
            "placeholder": "Semua status",
            "value": AssetState.status_filter,
            "options": AssetState.master_status_options,
            "on_change": AssetState.set_status_filter,
        },
    ]

    pc_selects: list[PillSelectConfig] = [
        {
            "placeholder": "Semua OS",
            "value": AssetState.filter_os_value,
            "options": AssetState.os_filter_options,
            "on_change": AssetState.set_attr_filter("os"),
        },
        {
            "placeholder": "Semua RAM",
            "value": AssetState.filter_ram_value,
            "options": AssetState.ram_filter_options,
            "on_change": AssetState.set_attr_filter("ram"),
        },
        {
            "placeholder": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "placeholder": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
    ]

    monitor_selects: list[PillSelectConfig] = [
        {
            "placeholder": "Semua merk",
            "value": AssetState.filter_merk_value,
            "options": AssetState.master_merk_options,
            "on_change": AssetState.set_attr_filter("merk"),
        },
        {
            "placeholder": "Semua ukuran",
            "value": AssetState.filter_ukuran_value,
            "options": AssetState.master_ukuran_options,
            "on_change": AssetState.set_attr_filter("ukuran_layar"),
        },
        {
            "placeholder": "Semua resolusi",
            "value": AssetState.filter_resolusi_value,
            "options": AssetState.master_resolusi_options,
            "on_change": AssetState.set_attr_filter("resolusi_layar"),
        },
        {
            "placeholder": "Semua konektivitas",
            "value": AssetState.filter_konektivitas_value,
            "options": AssetState.master_konektivitas_options,
            "on_change": AssetState.set_attr_filter("konektivitas"),
        },
        {
            "placeholder": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "placeholder": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
    ]

    default_cat_selects: list[PillSelectConfig] = [
        {
            "placeholder": "Semua lokasi",
            "value": AssetState.lokasi_filter,
            "options": AssetState.master_lokasi_options,
            "on_change": AssetState.set_lokasi_filter,
        },
        {
            "placeholder": "Semua pemilik",
            "value": AssetState.kepemilikan_filter,
            "options": AssetState.master_kepemilikan_options,
            "on_change": AssetState.set_kepemilikan_filter,
        },
        {
            "placeholder": "Semua kondisi",
            "value": AssetState.kondisi_filter,
            "options": AssetState.master_kondisi_options,
            "on_change": AssetState.set_kondisi_filter,
        },
        {
            "placeholder": "Semua status",
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
                _build_bar(
                    "Cari ID aset, nama aset, SN/PID, pemakai...",
                    all_selects,
                    ALL_ASSETS_COL_OPTIONS,
                ),
            ),
            (
                "pc",
                _build_bar(
                    "Cari hostname PC, user, CPU, OS...",
                    pc_selects,
                    PC_COL_OPTIONS,
                ),
            ),
            (
                "server",
                _build_bar(
                    "Cari ID server, nama server, CPU, OS...",
                    pc_selects,
                    SERVER_COL_OPTIONS,
                ),
            ),
            (
                "monitor",
                _build_bar(
                    "Cari ID aset, merk, tipe monitor...",
                    monitor_selects,
                    MONITOR_COL_OPTIONS,
                ),
            ),
            (
                "ups",
                _build_bar(
                    "Cari ID UPS, merek, kapasitas, beban...",
                    default_cat_selects,
                    UPS_COL_OPTIONS,
                ),
            ),
            _build_bar(
                "Cari ID aset, nama unit, SN/PID...",
                default_cat_selects,
                ALL_ASSETS_COL_OPTIONS,
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
        _category_tiles_row(),
        rx.box(
            _subcategory_tab_bar(),
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
                    "border_radius": Radius.KPI_CARD,
                    "box_shadow": Shadow.TABLE_CARD,
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
