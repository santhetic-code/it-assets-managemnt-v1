"""
Komponen Modal Form Tambah / Edit PC ITAM Pro.
Jenis PC diisi otomatis dari tab aktif; mendukung 'Simpan & tambah lagi' dan 'Duplikat'.
"""
from typing import Any

import reflex as rx

from itam_pro.states.pc_state import PCState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Shadow, Size, Space


def _field_label(text: Any, required: bool = False) -> rx.Component:
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
) -> rx.Component:
    return rx.el.input(
        type="text",
        value=value,
        on_change=on_change,
        placeholder=placeholder,
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


def _jenis_select() -> rx.Component:
    return rx.box(
        rx.el.select(
            rx.foreach(
                PCState.master_jenis_options,
                lambda opt: rx.el.option(opt, value=opt),
            ),
            value=PCState.form_jenis,
            on_change=PCState.set_form_jenis,
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


def pc_form_modal() -> rx.Component:
    """Modal Form Tambah / Edit Spesifikasi PC."""
    return rx.cond(
        PCState.form_modal_open,
        rx.box(
            rx.box(
                on_click=PCState.close_form_modal,
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
                                PCState.form_mode == "edit",
                                f"Edit PC · {PCState.form_editing_id}",
                                f"Tambah PC {PCState.form_jenis}",
                            ),
                            font_size=FontSize.LOGO,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.TEXT,
                        ),
                        rx.text(
                            "Jenis PC terisi otomatis sesuai tab aktif. Kosongkan field perangkat "
                            "jika tidak terpasang (tampil '—').",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.el.button(
                        rx.icon(tag="x", size=Size.ICON_SM, color=Color.MUTED),
                        type="button",
                        aria_label="Tutup form PC",
                        on_click=PCState.close_form_modal,
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
                            PCState.form_error != "",
                            rx.hstack(
                                rx.icon(
                                    tag="circle-alert",
                                    size=16,
                                    color=Color.DANGER_FG,
                                    flex_shrink="0",
                                ),
                                rx.text(
                                    PCState.form_error,
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
                        # Grup 1: Identitas (Nama PC, Jenis, User/Fungsi)
                        rx.box(
                            rx.vstack(
                                _field_label("Nama PC / Hostname", required=True),
                                _text_input(
                                    value=PCState.form_nama_pc,
                                    on_change=PCState.set_form_nama_pc,
                                    placeholder="Contoh: PC-OPS-B14-01 / SRV-DB-MAIN-01",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Jenis PC", required=True),
                                _jenis_select(),
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
                        rx.box(
                            rx.vstack(
                                _field_label(PCState.form_user_label),
                                _text_input(
                                    value=PCState.form_user,
                                    on_change=PCState.set_form_user,
                                    placeholder="Nama pengguna atau fungsi server/backup...",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Operasi System"),
                                _text_input(
                                    value=PCState.form_operasi_system,
                                    on_change=PCState.set_form_operasi_system,
                                    placeholder="Contoh: Windows 11 Pro 64-bit / Ubuntu 24.04",
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
                        # Grup 2: Perangkat Keras (CPU, Mainboard, RAM, VGA, HDD/SSD)
                        rx.box(
                            rx.vstack(
                                _field_label("CPU / Prosesor"),
                                _text_input(
                                    value=PCState.form_cpu,
                                    on_change=PCState.set_form_cpu,
                                    placeholder="Contoh: Intel Core i5-12400",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Mainboard"),
                                _text_input(
                                    value=PCState.form_mainboard,
                                    on_change=PCState.set_form_mainboard,
                                    placeholder="Contoh: ASRock B660M Pro RS",
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
                                _field_label("RAM"),
                                _text_input(
                                    value=PCState.form_ram,
                                    on_change=PCState.set_form_ram,
                                    placeholder="Contoh: 16GB DDR4 3200MHz",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("VGA / Grafis"),
                                _text_input(
                                    value=PCState.form_vga,
                                    on_change=PCState.set_form_vga,
                                    placeholder="Contoh: Intel UHD 730 / GTX 1650 4GB",
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
                            _field_label("HDD / SSD"),
                            _text_input(
                                value=PCState.form_hdd_ssd,
                                on_change=PCState.set_form_hdd_ssd,
                                placeholder="Contoh: SSD NVMe Samsung 980 500GB + HDD 1TB",
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        # Grup 3: Periferal (Monitor, Keyboard, Mouse)
                        rx.box(
                            rx.vstack(
                                _field_label("Monitor"),
                                _text_input(
                                    value=PCState.form_monitor,
                                    on_change=PCState.set_form_monitor,
                                    placeholder="Contoh: LG 24MK600M 24\"",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Keyboard"),
                                _text_input(
                                    value=PCState.form_keyboard,
                                    on_change=PCState.set_form_keyboard,
                                    placeholder="Contoh: Logitech K120 USB",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                _field_label("Mouse"),
                                _text_input(
                                    value=PCState.form_mouse,
                                    on_change=PCState.set_form_mouse,
                                    placeholder="Contoh: Logitech B100 Optical",
                                ),
                                spacing="1",
                                align="start",
                                width="100%",
                            ),
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "display": "grid",
                                    "grid_template_columns": "repeat(3, minmax(0, 1fr))",
                                    "gap": Space.S3,
                                    "@media (max-width: 639px)": {"grid_template_columns": "1fr"},
                                }
                            ),
                        ),
                        # Catatan
                        rx.vstack(
                            _field_label("Catatan (Opsional)"),
                            rx.el.textarea(
                                value=PCState.form_catatan,
                                on_change=PCState.set_form_catatan,
                                placeholder=(
                                    "Catatan tambahan lokasi meja, KVM switch, jadwal sync, dll."
                                ),
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
                            on_click=PCState.close_form_modal,
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
                            PCState.form_mode == "edit",
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
                                on_click=PCState.duplicate_current_form,
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
                            PCState.form_mode == "add",
                            rx.el.button(
                                "Simpan & tambah lagi",
                                type="button",
                                on_click=PCState.save_and_add_another,
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
                                PCState.form_mode == "edit",
                                "Simpan Perubahan",
                                "Simpan PC",
                            ),
                            type="button",
                            on_click=PCState.save_pc_form,
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
                        "max_width": "680px",
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


__all__ = ["pc_form_modal"]
