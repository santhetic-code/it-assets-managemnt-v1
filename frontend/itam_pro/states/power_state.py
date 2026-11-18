"""
State Management untuk Halaman Laporan -> Rekap Watt Server (/watt-server).
Mode Tabel Rekap Manual sesuai spreadsheet docs/data/rekap_watt_server.csv.
"""

from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client


def _fmt_ribuan(val: int | float) -> str:
    """Format angka ribuan menggunakan titik (contoh: 3104 -> '3.104')."""
    return f"{round(val):,}".replace(",", ".")


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
        return bool(self.search_query.strip())

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} server"

    @rx.var(cache=True)
    def estimasi_search_subnote(self) -> str:
        if not self.search_query.strip():
            return f"Total dari {self.total_items} server"
        return (
            f"{self.total_items} dari {self.overall_total_servers} server, "
            f"total keseluruhan {self.overall_tdp_display} / "
            f"{self.overall_psu_min_display} / {self.overall_psu_rek_display} W"
        )

    @rx.var(cache=True)
    def delete_target_label(self) -> str:
        return f"{self.delete_target_nama} ({self.delete_target_id})"

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
                "sort_by": self.sort_by,
                "sort_dir": self.sort_dir,
            }
            res = await api_client.get_server_power(
                filters=filters,
                page=self.page,
                page_size=self.page_size,
            )
            raw_items = res.get("items", [])
            enriched_items: list[dict[str, Any]] = []
            for idx, it in enumerate(raw_items, start=1):
                row = dict(it)
                tdp_val = int(row.get("tdp_total_w") or row.get("watt") or 0)
                min_val = int(row.get("psu_min_w") or 0)
                rek_val = int(row.get("psu_rekomendasi_w") or 0)
                row["no"] = str(idx)
                row["tdp_total_w"] = tdp_val
                row["psu_min_w"] = min_val
                row["psu_rekomendasi_w"] = rek_val
                row["tdp_num_display"] = _fmt_ribuan(tdp_val)
                row["psu_min_num_display"] = _fmt_ribuan(min_val)
                row["psu_rek_num_display"] = _fmt_ribuan(rek_val)
                enriched_items.append(row)

            self.items = enriched_items
            self.total_items = int(res.get("total", len(enriched_items)))

            if not self.search_query.strip():
                self.all_servers_cache = list(enriched_items)

            summary = res.get("summary", {})
            tdp_sum = int(
                summary.get("total_tdp_w")
                or sum(x["tdp_total_w"] for x in enriched_items)
            )
            min_sum = int(
                summary.get("total_psu_min_w")
                or sum(x["psu_min_w"] for x in enriched_items)
            )
            rek_sum = int(
                summary.get("total_psu_rek_w")
                or sum(x["psu_rekomendasi_w"] for x in enriched_items)
            )

            ov_cnt = int(
                summary.get("overall_total_servers")
                or len(self.all_servers_cache)
                or self.total_items
            )
            ov_tdp = int(summary.get("overall_total_tdp_w") or tdp_sum)
            ov_min = int(summary.get("overall_total_psu_min_w") or min_sum)
            ov_rek = int(summary.get("overall_total_psu_rek_w") or rek_sum)

            self.overall_total_servers = ov_cnt
            self.estimasi_tdp_display = _fmt_ribuan(tdp_sum)
            self.estimasi_psu_min_display = _fmt_ribuan(min_sum)
            self.estimasi_psu_rek_display = _fmt_ribuan(rek_sum)
            self.overall_tdp_display = _fmt_ribuan(ov_tdp)
            self.overall_psu_min_display = _fmt_ribuan(ov_min)
            self.overall_psu_rek_display = _fmt_ribuan(ov_rek)
        finally:
            self.is_loading = False

    # --- HANDLERS PENCARIAN, SORT, & EXPORT ---
    @rx.event
    async def set_search_query(self, query: str) -> None:
        if self.search_query == query:
            return
        self.search_query = query
        self.page = 1
        await self.fetch_power_data()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
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
    async def export_watt_excel(self) -> Any:
        data_bytes = await api_client.generate_watt_excel_bytes(self.items)
        return rx.download(data=data_bytes, filename="Rekap_Watt_Server_ITAM_Pro.xlsx")

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
