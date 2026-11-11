"""Halaman View Jadwal Maintenance ITAM Pro (Artboard 13 & 14).

Melebur jadwal fisik (PC/Printer/Server) dan perangkat lunak (Backup Database)
ke dalam satu ekosistem terpadu menggunakan recurrence engine.
"""

from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.filter_bar import table_filter_bar
from itam_pro.components.ui.tabs import app_tabs
from itam_pro.states.maintenance_state import MaintenanceState
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


def _mnt_kpi_card(
    card_key: str,
    title: str,
    count_val: Any,
    subtitle: str,
    footer_link: str,
    icon_tag: str,
    icon_color: str,
    icon_bg: str,
    extra_badge: str = "",
) -> rx.Component:
    is_active = MaintenanceState.active_kpi_card == card_key
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon(
                        tag=icon_tag,
                        size=16,
                        color=rx.cond(is_active, Color.WHITE, icon_color),
                    ),
                    width="30px",
                    height="30px",
                    border_radius="8px",
                    background_color=rx.cond(is_active, Color.WHITE_ALPHA_18, icon_bg),
                ),
                rx.text(
                    title,
                    font_size=FontSize.GROUP_LABEL,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(is_active, Color.WHITE_85, Color.MUTED),
                    letter_spacing="0.06em",
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.text(
                    count_val,
                    font_size="30px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=rx.cond(is_active, Color.WHITE, Color.TEXT),
                    line_height="1.1",
                ),
                rx.cond(
                    extra_badge != "",
                    rx.box(
                        rx.text(
                            extra_badge,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.SUCCESS_FG,
                        ),
                        padding="2px 8px",
                        border_radius=Radius.FULL,
                        background_color=Color.SUCCESS_BG,
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                subtitle,
                font_size=FontSize.XS,
                color=rx.cond(is_active, Color.WHITE_ALPHA_80, Color.MUTED),
            ),
            rx.cond(
                footer_link != "",
                rx.text(
                    footer_link,
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(is_active, Color.WHITE, Color.ACCENT),
                    padding_top="2px",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        on_click=MaintenanceState.select_kpi_card(card_key),
        style=rx.Style(
            {
                "padding": "18px 20px",
                "border_radius": Radius.CARD,
                "background_color": rx.cond(is_active, Color.NAVY_800, Color.SURFACE),
                "border": rx.cond(
                    is_active,
                    f"2px solid {Color.NAVY_800}",
                    f"1px solid {Color.BORDER}",
                ),
                "cursor": "pointer",
            }
        ),
    )


def _kpi_cards() -> rx.Component:
    """4 Kartu KPI yang bisa diklik sesuai Artboard 13."""
    return rx.grid(
        _mnt_kpi_card(
            "terlambat",
            "TERLAMBAT",
            MaintenanceState.summary["terlambat"],
            "perlu segera ditangani",
            "Lihat yang terlambat →",
            "triangle-alert",
            Color.DANGER_FG,
            Color.DANGER_BG,
        ),
        _mnt_kpi_card(
            "segera",
            "JATUH TEMPO ≤ 7 HARI",
            MaintenanceState.summary["segera"],
            "belum ada yang mendesak",
            "",
            "clock",
            Color.WARNING_FG,
            Color.WARNING_BG,
            extra_badge="Aman",
        ),
        _mnt_kpi_card(
            "jadwal_aktif",
            "JADWAL AKTIF",
            MaintenanceState.summary["aktif"],
            "rencana berjalan",
            "Lihat kalender →",
            "calendar",
            Color.ACCENT,
            Color.INFO_BG,
        ),
        _mnt_kpi_card(
            "tindak_lanjut",
            "PERLU TINDAK LANJUT",
            MaintenanceState.summary["tindak_lanjut"],
            "temuan dari hasil maintenance",
            "Lihat temuan →",
            "wrench",
            Color.WARNING_FG,
            Color.WARNING_BG,
        ),
        columns="4",
        spacing="4",
        width="100%",
    )


def _category_chip_pill(name: str) -> rx.Component:
    is_active = MaintenanceState.active_category_chip == name
    cnt = rx.cond(
        MaintenanceState.chip_counts[name],
        MaintenanceState.chip_counts[name],
        0,
    )
    return rx.box(
        rx.text(
            f"{name} {cnt}",
            font_size=FontSize.XS,
            font_weight=FontWeight.BOLD,
            color=rx.cond(is_active, Color.ACCENT_BRIGHT, Color.TEXT),
        ),
        on_click=MaintenanceState.select_category_chip(name),
        style=rx.Style(
            {
                "padding": "6px 14px",
                "border_radius": Radius.FULL,
                "background_color": rx.cond(is_active, Color.INFO_BG, Color.SURFACE),
                "border": rx.cond(
                    is_active,
                    f"1px solid {Color.ACCENT_BRIGHT}",
                    f"1px solid {Color.BORDER}",
                ),
                "cursor": "pointer",
            }
        ),
    )


def _schedule_row_item(plan: Any, is_overdue_row: bool = False) -> rx.Component:
    """Satu baris jadwal maintenance sesuai kolom Artboard 13."""
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    plan["objek_display"],
                    font_size=FontSize.SM,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    plan["sub_label"],
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                spacing="0",
                align="start",
            )
        ),
        rx.table.cell(rx.text(plan["kegiatan"], font_size=FontSize.SM, color=Color.TEXT)),
        rx.table.cell(rx.text(plan["jenis"], font_size=FontSize.SM, color=Color.TEXT)),
        rx.table.cell(rx.text(plan["frekuensi"], font_size=FontSize.SM, color=Color.TEXT)),
        rx.table.cell(
            rx.text(plan["terakhir_hasil_display"], font_size=FontSize.XS, color=Color.MUTED)
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    plan["jadwal_display"],
                    font_size=FontSize.SM,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    plan["status_label"],
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(
                        plan["status"] == "Terlambat",
                        Color.DANGER_FG,
                        Color.MUTED,
                    ),
                ),
                spacing="0",
                align="start",
            )
        ),
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.text(
                        plan["pelaksana_tipe"],
                        font_size="11px",
                        font_weight=FontWeight.BOLD,
                        color=rx.cond(
                            plan["pelaksana_tipe"] == "Vendor",
                            Color.PURPLE_700,
                            Color.SUCCESS_FG,
                        ),
                    ),
                    padding="2px 8px",
                    border_radius=Radius.FULL,
                    background_color=rx.cond(
                        plan["pelaksana_tipe"] == "Vendor",
                        Color.PURPLE_100,
                        Color.SUCCESS_BG,
                    ),
                ),
                rx.text(plan["pic"], font_size=FontSize.SM, color=Color.TEXT),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    plan["status"],
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=rx.cond(
                        plan["status"] == "Terlambat",
                        Color.DANGER_FG,
                        Color.ACCENT_BRIGHT,
                    ),
                ),
                padding="3px 10px",
                border_radius=Radius.FULL,
                background_color=rx.cond(
                    plan["status"] == "Terlambat",
                    Color.DANGER_BG,
                    Color.INFO_BG,
                ),
                display="inline-block",
            )
        ),
        rx.table.cell(
            rx.el.button(
                "Selesai",
                type="button",
                on_click=MaintenanceState.open_tandai_selesai(plan),
                style=rx.Style(
                    {
                        "padding": "6px 14px",
                        "border_radius": Radius.CONTROL,
                        "font_size": FontSize.XS,
                        "font_weight": FontWeight.BOLD,
                        "background_color": (
                            Color.ACCENT_BRIGHT if is_overdue_row else Color.SURFACE
                        ),
                        "color": Color.WHITE if is_overdue_row else Color.TEXT,
                        "border": "none" if is_overdue_row else f"1px solid {Color.BORDER}",
                        "cursor": "pointer",
                    }
                ),
            )
        ),
    )


def _daftar_tab() -> rx.Component:
    return rx.vstack(
        _kpi_cards(),
        # Baris Chip Jenis Objek (Artboard 13)
        rx.hstack(
            _category_chip_pill("Semua"),
            _category_chip_pill("PC & Server"),
            _category_chip_pill("UPS"),
            _category_chip_pill("AC"),
            _category_chip_pill("Genset"),
            _category_chip_pill("Jaringan"),
            _category_chip_pill("Fasilitas"),
            _category_chip_pill("Kendaraan"),
            spacing="2",
            wrap="wrap",
            width="100%",
        ),
        # Kartu Filter + Tabel Terkelompok (TERLAMBAT & MENDATANG)
        rx.box(
            rx.hstack(
                rx.el.input(
                    placeholder="Cari objek atau kegiatan...",
                    value=MaintenanceState.search_query,
                    on_change=MaintenanceState.set_search_query,
                    style=rx.Style(
                        {
                            "width": "240px",
                            "height": "38px",
                            "padding": "0 12px",
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.SM,
                        }
                    ),
                ),
                rx.el.select(
                    rx.el.option("Semua status", value="Semua status"),
                    rx.el.option("Terlambat", value="Terlambat"),
                    rx.el.option("Segera", value="Segera"),
                    rx.el.option("Terjadwal", value="Terjadwal"),
                    value=MaintenanceState.status_filter,
                    on_change=MaintenanceState.set_status_filter,
                    style=rx.Style(
                        {
                            "height": "38px",
                            "padding": "0 12px",
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.SM,
                        }
                    ),
                ),
                rx.el.select(
                    rx.el.option("Semua jenis", value="Semua jenis"),
                    rx.el.option("Preventif", value="Preventif"),
                    rx.el.option("Inspeksi", value="Inspeksi"),
                    rx.el.option("Korektif", value="Korektif"),
                    value=MaintenanceState.jenis_filter,
                    on_change=MaintenanceState.set_jenis_filter,
                    style=rx.Style(
                        {
                            "height": "38px",
                            "padding": "0 12px",
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.SM,
                        }
                    ),
                ),
                rx.el.select(
                    rx.el.option("Semua pelaksana", value="Semua pelaksana"),
                    rx.el.option("Vendor", value="Vendor"),
                    rx.el.option("Internal", value="Internal"),
                    value=MaintenanceState.pelaksana_filter,
                    on_change=MaintenanceState.set_pelaksana_filter,
                    style=rx.Style(
                        {
                            "height": "38px",
                            "padding": "0 12px",
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.SM,
                        }
                    ),
                ),
                rx.el.select(
                    rx.el.option("Semua PIC", value="Semua PIC"),
                    rx.el.option("Teknisi AC", value="Teknisi AC"),
                    rx.el.option("Ridho", value="Ridho"),
                    rx.el.option("Surya", value="Surya"),
                    value=MaintenanceState.pic_filter,
                    on_change=MaintenanceState.set_pic_filter,
                    style=rx.Style(
                        {
                            "height": "38px",
                            "padding": "0 12px",
                            "border": f"1px solid {Color.INPUT_BORDER}",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.SM,
                        }
                    ),
                ),
                rx.el.button(
                    "Reset filter",
                    type="button",
                    on_click=MaintenanceState.reset_filters,
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
                rx.spacer(),
                rx.text(
                    MaintenanceState.total_filtered_label,
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                spacing="2",
                align="center",
                wrap="wrap",
                padding="14px 18px",
                width="100%",
                style=rx.Style({"border_bottom": f"1px solid {Color.BORDER}"}),
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("OBJEK"),
                        rx.table.column_header_cell("KEGIATAN"),
                        rx.table.column_header_cell("JENIS"),
                        rx.table.column_header_cell("FREKUENSI"),
                        rx.table.column_header_cell("TERAKHIR · HASIL"),
                        rx.table.column_header_cell("JADWAL BERIKUTNYA"),
                        rx.table.column_header_cell("PELAKSANA"),
                        rx.table.column_header_cell("STATUS"),
                        rx.table.column_header_cell("AKSI"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(
                            rx.text(
                                f"TERLAMBAT · {MaintenanceState.overdue_count_filtered}",
                                font_size="11px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.DANGER_FG,
                                letter_spacing="0.06em",
                            ),
                            col_span=9,
                            style=rx.Style(
                                {"background_color": Color.RED_50, "padding": "8px 16px"}
                            ),
                        )
                    ),
                    rx.foreach(
                        MaintenanceState.overdue_plans,
                        lambda p: _schedule_row_item(p, is_overdue_row=True),
                    ),
                    rx.table.row(
                        rx.table.cell(
                            rx.text(
                                f"MENDATANG · {MaintenanceState.upcoming_count_filtered}",
                                font_size="11px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.MUTED,
                                letter_spacing="0.06em",
                            ),
                            col_span=9,
                            style=rx.Style(
                                {
                                    "background_color": Color.TABLE_HEADER_BG,
                                    "padding": "8px 16px",
                                }
                            ),
                        )
                    ),
                    rx.foreach(
                        MaintenanceState.upcoming_plans,
                        lambda p: _schedule_row_item(p, is_overdue_row=False),
                    ),
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
        width="100%",
        spacing="4",
    )


def _tandai_selesai_dialog() -> rx.Component:
    """Modal Tandai Selesai sesuai Artboard 14 (Kanan)."""
    return rx.cond(
        MaintenanceState.is_selesai_open,
        rx.box(
            rx.box(
                on_click=MaintenanceState.close_tandai_selesai,
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
                                "Tandai selesai",
                                font_size="20px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                MaintenanceState.selesai_plan_title,
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
                            on_click=MaintenanceState.close_tandai_selesai,
                            style=rx.Style(
                                {"background": "transparent", "border": "none", "cursor": "pointer"}
                            ),
                        ),
                        width="100%",
                        align="start",
                    ),
                    # Unit dikerjakan (untuk kelompok AC)
                    rx.cond(
                        MaintenanceState.selesai_is_group,
                        rx.vstack(
                            rx.text(
                                "Unit dikerjakan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.hstack(
                                rx.foreach(
                                    MaintenanceState.selesai_all_units,
                                    lambda u: rx.el.label(
                                        rx.hstack(
                                            rx.el.input(
                                                type="checkbox",
                                                checked=MaintenanceState.selesai_checked_units.contains(
                                                    u
                                                ),
                                                on_change=MaintenanceState.toggle_selesai_unit(u),
                                            ),
                                            rx.text(
                                                u,
                                                font_size=FontSize.XS,
                                                font_weight=FontWeight.SEMIBOLD,
                                            ),
                                            spacing="1",
                                            align="center",
                                        ),
                                        style=rx.Style(
                                            {"cursor": "pointer", "margin_right": "10px"}
                                        ),
                                    ),
                                ),
                                rx.text(
                                    MaintenanceState.selesai_units_summary_label,
                                    font_size=FontSize.XS,
                                    color=Color.MUTED,
                                ),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    # Baris Tanggal dikerjakan & Pelaksana
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Tanggal dikerjakan *",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="date",
                                value=MaintenanceState.selesai_tgl,
                                on_change=MaintenanceState.set_selesai_tgl,
                                style=_modal_input_style(),
                            ),
                            width="58%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Pelaksana",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.hstack(
                                rx.el.button(
                                    "Vendor",
                                    type="button",
                                    on_click=MaintenanceState.set_selesai_pelaksana_tipe("Vendor"),
                                    style=rx.Style(
                                        {
                                            "padding": "7px 14px",
                                            "border_radius": Radius.CONTROL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.selesai_pelaksana_tipe
                                                == "Vendor",
                                                Color.SURFACE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.selesai_pelaksana_tipe
                                                == "Vendor",
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": "none",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                rx.el.button(
                                    "Internal",
                                    type="button",
                                    on_click=MaintenanceState.set_selesai_pelaksana_tipe(
                                        "Internal"
                                    ),
                                    style=rx.Style(
                                        {
                                            "padding": "7px 14px",
                                            "border_radius": Radius.CONTROL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.selesai_pelaksana_tipe
                                                == "Internal",
                                                Color.SURFACE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.selesai_pelaksana_tipe
                                                == "Internal",
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": "none",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                spacing="1",
                                padding="3px",
                                style=rx.Style(
                                    {
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                            width="42%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Baris Vendor/Teknisi & Biaya (Rp)
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Vendor / teknisi",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.select(
                                rx.el.option("Teknisi AC", value="Teknisi AC"),
                                rx.el.option("Ridho", value="Ridho"),
                                rx.el.option("Surya", value="Surya"),
                                value=MaintenanceState.selesai_pic,
                                on_change=MaintenanceState.set_selesai_pic,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Biaya (Rp)",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                placeholder="Contoh: 450.000",
                                value=MaintenanceState.selesai_biaya,
                                on_change=MaintenanceState.set_selesai_biaya,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Checklist 2 kolom
                    rx.vstack(
                        rx.text(
                            "Checklist",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.box(
                            rx.foreach(
                                MaintenanceState.selesai_checklist_options,
                                lambda chk: rx.el.label(
                                    rx.hstack(
                                        rx.el.input(
                                            type="checkbox",
                                            checked=MaintenanceState.selesai_checked_items.contains(
                                                chk
                                            ),
                                            on_change=MaintenanceState.toggle_selesai_checklist(
                                                chk
                                            ),
                                        ),
                                        rx.text(chk, font_size=FontSize.XS, color=Color.TEXT),
                                        spacing="2",
                                        align="center",
                                    ),
                                    style=rx.Style({"cursor": "pointer"}),
                                ),
                            ),
                            style=rx.Style(
                                {
                                    "display": "grid",
                                    "grid_template_columns": "1fr 1fr",
                                    "gap": "8px",
                                    "width": "100%",
                                }
                            ),
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    # Hasil / catatan
                    rx.vstack(
                        rx.text(
                            "Hasil / catatan",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.textarea(
                            placeholder="Mis. AC 2 kurang dingin, perlu tambah freon",
                            value=MaintenanceState.selesai_catatan,
                            on_change=MaintenanceState.set_selesai_catatan,
                            rows=2,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "padding": "8px 12px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                }
                            ),
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    # Kotak dashed Unggah foto atau nota
                    rx.center(
                        rx.text(
                            "Unggah foto atau nota (maks. 5 file)",
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        width="100%",
                        padding="10px",
                        style=rx.Style(
                            {
                                "border": f"1.5px dashed {Color.BLUE_300}",
                                "border_radius": Radius.CONTROL,
                                "background_color": Color.SLATE_50,
                            }
                        ),
                    ),
                    # Centang Ada temuan
                    rx.el.label(
                        rx.hstack(
                            rx.el.input(
                                type="checkbox",
                                checked=MaintenanceState.selesai_ada_temuan,
                                on_change=MaintenanceState.toggle_selesai_ada_temuan,
                            ),
                            rx.text(
                                "Ada temuan, buat tiket perbaikan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.SEMIBOLD,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        style=rx.Style({"cursor": "pointer"}),
                    ),
                    # Kotak Pratinjau Jadwal Berikutnya
                    rx.box(
                        rx.hstack(
                            rx.text(
                                "Jadwal berikutnya otomatis:",
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                MaintenanceState.preview_next_due_selesai_modal,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            spacing="1",
                            wrap="wrap",
                        ),
                        width="100%",
                        padding="10px 14px",
                        style=rx.Style(
                            {
                                "background_color": Color.BLUE_50,
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=MaintenanceState.close_tandai_selesai,
                            style=rx.Style(
                                {
                                    "padding": "8px 18px",
                                    "background_color": Color.SURFACE,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan & jadwalkan berikutnya",
                            type="button",
                            on_click=MaintenanceState.submit_tandai_selesai,
                            style=rx.Style(
                                {
                                    "padding": "8px 20px",
                                    "background_color": Color.ACCENT_BRIGHT,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    align="start",
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
                        "max_height": "92vh",
                        "overflow_y": "auto",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "22px 24px",
                        "z_index": "90",
                    }
                ),
                role="dialog",
            ),
        ),
    )


def _buat_jadwal_massal_dialog() -> rx.Component:
    """Modal Buat Rencana Maintenance sesuai Artboard 14 (Kiri)."""
    return rx.cond(
        MaintenanceState.is_massal_open,
        rx.box(
            rx.box(
                on_click=MaintenanceState.close_massal,
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
                                "Buat rencana maintenance",
                                font_size="20px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                "Satu rencana otomatis menghasilkan jadwal berikutnya.",
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
                            on_click=MaintenanceState.close_massal,
                            style=rx.Style(
                                {"background": "transparent", "border": "none", "cursor": "pointer"}
                            ),
                        ),
                        width="100%",
                        align="start",
                    ),
                    # Baris Pill Template (PC | Server | UPS | AC | Genset | Jaringan | Kustom)
                    rx.vstack(
                        rx.text(
                            "Template",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.hstack(
                            *[
                                rx.el.button(
                                    t_name,
                                    type="button",
                                    on_click=MaintenanceState.select_plan_template(t_name),
                                    style=rx.Style(
                                        {
                                            "padding": "5px 12px",
                                            "border_radius": Radius.FULL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.plan_template == t_name,
                                                Color.INFO_BG,
                                                Color.SURFACE,
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.plan_template == t_name,
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": rx.cond(
                                                MaintenanceState.plan_template == t_name,
                                                f"1px solid {Color.ACCENT_BRIGHT}",
                                                f"1px solid {Color.BORDER}",
                                            ),
                                            "cursor": "pointer",
                                        }
                                    ),
                                )
                                for t_name in (
                                    "PC",
                                    "Server",
                                    "UPS",
                                    "AC",
                                    "Genset",
                                    "Jaringan",
                                    "Kustom",
                                )
                            ],
                            spacing="2",
                            wrap="wrap",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    # Toggle Objek (Satu aset | Kelompok aset | Lokasi)
                    rx.vstack(
                        rx.text("Objek", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                        rx.hstack(
                            *[
                                rx.el.button(
                                    obj_opt,
                                    type="button",
                                    on_click=MaintenanceState.set_plan_objek_tipe(obj_opt),
                                    style=rx.Style(
                                        {
                                            "padding": "6px 14px",
                                            "border_radius": Radius.CONTROL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.plan_objek_tipe == obj_opt,
                                                Color.SURFACE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.plan_objek_tipe == obj_opt,
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": "none",
                                            "cursor": "pointer",
                                        }
                                    ),
                                )
                                for obj_opt in ("Satu aset", "Kelompok aset", "Lokasi")
                            ],
                            spacing="1",
                            padding="3px",
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
                    # Kategori & Lokasi
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Kategori",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.select(
                                rx.el.option("AC", value="AC"),
                                rx.el.option("PC", value="PC"),
                                rx.el.option("Server", value="Server"),
                                rx.el.option("UPS", value="UPS"),
                                rx.el.option("Genset", value="Genset"),
                                rx.el.option("Jaringan", value="Jaringan"),
                                rx.el.option("Kendaraan", value="Kendaraan"),
                                rx.el.option("Fasilitas", value="Fasilitas"),
                                value=MaintenanceState.massal_kategori,
                                on_change=MaintenanceState.set_massal_kategori,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text("Lokasi", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                            rx.el.select(
                                rx.el.option("Kantor Blok 12", value="Kantor Blok 12"),
                                rx.el.option("Kantor Blok 13", value="Kantor Blok 13"),
                                rx.el.option("Kantor Blok 14", value="Kantor Blok 14"),
                                rx.el.option("Ruko Rinjani", value="Ruko Rinjani"),
                                value=MaintenanceState.plan_lokasi,
                                on_change=MaintenanceState.set_plan_lokasi,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Ruangan & Chip N unit terdeteksi
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Ruangan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.select(
                                rx.foreach(
                                    MaintenanceState.room_options_for_plan,
                                    lambda rm: rx.el.option(rm, value=rm),
                                ),
                                value=MaintenanceState.plan_ruangan,
                                on_change=MaintenanceState.set_plan_ruangan,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(" ", font_size=FontSize.XS),
                            rx.box(
                                rx.text(
                                    f"{MaintenanceState.plan_detected_units} unit terdeteksi",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.SUCCESS_FG,
                                ),
                                padding="8px 14px",
                                border_radius=Radius.CONTROL,
                                background_color=Color.SUCCESS_BG,
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Kegiatan & Jenis
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Kegiatan *",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                value=MaintenanceState.massal_kegiatan,
                                on_change=MaintenanceState.set_massal_kegiatan,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text("Jenis", font_size=FontSize.XS, font_weight=FontWeight.BOLD),
                            rx.el.select(
                                rx.el.option("Preventif", value="Preventif"),
                                rx.el.option("Inspeksi", value="Inspeksi"),
                                rx.el.option("Korektif", value="Korektif"),
                                value=MaintenanceState.massal_jenis,
                                on_change=MaintenanceState.set_massal_jenis,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Frekuensi & Terakhir dikerjakan
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Frekuensi",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.hstack(
                                rx.el.input(
                                    type="number",
                                    value=MaintenanceState.plan_interval_nilai,
                                    on_change=MaintenanceState.set_plan_interval_nilai,
                                    style=rx.Style(
                                        {
                                            "width": "64px",
                                            "height": Size.FILTER_CONTROL_H,
                                            "padding": "0 10px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                rx.el.select(
                                    rx.el.option("bulan", value="bulan"),
                                    rx.el.option("minggu", value="minggu"),
                                    rx.el.option("hari", value="hari"),
                                    value=MaintenanceState.plan_interval_satuan,
                                    on_change=MaintenanceState.set_plan_interval_satuan,
                                    style=_modal_input_style(),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Terakhir dikerjakan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="date",
                                value=MaintenanceState.massal_tgl_mulai,
                                on_change=MaintenanceState.set_massal_tgl_mulai,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    # Kotak Pratinjau Jadwal Berikutnya
                    rx.box(
                        rx.hstack(
                            rx.text(
                                "Jadwal berikutnya otomatis:",
                                font_size=FontSize.XS,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                MaintenanceState.preview_next_due_plan_modal,
                                font_size=FontSize.XS,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            spacing="1",
                        ),
                        width="100%",
                        padding="10px 14px",
                        style=rx.Style(
                            {
                                "background_color": Color.BLUE_50,
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    # Pemicu jam pakai
                    rx.hstack(
                        rx.el.input(
                            type="checkbox",
                            checked=MaintenanceState.plan_use_meter,
                            on_change=MaintenanceState.toggle_plan_use_meter,
                        ),
                        rx.text(
                            "Tambah pemicu jam pakai (genset, kendaraan): servis tiap",
                            font_size=FontSize.XS,
                        ),
                        rx.el.input(
                            value=MaintenanceState.plan_meter_interval,
                            on_change=MaintenanceState.set_plan_meter_interval,
                            style=rx.Style(
                                {
                                    "width": "64px",
                                    "height": "30px",
                                    "padding": "0 8px",
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                }
                            ),
                        ),
                        rx.text("jam", font_size=FontSize.XS),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    # Pelaksana & Pengingat
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Pelaksana",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.hstack(
                                rx.el.button(
                                    "Vendor",
                                    type="button",
                                    on_click=MaintenanceState.set_plan_pelaksana_tipe("Vendor"),
                                    style=rx.Style(
                                        {
                                            "padding": "6px 12px",
                                            "border_radius": Radius.CONTROL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.plan_pelaksana_tipe == "Vendor",
                                                Color.SURFACE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.plan_pelaksana_tipe == "Vendor",
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": "none",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                rx.el.button(
                                    "Internal",
                                    type="button",
                                    on_click=MaintenanceState.set_plan_pelaksana_tipe("Internal"),
                                    style=rx.Style(
                                        {
                                            "padding": "6px 12px",
                                            "border_radius": Radius.CONTROL,
                                            "font_size": FontSize.XS,
                                            "font_weight": FontWeight.BOLD,
                                            "background_color": rx.cond(
                                                MaintenanceState.plan_pelaksana_tipe
                                                == "Internal",
                                                Color.SURFACE,
                                                "transparent",
                                            ),
                                            "color": rx.cond(
                                                MaintenanceState.plan_pelaksana_tipe
                                                == "Internal",
                                                Color.ACCENT_BRIGHT,
                                                Color.TEXT,
                                            ),
                                            "border": "none",
                                            "cursor": "pointer",
                                        }
                                    ),
                                ),
                                spacing="1",
                                padding="3px",
                                style=rx.Style(
                                    {
                                        "background_color": Color.TABLE_HEADER_BG,
                                        "border_radius": Radius.CONTROL,
                                    }
                                ),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Pengingat",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.hstack(
                                *[
                                    rx.el.button(
                                        rem_lbl,
                                        type="button",
                                        on_click=MaintenanceState.toggle_plan_reminder(rem_lbl),
                                        style=rx.Style(
                                            {
                                                "padding": "4px 10px",
                                                "border_radius": Radius.FULL,
                                                "font_size": FontSize.XS,
                                                "font_weight": FontWeight.BOLD,
                                                "background_color": rx.cond(
                                                    MaintenanceState.plan_reminders.contains(
                                                        rem_lbl
                                                    ),
                                                    Color.INFO_BG,
                                                    Color.SURFACE,
                                                ),
                                                "color": rx.cond(
                                                    MaintenanceState.plan_reminders.contains(
                                                        rem_lbl
                                                    ),
                                                    Color.ACCENT_BRIGHT,
                                                    Color.TEXT,
                                                ),
                                                "border": f"1px solid {Color.BORDER}",
                                                "cursor": "pointer",
                                            }
                                        ),
                                    )
                                    for rem_lbl in ("H-7", "H-1", "Hari H")
                                ],
                                spacing="1",
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=MaintenanceState.close_massal,
                            style=rx.Style(
                                {
                                    "padding": "8px 18px",
                                    "background_color": Color.SURFACE,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan rencana",
                            type="button",
                            on_click=MaintenanceState.submit_massal,
                            style=rx.Style(
                                {
                                    "padding": "8px 20px",
                                    "background_color": Color.ACCENT_BRIGHT,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "500px",
                        "max_width": "94vw",
                        "max_height": "92vh",
                        "overflow_y": "auto",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "22px 24px",
                        "z_index": "90",
                    }
                ),
                role="dialog",
            ),
        ),
    )


def _import_ac_csv_dialog() -> rx.Component:
    """Modal Import CSV Google Sheet AC (Bagian F)."""
    return rx.cond(
        MaintenanceState.is_import_ac_open,
        rx.box(
            rx.box(
                on_click=MaintenanceState.close_import_ac_modal,
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
                        "Import CSV Jadwal AC (Google Sheet)",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.text(
                        "Kolom: Lokasi, Jenis Ruangan, Jumlah AC, "
                        "Tanggal Cuci Terakhir (dd/mm/yyyy), Interval (bulan). "
                        "Jadwal berikutnya & status dihitung ulang otomatis.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    rx.el.textarea(
                        value=MaintenanceState.import_ac_csv_text,
                        on_change=MaintenanceState.set_import_ac_csv_text,
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
                    rx.text(
                        MaintenanceState.import_ac_preview_summary,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.ACCENT_BRIGHT,
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=MaintenanceState.close_import_ac_modal,
                            style=rx.Style(
                                {
                                    "padding": "8px 16px",
                                    "background": Color.SURFACE,
                                    "border": f"1px solid {Color.BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Validasi Ulang",
                            type="button",
                            on_click=MaintenanceState.run_import_ac_preview,
                            style=rx.Style(
                                {
                                    "padding": "8px 16px",
                                    "background": Color.INFO_BG,
                                    "color": Color.ACCENT_BRIGHT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan & Impor Rencana AC",
                            type="button",
                            on_click=MaintenanceState.commit_import_ac_csv,
                            style=rx.Style(
                                {
                                    "padding": "8px 18px",
                                    "background": Color.ACCENT_BRIGHT,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_size": FontSize.XS,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
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
                        "width": "540px",
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
    )


def _kalender_tab() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="calendar", size=18, color=Color.ACCENT),
                    rx.text(
                        "Kalender Perawatan Bulan Ini",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Klik baris rencana untuk menandai selesai pekerjaan",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
                justify="between",
                width="100%",
                padding="16px 20px",
                style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
            ),
            rx.center(
                rx.vstack(
                    rx.icon(tag="calendar-days", size=48, color=Color.ACCENT),
                    rx.text(
                        "Tampilan Kalender Jadwal Terpadu",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.BOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Menampilkan ringkasan jadwal jatuh tempo dan status operasional bulanan.",
                        font_size=FontSize.SM,
                        color=Color.MUTED,
                    ),
                    rx.grid(
                        rx.foreach(
                            MaintenanceState.plans,
                            lambda plan: rx.box(
                                rx.hstack(
                                    rx.box(
                                        width="8px",
                                        height="8px",
                                        border_radius=Radius.FULL,
                                        background_color=rx.match(
                                            plan["status"],
                                            ("Terlambat", Color.DANGER_FG),
                                            ("Segera", Color.WARNING_FG),
                                            Color.INFO_FG,
                                        ),
                                    ),
                                    rx.vstack(
                                        rx.text(
                                            plan["jadwal_berikutnya"],
                                            font_size=FontSize.XS,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.MUTED,
                                        ),
                                        rx.text(
                                            plan["objek_display"],
                                            font_size=FontSize.SM,
                                            font_weight=FontWeight.BOLD,
                                            color=Color.TEXT,
                                        ),
                                        rx.text(
                                            plan["kegiatan"],
                                            font_size=FontSize.XS,
                                            color=Color.MUTED,
                                        ),
                                        spacing="1",
                                        align="start",
                                    ),
                                    spacing="3",
                                    align="start",
                                ),
                                on_click=MaintenanceState.open_tandai_selesai(plan),
                                style=rx.Style(
                                    {
                                        "padding": "12px 14px",
                                        "background_color": Color.SURFACE,
                                        "border": f"1px solid {Color.BORDER}",
                                        "border_radius": Radius.CONTROL,
                                        "cursor": "pointer",
                                        "_hover": {"border_color": Color.ACCENT},
                                    }
                                ),
                            ),
                        ),
                        columns="3",
                        spacing="3",
                        width="100%",
                        padding="20px",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                padding="30px 10px",
                width="100%",
            ),
            width="100%",
            spacing="0",
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
    )


def _riwayat_tab() -> rx.Component:
    return rx.box(
        table_filter_bar(
            search_value=MaintenanceState.history_search_query,
            on_search_change=MaintenanceState.set_history_search,
            search_placeholder="Cari log riwayat...",
        ),
        reusable_data_table(
            items=MaintenanceState.logs,
            id_key="id",
            columns=[
                {
                    "header": "TANGGAL SELESAI",
                    "accessor": "tanggal_selesai",
                    "render_type": "date",
                },
                {"header": "OBJEK", "accessor": "objek_display", "render_type": "bold"},
                {"header": "KEGIATAN", "accessor": "kegiatan"},
                {"header": "HASIL", "accessor": "hasil"},
                {"header": "DIKERJAKAN OLEH", "accessor": "dikerjakan_oleh"},
                {"header": "CATATAN", "accessor": "catatan"},
            ],
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
    )


def maintenance_view_page() -> rx.Component:
    """Komponen Page Utama Modul Jadwal Maintenance (/operations/maintenance)."""
    return base_layout(
        rx.vstack(
            rx.hstack(
                app_tabs(
                    items=[
                        {"label": "Daftar", "value": "daftar"},
                        {"label": "Kalender", "value": "kalender"},
                        {"label": "Riwayat", "value": "riwayat"},
                        {"label": "Rencana", "value": "rencana"},
                    ],
                    active_value=MaintenanceState.active_tab,
                    on_change=MaintenanceState.set_tab,
                ),
                rx.hstack(
                    rx.el.button(
                        "Import CSV",
                        type="button",
                        on_click=MaintenanceState.open_import_ac_modal,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 16px",
                                "background_color": Color.SURFACE,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "color": Color.TEXT,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    rx.el.button(
                        "+ Buat Rencana",
                        type="button",
                        on_click=MaintenanceState.open_massal,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 18px",
                                "background_color": Color.ACCENT_BRIGHT,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "color": Color.WHITE,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                            }
                        ),
                    ),
                    spacing="3",
                    align="center",
                    padding_right=Space.S5,
                ),
                justify="between",
                align="center",
                width="100%",
                style=rx.Style(
                    {
                        "background_color": Color.SURFACE,
                        "border_bottom": f"1px solid {Color.BORDER}",
                    }
                ),
            ),
            rx.match(
                MaintenanceState.active_tab,
                ("daftar", _daftar_tab()),
                ("kalender", _kalender_tab()),
                ("riwayat", _riwayat_tab()),
                ("rencana", _daftar_tab()),
                _daftar_tab(),
            ),
            _tandai_selesai_dialog(),
            _buat_jadwal_massal_dialog(),
            _import_ac_csv_dialog(),
            spacing="5",
            width="100%",
        ),
        breadcrumb=("Operations", "Jadwal Maintenance"),
    )
