"""
State Manajemen Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro (Tahap 9).
"""
import math
from datetime import date
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client

VALID_TABS = ("pembelian", "invoice", "tagihan")
TAB_LABELS = {"pembelian": "pembelian", "invoice": "invoice", "tagihan": "tagihan"}


class FinanceState(rx.State):
    """Controller State untuk Modul Finansial ITAM Pro."""

    active_tab: str = "pembelian"

    # State bersama (pencarian & paginasi tab aktif)
    total_items: int = 0
    page: int = 1
    page_size: int = 10
    search_query: str = ""

    # Tab 1: Rekap Pembelian
    purchases: list[dict[str, Any]] = []
    status_filter: str = "Semua"
    status_options: list[str] = [
        "Semua",
        "Belum dicatat",
        "Bukan aset",
        "1 aset dibuat",
        "2 aset dibuat",
        "3 aset dibuat",
        "4 aset dibuat",
        "5 aset dibuat",
    ]
    summary: dict[str, Any] = {
        "total_belanja": 0,
        "belanja_terbesar": 0,
        "belum_dicatat": 0,
    }

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

    # Modal "Jadikan Aset"
    is_asset_modal_open: bool = False
    selected_purchase_id: str = ""
    selected_purchase_title: str = ""
    asset_form_kategori: str = "PC"
    asset_form_lokasi: str = "Kantor Pusat"
    kategori_options: list[str] = ["PC", "Monitor", "Server", "UPS", "Lainnya"]
    lokasi_options: list[str] = [
        "Kantor Pusat",
        "Kantor Blok 14",
        "Server Room Lt.2",
        "Gudang IT",
    ]

    # --- COMPUTED PROPERTIES ---

    @rx.var
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 1
        return max(1, math.ceil(self.total_items / self.page_size))

    @rx.var
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var
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

    @rx.var
    def summary_text(self) -> str:
        label = TAB_LABELS.get(self.active_tab, "data")
        if self.total_items == 0:
            return f"Menampilkan 0 dari 0 {label}"
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return f"Menampilkan {start}-{end} dari {self.total_items} {label}"

    @rx.var
    def result_count_label(self) -> str:
        return f"{self.total_items} {TAB_LABELS.get(self.active_tab, 'data')}"

    @rx.var
    def total_belanja_display(self) -> str:
        val = int(self.summary.get("total_belanja", 0))
        return f"Rp {val:,}".replace(",", ".")

    @rx.var
    def belanja_terbesar_display(self) -> str:
        val = int(self.summary.get("belanja_terbesar", 0))
        return f"Rp {val:,}".replace(",", ".")

    @rx.var
    def belum_dicatat_count(self) -> int:
        return int(self.summary.get("belum_dicatat", 0))

    @rx.var
    def bills_perlu_dibayar_display(self) -> str:
        val = int(self.bills_summary.get("perlu_dibayar_30d", 0))
        return f"Rp{val:,}".replace(",", ".")

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
        params = self.router.page.params or {}
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
        filters = {"search": self.search_query, "aset_status": self.status_filter}
        res = await api_client.get_purchases(filters, self.page, self.page_size)
        self.purchases = res.get("items", [])
        self.total_items = int(res.get("total", 0))
        self.summary = res.get("summary", {})

    @rx.event
    async def fetch_invoices(self) -> None:
        filters = {"search": self.search_query, "tautan": self.invoice_link_filter}
        res = await api_client.get_invoices(filters, self.page, self.page_size)
        self.invoices = res.get("items", [])
        self.total_items = int(res.get("total", 0))
        self.invoices_summary = res.get("summary", {})

    @rx.event
    async def fetch_bills(self) -> None:
        filters = {"search": self.search_query, "status": self.bill_status_filter}
        res = await api_client.get_bills(filters, self.page, self.page_size)
        self.bills = res.get("items", [])
        self.total_items = int(res.get("total", 0))
        self.bills_summary = res.get("summary", {})

    # --- TAB & FILTER ---

    @rx.event
    def set_tab(self, tab: str):
        self.active_tab = tab
        self.search_query = ""
        self.page = 1
        return rx.redirect(f"/finance/purchases?tab={tab}")

    @rx.event
    async def set_search_query(self, val: str) -> None:
        self.search_query = val
        self.page = 1
        await self._refetch()

    @rx.event
    async def set_status_filter(self, val: str) -> None:
        self.status_filter = val
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_invoice_link_filter(self, val: str) -> None:
        self.invoice_link_filter = val
        self.page = 1
        await self.fetch_invoices()

    @rx.event
    async def set_bill_status_filter(self, val: str) -> None:
        self.bill_status_filter = val
        self.page = 1
        await self.fetch_bills()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.status_filter = "Semua"
        self.invoice_link_filter = "Semua"
        self.bill_status_filter = "Semua"
        self.page = 1
        await self._refetch()

    # --- MODAL JADIKAN ASET ---

    @rx.event
    def open_jadikan_aset_modal(self, purchase_id: str) -> None:
        self.selected_purchase_id = purchase_id
        for p in self.purchases:
            if p.get("id_pembelian") == purchase_id:
                self.selected_purchase_title = (
                    f"{p.get('produk', '')} ({p.get('pcs', 1)} unit)"
                )
                break
        self.asset_form_kategori = "PC"
        self.asset_form_lokasi = "Kantor Pusat"
        self.is_asset_modal_open = True

    @rx.event
    def close_asset_modal(self) -> None:
        self.is_asset_modal_open = False
        self.selected_purchase_id = ""
        self.selected_purchase_title = ""

    @rx.event
    def set_asset_form_kategori(self, val: str) -> None:
        self.asset_form_kategori = val

    @rx.event
    def set_asset_form_lokasi(self, val: str) -> None:
        self.asset_form_lokasi = val

    @rx.event
    async def submit_jadikan_aset(self) -> None:
        payload = {
            "kategori": self.asset_form_kategori,
            "kepemilikan": "XML",
            "lokasi": self.asset_form_lokasi,
        }
        await api_client.convert_purchase_to_asset(self.selected_purchase_id, payload)
        self.is_asset_modal_open = False
        await self.fetch_purchases()

    # --- MODAL TANDAI DIBAYAR ---

    @rx.event
    def open_pay_bill_modal(self, bill_id: str) -> None:
        for b in self.bills:
            if b.get("id") == bill_id:
                self.pay_bill_id = bill_id
                self.pay_bill_title = (
                    f"{b.get('nama', '')} · jatuh tempo {b.get('jatuh_tempo', '')}"
                )
                self.pay_nominal = str(b.get("nominal", ""))
                break
        else:
            return
        self.pay_date = date.today().isoformat()
        self.pay_error = ""
        self.is_pay_modal_open = True

    @rx.event
    def close_pay_modal(self) -> None:
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
        nominal_txt = self.pay_nominal.strip()
        if not self.pay_date or not nominal_txt.isdigit() or int(nominal_txt) <= 0:
            self.pay_error = "Tanggal bayar dan nominal (angka > 0) wajib diisi."
            return
        await api_client.pay_bill(self.pay_bill_id, self.pay_date, int(nominal_txt))
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
            if 1 <= target <= self.total_pages:
                self.page = target
                await self._refetch()


__all__ = ["FinanceState"]
