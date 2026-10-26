"""
Halaman View Jadwal Maintenance ITAM Pro (Tahap 10).
Melebur jadwal fisik (PC/Printer/Server) dan perangkat lunak (Backup Database)
ke dalam satu ekosistem terpadu menggunakan recurrence engine.
"""
import reflex as rx

from itam_pro.components.layout.base_layout import base_layout
from itam_pro.components.tables.data_table import reusable_data_table
from itam_pro.components.tables.filter_bar import table_filter_bar
from itam_pro.components.ui.stat_card import stat_card
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


def _tandai_selesai_dialog() -> rx.Component:
    """Modal konfirmasi penyelesaian maintenance dan pergeseran siklus."""
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
                    rx.heading(
                        "Tandai Selesai Maintenance",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        MaintenanceState.selesai_plan_title,
                        font_size=FontSize.SM,
                        color=Color.MUTED,
                    ),
                    rx.text(
                        "Tanggal Selesai",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.input(
                        type="date",
                        value=MaintenanceState.selesai_tgl,
                        on_change=MaintenanceState.set_selesai_tgl,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Hasil Pekerjaan",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.select(
                        rx.el.option("Normal", value="Normal"),
                        rx.el.option("Perlu tindak lanjut", value="Perlu tindak lanjut"),
                        rx.el.option("Komponen diganti", value="Komponen diganti"),
                        value=MaintenanceState.selesai_hasil,
                        on_change=MaintenanceState.set_selesai_hasil,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Dikerjakan Oleh (PIC)",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.select(
                        rx.el.option("Ridho", value="Ridho"),
                        rx.el.option("Surya", value="Surya"),
                        value=MaintenanceState.selesai_pic,
                        on_change=MaintenanceState.set_selesai_pic,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Catatan Tambahan",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.textarea(
                        placeholder="Contoh: Baterai diganti unit baru, voltase stabil 13.8V.",
                        value=MaintenanceState.selesai_catatan,
                        on_change=MaintenanceState.set_selesai_catatan,
                        style=rx.Style(
                            {
                                "width": "100%",
                                "min_height": "80px",
                                "padding": "10px 12px",
                                "background_color": Color.SURFACE,
                                "color": Color.TEXT,
                                "border": f"1px solid {Color.INPUT_BORDER}",
                                "border_radius": Radius.CONTROL,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "outline": "none",
                                "box_sizing": "border-box",
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
                                    "flex": "1",
                                    "height": Size.BUTTON_MD_H,
                                    "background-color": Color.SURFACE,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.TEXT,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Simpan & Geser Jadwal",
                            type="button",
                            on_click=MaintenanceState.submit_tandai_selesai,
                            style=rx.Style(
                                {
                                    "flex": "2",
                                    "height": Size.BUTTON_MD_H,
                                    "background-color": Color.ACCENT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WHITE,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        spacing="3",
                        width="100%",
                        margin_top=Space.S3,
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
                        "width": "460px",
                        "max_width": "92vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
                role="dialog",
            ),
        ),
    )


def _buat_jadwal_massal_dialog() -> rx.Component:
    """Modal form pembuatan jadwal maintenance secara massal per kategori aset."""
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
                    rx.heading(
                        "Buat Jadwal Maintenance Massal",
                        font_size=FontSize.SUBTITLE,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                    ),
                    rx.text(
                        "Jadwal serentak akan digenerate untuk semua unit aset pada "
                        "kategori yang dipilih.",
                        font_size=FontSize.SM,
                        color=Color.MUTED,
                    ),
                    rx.text(
                        "Target Kategori",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.select(
                        rx.el.option("PC", value="PC"),
                        rx.el.option("Server", value="Server"),
                        rx.el.option("Monitor", value="Monitor"),
                        rx.el.option("UPS", value="UPS"),
                        rx.el.option("Printer", value="Printer"),
                        rx.el.option("Laptop", value="Laptop"),
                        rx.el.option("Semua Aset", value="Semua"),
                        value=MaintenanceState.massal_kategori,
                        on_change=MaintenanceState.set_massal_kategori,
                        style=_modal_input_style(),
                    ),
                    rx.text(
                        "Nama Kegiatan",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.TEXT,
                    ),
                    rx.el.input(
                        type="text",
                        placeholder="Contoh: Cek suhu & bersihkan debu kipas",
                        value=MaintenanceState.massal_kegiatan,
                        on_change=MaintenanceState.set_massal_kegiatan,
                        style=_modal_input_style(),
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Jenis",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                                color=Color.TEXT,
                            ),
                            rx.el.select(
                                rx.el.option("Pengecekan rutin", value="Pengecekan rutin"),
                                rx.el.option("Backup", value="Backup"),
                                rx.el.option("Ganti baterai", value="Ganti baterai"),
                                rx.el.option("Servis", value="Servis"),
                                value=MaintenanceState.massal_jenis,
                                on_change=MaintenanceState.set_massal_jenis,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Frekuensi",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                                color=Color.TEXT,
                            ),
                            rx.el.select(
                                rx.el.option("Mingguan", value="Mingguan"),
                                rx.el.option("Bulanan", value="Bulanan"),
                                rx.el.option("3 bulan", value="3 bulan"),
                                rx.el.option("6 bulan", value="6 bulan"),
                                rx.el.option("Tahunan", value="Tahunan"),
                                rx.el.option("Sekali", value="Sekali"),
                                value=MaintenanceState.massal_frekuensi,
                                on_change=MaintenanceState.set_massal_frekuensi,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Tanggal Mulai",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                                color=Color.TEXT,
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
                        rx.vstack(
                            rx.text(
                                "PIC",
                                font_size=FontSize.SM,
                                font_weight=FontWeight.SEMIBOLD,
                                color=Color.TEXT,
                            ),
                            rx.el.select(
                                rx.el.option("Ridho", value="Ridho"),
                                rx.el.option("Surya", value="Surya"),
                                value=MaintenanceState.massal_pic,
                                on_change=MaintenanceState.set_massal_pic,
                                style=_modal_input_style(),
                            ),
                            width="50%",
                            align="start",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    rx.hstack(
                        rx.el.button(
                            "Batal",
                            type="button",
                            on_click=MaintenanceState.close_massal,
                            style=rx.Style(
                                {
                                    "flex": "1",
                                    "height": Size.BUTTON_MD_H,
                                    "background-color": Color.SURFACE,
                                    "border": f"1px solid {Color.INPUT_BORDER}",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.TEXT,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        rx.el.button(
                            "Buat Massal",
                            type="button",
                            on_click=MaintenanceState.submit_massal,
                            style=rx.Style(
                                {
                                    "flex": "2",
                                    "height": Size.BUTTON_MD_H,
                                    "background_color": Color.ACCENT,
                                    "border": "none",
                                    "border_radius": Radius.CONTROL,
                                    "font_family": FONT_FAMILY,
                                    "font_size": FontSize.SM,
                                    "font_weight": FontWeight.BOLD,
                                    "color": Color.WHITE,
                                    "cursor": "pointer",
                                }
                            ),
                        ),
                        spacing="3",
                        width="100%",
                        margin_top=Space.S3,
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
                        "max_width": "92vw",
                        "background_color": Color.SURFACE,
                        "border": f"1px solid {Color.BORDER}",
                        "border_radius": Radius.CARD,
                        "box_shadow": Shadow.POPOVER,
                        "padding": "24px",
                        "z_index": "90",
                    }
                ),
                role="dialog",
            ),
        ),
    )


def _kpi_cards() -> rx.Component:
    return rx.grid(
        stat_card(
            "Terlambat",
            MaintenanceState.summary["terlambat"],
            "triangle-alert",
            tone="danger",
            description="perlu segera ditangani",
        ),
        stat_card(
            "Jatuh tempo ≤ 7 hari",
            MaintenanceState.summary["segera"],
            "clock",
            tone="warning",
        ),
        stat_card(
            "Jadwal aktif",
            MaintenanceState.summary["aktif"],
            "calendar",
            description="terpantau",
        ),
        stat_card(
            "Perlu tindak lanjut",
            MaintenanceState.summary["tindak_lanjut"],
            "wrench",
            tone="warning",
            description="dari hasil maintenance",
        ),
        columns="4",
        spacing="4",
        width="100%",
        margin_bottom=Space.SECTION,
    )


def _daftar_tab() -> rx.Component:
    return rx.vstack(
        _kpi_cards(),
        rx.box(
            table_filter_bar(
                search_value=MaintenanceState.search_query,
                on_search_change=MaintenanceState.set_search_query,
                search_placeholder="Cari objek atau kegiatan...",
            ),
            reusable_data_table(
                items=MaintenanceState.plans,
                id_key="id",
                columns=[
                    {"header": "OBJEK", "accessor": "objek_display", "render_type": "bold"},
                    {"header": "KEGIATAN", "accessor": "kegiatan"},
                    {"header": "JENIS", "accessor": "jenis"},
                    {"header": "FREKUENSI", "accessor": "frekuensi"},
                    {"header": "TERAKHIR · HASIL", "accessor": "terakhir_hasil"},
                    {
                        "header": "JADWAL BERIKUTNYA",
                        "accessor": "jadwal_berikutnya",
                        "render_type": "date",
                    },
                    {"header": "PIC", "accessor": "pic"},
                    {
                        "header": "STATUS",
                        "accessor": "status",
                        "render_type": "badge",
                        "badge_variant_key": "status_variant",
                    },
                ],
                on_row_click=MaintenanceState.open_tandai_selesai,
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
    """Komponen Page Utama Modul Jadwal Maintenance."""
    return base_layout(
        rx.vstack(
            rx.hstack(
                app_tabs(
                    items=[
                        {"label": "Daftar", "value": "daftar"},
                        {"label": "Kalender", "value": "kalender"},
                        {"label": "Riwayat", "value": "riwayat"},
                    ],
                    active_value=MaintenanceState.active_tab,
                    on_change=MaintenanceState.set_tab,
                ),
                # Tombol Import CSV dan Massal di sebelah kanan
                rx.hstack(
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="upload", size=15),
                            rx.text("Import CSV"),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=rx.window_alert("Menunggu header asli dari sheet."),
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
                                "white_space": "nowrap",
                            }
                        ),
                    ),
                    rx.el.button(
                        rx.hstack(
                            rx.icon(tag="circle-plus", size=15),
                            rx.text("Buat jadwal massal"),
                            spacing="2",
                            align="center",
                        ),
                        type="button",
                        on_click=MaintenanceState.open_massal,
                        style=rx.Style(
                            {
                                "height": Size.FILTER_CONTROL_H,
                                "padding": "0 16px",
                                "background_color": Color.ACCENT,
                                "border": "none",
                                "border_radius": Radius.CONTROL,
                                "color": Color.WHITE,
                                "font_family": FONT_FAMILY,
                                "font_size": FontSize.SM,
                                "font_weight": FontWeight.BOLD,
                                "cursor": "pointer",
                                "white_space": "nowrap",
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
                _daftar_tab(),
            ),
            _tandai_selesai_dialog(),
            _buat_jadwal_massal_dialog(),
            spacing="5",
            width="100%",
        )
    )
