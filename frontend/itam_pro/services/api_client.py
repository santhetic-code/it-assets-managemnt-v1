"""
Klien API terpusat untuk State Reflex.
Mendukung mode USE_MOCK=true (Frontend-first) dan USE_MOCK=false (FastAPI Backend).
Dioptimalkan dengan Persistent HTTP Connection Pooling & tanpa artificial delay.
"""
import asyncio
import os
from typing import Any

import httpx

from itam_pro.config import USE_MOCK
from itam_pro.services.mock.auth_mock import verify_mock_login
from itam_pro.services.mock.credential_mock import (
    get_filtered_credentials,
    reveal_mock_credential,
)
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
from itam_pro.services.power_service import (
    query_server_power,
    remove_server_power_entry,
    save_server_power_entry,
)

BACKEND_URL: str = os.getenv("BACKEND_INTERNAL_URL", "http://backend:8001")


class AuthenticationError(Exception):
    """Exception khusus ketika autentikasi gagal."""


class APIClient:
    def __init__(self) -> None:
        self.base_url = BACKEND_URL
        self.timeout = 10.0
        self.token: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Gunakan kembali koneksi HTTP (keep-alive pool) pada event loop yang aktif."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if (
            self._client is None
            or self._client.is_closed
            or self._client_loop is not current_loop
        ):
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=25,
                    max_connections=100,
                    keepalive_expiry=30.0,
                ),
            )
            self._client_loop = current_loop
        return self._client

    def set_token(self, token: str | None) -> None:
        """Simpan token sesi JWT untuk otentikasi otomatis request berikutnya."""
        self.token = token

    def clear_token(self) -> None:
        """Hapus token sesi saat logout."""
        self.token = None

    async def request(
        self,
        method: str,
        endpoint: str,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        headers = {"Accept": "application/json"}
        effective_token = token or self.token
        if effective_token:
            headers["Authorization"] = f"Bearer {effective_token}"

        client = self._get_client()
        response = await client.request(
            method=method,
            url=endpoint,
            headers=headers,
            params=params,
            json=json_data,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail_msg = ""
            try:
                err_json = response.json()
                if isinstance(err_json, dict) and "detail" in err_json:
                    detail_msg = str(err_json["detail"])
            except Exception:
                pass
            if detail_msg:
                raise Exception(detail_msg) from exc
            raise exc
        return response.json()

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> dict[str, Any]:
        """Autentikasi pengguna ke Mock Service atau Backend FastAPI."""
        if USE_MOCK:
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
            return query_mock_assets(filters=filters, page=page, page_size=page_size)

        clean_filters = dict(filters)
        attr_filters = clean_filters.pop("attr_filters", None)
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **clean_filters,
        }
        if isinstance(attr_filters, dict):
            for k, v in attr_filters.items():
                if v and str(v).strip() not in ("", "Semua"):
                    params[f"attr_{k}"] = v

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
            return create_mock_assets(payload=payload, count=duplicate_count)

        if duplicate_count > 1:
            response = await self.request(
                method="POST",
                endpoint="/api/v1/assets/bulk",
                token=token,
                json_data={"asset": payload, "duplicate_count": duplicate_count},
            )
            if isinstance(response, dict) and "items" in response:
                return list(response["items"])
            return [response] if isinstance(response, dict) else []

        response = await self.request(
            method="POST",
            endpoint="/api/v1/assets",
            token=token,
            json_data=payload,
        )
        return [response] if isinstance(response, dict) else list(response)

    async def update_asset(
        self,
        asset_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any] | None:
        """Perbarui satu aset beserta attributes-nya."""
        if USE_MOCK:
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

    @property
    def use_mock(self) -> bool:
        return USE_MOCK

    async def get_purchases(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_purchases(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "pembelian",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def convert_purchase_to_asset(
        self,
        id_pembelian: str,
        payload: dict[str, str],
    ) -> bool:
        if USE_MOCK:
            action_jadikan_aset(
                id_pembelian,
                payload["kategori"],
                payload["kepemilikan"],
                payload["lokasi"],
            )
            return True
        await self.request(
            "POST",
            f"/api/v1/purchases/{id_pembelian}/convert-to-asset",
            json_data=payload,
        )
        return True

    async def get_invoices(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_invoices(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "invoice",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def get_bills(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_bills(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "tagihan berulang",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def pay_bill(self, bill_id: str, tgl_bayar: str, nominal: int) -> bool:
        if USE_MOCK:
            action_pay_bill(bill_id, tgl_bayar, nominal)
            return True
        await self.request(
            "POST",
            f"/api/v1/purchases/{bill_id}/pay",
            json_data={"tanggal_bayar": tgl_bayar, "advance_cycle": True},
        )
        return True

    async def get_maintenance_plans(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_maintenance_plans(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "jadwal",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/maintenance", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def get_maintenance_logs(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_maintenance_logs(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "riwayat",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/maintenance", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0}

    async def mark_maintenance_complete(
        self,
        plan_id: str,
        tgl_selesai: str,
        hasil: str,
        catatan: str,
        pic: str,
    ) -> bool:
        if USE_MOCK:
            action_tandai_selesai(plan_id, tgl_selesai, hasil, catatan, pic)
            return True
        await self.request(
            "POST",
            f"/api/v1/maintenance/{plan_id}/complete",
            json_data={
                "tanggal_selesai": tgl_selesai,
                "hasil": hasil,
                "tindakan": hasil,
                "catatan": catatan,
                "teknisi": pic,
            },
        )
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
            action_buat_jadwal_massal(kategori, kegiatan, jenis, frekuensi, tgl_mulai, pic)
            return True
        await self.request(
            "POST",
            "/api/v1/maintenance/bulk",
            json_data={
                "kategori": kategori,
                "judul": kegiatan,
                "kegiatan": kegiatan,
                "deskripsi": kegiatan,
                "jenis": jenis,
                "frekuensi": frekuensi,
                "tgl_mulai": tgl_mulai,
                "pic": pic,
            },
        )
        return True

    async def get_credentials(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar kredensial berdasarkan permissions token."""
        if USE_MOCK:
            permissions = {
                "website": "edit",
                "detail_pc": "edit",
                "sql_server": "edit",
                "mikrotik": "edit",
                "internet_kantor": "edit",
                "email": "edit",
                "sosmed": "edit",
                "lainnya": "edit",
            }
            if token == "mock-token-member":
                permissions = {"website": "reveal", "mikrotik": "view"}
            elif token == "mock-token-viewer":
                permissions = {}
            return get_filtered_credentials(permissions, filters, page, page_size)
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/credentials", token=token, params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "tab_counts": {}}

    async def reveal_credential(
        self,
        crd_id: str,
        field_key: str,
        actor: str,
    ) -> dict[str, Any]:
        """Buka rahasia kredensial (dengan audit trail)."""
        if USE_MOCK:
            return await reveal_mock_credential(crd_id, field_key, actor)
        res = await self.request("POST", f"/api/v1/credentials/{crd_id}/reveal")
        if isinstance(res, dict):
            return {
                **res,
                "value": res.get("value") or res.get("password") or res.get("secret") or "",
                "expires_in": 15,
            }
        return {"value": "", "expires_in": 0}

    async def get_server_power(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Ambil daftar Rekap Watt Server beserta ringkasan ESTIMASI."""
        if USE_MOCK:
            return query_server_power(filters=filters, page=page, page_size=page_size)
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/watt-server", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def save_server_power(
        self,
        payload: dict[str, Any],
        asset_id: str = "",
    ) -> dict[str, Any]:
        """Tambah atau perbarui entri Rekap Watt Server secara manual."""
        if USE_MOCK:
            return save_server_power_entry(payload=payload, asset_id=asset_id)
        if asset_id and asset_id.strip():
            res = await self.request(
                "PUT",
                f"/api/v1/watt-server/{asset_id.strip()}",
                json_data=payload,
            )
        else:
            res = await self.request("POST", "/api/v1/watt-server", json_data=payload)
        return res if isinstance(res, dict) else {}

    async def delete_server_power(self, asset_id: str) -> bool:
        """Hapus satu entri server dari Rekap Watt Server."""
        if USE_MOCK:
            return remove_server_power_entry(asset_id=asset_id)
        await self.request("DELETE", f"/api/v1/watt-server/{asset_id.strip()}")
        return True

    async def get_audit_logs(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 15,
    ) -> dict[str, Any]:
        """Ambil daftar Audit Log berhalaman dari backend."""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        res = await self.request("GET", "/api/v1/audit-logs", params=params)
        return res if isinstance(res, dict) else {"items": res}

    async def get_users(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """Ambil daftar pengguna dari backend."""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        res = await self.request("GET", "/api/v1/users", params=params)
        return res if isinstance(res, dict) else {"items": res}

    async def change_password(
        self,
        old_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Ubah password akun sendiri yang sedang login."""
        res = await self.request(
            "POST",
            "/api/v1/users/me/password",
            json_data={"old_password": old_password, "new_password": new_password},
        )
        return res if isinstance(res, dict) else {}

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Buat akun pengguna baru (Administrator)."""
        res = await self.request("POST", "/api/v1/users", json_data=payload)
        return res if isinstance(res, dict) else {}

    async def update_user(
        self,
        identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Perbarui data pengguna (Administrator)."""
        res = await self.request(
            "PATCH",
            f"/api/v1/users/{identifier}",
            json_data=payload,
        )
        return res if isinstance(res, dict) else {}

    async def reset_user_password(
        self,
        identifier: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Reset password akun pengguna oleh Administrator."""
        res = await self.request(
            "POST",
            f"/api/v1/users/{identifier}/reset-password",
            json_data={"new_password": new_password},
        )
        return res if isinstance(res, dict) else {}

    async def delete_user(self, identifier: str) -> dict[str, Any]:
        """Hapus akun pengguna oleh Administrator."""
        res = await self.request("DELETE", f"/api/v1/users/{identifier}")
        return res if isinstance(res, dict) else {}

    async def get_dashboard(self) -> dict[str, Any]:
        """Ambil ringkasan Dashboard real-time dari backend."""
        res = await self.request("GET", "/api/v1/dashboard")
        return res if isinstance(res, dict) else {}


api_client = APIClient()

__all__ = [
    "BACKEND_URL",
    "USE_MOCK",
    "APIClient",
    "AuthenticationError",
    "api_client",
]
