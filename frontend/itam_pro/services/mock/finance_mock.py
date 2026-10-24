"""
Data Mock Modul Finansial (Pembelian & Invoice) ITAM Pro.
"""
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse

from itam_pro.services.mock.seed import create_mock_assets

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

MOCK_INVOICES: list[dict[str, Any]] = [
    {
        "id_invoice": "INV-2026-001",
        "nomor_invoice": "INV/2026/10/0045",
        "tanggal": "2026-10-16",
        "jatuh_tempo": "2026-10-28",
        "vendor": "Samsung Official Store",
        "total": 2500000,
        "status": "Belum Dibayar",
    },
    {
        "id_invoice": "INV-2026-002",
        "nomor_invoice": "INV/2026/10/0078",
        "tanggal": "2026-10-18",
        "jatuh_tempo": "2026-10-25",
        "vendor": "Microsoft Store Indonesia",
        "total": 2100000,
        "status": "Belum Dibayar",
    },
    {
        "id_invoice": "INV-2026-003",
        "nomor_invoice": "INV/2026/10/0012",
        "tanggal": "2026-10-10",
        "jatuh_tempo": "2026-10-20",
        "vendor": "Dell Authorized Store",
        "total": 7350000,
        "status": "Lunas",
    },
]


def parse_marketplace_domain(url: str) -> str | None:
    """Validasi HTTP/HTTPS dan ekstrak nama chip domain."""
    if not url or str(url).strip() == "":
        return None
    url = str(url).strip()
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


__all__ = [
    "MOCK_INVOICES",
    "MOCK_PURCHASES",
    "action_jadikan_aset",
    "parse_marketplace_domain",
    "query_purchases",
]
