"""
Utilitas Router Reflex untuk ITAM Pro.
Abstraksi untuk menghindari DeprecationWarning dari pemanggilan langsung
self.router.page.raw_path / params.
"""
from typing import Any


def get_current_raw_path(router_obj: Any) -> str:
    """Mendapatkan raw_path dengan aman untuk menghindari DeprecationWarning di masa depan."""
    if hasattr(router_obj, "page") and hasattr(router_obj.page, "raw_path"):
        return str(router_obj.page.raw_path or "")
    # Fallback jika struktur Reflex berubah di versi mendatang
    return str(getattr(router_obj, "session", {}).get("client_ip", "/"))


def get_current_params(router_obj: Any) -> dict[str, Any]:
    """Mendapatkan dictionary params route dengan aman."""
    if hasattr(router_obj, "page") and hasattr(router_obj.page, "params"):
        return dict(router_obj.page.params or {})
    return {}


__all__ = ["get_current_params", "get_current_raw_path"]
