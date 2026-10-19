"""
Klien API terpusat untuk State Reflex.
Mendukung mode USE_MOCK=true (Frontend-first) dan USE_MOCK=false (FastAPI Backend).
"""
import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

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


api_client = APIClient()
