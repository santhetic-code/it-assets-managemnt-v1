"""
Halaman Overview -> Dashboard (/dashboard).

Dioptimalkan dengan pre-compiled static rx.Style untuk rendering komponen grafik & grid.
"""

import reflex as rx

from itam_pro.components.layout import base_layout
from itam_pro.components.ui import (
    action_primary_button,
    app_badge,
    app_card,
    hero_stat_card,
    metric_progress_bar,
    page_header,
    secondary_button,
    stat_card,
)
from itam_pro.states.auth_state import AuthState
from itam_pro.states.dashboard_state import (
    ActivityItem,
    AttentionItem,
    CategoryAssetItem,
    DashboardState,
    UPSLoadItem,
)
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size, Space

_KPI_GRID_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1fr 1fr 1fr",
        "gap": Space.S4,
        "align_items": "stretch",
        "@media (max-width: 1150px)": {
            "grid_template_columns": "repeat(2, minmax(0, 1fr))",
        },
        "@media (max-width: 599px)": {
            "grid_template_columns": "1fr",
        },
    }
)


_CHARTS_GRID_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "2fr 1fr",
        "gap": Space.S4,
        "@media (max-width: 899px)": {
            "grid_template_columns": "1fr",
        },
    }
)


_BOTTOM_GRID_STYLE = rx.Style(
    {
        "width": "100%",
        "display": "grid",
        "grid_template_columns": "repeat(3, minmax(0, 1fr))",
        "gap": Space.S4,
        "align_items": "stretch",
        "@media (max-width: 899px)": {
            "grid_template_columns": "1fr",
        },
    }
)


_DONUT_OVERLAY_STYLE = rx.Style(
    {
        "position": "absolute",
        "inset": "0",
        "pointer_events": "none",
    }
)


_DONUT_CONTAINER_STYLE = rx.Style(
    {
        "position": "relative",
        "width": "165px",
        "height": "170px",
        "flex_shrink": "0",
        "cursor": "pointer",
    }
)


_CATEGORY_WRAPPER_STYLE = rx.Style(
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
)


def _dashboard_header() -> rx.Component:
    """1) Header: ikon kotak gradien biru 52px + judul + waktu WIB; Export & + Tambah Aset."""
    return page_header(
        icon="box",
        title="Dashboard",
        subtitle=(
            "Ringkasan aset IT, jadwal, dan keamanan — "
            f"diperbarui {DashboardState.last_updated_wib}"
        ),
        actions=[
            secondary_button(
                label="Export Laporan",
                on_click=DashboardState.export_dashboard_report,
            ),
            action_primary_button(
                label="+ Tambah Aset",
                on_click=rx.redirect("/assets"),
            ),
        ],
    )


def _alert_banner() -> rx.Component:
    """Banner ringkas amber di bawah header: jadwal terlambat, login gagal, aset belum tertaut."""
    return rx.cond(
        DashboardState.banner_visible,
        rx.hstack(
            rx.text(
                DashboardState.banner_summary,
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.WARNING_FG,
            ),
            rx.el.button(
                "Tinjau semua →",
                type="button",
                on_click=DashboardState.scroll_to_attention,
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "0",
                        "color": Color.ACCENT,
                        "font_family": FONT_FAMILY,
                        "font_size": FontSize.SM,
                        "font_weight": FontWeight.BOLD,
                        "cursor": "pointer",
                        "white_space": "nowrap",
                    }
                ),
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            spacing="3",
            padding="11px 16px",
            style=rx.Style(
                {
                    "background_color": Color.WARNING_BG,
                    "border": f"1px solid {Color.WARNING_BORDER}",
                    "border_radius": Radius.CONTROL,
                }
            ),
        ),
        rx.fragment(),
    )


def _kpi_row() -> rx.Component:
    """2) Baris KPI: Kartu 1 Hero (donut % dipakai) + 4 kartu KPI putih (5 -> 2 -> 1 kolom)."""
    return rx.box(
        hero_stat_card(
            icon="box",
            label="TOTAL ASET",
            value=DashboardState.kpi_total_assets,
            subtext=DashboardState.kpi_category_breakdown,
            percent=DashboardState.kpi_in_use_pct,
            percent_caption="dipakai",
            link_text="Lihat detail →",
            href="/assets",
            glow_ring=True,
        ),
        stat_card(
            icon="circle-check",
            tone="purple",
            label="SEDANG DIPAKAI",
            value=DashboardState.kpi_in_use,
            subtext=DashboardState.kpi_in_use_note,
            link_text="Lihat detail →",
            href="/assets?status=Digunakan",
        ),
        stat_card(
            icon="clock",
            tone="success",
            label="JADWAL TERLAMBAT",
            value=DashboardState.kpi_overdue_maint_display,
            value_tone=rx.cond(DashboardState.kpi_overdue_maint > 0, "danger", "default"),
            subtext=DashboardState.kpi_overdue_note,
            link_text="Lihat detail →",
            href="/operations/maintenance",
        ),
        stat_card(
            icon="shield",
            tone="warning",
            label="GARANSI ≤ 30 HARI",
            value=DashboardState.kpi_warranty_display,
            value_tone=rx.cond(DashboardState.kpi_warranty_30d > 0, "warning", "default"),
            subtext=DashboardState.kpi_warranty_note,
            link_text="Lihat detail →",
            href="/assets?warranty=expiring",
        ),
        stat_card(
            icon="zap",
            tone="info",
            label="DAYA SERVER (TDP)",
            value=DashboardState.kpi_power_kw_display,
            subtext=DashboardState.kpi_power_kwh_note,
            link_text="Lihat detail →",
            href="/watt-server",
        ),
        style=_KPI_GRID_STYLE,
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
                        width=38,
                        domain=[0, "auto"],
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
        on_action_click=rx.redirect("/finance/purchases"),
    )


def _category_legend_row(item: CategoryAssetItem) -> rx.Component:
    """Baris legenda untuk donut chart Aset per Kategori."""
    return rx.link(
        rx.hstack(
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
            padding_y="4px",
            padding_x="6px",
            border_radius=Radius.SM,
            transition="all 0.15s ease",
            _hover={
                "background_color": Color.SURFACE_HOVER,
                "cursor": "pointer",
            },
        ),
        href=item["href"],
        underline="none",
        text_decoration="none",
        width="100%",
    )


def _assets_by_category_card() -> rx.Component:
    """Kartu donut chart 'Aset per Kategori' beserta angka total di tengah & legenda."""
    return app_card(
        rx.box(
            # Donut Chart dengan label total di tengah
            rx.link(
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
                        style=_DONUT_OVERLAY_STYLE,
                    ),
                    style=_DONUT_CONTAINER_STYLE,
                ),
                href="/assets",
                underline="none",
                text_decoration="none",
            ),
            # Legenda Kategori + Jumlah
            rx.vstack(
                rx.foreach(DashboardState.category_assets, _category_legend_row),
                spacing="3",
                width="100%",
            ),
            style=_CATEGORY_WRAPPER_STYLE,
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
        style=_CHARTS_GRID_STYLE,
    )


def _ups_load_row(item: UPSLoadItem) -> rx.Component:
    """Render satu baris progress bar Beban UPS."""
    return metric_progress_bar(
        label=item["label"],
        percent=item["percent"],
        percent_label=item["percent_label"],
    )


def _ups_loads_card() -> rx.Component:
    """Kolom 1 Baris 3: Kartu 'Beban UPS tertinggi' (3 teratas)."""
    return app_card(
        rx.vstack(
            rx.foreach(DashboardState.ups_loads, _ups_load_row),
            spacing="4",
            width="100%",
        ),
        title="Beban UPS tertinggi",
        action_label="Rekap Watt",
        on_action_click=rx.redirect("/watt-server"),
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
        app_badge(
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
    """Kolom 2 Baris 3: Kartu 'Perlu Perhatian' (jadwal terlambat, garansi, tagihan)."""
    return rx.box(
        app_card(
            rx.cond(
                DashboardState.has_attention_items,
                rx.vstack(
                    rx.foreach(DashboardState.attention_items, _attention_row),
                    spacing="0",
                    width="100%",
                ),
                rx.text(
                    "Semua jadwal, garansi, dan tagihan dalam kondisi aman.",
                    font_size=FontSize.SM,
                    color=Color.MUTED,
                ),
            ),
            title="Perlu Perhatian",
            action_label="Lihat semua",
            on_action_click=rx.redirect("/operations/maintenance"),
        ),
        id="dashboard-attention-section",
        style=rx.Style({"width": "100%", "height": "100%"}),
    )


def _activity_row(item: ActivityItem, index: int) -> rx.Component:
    """Satu baris 'Aktivitas Penting' (tanpa login sukses) + badge waktu peringatan."""
    time_elem = rx.cond(
        item["is_warning"],
        app_badge(label=item["relative_time"], variant="warning"),
        rx.text(
            item["relative_time"],
            font_size=FontSize.FOOTER,
            font_weight=FontWeight.REGULAR,
            color=Color.MUTED,
            white_space="nowrap",
            flex_shrink="0",
            style=rx.Style({"font_variant_numeric": "tabular-nums"}),
        ),
    )
    row_body = rx.hstack(
        rx.vstack(
            rx.text(
                item["title"],
                font_size=FontSize.SM,
                font_weight=FontWeight.SEMIBOLD,
                color=Color.TEXT,
                line_height="1.35",
            ),
            rx.text(
                item["actor"],
                font_size=FontSize.XS,
                color=Color.MUTED,
                line_height="1.25",
            ),
            spacing="0",
            align="start",
        ),
        time_elem,
        width="100%",
        justify="between",
        align="center",
        spacing="3",
        padding_y="10px",
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
    return rx.cond(
        AuthState.is_admin,
        rx.link(row_body, href=item["href"], underline="none", width="100%"),
        row_body,
    )


def _recent_activities_card() -> rx.Component:
    """Kolom 3 Baris 3: Kartu 'Aktivitas Penting' (tanpa login sukses)."""
    return app_card(
        rx.vstack(
            rx.vstack(
                rx.foreach(DashboardState.recent_activities, _activity_row),
                spacing="0",
                width="100%",
            ),
            rx.cond(
                AuthState.is_admin,
                rx.link(
                    "Buka Audit Log →",
                    href="/audit-log",
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT,
                    underline="hover",
                    padding_top="8px",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        title="Aktivitas Penting",
        subtitle="tanpa login sukses",
    )


def _bottom_three_columns_row() -> rx.Component:
    """4) Baris 3: 3 kolom sama lebar (1 kolom di <900px)."""
    return rx.box(
        _ups_loads_card(),
        _attention_card(),
        _recent_activities_card(),
        style=_BOTTOM_GRID_STYLE,
    )


def dashboard_page() -> rx.Component:
    """Halaman utama /dashboard yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _dashboard_header(),
        _alert_banner(),
        _kpi_row(),
        _charts_row(),
        _bottom_three_columns_row(),
        spacing="0",
        style=rx.Style({"gap": Space.S4, "padding_bottom": Space.S8}),
        align="start",
        width="100%",
    )

    return base_layout(
        content=content,
        breadcrumb=("Overview", "Dashboard"),
    )
