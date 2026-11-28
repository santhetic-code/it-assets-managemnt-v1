"""
State Manajemen Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro (Tahap 9).
Dioptimalkan dengan @rx.var(cache=True), filter guards, dan parser nominal Rupiah yang aman.
"""

import csv
import io
import math
import re
from datetime import date, timedelta
from typing import Any

import reflex as rx

from itam_pro.config import USE_MOCK
from itam_pro.services.api_client import api_client
from itam_pro.services.mock.finance_mock import (
    MOCK_BILLS,
    MOCK_INVOICES,
    MOCK_PURCHASES,
    _is_consumable_product,
    _status_display_meta,
    action_create_purchase,
    action_import_purchases,
    action_jadikan_aset,
    parse_marketplace_domain,
)
from itam_pro.services.recurrence import calculate_bill_status
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


def _normalize_purchase_item(raw: dict[str, Any], seq_no: int = 1) -> dict[str, Any]:
    """Normalisasi satu baris pembelian agar seluruh kolom UI terisi di Mock & Backend."""
    row = dict(raw)
    pid = str(
        row.get("id_pembelian")
        or row.get("kode_pembelian")
        or row.get("id")
        or f"PO-{seq_no:03d}"
    ).strip()
    tgl_raw = str(row.get("tanggal") or row.get("tanggal_beli") or "").strip()
    produk = (
        str(
            row.get("produk") or row.get("nama_item") or row.get("nama_barang") or "—"
        ).strip()
        or "—"
    )

    harga_raw = (
        row.get("harga") if row.get("harga") is not None else row.get("harga_satuan", 0)
    )
    pcs_raw = row.get("pcs") if row.get("pcs") is not None else row.get("jumlah", 1)
    total_raw = (
        row.get("total") if row.get("total") is not None else row.get("total_harga", 0)
    )

    harga = _parse_int_safe(harga_raw)
    pcs = max(1, _parse_int_safe(pcs_raw))
    total = _parse_int_safe(total_raw) or (harga * pcs)

    link_mp = str(row.get("link_marketplace") or "").strip()
    if not link_mp:
        ket = str(row.get("keterangan") or "").strip()
        if ket.startswith(("http://", "https://")):
            link_mp = ket

    nama_toko = str(row.get("nama_toko") or row.get("vendor") or "").strip()
    toko_chip = str(row.get("toko_chip") or "").strip()
    if not toko_chip:
        dom = str(row.get("domain_chip") or "").strip()
        if dom and dom not in ("-", "—", "URL Invalid", "None"):
            toko_chip = dom
        elif link_mp:
            try:
                toko_chip = parse_marketplace_domain(link_mp) or ""
            except ValueError:
                toko_chip = ""
        if not toko_chip:
            toko_low = nama_toko.lower()
            if "shopee" in toko_low:
                toko_chip = "Shopee"
            elif "tokopedia" in toko_low:
                toko_chip = "Tokopedia"
            elif nama_toko and nama_toko not in ("-", "—"):
                toko_chip = nama_toko
            else:
                toko_chip = "Offline"

    dibeli_oleh = (
        str(row.get("dibeli_oleh") or row.get("penanggung_jawab") or "—").strip() or "—"
    )

    # Normalisasi status aset dari mock maupun kolom `id_aset` backend
    id_aset_str = str(row.get("id_aset") or "").strip()
    reg_list = list(row.get("registered_assets") or [])
    if id_aset_str.upper() == "BUKAN-ASET":
        raw_status = "Bukan aset"
        reg_count = 0
    elif id_aset_str and id_aset_str not in ("-", "—"):
        codes = [x.strip() for x in id_aset_str.split(",") if x.strip()]
        reg_count = len(codes)
        raw_status = (
            f"Terdaftar ({reg_count} aset)"
            if reg_count >= pcs
            else f"Sebagian ({reg_count}/{pcs})"
        )
    elif row.get("aset_status"):
        raw_status = str(row.get("aset_status"))
        reg_count = len(reg_list) if reg_list else int(row.get("registered_count") or 0)
    else:
        raw_status = (
            "Bukan aset" if _is_consumable_product(produk) else "Belum didaftarkan"
        )
        reg_count = 0

    status_label, status_variant = _status_display_meta(raw_status)

    row.update(
        {
            "no": int(row.get("no") or seq_no),
            "id": pid,
            "id_pembelian": pid,
            "tanggal": tgl_raw,
            "tanggal_display": format_tanggal(tgl_raw),
            "produk": produk,
            "harga": harga,
            "harga_display": format_rupiah(harga),
            "pcs": pcs,
            "total": total,
            "total_display": format_rupiah(total),
            "nama_toko": nama_toko or toko_chip,
            "toko_chip": toko_chip,
            "link_marketplace": link_mp,
            "dibeli_oleh": dibeli_oleh,
            "aset_status": raw_status,
            "aset_status_label": status_label,
            "aset_status_variant": status_variant,
            "registered_count": reg_count,
        }
    )
    return row


def _normalize_invoice_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalisasi satu baris Invoice untuk Mock & Backend."""
    row = dict(raw)
    no_inv = str(
        row.get("no_invoice")
        or row.get("nomor_invoice")
        or row.get("kode_pembelian")
        or "—"
    ).strip()
    tgl_raw = str(row.get("tanggal") or row.get("tanggal_beli") or "").strip()
    total_val = _parse_int_safe(
        row.get("total") if row.get("total") is not None else row.get("total_harga", 0)
    )
    terkait_id = str(row.get("terkait_id") or row.get("id_aset") or "").strip()
    is_linked = bool(row.get("terkait_tipe")) or (
        bool(terkait_id) and terkait_id not in ("-", "—", "BUKAN-ASET")
    )
    terkait_lbl = str(row.get("terkait_label") or "").strip()
    if not terkait_lbl or terkait_lbl in ("-", "—"):
        terkait_lbl = f"Terkait · {terkait_id}" if is_linked else "Belum ditautkan"

    row.update(
        {
            "no_invoice": no_inv,
            "tanggal": tgl_raw,
            "tanggal_display": format_tanggal(tgl_raw),
            "vendor": str(row.get("vendor") or row.get("nama_toko") or "—").strip()
            or "—",
            "total": total_val,
            "total_rp_display": format_rupiah(total_val),
            "berkas": str(row.get("berkas") or "—").strip() or "—",
            "terkait_label": terkait_lbl,
            "tautan_variant": "success" if is_linked else "warning",
        }
    )
    return row


_BILL_VARIANT_MAP = {"Terlambat": "danger", "Segera": "warning", "Terjadwal": "info"}


def _normalize_bill_item(
    raw: dict[str, Any], today: date | None = None
) -> dict[str, Any]:
    """Normalisasi satu baris Tagihan Berulang untuk Mock & Backend."""
    ref = today or date.today()
    row = dict(raw)
    bid = str(row.get("id") or row.get("kode_pembelian") or "").strip()
    nama = str(row.get("nama") or row.get("nama_item") or "—").strip() or "—"
    nominal_val = _parse_int_safe(
        row.get("nominal")
        if row.get("nominal") is not None
        else (row.get("total_harga") or row.get("harga_satuan") or 0)
    )
    jt_raw = str(
        row.get("jatuh_tempo") or row.get("tanggal_jatuh_tempo") or ""
    ).strip()
    pengingat_hari = _parse_int_safe(row.get("pengingat_hari", 7)) or 7

    status_val = str(row.get("status") or "").strip()
    status_lbl = str(row.get("status_label") or "").strip()
    if jt_raw and len(jt_raw) >= 10:
        try:
            info = calculate_bill_status(jt_raw[:10], pengingat_hari, ref)
            status_val = info["status"]
            status_lbl = info["label"]
        except ValueError:
            pass
    if not status_val:
        status_val = "Terjadwal"
    if not status_lbl:
        status_lbl = status_val

    row.update(
        {
            "id": bid,
            "nama": nama,
            "vendor": str(row.get("vendor") or "—").strip() or "—",
            "kategori": str(row.get("kategori") or "Lainnya").strip() or "Lainnya",
            "periode": str(
                row.get("periode") or row.get("siklus_tagihan") or "Bulanan"
            ).strip(),
            "nominal": nominal_val,
            "nominal_rp_display": format_rupiah(nominal_val),
            "jatuh_tempo": jt_raw,
            "jatuh_tempo_display": format_tanggal(jt_raw),
            "pengingat_hari": pengingat_hari,
            "pengingat_display": str(
                row.get("pengingat_display") or f"{pengingat_hari} hari sebelumnya"
            ),
            "pembayar": str(
                row.get("pembayar") or row.get("penanggung_jawab") or "—"
            ).strip(),
            "status": status_val,
            "status_label": status_lbl,
            "status_variant": _BILL_VARIANT_MAP.get(status_val, "info"),
            "aktif": bool(row.get("aktif", True)),
        }
    )
    return row


def _compute_nearest_bill(
    bills: list[dict[str, Any]], today: date | None = None
) -> tuple[str, str]:
    """Hitung tagihan berulang aktif terdekat (nama + tanggal jatuh tempo)."""
    ref = today or date.today()
    active = [
        b
        for b in bills
        if b.get("aktif", True) and str(b.get("status", "")).lower() != "dibatalkan"
    ]
    if not active:
        return ("Belum ada tagihan", "tidak ada tagihan aktif")

    dated: list[tuple[date, dict[str, Any]]] = []
    for b in active:
        raw_jt = str(b.get("jatuh_tempo") or "")[:10]
        try:
            dated.append((date.fromisoformat(raw_jt), b))
        except ValueError:
            continue

    if not dated:
        first = active[0]
        return (str(first.get("nama") or "Tagihan"), "jatuh tempo belum diatur")

    upcoming = [(d, b) for d, b in dated if d >= ref]
    pool = upcoming if upcoming else dated
    pool.sort(key=lambda pair: pair[0])
    due_dt, nearest = pool[0]
    nama_lbl = str(nearest.get("nama") or nearest.get("kategori") or "Tagihan")
    h_days = _parse_int_safe(nearest.get("pengingat_hari", 7)) or 7
    return (nama_lbl, f"jatuh tempo {format_tanggal(due_dt)} · pengingat H-{h_days}")


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
    status_filter: str = ""
    status_options: list[str] = [
        "Belum didaftarkan",
        "Terdaftar",
        "Habis pakai · tidak perlu aset",
    ]
    marketplace_filter: str = ""
    marketplace_options: list[str] = ["Shopee", "Tokopedia", "Offline", "Lainnya"]
    period_filter: str = ""
    period_options: list[str] = [
        "Bulan ini",
        "3 bulan terakhir",
        "6 bulan terakhir",
        "Tahun ini",
    ]
    summary: dict[str, Any] = {
        "total_belanja": 0,
        "belanja_terbesar": 0,
        "belum_dicatat": 0,
        "registered_purchases": 0,
        "total_all_purchases": 0,
        "nearest_bill_name": "Belum ada tagihan",
        "nearest_bill_note": "tidak ada tagihan aktif",
    }
    tab_counts: dict[str, int] = {
        "pembelian": 0,
        "invoice": 0,
        "tagihan": 0,
    }
    hidden_columns: list[str] = ["link_marketplace", "dibeli_oleh"]
    selected_purchase_ids: list[str] = []

    # Tab 2: Invoice (arsip bukti pembayaran)
    invoices: list[dict[str, Any]] = []
    invoice_link_filter: str = ""
    invoice_link_options: list[str] = ["Sudah ditautkan", "Belum ditautkan"]
    invoices_summary: dict[str, int] = {
        "total_invoice": 0,
        "sudah_ditautkan": 0,
        "belum_ditautkan": 0,
        "tanpa_bukti": 0,
    }

    # Tab 3: Tagihan Berulang
    bills: list[dict[str, Any]] = []
    bill_status_filter: str = ""
    bill_status_options: list[str] = ["Terlambat", "Segera", "Terjadwal"]
    bills_summary: dict[str, int] = {
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
        val = str(self.summary.get("nearest_bill_name") or "").strip()
        return val if val and val not in ("-", "—") else "Belum ada tagihan"

    @rx.var(cache=True)
    def nearest_bill_note(self) -> str:
        return str(self.summary.get("nearest_bill_note") or "tidak ada tagihan aktif")

    @rx.var(cache=True)
    def registered_percent(self) -> int:
        """Persentase pembelian yang sudah terdaftar sebagai aset (donut Hero Tab 1)."""
        total_all = _parse_int_safe(
            self.summary.get("total_all_purchases", self.total_items)
        )
        if total_all <= 0:
            return 0
        reg = _parse_int_safe(self.summary.get("registered_purchases", 0))
        return min(100, round((reg / total_all) * 100))

    @rx.var(cache=True)
    def invoice_linked_percent(self) -> int:
        """Persentase invoice yang sudah ditautkan (donut Hero Tab 2)."""
        total_inv = _parse_int_safe(self.invoices_summary.get("total_invoice", 0))
        if total_inv <= 0:
            return 0
        linked = _parse_int_safe(self.invoices_summary.get("sudah_ditautkan", 0))
        return min(100, round((linked / total_inv) * 100))

    @rx.var(cache=True)
    def bills_urgent_percent(self) -> int:
        """Persentase tagihan terlambat/segera dari tagihan aktif (donut Hero Tab 3)."""
        aktif = _parse_int_safe(self.bills_summary.get("tagihan_aktif", 0))
        if aktif <= 0:
            return 0
        urgent = _parse_int_safe(
            self.bills_summary.get("terlambat", 0)
        ) + _parse_int_safe(self.bills_summary.get("segera", 0))
        return min(100, round((urgent / aktif) * 100))

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

    def _update_tab_counts_from_res(self, res: dict[str, Any]) -> None:
        tc = res.get("tab_counts") or {}
        if tc:
            self.tab_counts = {
                "pembelian": _parse_int_safe(
                    tc.get("Pembelian", self.tab_counts["pembelian"])
                ),
                "invoice": _parse_int_safe(
                    tc.get("Invoice", self.tab_counts["invoice"])
                ),
                "tagihan": _parse_int_safe(
                    tc.get("Tagihan Berulang", self.tab_counts["tagihan"])
                ),
            }
        elif USE_MOCK:
            self.tab_counts = {
                "pembelian": len(MOCK_PURCHASES),
                "invoice": len(MOCK_INVOICES),
                "tagihan": sum(1 for b in MOCK_BILLS if b.get("aktif", True)),
            }

    @rx.event
    async def fetch_purchases(self) -> None:
        ref = date.today()
        if USE_MOCK:
            filters = {
                "search": self.search_query,
                "aset_status": self.status_filter or "Semua",
                "marketplace": self.marketplace_filter or "Semua",
                "periode": self.period_filter or "Semua",
            }
            res = await api_client.get_purchases(filters, self.page, self.page_size)
            self.purchases = [
                _normalize_purchase_item(it, idx)
                for idx, it in enumerate(res.get("items") or [], start=1)
            ]
            self.total_items = _parse_int_safe(res.get("total", len(self.purchases)))
            raw_summary = res.get("summary") or {}
            reg_cnt = sum(
                1
                for p in MOCK_PURCHASES
                if str(p.get("aset_status", "")).lower().startswith("terdaftar")
            )
            nearest_name = str(raw_summary.get("nearest_bill_name") or "").strip()
            nearest_note = str(raw_summary.get("nearest_bill_note") or "").strip()
            if not nearest_name or nearest_name in ("-", "—"):
                nearest_name, nearest_note = _compute_nearest_bill(
                    [_normalize_bill_item(b, ref) for b in MOCK_BILLS], ref
                )
            self.summary = {
                **raw_summary,
                "total_belanja": _parse_int_safe(raw_summary.get("total_belanja", 0)),
                "belanja_terbesar": _parse_int_safe(
                    raw_summary.get("belanja_terbesar", 0)
                ),
                "belum_dicatat": _parse_int_safe(raw_summary.get("belum_dicatat", 0)),
                "registered_purchases": reg_cnt,
                "total_all_purchases": _parse_int_safe(
                    raw_summary.get("total_all_purchases", len(MOCK_PURCHASES))
                ),
                "nearest_bill_name": nearest_name,
                "nearest_bill_note": nearest_note,
            }
            self._update_tab_counts_from_res(res)
            return

        # Mode live backend: ambil daftar pembelian, normalisasi, lalu filter & paginasi akurat
        res = await api_client.get_purchases(
            {"search": self.search_query.strip()} if self.search_query.strip() else {},
            page=1,
            page_size=200,
        )
        all_norm = [
            _normalize_purchase_item(it, idx)
            for idx, it in enumerate(res.get("items") or [], start=1)
        ]

        min_date: date | None = None
        if self.period_filter == "Bulan ini":
            min_date = ref.replace(day=1)
        elif self.period_filter == "3 bulan terakhir":
            min_date = ref - timedelta(days=90)
        elif self.period_filter == "6 bulan terakhir":
            min_date = ref - timedelta(days=180)
        elif self.period_filter == "Tahun ini":
            min_date = ref.replace(month=1, day=1)

        filtered: list[dict[str, Any]] = []
        for row in all_norm:
            if self.status_filter and self.status_filter != "Semua":
                sf = self.status_filter.lower()
                if sf == "terdaftar" and row["aset_status_variant"] != "success":
                    continue
                if (
                    sf == "belum didaftarkan"
                    and row["aset_status_label"] != "Belum didaftarkan"
                ):
                    continue
                if "habis pakai" in sf and row["aset_status_variant"] != "neutral":
                    continue

            if self.marketplace_filter and self.marketplace_filter != "Semua":
                mp = self.marketplace_filter
                chip = str(row.get("toko_chip") or "Offline")
                if mp == "Lainnya":
                    if chip in ("Shopee", "Tokopedia", "Offline"):
                        continue
                elif chip.lower() != mp.lower():
                    continue

            if min_date is not None:
                try:
                    if date.fromisoformat(str(row["tanggal"])[:10]) < min_date:
                        continue
                except ValueError:
                    pass
            filtered.append(row)

        self.total_items = len(filtered)
        start = max(0, (self.page - 1) * self.page_size)
        paged = filtered[start : start + self.page_size]
        for idx, r in enumerate(paged, start=1):
            r["no"] = start + idx
        self.purchases = paged

        # Ambil tagihan berulang terdekat dari modul Tagihan Berulang backend
        nearest_name, nearest_note = ("Belum ada tagihan", "tidak ada tagihan aktif")
        try:
            bills_res = await api_client.get_bills({}, page=1, page_size=50)
            norm_bills = [
                _normalize_bill_item(b, ref) for b in (bills_res.get("items") or [])
            ]
            nearest_name, nearest_note = _compute_nearest_bill(norm_bills, ref)
        except Exception:
            pass

        belum_cnt = sum(
            1 for x in all_norm if x["aset_status_label"] == "Belum didaftarkan"
        )
        reg_cnt = sum(1 for x in all_norm if x["aset_status_variant"] == "success")
        self.summary = {
            "total_belanja": sum(int(x["total"]) for x in filtered),
            "belanja_terbesar": max((int(x["total"]) for x in filtered), default=0),
            "belum_dicatat": belum_cnt,
            "registered_purchases": reg_cnt,
            "total_all_purchases": len(all_norm),
            "nearest_bill_name": nearest_name,
            "nearest_bill_note": nearest_note,
        }
        self._update_tab_counts_from_res(res)

    @rx.event
    async def fetch_invoices(self) -> None:
        filters: dict[str, Any] = {"search": self.search_query}
        if self.invoice_link_filter and self.invoice_link_filter != "Semua":
            filters["tautan" if USE_MOCK else "link_status"] = self.invoice_link_filter
        res = await api_client.get_invoices(filters, self.page, self.page_size)
        self.invoices = [
            _normalize_invoice_item(it) for it in (res.get("items") or [])
        ]
        self.total_items = _parse_int_safe(res.get("total", len(self.invoices)))
        raw_summary = res.get("summary") or {}
        self.invoices_summary = {
            **{k: _parse_int_safe(v) for k, v in raw_summary.items()},
            "total_invoice": _parse_int_safe(
                raw_summary.get("total_invoice", self.total_items)
            ),
            "sudah_ditautkan": _parse_int_safe(raw_summary.get("sudah_ditautkan", 0)),
            "belum_ditautkan": _parse_int_safe(raw_summary.get("belum_ditautkan", 0)),
            "tanpa_bukti": _parse_int_safe(raw_summary.get("tanpa_bukti", 0)),
        }
        self._update_tab_counts_from_res(res)

    @rx.event
    async def fetch_bills(self) -> None:
        ref = date.today()
        filters: dict[str, Any] = {"search": self.search_query}
        if self.bill_status_filter and self.bill_status_filter != "Semua":
            filters["status"] = self.bill_status_filter
        res = await api_client.get_bills(filters, self.page, self.page_size)
        self.bills = [
            _normalize_bill_item(it, ref) for it in (res.get("items") or [])
        ]
        self.total_items = _parse_int_safe(res.get("total", len(self.bills)))
        raw_summary = res.get("summary") or {}
        self.bills_summary = {
            **{k: _parse_int_safe(v) for k, v in raw_summary.items()},
            "terlambat": _parse_int_safe(raw_summary.get("terlambat", 0)),
            "segera": _parse_int_safe(raw_summary.get("segera", 0)),
            "tagihan_aktif": _parse_int_safe(
                raw_summary.get("tagihan_aktif", self.total_items)
            ),
            "perlu_dibayar_30d": _parse_int_safe(
                raw_summary.get("perlu_dibayar_30d", 0)
            ),
        }
        self._update_tab_counts_from_res(res)

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
        clean = "" if val in ("", "Semua", "Semua status aset") else val
        if self.status_filter == clean:
            return
        self.status_filter = clean
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_marketplace_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Semua marketplace") else val
        if self.marketplace_filter == clean:
            return
        self.marketplace_filter = clean
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_period_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Periode") else val
        if self.period_filter == clean:
            return
        self.period_filter = clean
        self.page = 1
        await self.fetch_purchases()

    @rx.event
    async def set_invoice_link_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Semua status tautan") else val
        if self.invoice_link_filter == clean:
            return
        self.invoice_link_filter = clean
        self.page = 1
        await self.fetch_invoices()

    @rx.event
    async def set_bill_status_filter(self, val: str) -> None:
        clean = "" if val in ("", "Semua", "Semua status") else val
        if self.bill_status_filter == clean:
            return
        self.bill_status_filter = clean
        self.page = 1
        await self.fetch_bills()

    @rx.event
    async def reset_filters(self) -> None:
        self.search_query = ""
        self.status_filter = ""
        self.marketplace_filter = ""
        self.period_filter = ""
        self.invoice_link_filter = ""
        self.bill_status_filter = ""
        self.page = 1
        await self._refetch()

    @rx.event
    async def filter_unregistered_purchases(self) -> None:
        """Klik kartu KPI 'Belum Didaftarkan' untuk langsung memfilter baris tersebut."""
        self.status_filter = (
            "" if self.status_filter == "Belum didaftarkan" else "Belum didaftarkan"
        )
        self.page = 1
        await self.fetch_purchases()

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
                if USE_MOCK:
                    action_jadikan_aset(
                        id_pembelian=pid,
                        kategori=self.asset_form_kategori,
                        kepemilikan="XML",
                        lokasi=self.asset_form_lokasi,
                        garansi_sampai=self.asset_form_garansi.strip() or None,
                    )
                else:
                    await api_client.convert_purchase_to_asset(
                        pid,
                        {
                            "kategori": self.asset_form_kategori,
                            "kepemilikan": "XML",
                            "lokasi": self.asset_form_lokasi,
                            "garansi_sampai": self.asset_form_garansi.strip() or None,
                        },
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
            if USE_MOCK:
                action_jadikan_aset(
                    id_pembelian=self.selected_purchase_id,
                    kategori=self.asset_form_kategori,
                    kepemilikan="XML",
                    lokasi=self.asset_form_lokasi,
                    jumlah_daftar=qty_int,
                    nama_aset=self.asset_form_nama.strip() or None,
                    garansi_sampai=self.asset_form_garansi.strip() or None,
                )
            else:
                await api_client.convert_purchase_to_asset(
                    self.selected_purchase_id,
                    {
                        "kategori": self.asset_form_kategori,
                        "kepemilikan": "XML",
                        "lokasi": self.asset_form_lokasi,
                        "jumlah": qty_int,
                        "garansi_sampai": self.asset_form_garansi.strip() or None,
                    },
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
        link_val = self.new_purchase_link.strip()
        try:
            if link_val:
                parse_marketplace_domain(link_val)
            if USE_MOCK:
                action_create_purchase(
                    {
                        "tanggal": self.new_purchase_tanggal
                        or date.today().isoformat(),
                        "produk": self.new_purchase_produk.strip(),
                        "harga": harga,
                        "pcs": pcs,
                        "nama_toko": self.new_purchase_toko.strip() or "Offline",
                        "link_marketplace": link_val,
                        "dibeli_oleh": self.new_purchase_pembeli.strip() or "Ridho",
                        "aset_status": (
                            "Bukan aset"
                            if self.new_purchase_status
                            == "Habis pakai · tidak perlu aset"
                            else "Belum didaftarkan"
                        ),
                    }
                )
            else:
                await api_client.request(
                    "POST",
                    "/api/v1/purchases",
                    json_data={
                        "nama_item": self.new_purchase_produk.strip(),
                        "kategori": "Hardware",
                        "jenis_transaksi": "Pembelian",
                        "vendor": self.new_purchase_toko.strip() or "Offline",
                        "lokasi": "Head Office (Office Blok 14)",
                        "jumlah": pcs,
                        "satuan": "pcs",
                        "harga_satuan": harga,
                        "total_harga": harga * pcs,
                        "tanggal_beli": self.new_purchase_tanggal
                        or date.today().isoformat(),
                        "status": "Lunas",
                        "is_recurring": False,
                        "id_aset": (
                            "BUKAN-ASET"
                            if self.new_purchase_status
                            == "Habis pakai · tidak perlu aset"
                            else None
                        ),
                        "penanggung_jawab": self.new_purchase_pembeli.strip()
                        or "Ridho",
                        "keterangan": link_val,
                    },
                )
        except Exception as exc:
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
