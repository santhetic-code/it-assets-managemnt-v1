"""
Komponen Modal Form Tambah / Edit Aset ITAM Pro.
Dropdown diambil dari daftar master, mendukung validasi kondisional,
'Simpan & tambah lagi', serta 'Duplikat x N' untuk input banyak unit sejenis.
"""
from typing import Any

import reflex as rx

from itam_pro.states.asset_state import AssetState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space


def _field_label(text: str, required: bool = False) -> rx.Component:
    """Label field form dengan tanda bintang merah jika wajib."""
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
    placeholder: Any = "",
    input_type: Any = "text",
    disabled: Any = False,
) -> rx.Component:
    """Input teks/tanggal/angka standar di dalam modal form."""
    return rx.el.input(
        type=input_type,
        value=value,
        on_change=on_change,
        placeholder=placeholder,
        disabled=disabled,
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.FILTER_CONTROL_H,
                "padding": "0 12px",
                "background_color": rx.cond(disabled, Color.TABLE_HEADER_BG, Color.SURFACE),
                "color": rx.cond(disabled, Color.MUTED, Color.TEXT),
                "border": f"1px solid {Color.INPUT_BORDER}",
                "border_radius": Radius.CONTROL,
                "font_family": FONT_FAMILY,
                "font_size": FontSize.SM,
                "outline": "none",
                "cursor": rx.cond(disabled, "not-allowed", "text"),
            }
        ),
        _focus=rx.Style(
            {
                "border_color": Color.ACCENT,
                "box_shadow": Color.FOCUS_RING,
            }
        ),
    )


def _master_select(
    options_var: Any,
    value: Any,
    on_change: Any,
) -> rx.Component:
    """Dropdown select yang opsinya diambil secara dinamis dari daftar master di State."""
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


def asset_form_modal() -> rx.Component:
    """Modal Form Tambah / Edit / Duplikat Aset."""
    return rx.cond(
        AssetState.form_modal_open,
        rx.box(
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
                                f"Edit Aset · {AssetState.form_editing_id}",
                                "Tambah Aset Baru",
                            ),
                            font_size=FontSize.LOGO,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Satu baris mewakili satu unit fisik. Gunakan Duplikat x N untuk "
                            "menyimpan banyak unit sejenis sekaligus.",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        aria_label="Tutup form",
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
                    padding="20px 24px 16px 24px",
                    style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
                ),
                # Body Form
                rx.box(
                    rx.vstack(
                        rx.cond(
                            AssetState.form_error != "",
                            rx.hstack(
                                rx.icon(
                                    tag="circle-alert",
                                    size=16,
                                    color=Color.DANGER_FG,
                                    flex_shrink="0",
                                ),
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
                                background_color=Color.DANGER_BG,
                                border_radius=Radius.CONTROL,
                            ),
                        ),
                        # Baris 1: Nama Aset & Kategori
                        rx.box(
                            rx.vstack(
                                _field_label("Nama Aset", required=True),
                                _text_input(
                                    value=AssetState.form_nama_aset,
                                    on_change=AssetState.set_form_nama_aset,
                                    placeholder="Contoh: Monitor LG 24MK600 / SSD Samsung 500GB",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Kategori", required=True),
                                _master_select(
                                    options_var=AssetState.master_kategori_options,
                                    value=AssetState.form_kategori,
                                    on_change=AssetState.set_form_kategori,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1.4fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        # Baris 2: SN / PID & Kepemilikan
                        rx.box(
                            rx.vstack(
                                _field_label("SN / PID (Opsional, tidak harus unik)"),
                                _text_input(
                                    value=AssetState.form_sn_pid,
                                    on_change=AssetState.set_form_sn_pid,
                                    placeholder="Kosongkan jika tidak ada SN/PID",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Kepemilikan", required=True),
                                _master_select(
                                    options_var=AssetState.master_kepemilikan_options,
                                    value=AssetState.form_kepemilikan,
                                    on_change=AssetState.set_form_kepemilikan,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "1.4fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        # Baris 3: Tgl Masuk Gudang & Tgl Keluar Gudang
                        rx.box(
                            rx.vstack(
                                _field_label("Tgl Masuk Gudang (Opsional)"),
                                _text_input(
                                    value=AssetState.form_tgl_masuk,
                                    on_change=AssetState.set_form_tgl_masuk,
                                    input_type="date",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Tgl Keluar Gudang (Opsional)"),
                                _text_input(
                                    value=AssetState.form_tgl_keluar,
                                    on_change=AssetState.set_form_tgl_keluar,
                                    input_type="date",
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
                        # Baris 4: Lokasi & Kondisi
                        rx.box(
                            rx.vstack(
                                _field_label("Lokasi", required=True),
                                _master_select(
                                    options_var=AssetState.master_lokasi_options,
                                    value=AssetState.form_lokasi,
                                    on_change=AssetState.set_form_lokasi,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Kondisi", required=True),
                                _master_select(
                                    options_var=AssetState.master_kondisi_options,
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
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": Space.S4,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        # Baris 5: Status & Digunakan Oleh
                        rx.box(
                            rx.vstack(
                                _field_label("Status", required=True),
                                _master_select(
                                    options_var=AssetState.master_status_options,
                                    value=AssetState.form_status,
                                    on_change=AssetState.set_form_status,
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        "Digunakan Oleh",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.SEMIBOLD,
                                        color=Color.TEXT,
                                    ),
                                    rx.cond(
                                        AssetState.is_digunakan_oleh_required,
                                        rx.text(
                                            "* (Wajib saat Digunakan)",
                                            font_size=FontSize.XS,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.DANGER_FG,
                                        ),
                                        rx.text(
                                            "(Nonaktif saat Tidak Digunakan)",
                                            font_size=FontSize.XS,
                                            color=Color.MUTED,
                                        ),
                                    ),
                                    spacing="1",
                                    align="center",
                                ),
                                _text_input(
                                    value=AssetState.form_digunakan_oleh,
                                    on_change=AssetState.set_form_digunakan_oleh,
                                    placeholder=rx.cond(
                                        AssetState.is_digunakan_oleh_required,
                                        "Nama pengguna / divisi...",
                                        "—",
                                    ),
                                    disabled=~AssetState.is_digunakan_oleh_required,
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
                        # Baris 6: Catatan
                        rx.vstack(
                            _field_label("Catatan (Opsional, tampil di drawer)"),
                            rx.el.textarea(
                                value=AssetState.form_catatan,
                                on_change=AssetState.set_form_catatan,
                                placeholder="Catatan tambahan kondisi unit atau histori pemakaian",
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
                        # Spesifikasi Dinamis: Kategori Monitor
                        rx.cond(
                            AssetState.form_kategori == "Monitor",
                            rx.vstack(
                                _section_title("Spesifikasi Monitor"),
                                rx.box(
                                    rx.vstack(
                                        _field_label("Merk", required=True),
                                        _text_input(
                                            value=AssetState.form_merk,
                                            on_change=AssetState.set_form_merk,
                                            placeholder="LG, Dell, Samsung, AOC, HP...",
                                        ),
                                        spacing="1",
                                        align="start",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        _field_label("Tipe / Model", required=True),
                                        _text_input(
                                            value=AssetState.form_tipe_model,
                                            on_change=AssetState.set_form_tipe_model,
                                            placeholder="Contoh: 24MK600M",
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
                                            "@media (max-width: 639px)": {
                                                "grid_template_columns": "1fr"
                                            },
                                        }
                                    ),
                                ),
                                rx.box(
                                    rx.vstack(
                                        _field_label("Ukuran Layar (inci)", required=True),
                                        _text_input(
                                            value=AssetState.form_ukuran_layar,
                                            on_change=AssetState.set_form_ukuran_layar,
                                            placeholder="24 / 21,5 / 27",
                                        ),
                                        spacing="1",
                                        align="start",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        _field_label("Resolusi Layar", required=True),
                                        _text_input(
                                            value=AssetState.form_resolusi_layar,
                                            on_change=AssetState.set_form_resolusi_layar,
                                            placeholder="Contoh: 1920 x 1080",
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
                                            "@media (max-width: 639px)": {
                                                "grid_template_columns": "1fr"
                                            },
                                        }
                                    ),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        # Spesifikasi Dinamis: Kategori PC atau Server
                        rx.cond(
                            (AssetState.form_kategori == "PC")
                            | (AssetState.form_kategori == "Server"),
                            rx.vstack(
                                _section_title("Spesifikasi PC / Server"),
                                rx.box(
                                    rx.vstack(
                                        _field_label("Jenis"),
                                        _master_select(
                                            options_var=AssetState.master_jenis_pc_options,
                                            value=AssetState.form_jenis_pc,
                                            on_change=AssetState.set_form_jenis_pc,
                                        ),
                                        spacing="1",
                                        align="start",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        _field_label("Operasi System"),
                                        _text_input(
                                            value=AssetState.form_os,
                                            on_change=AssetState.set_form_os,
                                            placeholder="Windows 11 Pro / Ubuntu 22.04",
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
                                            "@media (max-width: 639px)": {
                                                "grid_template_columns": "1fr"
                                            },
                                        }
                                    ),
                                ),
                                rx.box(
                                    rx.vstack(
                                        _field_label("CPU / Prosesor"),
                                        _text_input(
                                            value=AssetState.form_cpu,
                                            on_change=AssetState.set_form_cpu,
                                            placeholder="Intel i5-12400 / AMD Ryzen 5",
                                        ),
                                        spacing="1",
                                        align="start",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        _field_label("RAM"),
                                        _text_input(
                                            value=AssetState.form_ram,
                                            on_change=AssetState.set_form_ram,
                                            placeholder="16 GB DDR4",
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
                                            "@media (max-width: 639px)": {
                                                "grid_template_columns": "1fr"
                                            },
                                        }
                                    ),
                                ),
                                rx.box(
                                    rx.vstack(
                                        _field_label("VGA / Grafis"),
                                        _text_input(
                                            value=AssetState.form_vga,
                                            on_change=AssetState.set_form_vga,
                                            placeholder="NVIDIA GTX 1650 / Integrated",
                                        ),
                                        spacing="1",
                                        align="start",
                                        width="100%",
                                    ),
                                    rx.vstack(
                                        _field_label("Mainboard"),
                                        _text_input(
                                            value=AssetState.form_mainboard,
                                            on_change=AssetState.set_form_mainboard,
                                            placeholder="ASUS PRIME B660M",
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
                                            "@media (max-width: 639px)": {
                                                "grid_template_columns": "1fr"
                                            },
                                        }
                                    ),
                                ),
                                rx.vstack(
                                    _field_label("HDD / SSD"),
                                    _text_input(
                                        value=AssetState.form_hdd_ssd,
                                        on_change=AssetState.set_form_hdd_ssd,
                                        placeholder="SSD NVMe 512GB + HDD 1TB",
                                    ),
                                    spacing="1",
                                    align="start",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        # Baris 7: Duplikat x N (khusus mode tambah)
                        rx.cond(
                            AssetState.form_mode == "add",
                            rx.hstack(
                                rx.vstack(
                                    rx.text(
                                        "Duplikat x N (Input Banyak Unit Sejenis)",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                        color=Color.TEXT,
                                    ),
                                    rx.text(
                                        "Setiap unit dibuat sebagai baris terpisah dengan ID "
                                        "AST-XXXX otomatis.",
                                        font_size=FontSize.XS,
                                        color=Color.MUTED,
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                rx.hstack(
                                    rx.text(
                                        "x",
                                        font_size=FontSize.BASE,
                                        font_weight=FontWeight.EXTRABOLD,
                                        color=Color.ACCENT,
                                    ),
                                    rx.el.input(
                                        type="number",
                                        min="1",
                                        max="50",
                                        value=AssetState.form_duplicate_count,
                                        on_change=AssetState.set_form_duplicate_count,
                                        style=rx.Style(
                                            {
                                                "width": "76px",
                                                "height": "38px",
                                                "padding": "0 10px",
                                                "text_align": "center",
                                                "background_color": Color.SURFACE,
                                                "color": Color.TEXT,
                                                "border": f"1px solid {Color.INPUT_BORDER}",
                                                "border_radius": Radius.CONTROL,
                                                "font_family": FONT_FAMILY,
                                                "font_size": FontSize.SM,
                                                "font_weight": FontWeight.BOLD,
                                            }
                                        ),
                                    ),
                                    rx.text(
                                        "unit",
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.MEDIUM,
                                        color=Color.MUTED,
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                width="100%",
                                justify="between",
                                align="center",
                                padding="12px 16px",
                                style=rx.Style(
                                    {
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border": f"1px solid {Color.BORDER}",
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                            rx.fragment(),
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
                        "width": "94%",
                        "max_width": "640px",
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
