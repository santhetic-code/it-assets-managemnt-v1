"""
Entry Point & Routing Utama ITAM Pro.
"""
import reflex as rx

from itam_pro.pages.auth import login_page
from itam_pro.pages.finance import purchases_view_page
from itam_pro.pages.infrastructure import ip_vm_page
from itam_pro.pages.inventory import assets_view_page
from itam_pro.pages.operations.maintenance_view import maintenance_view_page
from itam_pro.pages.overview import dashboard_page
from itam_pro.states.asset_state import AssetState
from itam_pro.states.auth_state import AuthState
from itam_pro.states.dashboard_state import DashboardState
from itam_pro.states.finance_state import FinanceState
from itam_pro.states.ip_state import IPState
from itam_pro.states.maintenance_state import MaintenanceState
from itam_pro.styles import BASE_STYLE, GOOGLE_FONTS_URL


def root_redirect_page() -> rx.Component:
    """Komponen perantara untuk route '/' sebelum diarahkan oleh AuthState."""
    return rx.box()


def _redirect_page(target: str) -> rx.Component:
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

app.add_page(
    login_page,
    route="/login",
    title="Masuk · ITAM Pro",
)

app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Dashboard · ITAM Pro",
    on_load=[AuthState.check_auth, DashboardState.load_dashboard],
)

# Route Tunggal Generik Inventaris: Semua Aset & Kategori Dinamis
app.add_page(
    assets_view_page,
    route="/assets",
    title="Semua Aset · ITAM Pro",
    on_load=[AuthState.check_auth, AssetState.load_view_data],
)
app.add_page(
    assets_view_page,
    route="/assets/c/[slug]",
    title="Inventaris Kategori · ITAM Pro",
    on_load=[AuthState.check_auth, AssetState.load_view_data],
)

# Route Modul Infrastructure: IP & Server (VM)
app.add_page(
    ip_vm_page,
    route="/infrastructure/ip",
    title="IP & Server (VM) · ITAM Pro",
    on_load=[AuthState.check_auth, IPState.load_ip_page],
)

# Route Modul Finance: Pembelian & Invoice
app.add_page(
    purchases_view_page,
    route="/finance/purchases",
    title="Pembelian & Invoice · ITAM Pro",
    on_load=[AuthState.check_auth, FinanceState.load_finance_page],
)

# Route Modul Operations: Jadwal Maintenance
app.add_page(
    maintenance_view_page,
    route="/operations/maintenance",
    title="Jadwal Maintenance · ITAM Pro",
    on_load=[AuthState.check_auth, MaintenanceState.load_page],
)

# Redirect kompatibilitas untuk route lama
app.add_page(
    lambda: _redirect_page("/assets/c/pc"),
    route="/pc",
    on_load=rx.redirect("/assets/c/pc"),
)
app.add_page(
    lambda: _redirect_page("/assets/c/monitor"),
    route="/monitor",
    on_load=rx.redirect("/assets/c/monitor"),
)
app.add_page(
    lambda: _redirect_page("/infrastructure/ip"),
    route="/infrastructure/ip-vm",
    on_load=rx.redirect("/infrastructure/ip"),
)
app.add_page(
    lambda: _redirect_page("/finance/purchases"),
    route="/purchases",
    on_load=rx.redirect("/finance/purchases"),
)
app.add_page(
    lambda: _redirect_page("/finance/purchases?tab=invoice"),
    route="/invoices",
    on_load=rx.redirect("/finance/purchases?tab=invoice"),
)
app.add_page(
    lambda: _redirect_page("/operations/maintenance"),
    route="/maintenance",
    on_load=rx.redirect("/operations/maintenance"),
)
