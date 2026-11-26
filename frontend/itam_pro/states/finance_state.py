"""
State Manajemen Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro (Tahap 9).
Dioptimalkan dengan @rx.var(cache=True), filter guards, dan parser nominal Rupiah yang aman.
"""

import csv
import io
import math
import re
from datetime import date
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.mock.finance_mock import (
    action_create_purchase,
    action_import_purchases,
    action_jadikan_aset,
)
from itam_pro.services.router_utils import get_current_params
from itam_pro.services.validators import format_rupiah, format_tanggal

VALID_TABS = ("pembelian", "invoice", "tagihan")
TAB_LABELS = {"pembelian": "pembelian", "invoice": "invoice", "tagihan": "tagihan"}


def _parse_int_safe(val: Any) -> int:
    """Ekstrak nilai integer dengan aman dari int, float, atau string format Rupiah."""
    if isinstance(val, bool) or val is None:
        return 0
    if isinstance(val, (int, float)):
        return round(val)
    if isinstance(val, str):
        text = val.strip()
        if not text:
            return 0
        # Jika string memuat keterangan tambahan seperti 'Rp 17.609.700 (Synology DS225+ incl)',
        # ambil bagian nominal di sebelah kiri tanda kurung '(' terlebih dahulu.
        nominal_part = text.split("(", 1)[0]
        digits = re.sub(r"[^\d]", "", nominal_part)
        if digits:
            return int(digits)
    return 0


class FinanceState(rx.State):
    """Controller State untuk Modul Finansial ITAM Pro."""

    active_tab: str = "pembelian"

    # State bersama (pencarian & paginasi tab aktif)
    total_items: int = 0
    page: int = 1
    page_size: int = 10
    search_query: str = ""

    # Tab 1: Rekap Pembelian — Filter, Kolom Opsional & Seleksi Massal
    purchases: list[dict[str, Any]] = []
    status_filter: str = "Semua"
    status_options: list[str] = [
        "Semua",
        "Belum didaftarkan",
        "Terdaftar",
        "Habis pakai · tidak perlu aset",
    ]
    marketplace_filter: str = "Semua"
    marketplace_options: list[str] = ["Semua", "Shopee", "Tokopedia", "Offline", "Lainnya"]
    period_filter: str = "Semua"
    period_options: list[str] = [
        "Semua",
        "Bulan ini",
        "3 bulan terakhir",
        "6 bulan terakhir",
        "Tahun ini",
    ]
    summary: dict[str, Any] = {
        "total_belanja": 0,
        "belanja_terbesar": 0,
        "belum_dicatat": 0,
        "total_all_purchases": 0,
        "nearest_bill_name": "—",
        "nearest_bill_note": "",
    }
    hidden_columns: list[str] = ["link_marketplace", "dibeli_oleh"]
    selected_purchase_ids: list[str] = []

    # Tab 2: Invoice (arsip bukti pembayaran)
    invoices: list[dict[str, Any]] = []
    invoice_link_filter: str = "Semua"
    invoice_link_options: list[str] = ["Semua", "Sudah ditautkan", "Belum ditautkan"]
    invoices_summary: dict[str, Any] = {
        "total_invoice": 0,
        "sudah_ditautkan": 0,
        "belum_ditautkan": 0,
        "tanpa_bukti": 0,
    }

    # Tab 3: Tagihan Berulang
    bills: list[dict[str, Any]] = []
    bill_status_filter: str = "Semua"
    bill_status_options: list[str] = ["Semua", "Terlambat", "Segera", "Terjadwal"]
    bills_summary: dict[str, Any] = {
        "terlambat": 0,
        "segera": 0,
        "tagihan_aktif": 0,
        "perlu_dibayar_30d": 0,
    }

    # Modal "Tandai Dibayar"
    is_pay_modal_open: bool = False
    pay_bill_id: str = ""
    pay_bill_title: str = ""
    pay_date: str = ""
    pay_nominal: str = ""
    pay_error: str = ""

    # Modal "Daftarkan jadi aset" (Seksi 10)
    is_asset_modal_open: bool = False
    selected_purchase_id: str = ""
    selected_purchase_title: str = ""
    selected_purchase_max_qty: int = 1
    asset_form_kategori: str = "PC"
    asset_form_lokasi: str = "Head Office (Office Blok 14)"
    asset_form_qty: str = "1"
    asset_form_garansi: str = ""
    asset_form_error: str = ""
    kategori_options: list[str] = [
        "PC",
        "Laptop",
        "Server",
        "Monitor",
        "UPS",
        "RAM",
        "SSD",
        "HDD",
        "VGA",
        "PSU",
        "Keyboard",
        "Mouse",
        "Router/Switch",
        "CCTV",
        "AC",
        "Lainnya",
    ]
    lokasi_options: list[str] = [
        "Head Office (Office Blok 14)",
        "White House (Office Blok 13)",
        "Office 437 (Office Blok 12)",
        "Mess (Mess Blok 12)",
        "Konter (Ruko Rinjani)",
        "Gudang",
    ]

    # Prefill & Mode Massal Modal Daftarkan Aset
    bulk_target_ids: list[str] = []
    asset_form_nama: str = ""
    asset_form_harga_display: str = ""
    asset_form_tanggal_display: str = ""

    # Modal + Catat Pembelian
    is_add_purchase_modal_open: bool = False
    new_purchase_tanggal: str = ""
    new_purchase_produk: str = ""
    new_purchase_harga: str = ""
    new_purchase_pcs: str = "1"
    new_purchase_toko: str = ""
    new_purchase_link: str = ""
    new_purchase_pembeli: str = "Ridho"
    new_purchase_status: str = "Belum didaftarkan"
    new_purchase_error: str = ""

    # Modal Import CSV Pembelian
    is_import_modal_open: bool = False
    import_csv_text: str = (
        "Tanggal,Produk,Harga,Pcs,Toko,Link Marketplace,Dibeli Oleh\n"
        "2026-11-20,SSD NVMe 512GB,650000,1,Shopee,https://shopee.co.id/ssd-nvme,Ridho"
    )
    import_error: str = ""
    import_success: str = ""

    # --- COMPUTED PROPERTIES ---

    @rx.var(cache=True)
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 1
        return max(1, math.ceil(self.total_items / self.page_size))

    @rx.var(cache=True)
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var(cache=True)
    def page_tokens(self) -> list[str]:
        tp = self.total_pages
        if tp <= 7:
            return [str(i) for i in range(1, tp + 1)]
        cur = self.page
        tokens = ["1"]
        if cur > 3:
            tokens.append("...")
        for i in range(max(2, cur - 1), min(tp, cur + 2)):
            tokens.append(str(i))
        if cur < tp - 2:
            tokens.append("...")
        tokens.append(str(tp))
        return tokens

    @rx.var(cache=True)
    def summary_text(self) -> str:
        label = TAB_LABELS.get(self.active_tab, "data")
        if self.total_items == 0:
            return f"Menampilkan 0 dari 0 {label}"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}–{end} dari {self.total_items} {label}"

    @rx.var(cache=True)
    def result_count_label(self) -> str:
        return f"{self.total_items} {TAB_LABELS.get(self.active_tab, 'data')}"

    @rx.var(cache=True)
    def total_belanja_display(self) -> str:
        return format_rupiah(_parse_int_safe(self.summary.get("total_belanja", 0)))

    @rx.var(cache=True)
    def belanja_terbesar_display(self) -> str:
        return format_rupiah(_parse_int_safe(self.summary.get("belanja_terbesar", 0)))

    @rx.var(cache=True)
    def belum_dicatat_count(self) -> int:
        return _parse_int_safe(self.summary.get("belum_dicatat", 0))

    @rx.var(cache=True)
    def filtered_purchases_note(self) -> str:
        return f"{self.total_items} pembelian"

    @rx.var(cache=True)
    def belum_dicatat_note(self) -> str:
        total_all = _parse_int_safe(
            self.summary.get("total_all_purchases", self.total_items)
        )
        return f"dari {total_all} pembelian"

    @rx.var(cache=True)
    def nearest_bill_name(self) -> str:
        return str(self.summary.get("nearest_bill_name") or "—")

    @rx.var(cache=True)
    def nearest_bill_note(self) -> str:
        return str(self.summary.get("nearest_bill_note") or "")

    @rx.var(cache=True)
    def bills_perlu_dibayar_display(self) -> str:
        return format_rupiah(_parse_int_safe(self.bills_summary.get("perlu_dibayar_30d", 0)))

    @rx.var(cache=True)
    def selected_purchases_count(self) -> int:
        return len(self.selected_purchase_ids)

    @rx.var(cache=True)
    def has_selected_purchases(self) -> bool:
        return len(self.selected_purchase_ids) > 0

    @rx.var(cache=True)
    def selected_purchases_label(self) -> str:
        return f"{len(self.selected_purchase_ids)} pembelian dipilih"

    @rx.var(cache=True)
    def all_purchases_selected(self) -> bool:
        if not self.purchases or not self.selected_purchase_ids:
            return False
        selected = set(self.selected_purchase_ids)
        return all(str(p.get("id_pembelian", "")) in selected for p in self.purchases)

    @rx.var(cache=True)
    def is_bulk_register_mode(self) -> bool:
        return len(self.bulk_target_ids) > 1

    @rx.var(cache=True)
    def is_link_col_visible(self) -> bool:
        return "link_marketplace" not in self.hidden_columns

    @rx.var(cache=True)
    def is_buyer_col_visible(self) -> bool:
        return "dibeli_oleh" not in self.hidden_columns

    # --- FETCH ---

    async def _refetch(self) -> None:
        if self.active_tab == "invoice":
            await self.fetch_invoices()
        elif self.active_tab == "tagihan":
            await self.fetch_bills()
        else:
            await self.fetch_purchases()

    @rx.event
    async def load_finance_page(self) -> None:
        params = get_current_params(self.router)
        tab = str(params.get("tab", "pembelian"))
        if tab not in VALID_TABS:
            tab = "pembelian"
        if tab != self.active_tab:
            self.search_query = ""
            self.page = 1
        self.active_tab = tab
        await self._refetch()

    @rx.event
    async def fetch_purchases(self) -> None:
        filters = {
            "search": self.search_query,
            "aset_status": self.status_filter,
            "marketplace": self.marketplace_filter,
            "periode": self.period_filter,
        }
        res = await api_client.get_purchases(filters, self.page, self.page_size)
        self.purchases = res.get("items", [])
        self.total_items = _parse_int_safe(res.get("total", 0))
        raw_summary = res.get("summary") or {}
        self.summary = {
            **raw_summary,
            "total_belanja": _parse_int_safe(raw_summary.get("total_belanja", 0)),
            "belanja_terbesar": _parse_int_safe(raw_summary.get("belanja_terbesar", 0)),
            "belum_dicatat": _parse_int_safe(raw_summary.get("belum_dicatat", 0)),
            "total_all_purchases": _parse_int_safe(
                raw_summary.get("total_all_purchases", self.total_items)
            ),
            "nearest_bill_name": str(raw_summary.get("nearest_bill_name") or "—"),
            "nearest_bill_note": str(raw_summary.get("nearest_bill_note") or ""),
        }

    @rx.event
    async def fetch_invoices(self) -> None:
        filters = {"search": self.search_query, "tautan": self.invoice_link_filter}
        res = await api_client.get_invoices(filters, self.page, self.page_size)
        self.invoices = res.get("items", [])
        self.total_items = _parse_int_safe(res.get("total", 0))
        raw_summary = res.get("summary") or {}
        self.invoices_summary = {
            **raw_summary,
            "total_invoice": _parse_int_safe(raw_summary.get("total_invoice", 0)),
            "sudah_ditautkan": _parse_int_safe(raw_summary.get("sudah_ditautkan", 0)),
            "belum_ditautkan": _parse_int_safe(raw_summary.get("belum_ditautkan", 0)),
            "tanpa_bukti": _parse_int_safe(raw_summary.get("tanpa_bukti", 0)),
        }

    @rx.event
    async def fetch_bills(self) -> None:
        filters = {"search": self.search_query, "status": self.bill_status_filter}
        res = await api_client.get_bills(filters, self.page, self.page_size)
        self.bills = res.get("items", [])
        self.total_items = _parse_int_safe(res.get("total", 0))
        raw_summary = res.get("summary") or {}
        self.bills_summary = {
            **raw_summary,
            "terlambat": _parse_int_safe(raw_summary.get("terlambat", 0)),
            "segera": _parse_int_safe(raw_summary.get("segera", 0)),
            "tagihan_aktif": _parse_int_safe(raw_summary.get("tagihan_aktif", 0)),
            "perlu_dibayar_30d": _parse_int_safe(raw_summary.get("perlu_dibayar_30d", 0)),
        }

    # --- TAB & FILTER ---

    @rx.event
    def set_tab(self, tab: str):
        if self.active_tab == tab and self.page == 1 and not self.search_query:
            return rx.redirect(f"/finance/purchases?tab={tab}")
        self.active_tab = tab
        self.search_query = ""
        self.page = 1
        return rx.redirect(f"/finance/purchases?tab={tab}")

    @rx.event
    async def set_search_query(self, val: str) -> None:
        if self.search_query == val:
            return
        self.search_query = val
        self.page = 1
        await self._refetch()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        if self.status_filter == val:
            return
        self.status_filter = val
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_marketplace_filter(self, val: str) -> None:
        if self.marketplace_filter == val:
            return
        self.marketplace_filter = val
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_period_filter(self, val: str) -> None:
        if self.period_filter == val:
            return
        self.period_filter = val
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_invoice_link_filter(self, val: str) -> None:
        if self.invoice_link_filter == val:
            return
        self.invoice_link_filter = val
        self.page = 1
        await self.fetch_invoices()

    @rx.event
    async def set_bill_status_filter(self, val: str) -> None:
        if self.bill_status_filter == val:
            return
        self.bill_status_filter = val
        self.page = 1
        await self.fetch_bills()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.status_filter = "Semua"
        self.marketplace_filter = "Semua"
        self.period_filter = "Semua"
        self.invoice_link_filter = "Semua"
        self.bill_status_filter = "Semua"
        self.page = 1
        await self._refetch()

    @rx.event
    def toggle_column_visibility(self, col_key: str, _checked: Any = None) -> None:
        if col_key in self.hidden_columns:
            self.hidden_columns = [k for k in self.hidden_columns if k != col_key]
        else:
            self.hidden_columns = [*self.hidden_columns, col_key]

    @rx.event
    def toggle_purchase_selection(self, purchase_id: str, _checked: Any = None) -> None:
        if purchase_id in self.selected_purchase_ids:
            self.selected_purchase_ids = [
                x for x in self.selected_purchase_ids if x != purchase_id
            ]
        else:
            self.selected_purchase_ids = [*self.selected_purchase_ids, purchase_id]

    @rx.event
    def toggle_select_all_purchases(self, _checked: Any = None) -> None:
        page_ids = [
            str(p.get("id_pembelian", "")) for p in self.purchases if p.get("id_pembelian")
        ]
        if self.all_purchases_selected:
            self.selected_purchase_ids = [
                x for x in self.selected_purchase_ids if x not in page_ids
            ]
        else:
            merged = list(self.selected_purchase_ids)
            for pid in page_ids:
                if pid not in merged:
                    merged.append(pid)
            self.selected_purchase_ids = merged

    @rx.event
    def clear_purchase_selection(self) -> None:
        self.selected_purchase_ids = []

    # --- MODAL DAFTARKAN JADI ASET (SEKSI 10) ---

    def _guess_kategori(self, produk: str) -> str:
        low = produk.lower()
        if "ram" in low:
            return "RAM"
        if "ssd" in low:
            return "SSD"
        if "hdd" in low:
            return "HDD"
        if "monitor" in low:
            return "Monitor"
        if "ups" in low:
            return "UPS"
        if "cctv" in low:
            return "CCTV"
        if "switch" in low or "router" in low:
            return "Router/Switch"
        if "keyboard" in low:
            return "Keyboard"
        if "mouse" in low:
            return "Mouse"
        return "PC"

    @rx.event
    def open_jadikan_aset_modal(self, purchase_id: str) -> None:
        self.bulk_target_ids = [purchase_id]
        self.selected_purchase_id = purchase_id
        self.asset_form_error = ""
        for p in self.purchases:
            if p.get("id_pembelian") == purchase_id:
                pcs_val = int(p.get("pcs", 1) or 1)
                reg_cnt = int(p.get("registered_count", 0) or 0)
                sisa = max(1, pcs_val - reg_cnt)
                self.selected_purchase_max_qty = sisa
                self.asset_form_qty = str(sisa)
                self.asset_form_nama = str(p.get("produk", ""))
                self.asset_form_harga_display = str(
                    p.get("harga_display") or format_rupiah(p.get("harga", 0))
                )
                self.asset_form_tanggal_display = str(
                    p.get("tanggal_display") or format_tanggal(p.get("tanggal", ""))
                )
                self.selected_purchase_title = (
                    f"{purchase_id} · Maks. {sisa} dari {pcs_val} unit"
                )
                self.asset_form_kategori = self._guess_kategori(self.asset_form_nama)
                break
        self.asset_form_lokasi = (
            "Gudang"
            if self.asset_form_kategori in ("RAM", "SSD", "HDD", "VGA", "PSU")
            else "Head Office (Office Blok 14)"
        )
        self.is_asset_modal_open = True

    @rx.event
    def open_bulk_asset_modal(self) -> None:
        if not self.selected_purchase_ids:
            return
        if len(self.selected_purchase_ids) == 1:
            self.open_jadikan_aset_modal(self.selected_purchase_ids[0])
            return
        self.bulk_target_ids = list(self.selected_purchase_ids)
        self.selected_purchase_id = self.selected_purchase_ids[0]
        self.asset_form_error = ""
        self.asset_form_nama = f"{len(self.bulk_target_ids)} pembelian terpilih"
        selected_rows = [
            p for p in self.purchases if p.get("id_pembelian") in self.bulk_target_ids
        ]
        total_val = sum(int(p.get("total", 0) or 0) for p in selected_rows)
        self.asset_form_harga_display = format_rupiah(total_val)
        self.asset_form_tanggal_display = (
            str(selected_rows[0].get("tanggal_display", "—")) if selected_rows else "—"
        )
        self.selected_purchase_title = (
            f"Daftarkan {len(self.bulk_target_ids)} pembelian sekaligus (purchase_id tertaut)"
        )
        self.selected_purchase_max_qty = 999
        self.asset_form_qty = "1"
        self.asset_form_kategori = (
            self._guess_kategori(str(selected_rows[0].get("produk", "")))
            if selected_rows
            else "PC"
        )
        self.asset_form_lokasi = "Head Office (Office Blok 14)"
        self.is_asset_modal_open = True

    @rx.event
    def close_asset_modal(self) -> None:
        if self.is_asset_modal_open:
            self.is_asset_modal_open = False
        self.selected_purchase_id = ""
        self.selected_purchase_title = ""
        self.asset_form_error = ""

    @rx.event
    def set_asset_form_nama(self, val: str) -> None:
        self.asset_form_nama = val

    @rx.event
    def set_asset_form_kategori(self, val: str) -> None:
        self.asset_form_kategori = val
        if val in ("RAM", "SSD", "HDD", "VGA", "PSU"):
            self.asset_form_lokasi = "Gudang"

    @rx.event
    def set_asset_form_lokasi(self, val: str) -> None:
        self.asset_form_lokasi = val

    @rx.event
    def set_asset_form_qty(self, val: str) -> None:
        self.asset_form_qty = val

    @rx.event
    def set_asset_form_garansi(self, val: str) -> None:
        self.asset_form_garansi = val

    @rx.event
    async def submit_bukan_aset(self) -> None:
        targets = self.bulk_target_ids or (
            [self.selected_purchase_id] if self.selected_purchase_id else []
        )
        for pid in targets:
            await api_client.convert_purchase_to_asset(
                pid,
                {"bukan_aset": True, "kategori": "Bukan aset"},
            )
        self.is_asset_modal_open = False
        self.bulk_target_ids = []
        self.selected_purchase_ids = []
        await self.fetch_purchases()

    @rx.event
    async def submit_jadikan_aset(self) -> None:
        targets = self.bulk_target_ids or (
            [self.selected_purchase_id] if self.selected_purchase_id else []
        )
        if len(targets) > 1:
            for pid in targets:
                action_jadikan_aset(
                    id_pembelian=pid,
                    kategori=self.asset_form_kategori,
                    kepemilikan="XML",
                    lokasi=self.asset_form_lokasi,
                    garansi_sampai=self.asset_form_garansi.strip() or None,
                )
        else:
            try:
                qty_int = int(self.asset_form_qty.strip() or "1")
            except ValueError:
                self.asset_form_error = "Jumlah unit harus berupa angka bulat."
                return
            if qty_int < 1 or qty_int > self.selected_purchase_max_qty:
                self.asset_form_error = (
                    f"Jumlah unit harus antara 1 sampai {self.selected_purchase_max_qty}."
                )
                return
            action_jadikan_aset(
                id_pembelian=self.selected_purchase_id,
                kategori=self.asset_form_kategori,
                kepemilikan="XML",
                lokasi=self.asset_form_lokasi,
                jumlah_daftar=qty_int,
                nama_aset=self.asset_form_nama.strip() or None,
                garansi_sampai=self.asset_form_garansi.strip() or None,
            )

        self.is_asset_modal_open = False
        self.bulk_target_ids = []
        self.selected_purchase_ids = []
        await self.fetch_purchases()

    # --- MODAL CATAT PEMBELIAN, IMPORT CSV, & EXPORT CSV ---

    @rx.event
    def open_add_purchase_modal(self) -> None:
        self.new_purchase_tanggal = date.today().isoformat()
        self.new_purchase_produk = ""
        self.new_purchase_harga = ""
        self.new_purchase_pcs = "1"
        self.new_purchase_toko = ""
        self.new_purchase_link = ""
        self.new_purchase_pembeli = "Ridho"
        self.new_purchase_status = "Belum didaftarkan"
        self.new_purchase_error = ""
        self.is_add_purchase_modal_open = True

    @rx.event
    def close_add_purchase_modal(self) -> None:
        self.is_add_purchase_modal_open = False
        self.new_purchase_error = ""

    @rx.event
    def set_new_purchase_tanggal(self, val: str) -> None:
        self.new_purchase_tanggal = val

    @rx.event
    def set_new_purchase_produk(self, val: str) -> None:
        self.new_purchase_produk = val

    @rx.event
    def set_new_purchase_harga(self, val: str) -> None:
        self.new_purchase_harga = val

    @rx.event
    def set_new_purchase_pcs(self, val: str) -> None:
        self.new_purchase_pcs = val

    @rx.event
    def set_new_purchase_toko(self, val: str) -> None:
        self.new_purchase_toko = val

    @rx.event
    def set_new_purchase_link(self, val: str) -> None:
        self.new_purchase_link = val

    @rx.event
    def set_new_purchase_pembeli(self, val: str) -> None:
        self.new_purchase_pembeli = val

    @rx.event
    def set_new_purchase_status(self, val: str) -> None:
        self.new_purchase_status = val

    @rx.event
    async def submit_new_purchase(self) -> None:
        self.new_purchase_error = ""
        harga = _parse_int_safe(self.new_purchase_harga)
        pcs = _parse_int_safe(self.new_purchase_pcs)
        if not self.new_purchase_produk.strip():
            self.new_purchase_error = "Nama produk wajib diisi."
            return
        if harga <= 0 or pcs < 1:
            self.new_purchase_error = "Harga satuan (> 0) dan Pcs (>= 1) wajib valid."
            return
        try:
            action_create_purchase(
                {
                    "tanggal": self.new_purchase_tanggal or date.today().isoformat(),
                    "produk": self.new_purchase_produk.strip(),
                    "harga": harga,
                    "pcs": pcs,
                    "nama_toko": self.new_purchase_toko.strip() or "Offline",
                    "link_marketplace": self.new_purchase_link.strip(),
                    "dibeli_oleh": self.new_purchase_pembeli.strip() or "Ridho",
                    "aset_status": (
                        "Bukan aset"
                        if self.new_purchase_status == "Habis pakai · tidak perlu aset"
                        else "Belum didaftarkan"
                    ),
                }
            )
        except ValueError as exc:
            self.new_purchase_error = str(exc)
            return
        self.is_add_purchase_modal_open = False
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    def open_import_modal(self) -> None:
        self.import_error = ""
        self.import_success = ""
        self.is_import_modal_open = True

    @rx.event
    def close_import_modal(self) -> None:
        self.is_import_modal_open = False

    @rx.event
    def set_import_csv_text(self, val: str) -> None:
        self.import_csv_text = val

    @rx.event
    async def submit_import_csv(self) -> None:
        self.import_error = ""
        self.import_success = ""
        imported, errs = action_import_purchases(self.import_csv_text)
        if errs:
            self.import_error = " · ".join(errs[:3])
        if imported > 0:
            self.import_success = f"{imported} pembelian berhasil diimpor."
            self.page = 1
            await self.fetch_purchases()
            if not errs:
                self.is_import_modal_open = False

    @rx.event
    def export_purchases_csv(self) -> Any:
        """Unduh CSV pembelian sesuai filter halaman saat ini."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "Tanggal",
                "Produk",
                "Harga Satuan",
                "Pcs",
                "Total",
                "Toko",
                "Link Marketplace",
                "Dibeli Oleh",
                "Status Aset",
            ]
        )
        for p in self.purchases:
            writer.writerow(
                [
                    p.get("tanggal_display", p.get("tanggal", "")),
                    p.get("produk", ""),
                    p.get("harga_display", p.get("harga", 0)),
                    p.get("pcs", 1),
                    p.get("total_display", p.get("total", 0)),
                    p.get("toko_chip", p.get("nama_toko", "")),
                    p.get("link_marketplace", ""),
                    p.get("dibeli_oleh", ""),
                    p.get("aset_status_label", p.get("aset_status", "")),
                ]
            )
        return rx.download(data=buf.getvalue(), filename="Rekap_Pembelian_ITAM_Pro.csv")

    # --- MODAL TANDAI DIBAYAR ---

    @rx.event
    def open_pay_bill_modal(self, bill_id: str) -> None:
        for b in self.bills:
            if b.get("id") == bill_id:
                self.pay_bill_id = bill_id
                self.pay_bill_title = (
                    f"{b.get('nama', '')} · jatuh tempo {b.get('jatuh_tempo', '')}"
                )
                raw_nom = b.get("nominal", "")
                self.pay_nominal = str(_parse_int_safe(raw_nom)) if raw_nom else ""
                break
        else:
            return
        self.pay_date = date.today().isoformat()
        self.pay_error = ""
        self.is_pay_modal_open = True

    @rx.event
    def close_pay_modal(self) -> None:
        if self.is_pay_modal_open:
            self.is_pay_modal_open = False
        self.pay_bill_id = ""
        self.pay_error = ""

    @rx.event
    def set_pay_date(self, val: str) -> None:
        self.pay_date = val

    @rx.event
    def set_pay_nominal(self, val: str) -> None:
        self.pay_nominal = val

    @rx.event
    async def submit_pay_bill(self) -> None:
        nominal_val = _parse_int_safe(self.pay_nominal)
        if not self.pay_date or nominal_val <= 0:
            self.pay_error = "Tanggal bayar dan nominal (angka > 0) wajib diisi."
            return
        await api_client.pay_bill(self.pay_bill_id, self.pay_date, nominal_val)
        self.is_pay_modal_open = False
        self.pay_error = ""
        await self.fetch_bills()

    # --- PAGINASI ---

    @rx.event
    async def go_to_previous_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            await self._refetch()

    @rx.event
    async def go_to_next_page(self) -> None:
        if self.page < self.total_pages:
            self.page += 1
            await self._refetch()

    @rx.event
    async def select_page(self, token: str) -> None:
        if token.isdigit():
            target = int(token)
            if 1 <= target <= self.total_pages and target != self.page:
                self.page = target
                await self._refetch()


__all__ = ["FinanceState"]
