"""
Halaman Infrastructure -> Rekap Watt Server (/watt-server).
Mendukung Artboard 15 (Rekap, 5 KPI, & Utilisasi UPS), Artboard 16 (Asumsi & Rincian),
Artboard 17 (Kalkulator Watt Server), dan Artboard 18 (Katalog & Skenario).
"""

from typing import Any

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
    secondary_button,
)
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
    {
        "key": "nama_aset",
        "header": "SERVER",
        "width": "210px",
        "min_width": "185px",
        "render_type": "name_with_sub",
        "sub_key": "sub_label",
        "sticky_left": True,
        "sortable": True,
        "sort_key": "nama_aset",
    },
    {
        "key": "spesifikasi_ringkas",
        "header": "SPESIFIKASI RINGKAS",
        "width": "290px",
        "min_width": "250px",
        "render_type": "text",
        "sortable": True,
        "sort_key": "cpu",
    },
    {
        "key": "tdp_display",
        "header": "TOTAL TDP",
        "width": "130px",
        "min_width": "115px",
        "render_type": "bold_blue",
        "sortable": True,
        "sort_key": "beban_efektif_w",
    },
    {
        "key": "psu_pair_display",
        "header": "PSU MIN / REKOMENDASI",
        "width": "165px",
        "min_width": "150px",
        "render_type": "bold",
        "sortable": True,
        "sort_key": "psu_rekomendasi_w",
    },
    {
        "key": "kwh_display",
        "header": "ENERGI / BULAN",
        "width": "145px",
        "min_width": "130px",
        "render_type": "text",
        "sortable": True,
        "sort_key": "kwh_per_bulan",
    },
    {
        "key": "beban_badge",
        "header": "BEBAN",
        "width": "115px",
        "min_width": "105px",
        "render_type": "badge",
        "badge_variant_key": "beban_variant",
    },
    {
        "key": "ups_display",
        "header": "UPS · UTILISASI",
        "width": "145px",
        "min_width": "130px",
        "render_type": "text",
        "sortable": True,
        "sort_key": "ups_utilisasi_pct",
    },
]

WATT_COLUMN_OPTIONS: list[ColumnToggleOption] = [
    {"key": "spesifikasi_ringkas", "label": "Spesifikasi Ringkas"},
    {"key": "tdp_display", "label": "Total TDP"},
    {"key": "psu_pair_display", "label": "PSU Min / Rekomendasi"},
    {"key": "kwh_display", "label": "Energi / Bulan"},
    {"key": "beban_badge", "label": "Beban"},
    {"key": "ups_display", "label": "UPS & Utilisasi"},
]


def _watt_header() -> rx.Component:
    """Header Rekap Watt Server + Tab Navigasi (Rekap | Kalkulator | Katalog)."""
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.center(
                    rx.icon(tag="zap", size=24, color=Color.WHITE),
                    width="48px",
                    height="48px",
                    background_color=Color.ACCENT_BRIGHT,
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
                    ),
                    rx.text(
                        "Laporan turunan dari spesifikasi aset: beban, energi, "
                        "kebutuhan PSU, dan kecukupan UPS.",
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
                secondary_button("☀ Asumsi", on_click=PowerState.open_assumptions_modal),
                secondary_button(
                    "Edit spesifikasi di Semua Aset →",
                    on_click=rx.redirect("/assets?category=server"),
                ),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
        ),
        # Tab Bar Utama: Rekap | Kalkulator | Katalog komponen
        rx.hstack(
            rx.el.button(
                "Rekap",
                type="button",
                on_click=PowerState.set_main_section_tab("rekap"),
                style=rx.Style(
                    {
                        "padding": "8px 4px",
                        "margin_right": "20px",
                        "background": "transparent",
                        "border": "none",
                        "border_bottom": rx.cond(
                            PowerState.main_section_tab == "rekap",
                            f"2.5px solid {Color.ACCENT_BRIGHT}",
                            "2.5px solid transparent",
                        ),
                        "color": rx.cond(
                            PowerState.main_section_tab == "rekap",
                            Color.ACCENT_BRIGHT,
                            Color.MUTED,
                        ),
                        "font_weight": FontWeight.BOLD,
                        "font_size": FontSize.SM,
                        "cursor": "pointer",
                    }
                ),
            ),
            rx.el.button(
                "Kalkulator",
                type="button",
                on_click=PowerState.set_main_section_tab("kalkulator"),
                style=rx.Style(
                    {
                        "padding": "8px 4px",
                        "margin_right": "20px",
                        "background": "transparent",
                        "border": "none",
                        "border_bottom": rx.cond(
                            PowerState.main_section_tab == "kalkulator",
                            f"2.5px solid {Color.ACCENT_BRIGHT}",
                            "2.5px solid transparent",
                        ),
                        "color": rx.cond(
                            PowerState.main_section_tab == "kalkulator",
                            Color.ACCENT_BRIGHT,
                            Color.MUTED,
                        ),
                        "font_weight": FontWeight.BOLD,
                        "font_size": FontSize.SM,
                        "cursor": "pointer",
                    }
                ),
            ),
            rx.el.button(
                "Katalog komponen",
                type="button",
                on_click=PowerState.set_main_section_tab("katalog"),
                style=rx.Style(
                    {
                        "padding": "8px 4px",
                        "background": "transparent",
                        "border": "none",
                        "border_bottom": rx.cond(
                            PowerState.main_section_tab == "katalog",
                            f"2.5px solid {Color.ACCENT_BRIGHT}",
                            "2.5px solid transparent",
                        ),
                        "color": rx.cond(
                            PowerState.main_section_tab == "katalog",
                            Color.ACCENT_BRIGHT,
                            Color.MUTED,
                        ),
                        "font_weight": FontWeight.BOLD,
                        "font_size": FontSize.SM,
                        "cursor": "pointer",
                    }
                ),
            ),
            width="100%",
            border_bottom=f"1px solid {Color.BORDER}",
        ),
        # Baris Pemilih Cakupan & Ringkasan Asumsi (Artboard 15)
        rx.hstack(
            rx.hstack(
                rx.text("Cakupan", font_size=FontSize.XS, color=Color.MUTED),
                rx.box(
                    rx.text(
                        "Server",
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.ACCENT_BRIGHT,
                    ),
                    padding="5px 12px",
                    border_radius=Radius.CONTROL,
                    background_color=Color.SURFACE,
                    border=f"1px solid {Color.BORDER}",
                ),
                rx.box(
                    rx.text("PC Operasional · segera", font_size=FontSize.XS, color=Color.MUTED),
                    padding="5px 12px",
                    opacity="0.6",
                ),
                rx.box(
                    rx.text("Semua · segera", font_size=FontSize.XS, color=Color.MUTED),
                    padding="5px 12px",
                    opacity="0.6",
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.text(
                    PowerState.assumptions_summary_bar,
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                rx.el.button(
                    "Ubah",
                    type="button",
                    on_click=PowerState.open_assumptions_modal,
                    style=rx.Style(
                        {
                            "background": "transparent",
                            "border": "none",
                            "color": Color.ACCENT_BRIGHT,
                            "font_size": FontSize.XS,
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
            wrap="wrap",
        ),
        spacing="3",
        width="100%",
    )


def _five_watt_kpi_cards() -> rx.Component:
    """5 Kartu KPI sesuai Artboard 15 (Hero Total Beban TDP, Energi, PSU, Tertinggi, UPS)."""
    return rx.box(
        # 1. Hero Card: TOTAL BEBAN TDP
        rx.box(
            rx.vstack(
                rx.text(
                    "⚡ TOTAL BEBAN TDP",
                    font_size="11px",
                    font_weight=FontWeight.BOLD,
                    color=Color.WHITE_85,
                ),
                rx.text(
                    PowerState.kpi_total_tdp_kw_display,
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.WHITE,
                ),
                rx.text(
                    PowerState.kpi_total_tdp_sub,
                    font_size=FontSize.XS,
                    color=Color.WHITE_75,
                ),
                rx.text(
                    "Lihat peringkat →",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.WHITE,
                    padding_top="4px",
                ),
                spacing="2",
                align="start",
            ),
            on_click=PowerState.toggle_sort("beban_efektif_w"),
            style=rx.Style(
                {
                    "padding": "18px 20px",
                    "border_radius": Radius.CARD,
                    "background": Color.GRADIENT_WATT,
                    "cursor": "pointer",
                }
            ),
        ),
        # 2. ENERGI / BULAN (+ biaya hanya jika tarif diisi)
        rx.box(
            rx.vstack(
                rx.text(
                    "ENERGI / BULAN",
                    font_size="11px",
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.text(
                    PowerState.kpi_kwh_month_display,
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.cond(
                    PowerState.has_tarif_listrik,
                    rx.text(
                        PowerState.kpi_biaya_month_display,
                        font_size=FontSize.XS,
                        font_weight=FontWeight.BOLD,
                        color=Color.SUCCESS_FG,
                    ),
                    rx.text(PowerState.kpi_kwh_sub, font_size=FontSize.XS, color=Color.MUTED),
                ),
                rx.text(
                    "Ubah asumsi →",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT_BRIGHT,
                    padding_top="4px",
                ),
                spacing="2",
                align="start",
            ),
            on_click=PowerState.open_assumptions_modal,
            style=rx.Style(
                {
                    "padding": "18px 20px",
                    "border_radius": Radius.CARD,
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "cursor": "pointer",
                }
            ),
        ),
        # 3. PSU MIN / REKOMENDASI
        rx.box(
            rx.vstack(
                rx.text(
                    "PSU MIN / REKOMENDASI",
                    font_size="11px",
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.text(
                    PowerState.kpi_psu_summary_display,
                    font_size="26px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.text(PowerState.kpi_psu_sub, font_size=FontSize.XS, color=Color.MUTED),
                rx.text(
                    "Lihat per server →",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT_BRIGHT,
                    padding_top="4px",
                ),
                spacing="2",
                align="start",
            ),
            on_click=PowerState.toggle_sort("psu_rekomendasi_w"),
            style=rx.Style(
                {
                    "padding": "18px 20px",
                    "border_radius": Radius.CARD,
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "cursor": "pointer",
                }
            ),
        ),
        # 4. BEBAN TERTINGGI
        rx.box(
            rx.vstack(
                rx.text(
                    "⚠ BEBAN TERTINGGI",
                    font_size="11px",
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.text(
                    PowerState.kpi_max_tdp_display,
                    font_size="28px",
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.text(
                    PowerState.kpi_max_tdp_server,
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                rx.text(
                    "Buka rincian →",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT_BRIGHT,
                    padding_top="4px",
                ),
                spacing="2",
                align="start",
            ),
            on_click=PowerState.open_drawer(PowerState.kpi_max_tdp_id),
            style=rx.Style(
                {
                    "padding": "18px 20px",
                    "border_radius": Radius.CARD,
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "cursor": "pointer",
                }
            ),
        ),
        # 5. KECUKUPAN UPS
        rx.box(
            rx.vstack(
                rx.text(
                    "KECUKUPAN UPS",
                    font_size="11px",
                    font_weight=FontWeight.BOLD,
                    color=Color.MUTED,
                ),
                rx.hstack(
                    rx.text(
                        PowerState.kpi_ups_count_display,
                        font_size="28px",
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.box(
                        rx.text(
                            PowerState.kpi_ups_status_badge,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.SUCCESS_FG,
                        ),
                        padding="2px 10px",
                        border_radius=Radius.FULL,
                        background_color=Color.SUCCESS_BG,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(PowerState.kpi_ups_sub, font_size=FontSize.XS, color=Color.MUTED),
                rx.text(
                    "Lihat UPS →",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT_BRIGHT,
                    padding_top="4px",
                ),
                spacing="2",
                align="start",
            ),
            on_click=rx.redirect("/assets?category=ups"),
            style=rx.Style(
                {
                    "padding": "18px 20px",
                    "border_radius": Radius.CARD,
                    "background_color": Color.SURFACE,
                    "border": f"1.5px dashed {Color.BLUE_BORDER}",
                    "cursor": "pointer",
                }
            ),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(auto-fit, minmax(200px, 1fr))",
                "gap": Space.S4,
            }
        ),
    )


def _middle_analytics_panels() -> rx.Component:
    """2 Panel Artboard 15: Beban TDP per server (8 teratas) & Kecukupan UPS."""
    return rx.box(
        # Panel Kiri: Beban TDP per server
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Beban TDP per server",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.spacer(),
                    rx.box(
                        rx.text("sebagian data", font_size="11px", color=Color.MUTED),
                        padding="2px 10px",
                        border_radius=Radius.FULL,
                        background_color=Color.TABLE_HEADER_BG,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.foreach(
                    PowerState.ranked_servers_display,
                    lambda s: rx.hstack(
                        rx.text(
                            s["nama_aset"],
                            font_size=FontSize.XS,
                            width="185px",
                            flex_shrink="0",
                        ),
                        rx.box(
                            rx.box(
                                width=f"{s['tdp_bar_pct']}%",
                                height="10px",
                                border_radius=Radius.FULL,
                                background_color=rx.cond(
                                    s["beban_level"] == "Tinggi",
                                    Color.AMBER_700,
                                    Color.ACCENT_BRIGHT,
                                ),
                            ),
                            flex="1",
                            height="10px",
                            border_radius=Radius.FULL,
                            background_color=Color.TABLE_HEADER_BG,
                        ),
                        rx.text(
                            s["tdp_display"],
                            font_size=FontSize.XS,
                            font_weight=FontWeight.EXTRABOLD,
                            width="52px",
                            text_align="right",
                        ),
                        width="100%",
                        align="center",
                        spacing="3",
                        on_click=PowerState.open_drawer(s["id_aset"]),
                        style=rx.Style({"cursor": "pointer", "padding": "4px 0"}),
                    ),
                ),
                rx.hstack(
                    rx.el.button(
                        rx.cond(
                            PowerState.show_all_ranked_servers,
                            "Tampilkan 8 teratas",
                            f"+ {PowerState.hidden_ranked_count} server lainnya · Lihat semua",
                        ),
                        type="button",
                        on_click=PowerState.toggle_show_all_ranked,
                        style=rx.Style(
                            {
                                "background": "transparent",
                                "border": "none",
                                "color": Color.ACCENT_BRIGHT,
                                "font_size": FontSize.XS,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                                "padding": "0",
                            }
                        ),
                    ),
                    rx.text(
                        "· TDP adalah batas atas pemakaian, bukan pemakaian aktual.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    spacing="2",
                    padding_top="6px",
                ),
                spacing="3",
                width="100%",
            ),
            padding="20px 22px",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        # Panel Kanan: Kecukupan UPS
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Kecukupan UPS",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.spacer(),
                    rx.cond(
                        PowerState.unfilled_ups_watt_count > 0,
                        rx.box(
                            rx.text(
                                f"{PowerState.unfilled_ups_watt_count} UPS "
                                "belum diisi kapasitas watt",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.WARNING_FG,
                            ),
                            padding="2px 10px",
                            border_radius=Radius.FULL,
                            background_color=Color.WARNING_BG,
                        ),
                        rx.box(
                            rx.text(
                                "Datasheet lengkap",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.SUCCESS_FG,
                            ),
                            padding="2px 10px",
                            border_radius=Radius.FULL,
                            background_color=Color.SUCCESS_BG,
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.foreach(
                    PowerState.ups_items,
                    lambda u: rx.vstack(
                        rx.hstack(
                            rx.text(
                                u["header_label"],
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.spacer(),
                            rx.text(
                                f"{u['utilisasi_int']}%",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            width="100%",
                        ),
                        rx.box(
                            rx.box(
                                width=f"{u['utilisasi_int']}%",
                                height="7px",
                                border_radius=Radius.FULL,
                                background_color=rx.cond(
                                    u["status_variant"] == "danger",
                                    Color.DANGER_FG,
                                    rx.cond(
                                        u["status_variant"] == "warning",
                                        Color.WARNING_BAR,
                                        Color.SUCCESS_FG,
                                    ),
                                ),
                            ),
                            width="100%",
                            height="7px",
                            border_radius=Radius.FULL,
                            background_color=Color.TABLE_HEADER_BG,
                        ),
                        rx.hstack(
                            rx.text(u["sub_text"], font_size="11px", color=Color.MUTED),
                            rx.spacer(),
                            rx.cond(
                                PowerState.inline_ups_edit_id == u["id_aset"],
                                rx.hstack(
                                    rx.el.input(
                                        type="number",
                                        placeholder="Watt...",
                                        value=PowerState.inline_ups_watt_val,
                                        on_change=PowerState.set_inline_ups_watt_val,
                                        style=rx.Style(
                                            {
                                                "width": "80px",
                                                "height": "24px",
                                                "padding": "0 6px",
                                                "font_size": "11px",
                                                "border": f"1px solid {Color.INPUT_BORDER}",
                                                "border_radius": "4px",
                                            }
                                        ),
                                    ),
                                    rx.el.button(
                                        "Simpan",
                                        type="button",
                                        on_click=PowerState.submit_inline_ups_watt(u["id_aset"]),
                                        style=rx.Style(
                                            {
                                                "background": Color.ACCENT_BRIGHT,
                                                "color": Color.WHITE,
                                                "border": "none",
                                                "border_radius": "4px",
                                                "padding": "2px 8px",
                                                "font_size": "11px",
                                                "cursor": "pointer",
                                            }
                                        ),
                                    ),
                                    spacing="1",
                                ),
                                rx.cond(
                                    u["is_kapasitas_manual"],
                                    rx.fragment(),
                                    rx.el.button(
                                        "Isi kapasitas watt",
                                        type="button",
                                        on_click=PowerState.start_inline_ups_watt(
                                            u["id_aset"], ""
                                        ),
                                        style=rx.Style(
                                            {
                                                "background": "transparent",
                                                "border": "none",
                                                "color": Color.ACCENT_BRIGHT,
                                                "font_size": "11px",
                                                "font_weight": FontWeight.BOLD,
                                                "cursor": "pointer",
                                                "padding": "0",
                                            }
                                        ),
                                    ),
                                ),
                            ),
                            width="100%",
                            align="center",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),
                rx.text(
                    "Kapasitas watt UPS dari datasheet (diisi manual di aset UPS). "
                    "UPS yang belum diisi memakai perkiraan VA × 0,6 dan diberi label Perkiraan.",
                    font_size="11px",
                    color=Color.MUTED,
                    padding_top="4px",
                ),
                spacing="2",
                width="100%",
            ),
            padding="20px 22px",
            style=rx.Style(
                {
                    "background_color": Color.SURFACE,
                    "border": f"1.5px dashed {Color.BLUE_BORDER}",
                    "border_radius": Radius.CARD,
                }
            ),
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "1.05fr 0.95fr",
                "gap": Space.S4,
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


def _assumptions_modal() -> rx.Component:
    """Modal Pengaturan Asumsi (Artboard 16 Kiri)."""
    return rx.cond(
        PowerState.asmp_modal_open,
        rx.box(
            rx.box(
                on_click=PowerState.close_assumptions_modal,
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
                                "Pengaturan asumsi",
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            rx.text(
                                "Dipakai di seluruh laporan. Perubahan tercatat di Audit Log.",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.el.button(
                            rx.icon(tag="x", size=16, color=Color.MUTED),
                            type="button",
                            on_click=PowerState.close_assumptions_modal,
                            style=rx.Style(
                                {"background": "transparent", "border": "none", "cursor": "pointer"}
                            ),
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        PowerState.asmp_error != "",
                        rx.text(
                            PowerState.asmp_error,
                            font_size=FontSize.XS,
                            color=Color.DANGER_FG,
                            font_weight=FontWeight.BOLD,
                        ),
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Jam operasional per hari",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=PowerState.asmp_jam_per_hari,
                                on_change=PowerState.set_asmp_jam,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Hari per bulan",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=PowerState.asmp_hari_per_bulan,
                                on_change=PowerState.set_asmp_hari,
                                style=_modal_input_style(),
                            ),
                            rx.text(
                                f"Total {PowerState.asmp_total_jam_bulan} jam",
                                font_size="11px",
                                color=Color.MUTED,
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Faktor beban terhadap TDP (%)",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.input(
                            type="number",
                            value=PowerState.asmp_faktor_beban,
                            on_change=PowerState.set_asmp_faktor_beban,
                            style=_modal_input_style(),
                        ),
                        rx.text(
                            "100% = konservatif (batas atas). "
                            "Isi 60–80% jika sudah ada pengukuran.",
                            font_size="11px",
                            color=Color.MUTED,
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text(
                            "Tarif listrik (Rp/kWh) · opsional",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.input(
                            type="text",
                            placeholder="Kosongkan jika belum ada",
                            value=PowerState.asmp_tarif_kwh,
                            on_change=PowerState.set_asmp_tarif_kwh,
                            style=_modal_input_style(),
                        ),
                        rx.text(
                            "Jika kosong, laporan hanya menampilkan kWh "
                            "dan tidak menampilkan biaya rupiah.",
                            font_size="11px",
                            color=Color.MUTED,
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text(
                            "Faktor daya UPS",
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                        ),
                        rx.el.input(
                            type="text",
                            value=PowerState.asmp_faktor_daya_ups,
                            on_change=PowerState.set_asmp_faktor_daya_ups,
                            style=_modal_input_style(),
                        ),
                        rx.text(
                            "Dipakai hanya jika kapasitas watt UPS belum diisi "
                            "(hasil diberi label Perkiraan).",
                            font_size="11px",
                            color=Color.MUTED,
                        ),
                        width="100%",
                        align="start",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Batas waspada UPS (%)",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=PowerState.asmp_batas_waspada,
                                on_change=PowerState.set_asmp_waspada,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Batas kritis UPS (%)",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.el.input(
                                type="number",
                                value=PowerState.asmp_batas_kritis,
                                on_change=PowerState.set_asmp_kritis,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=PowerState.close_assumptions_modal),
                        rx.el.button(
                            "Simpan asumsi",
                            type="button",
                            on_click=PowerState.save_assumptions,
                            style=rx.Style(
                                {
                                    "height": Size.BUTTON_MD_H,
                                    "padding": "0 18px",
                                    "background_color": Color.ACCENT_BRIGHT,
                                    "color": Color.WHITE,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_weight": FontWeight.BOLD,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        justify="end",
                        spacing="2",
                        width="100%",
                        padding_top="8px",
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
                        "width": "460px",
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
        rx.fragment(),
    )


def _server_rincian_drawer() -> rx.Component:
    """Drawer Rincian Server & Simulasi Tambah Beban (Artboard 16 Kanan)."""
    return rx.cond(
        PowerState.drawer_open,
        rx.box(
            rx.box(
                on_click=PowerState.close_drawer,
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
                                PowerState.active_server["nama_aset"],
                                font_size=FontSize.SUBTITLE,
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            rx.text(
                                PowerState.active_server["sub_label"],
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
                            on_click=PowerState.close_drawer,
                            style=rx.Style(
                                {"background": "transparent", "border": "none", "cursor": "pointer"}
                            ),
                        ),
                        width="100%",
                    ),
                    # 3 Kartu Ringkasan Rincian
                    rx.grid(
                        rx.box(
                            rx.text(
                                "TOTAL TDP",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.active_server["tdp_display"],
                                font_size="18px",
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            padding="12px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        rx.box(
                            rx.text(
                                "PSU MIN / REK.",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.active_server["psu_pair_display"],
                                font_size="18px",
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            padding="12px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        rx.box(
                            rx.text(
                                "ENERGI / BULAN",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.active_server["kwh_display"],
                                font_size="18px",
                                font_weight=FontWeight.EXTRABOLD,
                            ),
                            padding="12px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        columns="3",
                        spacing="3",
                        width="100%",
                    ),
                    # Komposisi Beban
                    rx.vstack(
                        rx.text(
                            "KOMPOSISI BEBAN",
                            font_size="11px",
                            font_weight=FontWeight.BOLD,
                            color=Color.MUTED,
                        ),
                        rx.foreach(
                            PowerState.active_komposisi_list,
                            lambda k: rx.hstack(
                                rx.box(
                                    width="10px",
                                    height="10px",
                                    border_radius="50%",
                                    background_color=k["color"],
                                ),
                                rx.text(k["label"], font_size=FontSize.SM),
                                rx.spacer(),
                                rx.text(
                                    k["watt"],
                                    font_size=FontSize.SM,
                                    font_weight=FontWeight.BOLD,
                                ),
                                width="100%",
                                align="center",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # Cara Hitung PSU
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "CARA HITUNG PSU",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                "PSU Min = Pembulatan ke ukuran standar PSU terdekat ke atas "
                                "dari (Beban Efektif + Margin 75 W, min 250 W). "
                                "PSU Rek = Pembulatan kelipatan 50 W ke atas "
                                "dari (PSU Min + Margin 75 W, min 350 W).",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            rx.cond(
                                PowerState.active_server["psu_inconsistent"],
                                rx.text(
                                    (
                                        "Catatan konsistensi: Data aset mencatat "
                                        f"{PowerState.active_server['psu_pair_display']}, "
                                        "sedangkan rumus standar menghasilkan "
                                        f"{PowerState.active_server['formula_psu_min_w']} / "
                                        f"{PowerState.active_server['formula_psu_rek_w']} W."
                                    ),
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                    color=Color.WARNING_FG,
                                ),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        padding="12px 14px",
                        width="100%",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CONTROL,
                    ),
                    # Simulasi Tambah Beban
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "SIMULASI TAMBAH BEBAN",
                                font_size="11px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.hstack(
                                rx.el.input(
                                    type="number",
                                    value=PowerState.sim_extra_watt,
                                    on_change=PowerState.set_sim_extra_watt,
                                    style=rx.Style(
                                        {
                                            "width": "80px",
                                            "height": "34px",
                                            "padding": "0 10px",
                                            "border": f"1px solid {Color.INPUT_BORDER}",
                                            "border_radius": Radius.CONTROL,
                                        }
                                    ),
                                ),
                                rx.text(
                                    f"W → total {PowerState.sim_result['new_total_w']} · "
                                    f"{PowerState.sim_result['ups_id']} naik dari "
                                    f"{PowerState.sim_result['old_pct']} ke "
                                    f"{PowerState.sim_result['new_pct']}",
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                ),
                                rx.box(
                                    rx.text(
                                        PowerState.sim_result["status"],
                                        font_size="11px",
                                        font_weight=FontWeight.BOLD,
                                        color=Color.SUCCESS_FG,
                                    ),
                                    padding="2px 8px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.SUCCESS_BG,
                                ),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        padding="12px 14px",
                        width="100%",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CONTROL,
                    ),
                    # Terhubung ke UPS
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Terhubung",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                            ),
                            rx.text(
                                f"{PowerState.active_server['ups_id_aset']} · "
                                f"{PowerState.active_server['ups_display']} kapasitas "
                                f"({PowerState.active_server['ups_source_label']})",
                                font_size=FontSize.XS,
                                color=Color.MUTED,
                            ),
                            spacing="0",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.link(
                            rx.text(
                                "Buka aset →",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.BOLD,
                                color=Color.ACCENT_BRIGHT,
                            ),
                            href=f"/assets/{PowerState.active_server['ups_id_aset']}",
                            underline="none",
                        ),
                        padding="12px 14px",
                        width="100%",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CONTROL,
                    ),
                    rx.hstack(
                        secondary_button(
                            "Edit spesifikasi di aset →",
                            on_click=lambda: PowerState.open_edit_modal(
                                PowerState.active_server["id_aset"]
                            ),
                        ),
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
                        "width": "480px",
                        "max_width": "94vw",
                        "max_height": "90vh",
                        "overflow_y": "auto",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _calc_component_row(
    label: str,
    name_var: Any,
    qty_var: Any,
    watt_var: Any,
    slot_key: str,
) -> rx.Component:
    """Baris input komponen dalam kalkulator watt."""
    return rx.hstack(
        rx.vstack(
            rx.text(label, font_size=FontSize.XS, font_weight=FontWeight.BOLD),
            rx.text(name_var, font_size="11px", color=Color.MUTED),
            align="start",
            width="220px",
        ),
        rx.spacer(),
        rx.hstack(
            rx.el.button(
                "-",
                type="button",
                on_click=lambda: PowerState.step_calc_qty(slot_key, -1),
                style=rx.Style(
                    {
                        "width": "28px",
                        "height": "28px",
                        "border-radius": "4px",
                        "border": f"1px solid {Color.BORDER}",
                        "background": Color.SURFACE,
                        "cursor": "pointer",
                        "font_weight": FontWeight.BOLD,
                    }
                ),
            ),
            rx.center(
                rx.text(qty_var, font_size=FontSize.SM, font_weight=FontWeight.BOLD),
                width="32px",
            ),
            rx.el.button(
                "+",
                type="button",
                on_click=lambda: PowerState.step_calc_qty(slot_key, 1),
                style=rx.Style(
                    {
                        "width": "28px",
                        "height": "28px",
                        "border-radius": "4px",
                        "border": f"1px solid {Color.BORDER}",
                        "background": Color.SURFACE,
                        "cursor": "pointer",
                        "font_weight": FontWeight.BOLD,
                    }
                ),
            ),
            spacing="1",
            align="center",
        ),
        rx.text(
            watt_var,
            font_size=FontSize.SM,
            font_weight=FontWeight.EXTRABOLD,
            width="60px",
            text_align="right",
        ),
        padding="8px 12px",
        border=f"1px solid {Color.BORDER}",
        border_radius=Radius.CONTROL,
        width="100%",
        align="center",
    )


def _calculator_view_section() -> rx.Component:
    """Tab Kalkulator Watt Server (Artboard 17)."""
    return rx.vstack(
        # Bar Atas: Mode Awal & Pilihan Server
        rx.hstack(
            rx.hstack(
                rx.text("Mode Awal:", font_size=FontSize.SM, font_weight=FontWeight.BOLD),
                rx.el.button(
                    "Mulai dari Server yang Ada",
                    type="button",
                    on_click=PowerState.set_calc_start_mode("server_ada"),
                    style=rx.Style(
                        {
                            "padding": "6px 14px",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.XS,
                            "font_weight": FontWeight.BOLD,
                            "background_color": rx.cond(
                                PowerState.calc_start_mode == "server_ada",
                                Color.ACCENT_BRIGHT,
                                Color.SURFACE,
                            ),
                            "color": rx.cond(
                                PowerState.calc_start_mode == "server_ada",
                                Color.WHITE,
                                Color.TEXT,
                            ),
                            "border": f"1px solid {Color.BORDER}",
                            "cursor": "pointer",
                        }
                    ),
                ),
                rx.el.button(
                    "Rancang Baru dari Nol",
                    type="button",
                    on_click=PowerState.set_calc_start_mode("rancang_baru"),
                    style=rx.Style(
                        {
                            "padding": "6px 14px",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.XS,
                            "font_weight": FontWeight.BOLD,
                            "background_color": rx.cond(
                                PowerState.calc_start_mode == "rancang_baru",
                                Color.ACCENT_BRIGHT,
                                Color.SURFACE,
                            ),
                            "color": rx.cond(
                                PowerState.calc_start_mode == "rancang_baru",
                                Color.WHITE,
                                Color.TEXT,
                            ),
                            "border": f"1px solid {Color.BORDER}",
                            "cursor": "pointer",
                        }
                    ),
                ),
                spacing="2",
                align="center",
            ),
            rx.cond(
                PowerState.calc_start_mode == "server_ada",
                rx.hstack(
                    rx.select(
                        PowerState.server_select_options,
                        value=PowerState.calc_selected_server_id,
                        on_change=PowerState.set_calc_selected_server_id,
                    ),
                    secondary_button(
                        "Muat Spesifikasi",
                        on_click=PowerState.load_server_into_calculator,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.fragment(),
            ),
            rx.spacer(),
            # Toggle Mode Beban Dasar vs Puncak
            rx.hstack(
                rx.text("Mode Beban:", font_size=FontSize.SM, font_weight=FontWeight.BOLD),
                rx.el.button(
                    rx.cond(
                        PowerState.calc_load_mode == "puncak",
                        "⚡ Beban Puncak (Peak)",
                        "Beban Dasar (TDP)",
                    ),
                    type="button",
                    on_click=PowerState.toggle_calc_load_mode,
                    style=rx.Style(
                        {
                            "padding": "6px 14px",
                            "border_radius": Radius.CONTROL,
                            "font_size": FontSize.XS,
                            "font_weight": FontWeight.BOLD,
                            "background_color": rx.cond(
                                PowerState.calc_load_mode == "puncak",
                                Color.WARNING_BG,
                                Color.INFO_BG,
                            ),
                            "color": rx.cond(
                                PowerState.calc_load_mode == "puncak",
                                Color.WARNING_FG,
                                Color.INFO_FG,
                            ),
                            "border": f"1px solid {Color.BORDER}",
                            "cursor": "pointer",
                        }
                    ),
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            align="center",
            padding="12px 18px",
            background_color=Color.SURFACE,
            border=f"1px solid {Color.BORDER}",
            border_radius=Radius.CARD,
            wrap="wrap",
        ),
        # 2 Kolom: Kiri Komponen, Kanan Ringkasan Hasil
        rx.box(
            # Kolom Kiri: Input Komponen
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Komponen Hardware",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.text(
                        "Sesuaikan jumlah komponen untuk menghitung estimasi kebutuhan daya.",
                        font_size=FontSize.XS,
                        color=Color.MUTED,
                    ),
                    # Slot CPU
                    _calc_component_row(
                        label="Prosesor (CPU)",
                        name_var=PowerState.calc_cpu_name,
                        qty_var=PowerState.calc_cpu_qty,
                        watt_var=PowerState.calc_summary["cpu_w"],
                        slot_key="cpu",
                    ),
                    # Slot GPU
                    _calc_component_row(
                        label="Kartu Grafis (GPU)",
                        name_var=PowerState.calc_gpu_name,
                        qty_var=PowerState.calc_gpu_qty,
                        watt_var=PowerState.calc_summary["gpu_w"],
                        slot_key="gpu",
                    ),
                    # Slot Mobo
                    _calc_component_row(
                        label="Motherboard",
                        name_var=PowerState.calc_mobo_name,
                        qty_var=PowerState.calc_mobo_qty,
                        watt_var=PowerState.calc_summary["mobo_w"],
                        slot_key="mobo",
                    ),
                    # Slot RAM
                    _calc_component_row(
                        label="Memori RAM",
                        name_var=PowerState.calc_ram_name,
                        qty_var=PowerState.calc_ram_qty,
                        watt_var=PowerState.calc_summary["ram_w"],
                        slot_key="ram",
                    ),
                    # Slot SSD SATA
                    _calc_component_row(
                        label="SSD SATA 2,5 inci",
                        name_var=PowerState.calc_ssd_sata_name,
                        qty_var=PowerState.calc_ssd_sata_qty,
                        watt_var=PowerState.calc_summary["sata_w"],
                        slot_key="sata",
                    ),
                    # Slot SSD NVMe
                    _calc_component_row(
                        label="SSD NVMe M.2",
                        name_var=PowerState.calc_nvme_name,
                        qty_var=PowerState.calc_nvme_qty,
                        watt_var=PowerState.calc_summary["nvme_w"],
                        slot_key="nvme",
                    ),
                    # Slot HDD SATA
                    _calc_component_row(
                        label="HDD SATA 3,5 inci",
                        name_var=PowerState.calc_hdd_name,
                        qty_var=PowerState.calc_hdd_qty,
                        watt_var=PowerState.calc_summary["hdd_w"],
                        slot_key="hdd",
                    ),
                    # Slot Kipas
                    _calc_component_row(
                        label="Kipas Casing",
                        name_var=PowerState.calc_fan_name,
                        qty_var=PowerState.calc_fan_qty,
                        watt_var=PowerState.calc_summary["fan_w"],
                        slot_key="fan",
                    ),
                    spacing="3",
                    width="100%",
                ),
                padding="20px 22px",
                background_color=Color.SURFACE,
                border=f"1px solid {Color.BORDER}",
                border_radius=Radius.CARD,
            ),
            # Kolom Kanan: Ringkasan Hasil Kalkulasi
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Hasil Kalkulasi & Rekomendasi",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    # 4 Kartu Hasil Utama
                    rx.grid(
                        rx.box(
                            rx.text(
                                "TOTAL BEBAN EFEKTIF",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.calc_summary["eff_total_display"],
                                font_size="22px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.ACCENT_BRIGHT,
                            ),
                            padding="14px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        rx.box(
                            rx.text(
                                "PSU REKOMENDASI",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.calc_summary["psu_rek_display"],
                                font_size="22px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                f"Min: {PowerState.calc_summary['psu_min_display']}",
                                font_size="11px",
                                color=Color.MUTED,
                            ),
                            padding="14px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        rx.box(
                            rx.text(
                                "ENERGI / BULAN",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.text(
                                PowerState.calc_summary["kwh_display"],
                                font_size="22px",
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.TEXT,
                            ),
                            rx.text(
                                PowerState.calc_summary["biaya_display"],
                                font_size="11px",
                                color=Color.MUTED,
                            ),
                            padding="14px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        rx.box(
                            rx.text(
                                "UTILISASI UPS",
                                font_size="10px",
                                font_weight=FontWeight.BOLD,
                                color=Color.MUTED,
                            ),
                            rx.hstack(
                                rx.text(
                                    PowerState.calc_summary["ups_util_display"],
                                    font_size="22px",
                                    font_weight=FontWeight.EXTRABOLD,
                                    color=Color.TEXT,
                                ),
                                rx.box(
                                    rx.text(
                                        PowerState.calc_summary["ups_status"],
                                        font_size="10px",
                                        font_weight=FontWeight.BOLD,
                                        color=Color.SUCCESS_FG,
                                    ),
                                    padding="2px 8px",
                                    border_radius=Radius.FULL,
                                    background_color=Color.SUCCESS_BG,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            padding="14px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(
                        rx.text(
                            PowerState.calc_summary["min_ups_note"],
                            font_size=FontSize.XS,
                            color=Color.MUTED,
                        ),
                        padding="12px 14px",
                        border=f"1px solid {Color.BORDER}",
                        border_radius=Radius.CONTROL,
                        background_color=Color.TABLE_HEADER_BG,
                        width="100%",
                    ),
                    # Tombol Aksi Skenario
                    rx.hstack(
                        action_primary_button(
                            "Simpan Skenario",
                            on_click=PowerState.save_current_scenario,
                        ),
                        secondary_button(
                            "Buat Draft Aset Server",
                            on_click=PowerState.create_draft_server_from_calc,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="20px 22px",
                background_color=Color.SURFACE,
                border=f"1px solid {Color.BORDER}",
                border_radius=Radius.CARD,
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
        spacing="4",
        width="100%",
    )


def _catalog_and_scenarios_section() -> rx.Component:
    """Tab Katalog Komponen & Bandingkan Skenario (Artboard 18)."""
    return rx.box(
        # Kolom Kiri: Katalog Komponen
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Katalog Komponen Daya",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                    ),
                    rx.spacer(),
                    rx.box(
                        rx.text(
                            "Database Resmi & Estimasi",
                            font_size="11px",
                            color=Color.MUTED,
                        ),
                        padding="2px 10px",
                        border_radius=Radius.FULL,
                        background_color=Color.TABLE_HEADER_BG,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.text(
                    "Database TDP resmi & estimasi komponen untuk kalkulator Rekap Watt.",
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                rx.vstack(
                    rx.foreach(
                        PowerState.catalog_items,
                        lambda c: rx.hstack(
                            rx.vstack(
                                rx.text(
                                    c["nama"],
                                    font_size=FontSize.XS,
                                    font_weight=FontWeight.BOLD,
                                ),
                                rx.text(
                                    f"{c['kategori']} · {c['merek']} ({c['jenis_data']})",
                                    font_size="11px",
                                    color=Color.MUTED,
                                ),
                                align="start",
                                spacing="0",
                            ),
                            rx.spacer(),
                            rx.text(
                                f"{c['tdp_w']} W",
                                font_size=FontSize.XS,
                                font_weight=FontWeight.EXTRABOLD,
                                color=Color.ACCENT_BRIGHT,
                            ),
                            padding="8px 12px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                            width="100%",
                            align="center",
                        ),
                    ),
                    spacing="2",
                    max_height="600px",
                    overflow_y="auto",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            padding="20px 22px",
            background_color=Color.SURFACE,
            border=f"1px solid {Color.BORDER}",
            border_radius=Radius.CARD,
        ),
        # Kolom Kanan: Skenario Perhitungan Tersimpan
        rx.box(
            rx.vstack(
                rx.heading(
                    "Skenario Perhitungan",
                    font_size=FontSize.SUBTITLE,
                    font_weight=FontWeight.EXTRABOLD,
                ),
                rx.text(
                    "Daftar simulasi dan rancangan server yang disimpan untuk perbandingan.",
                    font_size=FontSize.XS,
                    color=Color.MUTED,
                ),
                rx.vstack(
                    rx.foreach(
                        PowerState.scenarios_list,
                        lambda sc: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        sc["nama"],
                                        font_size=FontSize.SM,
                                        font_weight=FontWeight.BOLD,
                                    ),
                                    rx.spacer(),
                                    rx.text(
                                        sc["subtitle"],
                                        font_size=FontSize.XS,
                                        color=Color.ACCENT_BRIGHT,
                                        font_weight=FontWeight.BOLD,
                                    ),
                                    width="100%",
                                    align="center",
                                ),
                                rx.text(
                                    f"Dibuat oleh: {sc['dibuat_oleh']}",
                                    font_size="11px",
                                    color=Color.MUTED,
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            padding="14px 16px",
                            border=f"1px solid {Color.BORDER}",
                            border_radius=Radius.CONTROL,
                            background_color=Color.TABLE_HEADER_BG,
                            width="100%",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            padding="20px 22px",
            background_color=Color.SURFACE,
            border=f"1px solid {Color.BORDER}",
            border_radius=Radius.CARD,
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "1fr 1fr",
                "gap": Space.S4,
            }
        ),
    )


def _estimasi_summary_footer() -> rx.Component:
    """Baris ringkasan di bawah tabel Rekap Watt Server."""
    return rx.hstack(
        rx.hstack(
            rx.text(
                "RINGKASAN:",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
            ),
            rx.text("Total TDP:", font_size=FontSize.SM, color=Color.MUTED),
            rx.text(
                PowerState.kpi_total_tdp_kw_display,
                font_size=FontSize.SM,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.ACCENT_BRIGHT,
            ),
            spacing="2",
        ),
        rx.text("·", color=Color.MUTED),
        rx.hstack(
            rx.text("PSU Min / Rek:", font_size=FontSize.SM, color=Color.MUTED),
            rx.text(
                PowerState.kpi_psu_summary_display,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            spacing="2",
        ),
        rx.text("·", color=Color.MUTED),
        rx.hstack(
            rx.text("Energi / Bulan:", font_size=FontSize.SM, color=Color.MUTED),
            rx.text(
                PowerState.kpi_kwh_month_display,
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.SUCCESS_FG,
            ),
            spacing="2",
        ),
        width="100%",
        align="center",
        wrap="wrap",
        padding="12px 20px",
        style=rx.Style(
            {
                "background_color": Color.TABLE_HEADER_BG,
                "border_top": f"1px solid {Color.BORDER}",
            }
        ),
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
                            placeholder="Contoh: NVIDIA GeForce GT 1030 2GB",
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
                        rx.el.textarea(
                            placeholder="Catatan kebutuhan daya, UPS, atau lokasi server...",
                            value=PowerState.form_catatan,
                            on_change=PowerState.set_form_catatan,
                            style=rx.Style(
                                {
                                    "width": "100%",
                                    "height": "72px",
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
            "label": "Cakupan: Server",
            "value": PowerState.scope_filter,
            "options": PowerState.scope_options,
            "on_change": PowerState.set_scope_filter,
        },
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
        {
            "label": "Semua UPS",
            "value": PowerState.ups_filter,
            "options": PowerState.ups_filter_options,
            "on_change": PowerState.set_ups_filter,
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
            search_placeholder="Cari ID server, CPU, GPU, RAM, penyimpanan, UPS...",
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
    """Halaman utama `/watt-server` dengan Tab Rekap, Kalkulator, dan Katalog Komponen."""
    content = rx.vstack(
        _watt_header(),
        rx.match(
            PowerState.main_section_tab,
            (
                "kalkulator",
                _calculator_view_section(),
            ),
            (
                "katalog",
                _catalog_and_scenarios_section(),
            ),
            rx.vstack(
                _five_watt_kpi_cards(),
                _middle_analytics_panels(),
                _watt_table_card(),
                spacing="4",
                width="100%",
            ),
        ),
        _server_rincian_drawer(),
        _assumptions_modal(),
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
