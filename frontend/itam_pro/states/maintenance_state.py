"""
State Manajemen Jadwal Maintenance ITAM Pro (Tahap 10).
Mengatur data jadwal rencana, riwayat/log maintenance, metrik KPI, dan aksi eksekusi.
"""
from datetime import date
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.router_utils import get_current_params

VALID_TABS = ("daftar", "kalender", "riwayat")


class MaintenanceState(rx.State):
    """Controller State untuk Modul Jadwal Maintenance."""

    active_tab: str = "daftar"
    plans: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []

    summary: dict[str, Any] = {
        "terlambat": 0,
        "segera": 0,
        "aktif": 0,
        "tindak_lanjut": 0,
    }

    search_query: str = ""
    history_search_query: str = ""

    # --- Modal Tandai Selesai ---
    is_selesai_open: bool = False
    selesai_plan_id: str = ""
    selesai_plan_title: str = ""
    selesai_tgl: str = ""
    selesai_hasil: str = "Normal"
    selesai_catatan: str = ""
    selesai_pic: str = "Ridho"

    # --- Modal Buat Jadwal Massal ---
    is_massal_open: bool = False
    massal_kategori: str = "PC"
    massal_kegiatan: str = "Cek & bersihkan debu internal"
    massal_jenis: str = "Pengecekan rutin"
    massal_frekuensi: str = "3 bulan"
    massal_tgl_mulai: str = ""
    massal_pic: str = "Ridho"

    # --- LIFECYCLE & FETCH ---

    @rx.event
    async def load_page(self) -> None:
        """Dipanggil saat on_load route /operations/maintenance."""
        params = get_current_params(self.router)
        tab = str(params.get("tab", "daftar")).strip().lower()
        if tab not in VALID_TABS:
            tab = "daftar"
        self.active_tab = tab
        await self._fetch_current_tab()

    async def _fetch_current_tab(self) -> None:
        if self.active_tab == "daftar":
            res = await api_client.get_maintenance_plans({"search": self.search_query})
            self.plans = res.get("items", [])
            self.summary = res.get(
                "summary",
                {"terlambat": 0, "segera": 0, "aktif": 0, "tindak_lanjut": 0},
            )
        elif self.active_tab == "kalender":
            res = await api_client.get_maintenance_plans({})
            self.plans = res.get("items", [])
        elif self.active_tab == "riwayat":
            res = await api_client.get_maintenance_logs({"search": self.history_search_query})
            self.logs = res.get("items", [])

    @rx.event
    async def set_tab(self, tab: str) -> None:
        self.active_tab = tab
        await self._fetch_current_tab()
        return rx.redirect(f"/operations/maintenance?tab={tab}")

    @rx.event
    async def set_search_query(self, query: str) -> None:
        self.search_query = query
        await self._fetch_current_tab()

    @rx.event
    async def set_history_search(self, query: str) -> None:
        self.history_search_query = query
        await self._fetch_current_tab()

    # --- ACTION: TANDAI SELESAI ---

    @rx.event
    def open_tandai_selesai(self, plan: dict[str, Any]) -> None:
        self.selesai_plan_id = plan.get("id", "")
        self.selesai_plan_title = f"{plan.get('id')} - {plan.get('objek_display', '')}"
        self.selesai_tgl = date.today().strftime("%Y-%m-%d")
        self.selesai_hasil = "Normal"
        self.selesai_catatan = ""
        self.selesai_pic = plan.get("pic") or "Ridho"
        self.is_selesai_open = True

    @rx.event
    def close_tandai_selesai(self) -> None:
        self.is_selesai_open = False

    @rx.event
    def set_selesai_tgl(self, val: str) -> None:
        self.selesai_tgl = val

    @rx.event
    def set_selesai_hasil(self, val: str) -> None:
        self.selesai_hasil = val

    @rx.event
    def set_selesai_catatan(self, val: str) -> None:
        self.selesai_catatan = val

    @rx.event
    def set_selesai_pic(self, val: str) -> None:
        self.selesai_pic = val

    @rx.event
    async def submit_tandai_selesai(self) -> None:
        if not self.selesai_plan_id:
            return
        await api_client.mark_maintenance_complete(
            plan_id=self.selesai_plan_id,
            tgl_selesai=self.selesai_tgl,
            hasil=self.selesai_hasil,
            catatan=self.selesai_catatan,
            pic=self.selesai_pic,
        )
        self.is_selesai_open = False
        await self._fetch_current_tab()
        return rx.toast("Maintenance berhasil dicatat dan jadwal digeser.")

    # --- ACTION: BUAT JADWAL MASSAL ---

    @rx.event
    def open_massal(self) -> None:
        self.massal_kategori = "PC"
        self.massal_kegiatan = "Cek & bersihkan debu internal"
        self.massal_jenis = "Pengecekan rutin"
        self.massal_frekuensi = "3 bulan"
        self.massal_tgl_mulai = date.today().strftime("%Y-%m-%d")
        self.massal_pic = "Ridho"
        self.is_massal_open = True

    @rx.event
    def close_massal(self) -> None:
        self.is_massal_open = False

    @rx.event
    def set_massal_kategori(self, val: str) -> None:
        self.massal_kategori = val

    @rx.event
    def set_massal_kegiatan(self, val: str) -> None:
        self.massal_kegiatan = val

    @rx.event
    def set_massal_jenis(self, val: str) -> None:
        self.massal_jenis = val

    @rx.event
    def set_massal_frekuensi(self, val: str) -> None:
        self.massal_frekuensi = val

    @rx.event
    def set_massal_tgl_mulai(self, val: str) -> None:
        self.massal_tgl_mulai = val

    @rx.event
    def set_massal_pic(self, val: str) -> None:
        self.massal_pic = val

    @rx.event
    async def submit_massal(self) -> None:
        await api_client.create_bulk_maintenance(
            kategori=self.massal_kategori,
            kegiatan=self.massal_kegiatan,
            jenis=self.massal_jenis,
            frekuensi=self.massal_frekuensi,
            tgl_mulai=self.massal_tgl_mulai,
            pic=self.massal_pic,
        )
        self.is_massal_open = False
        await self._fetch_current_tab()
        return rx.toast("Jadwal massal berhasil dibuat untuk seluruh unit.")
