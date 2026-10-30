"""
Halaman Infrastructure -> Rekap Watt Server (/watt-server).
Menampilkan spesifikasi perangkat keras server beserta kalkulasi TDP (W),
kebutuhan PSU Minimum & Rekomendasi, dan estimasi kWh bulanan.
"""
import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    ColumnToggleOption,
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
    stat_card,
)
from itam_pro.states.power_state import PowerState
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

WATT_TABLE_COLUMNS: list[ColumnDef] = [
    {
        "key": "nama_aset",
        "header": "ID Server",
        "width": "210px",
        "min_width": "190px",
        "render_type": "name_with_sub",
        "sub_key": "sub_label",
        "sticky_left": True,
        "sortable": True,
        "sort_key": "nama_aset",
    },
    {
        "key": "cpu",
        "header": "Model Prosesor (CPU)",
        "width": "250px",
        "min_width": "210px",
        "render_type": "text",
        "sortable": True,
        "sort_key": "cpu",
    },
    {
        "key": "vga",
        "header": "Kartu Grafis (GPU)",
        "width": "220px",
        "min_width": "185px",
        "render_type": "text",
    },
    {
        "key": "ram",
        "header": "Konfigurasi RAM",
        "width": "190px",
        "min_width": "165px",
        "render_type": "text",
    },
    {
        "key": "hdd_ssd",
        "header": "Konfigurasi Penyimpanan",
        "width": "195px",
        "min_width": "170px",
        "render_type": "text",
    },
    {
        "key": "tdp_display",
        "header": "Total TDP (W)",
        "width": "135px",
        "min_width": "125px",
        "render_type": "bold_blue",
        "sortable": True,
        "sort_key": "tdp_total_w",
    },
    {
        "key": "psu_min_display",
        "header": "PSU Minimum (W)",
        "width": "150px",
        "min_width": "135px",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "psu_min_w",
    },
    {
        "key": "psu_rek_display",
        "header": "PSU Rekomendasi (W)",
        "width": "170px",
        "min_width": "155px",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "psu_rekomendasi_w",
    },
    {
        "key": "beban_badge",
        "header": "Beban",
        "width": "115px",
        "min_width": "105px",
        "render_type": "badge",
        "badge_variant_key": "beban_variant",
    },
]

WATT_COLUMN_OPTIONS: list[ColumnToggleOption] = [
    {"key": "cpu", "label": "Model Prosesor (CPU)"},
    {"key": "vga", "label": "Kartu Grafis (GPU)"},
    {"key": "ram", "label": "Konfigurasi RAM"},
    {"key": "hdd_ssd", "label": "Konfigurasi Penyimpanan"},
    {"key": "tdp_display", "label": "Total TDP (W)"},
    {"key": "psu_min_display", "label": "PSU Minimum (W)"},
    {"key": "psu_rek_display", "label": "PSU Rekomendasi (W)"},
    {"key": "beban_badge", "label": "Badge Beban"},
]


def _watt_header() -> rx.Component:
    """Header halaman Rekap Watt Server dengan tombol Export dan + Tambah Server."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Rekap Watt Server",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Pemantauan spesifikasi perangkat keras, konsumsi daya TDP (Watt), "
                "serta rekomendasi kapasitas PSU per server fisik.",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.hstack(
            secondary_button(
                label="Export CSV",
                on_click=rx.toast.info("Data siap diekspor ke format CSV"),
            ),
            action_primary_button(
                label="+ Tambah Watt Server",
                on_click=PowerState.open_add_modal,
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


def _watt_kpi_cards() -> rx.Component:
    """Baris 4 Kartu KPI Rekap Watt Server."""
    return rx.grid(
        stat_card(
            "Total Beban TDP Server",
            PowerState.kpi_total_tdp_display,
            "zap",
            tone="info",
            description=PowerState.kpi_total_kw_note,
        ),
        stat_card(
            "Estimasi Energi / Bulan",
            PowerState.kpi_kwh_month_display,
            "activity",
            tone="success",
            description="Asumsi operasional 24/7 (720 jam)",
        ),
        stat_card(
            "Total PSU Min / Rekomendasi",
            PowerState.kpi_psu_summary_display,
            "cpu",
            tone="purple",
            description=PowerState.kpi_avg_tdp_note,
        ),
        stat_card(
            "Beban TDP Tertinggi",
            PowerState.kpi_max_tdp_display,
            "triangle-alert",
            tone="warning",
            description=PowerState.kpi_max_tdp_server,
        ),
        columns="4",
        spacing="4",
        width="100%",
    )


def _estimasi_summary_footer() -> rx.Component:
    """Baris ESTIMASI di bawah tabel (sinkron dengan baris terakhir spreadsheet)."""
    return rx.hstack(
        rx.hstack(
            rx.icon(tag="calculator", size=16, color=Color.ACCENT),
            rx.text(
                "ESTIMASI TOTAL (SESUAI FILTER):",
                font_size=FontSize.XS,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                letter_spacing="0.04em",
            ),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.hstack(
                rx.text("Total TDP:", font_size=FontSize.SM, color=Color.MUTED),
                rx.text(
                    PowerState.footer_tdp_display,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.ACCENT_BRIGHT,
                ),
                spacing="2",
            ),
            rx.text("·", color=Color.MUTED),
            rx.hstack(
                rx.text("PSU Minimum:", font_size=FontSize.SM, color=Color.MUTED),
                rx.text(
                    PowerState.footer_psu_min_display,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                spacing="2",
            ),
            rx.text("·", color=Color.MUTED),
            rx.hstack(
                rx.text("PSU Rekomendasi:", font_size=FontSize.SM, color=Color.MUTED),
                rx.text(
                    PowerState.footer_psu_rek_display,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.TEXT,
                ),
                spacing="2",
            ),
            rx.text("·", color=Color.MUTED),
            rx.hstack(
                rx.text("Est. Bulanan:", font_size=FontSize.SM, color=Color.MUTED),
                rx.text(
                    PowerState.footer_kwh_display,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.SUCCESS_FG,
                ),
                spacing="2",
            ),
            spacing="3",
            align="center",
            wrap="wrap",
        ),
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        padding="14px 20px",
        style=rx.Style(
            {
                "background_color": Color.TABLE_HEADER_BG,
                "border_bottom": f"1px solid {Color.BORDER}",
            }
        ),
    )


def _modal_input_style() -> rx.Style:
    return rx.Style(
        {
            "width": "100%",
            "height": Size.FILTER_CONTROL_H,
            "padding": "0 12px",
            "background_color": Color.SURFACE,
            "color": Color.TEXT,
            "border": f"1px solid {Color.INPUT_BORDER}",
            "border_radius": Radius.CONTROL,
            "font_family": FONT_FAMILY,
            "font_size": FontSize.SM,
            "outline": "none",
            "box_sizing": "border-box",
        }
    )


def _watt_form_modal() -> rx.Component:
    """Modal input/edit manual data Rekap Watt Server."""
    return rx.cond(
        PowerState.form_modal_open,
        rx.box(
            rx.box(
                on_click=PowerState.close_form_modal,
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
                                rx.cond(
                                    PowerState.is_edit_mode,
                                    "Edit Data Watt Server",
                                    "Tambah Data Watt Server",
                                ),
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                "Isi spesifikasi komponen dan nilai TDP/PSU sesuai kalkulasi.",
                                font_size=FontSize.SM,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                            type="button",
                            on_click=PowerState.close_form_modal,
                            style=rx.Style(
                                {
                                    "width": "32px",
                                    "height": "32px",
                                    "background": "transparent",
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "cursor": "pointer",
                                    "display": "inline-flex",
                                    "align_items": "center",
                                    "justify_content": "center",
                                }
                            ),
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(
                        PowerState.form_error != "",
                        rx.box(
                            rx.text(
                                PowerState.form_error,
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                                color=Color.DANGER_FG,
                            ),
                            padding="10px 12px",
                            width="100%",
                            style=rx.Style(
                                {
                                    "background_color": Color.DANGER_BG,
                                    "border": f"1px solid {Color.DANGER_FG}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                        rx.fragment(),
                    ),
                    rx.vstack(
                        rx.text(
                            "ID Server *",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.input(
                            type="text",
                            placeholder="Contoh: SERVER OTO H2H",
                            value=PowerState.form_nama_aset,
                            on_change=PowerState.set_form_nama_aset,
                            style=_modal_input_style(),
                        ),
                        rx.text(
                            "Model Prosesor (CPU) *",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.input(
                            type="text",
                            placeholder="Contoh: Intel Core i7-13700 2,10 GHz Desktop",
                            value=PowerState.form_cpu,
                            on_change=PowerState.set_form_cpu,
                            style=_modal_input_style(),
                        ),
                        rx.text(
                            "Kartu Grafis (GPU)",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.input(
                            type="text",
                            placeholder="Contoh: Intel UHD Graphics 620 Desktop",
                            value=PowerState.form_vga,
                            on_change=PowerState.set_form_vga,
                            style=_modal_input_style(),
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    "Konfigurasi RAM",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="text",
                                    placeholder="Contoh: 4x DDR4 dengan kilat LED",
                                    value=PowerState.form_ram,
                                    on_change=PowerState.set_form_ram,
                                    style=_modal_input_style(),
                                ),
                                width="50%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Konfigurasi Penyimpanan",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="text",
                                    placeholder="Contoh: 2x SSD SATA, 1x SSD M.2",
                                    value=PowerState.form_hdd_ssd,
                                    on_change=PowerState.set_form_hdd_ssd,
                                    style=_modal_input_style(),
                                ),
                                width="50%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    "Total TDP (W) *",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="number",
                                    placeholder="159",
                                    value=PowerState.form_tdp_w,
                                    on_change=PowerState.set_form_tdp_w,
                                    style=_modal_input_style(),
                                ),
                                width="33%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text(
                                    "PSU Minimum (W)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="number",
                                    placeholder="250",
                                    value=PowerState.form_psu_min_w,
                                    on_change=PowerState.set_form_psu_min_w,
                                    style=_modal_input_style(),
                                ),
                                width="33%",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text(
                                    "PSU Rekomendasi (W)",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.TEXT,
                                ),
                                rx.el.input(
                                    type="number",
                                    placeholder="350",
                                    value=PowerState.form_psu_rek_w,
                                    on_change=PowerState.set_form_psu_rek_w,
                                    style=_modal_input_style(),
                                ),
                                width="34%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.text(
                            "Catatan Tambahan",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.input(
                            type="text",
                            placeholder="Opsional (mis. diukur dengan wattmeter / kalkulator PSU)",
                            value=PowerState.form_catatan,
                            on_change=PowerState.set_form_catatan,
                            style=_modal_input_style(),
                        ),
                        spacing="2",
                        width="100%",
                        align="start",
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=PowerState.close_form_modal,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 16px",
                                    "background_color": Color.SURFACE,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.SEMIBOLD,
                                    "color": Color.TEXT,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan Data Watt",
                            type="button",
                            on_click=PowerState.submit_form,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 20px",
                                    "background_color": Color.ACCENT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WHITE,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        width="100%",
                        justify="end",
                        spacing="3",
                        margin_top="8px",
                    ),
                    spacing="3",
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "540px",
                        "max_width": "94vw",
                        "max_height": "90vh",
                        "overflow_y": "auto",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _watt_table_card() -> rx.Component:
    """Kartu pembungkus Tabs + Filter Bar + Reusable Data Table + Baris ESTIMASI + Pagination."""
    tabs_config: list[TabItemConfig] = [
        {"key": "Semua", "label": "Semua Server", "count": PowerState.tab_counts["Semua"]},
        {
            "key": "Operasional",
            "label": "Server Operasional",
            "count": PowerState.tab_counts["Operasional"],
        },
        {
            "key": "Backup",
            "label": "Server Backup",
            "count": PowerState.tab_counts["Backup"],
        },
    ]

    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua prosesor",
            "value": PowerState.cpu_brand_filter,
            "options": PowerState.cpu_brand_options,
            "on_change": PowerState.set_cpu_brand_filter,
        },
        {
            "label": "Semua tingkat beban",
            "value": PowerState.beban_filter,
            "options": PowerState.beban_options,
            "on_change": PowerState.set_beban_filter,
        },
    ]

    return rx.box(
        app_tabs(
            tabs=tabs_config,
            active_tab=PowerState.active_tab,
            on_change=PowerState.set_tab,
        ),
        table_filter_bar(
            search_value=PowerState.search_query,
            on_search_change=PowerState.set_search_query,
            search_placeholder="Cari ID server, CPU, GPU, RAM, penyimpanan...",
            dropdowns=dropdowns,
            on_reset=PowerState.reset_filters,
            result_count_text=PowerState.result_count_label,
            column_options=WATT_COLUMN_OPTIONS,
            hidden_columns=PowerState.hidden_columns,
            on_toggle_column=PowerState.toggle_column_visibility,
            on_reset_columns=PowerState.reset_columns,
        ),
        reusable_data_table(
            columns=WATT_TABLE_COLUMNS,
            rows=PowerState.items,
            id_key="id",
            active_row_id=PowerState.active_row_id,
            is_loading=PowerState.is_loading,
            on_row_click=PowerState.open_drawer,
            on_edit_row=PowerState.open_edit_modal,
            on_duplicate_row=PowerState.open_duplicate_modal,
            duplicate_action_label="Duplikat Server",
            on_delete_row=PowerState.confirm_delete_entry,
            on_reset_filter=PowerState.reset_filters,
            sort_by=PowerState.sort_by,
            sort_dir=PowerState.sort_dir,
            on_sort=PowerState.toggle_sort,
            hidden_columns=PowerState.hidden_columns,
            empty_message="Tidak ada data server yang cocok",
            empty_subtitle="Coba ubah kata kunci pencarian atau atur ulang filter beban TDP.",
            empty_action_label="Reset filter",
            on_empty_action=PowerState.reset_filters,
        ),
        _estimasi_summary_footer(),
        table_pagination(
            summary_text=PowerState.pagination_summary,
            current_page=PowerState.page,
            current_page_str=PowerState.current_page_str,
            total_pages=PowerState.total_pages,
            page_tokens=PowerState.page_tokens,
            on_prev=PowerState.prev_page,
            on_next=PowerState.next_page,
            on_page_select=PowerState.select_page,
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


def watt_server_page() -> rx.Component:
    """Halaman utama `/watt-server`."""
    content = rx.vstack(
        _watt_header(),
        _watt_kpi_cards(),
        _watt_table_card(),
        detail_drawer(
            is_open=PowerState.drawer_open,
            on_close=PowerState.close_drawer,
            code_var=PowerState.active_code,
            title_var=PowerState.active_title,
            category_var=PowerState.active_category_badge,
            status_var=PowerState.active_status_badge,
            active_tab=PowerState.drawer_tab,
            on_tab_change=PowerState.set_drawer_tab,
            section1_title="Spesifikasi perangkat keras",
            general_items=PowerState.active_general_items,
            section2_title="Konsumsi daya & rekomendasi PSU",
            usage_items=PowerState.active_power_items,
            history_items=PowerState.active_history_items,
            duplicate_label="Duplikat",
            on_edit=lambda _=None: PowerState.open_edit_modal(""),
            on_duplicate=lambda _=None: PowerState.open_duplicate_modal(""),
            on_delete=lambda _=None: PowerState.confirm_delete_entry(""),
            tabs=(("detail", "Spesifikasi & Daya"), ("history", "Riwayat & Catatan")),
        ),
        _watt_form_modal(),
        confirm_delete_dialog(
            is_open=PowerState.delete_dialog_open,
            title="Hapus Data Server?",
            description=(
                f"Apakah Anda yakin ingin menghapus {PowerState.delete_target_label} "
                "dari Rekap Watt Server dan inventaris aset?"
            ),
            on_cancel=PowerState.cancel_delete,
            on_confirm=PowerState.execute_delete_entry,
        ),
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Infrastructure", "Rekap Watt Server"),
    )


__all__ = ["WATT_TABLE_COLUMNS", "watt_server_page"]
