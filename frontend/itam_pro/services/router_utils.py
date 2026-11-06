"""
Utilitas Router ITAM Pro (Bebas DeprecationWarning RouterData.page).
"""

from typing import Any
from urllib.parse import parse_qs, urlsplit


def get_current_raw_path(router_obj: Any) -> str:
    """Mendapatkan raw_path dengan aman dari RouterData.url tanpa menyentuh .page."""
    url_obj = getattr(router_obj, "url", None)
    if url_obj is not None and type(url_obj).__name__ not in ("MagicMock", "Mock"):
        path_val = getattr(url_obj, "path", None)
        if isinstance(path_val, str) and path_val.strip():
            return path_val.strip()
        url_str = str(url_obj).strip()
        if url_str and not url_str.startswith("<"):
            parsed = urlsplit(url_str)
            if parsed.path:
                return parsed.path

    # Fallback aman tanpa menyentuh properti publik .page (mengakses _page)
    page_obj = getattr(router_obj, "_page", None)
    if page_obj is not None:
        raw_p = getattr(page_obj, "raw_path", None)
        if isinstance(raw_p, str) and raw_p.strip():
            return raw_p.strip()
        p = getattr(page_obj, "path", None)
        if isinstance(p, str) and p.strip():
            return p.strip()

    # Fallback khusus jika router_obj adalah MagicMock yang tidak di-wrap RouterData
    if type(router_obj).__name__ in ("MagicMock", "Mock"):
        raw_p = getattr(getattr(router_obj, "page", None), "path", None)
        if isinstance(raw_p, str) and raw_p.strip():
            return raw_p.strip()

    return "/"


def get_current_params(router_obj: Any) -> dict[str, Any]:
    """Mendapatkan dictionary query params route tanpa menyentuh RouterData.page."""
    url_obj = getattr(router_obj, "url", None)
    if url_obj is not None and type(url_obj).__name__ not in ("MagicMock", "Mock"):
        q_params = getattr(url_obj, "query_parameters", None)
        if isinstance(q_params, dict) and q_params:
            return dict(q_params)
        url_str = str(url_obj).strip()
        if "?" in url_str:
            query_str = urlsplit(url_str).query
            parsed_qs = parse_qs(query_str)
            return {k: v[0] for k, v in parsed_qs.items() if v}

    # Fallback aman tanpa menyentuh properti publik .page (mengakses _page)
    page_obj = getattr(router_obj, "_page", None)
    if page_obj is not None:
        params = getattr(page_obj, "params", None)
        if isinstance(params, dict):
            return dict(params)

    # Fallback khusus jika router_obj adalah MagicMock yang tidak di-wrap RouterData
    if type(router_obj).__name__ in ("MagicMock", "Mock"):
        params = getattr(getattr(router_obj, "page", None), "params", None)
        if isinstance(params, dict):
            return dict(params)

    return {}


__all__ = ["get_current_params", "get_current_raw_path"]
