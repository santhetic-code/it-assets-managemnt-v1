"""
Data Mock Assets Inventory (~42 aset campuran PC, Monitor, Server, UPS).
Mendukung pencarian, filter kategori/status/lokasi, dan paginasi.
"""
from typing import Any

BULAN_ID = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
]


def format_date_id(iso_date: str) -> str:
    """Ubah YYYY-MM-DD menjadi format Indonesia '12 Mar 2027'."""
    parts = iso_date.split("-")
    if len(parts) != 3:
        return iso_date
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    return f"{day:02d} {BULAN_ID[month]} {year}"


def _build_mock_assets() -> list[dict[str, Any]]:
    """Bangun 42 data aset realistis (PC, Monitor, Server, UPS)."""
    raw_templates: list[dict[str, Any]] = [
        {
            "id": "PC-0214",
            "name": "Dell OptiPlex 7010 SFF",
            "category": "PC",
            "serial": "DL7010-9921A",
            "location": "HQ Lt. 2 · Operasional",
            "pic": "Budi Santoso",
            "status": "In Use",
            "warranty_iso": "2027-03-12",
            "warranty_tone": "normal",
            "vendor": "PT Mitra Komputindo",
            "purchase_date": "12 Mar 2024",
            "price": "Rp 12.500.000",
            "specs": [
                {"label": "Prosesor", "value": "Intel Core i7-13700"},
                {"label": "RAM", "value": "16 GB DDR5"},
                {"label": "Penyimpanan", "value": "512 GB NVMe SSD"},
                {"label": "OS", "value": "Windows 11 Pro 64-bit"},
            ],
            "related": [
                {"label": "Monitor Terhubung", "value": "MON-0104 (Dell 24\")"},
                {"label": "Alamat IP", "value": "10.10.2.14"},
                {"label": "Invoice", "value": "INV-2024-0312"},
            ],
        },
        {
            "id": "SRV-0002",
            "name": "Server Rack-02 Dell PowerEdge R750",
            "category": "Server",
            "serial": "PE750-DC02X",
            "location": "Data Center Lt. 4",
            "pic": "Admin IT",
            "status": "In Use",
            "warranty_iso": "2026-10-31",
            "warranty_tone": "warning",
            "vendor": "PT Nusantara Serverindo",
            "purchase_date": "31 Okt 2023",
            "price": "Rp 84.000.000",
            "specs": [
                {"label": "Prosesor", "value": "2x Intel Xeon Silver 4314"},
                {"label": "RAM", "value": "128 GB ECC DDR4"},
                {"label": "RAID Storage", "value": "4x 1.92 TB Enterprise SSD"},
                {"label": "Konsumsi Daya", "value": "680 Watt"},
            ],
            "related": [
                {"label": "UPS Terhubung", "value": "UPS-0001 (UPS Server 1)"},
                {"label": "IP Management", "value": "10.10.1.12"},
                {"label": "Rack Unit", "value": "Rack A · U14-U15"},
            ],
        },
        {
            "id": "UPS-0003",
            "name": "APC Smart-UPS 2000VA Jaringan",
            "category": "UPS",
            "serial": "APC2K-8831J",
            "location": "Data Center Lt. 4",
            "pic": "Teknisi 1",
            "status": "Maintenance",
            "warranty_iso": "2026-11-05",
            "warranty_tone": "warning",
            "vendor": "PT Daya Mandiri",
            "purchase_date": "05 Nov 2023",
            "price": "Rp 14.800.000",
            "specs": [
                {"label": "Kapasitas", "value": "2,0 kVA / 1.400 W"},
                {"label": "Beban Saat Ini", "value": "91% (1.274 W)"},
                {"label": "Umur Baterai", "value": "2 tahun 11 bulan"},
                {"label": "Tipe Output", "value": "Pure Sine Wave"},
            ],
            "related": [
                {"label": "Perangkat Terproteksi", "value": "Core Switch & Firewall"},
                {"label": "Tiket Maintenance", "value": "MNT-2026-089 (Terlambat)"},
                {"label": "Invoice", "value": "INV-2023-1105"},
            ],
        },
        {
            "id": "MON-0104",
            "name": "Dell UltraSharp 24\" U2422H",
            "category": "Monitor",
            "serial": "DLU24-5512M",
            "location": "HQ Lt. 2 · Operasional",
            "pic": "Budi Santoso",
            "status": "In Use",
            "warranty_iso": "2027-03-12",
            "warranty_tone": "normal",
            "vendor": "PT Mitra Komputindo",
            "purchase_date": "12 Mar 2024",
            "price": "Rp 4.200.000",
            "specs": [
                {"label": "Ukuran Panel", "value": "24 Inci IPS"},
                {"label": "Resolusi", "value": "1920 x 1080 @ 60Hz"},
                {"label": "Port", "value": "HDMI, DisplayPort, USB-C"},
            ],
            "related": [
                {"label": "PC Terhubung", "value": "PC-0214 (Dell OptiPlex)"},
                {"label": "Pengguna", "value": "Budi Santoso"},
            ],
        },
        {
            "id": "PC-0198",
            "name": "Lenovo ThinkCentre M70s Gen 3",
            "category": "PC",
            "serial": "LN70S-4410P",
            "location": "HQ Lt. 3 · Finance",
            "pic": "Siti Rahmawati",
            "status": "In Use",
            "warranty_iso": "2026-10-28",
            "warranty_tone": "warning",
            "vendor": "PT Surya Digital",
            "purchase_date": "28 Okt 2023",
            "price": "Rp 11.200.000",
            "specs": [
                {"label": "Prosesor", "value": "Intel Core i5-12500"},
                {"label": "RAM", "value": "16 GB DDR4"},
                {"label": "Penyimpanan", "value": "512 GB NVMe SSD"},
                {"label": "OS", "value": "Windows 11 Pro"},
            ],
            "related": [
                {"label": "Monitor Terhubung", "value": "MON-0092 (Lenovo 24\")"},
                {"label": "Alamat IP", "value": "10.10.3.21"},
            ],
        },
        {
            "id": "UPS-0001",
            "name": "Eaton 9PX 6000i RT3U (UPS Server 1)",
            "category": "UPS",
            "serial": "ET6K-1102S",
            "location": "Data Center Lt. 4",
            "pic": "Admin IT",
            "status": "In Use",
            "warranty_iso": "2025-08-18",
            "warranty_tone": "danger",
            "vendor": "PT Daya Mandiri",
            "purchase_date": "18 Agu 2022",
            "price": "Rp 42.000.000",
            "specs": [
                {"label": "Kapasitas", "value": "6,0 kVA / 5.400 W"},
                {"label": "Beban Saat Ini", "value": "78% (4.212 W)"},
                {"label": "Umur Baterai", "value": "3 tahun 2 bulan (Perlu Ganti)"},
            ],
            "related": [
                {"label": "Server Terhubung", "value": "SRV-0001, SRV-0002"},
                {"label": "Rack Unit", "value": "Rack A · U01-U03"},
            ],
        },
    ]

    categories = ["PC", "Monitor", "Server", "UPS"]
    locations = [
        "HQ Lt. 2 · Operasional",
        "HQ Lt. 3 · Finance",
        "Data Center Lt. 4",
        "Cabang Bandung",
        "Gudang IT",
    ]
    statuses = ["In Use", "In Use", "In Use", "In Storage", "Maintenance", "Disposed"]
    pics = [
        "Andi Pratama",
        "Dewi Lestari",
        "Rizky Fauzan",
        "Teknisi 1",
        "Teknisi 2",
        "Admin IT",
        "Gudang Aset",
    ]
    warranties = [
        ("2027-06-15", "normal"),
        ("2027-09-20", "normal"),
        ("2026-11-02", "warning"),
        ("2026-04-10", "danger"),
        ("2028-01-14", "normal"),
    ]

    for idx in range(7, 43):
        cat = categories[idx % len(categories)]
        loc = locations[idx % len(locations)]
        st = "In Storage" if loc == "Gudang IT" else statuses[idx % len(statuses)]
        pic = pics[idx % len(pics)]
        w_iso, w_tone = warranties[idx % len(warranties)]

        if cat == "PC":
            code = f"PC-{200 + idx:04d}"
            name = f"HP ProDesk 400 G9 #{idx}"
            serial = f"HP400-88{idx:02d}K"
            specs = [
                {"label": "Prosesor", "value": "Intel Core i5-13500"},
                {"label": "RAM", "value": "16 GB DDR4"},
                {"label": "Penyimpanan", "value": "512 GB SSD"},
            ]
        elif cat == "Monitor":
            code = f"MON-{100 + idx:04d}"
            name = f"LG 24MP400 IPS 24\" #{idx}"
            serial = f"LG24M-77{idx:02d}L"
            specs = [
                {"label": "Ukuran Panel", "value": "23,8 Inci IPS"},
                {"label": "Resolusi", "value": "1920 x 1080 @ 75Hz"},
            ]
        elif cat == "Server":
            code = f"SRV-{idx:04d}"
            name = f"HPE ProLiant DL380 Gen10 #{idx}"
            serial = f"HPE380-33{idx:02d}S"
            specs = [
                {"label": "Prosesor", "value": "Intel Xeon Gold 5218"},
                {"label": "RAM", "value": "64 GB ECC"},
                {"label": "Konsumsi Daya", "value": "520 Watt"},
            ]
        else:
            code = f"UPS-{idx:04d}"
            name = f"APC Smart-UPS 1500VA #{idx}"
            serial = f"APC15-66{idx:02d}U"
            specs = [
                {"label": "Kapasitas", "value": "1,5 kVA / 1.000 W"},
                {"label": "Beban Saat Ini", "value": "48%"},
            ]

        raw_templates.append(
            {
                "id": code,
                "name": name,
                "category": cat,
                "serial": serial,
                "location": loc,
                "pic": pic,
                "status": st,
                "warranty_iso": w_iso,
                "warranty_tone": w_tone,
                "vendor": "PT Mitra Komputindo",
                "purchase_date": "15 Jan 2024",
                "price": "Rp 9.850.000",
                "specs": specs,
                "related": [
                    {"label": "Lokasi Fisik", "value": loc},
                    {"label": "Penanggung Jawab", "value": pic},
                ],
            }
        )

    formatted_list: list[dict[str, Any]] = []
    for item in raw_templates:
        warranty_str = format_date_id(item["warranty_iso"])
        if item["warranty_tone"] == "warning":
            warranty_display = f"{warranty_str} (≤30 hr)"
        elif item["warranty_tone"] == "danger":
            warranty_display = f"{warranty_str} (Habis)"
        else:
            warranty_display = warranty_str

        formatted_list.append(
            {
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "serial": item["serial"],
                "location": item["location"],
                "pic": item["pic"],
                "status": item["status"],
                "warranty": warranty_display,
                "warranty_tone": item["warranty_tone"],
                "general_info": [
                    {"label": "Kode Aset", "value": item["id"]},
                    {"label": "Nama Perangkat", "value": item["name"]},
                    {"label": "Kategori", "value": item["category"]},
                    {"label": "Serial Number", "value": item["serial"]},
                    {"label": "Lokasi", "value": item["location"]},
                    {"label": "Penanggung Jawab", "value": item["pic"]},
                    {"label": "Vendor", "value": item["vendor"]},
                    {"label": "Tgl Pembelian", "value": item["purchase_date"]},
                    {"label": "Nilai Perolehan", "value": item["price"]},
                    {"label": "Batas Garansi", "value": warranty_display},
                ],
                "specs_info": item["specs"],
                "related_info": item["related"],
                "history_info": [
                    {
                        "event": "Pemeriksaan berkala",
                        "date": "10 Okt 2026",
                        "note": f"Kondisi fisik dan fungsi {item['id']} terverifikasi normal.",
                    },
                    {
                        "event": "Serah terima PIC",
                        "date": item["purchase_date"],
                        "note": f"Aset dialokasikan kepada {item['pic']} di {item['location']}.",
                    },
                ],
            }
        )
    return formatted_list


MOCK_ASSETS_DB: list[dict[str, Any]] = _build_mock_assets()


def query_mock_assets(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Filter dan paginasi data aset mock seperti kontrak REST API Backend."""
    search = str(filters.get("search", "")).strip().lower()
    category = str(filters.get("category", "Semua"))
    status = str(filters.get("status", "Semua"))
    location = str(filters.get("location", "Semua"))
    excluded_ids = set(filters.get("excluded_ids", []))

    filtered: list[dict[str, Any]] = []
    for item in MOCK_ASSETS_DB:
        if item["id"] in excluded_ids:
            continue
        if category != "Semua" and item["category"] != category:
            continue
        if status != "Semua" and item["status"] != status:
            continue
        if location != "Semua" and item["location"] != location:
            continue
        if search:
            haystack = (
                f"{item['id']} {item['name']} {item['serial']} {item['pic']} {item['location']}"
            ).lower()
            if search not in haystack:
                continue
        filtered.append(item)

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    return {
        "items": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
