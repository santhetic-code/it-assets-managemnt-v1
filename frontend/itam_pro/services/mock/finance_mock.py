"""
Data Mock Modul Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro.
"""

import csv
import io
import os
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from itam_pro.services.mock.seed import create_mock_assets
from itam_pro.services.recurrence import calculate_bill_status, next_due
from itam_pro.services.validators import (
    format_rupiah as format_rupiah_id,
)
from itam_pro.services.validators import (
    format_tanggal,
)


def format_rupiah(value: Any) -> str:
    """Format angka ke 'Rp1.250.000'."""
    return f"Rp{int(value):,}".replace(",", ".")


_CONSUMABLE_KEYWORDS = (
    "tinta",
    "kabel",
    "baterai",
    "batre",
    "lakban",
    "kertas",
    "pasta",
    "thermal paste",
    "konektor rj45",
    "rj45",
    "ties",
)


def _is_consumable_product(product_name: str) -> bool:
    low = product_name.lower()
    return any(kw in low for kw in _CONSUMABLE_KEYWORDS)


def _status_display_meta(raw_status: str) -> tuple[str, str]:
    """Kembalikan (label_tampilan, badge_variant) untuk 3 status aset pembelian."""
    low = raw_status.strip().lower()
    if low in ("bukan aset", "habis pakai", "habis pakai · tidak perlu aset"):
        return ("Habis pakai · tidak perlu aset", "neutral")
    if low.startswith("terdaftar"):
        # 'Terdaftar (2 aset)' -> 'Terdaftar · 2 aset'
        if "(" in raw_status and ")" in raw_status:
            inner = raw_status.split("(", 1)[1].split(")", 1)[0].strip()
            return (f"Terdaftar · {inner}", "success")
        return ("Terdaftar", "success")
    if low.startswith("sebagian"):
        if "(" in raw_status and ")" in raw_status:
            inner = raw_status.split("(", 1)[1].split(")", 1)[0].strip()
            return (f"Sebagian · {inner}", "warning")
        return (raw_status, "warning")
    return ("Belum didaftarkan", "warning")


MOCK_PURCHASES: list[dict[str, Any]] = []

# Proses parsing CSV
_csv_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "docs", "data", "rekap_pembelian.csv"
)
if not os.path.exists(_csv_path):
    _csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "docs", "data", "rekap_pembelian.csv"
    )
if os.path.exists(_csv_path):
    with open(_csv_path, encoding="utf-8") as f:
        reader = list(csv.reader(f))
        # Header ada di baris ke-3 (index 2)
        if len(reader) > 2:
            for idx, row in enumerate(reader[3:], start=1):
                if len(row) < 7 or not row[1].strip():
                    continue

                # Format Tanggal: DD/MM/YYYY -> YYYY-MM-DD
                raw_date = row[1].strip()
                try:
                    dt = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    dt = raw_date

                # Harga ke integer
                raw_harga = row[3].replace("Rp", "").replace(".", "").strip()
                harga = int(raw_harga) if raw_harga.isdigit() else 0

                pcs = int(row[4]) if row[4].isdigit() else 1

                # Cek baris No 34
                total_hitung = harga * pcs
                raw_total = row[5].replace("Rp", "").replace(".", "").strip()
                total_csv = int(raw_total) if raw_total.isdigit() else 0

                if idx == 34 and total_hitung != total_csv:
                    print(
                        f"Peringatan (Impor CSV): Baris No {idx} memiliki selisih Rp1. "
                        f"Dihitung: Rp{total_hitung}, Di CSV: Rp{total_csv}. "
                        "Aplikasi menggunakan nilai hasil hitung harga x pcs."
                    )

                MOCK_PURCHASES.append(
                    {
                        "id_pembelian": f"PRC-CSV-{idx:03d}",
                        "tanggal": dt,
                        "produk": row[2].strip(),
                        "harga": harga,
                        "pcs": pcs,
                        "nama_toko": row[6].strip(),
                        "link_marketplace": row[7].strip() if len(row) > 7 else "",
                        "dibeli_oleh": "Data CSV",
                        "aset_status": (
                            "Bukan aset"
                            if _is_consumable_product(row[2].strip())
                            else "Belum didaftarkan"
                        ),
                    }
                )

# Invoice = arsip bukti pembayaran, tertaut ke pembelian atau tagihan (opsional).
MOCK_INVOICES: list[dict[str, Any]] = [
    {
        "no_invoice": "NOTA-0187",
        "tanggal": "2026-10-11",
        "vendor": "Vendor Jaringan",
        "total": 1250000,
        "berkas": "JPG · 1,2 MB",
        "terkait_tipe": None,
        "terkait_id": None,
        "terkait_label": "Belum ditautkan",
    },
    {
        "no_invoice": "INV/20260325/MPL/9921",
        "tanggal": "2026-03-25",
        "vendor": "SSG Official Store New",
        "total": 4251700,
        "berkas": "PDF · 214 KB",
        "terkait_tipe": "pembelian",
        "terkait_id": "PRC-2026-001",
        "terkait_label": "Pembelian · SSD Samsung EVO 870 500GB",
    },
    {
        "no_invoice": "INV/20251106/HST/3310",
        "tanggal": "2025-11-06",
        "vendor": "Vendor Hosting",
        "total": 1250000,
        "berkas": "PDF · 96 KB",
        "terkait_tipe": "tagihan",
        "terkait_id": "BILL-004",
        "terkait_label": "Tagihan · Hosting website perusahaan",
    },
]

_BILLS_SEED: list[dict[str, Any]] = [
    {
        "id": "BILL-001",
        "nama": "Domain perusahaan (.com)",
        "vendor": "Registrar",
        "kategori": "Domain",
        "periode": "Tahunan",
        "nominal": 185000,
        "jatuh_tempo": "2026-10-19",
        "pengingat_hari": 14,
        "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-002",
        "nama": "Internet kantor",
        "vendor": "ISP",
        "kategori": "Internet",
        "periode": "Bulanan",
        "nominal": 1450000,
        "jatuh_tempo": "2026-10-28",
        "pengingat_hari": 7,
        "pembayar": "Surya",
        "aktif": True,
    },
    {
        "id": "BILL-003",
        "nama": "Cloud backup",
        "vendor": "Vendor Cloud",
        "kategori": "Hosting",
        "periode": "Bulanan",
        "nominal": 450000,
        "jatuh_tempo": "2026-11-01",
        "pengingat_hari": 7,
        "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-004",
        "nama": "Hosting website perusahaan",
        "vendor": "Vendor Hosting",
        "kategori": "Hosting",
        "periode": "Tahunan",
        "nominal": 1250000,
        "jatuh_tempo": "2026-11-07",
        "pengingat_hari": 7,
        "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-005",
        "nama": "Lisensi antivirus (20 perangkat)",
        "vendor": "Vendor Antivirus",
        "kategori": "Lisensi",
        "periode": "Tahunan",
        "nominal": 3200000,
        "jatuh_tempo": "2026-12-15",
        "pengingat_hari": 14,
        "pembayar": "Surya",
        "aktif": True,
    },
    {
        "id": "BILL-006",
        "nama": "Sertifikat SSL",
        "vendor": "Vendor SSL",
        "kategori": "Lainnya",
        "periode": "Tahunan",
        "nominal": 650000,
        "jatuh_tempo": "2027-01-20",
        "pengingat_hari": 30,
        "pembayar": "Ridho",
        "aktif": True,
    },
]

# anchor_day = tanggal asli siklus agar 31 Jan -> 28 Feb -> 31 Mar (tidak melorot).
MOCK_BILLS: list[dict[str, Any]] = [
    {**b, "anchor_day": int(str(b["jatuh_tempo"])[8:10])} for b in _BILLS_SEED
]

MOCK_BILL_PAYMENTS: list[dict[str, Any]] = []


def _get_nearest_active_bill(today: date | None = None) -> tuple[str, str]:
    """Hitung tagihan berulang terdekat dari MOCK_BILLS untuk kartu KPI ke-4."""
    ref = today or date.today()
    active_bills = [b for b in MOCK_BILLS if b.get("aktif")]
    if not active_bills:
        return ("—", "tidak ada tagihan aktif")

    upcoming = [
        b for b in active_bills if date.fromisoformat(str(b["jatuh_tempo"])) >= ref
    ]
    pool = upcoming if upcoming else active_bills
    pool.sort(key=lambda b: str(b["jatuh_tempo"]))
    nearest = pool[0]
    due = date.fromisoformat(str(nearest["jatuh_tempo"]))
    label_name = str(nearest.get("kategori") or nearest.get("nama") or "Tagihan")
    note = (
        f"jatuh tempo {format_tanggal(due)} · pengingat H-{nearest.get('pengingat_hari', 7)}"
    )
    return (label_name, note)


def parse_marketplace_domain(url: str) -> str | None:
    """Validasi HTTP/HTTPS dan ekstrak nama chip domain."""
    if not url or url.strip() == "":
        return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL wajib diawali dengan http:// atau https://")

    domain = urlparse(url).netloc.lower()
    if "tokopedia.com" in domain:
        return "Tokopedia"
    if "shopee.co.id" in domain:
        return "Shopee"
    return domain


def query_purchases(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
    today: date | None = None,
) -> dict[str, Any]:
    """Filter, paginasi, dan kalkulasi dinamis untuk tabel Rekap Pembelian."""
    ref = today or date.today()
    search = str(filters.get("search", "")).strip().lower()
    status = str(filters.get("aset_status", "")).strip()
    marketplace = str(filters.get("marketplace", "")).strip()
    periode = str(filters.get("periode", "")).strip()

    min_date: date | None = None
    if periode == "Bulan ini":
        min_date = ref.replace(day=1)
    elif periode == "3 bulan terakhir":
        min_date = ref - timedelta(days=90)
    elif periode == "6 bulan terakhir":
        min_date = ref - timedelta(days=180)
    elif periode == "Tahun ini":
        min_date = ref.replace(month=1, day=1)

    filtered = []
    for item in MOCK_PURCHASES:
        raw_status = str(item.get("aset_status", "Belum didaftarkan"))
        if status and status != "Semua":
            st_low = status.lower()
            raw_low = raw_status.lower()
            if st_low in ("habis pakai", "habis pakai · tidak perlu aset", "bukan aset"):
                if raw_low not in ("bukan aset", "habis pakai", "habis pakai · tidak perlu aset"):
                    continue
            elif st_low == "terdaftar":
                if not raw_low.startswith("terdaftar"):
                    continue
            elif st_low == "sebagian":
                if not raw_low.startswith("sebagian"):
                    continue
            elif raw_status != status:
                continue

        if min_date is not None:
            try:
                item_dt = date.fromisoformat(str(item["tanggal"]))
                if item_dt < min_date:
                    continue
            except ValueError:
                pass

        try:
            domain_chip = parse_marketplace_domain(item.get("link_marketplace", ""))
        except ValueError:
            domain_chip = "URL Invalid"

        toko_chip = domain_chip if domain_chip else "Offline"
        if marketplace and marketplace != "Semua":
            if marketplace == "Lainnya":
                if toko_chip in ("Shopee", "Tokopedia", "Offline"):
                    continue
            elif toko_chip.lower() != marketplace.lower():
                continue

        if search:
            haystack = (
                f"{item['produk']} {item['nama_toko']} {toko_chip} {item['dibeli_oleh']}"
            ).lower()
            if search not in haystack:
                continue

        row = deepcopy(item)
        row["id"] = row["id_pembelian"]
        row["total"] = int(row["harga"]) * int(row["pcs"])
        row["domain_chip"] = domain_chip
        row["toko_chip"] = toko_chip
        row["tanggal_display"] = format_tanggal(row["tanggal"])
        row["harga_display"] = format_rupiah_id(row["harga"])
        row["total_display"] = format_rupiah_id(row["total"])
        row["registered_count"] = len(list(row.get("registered_assets") or []))
        label_status, variant_status = _status_display_meta(raw_status)
        row["aset_status_label"] = label_status
        row["aset_status_variant"] = variant_status
        filtered.append(row)

    filtered.sort(key=lambda x: str(x["tanggal"]), reverse=True)

    total_belanja_keseluruhan = sum(x["total"] for x in filtered)
    nearest_bill_name, nearest_bill_note = _get_nearest_active_bill(ref)

    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    for idx, row in enumerate(paginated):
        row["no"] = start + idx + 1

    return {
        "items": paginated,
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "summary": {
            "total_belanja": total_belanja_keseluruhan,
            "belanja_terbesar": max((x["total"] for x in filtered), default=0),
            "belum_dicatat": sum(
                1
                for x in MOCK_PURCHASES
                if x["aset_status"] in ("Belum didaftarkan", "Belum dicatat")
            ),
            "total_all_purchases": len(MOCK_PURCHASES),
            "nearest_bill_name": nearest_bill_name,
            "nearest_bill_note": nearest_bill_note,
        },
    }


def action_jadikan_aset(
    id_pembelian: str,
    kategori: str,
    kepemilikan: str,
    lokasi: str,
    jumlah_daftar: int | None = None,
    bukan_aset: bool = False,
    nama_aset: str | None = None,
    garansi_sampai: str | None = None,
) -> list[str]:
    """Otomatisasi pendaftaran item pembelian menjadi N aset (atau Habis pakai/Bukan aset)."""
    for p in MOCK_PURCHASES:
        if p["id_pembelian"] == id_pembelian or (
            id_pembelian == "PRC-2026-001" and p["id_pembelian"] == "PRC-CSV-001"
        ):
            if bukan_aset or kategori.lower() in (
                "bukan aset",
                "habis pakai",
                "habis pakai · tidak perlu aset",
            ):
                p["aset_status"] = "Bukan aset"
                p["registered_assets"] = []
                return []

            existing_list: list[str] = list(p.get("registered_assets") or [])
            total_pcs = int(p.get("pcs", 1))
            sisa = max(0, total_pcs - len(existing_list))
            if sisa <= 0:
                return existing_list

            qty_make = min(sisa, jumlah_daftar or sisa)
            is_comp = kategori.upper() in ("RAM", "SSD", "HDD", "VGA", "PSU")
            payload = {
                "nama_aset": (nama_aset or "").strip() or p["produk"],
                "kategori": kategori,
                "tanggal_masuk_gudang": p["tanggal"],
                "kepemilikan": kepemilikan,
                "lokasi": "Gudang" if is_comp else lokasi,
                "kondisi": "Baru",
                "status": "Cadangan" if is_comp else "Digunakan",
                "digunakan_oleh": "Cadangan - Gudang" if is_comp else "Operasional",
                "purchase_id": p["id_pembelian"],
                "harga_beli": int(p.get("harga", 0)),
                "tanggal_beli": str(p.get("tanggal", "")),
                "garansi_sampai": garansi_sampai or "",
                "attributes": (
                    {
                        "tipe": "DDR4" if kategori.upper() == "RAM" else "SATA",
                        "kapasitas_gb": 8 if kategori.upper() == "RAM" else 512,
                        "data_status": "Kosong",
                    }
                    if is_comp
                    else {}
                ),
            }
            created_rows = create_mock_assets(payload, count=qty_make)
            for created in created_rows:
                created["purchase_id"] = p["id_pembelian"]
                created["harga_beli"] = int(p.get("harga", 0))
                created["tanggal_beli"] = str(p.get("tanggal", ""))
                if garansi_sampai:
                    created["garansi_sampai"] = garansi_sampai

            new_ids = [str(r["id_aset"]) for r in created_rows]
            all_ids = [*existing_list, *new_ids]
            p["registered_assets"] = all_ids
            if len(all_ids) >= total_pcs:
                p["aset_status"] = f"Terdaftar ({len(all_ids)} aset)"
            else:
                p["aset_status"] = f"Sebagian ({len(all_ids)}/{total_pcs})"
            return all_ids
    return []


def action_create_purchase(payload: dict[str, Any]) -> dict[str, Any]:
    """Tambah catatan pembelian baru ke data mock.
    TODO(backend): sambungkan ke endpoint POST /api/v1/finance/purchases.
    """
    link = str(payload.get("link_marketplace", "")).strip()
    if link:
        parse_marketplace_domain(link)
    next_num = len(MOCK_PURCHASES) + 1
    produk = str(payload.get("produk", "")).strip()
    raw_status = str(payload.get("aset_status", "")).strip()
    if not raw_status:
        raw_status = "Bukan aset" if _is_consumable_product(produk) else "Belum didaftarkan"
    entry = {
        "id_pembelian": f"PRC-MAN-{next_num:03d}",
        "tanggal": str(payload.get("tanggal") or date.today().isoformat()),
        "produk": produk,
        "harga": max(0, int(payload.get("harga", 0))),
        "pcs": max(1, int(payload.get("pcs", 1))),
        "nama_toko": str(payload.get("nama_toko", "")).strip() or "Offline",
        "link_marketplace": link,
        "dibeli_oleh": str(payload.get("dibeli_oleh", "")).strip() or "Ridho",
        "aset_status": raw_status,
    }
    MOCK_PURCHASES.insert(0, entry)
    return deepcopy(entry)


def action_import_purchases(csv_text: str) -> tuple[int, list[str]]:
    """Impor baris pembelian dari teks CSV (Tanggal,Produk,Harga,Pcs,Toko,Link,Dibeli Oleh).
    TODO(backend): sambungkan ke endpoint POST /api/v1/finance/purchases/import.
    """
    errors: list[str] = []
    imported = 0
    reader = csv.reader(io.StringIO(csv_text.strip()))
    for row_idx, row in enumerate(reader, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        if row_idx == 1 and "produk" in ",".join(row).lower():
            continue
        if len(row) < 4:
            errors.append(
                f"Baris {row_idx}: minimal 4 kolom (Tanggal, Produk, Harga, Pcs)."
            )
            continue
        raw_tgl = row[0].strip()
        try:
            if "/" in raw_tgl:
                tgl_iso = datetime.strptime(raw_tgl, "%d/%m/%Y").strftime("%Y-%m-%d")
            else:
                tgl_iso = date.fromisoformat(raw_tgl).isoformat()
        except ValueError:
            errors.append(f"Baris {row_idx}: format tanggal tidak valid ({raw_tgl}).")
            continue
        produk = row[1].strip()
        raw_harga = row[2].replace("Rp", "").replace(".", "").replace(",", "").strip()
        if not produk or not raw_harga.isdigit():
            errors.append(f"Baris {row_idx}: produk atau harga tidak valid.")
            continue
        pcs = int(row[3].strip()) if row[3].strip().isdigit() else 1
        toko = row[4].strip() if len(row) > 4 and row[4].strip() else "Offline"
        link = row[5].strip() if len(row) > 5 else ""
        pembeli = row[6].strip() if len(row) > 6 and row[6].strip() else "Ridho"
        try:
            action_create_purchase(
                {
                    "tanggal": tgl_iso,
                    "produk": produk,
                    "harga": int(raw_harga),
                    "pcs": max(1, pcs),
                    "nama_toko": toko,
                    "link_marketplace": link,
                    "dibeli_oleh": pembeli,
                }
            )
            imported += 1
        except ValueError as exc:
            errors.append(f"Baris {row_idx}: {exc}")
    return imported, errors


def _paginate(rows: list[dict[str, Any]], page: int, page_size: int) -> list[dict[str, Any]]:
    start = max(0, (page - 1) * page_size)
    return rows[start : start + page_size]


def query_invoices(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query tab Invoice (arsip bukti pembayaran)."""
    search = str(filters.get("search", "")).strip().lower()
    link_filter = str(filters.get("tautan", "")).strip()

    rows: list[dict[str, Any]] = []
    for inv in MOCK_INVOICES:
        is_linked = bool(inv["terkait_tipe"])
        if link_filter == "Sudah ditautkan" and not is_linked:
            continue
        if link_filter == "Belum ditautkan" and is_linked:
            continue
        if search:
            haystack = f"{inv['no_invoice']} {inv['vendor']} {inv['terkait_label']}".lower()
            if search not in haystack:
                continue
        row = deepcopy(inv)
        row["total_display"] = format_rupiah(row["total"])
        row["total_rp_display"] = format_rupiah_id(row["total"])
        row["tanggal_display"] = format_tanggal(row["tanggal"])
        row["tautan_variant"] = "success" if is_linked else "warning"
        rows.append(row)

    rows.sort(key=lambda x: str(x["tanggal"]), reverse=True)

    sudah = sum(1 for i in MOCK_INVOICES if i["terkait_tipe"])
    # Pembelian tanpa bukti: pembelian yang belum punya invoice tertaut.
    linked_purchase_ids = {
        i["terkait_id"] for i in MOCK_INVOICES if i["terkait_tipe"] == "pembelian"
    }
    tanpa_bukti = sum(1 for p in MOCK_PURCHASES if p["id_pembelian"] not in linked_purchase_ids)

    return {
        "items": _paginate(rows, page, page_size),
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "summary": {
            "total_invoice": len(MOCK_INVOICES),
            "sudah_ditautkan": sudah,
            "belum_ditautkan": len(MOCK_INVOICES) - sudah,
            "tanpa_bukti": tanpa_bukti,
        },
    }


_STATUS_VARIANT = {"Terlambat": "danger", "Segera": "warning", "Terjadwal": "info"}


def query_bills(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
    today: date | None = None,
) -> dict[str, Any]:
    """Query tab Tagihan Berulang dengan status & KPI dinamis."""
    ref = today or date.today()
    search = str(filters.get("search", "")).strip().lower()
    status_filter = str(filters.get("status", "")).strip()

    rows: list[dict[str, Any]] = []
    terlambat = segera = aktif_count = perlu_dibayar_30 = 0

    for bill in MOCK_BILLS:
        if not bill["aktif"]:
            continue
        info = calculate_bill_status(bill["jatuh_tempo"], bill["pengingat_hari"], ref)
        aktif_count += 1
        if info["status"] == "Terlambat":
            terlambat += 1
        elif info["status"] == "Segera":
            segera += 1
        due = date.fromisoformat(str(bill["jatuh_tempo"]))
        if (due - ref).days <= 30:
            perlu_dibayar_30 += int(bill["nominal"])

        if status_filter and status_filter != "Semua" and info["status"] != status_filter:
            continue
        if search:
            haystack = f"{bill['nama']} {bill['vendor']} {bill['kategori']}".lower()
            if search not in haystack:
                continue

        row = deepcopy(bill)
        row["status"] = info["status"]
        row["status_label"] = info["label"]
        row["status_variant"] = _STATUS_VARIANT[info["status"]]
        row["nominal_display"] = format_rupiah(row["nominal"])
        row["nominal_rp_display"] = format_rupiah_id(row["nominal"])
        row["jatuh_tempo_display"] = format_tanggal(row["jatuh_tempo"])
        row["pengingat_display"] = f"{row['pengingat_hari']} hari sebelumnya"
        rows.append(row)

    rows.sort(key=lambda x: str(x["jatuh_tempo"]))

    return {
        "items": _paginate(rows, page, page_size),
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "summary": {
            "terlambat": terlambat,
            "segera": segera,
            "tagihan_aktif": aktif_count,
            "perlu_dibayar_30d": perlu_dibayar_30,
        },
    }


def action_pay_bill(bill_id: str, tgl_bayar: str, nominal: int) -> None:
    """Tandai dibayar: simpan riwayat & geser jatuh tempo dari jatuh tempo LAMA."""
    for bill in MOCK_BILLS:
        if bill["id"] != bill_id:
            continue
        MOCK_BILL_PAYMENTS.append(
            {
                "id": f"PAY-{len(MOCK_BILL_PAYMENTS) + 1:04d}",
                "bill_id": bill_id,
                "tanggal_bayar": tgl_bayar,
                "nominal": nominal,
            }
        )
        baru = next_due(bill["jatuh_tempo"], bill["periode"], bill.get("anchor_day"))
        if baru is None:
            bill["aktif"] = False
        else:
            bill["jatuh_tempo"] = baru.strftime("%Y-%m-%d")
        break


__all__ = [
    "MOCK_BILLS",
    "MOCK_BILL_PAYMENTS",
    "MOCK_INVOICES",
    "MOCK_PURCHASES",
    "action_create_purchase",
    "action_import_purchases",
    "action_jadikan_aset",
    "action_pay_bill",
    "format_rupiah",
    "parse_marketplace_domain",
    "query_bills",
    "query_invoices",
    "query_purchases",
]
