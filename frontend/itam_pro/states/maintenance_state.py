"""State Manajemen Jadwal Maintenance ITAM Pro (Artboard 13 & 14).

Dioptimalkan untuk alur Rencana, Jadwal, Riwayat, Kalender, dan Impor CSV AC.
"""

import csv
import io
from datetime import date
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.maintenance_mock import (
    MAINTENANCE_TEMPLATES,
    MASTER_ROOMS_BY_LOCATION,
    MOCK_MAINTENANCE_PLANS,
    format_date_short_id,
)
from itam_pro.services.recurrence import add_interval_clamped, parse_date_flexible
from itam_pro.services.router_utils import get_current_params

VALID_TABS = ("daftar", "kalender", "riwayat", "rencana")


def _normalize_plan_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Pastikan field tampilan tabel & chip selalu lengkap baik dari Backend maupun Mock."""
    row = dict(raw)
    aid = str(row.get("objek_asset_id") or row.get("id_aset") or "").strip().upper()
    kat_raw = str(row.get("kategori_chip") or row.get("kategori") or "").strip()
    teks = str(
        row.get("objek_display")
        or row.get("objek_teks")
        or row.get("nama_aset")
        or ""
    ).upper()

    if kat_raw in ("PC", "Server", "Laptop", "PC & Server") or aid.startswith(
        ("PC-", "SRV-", "LPT-")
    ):
        kat_chip = "PC & Server"
    elif kat_raw == "UPS" or aid.startswith("UPS-") or "UPS" in teks:
        kat_chip = "UPS"
    elif kat_raw == "AC" or teks.startswith("AC"):
        kat_chip = "AC"
    elif kat_raw == "Genset" or aid.startswith("GNS-") or "GENSET" in teks:
        kat_chip = "Genset"
    elif kat_raw in ("Jaringan", "Router", "Router/Switch") or aid.startswith(
        ("RTR-", "NET-")
    ):
        kat_chip = "Jaringan"
    elif kat_raw in ("Kendaraan", "Mobil", "Motor") or aid.startswith("KND-"):
        kat_chip = "Kendaraan"
    else:
        kat_chip = (
            kat_raw
            if kat_raw in ("PC & Server", "UPS", "AC", "Genset", "Jaringan", "Kendaraan")
            else "Fasilitas"
        )

    row["kategori_chip"] = kat_chip
    row["objek_tipe"] = row.get("objek_tipe") or (
        "kelompok" if int(row.get("jumlah_unit") or 1) > 1 else "aset"
    )

    if not row.get("sub_label"):
        if row["objek_tipe"] == "kelompok":
            row["sub_label"] = f"{row.get('jumlah_unit', 1)} unit"
        else:
            row["sub_label"] = str(row.get("deskripsi") or row.get("catatan") or "")

    jadwal_iso = str(
        row.get("jadwal_berikutnya") or row.get("tanggal_jadwal") or ""
    ).strip()
    row["jadwal_berikutnya"] = jadwal_iso
    row["jadwal_display"] = row.get("jadwal_display") or format_date_short_id(jadwal_iso)

    # Hitung status & selisih hari secara dinamis
    d_due = parse_date_flexible(jadwal_iso)
    if d_due is not None:
        diff = (d_due - date.today()).days
        if diff < 0:
            row["status"] = "Terlambat"
            row["status_label"] = f"Terlambat {abs(diff)} hari"
        elif diff == 0:
            row["status"] = "Segera"
            row["status_label"] = "Hari ini"
        elif diff <= 7:
            row["status"] = "Segera"
            row["status_label"] = f"{diff} hari lagi"
        else:
            row["status"] = "Terjadwal"
            row["status_label"] = f"{diff} hari lagi"
    else:
        row["status"] = str(row.get("status_efektif") or row.get("status") or "Terjadwal")
        row["status_label"] = str(row.get("status_label") or "—")

    if not row.get("terakhir_hasil_display"):
        th = str(row.get("terakhir_hasil") or row.get("tindakan") or "").strip()
        td = str(row.get("terakhir_dilakukan") or "").strip()
        if td and th and th not in ("-", "—"):
            row["terakhir_hasil_display"] = f"{format_date_short_id(td)} · {th}"
        elif th and th not in ("-", "—"):
            row["terakhir_hasil_display"] = th
        elif td:
            row["terakhir_hasil_display"] = format_date_short_id(td)
        else:
            row["terakhir_hasil_display"] = "—"

    pic_val = str(row.get("pic") or row.get("teknisi") or "Ridho").strip()
    row["pic"] = pic_val
    vendor_val = str(row.get("vendor_servis") or "").strip()
    if not row.get("pelaksana_tipe"):
        row["pelaksana_tipe"] = (
            "Vendor"
            if (vendor_val and vendor_val != "-")
            or "teknisi" in pic_val.lower()
            or "vendor" in pic_val.lower()
            else "Internal"
        )

    return row


class MaintenanceState(rx.State):
    """Controller State untuk Modul Jadwal Maintenance (Artboard 13 & 14)."""

    active_tab: str = "daftar"
    active_kpi_card: str = "all"  # "all" | "terlambat" | "segera" | "tindak_lanjut"
    active_category_chip: str = "Semua"
    plans: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    _skip_next_load_fetch: bool = False

    summary: dict[str, Any] = {
        "terlambat": 4,
        "segera": 0,
        "aktif": 10,
        "tindak_lanjut": 0,
    }
    chip_counts: dict[str, int] = {
        "Semua": 10,
        "PC & Server": 2,
        "UPS": 1,
        "AC": 5,
        "Genset": 2,
        "Jaringan": 0,
        "Fasilitas": 0,
        "Kendaraan": 0,
    }

    # Filter Bar
    search_query: str = ""
    status_filter: str = "Semua status"
    jenis_filter: str = "Semua jenis"
    pelaksana_filter: str = "Semua pelaksana"
    pic_filter: str = "Semua PIC"
    history_search_query: str = ""
    history_vendor_filter: str = "Semua pelaksana"

    # --- Modal 1: Buat Rencana Maintenance (Artboard 14 Kiri) ---
    is_massal_open: bool = False
    plan_template: str = "AC"
    plan_objek_tipe: str = "Kelompok aset"  # "Satu aset" | "Kelompok aset" | "Lokasi"
    plan_asset_id: str = "UPS-001"
    massal_kategori: str = "AC"
    plan_lokasi: str = "Kantor Blok 12"
    plan_ruangan: str = "Ruang Kerja"
    plan_detected_units: int = 3
    massal_kegiatan: str = "Cuci AC (cleaning)"
    massal_jenis: str = "Preventif"
    plan_interval_nilai: str = "3"
    plan_interval_satuan: str = "bulan"
    massal_frekuensi: str = "3 bulan"
    massal_tgl_mulai: str = "2026-08-07"
    plan_use_meter: bool = False
    plan_meter_interval: str = "250"
    plan_pelaksana_tipe: str = "Vendor"
    massal_pic: str = "Teknisi AC"
    plan_reminders: list[str] = ["H-7", "H-1"]

    # --- Modal 2: Tandai Selesai (Artboard 14 Kanan) ---
    is_selesai_open: bool = False
    selesai_plan_id: str = ""
    selesai_plan_title: str = ""
    selesai_is_group: bool = False
    selesai_all_units: list[str] = ["AC 1", "AC 2", "AC 3"]
    selesai_checked_units: list[str] = ["AC 1", "AC 2", "AC 3"]
    selesai_tgl: str = "2026-11-10"
    selesai_pelaksana_tipe: str = "Vendor"
    selesai_pic: str = "Teknisi AC"
    selesai_biaya: str = ""
    selesai_checklist_options: list[str] = [
        "Cuci indoor",
        "Cuci outdoor",
        "Cek freon / tekanan",
        "Cek saluran pembuangan",
    ]
    selesai_checked_items: list[str] = [
        "Cuci indoor",
        "Cuci outdoor",
        "Cek freon / tekanan",
    ]
    selesai_hasil: str = "Normal"
    selesai_catatan: str = ""
    selesai_ada_temuan: bool = False
    selesai_interval_nilai: int = 3
    selesai_interval_satuan: str = "bulan"

    # --- Modal 3: Import CSV AC dari Google Sheet ---
    is_import_ac_open: bool = False
    import_ac_csv_text: str = (
        "Lokasi,Jenis Ruangan,Jumlah AC,Tanggal Cuci Terakhir,Interval (bulan)\n"
        "Kantor Blok 12,Ruang Kerja,3,07/08/2026,3\n"
        "Kantor Blok 13,Ruang Kerja,4,28/08/2026,3\n"
        "Kantor Blok 14,Ruang Server,2,28/09/2026,2"
    )
    import_ac_preview_rows: list[dict[str, Any]] = []
    import_ac_errors: list[dict[str, Any]] = []

    # --- COMPUTED VARS ---

    @rx.var(cache=True)
    def filtered_plans(self) -> list[dict[str, Any]]:
        rows = list(self.plans)
        if self.active_kpi_card == "terlambat":
            rows = [r for r in rows if r.get("status") == "Terlambat"]
        elif self.active_kpi_card == "segera":
            rows = [r for r in rows if r.get("status") == "Segera"]
        elif self.active_kpi_card == "tindak_lanjut":
            rows = [r for r in rows if r.get("terakhir_hasil") == "Perlu tindak lanjut"]

        if self.active_category_chip and self.active_category_chip != "Semua":
            rows = [r for r in rows if r.get("kategori_chip") == self.active_category_chip]

        if self.status_filter and self.status_filter != "Semua status":
            rows = [r for r in rows if r.get("status") == self.status_filter]

        if self.jenis_filter and self.jenis_filter != "Semua jenis":
            rows = [r for r in rows if r.get("jenis") == self.jenis_filter]

        if self.pelaksana_filter and self.pelaksana_filter != "Semua pelaksana":
            rows = [r for r in rows if r.get("pelaksana_tipe") == self.pelaksana_filter]

        if self.pic_filter and self.pic_filter != "Semua PIC":
            rows = [r for r in rows if r.get("pic") == self.pic_filter]

        return rows

    @rx.var(cache=True)
    def overdue_plans(self) -> list[dict[str, Any]]:
        return [r for r in self.filtered_plans if r.get("status") == "Terlambat"]

    @rx.var(cache=True)
    def upcoming_plans(self) -> list[dict[str, Any]]:
        return [r for r in self.filtered_plans if r.get("status") != "Terlambat"]

    @rx.var(cache=True)
    def overdue_count_filtered(self) -> int:
        return len(self.overdue_plans)

    @rx.var(cache=True)
    def upcoming_count_filtered(self) -> int:
        return len(self.upcoming_plans)

    @rx.var(cache=True)
    def total_filtered_label(self) -> str:
        return f"{len(self.filtered_plans)} jadwal"

    @rx.var(cache=True)
    def room_options_for_plan(self) -> list[str]:
        return MASTER_ROOMS_BY_LOCATION.get(
            self.plan_lokasi, ["Ruang Kerja", "Ruang Server", "Lobby"]
        )

    @rx.var(cache=True)
    def preview_next_due_plan_modal(self) -> str:
        try:
            val = max(1, int(self.plan_interval_nilai or "3"))
        except ValueError:
            val = 3
        d_next = add_interval_clamped(
            self.massal_tgl_mulai or date.today().isoformat(),
            val,
            self.plan_interval_satuan,
        )
        return format_date_short_id(d_next.isoformat())

    @rx.var(cache=True)
    def preview_next_due_selesai_modal(self) -> str:
        d_next = add_interval_clamped(
            self.selesai_tgl or date.today().isoformat(),
            self.selesai_interval_nilai,
            self.selesai_interval_satuan,
        )
        return (
            f"{format_date_short_id(d_next.isoformat())} "
            f"({self.selesai_interval_nilai} {self.selesai_interval_satuan} "
            "dari tanggal dikerjakan)"
        )

    @rx.var(cache=True)
    def selesai_units_summary_label(self) -> str:
        return f"{len(self.selesai_checked_units)} dari {len(self.selesai_all_units)} unit"

    @rx.var(cache=True)
    def total_biaya_riwayat_display(self) -> str:
        total = sum(int(entry.get("biaya") or 0) for entry in self.logs)
        return f"Rp {total:,}".replace(",", ".")

    @rx.var(cache=True)
    def import_ac_preview_summary(self) -> str:
        return f"Pratinjau: {len(self.import_ac_preview_rows)} rencana valid siap diimpor"

    # --- LIFECYCLE & FETCH ---

    @rx.event
    async def load_page(self) -> None:
        params = get_current_params(self.router)
        tab = str(params.get("tab", "daftar")).strip().lower()
        if tab not in VALID_TABS:
            tab = "daftar"

        if self._skip_next_load_fetch and tab == self.active_tab:
            self._skip_next_load_fetch = False
            return

        self._skip_next_load_fetch = False
        self.active_tab = tab
        await self._fetch_current_tab()

    async def _fetch_current_tab(self) -> None:
        res = await api_client.get_maintenance_plans(
            {"search": self.search_query}, page_size=50
        )
        raw_items = res.get("items", [])
        items = [_normalize_plan_item(it) for it in raw_items]
        self.plans = items

        terlambat_cnt = sum(1 for it in items if it.get("status") == "Terlambat")
        segera_cnt = sum(1 for it in items if it.get("status") == "Segera")
        tindak_cnt = sum(
            1
            for it in items
            if "tindak lanjut" in str(it.get("terakhir_hasil", "")).lower()
            or "tindak lanjut" in str(it.get("hasil", "")).lower()
        )
        self.summary = {
            "terlambat": terlambat_cnt,
            "segera": segera_cnt,
            "aktif": len(items),
            "tindak_lanjut": tindak_cnt,
        }

        c_map: dict[str, int] = {
            "Semua": len(items),
            "PC & Server": 0,
            "UPS": 0,
            "AC": 0,
            "Genset": 0,
            "Jaringan": 0,
            "Fasilitas": 0,
            "Kendaraan": 0,
        }
        for it in items:
            kc = str(it.get("kategori_chip") or "Fasilitas")
            c_map[kc] = c_map.get(kc, 0) + 1
        self.chip_counts = c_map

        if self.active_tab == "riwayat":
            log_res = await api_client.get_maintenance_logs(
                {"search": self.history_search_query}, page_size=50
            )
            self.logs = log_res.get("items", [])

    @rx.event
    async def set_tab(self, tab: str) -> rx.event.EventSpec:
        self.active_tab = tab
        await self._fetch_current_tab()
        self._skip_next_load_fetch = True
        return rx.redirect(f"/operations/maintenance?tab={tab}")

    @rx.event
    def select_kpi_card(self, card_key: str) -> Any:
        if card_key == "jadwal_aktif":
            return MaintenanceState.set_tab("kalender")
        self.active_kpi_card = "all" if self.active_kpi_card == card_key else card_key
        return None

    @rx.event
    def select_category_chip(self, chip_name: str) -> None:
        self.active_category_chip = chip_name

    @rx.event
    async def set_search_query(self, query: str) -> None:
        if self.search_query == query:
            return
        self.search_query = query
        await self._fetch_current_tab()

    @rx.event
    def set_status_filter(self, val: str) -> None:
        self.status_filter = val

    @rx.event
    def set_jenis_filter(self, val: str) -> None:
        self.jenis_filter = val

    @rx.event
    def set_pelaksana_filter(self, val: str) -> None:
        self.pelaksana_filter = val

    @rx.event
    def set_pic_filter(self, val: str) -> None:
        self.pic_filter = val

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.active_kpi_card = "all"
        self.active_category_chip = "Semua"
        self.status_filter = "Semua status"
        self.jenis_filter = "Semua jenis"
        self.pelaksana_filter = "Semua pelaksana"
        self.pic_filter = "Semua PIC"
        await self._fetch_current_tab()

    @rx.event
    async def set_history_search(self, query: str) -> None:
        if self.history_search_query == query:
            return
        self.history_search_query = query
        await self._fetch_current_tab()

    # --- HANDLERS MODAL 1: BUAT RENCANA MAINTENANCE (ARTBOARD 14 KIRI) ---

    @rx.event
    def open_massal(self) -> None:
        self.select_plan_template("AC")
        self.is_massal_open = True

    @rx.event
    def close_massal(self) -> None:
        self.is_massal_open = False

    @rx.event
    def select_plan_template(self, tpl_name: str) -> None:
        self.plan_template = tpl_name
        tpl = MAINTENANCE_TEMPLATES.get(tpl_name, MAINTENANCE_TEMPLATES["AC"])
        self.massal_kategori = str(tpl.get("kategori", "AC"))
        self.massal_kegiatan = str(tpl.get("kegiatan", ""))
        self.massal_jenis = str(tpl.get("jenis", "Preventif"))
        self.plan_interval_nilai = str(tpl.get("interval_nilai", 3))
        self.plan_interval_satuan = str(tpl.get("interval_satuan", "bulan"))
        self.massal_frekuensi = f"{self.plan_interval_nilai} {self.plan_interval_satuan}"
        self.plan_pelaksana_tipe = str(tpl.get("pelaksana_tipe", "Internal"))
        self.massal_pic = str(tpl.get("pelaksana_nama", "Ridho"))
        self.plan_objek_tipe = (
            "Kelompok aset" if tpl.get("objek_tipe") == "kelompok" else "Satu aset"
        )
        self.plan_use_meter = bool(tpl.get("interval_pemakaian"))
        if tpl.get("interval_pemakaian"):
            self.plan_meter_interval = str(tpl["interval_pemakaian"])

    @rx.event
    def set_plan_objek_tipe(self, val: str) -> None:
        self.plan_objek_tipe = val

    @rx.event
    def set_massal_kategori(self, val: str) -> None:
        self.massal_kategori = val

    @rx.event
    def set_plan_lokasi(self, val: str) -> None:
        self.plan_lokasi = val
        rooms = MASTER_ROOMS_BY_LOCATION.get(val, ["Ruang Kerja"])
        self.plan_ruangan = rooms[0]
        self.plan_detected_units = 4 if "13" in val else (2 if "14" in val else 3)

    @rx.event
    def set_plan_ruangan(self, val: str) -> None:
        self.plan_ruangan = val

    @rx.event
    def set_massal_kegiatan(self, val: str) -> None:
        self.massal_kegiatan = val

    @rx.event
    def set_massal_jenis(self, val: str) -> None:
        self.massal_jenis = val

    @rx.event
    def set_plan_interval_nilai(self, val: str) -> None:
        self.plan_interval_nilai = val
        self.massal_frekuensi = f"{val} {self.plan_interval_satuan}"

    @rx.event
    def set_plan_interval_satuan(self, val: str) -> None:
        self.plan_interval_satuan = val
        self.massal_frekuensi = f"{self.plan_interval_nilai} {val}"

    @rx.event
    def set_massal_frekuensi(self, val: str) -> None:
        self.massal_frekuensi = val

    @rx.event
    def set_massal_tgl_mulai(self, val: str) -> None:
        self.massal_tgl_mulai = val

    @rx.event
    def toggle_plan_use_meter(self, _checked: Any = None) -> None:
        self.plan_use_meter = not self.plan_use_meter

    @rx.event
    def set_plan_meter_interval(self, val: str) -> None:
        self.plan_meter_interval = val

    @rx.event
    def set_plan_pelaksana_tipe(self, val: str) -> None:
        self.plan_pelaksana_tipe = val
        self.massal_pic = "Teknisi AC" if val == "Vendor" else "Ridho"

    @rx.event
    def set_massal_pic(self, val: str) -> None:
        self.massal_pic = val

    @rx.event
    def toggle_plan_reminder(self, rem: str) -> None:
        if rem in self.plan_reminders:
            self.plan_reminders = [r for r in self.plan_reminders if r != rem]
        else:
            self.plan_reminders = [*self.plan_reminders, rem]

    @rx.event
    async def submit_massal(self) -> rx.event.EventSpec:
        int_val = int(self.plan_interval_nilai or "3")
        next_dt = add_interval_clamped(
            self.massal_tgl_mulai or date.today().isoformat(),
            int_val,
            self.plan_interval_satuan,
        )
        new_id = f"MP-{len(MOCK_MAINTENANCE_PLANS) + 1:03d}"
        is_grp = self.plan_objek_tipe == "Kelompok aset"
        obj_teks = (
            f"{self.massal_kategori} · {self.plan_lokasi} · {self.plan_ruangan}"
            if is_grp
            else f"{self.plan_lokasi} · {self.plan_ruangan}"
        )
        tpl = MAINTENANCE_TEMPLATES.get(self.plan_template, {})
        MOCK_MAINTENANCE_PLANS.insert(
            0,
            {
                "id": new_id,
                "objek_tipe": "kelompok" if is_grp else "aset",
                "objek_asset_id": "" if is_grp else self.plan_asset_id,
                "objek_teks": obj_teks,
                "kategori_chip": (
                    self.massal_kategori
                    if self.massal_kategori != "PC"
                    else "PC & Server"
                ),
                "lokasi": self.plan_lokasi,
                "ruangan": self.plan_ruangan,
                "jumlah_unit": self.plan_detected_units if is_grp else 1,
                "unit_list": (
                    [f"{self.massal_kategori} {i + 1}" for i in range(self.plan_detected_units)]
                    if is_grp
                    else [self.plan_asset_id]
                ),
                "jenis": self.massal_jenis,
                "kegiatan": self.massal_kegiatan,
                "frekuensi": f"Tiap {int_val} {self.plan_interval_satuan}",
                "interval_nilai": int_val,
                "interval_satuan": self.plan_interval_satuan,
                "hitung_dari": "tanggal_selesai",
                "terakhir_dilakukan": self.massal_tgl_mulai,
                "terakhir_hasil": format_date_short_id(self.massal_tgl_mulai),
                "jadwal_berikutnya": next_dt.strftime("%Y-%m-%d"),
                "pelaksana_tipe": self.plan_pelaksana_tipe,
                "pic": self.massal_pic,
                "checklist": list(
                    tpl.get("checklist") or ["Cek kondisi fisik", "Uji operasional"]
                ),
                "catatan": f"{self.plan_detected_units} unit",
            },
        )
        self.is_massal_open = False
        await self._fetch_current_tab()
        return rx.toast("Rencana maintenance berhasil disimpan & dijadwalkan.")

    # --- HANDLERS MODAL 2: TANDAI SELESAI (ARTBOARD 14 KANAN) ---

    @rx.event
    def open_tandai_selesai(self, plan: dict[str, Any]) -> None:
        self.selesai_plan_id = str(plan.get("id", ""))
        self.selesai_plan_title = (
            f"{plan.get('kegiatan', '')} · {plan.get('objek_display', '')}"
        )
        u_list = list(plan.get("unit_list") or [])
        if not u_list:
            jml = int(plan.get("jumlah_unit") or 1)
            u_list = (
                [f"AC {i + 1}" for i in range(jml)]
                if jml > 1
                else [str(plan.get("objek_display", "Unit 1"))]
            )
        self.selesai_is_group = len(u_list) > 1 or plan.get("objek_tipe") == "kelompok"
        self.selesai_all_units = u_list
        self.selesai_checked_units = list(u_list)
        self.selesai_tgl = date.today().strftime("%Y-%m-%d")
        self.selesai_pelaksana_tipe = str(plan.get("pelaksana_tipe") or "Internal")
        self.selesai_pic = str(plan.get("pic") or "Ridho")
        self.selesai_biaya = ""
        chk = list(
            plan.get("checklist")
            or [
                "Cuci indoor",
                "Cuci outdoor",
                "Cek freon / tekanan",
                "Cek saluran pembuangan",
            ]
        )
        self.selesai_checklist_options = chk
        self.selesai_checked_items = chk[:-1] if len(chk) > 1 else chk
        self.selesai_hasil = "Normal"
        self.selesai_catatan = ""
        self.selesai_ada_temuan = False
        self.selesai_interval_nilai = int(plan.get("interval_nilai") or 3)
        self.selesai_interval_satuan = str(plan.get("interval_satuan") or "bulan")
        self.is_selesai_open = True

    @rx.event
    def close_tandai_selesai(self) -> None:
        self.is_selesai_open = False

    @rx.event
    def toggle_selesai_unit(self, unit_name: str, _checked: Any = None) -> None:
        if unit_name in self.selesai_checked_units:
            self.selesai_checked_units = [
                u for u in self.selesai_checked_units if u != unit_name
            ]
        else:
            self.selesai_checked_units = [*self.selesai_checked_units, unit_name]

    @rx.event
    def toggle_selesai_checklist(self, item_label: str, _checked: Any = None) -> None:
        if item_label in self.selesai_checked_items:
            self.selesai_checked_items = [
                x for x in self.selesai_checked_items if x != item_label
            ]
        else:
            self.selesai_checked_items = [*self.selesai_checked_items, item_label]

    @rx.event
    def set_selesai_tgl(self, val: str) -> None:
        self.selesai_tgl = val

    @rx.event
    def set_selesai_pelaksana_tipe(self, val: str) -> None:
        self.selesai_pelaksana_tipe = val
        self.selesai_pic = "Teknisi AC" if val == "Vendor" else "Ridho"

    @rx.event
    def set_selesai_pic(self, val: str) -> None:
        self.selesai_pic = val

    @rx.event
    def set_selesai_biaya(self, val: str) -> None:
        self.selesai_biaya = val

    @rx.event
    def set_selesai_hasil(self, val: str) -> None:
        self.selesai_hasil = val

    @rx.event
    def set_selesai_catatan(self, val: str) -> None:
        self.selesai_catatan = val

    @rx.event
    def toggle_selesai_ada_temuan(self, _checked: Any = None) -> None:
        self.selesai_ada_temuan = not self.selesai_ada_temuan
        self.selesai_hasil = "Perlu tindak lanjut" if self.selesai_ada_temuan else "Normal"

    @rx.event
    async def submit_tandai_selesai(self) -> rx.event.EventSpec | None:
        if not self.selesai_plan_id:
            return None
        from itam_pro.services.mock.maintenance_mock import action_tandai_selesai

        raw_biaya = "".join(ch for ch in (self.selesai_biaya or "") if ch.isdigit())
        biaya_int = int(raw_biaya) if raw_biaya else 0
        action_tandai_selesai(
            plan_id=self.selesai_plan_id,
            tgl_selesai=self.selesai_tgl,
            hasil="Perlu tindak lanjut" if self.selesai_ada_temuan else self.selesai_hasil,
            catatan=self.selesai_catatan,
            pic=self.selesai_pic,
            biaya=biaya_int,
            pelaksana_tipe=self.selesai_pelaksana_tipe,
            unit_dikerjakan=self.selesai_checked_units,
            ada_temuan=self.selesai_ada_temuan,
            checklist_hasil=self.selesai_checked_items,
        )
        self.is_selesai_open = False
        await self._fetch_current_tab()
        return rx.toast("Maintenance selesai dicatat & jadwal berikutnya telah diperbarui.")

    # --- HANDLERS MODAL 3: IMPORT CSV AC DARI GOOGLE SHEET ---

    @rx.event
    def open_import_ac_modal(self) -> None:
        self.run_import_ac_preview()
        self.is_import_ac_open = True

    @rx.event
    def close_import_ac_modal(self) -> None:
        self.is_import_ac_open = False

    @rx.event
    def set_import_ac_csv_text(self, val: str) -> None:
        self.import_ac_csv_text = val

    @rx.event
    def run_import_ac_preview(self) -> None:
        reader = list(csv.DictReader(io.StringIO(self.import_ac_csv_text.strip())))
        valid: list[dict[str, Any]] = []
        errs: list[dict[str, Any]] = []
        for idx, r in enumerate(reader, start=2):
            norm = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
            lok = norm.get("lokasi") or ""
            rng = norm.get("jenis ruangan") or norm.get("ruangan") or ""
            jml = int(norm.get("jumlah ac") or "1")
            tgl_raw = norm.get("tanggal cuci terakhir") or ""
            int_bln = int(norm.get("interval (bulan)") or "3")
            d_last = parse_date_flexible(tgl_raw)
            if not lok or not rng or d_last is None:
                errs.append(
                    {"row": idx, "reason": f"Baris {idx}: format tanggal/lokasi tidak valid"}
                )
                continue
            d_next = add_interval_clamped(d_last, int_bln, "bulan")
            valid.append(
                {
                    "lokasi": lok,
                    "ruangan": rng,
                    "jumlah_unit": jml,
                    "last_done": d_last.strftime("%Y-%m-%d"),
                    "interval_bulan": int_bln,
                    "next_due": d_next.strftime("%Y-%m-%d"),
                    "next_due_display": format_date_short_id(d_next.strftime("%Y-%m-%d")),
                }
            )
        self.import_ac_preview_rows = valid
        self.import_ac_errors = errs

    @rx.event
    async def commit_import_ac_csv(self) -> rx.event.EventSpec:
        for r in self.import_ac_preview_rows:
            new_id = f"MP-AC-{len(MOCK_MAINTENANCE_PLANS) + 1:02d}"
            jml = int(r["jumlah_unit"])
            MOCK_MAINTENANCE_PLANS.insert(
                0,
                {
                    "id": new_id,
                    "objek_tipe": "kelompok",
                    "objek_asset_id": "",
                    "objek_teks": f"AC · {r['lokasi']} · {r['ruangan']}",
                    "kategori_chip": "AC",
                    "lokasi": r["lokasi"],
                    "ruangan": r["ruangan"],
                    "jumlah_unit": jml,
                    "unit_list": [f"AC {i + 1}" for i in range(jml)],
                    "jenis": "Preventif",
                    "kegiatan": "Cuci AC (cleaning)",
                    "frekuensi": f"Tiap {r['interval_bulan']} bulan",
                    "interval_nilai": int(r["interval_bulan"]),
                    "interval_satuan": "bulan",
                    "hitung_dari": "tanggal_selesai",
                    "terakhir_dilakukan": r["last_done"],
                    "terakhir_hasil": format_date_short_id(r["last_done"]),
                    "jadwal_berikutnya": r["next_due"],
                    "pelaksana_tipe": "Vendor",
                    "pic": "Teknisi AC",
                    "checklist": [
                        "Cuci indoor",
                        "Cuci outdoor",
                        "Cek freon / tekanan",
                        "Cek saluran pembuangan",
                    ],
                    "catatan": f"{jml} unit",
                },
            )
        self.is_import_ac_open = False
        await self._fetch_current_tab()
        return rx.toast(
            f"Berhasil mengimpor {len(self.import_ac_preview_rows)} rencana AC dari CSV."
        )
