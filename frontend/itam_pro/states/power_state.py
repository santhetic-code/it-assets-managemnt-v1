"""
State Management untuk Halaman Infrastructure -> Rekap Watt Server (/watt-server).
"""
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client


def _fmt_ribuan(val: int | float) -> str:
    """Format angka ribuan menggunakan titik (contoh: 3104 -> '3.104')."""
    return f"{round(val):,}".replace(",", ".")


class PowerState(rx.State):
    """State untuk tabel, ringkasan KPI, drawer, dan modal form Rekap Watt Server."""

    items: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 20
    is_loading: bool = False

    # Tab & Filter
    active_tab: str = "Semua"
    search_query: str = ""
    cpu_brand_filter: str = ""
    beban_filter: str = ""
    sort_by: str = ""
    sort_dir: str = "asc"
    hidden_columns: list[str] = []

    tab_counts: dict[str, int] = {"Semua": 16, "Operasional": 11, "Backup": 5}

    # Ringkasan KPI & Footer ESTIMASI
    kpi_total_tdp_display: str = "3.104 W"
    kpi_total_kw_note: str = "3,10 kW · 16 unit server"
    kpi_kwh_month_display: str = "2.234,9 kWh"
    kpi_psu_summary_display: str = "4.600 W / 6.150 W"
    kpi_avg_tdp_note: str = "Rata-rata 194 W per server"
    kpi_max_tdp_display: str = "300 W"
    kpi_max_tdp_server: str = "SERVER BACKUP REAL TIME"

    footer_tdp_display: str = "3.104 W"
    footer_psu_min_display: str = "4.600 W"
    footer_psu_rek_display: str = "6.150 W"
    footer_kwh_display: str = "2.234,9 kWh/bln"

    # Drawer Detail
    drawer_open: bool = False
    drawer_tab: str = "detail"
    active_row_id: str = ""
    active_code: str = ""
    active_title: str = ""
    active_category_badge: str = "Server"
    active_status_badge: str = "Efisien"
    active_general_items: list[dict[str, str]] = []
    active_power_items: list[dict[str, str]] = []
    active_history_items: list[dict[str, str]] = []

    # Modal Form Tambah / Edit Manual
    form_modal_open: bool = False
    is_edit_mode: bool = False
    edit_asset_id: str = ""
    form_error: str = ""

    form_nama_aset: str = ""
    form_cpu: str = ""
    form_vga: str = ""
    form_ram: str = ""
    form_hdd_ssd: str = ""
    form_tdp_w: str = ""
    form_psu_min_w: str = ""
    form_psu_rek_w: str = ""
    form_lokasi: str = "Kantor Pusat"
    form_status: str = "Digunakan"
    form_catatan: str = ""

    # Dialog Hapus
    delete_dialog_open: bool = False
    delete_target_id: str = ""
    delete_target_label: str = ""

    @rx.var
    def cpu_brand_options(self) -> list[str]:
        return ["Intel", "AMD"]

    @rx.var
    def beban_options(self) -> list[str]:
        return [
            "Rendah (< 170 W)",
            "Menengah (170 - 220 W)",
            "Tinggi (> 220 W)",
        ]

    @rx.var
    def result_count_label(self) -> str:
        return f"{self.total_items} server"

    @rx.var
    def total_pages(self) -> int:
        if self.total_items <= 0:
            return 1
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @rx.var
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var
    def page_tokens(self) -> list[str]:
        return [str(i) for i in range(1, self.total_pages + 1)]

    @rx.var
    def pagination_summary(self) -> str:
        if self.total_items == 0:
            return "Menampilkan 0 dari 0 server"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}-{end} dari {self.total_items} server"

    @rx.event
    async def load_power_page(self) -> None:
        """Muat data saat halaman /watt-server dibuka."""
        await self.fetch_power_data()

    async def fetch_power_data(self) -> None:
        self.is_loading = True
        filters = {
            "tab": self.active_tab,
            "search": self.search_query,
            "cpu_brand": self.cpu_brand_filter,
            "beban_level": self.beban_filter,
            "sort_by": self.sort_by,
            "sort_dir": self.sort_dir,
        }
        res = await api_client.get_server_power(
            filters=filters,
            page=self.page,
            page_size=self.page_size,
        )
        self.items = res.get("items", [])
        self.total_items = int(res.get("total", 0))
        self.tab_counts = res.get(
            "tab_counts",
            {"Semua": self.total_items, "Operasional": 0, "Backup": 0},
        )

        summary = res.get("summary", {})
        tdp_w = int(summary.get("total_tdp_w", 0))
        tdp_kw = float(summary.get("total_tdp_kw", 0.0))
        psu_min = int(summary.get("total_psu_min_w", 0))
        psu_rek = int(summary.get("total_psu_rek_w", 0))
        kwh_bln = float(summary.get("est_kwh_month", 0.0))
        avg_tdp = float(summary.get("avg_tdp_w", 0.0))
        max_tdp = int(summary.get("max_tdp_w", 0))
        max_srv = str(summary.get("max_tdp_server", "—"))

        kw_str = f"{tdp_kw:.2f}".replace(".", ",")
        kwh_str = f"{kwh_bln:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        avg_str = f"{avg_tdp:.0f}"

        self.kpi_total_tdp_display = f"{_fmt_ribuan(tdp_w)} W"
        self.kpi_total_kw_note = f"{kw_str} kW · {self.total_items} unit server"
        self.kpi_kwh_month_display = f"{kwh_str} kWh"
        self.kpi_psu_summary_display = f"{_fmt_ribuan(psu_min)} W / {_fmt_ribuan(psu_rek)} W"
        self.kpi_avg_tdp_note = f"Rata-rata {avg_str} W per server"
        self.kpi_max_tdp_display = f"{_fmt_ribuan(max_tdp)} W"
        self.kpi_max_tdp_server = max_srv

        self.footer_tdp_display = f"{_fmt_ribuan(tdp_w)} W ({kw_str} kW)"
        self.footer_psu_min_display = f"{_fmt_ribuan(psu_min)} W"
        self.footer_psu_rek_display = f"{_fmt_ribuan(psu_rek)} W"
        self.footer_kwh_display = f"{kwh_str} kWh/bln"
        self.is_loading = False

    async def set_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.page = 1
        await self.fetch_power_data()

    async def set_search_query(self, val: str) -> None:
        self.search_query = val
        self.page = 1
        await self.fetch_power_data()

    async def set_cpu_brand_filter(self, val: str) -> None:
        self.cpu_brand_filter = val
        self.page = 1
        await self.fetch_power_data()

    async def set_beban_filter(self, val: str) -> None:
        self.beban_filter = val
        self.page = 1
        await self.fetch_power_data()

    async def reset_filters(self) -> None:
        self.active_tab = "Semua"
        self.search_query = ""
        self.cpu_brand_filter = ""
        self.beban_filter = ""
        self.sort_by = ""
        self.sort_dir = "asc"
        self.page = 1
        await self.fetch_power_data()

    async def toggle_sort(self, col_key: str) -> None:
        if self.sort_by == col_key:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_by = col_key
            self.sort_dir = "asc"
        await self.fetch_power_data()

    def toggle_column_visibility(self, col_key: str) -> None:
        if col_key in self.hidden_columns:
            self.hidden_columns = [c for c in self.hidden_columns if c != col_key]
        else:
            self.hidden_columns = [*self.hidden_columns, col_key]

    def reset_columns(self) -> None:
        self.hidden_columns = []

    async def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self.fetch_power_data()

    async def next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self.fetch_power_data()

    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages:
                self.page = target
                await self.fetch_power_data()

    # --- Drawer Detail ---
    def open_drawer(self, row_id: str) -> None:
        target = next((x for x in self.items if x["id"] == row_id), None)
        if not target:
            return
        self.active_row_id = row_id
        self.active_code = target["id_aset"]
        self.active_title = target["nama_aset"]
        self.active_category_badge = target["grup_server"]
        self.active_status_badge = target["beban_badge"]
        self.drawer_tab = "detail"
        self.active_general_items = [
            {"label": "ID Aset", "value": target["id_aset"]},
            {"label": "ID Server", "value": target["nama_aset"]},
            {"label": "Kelompok Server", "value": target["grup_server"]},
            {"label": "Model Prosesor (CPU)", "value": target["cpu"]},
            {"label": "Kartu Grafis (GPU)", "value": target["vga"]},
            {"label": "Konfigurasi RAM", "value": target["ram"]},
            {"label": "Konfigurasi Penyimpanan", "value": target["hdd_ssd"]},
        ]
        self.active_power_items = [
            {"label": "Total TDP (W)", "value": target["tdp_display"]},
            {"label": "PSU Minimum (W)", "value": target["psu_min_display"]},
            {"label": "PSU Rekomendasi (W)", "value": target["psu_rek_display"]},
            {"label": "Estimasi Bulanan (720j)", "value": target["kwh_display"]},
            {"label": "Klasifikasi Beban", "value": target["beban_level"]},
            {"label": "Catatan", "value": target["catatan"]},
        ]
        self.active_history_items = [
            {
                "event": f"Pencatatan daya server {target['id_aset']}",
                "date": "2026-10-20",
                "note": f"TDP: {target['tdp_display']} · Beban: {target['beban_badge']}",
            }
        ]
        self.drawer_open = True

    def close_drawer(self) -> None:
        self.drawer_open = False

    def set_drawer_tab(self, tab: str) -> None:
        self.drawer_tab = tab

    # --- Modal Tambah / Edit Manual ---
    def open_add_modal(self) -> None:
        self.is_edit_mode = False
        self.edit_asset_id = ""
        self.form_error = ""
        self.form_nama_aset = ""
        self.form_cpu = ""
        self.form_vga = ""
        self.form_ram = ""
        self.form_hdd_ssd = ""
        self.form_tdp_w = "160"
        self.form_psu_min_w = "250"
        self.form_psu_rek_w = "350"
        self.form_lokasi = "Kantor Pusat"
        self.form_status = "Digunakan"
        self.form_catatan = ""
        self.form_modal_open = True

    def open_edit_modal(self, row_id: str) -> None:
        target_id = row_id or self.active_row_id
        target = next((x for x in self.items if x["id"] == target_id), None)
        if not target:
            return
        self.is_edit_mode = True
        self.edit_asset_id = target["id_aset"]
        self.form_error = ""
        self.form_nama_aset = target["nama_aset"]
        self.form_cpu = "" if target["cpu"] == "—" else target["cpu"]
        self.form_vga = "" if target["vga"] == "—" else target["vga"]
        self.form_ram = "" if target["ram"] == "—" else target["ram"]
        self.form_hdd_ssd = "" if target["hdd_ssd"] == "—" else target["hdd_ssd"]
        self.form_tdp_w = str(target["tdp_total_w"])
        self.form_psu_min_w = str(target["psu_min_w"])
        self.form_psu_rek_w = str(target["psu_rekomendasi_w"])
        self.form_lokasi = target["lokasi"]
        self.form_status = target["status"]
        self.form_catatan = "" if target["catatan"] == "—" else target["catatan"]
        self.drawer_open = False
        self.form_modal_open = True

    def open_duplicate_modal(self, row_id: str) -> None:
        target_id = row_id or self.active_row_id
        target = next((x for x in self.items if x["id"] == target_id), None)
        if not target:
            return
        self.open_edit_modal(target_id)
        self.is_edit_mode = False
        self.edit_asset_id = ""
        self.form_nama_aset = f"{target['nama_aset']} COPY"

    def close_form_modal(self) -> None:
        self.form_modal_open = False
        self.form_error = ""

    def set_form_nama_aset(self, val: str) -> None:
        self.form_nama_aset = val

    def set_form_cpu(self, val: str) -> None:
        self.form_cpu = val

    def set_form_vga(self, val: str) -> None:
        self.form_vga = val

    def set_form_ram(self, val: str) -> None:
        self.form_ram = val

    def set_form_hdd_ssd(self, val: str) -> None:
        self.form_hdd_ssd = val

    def set_form_tdp_w(self, val: float | str) -> None:
        if isinstance(val, float) and val.is_integer():
            self.form_tdp_w = str(int(val))
        else:
            self.form_tdp_w = str(val) if val is not None else ""

    def set_form_psu_min_w(self, val: float | str) -> None:
        if isinstance(val, float) and val.is_integer():
            self.form_psu_min_w = str(int(val))
        else:
            self.form_psu_min_w = str(val) if val is not None else ""

    def set_form_psu_rek_w(self, val: float | str) -> None:
        if isinstance(val, float) and val.is_integer():
            self.form_psu_rek_w = str(int(val))
        else:
            self.form_psu_rek_w = str(val) if val is not None else ""

    def set_form_catatan(self, val: str) -> None:
        self.form_catatan = val

    async def submit_form(self) -> None:
        if not self.form_nama_aset.strip():
            self.form_error = "ID Server wajib diisi (contoh: SERVER OTO H2H)."
            return
        if not self.form_cpu.strip():
            self.form_error = "Model Prosesor (CPU) wajib diisi."
            return
        try:
            tdp_val = int(float(self.form_tdp_w.strip()))
            psu_min_val = int(float(self.form_psu_min_w.strip() or "0"))
            psu_rek_val = int(float(self.form_psu_rek_w.strip() or "0"))
            if tdp_val <= 0:
                self.form_error = "Total TDP (W) harus lebih besar dari 0."
                return
        except ValueError:
            self.form_error = "Nilai TDP dan PSU harus berupa angka bulat (Watt)."
            return

        payload = {
            "nama_aset": self.form_nama_aset.strip(),
            "cpu": self.form_cpu.strip(),
            "vga": self.form_vga.strip(),
            "ram": self.form_ram.strip(),
            "hdd_ssd": self.form_hdd_ssd.strip(),
            "tdp_total_w": tdp_val,
            "psu_min_w": psu_min_val,
            "psu_rekomendasi_w": psu_rek_val,
            "lokasi": self.form_lokasi,
            "status": self.form_status,
            "catatan": self.form_catatan.strip(),
        }
        await api_client.save_server_power(payload=payload, asset_id=self.edit_asset_id)
        self.form_modal_open = False
        await self.fetch_power_data()

    # --- Dialog Hapus ---
    def confirm_delete_entry(self, row_id: str) -> None:
        target_id = row_id or self.active_row_id
        target = next((x for x in self.items if x["id"] == target_id), None)
        if not target:
            return
        self.delete_target_id = target["id_aset"]
        self.delete_target_label = f"{target['nama_aset']} ({target['id_aset']})"
        self.drawer_open = False
        self.delete_dialog_open = True

    def cancel_delete(self) -> None:
        self.delete_dialog_open = False
        self.delete_target_id = ""

    async def execute_delete_entry(self) -> None:
        if self.delete_target_id:
            await api_client.delete_server_power(self.delete_target_id)
        self.delete_dialog_open = False
        self.delete_target_id = ""
        await self.fetch_power_data()


__all__ = ["PowerState"]
