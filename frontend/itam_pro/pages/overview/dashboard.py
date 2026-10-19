"""
Halaman Overview -> Dashboard (/dashboard).
Tahap 3: Kartu KPI, Pembelian per Bulan, Aset per Kategori, Beban UPS,
Perlu Perhatian, dan Aktivitas Terbaru.
"""
import reflex as rx

from itam_pro.components.layout import base_layout
from itam_pro.components.ui import (
    action_primary_button,
    app_card,
    metric_progress_bar,
    secondary_button,
    stat_card,
    status_badge,
)
from itam_pro.states.dashboard_state import (
    ActivityItem,
    AttentionItem,
    CategoryAssetItem,
    DashboardState,
    UPSLoadItem,
)
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space


def _dashboard_header() -> rx.Component:
    """1) Header: Judul, subjudul di kiri; tombol Export Laporan & + Tambah Aset di kanan."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Dashboard",
                font_size=FontSize.TITLE,
                font_weight=FontWeight.EXTRABOLD,
                color=Color.TEXT,
                line_height="1.2",
                letter_spacing="-0.02em",
            ),
            rx.text(
                "Ringkasan aset IT dan kondisi infrastruktur — data contoh",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            spacing="1",
            align="start",
        ),
        rx.hstack(
            secondary_button(
                label="Export Laporan",
                on_click=DashboardState.show_coming_soon("Export Laporan"),
            ),
            action_primary_button(
                label="+ Tambah Aset",
                on_click=DashboardState.show_coming_soon("Form Tambah Aset"),
            ),
            spacing="3",
            align="center",
        ),
        style=rx.Style(
            {
                "width": "100%",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "flex_wrap": "wrap",
                "gap": Space.S4,
            }
        ),
    )


def _kpi_row() -> rx.Component:
    """2) Baris KPI: 5 kolom, gap 16px (2 kolom di <900px, 1 kolom di <560px)."""
    return rx.box(
        rx.foreach(DashboardState.kpi_cards, stat_card),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(5, minmax(0, 1fr))",
                "gap": Space.S4,
                "@media (max-width: 899px)": {
                    "grid_template_columns": "repeat(2, minmax(0, 1fr))",
                },
                "@media (max-width: 559px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )


def _monthly_purchases_card() -> rx.Component:
    """Kartu grafik batang 'Pembelian per Bulan' (rx.recharts bar chart)."""
    return app_card(
        rx.box(
            rx.recharts.responsive_container(
                rx.recharts.bar_chart(
                    rx.recharts.cartesian_grid(
                        stroke_dasharray="3 3",
                        vertical=False,
                        stroke=Color.CHART_GRID,
                    ),
                    rx.recharts.x_axis(
                        data_key="month",
                        axis_line=False,
                        tick_line=False,
                        custom_attrs={"fontSize": "13px", "fill": Color.MUTED},
                    ),
                    rx.recharts.y_axis(
                        axis_line=False,
                        tick_line=False,
                        width=34,
                        domain=[0, 100],
                        custom_attrs={"fontSize": "12px", "fill": Color.MUTED},
                    ),
                    rx.recharts.tooltip(),
                    rx.recharts.bar(
                        data_key="amount",
                        fill=Color.CHART_BAR,
                        radius=[8, 8, 4, 4],
                        max_bar_size=54,
                        label={
                            "position": "top",
                            "fill": Color.TEXT,
                            "fontSize": 13,
                            "fontWeight": 700,
                            "fontFamily": FONT_FAMILY,
                        },
                    ),
                    data=DashboardState.monthly_purchases,
                    margin={"top": 24, "right": 12, "left": 0, "bottom": 4},
                ),
                width="100%",
                height=245,
            ),
            width="100%",
        ),
        title="Pembelian per Bulan",
        subtitle=DashboardState.purchase_subtitle,
        action_label="Rekap Pembelian",
        on_action_click=DashboardState.show_coming_soon("Halaman Rekap Pembelian"),
    )


def _category_legend_row(item: CategoryAssetItem) -> rx.Component:
    """Baris legenda untuk donut chart Aset per Kategori."""
    return rx.hstack(
        rx.hstack(
            rx.box(
                style=rx.Style(
                    {
                        "width": Size.LEGEND_DOT,
                        "height": Size.LEGEND_DOT,
                        "border_radius": Radius.FULL,
                        "background_color": item["fill"],
                        "flex_shrink": "0",
                    }
                ),
            ),
            rx.text(
                item["name"],
                font_size=FontSize.SM,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
            ),
            spacing="2",
            align="center",
        ),
        rx.text(
            item["formatted_value"],
            font_size=FontSize.SM,
            font_weight=FontWeight.BOLD,
            color=Color.TEXT,
        ),
        width="100%",
        justify="between",
        align="center",
    )


def _assets_by_category_card() -> rx.Component:
    """Kartu donut chart 'Aset per Kategori' beserta angka total di tengah & legenda."""
    return app_card(
        rx.box(
            # Donut Chart dengan label total di tengah
            rx.box(
                rx.recharts.responsive_container(
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            data=DashboardState.category_assets,
                            data_key="value",
                            name_key="name",
                            cx="50%",
                            cy="50%",
                            inner_radius=50,
                            outer_radius=74,
                            padding_angle=2,
                            stroke="none",
                        ),
                        rx.recharts.tooltip(),
                    ),
                    width="100%",
                    height=170,
                ),
                # Overlay angka total di tengah lubang donut
                rx.vstack(
                    rx.text(
                        DashboardState.total_assets_formatted,
                        font_size=FontSize.DONUT_TOTAL,
                        font_weight=FontWeight.EXTRABOLD,
                        color=Color.TEXT,
                        line_height="1.1",
                    ),
                    rx.text(
                        "total aset",
                        font_size=FontSize.GROUP_LABEL,
                        font_weight=FontWeight.REGULAR,
                        color=Color.MUTED,
                        line_height="1.1",
                    ),
                    spacing="0",
                    align="center",
                    justify="center",
                    style=rx.Style(
                        {
                            "position": "absolute",
                            "inset": "0",
                            "pointer_events": "none",
                        }
                    ),
                ),
                style=rx.Style(
                    {
                        "position": "relative",
                        "width": "165px",
                        "height": "170px",
                        "flex_shrink": "0",
                    }
                ),
            ),
            # Legenda Kategori + Jumlah
            rx.vstack(
                rx.foreach(DashboardState.category_assets, _category_legend_row),
                spacing="3",
                width="100%",
            ),
            style=rx.Style(
                {
                    "display": "flex",
                    "align_items": "center",
                    "gap": Space.S5,
                    "width": "100%",
                    "margin_top": "auto",
                    "margin_bottom": "auto",
                    "@media (max-width: 479px)": {
                        "flex_direction": "column",
                    },
                }
            ),
        ),
        title="Aset per Kategori",
        action_label="Inventory",
        on_action_click=rx.redirect("/assets"),
    )


def _charts_row() -> rx.Component:
    """3) Baris 2: Grid 2fr 1fr (1 kolom di <900px)."""
    return rx.box(
        _monthly_purchases_card(),
        _assets_by_category_card(),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "2fr 1fr",
                "gap": Space.S4,
                "@media (max-width: 899px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )


def _ups_load_row(item: UPSLoadItem) -> rx.Component:
    """Render satu baris progress bar Beban UPS."""
    return metric_progress_bar(
        label=item["label"],
        percent=item["percent"],
        percent_label=item["percent_label"],
    )


def _ups_loads_card() -> rx.Component:
    """Kolom 1 Baris 3: Kartu 'Beban UPS'."""
    return app_card(
        rx.vstack(
            rx.foreach(DashboardState.ups_loads, _ups_load_row),
            spacing="4",
            width="100%",
        ),
        title="Beban UPS",
        action_label="Rekap UPS",
        on_action_click=DashboardState.show_coming_soon("Halaman Rekap UPS"),
    )


def _attention_row(item: AttentionItem, index: int) -> rx.Component:
    """Render satu baris item 'Perlu Perhatian' dengan badge status."""
    return rx.hstack(
        rx.vstack(
            rx.text(
                item["title"],
                font_size=FontSize.BASE,
                font_weight=FontWeight.BOLD,
                color=Color.TEXT,
                line_height="1.25",
            ),
            rx.text(
                item["description"],
                font_size=FontSize.FOOTER,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                line_height="1.3",
            ),
            spacing="1",
            align="start",
        ),
        status_badge(
            label=item["badge_label"],
            variant=item["badge_variant"],
        ),
        width="100%",
        justify="between",
        align="center",
        padding_y="11px",
        style=rx.Style(
            {
                "border_top": rx.cond(
                    index == 0,
                    "none",
                    f"1px solid {Color.DIVIDER}",
                ),
            }
        ),
    )


def _attention_card() -> rx.Component:
    """Kolom 2 Baris 3: Kartu 'Perlu Perhatian'."""
    return app_card(
        rx.vstack(
            rx.foreach(DashboardState.attention_items, _attention_row),
            spacing="0",
            width="100%",
        ),
        title="Perlu Perhatian",
        action_label="Lihat semua",
        on_action_click=DashboardState.show_coming_soon("Daftar Perlu Perhatian"),
    )


def _activity_row(item: ActivityItem, index: int) -> rx.Component:
    """Render satu baris 'Aktivitas Terbaru' dengan waktu relatif di kanan."""
    return rx.hstack(
        rx.text(
            item["actor_and_action"],
            rx.el.strong(
                item["target"],
                style=rx.Style({"font_weight": FontWeight.BOLD, "color": Color.TEXT}),
            ),
            font_size=FontSize.SM,
            font_weight=FontWeight.REGULAR,
            color=Color.TEXT,
            line_height="1.4",
        ),
        rx.text(
            item["relative_time"],
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            white_space="nowrap",
            flex_shrink="0",
        ),
        width="100%",
        justify="between",
        align="center",
        spacing="3",
        padding_y="11px",
        style=rx.Style(
            {
                "border_top": rx.cond(
                    index == 0,
                    "none",
                    f"1px solid {Color.DIVIDER}",
                ),
            }
        ),
    )


def _recent_activities_card() -> rx.Component:
    """Kolom 3 Baris 3: Kartu 'Aktivitas Terbaru'."""
    return app_card(
        rx.vstack(
            rx.foreach(DashboardState.recent_activities, _activity_row),
            spacing="0",
            width="100%",
        ),
        title="Aktivitas Terbaru",
        action_label="Audit Log",
        on_action_click=DashboardState.show_coming_soon("Halaman Audit Log"),
    )


def _bottom_three_columns_row() -> rx.Component:
    """4) Baris 3: 3 kolom sama lebar (1 kolom di <900px)."""
    return rx.box(
        _ups_loads_card(),
        _attention_card(),
        _recent_activities_card(),
        style=rx.Style(
            {
                "width": "100%",
                "display": "grid",
                "grid_template_columns": "repeat(3, minmax(0, 1fr))",
                "gap": Space.S4,
                "@media (max-width: 899px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )


def dashboard_page() -> rx.Component:
    """Halaman utama /dashboard yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _dashboard_header(),
        _kpi_row(),
        _charts_row(),
        _bottom_three_columns_row(),
        spacing="0",
        style=rx.Style({"gap": Space.S4}),
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Overview", "Dashboard"),
    )
