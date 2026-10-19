"""
Entry Point & Routing Utama ITAM Pro.
"""
import reflex as rx

from itam_pro.pages.auth import login_page
from itam_pro.pages.inventory import assets_inventory_page
from itam_pro.pages.overview import dashboard_page
from itam_pro.states.asset_state import AssetState
from itam_pro.states.auth_state import AuthState
from itam_pro.states.dashboard_state import DashboardState
from itam_pro.states.nav_state import NavState
from itam_pro.styles import BASE_STYLE, GOOGLE_FONTS_URL


def root_redirect_page() -> rx.Component:
    """Komponen perantara untuk route '/' sebelum diarahkan oleh AuthState."""
    return rx.box()


app = rx.App(
    stylesheets=[GOOGLE_FONTS_URL],
    style=BASE_STYLE,
)

# Route "/" -> redirect ke /dashboard bila sudah login, selain itu /login
app.add_page(
    root_redirect_page,
    route="/",
    title="ITAM Pro",
    on_load=AuthState.redirect_from_root,
)

# Route halaman login
app.add_page(
    login_page,
    route="/login",
    title="Masuk · ITAM Pro",
)

# Route halaman Dashboard
app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Dashboard · ITAM Pro",
    on_load=[
        AuthState.check_auth,
        NavState.set_page_context("Overview", "Dashboard"),
        DashboardState.load_dashboard,
    ],
)

# Route halaman Assets Inventory
app.add_page(
    assets_inventory_page,
    route="/assets",
    title="Assets Inventory · ITAM Pro",
    on_load=[
        AuthState.check_auth,
        NavState.set_page_context("Inventory", "Assets Inventory"),
        AssetState.load_assets,
    ],
)
