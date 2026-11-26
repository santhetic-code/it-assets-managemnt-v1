"""Halaman Security -> Audit Log (/audit-log), khusus Administrator (append-only)."""

from typing import Any

import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables import (
    ColumnDef,
    FilterDropdownConfig,
    reusable_data_table,
    table_filter_bar,
    table_pagination,
)
from itam_pro.components.ui.badge import app_badge, connector_chip
from itam_pro.components.ui.button import action_primary_button, secondary_button
from itam_pro.components.ui.stat_card import stat_card
from itam_pro.components.ui.tabs import TabItemConfig, app_tabs
from itam_pro.states.audit_state import AuditState
from itam_pro.states.auth_state import AuthState
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


def _cell_waktu_wib(row: dict[str, Any]) -> rx.Component:
    return rx.text(
        row["waktu_ringkas"],
        title=row["waktu_lengkap"],
        font_size=FontSize.SM,
        font_weight=FontWeight.MEDIUM,
        color=Color.TEXT,
        white_space="nowrap",
        style=rx.Style({"font_variant_numeric": "tabular-nums"}),
    )


def _cell_pelaku(row: dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.text(
            row["nama_pengguna"],
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.TEXT,
            line_height="1.25",
        ),
        rx.text(
            row["actor_sub"],
            font_size=FontSize.XS,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            line_height="1.2",
        ),
        spacing="0",
        align="start",
    )


def _cell_modul(row: dict[str, Any]) -> rx.Component:
    return connector_chip(row["modul"])


def _cell_aksi(row: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        app_badge(label=row["aksi_label"], variant=row["tingkat_variant"]),
        rx.cond(
            row["group_badge"] != "",
            app_badge(label=row["group_badge"], variant="neutral"),
            rx.fragment(),
        ),
        spacing="1",
        align="center",
        wrap="wrap",
    )


def _cell_target(row: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(
            row["target_id"],
            font_size=FontSize.SM,
            font_weight=FontWeight.SEMIBOLD,
            color=Color.TEXT,
        ),
        rx.cond(
            row["target_context"] != "",
            rx.text(
                row["target_context"],
                font_size=FontSize.XS,
                color=Color.MUTED,
            ),
            rx.fragment(),
        ),
        spacing="1",
        align="center",
        wrap="wrap",
    )


AUDIT_COLUMNS: list[ColumnDef] = [
    {
        "key": "waktu_wib",
        "header": "Waktu (WIB)",
        "width": "130px",
        "min_width": "120px",
        "accessor": _cell_waktu_wib,
    },
    {
        "key": "nama_pengguna",
        "header": "Pelaku",
        "width": "195px",
        "min_width": "170px",
        "accessor": _cell_pelaku,
    },
    {
        "key": "modul",
        "header": "Modul",
        "width": "115px",
        "min_width": "105px",
        "accessor": _cell_modul,
    },
    {
        "key": "aksi_label",
        "header": "Aksi",
        "width": "165px",
        "min_width": "145px",
        "accessor": _cell_aksi,
    },
    {
        "key": "target_id",
        "header": "Target",
        "width": "185px",
        "min_width": "150px",
        "accessor": _cell_target,
    },
]


def _warning_banner() -> rx.Component:
    return rx.cond(
        AuditState.warning_banner_visible,
        rx.box(
            rx.hstack(
                rx.icon(
                    tag="triangle-alert",
                    size=18,
                    color=Color.DANGER_FG,
                    flex_shrink="0",
                ),
                rx.text(
                    AuditState.warning_banner_summary,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=Color.DANGER_FG,
                ),
                spacing="3",
                align="center",
            ),
            rx.el.button(
                "Tampilkan",
                type="button",
                on_click=AuditState.show_warnings_from_banner,
                style=rx.Style(
                    {
                        "min_height": "44px",
                        "padding": "0 16px",
                        "background_color": Color.SURFACE,
                        "color": Color.DANGER_FG,
                        "border": f"1px solid {Color.DANGER_BORDER}",
                        "border_radius": Radius.CONTROL,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
                _hover=rx.Style({"background_color": Color.DANGER_BG}),
            ),
            role="alert",
            style=rx.Style(
                {
                    "width": "100%",
                    "padding": "10px 16px",
                    "background_color": Color.RED_50,
                    "border": f"1px solid {Color.DANGER_BORDER}",
                    "border_radius": Radius.CONTROL,
                    "display": "flex",
                    "align_items": "center",
                    "justify_content": "space-between",
                    "flex_wrap": "wrap",
                    "gap": Space.S3,
                }
            ),
        ),
        rx.fragment(),
    )


def _extra_filter_controls() -> rx.Component:
    date_input_style = rx.Style(
        {
            "height": Size.FILTER_CONTROL_H,
            "min_height": "40px",
            "padding": "0 10px",
            "background_color": Color.SURFACE,
            "color": Color.TEXT,
            "border": f"1px solid {Color.INPUT_BORDER}",
            "border_radius": Radius.CONTROL,
            "font_family": FONT_FAMILY,
            "font_size": FontSize.SM,
        }
    )
    return rx.hstack(
        rx.cond(
            AuditState.is_custom_date_range,
            rx.hstack(
                rx.el.input(
                    type="date",
                    aria_label="Tanggal mulai",
                    value=AuditState.date_from,
                    on_change=AuditState.set_date_from,
                    style=date_input_style,
                ),
                rx.text("–", color=Color.MUTED, font_size=FontSize.SM),
                rx.el.input(
                    type="date",
                    aria_label="Tanggal selesai",
                    value=AuditState.date_to,
                    on_change=AuditState.set_date_to,
                    style=date_input_style,
                ),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.hstack(
                rx.cond(
                    AuditState.hide_login_success,
                    rx.text("✓", font_weight=FontWeight.BOLD, color=Color.ACCENT),
                    rx.fragment(),
                ),
                rx.text(
                    "Sembunyikan login berhasil",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.SEMIBOLD,
                    color=rx.cond(AuditState.hide_login_success, Color.ACCENT, Color.TEXT),
                    white_space="nowrap",
                ),
                spacing="1",
                align="center",
            ),
            type="button",
            on_click=AuditState.toggle_hide_login_success,
            style=rx.Style(
                {
                    "height": Size.FILTER_CONTROL_H,
                    "padding": "0 14px",
                    "background_color": rx.cond(
                        AuditState.hide_login_success, Color.INFO_BG, Color.SURFACE
                    ),
                    "border": rx.cond(
                        AuditState.hide_login_success,
                        f"1px solid {Color.BLUE_BORDER}",
                        f"1px solid {Color.INPUT_BORDER}",
                    ),
                    "border_radius": Radius.CONTROL,
                    "font_family": FONT_FAMILY,
                    "cursor": "pointer",
                    "display": "inline-flex",
                    "align_items": "center",
                }
            ),
        ),
        spacing="2",
        align="center",
        wrap="wrap",
    )


_TWO_COL_LAYOUT_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "minmax(0, 1fr) 360px",
        "gap": Space.S4,
        "align_items": "start",
        "@media (max-width: 899px)": {
            "grid_template_columns": "1fr",
        },
    }
)


def _audit_kpi_row() -> rx.Component:
    """4 Kartu KPI Audit Log (kartu pertama Color.BRAND)."""
    return rx.grid(
        stat_card(
            "KEJADIAN (30 HARI)",
            AuditState.kpi_events_30d,
            note=AuditState.kpi_events_note,
            primary=True,
        ),
        stat_card(
            "PERINGATAN",
            AuditState.kpi_warnings_count,
            value_tone="danger",
            note="login gagal terdeteksi",
        ),
        stat_card(
            "PERUBAHAN DATA",
            AuditState.kpi_changes_count,
            note="kejadian penting",
        ),
        stat_card(
            "PASSWORD DIBUKA HARI INI",
            AuditState.kpi_reveals_today,
            note="akses Credential Manager",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="4",
        width="100%",
    )


def _detail_meta_row(label: str, value: Any, *, mono: bool = False) -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size=FontSize.SM, color=Color.MUTED),
        rx.text(
            value,
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.TEXT,
            text_align="right",
            font_family="monospace" if mono else FONT_FAMILY,
        ),
        width="100%",
        justify="between",
        align="center",
        padding_y="8px",
        style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
    )


def _audit_detail_panel() -> rx.Component:
    """Panel kanan Detail Kejadian pada layout dua kolom (hanya-baca)."""
    diff_block = rx.cond(
        AuditState.has_selected_changes,
        rx.vstack(
            rx.text(
                "Perubahan data",
                font_size=FontSize.SM,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
            ),
            rx.vstack(
                rx.foreach(
                    AuditState.selected_changes,
                    lambda ch: rx.vstack(
                        rx.text(ch["field"], font_size=FontSize.XS, color=Color.MUTED),
                        rx.hstack(
                            rx.text(
                                ch["before"],
                                font_size=FontSize.SM,
                                color=Color.DANGER_FG,
                                style=rx.Style({"text_decoration": "line-through"}),
                            ),
                            rx.text("→", font_size=FontSize.SM, color=Color.MUTED),
                            rx.text(
                                ch["after"],
                                font_size=FontSize.SM,
                                font_weight=FontWeight.BOLD,
                                color=Color.SUCCESS_FG,
                            ),
                            spacing="2",
                            align="center",
                            wrap="wrap",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
                padding="12px",
                style=rx.Style(
                    {
                        "background_color": Color.TABLE_HEADER_BG,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CONTROL,
                    }
                ),
            ),
            rx.text(
                "Nilai rahasia kredensial disanitasi dan tidak pernah ditampilkan.",
                font_size=FontSize.XS,
                color=Color.MUTED,
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )

    grouped_block = rx.cond(
        AuditState.is_selected_grouped,
        rx.vstack(
            rx.text(
                "Waktu kejadian dalam grup (1 menit)",
                font_size=FontSize.XS,
                font_weight=FontWeight.BOLD,
                color=Color.MUTED,
            ),
            rx.vstack(
                rx.foreach(
                    AuditState.selected_grouped_timestamps,
                    lambda ts: rx.hstack(
                        rx.text(
                            ts["kode_audit"],
                            font_size=FontSize.XS,
                            font_weight=FontWeight.BOLD,
                            color=Color.ACCENT,
                        ),
                        rx.text(ts["waktu_wib"], font_size=FontSize.XS, color=Color.TEXT),
                        width="100%",
                        justify="between",
                        padding="6px 10px",
                        style=rx.Style({"border_bottom": f"1px solid {Color.DIVIDER}"}),
                    ),
                ),
                spacing="0",
                width="100%",
                style=rx.Style(
                    {
                        "background_color": Color.TABLE_HEADER_BG,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CONTROL,
                    }
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )

    selected_body = rx.vstack(
        rx.hstack(
            app_badge(
                label=AuditState.selected_tingkat,
                variant=AuditState.selected_tingkat_variant,
            ),
            connector_chip(AuditState.selected_modul),
            spacing="2",
            align="center",
        ),
        rx.vstack(
            rx.heading(
                AuditState.selected_heading_title,
                font_size=FontSize.SUBTITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.3",
            ),
            rx.text(
                AuditState.selected_detail,
                font_size=FontSize.SM,
                color=Color.MUTED,
                line_height="1.45",
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        rx.vstack(
            _detail_meta_row("Waktu", AuditState.selected_waktu_lengkap),
            _detail_meta_row("Pelaku", AuditState.selected_actor_display),
            _detail_meta_row("Alamat IP", AuditState.selected_ip_address, mono=True),
            _detail_meta_row("Sesi", AuditState.selected_session_id, mono=True),
            spacing="0",
            width="100%",
        ),
        diff_block,
        grouped_block,
        rx.hstack(
            rx.cond(
                AuthState.is_admin & AuditState.has_selected_target_link,
                rx.link(
                    secondary_button(AuditState.selected_target_link_label),
                    href=AuditState.selected_target_url,
                    underline="none",
                ),
                rx.fragment(),
            ),
            secondary_button(
                "Salin ID kejadian",
                on_click=AuditState.copy_selected_event_id,
            ),
            spacing="2",
            width="100%",
            wrap="wrap",
            padding_top="4px",
        ),
        rx.text("Log hanya-baca", font_size=FontSize.XS, color=Color.MUTED),
        spacing="4",
        align="start",
        width="100%",
    )

    empty_panel = rx.vstack(
        rx.text(
            "Klik salah satu baris kejadian di tabel untuk melihat waktu, pelaku, IP, "
            "ID sesi, dan rincian perubahan data.",
            font_size=FontSize.SM,
            color=Color.MUTED,
            line_height="1.5",
        ),
        rx.text("Log hanya-baca", font_size=FontSize.XS, color=Color.MUTED),
        spacing="3",
        align="start",
        width="100%",
        padding_y="12px",
    )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Detail Kejadian",
                    font_size=FontSize.SUBTITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                ),
                rx.cond(
                    AuditState.drawer_open,
                    rx.hstack(
                        rx.text(
                            AuditState.selected_kode_audit,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.SEMIBOLD,
                            color=Color.MUTED,
                        ),
                        rx.el.button(
                            "×",
                            id="audit-detail-close-btn",
                            type="button",
                            aria_label="Tutup panel detail kejadian",
                            on_click=AuditState.close_detail_drawer,
                            style=rx.Style(
                                {
                                    "background": "transparent",
                                    "border": "none",
                                    "font_size": FontSize.SUBTITLE,
                                    "color": Color.MUTED,
                                    "cursor": "pointer",
                                    "padding": "0 4px",
                                }
                            ),
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            rx.cond(AuditState.drawer_open, selected_body, empty_panel),
            rx.script(
                "if (!window.__itamAuditEscBound) { window.__itamAuditEscBound = true; "
                "window.addEventListener('keydown', (e) => { if (e.key === 'Escape') { "
                "const btn = document.getElementById('audit-detail-close-btn'); "
                "if (btn) btn.click(); } }); }"
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        aria_label="Detail kejadian Audit Log",
        style=rx.Style(
            {
                "width": "100%",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": Radius.CARD,
                "padding": Space.S5,
                "position": "sticky",
                "top": "84px",
            }
        ),
    )


def _export_csv_modal() -> rx.Component:
    """Modal pilihan rentang tanggal sebelum Export CSV."""
    input_style = rx.Style(
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
        }
    )
    return rx.cond(
        AuditState.export_modal_open,
        rx.box(
            rx.box(
                on_click=AuditState.close_export_modal,
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
                        "Export Audit Log (CSV)",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Pilih rentang tanggal data yang akan diekspor. Seluruh entri mentah "
                        "pada rentang tersebut akan disertakan dan aktivitas ekspor dicatat.",
                        font_size=FontSize.SM,
                        color=Color.MUTED,
                    ),
                    rx.el.select(
                        rx.el.option("Sesuai filter aktif saat ini", value="active"),
                        rx.el.option("Hari ini", value="hari_ini"),
                        rx.el.option("7 hari terakhir", value="7_hari"),
                        rx.el.option("30 hari terakhir", value="30_hari"),
                        rx.el.option("Pilih rentang tanggal kustom", value="rentang"),
                        value=AuditState.export_range_mode,
                        on_change=AuditState.set_export_range_mode,
                        style=input_style,
                    ),
                    rx.cond(
                        AuditState.is_export_custom_range,
                        rx.grid(
                            rx.vstack(
                                rx.text(
                                    "Dari Tanggal", font_size=FontSize.XS, color=Color.MUTED
                                ),
                                rx.el.input(
                                    type="date",
                                    value=AuditState.export_date_from,
                                    on_change=AuditState.set_export_date_from,
                                    style=input_style,
                                ),
                                align="start",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Sampai Tanggal", font_size=FontSize.XS, color=Color.MUTED
                                ),
                                rx.el.input(
                                    type="date",
                                    value=AuditState.export_date_to,
                                    on_change=AuditState.set_export_date_to,
                                    style=input_style,
                                ),
                                align="start",
                                width="100%",
                            ),
                            columns="2",
                            spacing="3",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.hstack(
                        secondary_button("Batal", on_click=AuditState.close_export_modal),
                        action_primary_button(
                            "Unduh CSV", on_click=AuditState.confirm_export_csv
                        ),
                        width="100%",
                        justify="end",
                        spacing="2",
                        padding_top="8px",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "92%",
                        "max_width": "460px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": Space.S6,
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def _integrity_modal() -> rx.Component:
    """Modal Verifikasi Integritas (UI-only; logika hash-chain pada fase backend berikutnya)."""
    return rx.cond(
        AuditState.integrity_modal_open,
        rx.box(
            rx.box(
                on_click=AuditState.close_integrity_modal,
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
                        "Verifikasi Integritas Audit Log",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                app_badge(label="Append-only aktif", variant="success"),
                                app_badge(
                                    label="Hash-chain: Fase berikutnya", variant="warning"
                                ),
                                spacing="2",
                            ),
                            rx.text(
                                "Mode pratinjau UI: seluruh catatan bersifat hanya-baca tanpa "
                                "opsi ubah/hapus. Verifikasi rantai hash (hash-chain) "
                                "kriptografis akan diaktifkan setelah endpoint backend tersedia.",
                                font_size=FontSize.SM,
                                color=Color.TEXT,
                                line_height="1.5",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        padding="12px 14px",
                        width="100%",
                        style=rx.Style(
                            {
                                "background_color": Color.INFO_BG,
                                "border": f"1px solid {Color.BLUE_BORDER}",
                                "border_radius": Radius.CONTROL,
                            }
                        ),
                    ),
                    rx.hstack(
                        action_primary_button(
                            "Tutup", on_click=AuditState.close_integrity_modal
                        ),
                        width="100%",
                        justify="end",
                    ),
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                role="dialog",
                aria_modal="true",
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "50%",
                        "left": "50%",
                        "transform": "translate(-50%, -50%)",
                        "width": "92%",
                        "max_width": "460px",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": Space.S6,
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def audit_view_page() -> rx.Component:
    severity_tabs: list[TabItemConfig] = [
        {"key": "Semua", "label": "Semua", "count": AuditState.tab_counts["Semua"]},
        {"key": "Peringatan", "label": "Peringatan", "count": AuditState.tab_counts["Peringatan"]},
        {"key": "Penting", "label": "Penting", "count": AuditState.tab_counts["Penting"]},
        {"key": "Info", "label": "Info", "count": AuditState.tab_counts["Info"]},
    ]

    dropdowns: list[FilterDropdownConfig] = [
        {
            "label": "Semua modul",
            "value": AuditState.module_filter,
            "options": AuditState.module_options,
            "on_change": AuditState.set_module_filter,
        },
        {
            "label": "Semua pelaku",
            "value": AuditState.actor_filter,
            "options": AuditState.actor_options,
            "on_change": AuditState.set_actor_filter,
        },
        {
            "label": "Semua periode",
            "value": AuditState.period_filter,
            "options": AuditState.period_options,
            "on_change": AuditState.set_period_filter,
        },
    ]

    header_row = rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Audit Log",
                    font_size=FontSize.TITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.TEXT,
                    line_height="1.2",
                ),
                app_badge(label="Hanya Administrator", variant="neutral"),
                spacing="3",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Rekam jejak perubahan data, autentikasi, dan akses kredensial. "
                "Hanya-baca: tidak dapat diubah atau dihapus.",
                font_size=FontSize.BASE,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.hstack(
            secondary_button("Export CSV", on_click=AuditState.open_export_modal),
            action_primary_button(
                "Verifikasi Integritas",
                on_click=AuditState.open_integrity_modal,
            ),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "flex-start",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
            }
        ),
    )

    table_card = rx.box(
        app_tabs(
            tabs=severity_tabs,
            active_tab=AuditState.severity_tab,
            on_change=AuditState.set_severity_tab,
        ),
        table_filter_bar(
            search_value=AuditState.search_query,
            on_search_change=AuditState.set_search_query,
            search_placeholder="Cari pelaku, aksi, target...",
            dropdowns=dropdowns,
            extra_controls=_extra_filter_controls(),
            on_reset=AuditState.reset_filters,
            result_count_text=AuditState.result_count_label,
        ),
        reusable_data_table(
            columns=AUDIT_COLUMNS,
            rows=AuditState.logs,
            id_key="kode_audit",
            active_row_id=AuditState.active_row_id,
            is_loading=AuditState.is_loading,
            on_row_click=AuditState.open_detail_drawer,
            danger_row_key="tingkat",
            danger_row_value="Peringatan",
            show_action_header=False,
            empty_message="Tidak ada kejadian audit yang cocok",
            on_empty_action=AuditState.reset_filters,
        ),
        table_pagination(
            summary_text=AuditState.pagination_summary,
            current_page=AuditState.page,
            current_page_str=AuditState.current_page_str,
            total_pages=AuditState.total_pages,
            page_tokens=AuditState.page_tokens,
            on_prev=AuditState.prev_page,
            on_next=AuditState.next_page,
            on_page_select=AuditState.select_page,
        ),
        rx.box(
            rx.text(
                "Waktu ditampilkan dalam WIB (disimpan UTC). Data mentah tetap tersimpan "
                "satu per satu.",
                font_size=FontSize.XS,
                color=Color.MUTED,
            ),
            padding="10px 20px 14px 20px",
            style=rx.Style({"border_top": f"1px solid {Color.DIVIDER}"}),
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

    content = rx.vstack(
        header_row,
        _audit_kpi_row(),
        _warning_banner(),
        rx.box(
            table_card,
            _audit_detail_panel(),
            style=_TWO_COL_LAYOUT_STYLE,
        ),
        _export_csv_modal(),
        _integrity_modal(),
        spacing="4",
        width="100%",
    )
    return base_layout(content=content, breadcrumb=("Security", "Audit Log"))


__all__ = ["audit_view_page"]
