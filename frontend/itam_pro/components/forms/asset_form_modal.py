"""
Komponen DynamicForm Modal Tambah / Edit Aset ITAM Pro (Tahap 6c-1).
Menyesuaikan seksi Spesifikasi secara otomatis berdasarkan kategori yang dipilih,
mengunci kategori saat dibuka dari `/assets/c/[slug]`, dan menampilkan peringatan
non-blocking bila SN/PID sudah digunakan oleh aset lain.
"""
from typing import Any

import reflex as rx

from itam_pro.states.asset_state import AssetState
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


def _field_label(text: str, required: Any = False) -> rx.Component:
    asterisk = rx.text(
        "*",
        font_size=FontSize.SM,
        font_weight=FontWeight.BOLD,
        color=Color.DANGER_FG,
    )
    if isinstance(required, rx.Var):
        req_indicator = rx.cond(required, asterisk, rx.fragment())
    elif required:
        req_indicator = asterisk
    else:
        req_indicator = rx.fragment()

    return rx.hstack(
        rx.text(
            text,
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
        ),
        req_indicator,
        spacing="1",
        align="center",
    )


def _section_divider(title: str) -> rx.Component:
    return rx.vstack(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.ACCENT,
            letter_spacing="0.06em",
        ),
        rx.box(
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "1px",
                    "background_color": Color.BORDER,
                }
            )
        ),
        spacing="1",
        align="start",
        width="100%",
        padding_top="4px",
    )


def _text_input(
    value: Any,
    on_change: Any,
    placeholder: str = "",
    disabled: Any = False,
    input_type: Any = "text",
    list_id: str | None = None,
) -> rx.Component:
    return rx.el.input(
        type=input_type,
        value=value,
        on_change=on_change,
        placeholder=placeholder,
        disabled=disabled,
        list=list_id,
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.FILTER_CONTROL_H,
                "padding": "0 12px",
                "background_color": rx.cond(
                    disabled, Color.TABLE_HEADER_BG, Color.SURFACE
                ),
                "color": rx.cond(disabled, Color.MUTED, Color.TEXT),
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "outline": "none",
            }
        ),
    )


def _select_input(
    options: Any,
    value: Any,
    on_change: Any,
    disabled: Any = False,
) -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.foreach(options, lambda opt: rx.el.option(opt, value=opt)),
            value=value,
            on_change=on_change,
            disabled=disabled,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 32px 0 12px",
                    "background_color": rx.cond(
                        disabled, Color.TABLE_HEADER_BG, Color.SURFACE
                    ),
                    "color": rx.cond(disabled, Color.MUTED, Color.TEXT),
                    "border": f"1px solid {Color.INPUT_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.MEDIUM,
                    "outline": "none",
                    "cursor": rx.cond(disabled, "not-allowed", "pointer"),
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


def _connector_checkbox_chip(port: Any) -> rx.Component:
    form_konektivitas: Any = AssetState.form_konektivitas
    is_checked = form_konektivitas.contains(port)
    return rx.el.label(
        rx.hstack(
            rx.el.input(
                type="checkbox",
                checked=is_checked,
                on_change=AssetState.toggle_form_konektivitas(port),
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
            ),
            spacing="2",
            align="center",
        ),
        style=rx.Style(
            {
                "padding": "8px 14px",
                "background_color": rx.cond(
                    is_checked, Color.INFO_BG, Color.TABLE_HEADER_BG
                ),
                "border": rx.cond(
                    is_checked,
                    f"1px solid {Color.ACCENT}",
                    f"1px solid {Color.INPUT_BORDER}",
                ),
                "border_radius": Radius.CONTROL,
                "cursor": "pointer",
                "display": "inline-flex",
                "align_items": "center",
            }
        ),
    )


def _pc_spec_fields_section() -> rx.Component:
    """Bagian spesifikasi dinamis untuk kategori PC dan Server."""
    attrs: Any = AssetState.form_attributes
    return rx.vstack(
        _section_divider("2. Spesifikasi Perangkat (PC / Server)"),
        rx.box(
            rx.vstack(
                _field_label("Jenis PC", required=True),
                _select_input(
                    options=AssetState.master_jenis_pc_options,
                    value=attrs["jenis"],
                    on_change=lambda v: AssetState.set_form_attr("jenis", v),
                    disabled=AssetState.form_kategori == "Server",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Operasi System", required=True),
                _text_input(
                    value=attrs["os"],
                    on_change=lambda v: AssetState.set_form_attr("os", v),
                    placeholder="Windows 11 Pro / Ubuntu 24.04",
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
        rx.box(
            rx.vstack(
                _field_label("CPU", required=True),
                _text_input(
                    value=attrs["cpu"],
                    on_change=lambda v: AssetState.set_form_attr("cpu", v),
                    placeholder="Contoh: Intel Core i5-12400",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("RAM", required=True),
                _text_input(
                    value=attrs["ram"],
                    on_change=lambda v: AssetState.set_form_attr("ram", v),
                    placeholder="Contoh: 16 GB DDR4",
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
        rx.box(
            rx.vstack(
                _field_label("HDD / SSD", required=True),
                _text_input(
                    value=attrs["hdd_ssd"],
                    on_change=lambda v: AssetState.set_form_attr("hdd_ssd", v),
                    placeholder="Contoh: SSD NVMe 512 GB",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Mainboard"),
                _text_input(
                    value=attrs["mainboard"],
                    on_change=lambda v: AssetState.set_form_attr("mainboard", v),
                    placeholder="Contoh: MSI PRO H610M-E",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("VGA"),
                _text_input(
                    value=attrs["vga"],
                    on_change=lambda v: AssetState.set_form_attr("vga", v),
                    placeholder="Contoh: Intel UHD / GTX 1650",
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
                }
            ),
        ),
        rx.box(
            rx.vstack(
                _field_label("Monitor Terpasang"),
                _text_input(
                    value=attrs["monitor"],
                    on_change=lambda v: AssetState.set_form_attr("monitor", v),
                    placeholder='Contoh: LG 24" (MON-0001)',
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Keyboard"),
                _text_input(
                    value=attrs["keyboard"],
                    on_change=lambda v: AssetState.set_form_attr("keyboard", v),
                    placeholder="Contoh: Logitech K120",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Mouse"),
                _text_input(
                    value=attrs["mouse"],
                    on_change=lambda v: AssetState.set_form_attr("mouse", v),
                    placeholder="Contoh: Logitech B100",
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
                }
            ),
        ),
        spacing="3",
        width="100%",
    )


def _monitor_spec_fields_section() -> rx.Component:
    """Bagian spesifikasi dinamis untuk kategori Monitor."""
    attrs: Any = AssetState.form_attributes
    return rx.vstack(
        _section_divider("2. Spesifikasi Layar Monitor"),
        rx.box(
            rx.vstack(
                _field_label("Merk (Pilih / Ketik Baru)", required=True),
                _text_input(
                    value=attrs["merk"],
                    on_change=lambda v: AssetState.set_form_attr("merk", v),
                    placeholder="LG, Dell, Samsung, AOC, HP...",
                    list_id="dynamic-merk-datalist",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Tipe / Model", required=True),
                _text_input(
                    value=attrs["tipe_model"],
                    on_change=lambda v: AssetState.set_form_attr("tipe_model", v),
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
                }
            ),
        ),
        rx.box(
            rx.vstack(
                _field_label('Ukuran Layar (inci ")', required=True),
                _text_input(
                    value=attrs["ukuran_layar"],
                    on_change=lambda v: AssetState.set_form_attr("ukuran_layar", v),
                    placeholder="24 / 21,5 / 23,8",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.vstack(
                _field_label("Resolusi Layar", required=True),
                _text_input(
                    value=attrs["resolusi_layar"],
                    on_change=lambda v: AssetState.set_form_attr("resolusi_layar", v),
                    placeholder="Contoh: 1920 × 1080",
                    list_id="dynamic-resolusi-datalist",
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
            _field_label("Konektivitas (Pilih minimal 1)", required=True),
            rx.hstack(
                rx.foreach(
                    AssetState.master_konektivitas_options,
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
        spacing="3",
        width="100%",
    )


def asset_form_modal() -> rx.Component:
    """Modal DynamicForm terpadu untuk seluruh kategori aset."""
    return rx.cond(
        AssetState.form_modal_open,
        rx.box(
            rx.el.datalist(
                rx.foreach(
                    AssetState.master_merk_options,
                    lambda m: rx.el.option(value=m),
                ),
                id="dynamic-merk-datalist",
            ),
            rx.el.datalist(
                rx.foreach(
                    AssetState.master_resolusi_options,
                    lambda r: rx.el.option(value=r),
                ),
                id="dynamic-resolusi-datalist",
            ),
            rx.box(
                on_click=AssetState.close_form_modal,
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
                # Header Modal
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            rx.cond(
                                AssetState.form_mode == "edit",
                                f"Edit Aset · {AssetState.form_id_aset}",
                                f"Tambah Aset Baru · {AssetState.form_id_aset}",
                            ),
                            font_size=FontSize.LOGO,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Satu formulir terpadu untuk data fisik aset dan atribut kategori.",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        on_click=AssetState.close_form_modal,
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
                    padding="18px 24px 14px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body Modal
                rx.box(
                    rx.vstack(
                        rx.cond(
                            AssetState.form_error != "",
                            rx.hstack(
                                rx.icon(tag="circle-alert", size=16, color=Color.DANGER_FG),
                                rx.text(
                                    AssetState.form_error,
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
                        rx.cond(
                            AssetState.form_sn_warning != "",
                            rx.hstack(
                                rx.icon(tag="triangle-alert", size=16, color=Color.WARNING_FG),
                                rx.text(
                                    f"{AssetState.form_sn_warning} (tetap dapat disimpan).",
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.SEMIBOLD,
                                    color=Color.WARNING_FG,
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                                padding="10px 14px",
                                style=rx.Style(
                                    {
                                        "background_color": Color.WARNING_BG,
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                        ),
                        _section_divider("1. Data Aset (Inti)"),
                        rx.box(
                            rx.vstack(
                                _field_label("Kategori", required=True),
                                _select_input(
                                    options=AssetState.master_kategori_options,
                                    value=AssetState.form_kategori,
                                    on_change=AssetState.set_form_kategori,
                                    disabled=AssetState.form_category_locked
                                    & (AssetState.current_slug != "pc"),
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("ID Aset (Otomatis)"),
                                _text_input(
                                    value=AssetState.form_id_aset,
                                    on_change=lambda _: None,
                                    disabled=True,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label(
                                    "Nama Aset / Hostname",
                                    required=AssetState.form_kategori != "Monitor",
                                ),
                                _text_input(
                                    value=AssetState.form_nama_aset,
                                    on_change=AssetState.set_form_nama_aset,
                                    placeholder="Otomatis untuk Monitor bila dikosongkan",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 0.9fr 1.4fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("SN / PID (Opsional)"),
                                _text_input(
                                    value=AssetState.form_sn_pid,
                                    on_change=AssetState.set_form_sn_pid,
                                    placeholder="Nomor seri perangkat",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Status", required=True),
                                _select_input(
                                    options=AssetState.master_status_options,
                                    value=AssetState.form_status,
                                    on_change=AssetState.set_form_status,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label(
                                    "Digunakan Oleh / Fungsi",
                                    required=AssetState.form_is_digunakan
                                    & (AssetState.form_kategori != "Monitor"),
                                ),
                                _text_input(
                                    value=AssetState.form_digunakan_oleh,
                                    on_change=AssetState.set_form_digunakan_oleh,
                                    placeholder="Nama pemakai / fungsi unit",
                                    disabled=AssetState.form_status == "Tidak Digunakan",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr 1.3fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Kepemilikan", required=True),
                                _select_input(
                                    options=AssetState.master_kepemilikan_options,
                                    value=AssetState.form_kepemilikan,
                                    on_change=AssetState.set_form_kepemilikan,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Lokasi", required=True),
                                _select_input(
                                    options=AssetState.master_lokasi_options,
                                    value=AssetState.form_lokasi,
                                    on_change=AssetState.set_form_lokasi,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Kondisi", required=True),
                                _select_input(
                                    options=AssetState.master_kondisi_options,
                                    value=AssetState.form_kondisi,
                                    on_change=AssetState.set_form_kondisi,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "0.8fr 1.2fr 1.2fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        rx.box(
                            rx.vstack(
                                _field_label("Tgl Masuk Gudang"),
                                _text_input(
                                    value=AssetState.form_tanggal_masuk,
                                    on_change=AssetState.set_form_tanggal_masuk,
                                    input_type="date",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Tgl Keluar Gudang"),
                                _text_input(
                                    value=AssetState.form_tanggal_keluar,
                                    on_change=AssetState.set_form_tanggal_keluar,
                                    input_type="date",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.cond(
                                AssetState.form_mode == "add",
                                rx.vstack(
                                    _field_label("Duplikat × N Unit"),
                                    _text_input(
                                        value=AssetState.form_duplicate_count,
                                        on_change=AssetState.set_form_duplicate_count,
                                        input_type="number",
                                    ),
                                    spacing="1",
                                    align="start",
                                    width="100%",
                                ),
                                rx.box(),
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr 0.8fr",
                                    "gap": Space.S4,
                                }
                            ),
                        ),
                        # Seksi 2: Spesifikasi Kategori Dinamis
                        rx.match(
                            AssetState.form_active_category_slug,
                            ("pc", _pc_spec_fields_section()),
                            ("monitor", _monitor_spec_fields_section()),
                            rx.fragment(),
                        ),
                        rx.vstack(
                            _field_label("Catatan (Opsional)"),
                            _text_input(
                                value=AssetState.form_catatan,
                                on_change=AssetState.set_form_catatan,
                                placeholder="Catatan penempatan atau keterangan tambahan...",
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    style=rx.Style(
                        {
                            "padding": "18px 24px",
                            "overflow_y": "auto",
                            "max_height": "calc(90vh - 140px)",
                        }
                    ),
                ),
                # Footer Modal
                rx.hstack(
                    rx.el.button(
                        "Batal",
                        type="button",
                        on_click=AssetState.close_form_modal,
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
                            AssetState.form_mode == "add",
                            rx.el.button(
                                "Simpan & tambah lagi",
                                type="button",
                                on_click=AssetState.save_and_add_another,
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
                                AssetState.form_mode == "edit",
                                "Simpan Perubahan",
                                "Simpan Aset",
                            ),
                            type="button",
                            on_click=AssetState.save_asset_form,
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
                        "width": "95%",
                        "max_width": "760px",
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


__all__ = ["asset_form_modal"]
