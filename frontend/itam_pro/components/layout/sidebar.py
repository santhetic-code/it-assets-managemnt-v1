"""
Komponen Sidebar Navigasi Utama ITAM Pro (248px).
Hanya menyorot satu menu yang cocok secara eksak dengan NavState.active_path.
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
                            "rgba(255, 255, 255, 0.22)",
                            "rgba(255, 255, 255, 0.08)",
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
                    is_active, Color.ACCENT_BRIGHT, "rgba(255, 255, 255, 0.06)"
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
        # Header Brand Logo
        rx.hstack(
            rx.center(
                rx.icon(tag="shield-check", size=20, color=Color.WHITE),
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
                    "Asset Management",
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
        # Daftar Grup Menu
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
                _nav_link_item("Jadwal Maintenance", "/maintenance", "wrench"),
            ),
            _sidebar_group(
                "Finance",
                _nav_link_item("Rekap Pembelian", "/purchases", "shopping-cart"),
                _nav_link_item("Invoice", "/invoices", "file-text"),
            ),
            _sidebar_group(
                "Security",
                _nav_link_item("Credential Manager", "/credentials", "key-round"),
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
        width=Size.SIDEBAR_WIDTH,
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


def app_sidebar() -> rx.Component:
    return sidebar_content()


def sidebar() -> rx.Component:
    return sidebar_content()


__all__ = ["app_sidebar", "sidebar", "sidebar_content"]
