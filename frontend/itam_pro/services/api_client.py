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
from itam_pro.services.mock.finance_mock import (
    action_jadikan_aset,
    action_pay_bill,
    query_bills,
    query_invoices,
    query_purchases,
)
from itam_pro.services.mock.ip_mock import (
    create_mock_ip_entry,
    delete_mock_ip_entry,
    find_ip_duplicate_owner,
    get_vms_on_host,
    is_valid_ipv4,
    query_mock_ip_entries,
    update_mock_ip_entry,
)
from itam_pro.services.mock.maintenance_mock import (
    action_buat_jadwal_massal,
    action_tandai_selesai,
    query_maintenance_logs,
    query_maintenance_plans,
)
from itam_pro.services.mock.seed import (
    create_mock_assets,
    delete_mock_asset,
    find_sn_duplicate,
    get_mock_category_counts,
    peek_next_asset_id,
    query_mock_assets,
    update_mock_asset,
)

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
        """Ambil daftar aset dengan filter & paginasi untuk Semua Aset atau /assets/c/[slug]."""
        if USE_MOCK:
            await asyncio.sleep(0.08)
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
        """Tambah 1 atau N unit aset fisik baru beserta attributes-nya."""
        if USE_MOCK:
            await asyncio.sleep(0.12)
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
        """Perbarui satu aset beserta attributes-nya."""
        if USE_MOCK:
            await asyncio.sleep(0.12)
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

    def check_sn_duplicate_sync(self, sn_pid: str, exclude_id: str = "") -> str | None:
        """Periksa apakah SN/PID sudah digunakan oleh aset lain (non-blocking warning)."""
        return find_sn_duplicate(sn_pid=sn_pid, exclude_id=exclude_id)

    def peek_next_id_sync(self, kategori: str) -> str:
        """Ambil preview ID Aset otomatis berikutnya berdasarkan kategori."""
        return peek_next_asset_id(kategori=kategori)

    def get_category_counts_sync(self) -> dict[str, int]:
        """Ambil jumlah unit per kategori untuk badge Sidebar."""
        return get_mock_category_counts()

    async def get_ip_entries(
        self,
        grup: str,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar entri IP & Server (VM) dengan filter, sort numerik, & KPI."""
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_mock_ip_entries(
                grup=grup,
                filters=filters,
                page=page,
                page_size=page_size,
            )

        params: dict[str, Any] = {
            "grup": grup,
            "page": page,
            "page_size": page_size,
            **filters,
        }
        response = await self.request(
            method="GET",
            endpoint="/api/v1/ip-entries",
            token=token,
            params=params,
        )
        return response  # type: ignore[return-value]

    async def create_ip_entry(
        self,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Tambah satu entri IP baru."""
        if USE_MOCK:
            await asyncio.sleep(0.1)
            return create_mock_ip_entry(payload=payload)

        response = await self.request(
            method="POST",
            endpoint="/api/v1/ip-entries",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def update_ip_entry(
        self,
        entry_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any] | None:
        """Perbarui satu entri IP."""
        if USE_MOCK:
            await asyncio.sleep(0.1)
            return update_mock_ip_entry(entry_id=entry_id, payload=payload)

        response = await self.request(
            method="PUT",
            endpoint=f"/api/v1/ip-entries/{entry_id}",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def delete_ip_entry(
        self,
        entry_id: str,
        token: str | None = None,
    ) -> bool:
        """Hapus satu entri IP."""
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return delete_mock_ip_entry(entry_id=entry_id)

        await self.request(
            method="DELETE",
            endpoint=f"/api/v1/ip-entries/{entry_id}",
            token=token,
        )
        return True

    def check_ip_duplicate_sync(self, ip_address: str, exclude_id: str = "") -> str | None:
        return find_ip_duplicate_owner(ip_address=ip_address, exclude_id=exclude_id)

    def validate_ipv4_sync(self, ip_address: str) -> bool:
        return is_valid_ipv4(ip_str=ip_address)

    def get_vms_on_host_sync(self, host_asset_id: str) -> list[dict[str, str]]:
        return get_vms_on_host(host_asset_id=host_asset_id)

    async def get_purchases(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_purchases(filters, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "summary": {}}

    async def convert_purchase_to_asset(
        self,
        id_pembelian: str,
        payload: dict[str, str],
    ) -> bool:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            action_jadikan_aset(
                id_pembelian,
                payload["kategori"],
                payload["kepemilikan"],
                payload["lokasi"],
            )
            return True
        return True

    async def get_invoices(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_invoices(filters, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "summary": {}}

    async def get_bills(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_bills(filters, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "summary": {}}

    async def pay_bill(self, bill_id: str, tgl_bayar: str, nominal: int) -> bool:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            action_pay_bill(bill_id, tgl_bayar, nominal)
            return True
        return True

    async def get_maintenance_plans(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_maintenance_plans(filters, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "summary": {}}

    async def get_maintenance_logs(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            return query_maintenance_logs(filters, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def mark_maintenance_complete(
        self,
        plan_id: str,
        tgl_selesai: str,
        hasil: str,
        catatan: str,
        pic: str,
    ) -> bool:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            action_tandai_selesai(plan_id, tgl_selesai, hasil, catatan, pic)
            return True
        return True

    async def create_bulk_maintenance(
        self,
        kategori: str,
        kegiatan: str,
        jenis: str,
        frekuensi: str,
        tgl_mulai: str,
        pic: str,
    ) -> bool:
        if USE_MOCK:
            await asyncio.sleep(0.08)
            action_buat_jadwal_massal(kategori, kegiatan, jenis, frekuensi, tgl_mulai, pic)
            return True
        return True


api_client = APIClient()

__all__ = [
    "BACKEND_URL",
    "USE_MOCK",
    "APIClient",
    "AuthenticationError",
    "api_client",
]
