"""
Klien API terpusat untuk State Reflex.
Mendukung mode USE_MOCK=true (Frontend-first) dan USE_MOCK=false (FastAPI Backend).
"""
import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from itam_pro.services.mock.asset_mock import (
    create_mock_assets,
    delete_mock_asset,
    query_mock_assets,
    update_mock_asset,
)
from itam_pro.services.mock.auth_mock import verify_mock_login
from itam_pro.services.mock.dashboard_mock import get_mock_dashboard_summary

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"
BACKEND_URL: str = os.getenv("BACKEND_INTERNAL_URL", "http://backend:8001")


class AuthenticationError(Exception):
    """Exception khusus ketika autentikasi gagal."""


class APIClient:
    def __init__(self) -> None:
        self.base_url = BACKEND_URL
        self.timeout = 10.0

    async def request(
        self,
        method: str,
        endpoint: str,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=endpoint,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> dict[str, Any]:
        """Autentikasi pengguna ke Mock Service atau Backend FastAPI."""
        if USE_MOCK:
            await asyncio.sleep(0.6)
            result = verify_mock_login(username, password)
            if not result:
                raise AuthenticationError("Username atau password salah")
            return result

        try:
            response = await self.request(
                method="POST",
                endpoint="/api/v1/auth/login",
                json_data={
                    "username": username,
                    "password": password,
                    "remember_me": remember_me,
                },
            )
            return response  # type: ignore[return-value]
        except httpx.HTTPStatusError as exc:
            raise AuthenticationError("Username atau password salah") from exc
        except httpx.RequestError as exc:
            raise AuthenticationError("Gagal terhubung ke layanan autentikasi") from exc

    async def get_dashboard_summary(self, token: str | None = None) -> dict[str, Any]:
        """Ambil ringkasan data Dashboard dari Mock Service atau Backend FastAPI."""
        if USE_MOCK:
            return get_mock_dashboard_summary()

        response = await self.request(
            method="GET",
            endpoint="/api/v1/dashboard/summary",
            token=token,
        )
        return response  # type: ignore[return-value]

    async def get_assets(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar aset dengan filter & paginasi ({items, total, page, page_size})."""
        if USE_MOCK:
            await asyncio.sleep(0.12)
            return query_mock_assets(filters=filters, page=page, page_size=page_size)

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        response = await self.request(
            method="GET",
            endpoint="/api/v1/assets",
            token=token,
            params=params,
        )
        return response  # type: ignore[return-value]

    async def create_assets(
        self,
        payload: dict[str, Any],
        duplicate_count: int = 1,
        token: str | None = None,
    ) -> list[dict[str, Any]]:
        """Tambah 1 atau N unit aset fisik baru."""
        if USE_MOCK:
            await asyncio.sleep(0.15)
            return create_mock_assets(payload=payload, count=duplicate_count)

        response = await self.request(
            method="POST",
            endpoint="/api/v1/assets",
            token=token,
            json_data={**payload, "duplicate_count": duplicate_count},
        )
        return response  # type: ignore[return-value]

    async def update_asset(
        self,
        asset_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any] | None:
        """Perbarui satu aset."""
        if USE_MOCK:
            await asyncio.sleep(0.15)
            return update_mock_asset(asset_id=asset_id, payload=payload)

        response = await self.request(
            method="PUT",
            endpoint=f"/api/v1/assets/{asset_id}",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def delete_asset(
        self,
        asset_id: str,
        token: str | None = None,
    ) -> bool:
        """Hapus satu aset."""
        if USE_MOCK:
            await asyncio.sleep(0.1)
            return delete_mock_asset(asset_id=asset_id)

        await self.request(
            method="DELETE",
            endpoint=f"/api/v1/assets/{asset_id}",
            token=token,
        )
        return True


api_client = APIClient()

__all__ = [
    "BACKEND_URL",
    "USE_MOCK",
    "APIClient",
    "AuthenticationError",
    "api_client",
]
