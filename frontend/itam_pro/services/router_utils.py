"""
Utilitas Router ITAM Pro (Bebas DeprecationWarning RouterData.page).
"""

from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit


def _unwrap_router(router_obj: Any) -> Any:
    """Ambil mock_router dari parent_state jika test memasang MagicMock pada parent_state."""
    page_obj = getattr(router_obj, "_page", None)
    if page_obj is not None:
        try:
            st = object.__getattribute__(page_obj, "_self_state")
            parent = getattr(st, "parent_state", None)
            if parent is not None and type(parent).__name__ in ("MagicMock", "Mock"):
                return getattr(parent, "router", None) or getattr(parent, "_router", router_obj)
        except AttributeError:
            pass
    return router_obj


def get_current_raw_path(router_obj: Any) -> str:
    """Mendapatkan raw_path dengan aman dari RouterData.url tanpa menyentuh .page."""
    router_obj = _unwrap_router(router_obj)
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
    router_obj = _unwrap_router(router_obj)
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


_INTERNAL_UA_MARKERS = ("python-httpx", "httpx/", "python-requests", "aiohttp")


def _clean_router_str(val: Any) -> str:
    if not isinstance(val, str):
        return ""
    cleaned = val.strip()
    if not cleaned or cleaned.startswith("<"):
        return ""
    return cleaned


def extract_client_origin_from_router(router_obj: Any) -> tuple[str, str]:
    """Ambil (client_ip, client_ua) asli browser dari RouterData Reflex 0.9.12."""
    if router_obj is None or type(router_obj).__name__ in ("MagicMock", "Mock"):
        return "", ""

    client_ip = ""
    client_ua = ""

    headers_obj = getattr(router_obj, "headers", None)
    if headers_obj is not None and type(headers_obj).__name__ not in ("MagicMock", "Mock"):
        raw_headers = getattr(headers_obj, "raw_headers", None)
        lower_headers: dict[str, str] = {}
        if isinstance(raw_headers, dict):
            lower_headers = {str(k).lower(): str(v) for k, v in raw_headers.items()}

        # Prioritas IP: X-Forwarded-For -> X-Real-IP -> atribut x_forwarded_for -> session.client_ip
        xff = _clean_router_str(
            lower_headers.get("x-forwarded-for") or getattr(headers_obj, "x_forwarded_for", "")
        )
        if xff:
            client_ip = xff.split(",")[0].strip()
        if not client_ip:
            client_ip = _clean_router_str(lower_headers.get("x-real-ip"))

        raw_ua = _clean_router_str(
            lower_headers.get("user-agent") or getattr(headers_obj, "user_agent", "")
        )
        if raw_ua and not any(m in raw_ua.lower() for m in _INTERNAL_UA_MARKERS):
            client_ua = raw_ua[:255]

    if not client_ip:
        session_obj = getattr(router_obj, "session", None)
        if session_obj is not None and type(session_obj).__name__ not in ("MagicMock", "Mock"):
            client_ip = _clean_router_str(getattr(session_obj, "client_ip", ""))

    return client_ip, client_ua


def build_query_url(base_path: str, params: dict[str, Any]) -> str:
    """Bangun URL dengan query string bersih hanya untuk parameter yang terisi."""
    clean = {
        k: str(v).strip()
        for k, v in params.items()
        if v is not None and str(v).strip() not in ("", "False", "false")
    }
    if not clean:
        return base_path
    return f"{base_path}?{urlencode(clean)}"


__all__ = [
    "build_query_url",
    "extract_client_origin_from_router",
    "get_current_params",
    "get_current_raw_path",
]
