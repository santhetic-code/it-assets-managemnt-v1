"""
Utilitas Router ITAM Pro. (Menggantikan pemakaian router.page yang deprecated).
"""
from typing import Any


def get_current_raw_path(router_obj: Any) -> str:
    """Mendapatkan raw_path dengan aman untuk menghindari DeprecationWarning di masa depan."""
    if hasattr(router_obj, "url") and hasattr(router_obj.url, "path"):
        val = router_obj.url.path
        if isinstance(val, str) and val.strip():
            return val.strip()
    if hasattr(router_obj, "page") and hasattr(router_obj.page, "raw_path"):
        val = router_obj.page.raw_path
        if isinstance(val, str) and val.strip():
            return val.strip()
    if hasattr(router_obj, "page") and hasattr(router_obj.page, "path"):
        val = router_obj.page.path
        if isinstance(val, str) and val.strip():
            return val.strip()

    # Fallback yang lebih aman tanpa menggunakan .get() pada objek internal
    session_obj = getattr(router_obj, "session", None)
    if session_obj:
        ip = getattr(session_obj, "client_ip", None)
        if ip is not None:
            return str(ip)
        if isinstance(session_obj, dict):
            return str(session_obj.get("client_ip", "/"))

    return "/"


def get_current_params(router_obj: Any) -> dict[str, Any]:
    """Mendapatkan dictionary params route dengan aman."""
    if hasattr(router_obj, "page") and hasattr(router_obj.page, "params"):
        params = router_obj.page.params
        if isinstance(params, dict):
            return dict(params)
    if hasattr(router_obj, "url") and hasattr(router_obj.url, "query_parameters"):
        query = router_obj.url.query_parameters
        if isinstance(query, dict):
            return dict(query)
    return {}


__all__ = ["get_current_params", "get_current_raw_path"]
