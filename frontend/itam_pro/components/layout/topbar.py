"""
Komponen Topbar ITAM Pro.
Sticky, latar putih semi-transparan + blur, breadcrumb pill biru muda,
search pill abu (radius 12px) + Ctrl K, tombol notifikasi 42x42, avatar gradasi biru.
"""

import reflex as rx

from itam_pro.states.auth_state import AuthState
from itam_pro.states.nav_state import NavState
from itam_pro.styles import FONT_FAMILY, Color, FontSize, FontWeight, Radius, Size


def _mobile_menu_trigger() -> rx.Component:
    """Tombol pembuka drawer sidebar khusus layar <900px."""
    return rx.el.button(
        rx.icon(tag="menu", size=Size.ICON_LG, color=Color.TEXT, stroke_width=2),
        type="button",
        aria_label="Buka menu navigasi",
        on_click=NavState.toggle_mobile_sidebar,
        style=rx.Style(
            {
                "width": "42px",
                "height": "42px",
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "12px",
                "background_color": Color.SURFACE,
                "display": "none",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "flex_shrink": "0",
                "@media (max-width: 899px)": {
                    "display": "inline-flex",
                },
            }
        ),
    )


def _breadcrumb(group: str | rx.Var[str], page: str | rx.Var[str]) -> rx.Component:
    """Breadcrumb kiri: 'Grup › [Pill Biru Muda Halaman Aktif]'."""
    return rx.hstack(
        _mobile_menu_trigger(),
        rx.hstack(
            rx.text(
                group,
                font_size=FontSize.SM,
                font_weight=FontWeight.MEDIUM,
                color=Color.MUTED,
            ),
            rx.text(
                "›",
                font_size=FontSize.BASE,
                font_weight=FontWeight.REGULAR,
                color=Color.MUTED,
                margin_x="2px",
            ),
            rx.box(
                rx.text(
                    page,
                    font_size=FontSize.SM,
                    font_weight=FontWeight.BOLD,
                    color=Color.ACCENT,
                    line_height="1.2",
                ),
                style=rx.Style(
                    {
                        "padding": "5px 12px",
                        "background_color": Color.BLUE_100,
                        "border_radius": Radius.FULL,
                        "display": "inline-flex",
                        "align_items": "center",
                    }
                ),
            ),
            spacing="2",
            align="center",
        ),
        spacing="3",
        align="center",
    )


def _search_box() -> rx.Component:
    """Kotak pencarian berbentuk pill abu (radius 12px) dengan badge 'Ctrl K'."""
    return rx.hstack(
        rx.icon(
            tag="search",
            size=Size.ICON_SM,
            color=Color.MUTED,
            stroke_width=2,
            flex_shrink="0",
        ),
        rx.el.input(
            type="text",
            placeholder="Cari aset, IP, serial number...",
            value=NavState.global_search_query,
            on_change=NavState.set_global_search_query,
            style=rx.Style(
                {
                    "width": "100%",
                    "height": "100%",
                    "border": "none",
                    "outline": "none",
                    "background": "transparent",
                    "color": Color.TEXT,
                    "font_family": FONT_FAMILY,
                    "font_size": FontSize.SM,
                    "font_weight": FontWeight.REGULAR,
                }
            ),
        ),
        rx.box(
            "Ctrl K",
            style=rx.Style(
                {
                    "padding": "4px 8px",
                    "background_color": Color.SURFACE,
                    "border": f"1px solid {Color.BORDER}",
                    "border_radius": "6px",
                    "font_size": FontSize.GROUP_LABEL,
                    "font_weight": FontWeight.SEMIBOLD,
                    "color": Color.MUTED,
                    "white_space": "nowrap",
                    "line_height": "1",
                    "flex_shrink": "0",
                }
            ),
        ),
        spacing="2",
        align="center",
        style=rx.Style(
            {
                "width": Size.SEARCH_WIDTH,
                "height": "42px",
                "padding": "0 12px 0 14px",
                "background_color": Color.SLATE_100,
                "border": "1px solid transparent",
                "border_radius": "12px",
                "transition": "all 0.15s ease",
                "@media (max-width: 767px)": {
                    "display": "none",
                },
                "&:focus-within": {
                    "background_color": Color.SURFACE,
                    "border_color": Color.ACCENT,
                    "box_shadow": Color.FOCUS_RING,
                },
            }
        ),
    )


def _notification_button() -> rx.Component:
    """Tombol lonceng 42x42 radius 12px dengan indikator titik merah."""
    return rx.el.button(
        rx.box(
            rx.icon(
                tag="bell",
                size=Size.ICON_MD,
                color=Color.TEXT,
                stroke_width=2,
            ),
            rx.box(
                style=rx.Style(
                    {
                        "position": "absolute",
                        "top": "-2px",
                        "right": "-2px",
                        "width": "8px",
                        "height": "8px",
                        "background_color": Color.NOTIFICATION_DOT,
                        "border": f"1.5px solid {Color.SURFACE}",
                        "border_radius": Radius.FULL,
                    }
                ),
            ),
            style=rx.Style(
                {
                    "position": "relative",
                    "display": "inline-flex",
                    "align_items": "center",
                    "justify_content": "center",
                }
            ),
        ),
        type="button",
        aria_label="Notifikasi sistem",
        style=rx.Style(
            {
                "width": "42px",
                "height": "42px",
                "background_color": Color.SURFACE,
                "border": f"1px solid {Color.BORDER}",
                "border_radius": "12px",
                "display": "inline-flex",
                "align_items": "center",
                "justify_content": "center",
                "cursor": "pointer",
                "flex_shrink": "0",
                "transition": "background-color 0.15s ease",
                "&:hover": {"background_color": Color.SURFACE_HOVER},
            }
        ),
    )


def _profile_menu() -> rx.Component:
    """Avatar bulat bergradasi biru + nama + role dari AuthState.current_user."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.el.button(
                rx.hstack(
                    rx.center(
                        rx.text(
                            AuthState.user_initials,
                            font_size=FontSize.SM,
                            font_weight=FontWeight.EXTRABOLD,
                            color=Color.WHITE,
                        ),
                        width=Size.AVATAR_BOX,
                        height=Size.AVATAR_BOX,
                        border_radius=Radius.FULL,
                        flex_shrink="0",
                        style=rx.Style(
                            {
                                "background": Color.GRADIENT_BLUE,
                                "box_shadow": "0 2px 6px rgba(29, 78, 216, 0.25)",
                            }
                        ),
                    ),
                    rx.vstack(
                        rx.text(
                            AuthState.user_display_name,
                            font_size=FontSize.BASE,
                            font_weight=FontWeight.BOLD,
                            color=Color.TEXT,
                            line_height="1.2",
                        ),
                        rx.text(
                            AuthState.user_role_label,
                            font_size=FontSize.XS,
                            font_weight=FontWeight.REGULAR,
                            color=Color.MUTED,
                            line_height="1.2",
                        ),
                        spacing="0",
                        style=rx.Style({"gap": "2px"}),
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                ),
                type="button",
                style=rx.Style(
                    {
                        "background": "transparent",
                        "border": "none",
                        "padding": "4px 6px",
                        "border_radius": "12px",
                        "cursor": "pointer",
                        "display": "inline-flex",
                        "align_items": "center",
                        "transition": "background-color 0.15s ease",
                        "&:hover": {"background_color": Color.SURFACE_HOVER},
                    }
                ),
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.hstack(
                    rx.icon(tag="user", size=Size.ICON_SM, color=Color.TEXT),
                    rx.text(
                        "Pengaturan Akun",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.MEDIUM,
                        color=Color.TEXT,
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=NavState.select_menu(
                    "Admin", "Pengaturan Akun", "/account-settings", True
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.hstack(
                    rx.icon(tag="log-out", size=Size.ICON_SM, color=Color.DANGER_FG),
                    rx.text(
                        "Keluar",
                        font_size=FontSize.SM,
                        font_weight=FontWeight.SEMIBOLD,
                        color=Color.DANGER_FG,
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=AuthState.logout,
            ),
            align="end",
        ),
    )


def topbar(
    breadcrumb: tuple[str | rx.Var[str], str | rx.Var[str]] = ("Overview", "Dashboard"),
) -> rx.Component:
    """Bar navigasi atas sticky dengan efek semi-transparan dan blur."""
    group, page = breadcrumb
    return rx.box(
        _breadcrumb(group, page),
        _search_box(),
        rx.hstack(
            _notification_button(),
            _profile_menu(),
            spacing="3",
            align="center",
        ),
        as_="header",
        style=rx.Style(
            {
                "width": "100%",
                "height": Size.TOPBAR_HEIGHT,
                "background_color": "rgba(255, 255, 255, 0.88)",
                "backdrop_filter": "blur(12px)",
                "-webkit-backdrop-filter": "blur(12px)",
                "border_bottom": f"1px solid {Color.BORDER}",
                "padding": "0 32px",
                "display": "flex",
                "align_items": "center",
                "justify_content": "space-between",
                "position": "sticky",
                "top": "0",
                "z_index": "30",
                "@media (max-width: 899px)": {
                    "padding": "0 20px",
                },
            }
        ),
    )
