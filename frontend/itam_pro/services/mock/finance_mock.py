"""
Data Mock Modul Finansial (Pembelian, Invoice, Tagihan Berulang) ITAM Pro.
"""
from copy import deepcopy
from datetime import date
from typing import Any
from urllib.parse import urlparse

from itam_pro.services.mock.seed import create_mock_assets
from itam_pro.services.recurrence import calculate_bill_status, next_due


def format_rupiah(value: Any) -> str:
    """Format angka ke 'Rp1.250.000'."""
    return f"Rp{int(value):,}".replace(",", ".")

# Mock Data Awal Rekap Pembelian ITAM Pro
MOCK_PURCHASES: list[dict[str, Any]] = [
    {
        "id_pembelian": "PRC-2026-001",
        "tanggal": "2026-10-15",
        "produk": "SSD NVMe Samsung 980 1TB",
        "harga": 1250000,
        "pcs": 2,
        "nama_toko": "Samsung Official",
        "link_marketplace": "https://tokopedia.com/samsung/ssd",
        "dibeli_oleh": "Ridho",
        "aset_status": "Belum dicatat",
    },
    {
        "id_pembelian": "PRC-2026-002",
        "tanggal": "2026-10-18",
        "produk": "Lisensi Windows 11 Pro",
        "harga": 2100000,
        "pcs": 1,
        "nama_toko": "Microsoft Store",
        "link_marketplace": "https://microsoft.com",
        "dibeli_oleh": "Surya",
        "aset_status": "Bukan aset",
    },
    {
        "id_pembelian": "PRC-2026-003",
        "tanggal": "2026-10-19",
        "produk": "Monitor Dell 24 Inch P2422H",
        "harga": 2450000,
        "pcs": 3,
        "nama_toko": "Dell Authorized Store",
        "link_marketplace": "https://tokopedia.com/dell/p2422h",
        "dibeli_oleh": "Dimas",
        "aset_status": "Belum dicatat",
    },
    {
        "id_pembelian": "PRC-2026-004",
        "tanggal": "2026-10-20",
        "produk": "UPS APC BVX1200LI 1200VA",
        "harga": 1850000,
        "pcs": 2,
        "nama_toko": "Schneider Electric Store",
        "link_marketplace": "https://shopee.co.id/schneider/apc-1200va",
        "dibeli_oleh": "Ridho",
        "aset_status": "Belum dicatat",
    },
    {
        "id_pembelian": "PRC-2026-005",
        "tanggal": "2026-10-21",
        "produk": "RAM Corsair Vengeance 32GB DDR5",
        "harga": 1750000,
        "pcs": 4,
        "nama_toko": "Corsair Official Store",
        "link_marketplace": "https://tokopedia.com/corsair/ddr5-32gb",
        "dibeli_oleh": "Andi",
        "aset_status": "Belum dicatat",
    },
    {
        "id_pembelian": "PRC-2026-006",
        "tanggal": "2026-10-22",
        "produk": "Server Rackmount Dell PowerEdge R450",
        "harga": 38500000,
        "pcs": 1,
        "nama_toko": "Mitra Solusi Komputindo",
        "link_marketplace": "https://mitrasolusi.co.id/dell-r450",
        "dibeli_oleh": "Surya",
        "aset_status": "Belum dicatat",
    },
    {
        "id_pembelian": "PRC-2026-007",
        "tanggal": "2026-10-23",
        "produk": "Kabel Patchcord Cat6 3m UTP (Pack 10 pcs)",
        "harga": 250000,
        "pcs": 5,
        "nama_toko": "Belden Networking Center",
        "link_marketplace": "https://shopee.co.id/belden/cat6-3m",
        "dibeli_oleh": "Budi",
        "aset_status": "Bukan aset",
    },
]

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
        "id": "BILL-001", "nama": "Domain perusahaan (.com)", "vendor": "Registrar",
        "kategori": "Domain", "periode": "Tahunan", "nominal": 185000,
        "jatuh_tempo": "2026-10-19", "pengingat_hari": 14, "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-002", "nama": "Internet kantor", "vendor": "ISP",
        "kategori": "Internet", "periode": "Bulanan", "nominal": 1450000,
        "jatuh_tempo": "2026-10-28", "pengingat_hari": 7, "pembayar": "Surya",
        "aktif": True,
    },
    {
        "id": "BILL-003", "nama": "Cloud backup", "vendor": "Vendor Cloud",
        "kategori": "Hosting", "periode": "Bulanan", "nominal": 450000,
        "jatuh_tempo": "2026-11-01", "pengingat_hari": 7, "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-004", "nama": "Hosting website perusahaan", "vendor": "Vendor Hosting",
        "kategori": "Hosting", "periode": "Tahunan", "nominal": 1250000,
        "jatuh_tempo": "2026-11-07", "pengingat_hari": 7, "pembayar": "Ridho",
        "aktif": True,
    },
    {
        "id": "BILL-005", "nama": "Lisensi antivirus (20 perangkat)",
        "vendor": "Vendor Antivirus", "kategori": "Lisensi", "periode": "Tahunan",
        "nominal": 3200000, "jatuh_tempo": "2026-12-15", "pengingat_hari": 14,
        "pembayar": "Surya", "aktif": True,
    },
    {
        "id": "BILL-006", "nama": "Sertifikat SSL", "vendor": "Vendor SSL",
        "kategori": "Lainnya", "periode": "Tahunan", "nominal": 650000,
        "jatuh_tempo": "2027-01-20", "pengingat_hari": 30, "pembayar": "Ridho",
        "aktif": True,
    },
]

# anchor_day = tanggal asli siklus agar 31 Jan -> 28 Feb -> 31 Mar (tidak melorot).
MOCK_BILLS: list[dict[str, Any]] = [
    {**b, "anchor_day": int(str(b["jatuh_tempo"])[8:10])} for b in _BILLS_SEED
]

MOCK_BILL_PAYMENTS: list[dict[str, Any]] = []


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
) -> dict[str, Any]:
    """Filter, paginasi, dan kalkulasi dinamis untuk tabel Rekap Pembelian."""
    search = str(filters.get("search", "")).strip().lower()
    status = str(filters.get("aset_status", "")).strip()

    filtered = []
    for item in MOCK_PURCHASES:
        # Match filters
        if status and status != "Semua" and item["aset_status"] != status:
            continue
        if search:
            haystack = f"{item['produk']} {item['nama_toko']} {item['dibeli_oleh']}".lower()
            if search not in haystack:
                continue

        row = deepcopy(item)
        row["id"] = row["id_pembelian"]
        row["total"] = row["harga"] * row["pcs"]
        try:
            row["domain_chip"] = parse_marketplace_domain(row.get("link_marketplace", ""))
        except ValueError:
            row["domain_chip"] = "URL Invalid"

        filtered.append(row)

    # Sort default: Tanggal terbaru
    filtered.sort(key=lambda x: str(x["tanggal"]), reverse=True)

    # Kalkulasi KPI & Baris Total
    total_belanja_keseluruhan = sum(x["total"] for x in filtered)

    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    # Inject nomor urut tampilan
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
                1 for x in MOCK_PURCHASES if x["aset_status"] == "Belum dicatat"
            ),
        },
    }


def action_jadikan_aset(
    id_pembelian: str,
    kategori: str,
    kepemilikan: str,
    lokasi: str,
) -> None:
    """Otomatisasi pembuatan aset di MOCK_ASSETS berdasarkan data pembelian."""
    for p in MOCK_PURCHASES:
        if p["id_pembelian"] == id_pembelian:
            payload = {
                "nama_aset": p["produk"],
                "kategori": kategori,
                "tanggal_masuk_gudang": p["tanggal"],
                "kepemilikan": kepemilikan,
                "lokasi": lokasi,
                "kondisi": "Baru",
                "status": "Tidak Digunakan",
            }
            # Buat N unit ke seed.py
            create_mock_assets(payload, count=int(p["pcs"]))
            p["aset_status"] = f"{p['pcs']} aset dibuat"
            break


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
        rows.append(row)

    rows.sort(key=lambda x: str(x["tanggal"]), reverse=True)

    sudah = sum(1 for i in MOCK_INVOICES if i["terkait_tipe"])
    # Pembelian tanpa bukti: pembelian yang belum punya invoice tertaut.
    linked_purchase_ids = {
        i["terkait_id"] for i in MOCK_INVOICES if i["terkait_tipe"] == "pembelian"
    }
    tanpa_bukti = sum(
        1 for p in MOCK_PURCHASES if p["id_pembelian"] not in linked_purchase_ids
    )

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
    "action_jadikan_aset",
    "action_pay_bill",
    "format_rupiah",
    "parse_marketplace_domain",
    "query_bills",
    "query_invoices",
    "query_purchases",
]
