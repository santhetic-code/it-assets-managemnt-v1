"""
Base Layout Wrapper ITAM Pro.
Grid 248px (Sidebar) + 1fr (Topbar & Konten), latar Color.BG, padding konten 28px 32px.
"""
import reflex as rx

from itam_pro.states.nav_state import NavState
from itam_pro.styles import Color, Shadow, Size

from .sidebar import sidebar
from .topbar import topbar


def _mobile_sidebar_drawer() -> rx.Component:
    """Drawer overlay untuk menampilkan sidebar pada layar <900px."""
    return rx.cond(
        NavState.mobile_sidebar_open,
        rx.box(
            # Backdrop gelap
            rx.box(
                on_click=NavState.close_mobile_sidebar,
                style=rx.Style(
                    {
                        "position": "fixed",
                        "inset": "0",
                        "background_color": Color.OVERLAY_BACKDROP,
                        "z_index": "40",
                    }
                ),
            ),
            # Panel Sidebar di kiri
            rx.box(
                sidebar(),
                style=rx.Style(
                    {
                        "position": "fixed",
                        "top": "0",
                        "left": "0",
                        "bottom": "0",
                        "width": Size.SIDEBAR_WIDTH,
                        "box_shadow": Shadow.DRAWER,
                        "z_index": "50",
                    }
                ),
            ),
        ),
        rx.fragment(),
    )


def base_layout(
    content: rx.Component,
    breadcrumb: tuple[str | rx.Var[str], str | rx.Var[str]] = ("Overview", "Dashboard"),
) -> rx.Component:
    """
    Pembungkus utama seluruh halaman terproteksi ITAM Pro.
    """
    return rx.box(
        # Kolom 1: Sidebar Desktop (disembunyikan pada layar <900px)
        rx.box(
            sidebar(),
            style=rx.Style(
                {
                    "width": Size.SIDEBAR_WIDTH,
                    "min_height": "100vh",
                    "position": "sticky",
                    "top": "0",
                    "height": "100vh",
                    "@media (max-width: 899px)": {
                        "display": "none",
                    },
                }
            ),
        ),
        # Drawer Sidebar untuk Mobile (<900px)
        _mobile_sidebar_drawer(),
        # Kolom 2: Topbar + Area Konten Utama
        rx.box(
            topbar(breadcrumb=breadcrumb),
            rx.box(
                content,
                as_="main",
                style=rx.Style(
                    {
                        "width": "100%",
                        "padding": "28px 32px",
                        "flex": "1",
                        "@media (max-width: 899px)": {
                            "padding": "20px",
                        },
                    }
                ),
            ),
            style=rx.Style(
                {
                    "display": "flex",
                    "flex_direction": "column",
                    "min_height": "100vh",
                    "min_width": "0",
                    "width": "100%",
                    "background_color": Color.BG,
                }
            ),
        ),
        style=rx.Style(
            {
                "display": "grid",
                "grid_template_columns": f"{Size.SIDEBAR_WIDTH} 1fr",
                "min_height": "100vh",
                "width": "100%",
                "background_color": Color.BG,
                "@media (max-width: 899px)": {
                    "grid_template_columns": "1fr",
                },
            }
        ),
    )
