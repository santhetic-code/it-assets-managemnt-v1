"""
Komponen Sidebar Navigasi Utama ITAM Pro (248px).
Menggunakan ikon cube ('box') dan subjudul 'IT Assets Management' selaras halaman Login.
"""
from typing import Any

import reflex as rx

from itam_pro.services.category_config import get_pinned_categories
from itam_pro.states.asset_state import AssetState
from itam_pro.states.nav_state import NavState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def _nav_link_item(
    label: str,
    href: str,
    icon_tag: str,
    badge_count: Any | None = None,
) -> rx.Component:
    """Render satu baris menu sidebar dengan pencocokan rute eksak."""
    is_active = NavState.active_path == href

    return rx.el.a(
        rx.hstack(
            rx.hstack(
                rx.icon(
                    tag=icon_tag,
                    size=Size.ICON_MD,
                    color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                ),
                rx.text(
                    label,
                    font_size=FontSize.BASE,
                    font_weight=rx.cond(is_active, FontWeight.BOLD, FontWeight.MEDIUM),
                    color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_TEXT),
                ),
                spacing="3",
                align="center",
            ),
            rx.text(
                badge_count,
                font_size=FontSize.GROUP_LABEL,
                font_weight=FontWeight.BOLD,
                color=rx.cond(is_active, Color.WHITE, Color.SIDEBAR_MUTED),
                style=rx.Style(
                    {
                        "padding": "2px 8px",
                        "border_radius": Radius.FULL,
                        "background_color": rx.cond(
                            is_active,
                            Color.SIDEBAR_BADGE_ACTIVE_BG,
                            Color.SIDEBAR_BADGE_BG,
                        ),
                    }
                ),
            )
            if badge_count is not None
            else rx.fragment(),
            width="100%",
            justify="between",
            align="center",
        ),
        href=href,
        on_click=NavState.close_mobile_drawer,
        style=rx.Style(
            {
                "width": "100%",
                "padding": "10px 12px",
                "border_radius": Radius.CONTROL,
                "text_decoration": "none",
                "background_color": rx.cond(is_active, Color.ACCENT_BRIGHT, "transparent"),
                "display": "block",
                "font_family": FONT_FAMILY,
                "transition": "background-color 0.15s ease",
            }
        ),
        _hover=rx.Style(
            {
                "background_color": rx.cond(
                    is_active, Color.ACCENT_BRIGHT, Color.SIDEBAR_HOVER
                ),
            }
        ),
    )


def _sidebar_group(title: str, *items: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(
            title.upper(),
            font_size=FontSize.GROUP_LABEL,
            font_weight=FontWeight.BOLD,
            color=Color.SIDEBAR_MUTED,
            letter_spacing="0.08em",
            padding_x="12px",
        ),
        rx.vstack(*items, spacing="1", width="100%"),
        spacing="2",
        align="start",
        width="100%",
    )


def sidebar_content() -> rx.Component:
    """Isi navigasi sidebar 7 grup menu."""
    icon_map = {
        "pc": "monitor-speaker",
        "monitor": "monitor",
        "ups": "battery-charging",
    }
    pinned_categories = get_pinned_categories()

    return rx.vstack(
        # Header Brand Logo (Ikon cube 'box' + subjudul 'IT Assets Management')
        rx.hstack(
            rx.center(
                rx.icon(tag="box", size=20, color=Color.WHITE),
                width="36px",
                height="36px",
                background_color=Color.ACCENT_BRIGHT,
                border_radius=Radius.LOGO_BOX,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    "ITAM Pro",
                    font_size=FontSize.SUBTITLE,
                    font_weight=FontWeight.EXTRABOLD,
                    color=Color.WHITE,
                    line_height="1.1",
                ),
                rx.text(
                    "IT Assets Management",
                    font_size=FontSize.XS,
                    font_weight=FontWeight.MEDIUM,
                    color=Color.SIDEBAR_MUTED,
                    line_height="1.1",
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
            padding="20px 16px 12px 16px",
        ),
        # Daftar 7 Grup Menu
        rx.vstack(
            _sidebar_group(
                "Overview",
                _nav_link_item("Dashboard", "/dashboard", "layout-dashboard"),
            ),
            _sidebar_group(
                "Inventory",
                _nav_link_item(
                    "Semua Aset",
                    "/assets",
                    "boxes",
                    badge_count=AssetState.sidebar_counts["all"],
                ),
                *[
                    _nav_link_item(
                        cfg["name"],
                        f"/assets/c/{cfg['slug']}",
                        icon_map.get(cfg["slug"], "box"),
                        badge_count=AssetState.sidebar_counts[cfg["slug"]],
                    )
                    for cfg in pinned_categories
                ],
            ),
            _sidebar_group(
                "Infrastructure",
                _nav_link_item("IP & Server (VM)", "/infrastructure/ip", "network"),
                _nav_link_item("Rekap Watt Server", "/watt-server", "zap"),
            ),
            _sidebar_group(
                "Operations",
                _nav_link_item("Jadwal Maintenance", "/operations/maintenance", "wrench"),
            ),
            _sidebar_group(
                "Finance",
                _nav_link_item("Pembelian & Invoice", "/finance/purchases", "shopping-cart"),
            ),
            _sidebar_group(
                "Security",
                _nav_link_item("Credential Manager", "/security/credentials", "key-round"),
                _nav_link_item("Audit Log", "/audit-log", "scroll-text"),
            ),
            _sidebar_group(
                "Admin",
                _nav_link_item("Pengaturan Akun", "/account-settings", "settings"),
            ),
            spacing="5",
            width="100%",
            padding="12px",
            style=rx.Style({"overflow_y": "auto", "flex": "1"}),
        ),
        spacing="0",
        width=Size.SIDEBAR_W,
        height="100vh",
        style=rx.Style(
            {
                "background_color": Color.SIDEBAR,
                "position": "sticky",
                "top": "0",
                "left": "0",
                "flex_shrink": "0",
            }
        ),
    )


def sidebar() -> rx.Component:
    """Komponen sidebar desktop utama (dipanggil oleh base_layout.py)."""
    return sidebar_content()


def app_sidebar() -> rx.Component:
    """Alias kompatibilitas untuk sidebar."""
    return sidebar_content()


def mobile_sidebar_drawer() -> rx.Component:
    """Drawer navigasi sidebar untuk layar mobile (<900px)."""
    return rx.cond(
        NavState.mobile_drawer_open,
        rx.box(
            rx.box(
                on_click=NavState.close_mobile_drawer,
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
                sidebar_content(),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "0",
                        "left": "0",
                        "bottom": "0",
                        "width": Size.SIDEBAR_W,
                        "z_index": "90",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


__all__ = [
    "app_sidebar",
    "mobile_sidebar_drawer",
    "sidebar",
    "sidebar_content",
]
