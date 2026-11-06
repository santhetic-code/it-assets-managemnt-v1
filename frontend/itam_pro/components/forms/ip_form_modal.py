"""Komponen Form Modal Tambah / Edit IP & Server (VM)."""

from typing import Any

import reflex as rx

from itam_pro.states.ip_state import IPState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space


def _field_label(text: str, required: bool = False, optional: bool = False) -> rx.Component:
    return rx.hstack(
        rx.text(text, font_size=FontSize.SM, font_weight=FontWeight.BOLD, color=Color.TEXT),
        rx.text("*", font_size=FontSize.SM, font_weight=FontWeight.BOLD, color=Color.DANGER_FG)
        if required
        else rx.fragment(),
        rx.text(
            "(opsional)", font_size=FontSize.SM, font_weight=FontWeight.REGULAR, color=Color.MUTED
        )
        if optional
        else rx.fragment(),
        spacing="1",
        align="center",
    )


def _text_input(
    value: Any,
    on_change: Any,
    placeholder: str = "",
    list_id: str | None = None,
    monospace: bool = False,
) -> rx.Component:
    font_fam = (
        "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
        if monospace
        else FONT_FAMILY
    )
    return rx.el.input(
        type="text",
        value=value,
        on_change=on_change,
        placeholder=placeholder,
        list=list_id,
        style=rx.Style(
            {
                "width": "100%",
                "height": "42px",
                "padding": "0 14px",
                "background_color": Color.SURFACE,
                "color": Color.TEXT,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": "10px",
                "font_family": font_fam,
                "font_size": FontSize.SM,
                "outline": "none",
                "&:focus": {"border_color": Color.ACCENT, "box_shadow": Color.FOCUS_RING},
            }
        ),
    )


def _textarea_input(value: Any, on_change: Any, placeholder: str = "") -> rx.Component:
    return rx.el.textarea(
        value=value,
        on_change=on_change,
        placeholder=placeholder,
        rows=3,
        style=rx.Style(
            {
                "width": "100%",
                "min_height": "78px",
                "padding": "10px 14px",
                "background_color": Color.SURFACE,
                "color": Color.TEXT,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": "10px",
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "outline": "none",
                "resize": "vertical",
                "&:focus": {"border_color": Color.ACCENT, "box_shadow": Color.FOCUS_RING},
            }
        ),
    )


def _select_input(
    options: Any,
    value: Any,
    on_change: Any,
    empty_label: str | None = None,
) -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.el.option(empty_label, value="") if empty_label else rx.fragment(),
            rx.foreach(options, lambda opt: rx.el.option(opt, value=opt)),
            value=value,
            on_change=on_change,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "42px",
                    "padding": "0 34px 0 14px",
                    "background_color": Color.SURFACE,
                    "color": Color.TEXT,
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": "10px",
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "outline": "none",
                    "cursor": "pointer",
                    "appearance": "none",
                    "-webkit-appearance": "none",
                    "&:focus": {"border_color": Color.ACCENT, "box_shadow": Color.FOCUS_RING},
                }
            ),
        ),
        rx.icon(
            tag="chevron-down",
            size=16,
            color=Color.MUTED,
            style=rx.Style(
                {
                    "position": "absolute",
                    "right": "12px",
                    "top": "50%",
                    "transform": "translateY(-50%)",
                    "pointer_events": "none",
                }
            ),
        ),
        style=rx.Style({"position": "relative", "width": "100%"}),
    )


def ip_form_modal() -> rx.Component:
    return rx.cond(
        IPState.form_modal_open,
        rx.box(
            rx.el.datalist(
                rx.foreach(IPState.os_suggestions, lambda o: rx.el.option(value=o)),
                id="ip-os-suggestions-datalist",
            ),
            rx.box(
                on_click=IPState.close_form_modal,
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
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            rx.cond(
                                IPState.form_mode == "edit",
                                f"Edit IP · {IPState.form_ip_address}",
                                "Tambah IP & Server (VM)",
                            ),
                            font_size="20px",
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Subnet /24 otomatis. Kredensial dikelola di Credential Manager.",
                            font_size=FontSize.SM,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        on_click=IPState.close_form_modal,
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
                    padding="22px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                rx.box(
                    rx.vstack(
                        rx.cond(
                            IPState.form_error != "",
                            rx.hstack(
                                rx.icon(tag="circle-alert", size=16, color=Color.DANGER_FG),
                                rx.text(
                                    IPState.form_error,
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.DANGER_FG,
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                                padding="10px 14px",
                                style=rx.Style(
                                    {
                                        "background_color": Color.DANGER_BG,
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("IP Address (IPv4)", required=True),
                                _text_input(
                                    value=IPState.form_ip_address,
                                    on_change=IPState.set_form_ip_address,
                                    placeholder="192.168.1.30",
                                    monospace=True,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Pengguna", required=True),
                                _text_input(
                                    value=IPState.form_pengguna,
                                    on_change=IPState.set_form_pengguna,
                                    placeholder="Nama pengguna/sistem...",
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
                                }
                            ),
                        ),
                        rx.cond(
                            IPState.is_form_vm,
                            rx.box(
                                rx.vstack(
                                    _field_label("Jenis", required=True),
                                    _select_input(
                                        options=IPState.jenis_options,
                                        value=IPState.form_jenis,
                                        on_change=IPState.set_form_jenis,
                                    ),
                                    spacing="1",
                                    align="start",
                                    width="100%",
                                ),
                                rx.vstack(
                                    _field_label("Host Server Fisik", required=True),
                                    _select_input(
                                        options=IPState.server_asset_ids,
                                        value=IPState.form_host_asset_id,
                                        on_change=IPState.set_form_host_asset_id,
                                        empty_label="Pilih server fisik...",
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
                                    }
                                ),
                            ),
                            rx.vstack(
                                _field_label("Jenis", required=True),
                                _select_input(
                                    options=IPState.jenis_options,
                                    value=IPState.form_jenis,
                                    on_change=IPState.set_form_jenis,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Kategori", required=True),
                                _select_input(
                                    options=IPState.kategori_options,
                                    value=IPState.form_kategori,
                                    on_change=IPState.set_form_kategori,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Status", required=True),
                                _select_input(
                                    options=IPState.status_options,
                                    value=IPState.form_status,
                                    on_change=IPState.set_form_status,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1.2fr 0.8fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Fungsi", optional=True),
                                _text_input(
                                    value=IPState.form_fungsi,
                                    on_change=IPState.set_form_fungsi,
                                    placeholder="Fungsi sistem...",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Operating System", optional=True),
                                _text_input(
                                    value=IPState.form_os,
                                    on_change=IPState.set_form_os,
                                    placeholder="Windows 11...",
                                    list_id="ip-os-suggestions-datalist",
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
                                }
                            ),
                        ),
                        rx.vstack(
                            _field_label("Keterangan", optional=True),
                            _textarea_input(
                                value=IPState.form_keterangan,
                                on_change=IPState.set_form_keterangan,
                                placeholder="Catat kendala...",
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
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=IPState.close_form_modal,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 18px",
                                "background_color": Color.SURFACE,
                                "color": Color.TEXT,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": "10px",
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.cond(
                        IPState.form_mode == "add",
                        rx.el.button(
                            "Simpan & tambah lagi",
                            type="button",
                            on_click=IPState.save_and_add_another,
                            style=rx.Style(
                                {
                                    "height": "40px",
                                    "padding": "0 18px",
                                    "background_color": Color.BLUE_100,
                                    "color": Color.BLUE_700,
                                    "border": "none",
                                    "border_radius": "10px",
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
                        "Simpan",
                        type="button",
                        on_click=IPState.save_ip_form,
                        style=rx.Style(
                            {
                                "height": "40px",
                                "padding": "0 22px",
                                "background_color": Color.ACCENT,
                                "color": Color.WHITE,
                                "border": "none",
                                "border_radius": "10px",
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                                "box_shadow": "0 4px 12px rgba(29, 78, 216, 0.25)",
                            }
                        ),
                    ),
                    spacing="3",
                    justify="end",
                    align="center",
                    width="100%",
                    padding="16px 24px",
                    style=rx.Style(
                        {
                            "border_top": f"1px solid {Color.BORDER}",
                            "background_color": Color.SLATE_50,
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
                        "border_radius": "16px",
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


__all__ = ["ip_form_modal"]
