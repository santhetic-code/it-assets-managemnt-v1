"""
Halaman Laporan -> Rekap Watt Server (/watt-server).
Tampilan tabel rekap sederhana sesuai spreadsheet docs/data/rekap_watt_server.csv.
Semua nilai diisi manual oleh user.
"""

from typing import Any

import reflex as rx

from itam_pro.components.feedback import confirm_delete_dialog
from itam_pro.components.layout import base_layout
from itam_pro.components.tables import ColumnDef
from itam_pro.components.ui import (
    action_primary_button,
    app_badge,
    detail_drawer,
    hero_stat_card,
    page_header,
    pill_filter_bar,
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
        "width": "195px",
        "sticky_left": True,
        "sortable": True,
    },
    {"key": "cpu", "header": "CPU", "width": "150px"},
    {"key": "vga", "header": "GPU", "width": "135px"},
    {"key": "ram_storage", "header": "RAM · Penyimpanan", "width": "210px"},
    {"key": "tdp_total_w", "header": "TDP (W)", "width": "95px", "sortable": True},
    {"key": "tdp_psu_ratio", "header": "TDP / PSU Min", "width": "135px", "sortable": True},
    {"key": "psu_min_w", "header": "PSU Min", "width": "95px", "sortable": True},
    {"key": "psu_rekomendasi_w", "header": "PSU Rek", "width": "95px", "sortable": True},
    {"key": "ups", "header": "UPS Penyuplai", "width": "155px"},
    {"key": "status", "header": "Status", "width": "125px"},
]

_TOGGLEABLE_COLUMNS: list[tuple[str, str]] = [
    ("cpu", "CPU"),
    ("vga", "GPU"),
    ("ram_storage", "RAM · Penyimpanan"),
    ("tdp_psu_ratio", "TDP / PSU Min"),
    ("psu_min_w", "PSU Min"),
    ("psu_rekomendasi_w", "PSU Rek"),
    ("ups", "UPS Penyuplai"),
    ("status", "Status"),
]

_KPI_GRID_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1fr 1fr 1fr",
        "gap": Space.S4,
        "align_items": "stretch",
        "@media (max-width: 1150px)": {"grid_template_columns": "repeat(2, minmax(0, 1fr))"},
        "@media (max-width: 599px)": {"grid_template_columns": "1fr"},
    }
)


def _watt_header() -> rx.Component:
    """Header halaman Rekap Watt Server dengan kotak ikon petir gradien biru 52px."""
    return page_header(
        icon="zap",
        title="Rekap Watt Server",
        subtitle=(
            "Kebutuhan daya per server: TDP, PSU minimum, PSU rekomendasi, "
            "dan beban UPS penyuplai."
        ),
        actions=[
            secondary_button("Export", on_click=PowerState.export_watt_excel),
            secondary_button("Cetak A4", on_click=rx.call_script("window.print()")),
            action_primary_button("+ Tambah Server", on_click=PowerState.open_add_modal),
        ],
    )


def _watt_kpi_row() -> rx.Component:
    """5 Kartu KPI: Hero Total TDP (donut % TDP/PSU) + 4 kartu putih interaktif."""
    return rx.box(
        hero_stat_card(
            icon="box",
            label="TOTAL TDP",
            value=PowerState.kpi_total_tdp_display,
            subtext=PowerState.kpi_total_tdp_note,
            percent=PowerState.kpi_tdp_psu_pct,
            percent_caption="TDP/PSU",
            link_text="Lihat detail →",
            on_click=PowerState.reset_filters,
            glow_ring=True,
        ),
        stat_card(
            icon="circle-check",
            tone="purple",
            label="PSU MINIMUM",
            value=PowerState.kpi_psu_min_display,
            subtext=PowerState.kpi_psu_min_note,
            link_text="Lihat detail →",
            on_click=PowerState.toggle_sort("psu_min_w"),
        ),
        stat_card(
            icon="clock",
            tone="success",
            label="PSU REKOMENDASI",
            value=PowerState.kpi_psu_rek_display,
            subtext="acuan pembelian PSU",
            link_text="Lihat detail →",
            on_click=PowerState.toggle_sort("psu_rekomendasi_w"),
        ),
        stat_card(
            icon="shield",
            tone="warning",
            label="EST. ENERGI / BULAN",
            value=PowerState.kpi_est_kwh_display,
            subtext="batas atas (TDP × 24 jam × 30 hari)",
            link_text="Lihat detail →",
            on_click=PowerState.toggle_sort("tdp_total_w"),
        ),
        stat_card(
            icon="zap",
            tone="info",
            label="TDP TERTINGGI",
            value=PowerState.kpi_max_tdp_display,
            subtext=PowerState.kpi_max_tdp_server,
            link_text="Lihat detail →",
            on_click=PowerState.open_highest_tdp_drawer,
        ),
        style=_KPI_GRID_STYLE,
    )


def _col_display(col_key: str) -> Any:
    return rx.cond(PowerState.hidden_columns.contains(col_key), "none", "table-cell")


def _sortable_th(
    label: str,
    sort_key: str,
    *,
    col_key: str = "",
    align_right: bool = False,
    sticky_left: bool = False,
    min_w: str = "110px",
) -> rx.Component:
    is_sorted = PowerState.sort_by == sort_key
    th_style: dict[str, Any] = {
        "position": "sticky",
        "top": "0",
        "background_color": Color.TABLE_HEADER_BG,
        "padding": "12px 14px",
        "font_size": FontSize.GROUP_LABEL,
        "font_weight": FontWeight.EXTRABOLD,
        "color": Color.MUTED,
        "text_transform": "uppercase",
        "letter_spacing": "0.05em",
        "border_bottom": f"1px solid {Color.BORDER}",
        "white_space": "nowrap",
        "min_width": min_w,
        "cursor": "pointer",
        "user_select": "none",
        "z_index": "4" if sticky_left else "2",
    }
    if col_key:
        th_style["display"] = _col_display(col_key)
    if sticky_left:
        th_style["left"] = "0"
        th_style["box_shadow"] = Color.STICKY_COL_SHADOW

    return rx.el.th(
        rx.hstack(
            rx.text(label, font_size=FontSize.GROUP_LABEL, font_weight=FontWeight.EXTRABOLD),
            rx.cond(
                is_sorted,
                rx.text(
                    rx.cond(PowerState.sort_dir == "asc", "↑", "↓"),
                    font_size=FontSize.GROUP_LABEL,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.ACCENT_BRIGHT,
                ),
                rx.text("↕", font_size=FontSize.GROUP_LABEL, color=Color.SLATE_400),
            ),
            spacing="1",
            align="center",
            justify="end" if align_right else "start",
            width="100%",
        ),
        on_click=PowerState.toggle_sort(sort_key),
        style=rx.Style(th_style),
    )


def _static_th(
    label: str,
    *,
    col_key: str = "",
    min_w: str = "130px",
    align_right: bool = False,
) -> rx.Component:
    th_style: dict[str, Any] = {
        "position": "sticky",
        "top": "0",
        "z_index": "2",
        "background_color": Color.TABLE_HEADER_BG,
        "padding": "12px 14px",
        "font_size": FontSize.GROUP_LABEL,
        "font_weight": FontWeight.EXTRABOLD,
        "color": Color.MUTED,
        "text_transform": "uppercase",
        "letter_spacing": "0.05em",
        "text_align": "right" if align_right else "left",
        "border_bottom": f"1px solid {Color.BORDER}",
        "white_space": "nowrap",
        "min_width": min_w,
    }
    if col_key:
        th_style["display"] = _col_display(col_key)
    return rx.el.th(label, style=rx.Style(th_style))


def _server_table_row(row: dict[str, Any]) -> rx.Component:
    """Satu baris data server dengan bar TDP/PSU Min, chip UPS, status, dan klik drawer."""
    row_bg = rx.match(
        row["power_status"],
        ("Kritis", Color.DANGER_ROW_BG),
        ("Waspada", Color.WARNING_ROW_BG),
        Color.SURFACE,
    )
    bar_color = rx.match(
        row["power_status"],
        ("Kritis", Color.PROGRESS_HIGH),
        ("Waspada", Color.PROGRESS_MED),
        Color.PROGRESS_LOW,
    )
    cell_base: dict[str, Any] = {
        "padding": "12px 14px",
        "font_size": FontSize.SM,
        "color": Color.TEXT,
        "border_bottom": f"1px solid {Color.DIVIDER}",
        "background_color": row_bg,
        "vertical_align": "middle",
    }
    num_cell_base: dict[str, Any] = {
        **cell_base,
        "text_align": "right",
        "font_variant_numeric": "tabular-nums",
        "white_space": "nowrap",
    }
    return rx.el.tr(
        # 1. ID Server (sticky left)
        rx.el.td(
            rx.text(
                row["nama_aset"],
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            style=rx.Style(
                {
                    **cell_base,
                    "position": "sticky",
                    "left": "0",
                    "z_index": "1",
                    "box_shadow": Color.STICKY_COL_SHADOW,
                    "white_space": "nowrap",
                }
            ),
        ),
        # 2. CPU (ringkas + tooltip penuh)
        rx.el.td(
            rx.text(row["cpu_short"], title=row["cpu"], white_space="nowrap"),
            style=rx.Style({**cell_base, "display": _col_display("cpu")}),
        ),
        # 3. GPU (ringkas + tooltip penuh)
        rx.el.td(
            rx.text(row["vga_short"], title=row["vga"], white_space="nowrap"),
            style=rx.Style({**cell_base, "display": _col_display("vga")}),
        ),
        # 4. RAM · Penyimpanan (ringkas + tooltip penuh)
        rx.el.td(
            rx.text(
                row["ram_storage_short"],
                title=f"{row['ram']} · {row['hdd_ssd']}",
                white_space="nowrap",
            ),
            style=rx.Style({**cell_base, "display": _col_display("ram_storage")}),
        ),
        # 5. TDP (W) (rata kanan)
        rx.el.td(
            row["tdp_num_display"],
            style=rx.Style({**num_cell_base, "font_weight": FontWeight.EXTRABOLD}),
        ),
        # 6. TDP / PSU Min (progress bar + warna ambang)
        rx.el.td(
            rx.box(
                rx.box(
                    style=rx.Style(
                        {
                            "width": row["tdp_psu_bar_width"],
                            "height": "100%",
                            "background_color": bar_color,
                            "border_radius": Radius.FULL,
                            "transition": "width 0.2s ease",
                        }
                    )
                ),
                title=f"{row['tdp_psu_ratio_pct']}% dari PSU minimum",
                style=rx.Style(
                    {
                        "width": "100%",
                        "min_width": "88px",
                        "height": Size.PROGRESS_H,
                        "background_color": Color.PROGRESS_TRACK,
                        "border_radius": Radius.FULL,
                        "overflow": "hidden",
                    }
                ),
            ),
            style=rx.Style({**cell_base, "display": _col_display("tdp_psu_ratio")}),
        ),
        # 7. PSU Min (rata kanan)
        rx.el.td(
            row["psu_min_num_display"],
            style=rx.Style(
                {
                    **num_cell_base,
                    "font_weight": FontWeight.MEDIUM,
                    "display": _col_display("psu_min_w"),
                }
            ),
        ),
        # 8. PSU Rek (rata kanan)
        rx.el.td(
            row["psu_rek_num_display"],
            style=rx.Style(
                {
                    **num_cell_base,
                    "font_weight": FontWeight.MEDIUM,
                    "display": _col_display("psu_rekomendasi_w"),
                }
            ),
        ),
        # 9. UPS Penyuplai (chip biru bila tertaut, teks muted bila belum ditautkan)
        rx.el.td(
            rx.cond(
                row["has_ups"],
                app_badge(label=row["ups_chip_label"], variant="info"),
                rx.text(
                    "Belum ditautkan",
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                    white_space="nowrap",
                ),
            ),
            style=rx.Style({**cell_base, "white_space": "nowrap", "display": _col_display("ups")}),
        ),
        # 10. Status (Aman / Waspada / Kritis)
        rx.el.td(
            app_badge(label=row["power_status_label"], variant=row["power_status_variant"]),
            style=rx.Style(
                {**cell_base, "white_space": "nowrap", "display": _col_display("status")}
            ),
        ),
        on_click=PowerState.open_detail_drawer(row["id_aset"]),
        style=rx.Style({"cursor": "pointer"}),
        _hover=rx.Style({"filter": "brightness(0.985)"}),
    )


def _pinned_estimasi_row() -> rx.Component:
    """Baris ESTIMASI sticky bottom dengan sel 1-per-1 agar sejajar saat kolom disembunyikan."""
    est_cell: dict[str, Any] = {
        "position": "sticky",
        "bottom": "0",
        "z_index": "2",
        "background_color": Color.TABLE_HEADER_BG,
        "padding": "12px 14px",
        "border_top": f"1.5px solid {Color.BORDER}",
        "font_size": FontSize.SM,
        "font_weight": FontWeight.EXTRABOLD,
        "color": Color.TEXT,
        "white_space": "nowrap",
    }
    est_num: dict[str, Any] = {
        **est_cell,
        "text_align": "right",
        "font_variant_numeric": "tabular-nums",
    }
    return rx.el.tfoot(
        rx.el.tr(
            rx.el.td(
                rx.vstack(
                    rx.text("ESTIMASI", font_size=FontSize.SM, font_weight=FontWeight.EXTRABOLD),
                    rx.text(
                        PowerState.estimasi_search_subnote,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.MEDIUM,
                        color=Color.MUTED,
                    ),
                    spacing="0",
                    align="start",
                ),
                style=rx.Style(
                    {
                        **est_cell,
                        "left": "0",
                        "z_index": "3",
                        "box_shadow": Color.STICKY_ESTIMASI_SHADOW,
                    }
                ),
            ),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("cpu")})),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("vga")})),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("ram_storage")})),
            rx.el.td(PowerState.estimasi_tdp_display, style=rx.Style(est_num)),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("tdp_psu_ratio")})),
            rx.el.td(
                PowerState.estimasi_psu_min_display,
                style=rx.Style({**est_num, "display": _col_display("psu_min_w")}),
            ),
            rx.el.td(
                PowerState.estimasi_psu_rek_display,
                style=rx.Style({**est_num, "display": _col_display("psu_rekomendasi_w")}),
            ),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("ups")})),
            rx.el.td("", style=rx.Style({**est_cell, "display": _col_display("status")})),
        )
    )


def _column_chooser_popover() -> rx.Component:
    """Popover 'Atur kolom' untuk menyembunyikan/menampilkan kolom tabel Watt Server."""
    return rx.popover.root(
        rx.popover.trigger(
            rx.el.button(
                "Atur kolom",
                type="button",
                style=rx.Style(
                    {
                        "height": Size.FILTER_CONTROL_H,
                        "padding": "0 14px",
                        "background_color": Color.SURFACE,
                        "color": Color.TEXT,
                        "border": f"1px solid {Color.INPUT_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.SEMIBOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
            )
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "TAMPILKAN KOLOM",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.BOLD,
                        color=Color.MUTED,
                    ),
                    rx.el.button(
                        "Default",
                        type="button",
                        on_click=PowerState.reset_column_visibility,
                        style=rx.Style(
                            {
                                "background": "transparent",
                                "border": "none",
                                "color": Color.ACCENT,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                ),
                *[
                    rx.el.label(
                        rx.hstack(
                            rx.el.input(
                                type="checkbox",
                                checked=~PowerState.hidden_columns.contains(col_key),
                                on_change=PowerState.toggle_column_visibility(col_key),
                                style=rx.Style(
                                    {
                                        "width": Size.TABLE_CHECKBOX,
                                        "height": Size.TABLE_CHECKBOX,
                                        "accent_color": Color.ACCENT,
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.text(col_label, font_size=FontSize.SM, color=Color.TEXT),
                            spacing="2",
                            align="center",
                        ),
                        style=rx.Style({"cursor": "pointer", "padding": "3px 0"}),
                    )
                    for col_key, col_label in _TOGGLEABLE_COLUMNS
                ],
                spacing="1",
                width="200px",
                align="start",
            ),
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CONTROL,
                    "box_shadow": Shadow.POPOVER,
                    "padding": "12px 14px",
                }
            ),
        ),
    )


def _watt_table_card() -> rx.Component:
    """Kartu Tabel Rekap Watt Server dengan Pill Filter Bar, Atur kolom, & ESTIMASI sticky."""
    return rx.box(
        pill_filter_bar(
            search_placeholder="Cari ID server, CPU, GPU, RAM...",
            search_value=PowerState.search_query,
            on_search_change=PowerState.set_search_query,
            search_width="260px",
            selects=[
                {
                    "placeholder": "Semua status",
                    "options": PowerState.status_options,
                    "value": PowerState.status_filter,
                    "on_change": PowerState.set_status_filter,
                },
                {
                    "placeholder": "Semua UPS",
                    "options": PowerState.ups_options,
                    "value": PowerState.ups_filter,
                    "on_change": PowerState.set_ups_filter,
                },
            ],
            on_reset=PowerState.reset_filters,
            right_slot=rx.hstack(
                _column_chooser_popover(),
                rx.text(
                    PowerState.result_count_label,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.MUTED,
                    white_space="nowrap",
                ),
                spacing="3",
                align="center",
            ),
        ),
        rx.box(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _sortable_th("ID Server", "nama_aset", sticky_left=True, min_w="185px"),
                        _static_th("CPU", col_key="cpu", min_w="140px"),
                        _static_th("GPU", col_key="vga", min_w="120px"),
                        _static_th("RAM · Penyimpanan", col_key="ram_storage", min_w="195px"),
                        _sortable_th("TDP (W)", "tdp_total_w", align_right=True, min_w="90px"),
                        _sortable_th(
                            "TDP / PSU Min",
                            "tdp_psu_ratio_pct",
                            col_key="tdp_psu_ratio",
                            min_w="125px",
                        ),
                        _sortable_th(
                            "PSU Min",
                            "psu_min_w",
                            col_key="psu_min_w",
                            align_right=True,
                            min_w="90px",
                        ),
                        _sortable_th(
                            "PSU Rek",
                            "psu_rekomendasi_w",
                            col_key="psu_rekomendasi_w",
                            align_right=True,
                            min_w="90px",
                        ),
                        _static_th("UPS Penyuplai", col_key="ups", min_w="145px"),
                        _static_th("Status", col_key="status", min_w="120px"),
                    )
                ),
                rx.el.tbody(rx.foreach(PowerState.items, _server_table_row)),
                _pinned_estimasi_row(),
                style=rx.Style(
                    {
                        "width": "100%",
                        "border_collapse": "separate",
                        "border_spacing": "0",
                        "font_family": FONT_FAMILY,
                    }
                ),
            ),
            style=rx.Style(
                {
                    "width": "100%",
                    "max_height": "calc(100vh - 340px)",
                    "overflow_x": "auto",
                    "overflow_y": "auto",
                }
            ),
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


def _inline_field_error(err_var: Any) -> rx.Component:
    return rx.cond(
        err_var != "",
        rx.text(
            err_var,
            font_size=FontSize.XS,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.DANGER_FG,
        ),
        rx.fragment(),
    )


def _watt_form_modal() -> rx.Component:
    """Modal input/edit manual data Rekap Watt Server dengan validasi inline."""
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
                                "Isi manual sesuai data spesifikasi server.",
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
                        _inline_field_error(PowerState.form_nama_error),
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
                        _inline_field_error(PowerState.form_cpu_error),
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
                                _inline_field_error(PowerState.form_tdp_error),
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
                                _inline_field_error(PowerState.form_psu_min_error),
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
                                _inline_field_error(PowerState.form_psu_rek_error),
                                width="34%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                            align="start",
                        ),
                        rx.text(
                            "Catatan (opsional)",
                            font_size=FontSize.SM,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.TEXT,
                        ),
                        rx.el.textarea(
                            placeholder="Catatan tambahan server (opsional)...",
                            value=PowerState.form_catatan,
                            on_change=PowerState.set_form_catatan,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "68px",
                                    "padding": "8px 12px",
                                    "background_color": Color.SURFACE,
                                    "color": Color.TEXT,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "outline": "none",
                                    "box_sizing": "border-box",
                                    "resize": "none",
                                }
                            ),
                        ),
                        spacing="2",
                        width="100%",
                        align="start",
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=PowerState.close_form_modal),
                        action_primary_button(
                            "Simpan Data Server",
                            on_click=PowerState.submit_form,
                        ),
                        spacing="2",
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
                        "width": "540px",
                        "max_width": "92vw",
                        "max_height": "90vh",
                        "overflow_y": "auto",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.MODAL,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _drawer_spec_row(label: str, value: Any) -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size=FontSize.SM, color=Color.MUTED, width="38%", flex_shrink="0"),
        rx.text(
            value,
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
            width="62%",
            text_align="right",
        ),
        width="100%",
        justify="between",
        align="start",
        padding_y="7px",
        style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
    )


def _watt_detail_drawer() -> rx.Component:
    """Drawer detail server: spesifikasi lengkap, riwayat pengeditan, dan tombol Edit."""
    custom_header = rx.vstack(
        rx.hstack(
            rx.text(
                PowerState.selected_id_aset,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.ACCENT,
            ),
            rx.el.button(
                rx.icon(tag="x", size=18, color=Color.MUTED),
                type="button",
                aria_label="Tutup detail server",
                on_click=PowerState.close_detail_drawer,
                style=rx.Style(
                    {
                        "width": "34px",
                        "height": "34px",
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CONTROL,
                        "background_color": Color.SURFACE,
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                        "justify_content": "center",
                    }
                ),
            ),
            width="100%",
            justify="between",
            align="center",
        ),
        rx.heading(
            PowerState.selected_nama_aset,
            font_size=FontSize.LOGO,
            font_weight=FontWeight.EXTRABOLD,
            color=Color.TEXT,
        ),
        rx.hstack(
            app_badge(
                label=PowerState.selected_power_status_label,
                variant=PowerState.selected_power_status_variant,
            ),
            app_badge(label=PowerState.selected_ups_chip_label, variant="info"),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        spacing="2",
        align="start",
        width="100%",
        padding="20px 24px 16px 24px",
        style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
    )

    custom_body = rx.vstack(
        rx.vstack(
            rx.text(
                "SPESIFIKASI LENGKAP",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            _drawer_spec_row("Model Prosesor (CPU)", PowerState.selected_cpu),
            _drawer_spec_row("Kartu Grafis (GPU)", PowerState.selected_vga),
            _drawer_spec_row("Konfigurasi RAM", PowerState.selected_ram),
            _drawer_spec_row("Penyimpanan", PowerState.selected_hdd_ssd),
            _drawer_spec_row("Lokasi", PowerState.selected_lokasi),
            _drawer_spec_row("Catatan", PowerState.selected_catatan),
            spacing="0",
            width="100%",
        ),
        rx.vstack(
            rx.text(
                "KEBUTUHAN DAYA & UPS",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            _drawer_spec_row("Total TDP", PowerState.selected_tdp_display),
            _drawer_spec_row("Rasio TDP / PSU Min", PowerState.selected_tdp_psu_ratio_display),
            _drawer_spec_row("PSU Minimum", PowerState.selected_psu_min_display),
            _drawer_spec_row("PSU Rekomendasi", PowerState.selected_psu_rek_display),
            _drawer_spec_row("Est. Energi / Bulan (batas atas)", PowerState.selected_kwh_display),
            _drawer_spec_row("UPS Penyuplai", PowerState.selected_ups_chip_label),
            spacing="0",
            width="100%",
        ),
        rx.vstack(
            rx.text(
                "RIWAYAT PENGEDITAN",
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                letter_spacing="0.06em",
            ),
            rx.cond(
                PowerState.has_edit_history,
                rx.vstack(
                    rx.foreach(
                        PowerState.selected_edit_history,
                        lambda h: rx.vstack(
                            rx.hstack(
                                rx.text(
                                    h["pelaku"],
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.TEXT,
                                ),
                                rx.text(h["waktu"], font_size=FontSize.XS, color=Color.MUTED),
                                width="100%",
                                justify="between",
                            ),
                            rx.text(h["detail"], font_size=FontSize.SM, color=Color.TEXT),
                            spacing="1",
                            align="start",
                            width="100%",
                            padding="8px 10px",
                            style=rx.Style(
                                {
                                    "background_color": Color.TABLE_HEADER_BG,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": Radius.CONTROL,
                                }
                            ),
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.text(
                    "Belum ada riwayat pengeditan tercatat untuk server ini.",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        spacing="5",
        align="start",
        width="100%",
    )

    custom_footer = rx.hstack(
        action_primary_button("Edit Server", on_click=PowerState.open_edit_from_drawer),
        secondary_button("Duplikat", on_click=PowerState.open_duplicate_from_drawer),
        rx.el.button(
            "Hapus",
            type="button",
            on_click=PowerState.confirm_delete_from_drawer,
            style=rx.Style(
                {
                    "height": Size.BUTTON_MD_H,
                    "padding": "0 14px",
                    "background_color": Color.DANGER_BG,
                    "color": Color.DANGER_FG,
                    "border": f"1px solid {Color.DANGER_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.BOLD,
                    "cursor": "pointer",
                }
            ),
        ),
        width="100%",
        justify="start",
        spacing="2",
        padding="14px 24px",
        style=rx.Style(
            {
                "border_top": f"1px solid {Color.BORDER}",
                "background_color": Color.SURFACE,
            }
        ),
    )

    return detail_drawer(
        is_open=PowerState.drawer_open,
        on_close=PowerState.close_detail_drawer,
        custom_header=custom_header,
        custom_body=custom_body,
        custom_footer=custom_footer,
        show_tabs=False,
        aria_label="Detail Rekap Watt Server",
    )


def watt_server_page() -> rx.Component:
    """Halaman utama `/watt-server` (KPI 5 kartu, tabel TDP/PSU/UPS, drawer detail, & CRUD)."""
    content = rx.vstack(
        _watt_header(),
        _watt_kpi_row(),
        _watt_table_card(),
        _watt_detail_drawer(),
        _watt_form_modal(),
        confirm_delete_dialog(
            is_open=PowerState.delete_dialog_open,
            title="Hapus Data Watt Server",
            description=(
                f"Yakin ingin menghapus {PowerState.delete_target_label} "
                "dari Rekap Watt Server?"
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
        breadcrumb=("Laporan", "Rekap Watt Server"),
    )


__all__ = ["WATT_TABLE_COLUMNS", "watt_server_page"]
