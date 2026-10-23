"""
Komponen Modal Form Tambah / Edit IP & Server (VM) (660px).
Menyembunyikan field Host untuk jenis Fisik, dan menyembunyikan Aset Fisik untuk jenis VM.
"""
from typing import Any

import reflex as rx

from itam_pro.states.ip_state import IPState
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
                "height": Size.FILTER_CONTROL_H,
                "padding": "0 12px",
                "background_color": Color.SURFACE,
                "color": Color.TEXT,
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "font_family": font_fam,
                "font_size": FontSize.SM,
                "outline": "none",
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


def ip_form_modal() -> rx.Component:
    """Modal 660px untuk Tambah / Edit entri IP & Server (VM)."""
    return rx.cond(
        IPState.form_modal_open,
        rx.box(
            rx.el.datalist(
                rx.foreach(
                    IPState.os_suggestions,
                    lambda o: rx.el.option(value=o),
                ),
                id="ip-os-suggestions-datalist",
            ),
            # Scrim
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
            # Kartu Modal 660px
            rx.box(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            rx.cond(
                                IPState.form_mode == "edit",
                                f"Edit Entri IP · {IPState.form_ip_address}",
                                "Tambah IP & Server (VM)",
                            ),
                            font_size=FontSize.LOGO,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Subnet /24 diturunkan otomatis dari IPv4. Kredensial login "
                            "dikelola terpisah di Credential Manager.",
                            font_size=FontSize.XS,
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
                    padding="20px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body
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
                        # Baris 1: IP Address & Nama Server/VM
                        rx.box(
                            rx.vstack(
                                _field_label("IP Address (IPv4)", required=True),
                                _text_input(
                                    value=IPState.form_ip_address,
                                    on_change=IPState.set_form_ip_address,
                                    placeholder="Contoh: 192.168.10.30",
                                    monospace=True,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Nama Server / VM", required=True),
                                _text_input(
                                    value=IPState.form_nama,
                                    on_change=IPState.set_form_nama,
                                    placeholder="Contoh: VM-TRX-ENGINE-03",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1.3fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        # Baris 2: Jenis (Fisik/VM), Aset/Host kondisional, & Grup
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
                            rx.cond(
                                IPState.form_jenis == "Fisik",
                                rx.vstack(
                                    _field_label("Unit Aset Server (Opsional)"),
                                    _select_input(
                                        options=IPState.server_asset_ids,
                                        value=IPState.form_asset_id,
                                        on_change=IPState.set_form_asset_id,
                                        empty_label="— Belum ditautkan —",
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
                                        empty_label="— Pilih Host Server —",
                                    ),
                                    spacing="1",
                                    align="start",
                                    width="100%",
                                ),
                            ),
                            rx.vstack(
                                _field_label("Grup", required=True),
                                _select_input(
                                    options=IPState.grup_options,
                                    value=IPState.form_grup,
                                    on_change=IPState.set_form_grup,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "0.8fr 1.2fr 1fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        # Baris 3: Fungsi, OS (Combobox), & Status
                        rx.box(
                            rx.vstack(
                                _field_label("Fungsi"),
                                _text_input(
                                    value=IPState.form_fungsi,
                                    on_change=IPState.set_form_fungsi,
                                    placeholder="Contoh: Worker Transaksi / Database",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Operasi System (Saran / Ketik)"),
                                _text_input(
                                    value=IPState.form_os,
                                    on_change=IPState.set_form_os,
                                    placeholder="Ubuntu Server 24.04 LTS...",
                                    list_id="ip-os-suggestions-datalist",
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
                                    "grid_template_columns": "1.2fr 1.1fr 0.8fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        # Baris 4: Keterangan
                        rx.vstack(
                            _field_label("Keterangan (Opsional)"),
                            _text_input(
                                value=IPState.form_keterangan,
                                on_change=IPState.set_form_keterangan,
                                placeholder="Catatan port internal, cluster, atau fungsi...",
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
                # Footer (Batal / Simpan & tambah lagi / Simpan)
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=IPState.close_form_modal,
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
                    rx.hstack(
                        rx.cond(
                            IPState.form_mode == "add",
                            rx.el.button(
                                "Simpan & tambah lagi",
                                type="button",
                                on_click=IPState.save_and_add_another,
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
                            "Simpan",
                            type="button",
                            on_click=IPState.save_ip_form,
                            style=rx.Style(
                                {
                                    "height": Size.FILTER_CONTROL_H,
                                    "padding": "0 22px",
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
                        "max_width": "660px",
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


__all__ = ["ip_form_modal"]
