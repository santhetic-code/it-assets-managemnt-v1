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
from itam_pro.components.ui import action_primary_button, secondary_button
from itam_pro.states.power_state import PowerState
from itam_pro.styles import (
    FONT_FAMILY,
    Color,
    FontSize,
    FontWeight,
    Radius,
    Size,
    Space,
)

WATT_TABLE_COLUMNS: list[ColumnDef] = [
    {"key": "no", "header": "No", "width": "52px", "min_width": "48px", "render_type": "text"},
    {
        "key": "nama_aset",
        "header": "ID Server",
        "width": "220px",
        "min_width": "195px",
        "render_type": "bold",
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
    },
    {
        "key": "vga",
        "header": "Kartu Grafis (GPU)",
        "width": "230px",
        "min_width": "190px",
        "render_type": "text",
    },
    {
        "key": "ram",
        "header": "Konfigurasi RAM",
        "width": "195px",
        "min_width": "170px",
        "render_type": "text",
    },
    {
        "key": "hdd_ssd",
        "header": "Konfigurasi Penyimpanan",
        "width": "210px",
        "min_width": "180px",
        "render_type": "text",
    },
    {
        "key": "tdp_num_display",
        "header": "Total TDP (W)",
        "width": "135px",
        "min_width": "125px",
        "render_type": "bold_blue",
        "sortable": True,
        "sort_key": "tdp_total_w",
    },
    {
        "key": "psu_min_num_display",
        "header": "PSU Minimum (W)",
        "width": "150px",
        "min_width": "135px",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "psu_min_w",
    },
    {
        "key": "psu_rek_num_display",
        "header": "PSU Rekomendasi (W)",
        "width": "170px",
        "min_width": "155px",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "psu_rekomendasi_w",
    },
]


def _watt_header() -> rx.Component:
    """Header halaman Rekap Watt Server dengan chip petir dan tombol + Tambah Server."""
    return rx.hstack(
        rx.hstack(
            rx.center(
                rx.icon(tag="zap", size=24, color=Color.ACCENT_BRIGHT),
                width="48px",
                height="48px",
                background_color=Color.INFO_BG,
                border=f"1px solid {Color.BLUE_BORDER}",
                border_radius=Radius.CARD,
                flex_shrink="0",
            ),
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
                    "Rekap kebutuhan daya per server: TDP, PSU minimum, dan PSU rekomendasi. "
                    "Data diisi manual.",
                    font_size=FontSize.BASE,
                    color=Color.MUTED,
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        rx.hstack(
            secondary_button("Export", on_click=PowerState.export_watt_excel),
            secondary_button("Cetak A4", on_click=rx.call_script("window.print()")),
            action_primary_button("+ Tambah Server", on_click=PowerState.open_add_modal),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
    )


def _sortable_th(
    label: str,
    sort_key: str,
    *,
    align_right: bool = False,
    sticky_left: bool = False,
    min_w: str = "130px",
) -> rx.Component:
    is_sorted = PowerState.sort_by == sort_key
    th_style: dict[str, Any] = {
        "position": "sticky",
        "top": "0",
        "background_color": Color.TABLE_HEADER_BG,
        "padding": "12px 14px",
        "font_size": "11px",
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
    if sticky_left:
        th_style["left"] = "0"
        th_style["box_shadow"] = "1px 0 0 0 rgba(226, 232, 240, 1)"

    return rx.el.th(
        rx.hstack(
            rx.text(label, font_size="11px", font_weight=FontWeight.EXTRABOLD),
            rx.cond(
                is_sorted,
                rx.text(
                    rx.cond(PowerState.sort_dir == "asc", "↑", "↓"),
                    font_size="11px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.ACCENT_BRIGHT,
                ),
                rx.text("↕", font_size="11px", color=Color.SLATE_400),
            ),
            spacing="1",
            align="center",
            justify="end" if align_right else "start",
            width="100%",
        ),
        on_click=PowerState.toggle_sort(sort_key),
        style=rx.Style(th_style),
    )


def _static_th(label: str, *, min_w: str = "140px", align_center: bool = False) -> rx.Component:
    return rx.el.th(
        label,
        style=rx.Style(
            {
                "position": "sticky",
                "top": "0",
                "z_index": "2",
                "background_color": Color.TABLE_HEADER_BG,
                "padding": "12px 14px",
                "font_size": "11px",
                "font_weight": FontWeight.EXTRABOLD,
                "color": Color.MUTED,
                "text_transform": "uppercase",
                "letter_spacing": "0.05em",
                "text_align": "center" if align_center else "left",
                "border_bottom": f"1px solid {Color.BORDER}",
                "white_space": "nowrap",
                "min_width": min_w,
            }
        ),
    )


def _server_table_row(row: dict[str, Any]) -> rx.Component:
    """Satu baris data server sesuai urutan kolom spreadsheet."""
    cell_base = {
        "padding": "11px 14px",
        "font_size": FontSize.SM,
        "color": Color.TEXT,
        "border_bottom": f"1px solid {Color.DIVIDER}",
        "background_color": Color.SURFACE,
    }
    num_cell_base = {
        **cell_base,
        "text_align": "right",
        "font_variant_numeric": "tabular-nums",
        "white_space": "nowrap",
    }
    return rx.el.tr(
        rx.el.td(
            row["no"],
            style=rx.Style(
                {
                    **cell_base,
                    "color": Color.MUTED,
                    "font_variant_numeric": "tabular-nums",
                    "width": "48px",
                }
            ),
        ),
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
                    "box_shadow": "1px 0 0 0 rgba(226, 232, 240, 1)",
                    "white_space": "nowrap",
                }
            ),
        ),
        rx.el.td(row["cpu"], style=rx.Style(cell_base)),
        rx.el.td(row["vga"], style=rx.Style(cell_base)),
        rx.el.td(row["ram"], style=rx.Style(cell_base)),
        rx.el.td(row["hdd_ssd"], style=rx.Style(cell_base)),
        rx.el.td(
            row["tdp_num_display"],
            style=rx.Style(
                {
                    **num_cell_base,
                    "font_weight": FontWeight.EXTRABOLD,
                    "color": Color.ACCENT_BRIGHT,
                }
            ),
        ),
        rx.el.td(
            row["psu_min_num_display"],
            style=rx.Style({**num_cell_base, "font_weight": FontWeight.SEMIBOLD}),
        ),
        rx.el.td(
            row["psu_rek_num_display"],
            style=rx.Style({**num_cell_base, "font_weight": FontWeight.SEMIBOLD}),
        ),
        rx.el.td(
            rx.hstack(
                rx.el.button(
                    rx.icon(tag="pencil", size=14, color=Color.TEXT),
                    type="button",
                    title="Edit Server",
                    on_click=PowerState.open_edit_modal(row["id_aset"]),
                    style=rx.Style(
                        {
                            "width": "28px",
                            "height": "28px",
                            "display": "inline-flex",
                            "align_items": "center",
                            "justify_content": "center",
                            "background_color": Color.SURFACE,
                            "border": f"1px solid {Color.BORDER}",
                            "border_radius": "6px",
                            "cursor": "pointer",
                        }
                    ),
                ),
                rx.el.button(
                    rx.icon(tag="copy", size=14, color=Color.ACCENT_BRIGHT),
                    type="button",
                    title="Duplikat Server",
                    on_click=PowerState.open_duplicate_modal(row["id_aset"]),
                    style=rx.Style(
                        {
                            "width": "28px",
                            "height": "28px",
                            "display": "inline-flex",
                            "align_items": "center",
                            "justify_content": "center",
                            "background_color": Color.INFO_BG,
                            "border": f"1px solid {Color.BLUE_BORDER}",
                            "border_radius": "6px",
                            "cursor": "pointer",
                        }
                    ),
                ),
                rx.el.button(
                    rx.icon(tag="trash-2", size=14, color=Color.DANGER_FG),
                    type="button",
                    title="Hapus Server",
                    on_click=PowerState.confirm_delete_entry(row["id_aset"]),
                    style=rx.Style(
                        {
                            "width": "28px",
                            "height": "28px",
                            "display": "inline-flex",
                            "align_items": "center",
                            "justify_content": "center",
                            "background_color": Color.DANGER_BG,
                            "border": f"1px solid {Color.DANGER_BORDER}",
                            "border_radius": "6px",
                            "cursor": "pointer",
                        }
                    ),
                ),
                spacing="1",
                justify="center",
                align="center",
            ),
            style=rx.Style({**cell_base, "text_align": "center", "white_space": "nowrap"}),
        ),
    )


def _pinned_estimasi_row() -> rx.Component:
    """Baris ESTIMASI yang dipin (sticky bottom) dengan background biru muda."""
    est_cell = {
        "position": "sticky",
        "bottom": "0",
        "z_index": "2",
        "background_color": Color.INFO_BG,
        "padding": "12px 14px",
        "border_top": f"2px solid {Color.BLUE_BORDER}",
        "font_size": FontSize.SM,
        "font_weight": FontWeight.EXTRABOLD,
        "color": Color.TEXT,
    }
    est_num = {
        **est_cell,
        "text_align": "right",
        "font_variant_numeric": "tabular-nums",
        "white_space": "nowrap",
    }
    return rx.el.tfoot(
        rx.el.tr(
            rx.el.td("", style=rx.Style(est_cell)),
            rx.el.td(
                "ESTIMASI",
                style=rx.Style(
                    {
                        **est_cell,
                        "left": "0",
                        "z_index": "3",
                        "letter_spacing": "0.04em",
                        "box_shadow": "1px 0 0 0 rgba(191, 219, 254, 1)",
                    }
                ),
            ),
            rx.el.td(
                rx.text(
                    PowerState.estimasi_search_subnote,
                    font_size=FontSize.XS,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.MUTED,
                ),
                col_span=4,
                style=rx.Style(est_cell),
            ),
            rx.el.td(
                PowerState.estimasi_tdp_display,
                style=rx.Style({**est_num, "color": Color.ACCENT_BRIGHT}),
            ),
            rx.el.td(PowerState.estimasi_psu_min_display, style=rx.Style(est_num)),
            rx.el.td(PowerState.estimasi_psu_rek_display, style=rx.Style(est_num)),
            rx.el.td("", style=rx.Style(est_cell)),
        )
    )


def _watt_table_card() -> rx.Component:
    """Kartu Tabel Rekap Watt Server dengan kotak pencarian sederhana dan baris ESTIMASI sticky."""
    return rx.box(
        # Bar Pencarian Sederhana (Tanpa Tab & Tanpa Dropdown)
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon(
                        tag="search",
                        size=15,
                        color=Color.MUTED,
                        style=rx.Style(
                            {
                                "position": "absolute",
                                "left": "12px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                                "pointer_events": "none",
                            }
                        ),
                    ),
                    rx.el.input(
                        type="text",
                        placeholder="Cari ID server, CPU, GPU, RAM, penyimpanan...",
                        value=PowerState.search_query,
                        on_change=PowerState.set_search_query,
                        style=rx.Style(
                            {
                                "width": "340px",
                                "max_width": "100%",
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 12px 0 36px",
                                "background_color": Color.SURFACE,
                                "color": Color.TEXT,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "outline": "none",
                            }
                        ),
                    ),
                    style=rx.Style({"position": "relative"}),
                ),
                rx.cond(
                    PowerState.has_search,
                    rx.el.button(
                        "Reset",
                        type="button",
                        on_click=PowerState.reset_filters,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 12px",
                                "background": "transparent",
                                "border": "none",
                                "color": Color.ACCENT_BRIGHT,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                PowerState.result_count_label,
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            padding="14px 18px",
            style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
        ),
        # Area Tabel Scrollable dengan Header Sticky Top & Baris ESTIMASI Sticky Bottom
        rx.box(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _static_th("No", min_w="48px"),
                        _sortable_th("ID Server", "nama_aset", sticky_left=True, min_w="200px"),
                        _static_th("Model Prosesor (CPU)", min_w="230px"),
                        _static_th("Kartu Grafis (GPU)", min_w="210px"),
                        _static_th("Konfigurasi RAM", min_w="180px"),
                        _static_th("Konfigurasi Penyimpanan", min_w="195px"),
                        _sortable_th(
                            "Total TDP (W)",
                            "tdp_total_w",
                            align_right=True,
                            min_w="135px",
                        ),
                        _sortable_th(
                            "PSU Minimum (W)",
                            "psu_min_w",
                            align_right=True,
                            min_w="150px",
                        ),
                        _sortable_th(
                            "PSU Rekomendasi (W)",
                            "psu_rekomendasi_w",
                            align_right=True,
                            min_w="170px",
                        ),
                        _static_th("Aksi", min_w="110px", align_center=True),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(PowerState.items, _server_table_row),
                ),
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
                    "max_height": "calc(100vh - 230px)",
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
                "border_radius": Radius.CARD,
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
                        "box_shadow": "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def watt_server_page() -> rx.Component:
    """Halaman utama `/watt-server` (Tabel Rekap Manual sesuai spreadsheet)."""
    content = rx.vstack(
        _watt_header(),
        _watt_table_card(),
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
