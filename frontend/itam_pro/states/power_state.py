"""
State Management untuk Halaman Laporan -> Rekap Watt Server (/watt-server).
Mode Tabel Rekap Manual sesuai spreadsheet docs/data/rekap_watt_server.csv.
"""

import re
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.audit_mock import query_audit_logs
from itam_pro.services.power_service import (
    _compact_cpu,
    _compact_gpu,
    _compact_ram_storage,
    calculate_ups_load_pct,
    classify_tdp_psu_status,
)


def _fmt_ribuan(val: int | float) -> str:
    """Format angka ribuan menggunakan titik (contoh: 3104 -> '3.104')."""
    return f"{round(val):,}".replace(",", ".")


def _norm_server_token(text: str) -> str:
    """Normalisasi nama server untuk pencocokan relasi UPS yang toleran variasi label."""
    cleaned = re.sub(r"[^A-Z0-9]+", " ", (text or "").upper()).strip()
    cleaned = cleaned.replace("OTOMAX", "OTO")
    cleaned = re.sub(r"^MENYUPLAI\s+", "", cleaned)
    cleaned = re.sub(r"^SERVER\s+", "", cleaned)
    return cleaned.strip()


def _build_ups_fallback_lookup(
    raw_items: list[dict[str, Any]],
    ups_items: list[dict[str, Any]],
    power_factor: float = 0.6,
) -> dict[str, dict[str, Any]]:
    """Bangun peta id_aset server -> info UPS dari ups_items sebagai fallback live backend."""
    lookup: dict[str, dict[str, Any]] = {}
    if not ups_items:
        return lookup

    srv_by_id = {
        str(s.get("id_aset", "")).strip().upper(): s
        for s in raw_items
        if str(s.get("id_aset", "")).strip()
    }
    srv_tokens = [
        (
            str(s.get("id_aset", "")).strip().upper(),
            _norm_server_token(str(s.get("nama_aset", ""))),
            int(s.get("tdp_total_w") or s.get("watt") or 0),
        )
        for s in raw_items
        if str(s.get("id_aset", "")).strip()
    ]
    ignore_targets = {
        "",
        "BACKUP",
        "RAK JARINGAN",
        "SYNOLOGY",
        "PC OWNER",
        "PC SUPERVISOR OPERASIONAL",
    }

    for u in ups_items:
        u_id = str(u.get("id_aset", "")).strip().upper()
        if not u_id:
            continue
        cap_w = int(u.get("kapasitas_watt") or 0)
        if cap_w <= 0:
            va = int(u.get("kapasitas_va") or 650)
            cap_w = max(1, round(va * power_factor))

        matched_ids: list[str] = []
        for sid in list(u.get("linked_server_ids") or []):
            sid_u = str(sid).strip().upper()
            if sid_u in srv_by_id and sid_u not in matched_ids:
                matched_ids.append(sid_u)

        if not matched_ids:
            for sname in list(u.get("linked_servers") or []):
                tok = _norm_server_token(str(sname))
                for sid_u, srv_tok, _ in srv_tokens:
                    if (
                        tok
                        and srv_tok
                        and (tok == srv_tok or srv_tok in tok)
                        and sid_u not in matched_ids
                    ):
                        matched_ids.append(sid_u)

        if not matched_ids:
            raw_target = _norm_server_token(
                str(u.get("beban_perangkat") or u.get("digunakan_oleh") or "")
            )
            if raw_target and raw_target not in ignore_targets:
                for sid_u, srv_tok, _ in srv_tokens:
                    if sid_u in raw_target or (srv_tok and srv_tok in raw_target):
                        if sid_u not in matched_ids:
                            matched_ids.append(sid_u)

        if not matched_ids:
            continue

        pct = float(u.get("utilisasi_pct") or 0.0)
        if pct <= 0:
            total_load = sum(
                int(srv_by_id[sid].get("tdp_total_w") or srv_by_id[sid].get("watt") or 0)
                for sid in matched_ids
                if sid in srv_by_id
            )
            pct = calculate_ups_load_pct(total_load, cap_w)

        info = {
            "ups_id_aset": u_id,
            "ups_utilisasi_pct": pct,
            "ups_nama": str(u.get("nama_aset") or u.get("merek_va") or u_id),
        }
        for sid in matched_ids:
            lookup.setdefault(sid, info)

    return lookup


def _normalize_power_row(
    raw: dict[str, Any],
    idx: int,
    ups_fallback: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Normalisasi satu baris server agar field UI lengkap untuk mode Mock maupun Backend."""
    row = dict(raw)
    id_aset = str(row.get("id_aset") or row.get("id") or "").strip()
    row["id"] = id_aset or str(row.get("id") or idx)
    row["id_aset"] = id_aset
    row["no"] = str(idx)

    tdp_val = int(row.get("tdp_total_w") or row.get("watt") or 0)
    min_val = int(row.get("psu_min_w") or 0)
    rek_val = int(row.get("psu_rekomendasi_w") or 0)
    row["tdp_total_w"] = tdp_val
    row["psu_min_w"] = min_val
    row["psu_rekomendasi_w"] = rek_val
    row["tdp_num_display"] = _fmt_ribuan(tdp_val)
    row["psu_min_num_display"] = _fmt_ribuan(min_val)
    row["psu_rek_num_display"] = _fmt_ribuan(rek_val)

    cpu_full = str(row.get("cpu") or row.get("processor") or "—").strip() or "—"
    vga_full = str(row.get("vga") or row.get("gpu") or "—").strip() or "—"
    ram_full = str(row.get("ram") or "—").strip() or "—"
    hdd_full = str(row.get("hdd_ssd") or row.get("storage") or "—").strip() or "—"
    row["cpu"] = cpu_full
    row["vga"] = vga_full
    row["ram"] = ram_full
    row["hdd_ssd"] = hdd_full
    row["cpu_short"] = _compact_cpu(cpu_full)
    row["vga_short"] = _compact_gpu(vga_full)
    row["ram_storage_short"] = _compact_ram_storage(ram_full, hdd_full)

    # Hitung ulang rasio TDP / PSU Min secara deterministik (perbaiki bar kosong di live backend)
    ratio_info = classify_tdp_psu_status(tdp_val, min_val)
    row["tdp_psu_ratio_pct"] = ratio_info["ratio_pct"]
    row["tdp_psu_bar_width"] = ratio_info["bar_width"]
    row["power_status"] = ratio_info["status"]
    row["power_status_label"] = ratio_info["label"]
    row["power_status_variant"] = ratio_info["variant"]

    # Relasi UPS Penyuplai (prioritas field row, fallback ke ups_items backend)
    u_id = str(row.get("ups_id_aset") or "").strip().upper()
    u_pct = float(row.get("ups_utilisasi_pct") or 0.0)
    if not u_id and id_aset.upper() in ups_fallback:
        fb = ups_fallback[id_aset.upper()]
        u_id = str(fb.get("ups_id_aset") or "")
        u_pct = float(fb.get("ups_utilisasi_pct") or 0.0)

    row["ups_id_aset"] = u_id
    row["ups_utilisasi_pct"] = u_pct
    row["has_ups"] = bool(u_id)
    row["ups_chip_label"] = f"{u_id} · {round(u_pct)}%" if u_id else "Belum ditautkan"

    if not row.get("kwh_display"):
        kwh_val = round((tdp_val * 24 * 30) / 1000.0, 1)
        row["kwh_display"] = f"{str(kwh_val).replace('.', ',')} kWh"

    return row


class PowerState(rx.State):
    """State Rekap Watt Server: tabel manual, pencarian, sort, baris ESTIMASI, dan CRUD."""

    items: list[dict[str, Any]] = []
    all_servers_cache: list[dict[str, Any]] = []
    total_items: int = 0
    overall_total_servers: int = 16
    page: int = 1
    page_size: int = 25
    is_loading: bool = False

    # Pencarian & Pengurutan
    search_query: str = ""
    sort_by: str = ""
    sort_dir: str = "asc"

    # Ringkasan Baris ESTIMASI (Filtered & Keseluruhan)
    estimasi_tdp_display: str = "3.104"
    estimasi_psu_min_display: str = "4.600"
    estimasi_psu_rek_display: str = "6.150"
    overall_tdp_display: str = "3.104"
    overall_psu_min_display: str = "4.600"
    overall_psu_rek_display: str = "6.150"

    # Filter Status, UPS, & Atur Kolom
    status_filter: str = ""
    ups_filter: str = ""
    ups_options: list[str] = ["Belum ditautkan"]
    hidden_columns: list[str] = []

    # 5 Kartu KPI
    kpi_total_tdp_display: str = "3.104 W"
    kpi_total_tdp_note: str = "dari 16 server"
    kpi_tdp_psu_pct: int = 67
    kpi_psu_min_display: str = "4.600 W"
    kpi_psu_min_note: str = "total seluruh server"
    kpi_psu_rek_display: str = "6.150 W"
    kpi_est_kwh_display: str = "2.235 kWh"
    kpi_max_tdp_display: str = "211 W"
    kpi_max_tdp_server: str = "—"
    kpi_max_tdp_id: str = ""

    # Detail Drawer Server
    drawer_open: bool = False
    selected_server: dict[str, Any] = {}
    selected_edit_history: list[dict[str, Any]] = []

    # Modal Form Tambah / Edit Server Manual
    form_modal_open: bool = False
    form_mode: str = "add"  # "add" | "edit" | "duplicate"
    form_id_aset: str = ""
    form_nama_aset: str = ""
    form_cpu: str = ""
    form_vga: str = ""
    form_ram: str = ""
    form_hdd_ssd: str = ""
    form_tdp_w: str = "0"
    form_psu_min_w: str = "0"
    form_psu_rek_w: str = "0"
    form_catatan: str = ""

    # Pesan Error Inline per Field
    form_error: str = ""
    form_nama_error: str = ""
    form_cpu_error: str = ""
    form_tdp_error: str = ""
    form_psu_min_error: str = ""
    form_psu_rek_error: str = ""

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    delete_target_id: str = ""
    delete_target_nama: str = ""

    # --- COMPUTED VARS ---
    @rx.var(cache=True)
    def is_edit_mode(self) -> bool:
        return self.form_mode == "edit"

    @rx.var(cache=True)
    def has_search(self) -> bool:
        return bool(self.search_query.strip() or self.status_filter or self.ups_filter)

    @rx.var(cache=True)
    def status_options(self) -> list[str]:
        return ["Aman", "Waspada", "Kritis"]

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} server"

    @rx.var(cache=True)
    def estimasi_search_subnote(self) -> str:
        if not self.has_search:
            return f"Total dari {self.total_items} server"
        return f"{self.total_items} dari {self.overall_total_servers} server"

    @rx.var(cache=True)
    def delete_target_label(self) -> str:
        return f"{self.delete_target_nama} ({self.delete_target_id})"

    @rx.var(cache=True)
    def selected_id_aset(self) -> str:
        return str(self.selected_server.get("id_aset", ""))

    @rx.var(cache=True)
    def selected_nama_aset(self) -> str:
        return str(self.selected_server.get("nama_aset", ""))

    @rx.var(cache=True)
    def selected_cpu(self) -> str:
        return str(self.selected_server.get("cpu", "—"))

    @rx.var(cache=True)
    def selected_vga(self) -> str:
        return str(self.selected_server.get("vga", "—"))

    @rx.var(cache=True)
    def selected_ram(self) -> str:
        return str(self.selected_server.get("ram", "—"))

    @rx.var(cache=True)
    def selected_hdd_ssd(self) -> str:
        return str(self.selected_server.get("hdd_ssd", "—"))

    @rx.var(cache=True)
    def selected_tdp_display(self) -> str:
        return f"{self.selected_server.get('tdp_num_display', '0')} W"

    @rx.var(cache=True)
    def selected_psu_min_display(self) -> str:
        return f"{self.selected_server.get('psu_min_num_display', '0')} W"

    @rx.var(cache=True)
    def selected_psu_rek_display(self) -> str:
        return f"{self.selected_server.get('psu_rek_num_display', '0')} W"

    @rx.var(cache=True)
    def selected_tdp_psu_ratio_display(self) -> str:
        return f"{self.selected_server.get('tdp_psu_ratio_pct', 0)}%"

    @rx.var(cache=True)
    def selected_power_status_label(self) -> str:
        return str(self.selected_server.get("power_status_label", "Aman"))

    @rx.var(cache=True)
    def selected_power_status_variant(self) -> str:
        return str(self.selected_server.get("power_status_variant", "success"))

    @rx.var(cache=True)
    def selected_kwh_display(self) -> str:
        return str(self.selected_server.get("kwh_display", "0 kWh"))

    @rx.var(cache=True)
    def selected_ups_chip_label(self) -> str:
        return str(self.selected_server.get("ups_chip_label", "Belum ditautkan"))

    @rx.var(cache=True)
    def selected_lokasi(self) -> str:
        return str(self.selected_server.get("lokasi", "—"))

    @rx.var(cache=True)
    def selected_catatan(self) -> str:
        return str(self.selected_server.get("catatan", "—"))

    @rx.var(cache=True)
    def has_edit_history(self) -> bool:
        return len(self.selected_edit_history) > 0

    # --- EVENT HANDLERS UTAMA ---
    @rx.event
    async def load_power_page(self) -> None:
        """Muat data saat halaman /watt-server dibuka."""
        await self.fetch_power_data()

    @rx.event
    async def fetch_power_data(self) -> None:
        self.is_loading = True
        try:
            filters = {
                "scope": "server",
                "search": self.search_query.strip(),
                "sort_by": (
                    "" if self.sort_by == "tdp_psu_ratio_pct" else self.sort_by
                ),
                "sort_dir": self.sort_dir,
            }
            res = await api_client.get_server_power(
                filters=filters,
                page=1,
                page_size=max(self.page_size, 100),
            )
            raw_items = list(res.get("items") or [])
            ups_items = list(res.get("ups_items") or [])
            asmp = res.get("assumptions") or {}
            pf = float(asmp.get("faktor_daya_ups") or 0.6)

            ups_fallback = _build_ups_fallback_lookup(raw_items, ups_items, power_factor=pf)
            normalized_all = [
                _normalize_power_row(it, idx, ups_fallback)
                for idx, it in enumerate(raw_items, start=1)
            ]

            if not self.search_query.strip():
                self.all_servers_cache = list(normalized_all)
                linked_ups = sorted(
                    {
                        str(x["ups_id_aset"])
                        for x in normalized_all
                        if str(x.get("ups_id_aset") or "").strip()
                    }
                )
                self.ups_options = ["Belum ditautkan", *linked_ups]

            # Terapkan filter Status & UPS di sisi state (bekerja identik di mock & live backend)
            filtered = normalized_all
            if self.status_filter and self.status_filter not in ("Semua", "Semua status"):
                st_low = self.status_filter.lower()
                filtered = [x for x in filtered if str(x.get("power_status", "")).lower() == st_low]
            if self.ups_filter and self.ups_filter not in ("Semua", "Semua UPS"):
                if self.ups_filter.lower() == "belum ditautkan":
                    filtered = [x for x in filtered if not x.get("has_ups")]
                else:
                    u_target = self.ups_filter.upper()
                    filtered = [
                        x for x in filtered if str(x.get("ups_id_aset", "")).upper() == u_target
                    ]

            if self.sort_by == "tdp_psu_ratio_pct":
                filtered = sorted(
                    filtered,
                    key=lambda x: int(x.get("tdp_psu_ratio_pct") or 0),
                    reverse=(self.sort_dir == "desc"),
                )

            for idx, row in enumerate(filtered, start=1):
                row["no"] = str(idx)

            self.items = filtered
            self.total_items = len(filtered)

            # Hitung agregasi KPI & ESTIMASI langsung dari kolom TDP/PSU baris tampil
            tdp_sum = sum(int(x["tdp_total_w"]) for x in filtered)
            min_sum = sum(int(x["psu_min_w"]) for x in filtered)
            rek_sum = sum(int(x["psu_rekomendasi_w"]) for x in filtered)
            est_kwh = round((tdp_sum * 24 * 30) / 1000.0)

            highest_srv = max(filtered, key=lambda x: int(x["tdp_total_w"]), default=None)
            max_tdp = int(highest_srv["tdp_total_w"]) if highest_srv else 0
            max_srv = str(highest_srv["nama_aset"]) if highest_srv else "—"
            max_srv_id = str(highest_srv["id_aset"]) if highest_srv else ""

            ov_pool = self.all_servers_cache or normalized_all
            ov_cnt = len(ov_pool) or self.total_items
            ov_tdp = sum(int(x["tdp_total_w"]) for x in ov_pool)
            ov_min = sum(int(x["psu_min_w"]) for x in ov_pool)
            ov_rek = sum(int(x["psu_rekomendasi_w"]) for x in ov_pool)

            self.overall_total_servers = ov_cnt
            self.estimasi_tdp_display = _fmt_ribuan(tdp_sum)
            self.estimasi_psu_min_display = _fmt_ribuan(min_sum)
            self.estimasi_psu_rek_display = _fmt_ribuan(rek_sum)
            self.overall_tdp_display = _fmt_ribuan(ov_tdp)
            self.overall_psu_min_display = _fmt_ribuan(ov_min)
            self.overall_psu_rek_display = _fmt_ribuan(ov_rek)

            # Update 5 KPI cards + donut % TDP terhadap PSU minimum
            self.kpi_total_tdp_display = f"{_fmt_ribuan(tdp_sum)} W"
            self.kpi_total_tdp_note = f"dari {self.total_items} server"
            self.kpi_tdp_psu_pct = (
                min(100, round((tdp_sum / min_sum) * 100)) if min_sum > 0 else 0
            )
            self.kpi_psu_min_display = f"{_fmt_ribuan(min_sum)} W"
            self.kpi_psu_min_note = (
                "total filter aktif" if self.has_search else "total seluruh server"
            )
            self.kpi_psu_rek_display = f"{_fmt_ribuan(rek_sum)} W"
            self.kpi_est_kwh_display = f"{_fmt_ribuan(est_kwh)} kWh"
            self.kpi_max_tdp_display = f"{_fmt_ribuan(max_tdp)} W"
            self.kpi_max_tdp_server = max_srv
            self.kpi_max_tdp_id = max_srv_id

            if self.drawer_open and self.selected_id_aset:
                updated_sel = next(
                    (x for x in filtered if x["id_aset"] == self.selected_id_aset),
                    None,
                )
                if updated_sel:
                    self.selected_server = dict(updated_sel)
                    await self._load_selected_history(self.selected_id_aset)
        finally:
            self.is_loading = False

    # --- HANDLERS PENCARIAN, FILTER, ATUR KOLOM, SORT, & EXPORT ---
    @rx.event
    async def set_search_query(self, query: str) -> None:
        if self.search_query == query:
            return
        self.search_query = query
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Semua status") else val
        if self.status_filter == clean:
            return
        self.status_filter = clean
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_ups_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Semua UPS") else val
        if self.ups_filter == clean:
            return
        self.ups_filter = clean
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.status_filter = ""
        self.ups_filter = ""
        self.sort_by = ""
        self.sort_dir = "asc"
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    def toggle_column_visibility(self, col_key: str, _checked: Any = None) -> None:
        if col_key in self.hidden_columns:
            self.hidden_columns = [k for k in self.hidden_columns if k != col_key]
        else:
            self.hidden_columns = [*self.hidden_columns, col_key]

    @rx.event
    def reset_column_visibility(self) -> None:
        self.hidden_columns = []

    @rx.event
    async def toggle_sort(self, col_key: str) -> None:
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        await self.fetch_power_data()

    @rx.event
    async def export_watt_excel(self) -> Any:
        data_bytes = await api_client.generate_watt_excel_bytes(self.items)
        return rx.download(data=data_bytes, filename="Rekap_Watt_Server_ITAM_Pro.xlsx")

    # --- HANDLERS DETAIL DRAWER ---
    async def _load_selected_history(self, asset_id: str) -> None:
        """Ambil riwayat pengeditan server dari Audit Log (mock & live backend)."""
        # TODO(backend): ganti dengan GET /api/v1/power/servers/{id}/history saat tersedia.
        if USE_MOCK:
            res = query_audit_logs(
                filters={"search": asset_id, "hide_login_success": "false", "group": "false"},
                page=1,
                page_size=10,
            )
        else:
            try:
                res = await api_client.get_audit_logs(
                    filters={"search": asset_id}, page=1, page_size=10
                )
            except Exception:
                res = {"items": []}

        history: list[dict[str, Any]] = []
        for item in res.get("items", []):
            tgt = str(item.get("target_id", "")).upper()
            if tgt == asset_id.upper() or asset_id.upper() in str(item.get("detail", "")).upper():
                history.append(
                    {
                        "id": str(item.get("kode_audit") or item.get("id") or ""),
                        "waktu": str(item.get("waktu_wib") or item.get("timestamp") or "—"),
                        "pelaku": str(item.get("nama_pengguna") or item.get("actor") or "—"),
                        "detail": str(item.get("detail", "")),
                    }
                )
        self.selected_edit_history = history

    @rx.event
    async def open_detail_drawer(self, row_id: str) -> None:
        target = next(
            (x for x in self.items if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.selected_server = dict(target)
        await self._load_selected_history(str(target["id_aset"]))
        self.drawer_open = True

    @rx.event
    async def open_highest_tdp_drawer(self) -> None:
        """Buka detail drawer server dengan TDP tertinggi saat kartu KPI ke-5 diklik."""
        if self.kpi_max_tdp_id:
            await self.open_detail_drawer(self.kpi_max_tdp_id)

    @rx.event
    def close_detail_drawer(self) -> None:
        self.drawer_open = False

    @rx.event
    def open_edit_from_drawer(self) -> None:
        if self.selected_id_aset:
            self.open_edit_modal(self.selected_id_aset)

    @rx.event
    def open_duplicate_from_drawer(self) -> None:
        if self.selected_id_aset:
            self.open_duplicate_modal(self.selected_id_aset)

    @rx.event
    def confirm_delete_from_drawer(self) -> None:
        if self.selected_id_aset:
            self.drawer_open = False
            self.confirm_delete_entry(self.selected_id_aset)

    # --- HANDLERS FORM TAMBAH / EDIT SERVER MANUAL ---
    def _clear_form_errors(self) -> None:
        self.form_error = ""
        self.form_nama_error = ""
        self.form_cpu_error = ""
        self.form_tdp_error = ""
        self.form_psu_min_error = ""
        self.form_psu_rek_error = ""

    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self._clear_form_errors()
        self.form_id_aset = ""
        self.form_nama_aset = ""
        self.form_cpu = ""
        self.form_vga = ""
        self.form_ram = ""
        self.form_hdd_ssd = ""
        self.form_tdp_w = "159"
        self.form_psu_min_w = "250"
        self.form_psu_rek_w = "350"
        self.form_catatan = ""
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        target = next(
            (x for x in self.items if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.form_mode = "edit"
        self._clear_form_errors()
        self.form_id_aset = str(target["id_aset"])
        self.form_nama_aset = str(target["nama_aset"])
        self.form_cpu = "" if target.get("cpu") == "—" else str(target.get("cpu", ""))
        self.form_vga = "" if target.get("vga") == "—" else str(target.get("vga", ""))
        self.form_ram = "" if target.get("ram") == "—" else str(target.get("ram", ""))
        self.form_hdd_ssd = (
            "" if target.get("hdd_ssd") == "—" else str(target.get("hdd_ssd", ""))
        )
        self.form_tdp_w = str(target.get("tdp_total_w", 0))
        self.form_psu_min_w = str(target.get("psu_min_w", 0))
        self.form_psu_rek_w = str(target.get("psu_rekomendasi_w", 0))
        self.form_catatan = (
            "" if target.get("catatan") == "—" else str(target.get("catatan", ""))
        )
        self.form_modal_open = True

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        target = next(
            (x for x in self.items if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.form_mode = "duplicate"
        self._clear_form_errors()
        self.form_id_aset = ""
        self.form_nama_aset = f"{target['nama_aset']} COPY"
        self.form_cpu = "" if target.get("cpu") == "—" else str(target.get("cpu", ""))
        self.form_vga = "" if target.get("vga") == "—" else str(target.get("vga", ""))
        self.form_ram = "" if target.get("ram") == "—" else str(target.get("ram", ""))
        self.form_hdd_ssd = (
            "" if target.get("hdd_ssd") == "—" else str(target.get("hdd_ssd", ""))
        )
        self.form_tdp_w = str(target.get("tdp_total_w", 0))
        self.form_psu_min_w = str(target.get("psu_min_w", 0))
        self.form_psu_rek_w = str(target.get("psu_rekomendasi_w", 0))
        self.form_catatan = (
            "" if target.get("catatan") == "—" else str(target.get("catatan", ""))
        )
        self.form_modal_open = True

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self._clear_form_errors()

    @rx.event
    def set_form_nama_aset(self, val: str) -> None:
        self.form_nama_aset = val
        self.form_nama_error = ""

    @rx.event
    def set_form_cpu(self, val: str) -> None:
        self.form_cpu = val
        self.form_cpu_error = ""

    @rx.event
    def set_form_vga(self, val: str) -> None:
        self.form_vga = val

    @rx.event
    def set_form_ram(self, val: str) -> None:
        self.form_ram = val

    @rx.event
    def set_form_hdd_ssd(self, val: str) -> None:
        self.form_hdd_ssd = val

    @rx.event
    def set_form_tdp_w(self, val: str) -> None:
        self.form_tdp_w = val if val is not None else ""
        self.form_tdp_error = ""

    @rx.event
    def set_form_psu_min_w(self, val: str) -> None:
        self.form_psu_min_w = val if val is not None else ""
        self.form_psu_min_error = ""

    @rx.event
    def set_form_psu_rek_w(self, val: str) -> None:
        self.form_psu_rek_w = val if val is not None else ""
        self.form_psu_rek_error = ""

    @rx.event
    def set_form_catatan(self, val: str) -> None:
        self.form_catatan = val

    @rx.event
    async def submit_form(self) -> Any:
        self._clear_form_errors()
        nama_clean = self.form_nama_aset.strip()
        cpu_clean = self.form_cpu.strip()
        has_err = False

        if not nama_clean:
            self.form_nama_error = "ID Server wajib diisi (contoh: SERVER OTO H2H)."
            has_err = True
        else:
            pool = self.all_servers_cache or self.items
            for srv in pool:
                if (
                    str(srv.get("nama_aset", "")).strip().lower() == nama_clean.lower()
                    and (self.form_mode != "edit" or srv.get("id_aset") != self.form_id_aset)
                ):
                    self.form_nama_error = f"ID Server '{nama_clean}' sudah digunakan."
                    has_err = True
                    break

        if not cpu_clean:
            self.form_cpu_error = "Model Prosesor (CPU) wajib diisi."
            has_err = True

        tdp_val = 0
        psu_min_val = 0
        psu_rek_val = 0

        try:
            tdp_val = int(float((self.form_tdp_w or "0").strip()))
            if tdp_val < 0:
                self.form_tdp_error = "Total TDP (W) tidak boleh negatif."
                has_err = True
        except ValueError:
            self.form_tdp_error = "Masukkan angka bulat yang valid."
            has_err = True

        try:
            psu_min_val = int(float((self.form_psu_min_w or "0").strip() or "0"))
            if psu_min_val < 0:
                self.form_psu_min_error = "PSU Minimum tidak boleh negatif."
                has_err = True
        except ValueError:
            self.form_psu_min_error = "Masukkan angka bulat yang valid."
            has_err = True

        try:
            psu_rek_val = int(float((self.form_psu_rek_w or "0").strip() or "0"))
            if psu_rek_val < 0:
                self.form_psu_rek_error = "PSU Rekomendasi tidak boleh negatif."
                has_err = True
        except ValueError:
            self.form_psu_rek_error = "Masukkan angka bulat yang valid."
            has_err = True

        if (
            not self.form_psu_min_error
            and not self.form_psu_rek_error
            and psu_min_val > 0
            and psu_rek_val > 0
            and psu_rek_val < psu_min_val
        ):
            self.form_psu_rek_error = (
                "PSU rekomendasi tidak boleh lebih kecil dari PSU minimum."
            )
            has_err = True

        if has_err:
            return None

        payload = {
            "nama_aset": nama_clean,
            "cpu": cpu_clean,
            "vga": self.form_vga.strip(),
            "ram": self.form_ram.strip(),
            "hdd_ssd": self.form_hdd_ssd.strip(),
            "tdp_total_w": tdp_val,
            "psu_min_w": psu_min_val,
            "psu_rekomendasi_w": psu_rek_val,
            "catatan": self.form_catatan.strip(),
        }
        target_id = self.form_id_aset if self.form_mode == "edit" else ""
        try:
            await api_client.save_server_power(payload=payload, asset_id=target_id)
        except Exception as exc:
            self.form_error = str(exc)
            return None

        self.form_modal_open = False
        await self.fetch_power_data()
        return rx.toast.success("Data server berhasil disimpan.")

    # --- HANDLERS HAPUS SERVER ---
    @rx.event
    def confirm_delete_entry(self, row_id: str) -> None:
        target = next(
            (x for x in self.items if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.delete_target_id = str(target["id_aset"])
        self.delete_target_nama = str(target["nama_aset"])
        self.delete_dialog_open = True

    @rx.event
    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.delete_target_id = ""

    @rx.event
    async def execute_delete_entry(self) -> Any:
        if self.delete_target_id:
            await api_client.delete_server_power(self.delete_target_id)
        self.delete_dialog_open = False
        self.delete_target_id = ""
        await self.fetch_power_data()
        return rx.toast.success("Data server berhasil dihapus.")


__all__ = ["PowerState"]
