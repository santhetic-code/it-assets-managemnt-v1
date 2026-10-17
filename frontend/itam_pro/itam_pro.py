"""
Entry Point & Routing Utama ITAM Pro.
"""
import reflex as rx

from itam_pro.pages.auth import login_page
from itam_pro.styles import BASE_STYLE, FONT_FAMILY, GOOGLE_FONTS_URL


app = rx.App(
    stylesheets=[GOOGLE_FONTS_URL],
    style=BASE_STYLE,
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="blue",
        font_family=FONT_FAMILY,
    ),
)

# Route halaman login
app.add_page(
    login_page,
    route="/login",
    title="Masuk · ITAM Pro",
)

# Redirect sementara dari "/" ke "/login" selama Dashboard belum dibuat
app.add_page(
    login_page,
    route="/",
    title="ITAM Pro",
)
