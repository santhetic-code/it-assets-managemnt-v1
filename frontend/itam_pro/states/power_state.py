"""
State Management untuk Halaman Infrastructure -> Rekap Watt Server (/watt-server).
Mendukung Artboard 15 (Rekap & Utilisasi UPS), 16 (Asumsi & Rincian),
17 (Kalkulator Watt Server), dan 18 (Katalog & Skenario).
"""

import json
import math
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.power_service import calculate_psu_specs, energi_kwh_bulan
from itam_pro.styles.colors import Color


def _fmt_ribuan(val: int | float) -> str:
    """Format angka ribuan menggunakan titik (contoh: 3104 -> '3.104')."""
    return f"{round(val):,}".replace(",", ".")


class PowerState(rx.State):
    """State lengkap Rekap Watt Server, Asumsi, Rincian, Kalkulator, dan Katalog."""

    # Navigasi Tab Utama Halaman (/watt-server): "rekap" | "kalkulator" | "katalog"
    main_section_tab: str = "rekap"

    # Data Tabel Rekap & Panel
    items: list[dict[str, Any]] = []
    top_servers_all: list[dict[str, Any]] = []
    show_all_ranked_servers: bool = False
    ups_items: list[dict[str, Any]] = []
    all_ups_options: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 20
    is_loading: bool = False

    # Cakupan & Filter Tabel Rekap
    active_tab: str = "Semua"
    scope_filter: str = "Server"
    active_kpi_filter: str = ""
    search_query: str = ""
    cpu_brand_filter: str = ""
    beban_filter: str = ""
    ups_filter: str = ""
    sort_by: str = ""
    sort_dir: str = "asc"

    # Preferensi Atur Kolom disimpan per pengguna di LocalStorage
    watt_col_prefs_json: str = rx.LocalStorage("[]", name="itam_watt_hidden_cols")

    @rx.var(cache=True)
    def hidden_columns(self) -> list[str]:
        try:
            cols = json.loads(self.watt_col_prefs_json or "[]")
            return [str(c) for c in cols] if isinstance(cols, list) else []
        except ValueError:
            return []

    tab_counts: dict[str, int] = {"Semua": 16, "Operasional": 11, "Backup": 5}

    # Pengaturan Asumsi Aktif (Artboard 16 Kiri)
    asmp_jam_per_hari: int = 24
    asmp_hari_per_bulan: int = 30
    asmp_faktor_beban: int = 100
    asmp_tarif_kwh: str = ""  # Kosong = sembunyikan semua angka rupiah
    asmp_faktor_daya_ups: str = "0,6"
    asmp_batas_waspada: int = 70
    asmp_batas_kritis: int = 85
    asmp_modal_open: bool = False
    asmp_error: str = ""

    # Ringkasan 5 Kartu KPI (Artboard 15)
    kpi_total_tdp_kw_display: str = "3,10 kW"
    kpi_total_tdp_sub: str = "16 server · rata-rata 194 W"
    kpi_kwh_month_display: str = "2.235 kWh"
    kpi_kwh_sub: str = "asumsi 24/7 (720 jam) · faktor beban 100%"
    kpi_biaya_month_display: str = ""
    kpi_psu_summary_display: str = "4.600 / 6.150 W"
    kpi_psu_sub: str = "total kapasitas yang disarankan"
    kpi_max_tdp_display: str = "300 W"
    kpi_max_tdp_server: str = "SERVER BACKUP REAL TIME"
    kpi_max_tdp_id: str = "SRV-014"
    kpi_ups_count_display: str = "6 UPS"
    kpi_ups_status_badge: str = "Aman"
    kpi_ups_sub: str = "terpantau · tertinggi 54% (perkiraan)"
    unfilled_ups_watt_count: int = 6
    psu_kurang_count: int = 0

    # Inline Edit Kapasitas Watt UPS pada Panel Kecukupan UPS
    inline_ups_edit_id: str = ""
    inline_ups_watt_val: str = ""

    # Panel Rincian Server & Simulasi Tambah Beban (Artboard 16 Kanan)
    drawer_open: bool = False
    drawer_tab: str = "detail"
    active_row_id: str = ""
    active_server: dict[str, Any] = {}
    active_komposisi_list: list[dict[str, Any]] = []
    sim_extra_watt: str = "50"

    # Modal Form Tambah / Edit Server Manual
    form_modal_open: bool = False
    form_mode: str = "add"
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
    form_error: str = ""

    # Dialog Konfirmasi Hapus
    delete_dialog_open: bool = False
    delete_target_id: str = ""
    delete_target_nama: str = ""

    @rx.var(cache=True)
    def is_edit_mode(self) -> bool:
        return self.form_mode == "edit"

    @rx.var(cache=True)
    def delete_target_label(self) -> str:
        return f"{self.delete_target_nama} ({self.delete_target_id})"

    # --- STATE KALKULATOR WATT SERVER (ARTBOARD 17) ---
    calc_start_mode: str = "rancang_baru"  # "server_ada" | "rancang_baru"
    calc_selected_server_id: str = "SRV-003"
    calc_load_mode: str = "dasar"  # "dasar" | "puncak"
    calc_cpu_name: str = "Intel Core i5-12400"
    calc_cpu_qty: int = 1
    calc_gpu_name: str = "Intel UHD Graphics (terpadu)"
    calc_gpu_qty: int = 1
    calc_mobo_name: str = "Desktop ATX"
    calc_mobo_qty: int = 1
    calc_ram_name: str = "RAM DDR4 per modul"
    calc_ram_qty: int = 4
    calc_ssd_sata_name: str = "SSD SATA 2,5 inci"
    calc_ssd_sata_qty: int = 3
    calc_nvme_name: str = "SSD NVMe M.2"
    calc_nvme_qty: int = 1
    calc_hdd_name: str = "HDD SATA 3,5 inci"
    calc_hdd_qty: int = 0
    calc_fan_name: str = "Kipas casing"
    calc_fan_qty: int = 3
    calc_optical_name: str = "Tanpa drive optik"
    calc_optical_qty: int = 0
    calc_pcie_name: str = "Tanpa kartu PCIe"
    calc_pcie_qty: int = 0
    calc_custom_label: str = "Isi watt manual"
    calc_custom_watt: int = 0
    calc_custom_qty: int = 0
    calc_selected_ups_id: str = "UPS-009"

    # Modal Simpan Skenario & Bandingkan Skenario (Artboard 18 Kanan)
    scenario_modal_open: bool = False
    scenario_name_input: str = ""
    compare_modal_open: bool = False
    scenarios_list: list[dict[str, Any]] = []

    # --- STATE KATALOG KOMPONEN ADMIN (ARTBOARD 18 KIRI) ---
    catalog_items: list[dict[str, Any]] = []
    catalog_search: str = ""
    catalog_kat_filter: str = "Semua"
    catalog_modal_open: bool = False
    catalog_edit_id: int = 0
    cat_form_kategori: str = "cpu"
    cat_form_nama: str = ""
    cat_form_merek: str = "Intel"
    cat_form_tdp_w: str = "65"
    cat_form_peak_w: str = ""
    cat_form_jenis_data: str = "resmi"
    cat_form_sumber: str = "Intel ARK"
    cat_form_catatan: str = ""

    # --- COMPUTED VARS: ASUMSI & FILTER ---
    @rx.var(cache=True)
    def has_tarif_listrik(self) -> bool:
        try:
            return bool(
                self.asmp_tarif_kwh.strip()
                and float(self.asmp_tarif_kwh.replace(",", ".")) > 0
            )
        except ValueError:
            return False

    @rx.var(cache=True)
    def asmp_total_jam_bulan(self) -> int:
        return self.asmp_jam_per_hari * self.asmp_hari_per_bulan

    @rx.var(cache=True)
    def assumptions_summary_bar(self) -> str:
        base = (
            f"Asumsi: {self.asmp_jam_per_hari}/7 ({self.asmp_total_jam_bulan} jam) · "
            f"faktor beban {self.asmp_faktor_beban}% · kapasitas UPS dari datasheet (diisi manual)"
        )
        if self.has_tarif_listrik:
            val = int(float(self.asmp_tarif_kwh.replace(",", ".")))
            return f"{base} · memakai tarif Rp {_fmt_ribuan(val)}/kWh"
        return base

    @rx.var(cache=True)
    def ranked_servers_display(self) -> list[dict[str, Any]]:
        if self.show_all_ranked_servers:
            return self.top_servers_all
        return self.top_servers_all[:8]

    @rx.var(cache=True)
    def hidden_ranked_count(self) -> int:
        return max(0, len(self.top_servers_all) - 8)

    @rx.var(cache=True)
    def cpu_brand_options(self) -> list[str]:
        return ["Intel", "AMD"]

    @rx.var(cache=True)
    def beban_options(self) -> list[str]:
        return ["Rendah", "Sedang", "Tinggi"]

    @rx.var(cache=True)
    def scope_options(self) -> list[str]:
        return ["Server", "PC Operasional", "Semua"]

    @rx.var(cache=True)
    def ups_filter_options(self) -> list[str]:
        return [str(u["id_aset"]) for u in self.ups_items if u.get("id_aset")]

    @rx.var(cache=True)
    def server_select_options(self) -> list[str]:
        return [f"{s['id_aset']} · {s['nama_aset']}" for s in self.top_servers_all]

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} server"

    @rx.var(cache=True)
    def total_pages(self) -> int:
        if self.total_items <= 0:
            return 1
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @rx.var(cache=True)
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var(cache=True)
    def page_tokens(self) -> list[str]:
        return [str(i) for i in range(1, self.total_pages + 1)]

    @rx.var(cache=True)
    def pagination_summary(self) -> str:
        if self.total_items == 0:
            return "Menampilkan 0 dari 0 server"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}-{end} dari {self.total_items} server"

    # --- COMPUTED VARS: SIMULASI PANEL RINCIAN (ARTBOARD 16 KANAN) ---
    @rx.var(cache=True)
    def sim_result(self) -> dict[str, Any]:
        cur_w = int(
            self.active_server.get("beban_efektif_w")
            or self.active_server.get("tdp_total_w")
            or 0
        )
        try:
            add_w = int(float(self.sim_extra_watt or "0"))
        except ValueError:
            add_w = 0
        new_total_w = max(0, cur_w + add_w)
        u_id = str(self.active_server.get("ups_id_aset") or "")
        old_pct = round(float(self.active_server.get("ups_utilisasi_pct") or 0.0))

        ups_obj = next((u for u in self.ups_items if u.get("id_aset") == u_id), None)
        if ups_obj and ups_obj.get("kapasitas_watt", 0) > 0:
            cap_w = int(ups_obj["kapasitas_watt"])
            other_w = max(0, int(ups_obj.get("beban_server_w", cur_w)) - cur_w)
            new_ups_load = other_w + new_total_w
            new_pct = round((new_ups_load / cap_w) * 100)
            is_man = bool(ups_obj.get("is_kapasitas_manual", False))
            if new_pct < self.asmp_batas_waspada:
                st = "Aman"
            elif new_pct <= self.asmp_batas_kritis:
                st = "Waspada"
            else:
                st = "Kritis" if is_man else "Kritis (Perkiraan)"
        else:
            new_pct = old_pct
            st = "—"

        return {
            "new_total_w": f"{new_total_w} W",
            "ups_id": u_id or "UPS",
            "old_pct": f"{old_pct}%",
            "new_pct": f"{new_pct}%",
            "status": st,
        }

    # --- COMPUTED VARS: MESIN HITUNG KALKULATOR (ARTBOARD 17) ---
    def _lookup_cat_watt(self, nama: str) -> int:
        item = next((c for c in self.catalog_items if c.get("nama") == nama), None)
        if not item:
            return 0
        if self.calc_load_mode == "puncak" and item.get("peak_w"):
            return int(item["peak_w"])
        return int(item.get("tdp_w", 0))

    @rx.var(cache=True)
    def calc_summary(self) -> dict[str, Any]:
        cpu_w = self._lookup_cat_watt(self.calc_cpu_name) * max(0, self.calc_cpu_qty)
        gpu_w = self._lookup_cat_watt(self.calc_gpu_name) * max(0, self.calc_gpu_qty)
        mobo_w = self._lookup_cat_watt(self.calc_mobo_name) * max(0, self.calc_mobo_qty)
        ram_w = self._lookup_cat_watt(self.calc_ram_name) * max(0, self.calc_ram_qty)
        sata_w = self._lookup_cat_watt(self.calc_ssd_sata_name) * max(0, self.calc_ssd_sata_qty)
        nvme_w = self._lookup_cat_watt(self.calc_nvme_name) * max(0, self.calc_nvme_qty)
        hdd_w = self._lookup_cat_watt(self.calc_hdd_name) * max(0, self.calc_hdd_qty)
        fan_w = self._lookup_cat_watt(self.calc_fan_name) * max(0, self.calc_fan_qty)
        opt_w = self._lookup_cat_watt(self.calc_optical_name) * max(0, self.calc_optical_qty)
        pcie_w = self._lookup_cat_watt(self.calc_pcie_name) * max(0, self.calc_pcie_qty)
        cust_w = max(0, self.calc_custom_watt) * max(0, self.calc_custom_qty)

        storage_w = sata_w + nvme_w + hdd_w
        other_w = fan_w + opt_w + pcie_w + cust_w
        base_total = cpu_w + gpu_w + mobo_w + ram_w + storage_w + other_w
        eff_total = max(0, round(base_total * (self.asmp_faktor_beban / 100.0)))

        psu = calculate_psu_specs(eff_total)
        kwh = energi_kwh_bulan(float(eff_total), self.asmp_jam_per_hari, self.asmp_hari_per_bulan)
        kwh_str = f"{str(kwh).replace('.', ',')} kWh"

        biaya_str = "Opsional · tampil jika tarif diisi"
        if self.has_tarif_listrik:
            rp = round(kwh * float(self.asmp_tarif_kwh.replace(",", ".")))
            biaya_str = f"Rp {_fmt_ribuan(rp)}"

        ups_obj = next(
            (u for u in self.all_ups_options if u.get("id_aset") == self.calc_selected_ups_id),
            None,
        )
        cap_w = int(ups_obj.get("kapasitas_watt", 420)) if ups_obj else 420
        is_man = bool(ups_obj.get("is_kapasitas_manual", False)) if ups_obj else False
        util_pct = round((eff_total / cap_w) * 100) if cap_w > 0 else 0
        min_ups_w = (
            math.ceil(eff_total / (self.asmp_batas_waspada / 100.0))
            if eff_total > 0
            else 0
        )
        if util_pct < self.asmp_batas_waspada:
            u_st = "Aman"
        elif util_pct <= self.asmp_batas_kritis:
            u_st = "Waspada"
        else:
            u_st = "Kritis" if is_man else "Kritis (Perkiraan)"

        return {
            "cpu_w": f"{cpu_w} W",
            "gpu_w": f"{gpu_w} W",
            "mobo_w": f"{mobo_w} W",
            "ram_w": f"{ram_w} W",
            "sata_w": f"{sata_w} W",
            "nvme_w": f"{nvme_w} W",
            "hdd_w": f"{hdd_w} W",
            "storage_w": f"{storage_w} W",
            "fan_w": f"{fan_w} W",
            "opt_w": f"{opt_w} W",
            "pcie_w": f"{pcie_w} W",
            "cust_w": f"{cust_w} W",
            "eff_total_w": eff_total,
            "eff_total_display": f"{eff_total} W",
            "psu_min_display": f"{psu['psu_min_w']} W",
            "psu_rek_display": f"{psu['psu_rekomendasi_w']} W",
            "kwh_display": kwh_str,
            "biaya_display": biaya_str,
            "ups_util_pct": util_pct,
            "ups_util_display": f"{util_pct}%",
            "ups_status": u_st,
            "min_ups_note": (
                f"UPS minimal disarankan: ≥ {min_ups_w} W "
                f"(beban ÷ batas waspada {self.asmp_batas_waspada}%). "
                "Kapasitas watt diisi manual di aset UPS."
            ),
        }

    # --- EVENT HANDLERS UTAMA ---
    @rx.event
    async def load_power_page(self) -> None:
        self.catalog_items = await api_client.get_power_catalog()
        self.scenarios_list = await api_client.get_watt_scenarios()
        await self.fetch_power_data()

    @rx.event
    def set_main_section_tab(self, tab: str) -> None:
        self.main_section_tab = tab

    @rx.event
    def toggle_show_all_ranked(self) -> None:
        self.show_all_ranked_servers = not self.show_all_ranked_servers

    @rx.event
    async def fetch_power_data(self) -> None:
        self.is_loading = True
        filters = {
            "scope": self.scope_filter.lower(),
            "tab": self.active_tab,
            "search": self.search_query,
            "cpu_brand": self.cpu_brand_filter,
            "beban_level": self.beban_filter,
            "ups_id": self.ups_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_server_power(
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = res.get("items", [])
        self.top_servers_all = res.get("top_servers", self.items)
        self.ups_items = res.get("ups_items", [])
        self.all_ups_options = res.get("all_ups_options", self.ups_items)
        self.total_items = int(res.get("total", 0))
        self.tab_counts = res.get(
            "tab_counts", {"Semua": self.total_items, "Operasional": 0, "Backup": 0}
        )

        asmp = res.get("assumptions") or {}
        if asmp:
            self.asmp_jam_per_hari = int(asmp.get("jam_operasional_per_hari", 24))
            self.asmp_hari_per_bulan = int(asmp.get("hari_per_bulan", 30))
            self.asmp_faktor_beban = int(asmp.get("faktor_beban_persen", 100))
            t_val = asmp.get("tarif_listrik_per_kwh")
            self.asmp_tarif_kwh = (
                str(int(t_val)) if (t_val and float(t_val) > 0) else ""
            )
            self.asmp_faktor_daya_ups = str(
                asmp.get("faktor_daya_ups", 0.6)
            ).replace(".", ",")
            self.asmp_batas_waspada = int(asmp.get("batas_waspada_ups", 70))
            self.asmp_batas_kritis = int(asmp.get("batas_kritis_ups", 85))

        summary = res.get("summary", {})
        tdp_kw = float(summary.get("total_tdp_kw", 0.0))
        psu_min = int(summary.get("total_psu_min_w", 0))
        psu_rek = int(summary.get("total_psu_rek_w", 0))
        kwh_bln = float(summary.get("est_kwh_month", 0.0))
        avg_tdp = int(summary.get("avg_tdp_w", 0))
        max_tdp = int(summary.get("max_tdp_w", 0))
        max_srv = str(summary.get("max_tdp_server", "—"))
        self.kpi_max_tdp_id = str(summary.get("max_tdp_id", "SRV-014"))

        kw_str = f"{tdp_kw:.2f}".replace(".", ",")
        kwh_str = f"{round(kwh_bln):,}".replace(",", ".")

        self.kpi_total_tdp_kw_display = f"{kw_str} kW"
        self.kpi_total_tdp_sub = f"{self.total_items} server · rata-rata {avg_tdp} W"
        self.kpi_kwh_month_display = f"{kwh_str} kWh"
        self.kpi_kwh_sub = (
            f"asumsi {self.asmp_jam_per_hari}/7 ({self.asmp_total_jam_bulan} jam) · "
            f"faktor beban {self.asmp_faktor_beban}%"
        )
        est_rp = summary.get("estimasi_biaya_bulan")
        self.kpi_biaya_month_display = (
            f"Rp {_fmt_ribuan(est_rp)} / bln" if est_rp else ""
        )

        self.kpi_psu_summary_display = f"{_fmt_ribuan(psu_min)} / {_fmt_ribuan(psu_rek)} W"
        self.psu_kurang_count = int(summary.get("psu_kurang_count", 0))
        self.kpi_psu_sub = (
            f"{self.psu_kurang_count} server PSU kurang"
            if self.psu_kurang_count > 0
            else "total kapasitas yang disarankan"
        )
        self.kpi_max_tdp_display = f"{_fmt_ribuan(max_tdp)} W"
        self.kpi_max_tdp_server = max_srv

        u_cnt = int(summary.get("monitored_ups_count", len(self.ups_items)))
        u_max_pct = int(summary.get("max_ups_util_pct", 0))
        u_src = str(summary.get("max_ups_source", "perkiraan"))
        self.kpi_ups_count_display = f"{u_cnt} UPS"
        self.kpi_ups_status_badge = str(summary.get("max_ups_status", "Aman"))
        self.kpi_ups_sub = f"terpantau · tertinggi {u_max_pct}% ({u_src})"
        self.unfilled_ups_watt_count = int(summary.get("unfilled_ups_watt_count", 0))
        self.is_loading = False

    # --- HANDLERS FILTER & SORT ---
    @rx.event
    async def set_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_scope_filter(self, val: str) -> None:
        self.scope_filter = val
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_search_query(self, query: str) -> None:
        self.search_query = query
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_cpu_brand_filter(self, val: str) -> None:
        self.cpu_brand_filter = "" if val in ("Semua", "all") else val
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_beban_filter(self, val: str) -> None:
        self.beban_filter = "" if val in ("Semua", "all") else val
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def set_ups_filter(self, val: str) -> None:
        self.ups_filter = "" if val in ("Semua", "all") else val
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.cpu_brand_filter = ""
        self.beban_filter = ""
        self.ups_filter = ""
        self.sort_by = ""
        self.sort_dir = "asc"
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def toggle_sort(self, col_key: str) -> None:
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        await self.fetch_power_data()

    @rx.event
    def toggle_column_visibility(self, col_key: str) -> None:
        cur = list(self.hidden_columns)
        if col_key in cur:
            cur = [c for c in cur if c != col_key]
        else:
            cur.append(col_key)
        self.watt_col_prefs_json = json.dumps(cur)

    @rx.event
    def reset_columns(self) -> None:
        self.watt_col_prefs_json = "[]"

    # --- HANDLERS PAGINASI ---
    @rx.event
    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.fetch_power_data()

    @rx.event
    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.fetch_power_data()

    @rx.event
    async def select_page(self, token: str) -> None:
        try:
            p = int(token)
            if 1 <= p <= self.total_pages and p != self.page:
                self.page = p
                await self.fetch_power_data()
        except ValueError:
            pass

    # --- HANDLERS ASUMSI, INLINE UPS, & DRAWER RINCIAN ---
    @rx.event
    def open_assumptions_modal(self) -> None:
        self.asmp_error = ""
        self.asmp_modal_open = True

    @rx.event
    def close_assumptions_modal(self) -> None:
        self.asmp_modal_open = False

    @rx.event
    def set_asmp_jam(self, val: str) -> None:
        try:
            self.asmp_jam_per_hari = max(1, min(24, int(float(val or 24))))
        except ValueError:
            pass

    @rx.event
    def set_asmp_hari(self, val: str) -> None:
        try:
            self.asmp_hari_per_bulan = max(1, min(31, int(float(val or 30))))
        except ValueError:
            pass

    @rx.event
    def set_asmp_faktor_beban(self, val: str) -> None:
        try:
            self.asmp_faktor_beban = max(10, min(150, int(float(val or 100))))
        except ValueError:
            pass

    @rx.event
    def set_asmp_tarif_kwh(self, val: str) -> None:
        self.asmp_tarif_kwh = val

    @rx.event
    def set_asmp_faktor_daya_ups(self, val: str) -> None:
        self.asmp_faktor_daya_ups = val

    @rx.event
    def set_asmp_waspada(self, val: str) -> None:
        try:
            self.asmp_batas_waspada = max(30, min(95, int(float(val or 70))))
        except ValueError:
            pass

    @rx.event
    def set_asmp_kritis(self, val: str) -> None:
        try:
            self.asmp_batas_kritis = max(40, min(100, int(float(val or 85))))
        except ValueError:
            pass

    @rx.event
    async def save_assumptions(self) -> Any:
        if self.asmp_batas_waspada >= self.asmp_batas_kritis:
            self.asmp_error = "Batas waspada UPS harus lebih kecil dari batas kritis."
            return None
        try:
            pf = float(self.asmp_faktor_daya_ups.replace(",", "."))
        except ValueError:
            pf = 0.6
        tarif_clean = None
        if self.asmp_tarif_kwh.strip():
            try:
                t_num = float(self.asmp_tarif_kwh.replace(".", "").replace(",", "."))
                if t_num > 0:
                    tarif_clean = t_num
            except ValueError:
                pass
        await api_client.save_power_assumptions(
            {
                "jam_operasional_per_hari": self.asmp_jam_per_hari,
                "hari_per_bulan": self.asmp_hari_per_bulan,
                "faktor_beban_persen": self.asmp_faktor_beban,
                "tarif_listrik_per_kwh": tarif_clean,
                "faktor_daya_ups": pf,
                "batas_waspada_ups": self.asmp_batas_waspada,
                "batas_kritis_ups": self.asmp_batas_kritis,
            }
        )
        self.asmp_modal_open = False
        await self.fetch_power_data()
        return rx.toast.success("Pengaturan asumsi disimpan & tercatat di Audit Log.")

    @rx.event
    def start_inline_ups_watt(self, ups_id: str, cur_watt: Any = "") -> None:
        self.inline_ups_edit_id = ups_id
        self.inline_ups_watt_val = str(cur_watt or "")

    @rx.event
    def set_inline_ups_watt_val(self, val: str) -> None:
        self.inline_ups_watt_val = val

    @rx.event
    async def submit_inline_ups_watt(self, ups_id: str) -> Any:
        try:
            w_val = int(float(self.inline_ups_watt_val.strip()))
            if w_val <= 0:
                return rx.toast.error("Kapasitas Watt harus lebih besar dari 0.")
        except ValueError:
            return rx.toast.error("Masukkan angka Watt yang valid.")
        ups_obj = next((u for u in self.ups_items if u.get("id_aset") == ups_id), {})
        va_val = int(ups_obj.get("kapasitas_va", 650) or 650)
        await api_client.update_ups_capacity_watt(ups_id, w_val)
        self.inline_ups_edit_id = ""
        await self.fetch_power_data()
        if w_val > va_val:
            return rx.toast.warning(
                f"Kapasitas {w_val} W melebihi {va_val} VA. Periksa kembali datasheet."
            )
        return rx.toast.success(f"Kapasitas {ups_id} disimpan ({w_val} W · Datasheet).")

    @rx.event
    def open_drawer(self, row_id: str) -> None:
        target = next(
            (x for x in self.top_servers_all if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.active_row_id = str(target["id_aset"])
        self.active_server = target
        self.sim_extra_watt = "50"
        komp = target.get("komposisi_beban") or {
            "CPU": 65,
            "GPU": 15,
            "RAM": 16,
            "Storage": 15,
            "Lainnya": 87,
        }
        colors_map = {
            "CPU": Color.BLUE_600,
            "GPU": Color.PURPLE_600,
            "RAM": Color.GREEN_700,
            "Storage": Color.WARNING_BAR,
            "Lainnya": Color.SLATE_400,
        }
        self.active_komposisi_list = [
            {"label": k, "watt": f"{v} W", "color": colors_map.get(k, Color.SLATE_400)}
            for k, v in komp.items()
        ]
        self.drawer_open = True

    @rx.event
    def close_drawer(self) -> None:
        self.drawer_open = False
        self.active_row_id = ""

    @rx.event
    def set_drawer_tab(self, tab: str) -> None:
        self.drawer_tab = tab

    @rx.event
    def set_sim_extra_watt(self, val: str) -> None:
        self.sim_extra_watt = val

    # --- HANDLERS KALKULATOR & SKENARIO ---
    @rx.event
    def set_calc_start_mode(self, mode: str) -> None:
        self.calc_start_mode = mode

    @rx.event
    def set_calc_selected_server_id(self, val: str) -> None:
        self.calc_selected_server_id = val.split("·")[0].strip()

    @rx.event
    def load_server_into_calculator(self) -> Any:
        srv = next(
            (s for s in self.top_servers_all if s["id_aset"] == self.calc_selected_server_id),
            None,
        )
        if not srv:
            return rx.toast.error("Pilih server terlebih dahulu.")
        for c in self.catalog_items:
            if c["kategori"] == "cpu" and c["nama"].lower() in srv["cpu"].lower():
                self.calc_cpu_name = c["nama"]
                break
        self.calc_gpu_name = (
            "Intel UHD Graphics (terpadu)"
            if "UHD" in srv["vga"].upper()
            else "NVIDIA GeForce GT 1030 2GB"
        )
        self.calc_ram_qty = 4 if "4" in srv["ram"] else 2
        self.calc_ssd_sata_qty = 3 if "3" in srv["hdd_ssd"] else 2
        self.calc_nvme_qty = 1 if "M.2" in srv["hdd_ssd"] else 0
        if srv.get("ups_id_aset"):
            self.calc_selected_ups_id = srv["ups_id_aset"]
        return rx.toast.info(f"Spesifikasi {srv['nama_aset']} dimuat ke kalkulator.")

    @rx.event
    def toggle_calc_load_mode(self) -> None:
        self.calc_load_mode = "puncak" if self.calc_load_mode == "dasar" else "dasar"

    @rx.event
    def step_calc_qty(self, slot: str, delta: int) -> None:
        attr_map = {
            "cpu": "calc_cpu_qty",
            "gpu": "calc_gpu_qty",
            "mobo": "calc_mobo_qty",
            "ram": "calc_ram_qty",
            "sata": "calc_ssd_sata_qty",
            "nvme": "calc_nvme_qty",
            "hdd": "calc_hdd_qty",
            "fan": "calc_fan_qty",
            "opt": "calc_optical_qty",
            "pcie": "calc_pcie_qty",
            "custom": "calc_custom_qty",
        }
        field = attr_map.get(slot)
        if field:
            cur = int(getattr(self, field, 0))
            setattr(self, field, max(0, min(32, cur + delta)))

    @rx.event
    def set_calc_component(self, slot: str, val: str) -> None:
        field_map = {
            "cpu": "calc_cpu_name",
            "gpu": "calc_gpu_name",
            "mobo": "calc_mobo_name",
            "ram": "calc_ram_name",
            "sata": "calc_ssd_sata_name",
            "nvme": "calc_nvme_name",
            "hdd": "calc_hdd_name",
            "fan": "calc_fan_name",
            "opt": "calc_optical_name",
            "pcie": "calc_pcie_name",
            "ups": "calc_selected_ups_id",
        }
        if slot in field_map:
            setattr(self, field_map[slot], val)

    @rx.event
    async def save_current_scenario(self) -> Any:
        cs = self.calc_summary
        nama = self.scenario_name_input.strip() or f"Skenario {cs['eff_total_display']}"
        await api_client.save_watt_scenario(
            {
                "nama": nama,
                "asset_id": (
                    self.calc_selected_server_id
                    if self.calc_start_mode == "server_ada"
                    else None
                ),
                "subtitle": f"{cs['eff_total_display']} · PSU {cs['psu_rek_display']}",
                "komponen": [],
                "hasil": dict(cs),
            }
        )
        self.scenarios_list = await api_client.get_watt_scenarios()
        self.scenario_modal_open = False
        return rx.toast.success(f"Skenario '{nama}' berhasil disimpan.")

    @rx.event
    async def create_draft_server_from_calc(self) -> Any:
        cs = self.calc_summary
        await api_client.save_server_power(
            payload={
                "nama_aset": f"SERVER RANCANGAN ({cs['eff_total_display']})",
                "cpu": self.calc_cpu_name,
                "vga": self.calc_gpu_name,
                "ram": f"{self.calc_ram_qty}x {self.calc_ram_name}",
                "hdd_ssd": (
                    f"{self.calc_ssd_sata_qty}x SSD SATA, "
                    f"{self.calc_nvme_qty}x SSD M.2"
                ),
                "tdp_total_w": cs["eff_total_w"],
                "status": "Cadangan",
                "catatan": "Dibuat dari Kalkulator Watt Server",
            }
        )
        await self.fetch_power_data()
        self.main_section_tab = "rekap"
        return rx.toast.success("Draft aset Server berhasil dibuat dengan status Cadangan.")

    @rx.event
    async def export_watt_excel(self) -> Any:
        data_bytes = await api_client.generate_watt_excel_bytes(
            self.top_servers_all,
            {
                "jam_operasional_per_hari": self.asmp_jam_per_hari,
                "hari_per_bulan": self.asmp_hari_per_bulan,
                "faktor_beban_persen": self.asmp_faktor_beban,
                "tarif_listrik_per_kwh": (
                    float(self.asmp_tarif_kwh.replace(",", "."))
                    if self.has_tarif_listrik
                    else None
                ),
            },
        )
        return rx.download(data=data_bytes, filename="Rekap_Watt_Server_ITAM_Pro.xlsx")

    # --- HANDLERS MODAL TAMBAH / EDIT SERVER MANUAL ---
    @rx.event
    def open_add_modal(self) -> None:
        self.form_mode = "add"
        self.form_error = ""
        self.form_id_aset = ""
        self.form_nama_aset = ""
        self.form_cpu = ""
        self.form_vga = ""
        self.form_ram = ""
        self.form_hdd_ssd = ""
        self.form_tdp_w = "0"
        self.form_psu_min_w = "0"
        self.form_psu_rek_w = "0"
        self.form_catatan = ""
        self.form_modal_open = True

    @rx.event
    def open_edit_modal(self, row_id: str) -> None:
        target = next(
            (x for x in self.top_servers_all if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.form_mode = "edit"
        self.form_error = ""
        self.form_id_aset = target["id_aset"]
        self.form_nama_aset = target["nama_aset"]
        self.form_cpu = target.get("cpu", "")
        self.form_vga = target.get("vga", "")
        self.form_ram = target.get("ram", "")
        self.form_hdd_ssd = target.get("hdd_ssd", "")
        self.form_tdp_w = str(target.get("tdp_total_w", 0))
        self.form_psu_min_w = str(target.get("psu_min_w", 0))
        self.form_psu_rek_w = str(target.get("psu_rekomendasi_w", 0))
        self.form_catatan = target.get("catatan", "")
        self.form_modal_open = True

    @rx.event
    def open_duplicate_modal(self, row_id: str) -> None:
        target = next(
            (x for x in self.top_servers_all if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.form_mode = "duplicate"
        self.form_error = ""
        self.form_id_aset = ""
        self.form_nama_aset = f"{target['nama_aset']} (Salinan)"
        self.form_cpu = target.get("cpu", "")
        self.form_vga = target.get("vga", "")
        self.form_ram = target.get("ram", "")
        self.form_hdd_ssd = target.get("hdd_ssd", "")
        self.form_tdp_w = str(target.get("tdp_total_w", 0))
        self.form_psu_min_w = str(target.get("psu_min_w", 0))
        self.form_psu_rek_w = str(target.get("psu_rekomendasi_w", 0))
        self.form_catatan = target.get("catatan", "")
        self.form_modal_open = True

    @rx.event
    def close_form_modal(self) -> None:
        self.form_modal_open = False

    @rx.event
    def set_form_nama_aset(self, val: str) -> None:
        self.form_nama_aset = val

    @rx.event
    def set_form_cpu(self, val: str) -> None:
        self.form_cpu = val

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
        self.form_tdp_w = val

    @rx.event
    def set_form_psu_min_w(self, val: str) -> None:
        self.form_psu_min_w = val

    @rx.event
    def set_form_psu_rek_w(self, val: str) -> None:
        self.form_psu_rek_w = val

    @rx.event
    def set_form_catatan(self, val: str) -> None:
        self.form_catatan = val

    @rx.event
    async def submit_form(self) -> Any:
        if not self.form_nama_aset.strip():
            self.form_error = "Nama server wajib diisi."
            return None
        payload = {
            "nama_aset": self.form_nama_aset,
            "cpu": self.form_cpu,
            "vga": self.form_vga,
            "ram": self.form_ram,
            "hdd_ssd": self.form_hdd_ssd,
            "tdp_total_w": int(float(self.form_tdp_w or 0)),
            "psu_min_w": int(float(self.form_psu_min_w or 0)),
            "psu_rekomendasi_w": int(float(self.form_psu_rek_w or 0)),
            "catatan": self.form_catatan,
        }
        target_id = self.form_id_aset if self.form_mode == "edit" else ""
        await api_client.save_server_power(payload=payload, asset_id=target_id)
        self.form_modal_open = False
        await self.fetch_power_data()
        return rx.toast.success("Data server berhasil disimpan.")

    # --- HANDLERS HAPUS SERVER ---
    @rx.event
    def confirm_delete_entry(self, row_id: str) -> None:
        target = next(
            (x for x in self.top_servers_all if x["id"] == row_id or x["id_aset"] == row_id),
            None,
        )
        if not target:
            return
        self.delete_target_id = target["id_aset"]
        self.delete_target_nama = target["nama_aset"]
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
