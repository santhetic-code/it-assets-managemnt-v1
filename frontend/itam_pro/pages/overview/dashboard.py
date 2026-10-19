"""
Halaman Overview -> Dashboard (/dashboard).
Tahap 2: Struktur Base Layout dengan judul dan subjudul halaman.
"""
import reflex as rx

from itam_pro.components.layout import base_layout
from itam_pro.styles import Color, FontSize, FontWeight


def _dashboard_header() -> rx.Component:
    """Header halaman Dashboard berisi judul dan subjudul."""
    return rx.vstack(
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
        width="100%",
    )


def dashboard_page() -> rx.Component:
    """Halaman utama /dashboard yang dibungkus dengan base_layout."""
    content = rx.vstack(
        _dashboard_header(),
        spacing="6",
        align="start",
        width="100%",
    )
    return base_layout(
        content=content,
        breadcrumb=("Overview", "Dashboard"),
    )
