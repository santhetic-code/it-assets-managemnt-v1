"""
Komponen Modal Form Tambah / Edit Monitor ITAM Pro.
Mendukung combobox Merk & Resolusi (pilih atau ketik baru), input ukuran + satuan inci,
checkbox group konektivitas, validasi ID unik, 'Simpan & tambah lagi', dan 'Duplikat'.
"""
from typing import Any

import reflex as rx

from itam_pro.states.monitor_state import MonitorState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space


def _field_label(text: str, required: bool = False) -> rx.Component:
    return rx.hstack(
        rx.text(
            text,
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
        ),
        rx.text(
            "*",
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.DANGER_FG,
        )
        if required
        else rx.fragment(),
        spacing="1",
        align="center",
    )


def _text_input(
    value: Any,
    on_change: Any,
    placeholder: str = "",
    list_id: str | None = None,
) -> rx.Component:
    return rx.el.input(
        type="text",
        value=value,
        on_change=on_change,
        placeholder=placeholder,
        list=list_id,
        style=rx.Style(
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
            }
        ),
        _focus=rx.Style(
            {
                "border_color": Color.ACCENT,
                "box_shadow": Color.FOCUS_RING,
            }
        ),
    )


def _inch_input() -> rx.Component:
    """Input ukuran layar berupa angka + addon satuan 'inci'."""
    return rx.hstack(
        rx.el.input(
            type="text",
            input_mode="decimal",
            value=MonitorState.form_ukuran_layar,
            on_change=MonitorState.set_form_ukuran_layar,
            placeholder="24 / 21,5 / 23,8",
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "100%",
                    "padding": "0 12px",
                    "border": "none",
                    "outline": "none",
                    "background": "transparent",
                    "color": Color.TEXT,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.SEMIBOLD,
                }
            ),
        ),
        rx.center(
            rx.text(
                'inci (")',
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
                white_space="nowrap",
            ),
            height="100%",
            padding_x="12px",
            style=rx.Style(
                {
                    "background_color": Color.TABLE_HEADER_BG,
                    "border_left": f"1px solid {Color.INPUT_BORDER}",
                }
            ),
        ),
        spacing="0",
        align="center",
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.FILTER_CONTROL_H,
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "overflow": "hidden",
            }
        ),
        _focus_within=rx.Style(
            {
                "border_color": Color.ACCENT,
                "box_shadow": Color.FOCUS_RING,
            }
        ),
    )


def _connector_checkbox_chip(port: Any) -> rx.Component:
    """Item checkbox group untuk pilihan Konektivitas Monitor."""
    form_konektivitas: Any = MonitorState.form_konektivitas
    is_checked = form_konektivitas.contains(port)
    return rx.el.label(
        rx.hstack(
            rx.el.input(
                type="checkbox",
                checked=is_checked,
                on_change=MonitorState.toggle_form_konektivitas(port),
                style=rx.Style(
                    {
                        "width": "16px",
                        "height": "16px",
                        "accent_color": Color.ACCENT,
                        "cursor": "pointer",
                        "margin": "0",
                    }
                ),
            ),
            rx.text(
                port,
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=rx.cond(is_checked, Color.ACCENT, Color.TEXT),
                user_select="none",
            ),
            spacing="2",
            align="center",
        ),
        style=rx.Style(
            {
                "padding": "8px 14px",
                "background_color": rx.cond(is_checked, Color.INFO_BG, Color.TABLE_HEADER_BG),
                "border": rx.cond(
                    is_checked,
                    f"1px solid {Color.ACCENT}",
                    f"1px solid {Color.INPUT_BORDER}",
                ),
                "border_radius": Radius.CONTROL,
                "cursor": "pointer",
                "display": "inline-flex",
                "align_items": "center",
                "transition": "all 0.12s ease",
            }
        ),
    )


def _section_title(title: str) -> rx.Component:
    """Pemisah visual bagian form."""
    return rx.box(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.MUTED,
            letter_spacing="0.06em",
        ),
        rx.divider(border_color=Color.BORDER),
        width="100%",
        margin_y=Space.S2,
    )


def _select_input(
    options_var: Any,
    value: Any,
    on_change: Any,
) -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.foreach(
                options_var,
                lambda opt: rx.el.option(opt, value=opt),
            ),
            value=value,
            on_change=on_change,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 32px 0 12px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "outline": "none",
                    "cursor": "pointer",
                    "appearance": "none",
                    "-webkit-appearance": "none",
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=15,
            color=Color.MUTED,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "10px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "pointer_events": "none",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "width": "100%"}),
    )


def _status_select() -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.foreach(
                MonitorState.master_status_options,
                lambda opt: rx.el.option(opt, value=opt),
            ),
            value=MonitorState.form_status,
            on_change=MonitorState.set_form_status,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 32px 0 12px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "outline": "none",
                    "cursor": "pointer",
                    "appearance": "none",
                    "-webkit-appearance": "none",
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=15,
            color=Color.MUTED,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "10px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "pointer_events": "none",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "width": "100%"}),
    )


def monitor_form_modal() -> rx.Component:
    """Modal Form Tambah / Edit / Duplikat Monitor."""
    return rx.cond(
        MonitorState.form_modal_open,
        rx.box(
            # Datalist untuk combobox Merk dan Resolusi
            rx.el.datalist(
                rx.foreach(
                    MonitorState.master_merk_options,
                    lambda m: rx.el.option(value=m),
                ),
                id="monitor-merk-datalist",
            ),
            rx.el.datalist(
                rx.foreach(
                    MonitorState.master_resolusi_options,
                    lambda r: rx.el.option(value=r),
                ),
                id="monitor-resolusi-datalist",
            ),
            # Scrim Backdrop
            rx.box(
                on_click=MonitorState.close_form_modal,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.SCRIM,
                        "z_index": "80",
                    }
                ),
            ),
            # Kontainer Modal
            rx.box(
                # Header Modal
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            rx.cond(
                                MonitorState.form_mode == "edit",
                                f"Edit Monitor · {MonitorState.form_original_id}",
                                "Tambah Monitor Baru",
                            ),
                            font_size=FontSize.LOGO,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Pilih Merk & Resolusi yang ada atau ketik nilai baru untuk "
                            "menambahkannya ke daftar master.",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        aria_label="Tutup form monitor",
                        on_click=MonitorState.close_form_modal,
                        style=rx.Style(
                            {
                                "width": "34px",
                                "height": "34px",
                                "background_color": Color.TABLE_HEADER_BG,
                                "border": f"1px solid {Color.BORDER}",
                                "border_radius": Radius.CONTROL,
                                "display": "inline-flex",
                                "align_items": "center",
                                "justify_content": "center",
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    width="100%",
                    justify="between",
                    align="start",
                    padding="20px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body Form
                rx.box(
                    rx.vstack(
                        rx.cond(
                            MonitorState.form_error != "",
                            rx.hstack(
                                rx.icon(
                                    tag="circle-alert",
                                    size=16,
                                    color=Color.DANGER_FG,
                                    flex_shrink="0",
                                ),
                                rx.text(
                                    MonitorState.form_error,
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.DANGER_FG,
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                                padding="10px 14px",
                                background_color=Color.DANGER_BG,
                                border_radius=Radius.CONTROL,
                            ),
                        ),
                        # --- BAGIAN 1: DATA FISIK ASET ---
                        _section_title("1. Data Fisik Aset"),
                        rx.box(
                            rx.vstack(
                                _field_label("ID Aset (Wajib & Unik)", required=True),
                                _text_input(
                                    value=MonitorState.form_id_aset,
                                    on_change=MonitorState.set_form_id_aset,
                                    placeholder="MON-0025",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Status", required=True),
                                _status_select(),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Kepemilikan"),
                                _select_input(
                                    options_var=MonitorState.master_kepemilikan_options,
                                    value=MonitorState.form_kepemilikan,
                                    on_change=MonitorState.set_form_kepemilikan,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Lokasi"),
                                _select_input(
                                    options_var=MonitorState.master_lokasi_options,
                                    value=MonitorState.form_lokasi,
                                    on_change=MonitorState.set_form_lokasi,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Kondisi"),
                                _select_input(
                                    options_var=MonitorState.master_kondisi_options,
                                    value=MonitorState.form_kondisi,
                                    on_change=MonitorState.set_form_kondisi,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),

                        # --- BAGIAN 2: SPESIFIKASI MONITOR ---
                        _section_title("2. Spesifikasi Layar"),
                        rx.box(
                            rx.vstack(
                                _field_label("Merk", required=True),
                                _text_input(
                                    value=MonitorState.form_merk,
                                    on_change=MonitorState.set_form_merk,
                                    placeholder="LG, Dell, Samsung, AOC, HP...",
                                    list_id="monitor-merk-datalist",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Tipe / Model", required=True),
                                _text_input(
                                    value=MonitorState.form_tipe_model,
                                    on_change=MonitorState.set_form_tipe_model,
                                    placeholder="Contoh: 24MK600M / UltraSharp U2422H",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Ukuran Layar", required=True),
                                _inch_input(),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Resolusi Layar", required=True),
                                _text_input(
                                    value=MonitorState.form_resolusi_layar,
                                    on_change=MonitorState.set_form_resolusi_layar,
                                    placeholder="Contoh: 1920 x 1080",
                                    list_id="monitor-resolusi-datalist",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        rx.vstack(
                            _field_label("Konektivitas (Pilih minimal 1)", required=True),
                            rx.hstack(
                                rx.foreach(
                                    MonitorState.master_konektivitas_options,
                                    _connector_checkbox_chip,
                                ),
                                spacing="2",
                                wrap="wrap",
                                width="100%",
                            ),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        rx.vstack(
                            _field_label("Catatan (Opsional)"),
                            rx.el.textarea(
                                value=MonitorState.form_catatan,
                                on_change=MonitorState.set_form_catatan,
                                placeholder="Catatan tambahan kondisi layar atau histori unit...",
                                rows=2,
                                style=rx.Style(
                                    {
                                        "width": "100%",
                                        "padding": "10px 12px",
                                        "background_color": Color.SURFACE,
                                        "color": Color.TEXT,
                                        "border": f"1px solid {Color.INPUT_BORDER}",
                                        "border_radius": Radius.CONTROL,
                                        "font_family": FONT_FAMILY,
                                        "font_size": FontSize.SM,
                                        "outline": "none",
                                        "resize": "vertical",
                                    }
                                ),
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "20px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 148px)",
                        }
                    ),
                ),
                # Footer Modal
                rx.hstack(
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=MonitorState.close_form_modal,
                            style=rx.Style(
                                {
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 16px",
                                    "background_color": Color.SURFACE,
                                    "color": Color.TEXT,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.cond(
                            MonitorState.form_mode == "edit",
                            rx.el.button(
                                rx.hstack(
                                    rx.icon(tag="copy", size=15, color=Color.ACCENT),
                                    rx.text(
                                        "Duplikat",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.ACCENT,
                                    ),
                                    spacing="1",
                                    align="center",
                                ),
                                type="button",
                                on_click=MonitorState.duplicate_current_form,
                                style=rx.Style(
                                    {
                                        "height": Size.FILTER_CONTROL_H,
                                        "padding": "0 14px",
                                        "background_color": Color.INFO_BG,
                                        "border": "none",
                                        "border_radius": Radius.CONTROL,
                                        "font_family": FONT_FAMILY,
                                        "display": "inline-flex",
                                        "align_items": "center",
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.cond(
                            MonitorState.form_mode == "add",
                            rx.el.button(
                                "Simpan & tambah lagi",
                                type="button",
                                on_click=MonitorState.save_and_add_another,
                                style=rx.Style(
                                    {
                                        "height": Size.FILTER_CONTROL_H,
                                        "padding": "0 16px",
                                        "background_color": Color.INFO_BG,
                                        "color": Color.ACCENT,
                                        "border": "none",
                                        "border_radius": Radius.CONTROL,
                                        "font_family": FONT_FAMILY,
                                        "font_size": FontSize.SM,
                                        "font_weight": FontWeight.BOLD,
                                        "cursor": "pointer",
                                    }
                                ),
                            ),
                            rx.fragment(),
                        ),
                        rx.el.button(
                            rx.cond(
                                MonitorState.form_mode == "edit",
                                "Simpan Perubahan",
                                "Simpan Monitor",
                            ),
                            type="button",
                            on_click=MonitorState.save_monitor_form,
                            style=rx.Style(
                                {
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 20px",
                                    "background_color": Color.ACCENT,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    padding="14px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SURFACE,
                        }
                    ),
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "94%",
                        "max_width": "620px",
                        "max_height": "90vh",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "display": "flex",
                        "flex_direction": "column",
                        "overflow": "hidden",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


__all__ = ["monitor_form_modal"]
