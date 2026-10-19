"""
Data Mock Assets Inventory (~42 baris realistis sesuai kolom spreadsheet asli).
Satu baris = satu unit fisik dengan ID otomatis AST-0001.
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


def format_date_id(iso_date: str | None) -> str:
    """Ubah YYYY-MM-DD menjadi format Indonesia '12 Mar 2027' atau '—' jika kosong."""
    if not iso_date or not str(iso_date).strip() or str(iso_date).strip() == "—":
        return "—"
    parts = str(iso_date).strip().split("-")
    if len(parts) != 3:
        return str(iso_date)
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{day:02d} {BULAN_ID[month]} {year}"
    except (ValueError, IndexError):
        return str(iso_date)


def _format_asset_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Lengkapi tampilan tabel ('—' bila kosong) dan 2 grup informasi drawer."""
    sn_display = raw.get("sn_pid", "").strip() or "—"
    masuk_iso = raw.get("tanggal_masuk_gudang", "").strip()
    keluar_iso = raw.get("tanggal_keluar_gudang", "").strip()
    masuk_display = format_date_id(masuk_iso)
    keluar_display = format_date_id(keluar_iso)
    digunakan_display = (
        raw.get("digunakan_oleh", "").strip() or "—"
        if raw.get("status") == "Digunakan"
        else "—"
    )
    catatan_display = raw.get("catatan", "").strip() or "—"
    note_text = (
        f"Unit {raw['nama_aset']} ({raw['kepemilikan']}) "
        f"tercatat di {raw['lokasi']}."
    )

    return {
        "id": raw["id"],
        "nama_aset": raw["nama_aset"],
        "kategori": raw["kategori"],
        "sn_pid": sn_display,
        "sn_pid_raw": raw.get("sn_pid", "").strip(),
        "tanggal_masuk_gudang": masuk_display,
        "tanggal_masuk_iso": masuk_iso,
        "tanggal_keluar_gudang": keluar_display,
        "tanggal_keluar_iso": keluar_iso,
        "kepemilikan": raw["kepemilikan"],
        "lokasi": raw["lokasi"],
        "kondisi": raw["kondisi"],
        "status": raw["status"],
        "digunakan_oleh": digunakan_display,
        "digunakan_oleh_raw": raw.get("digunakan_oleh", "").strip(),
        "catatan": catatan_display,
        "catatan_raw": raw.get("catatan", "").strip(),
        "general_info": [
            {"label": "ID Internal", "value": raw["id"]},
            {"label": "Nama Aset", "value": raw["nama_aset"]},
            {"label": "Kategori", "value": raw["kategori"]},
            {"label": "SN / PID", "value": sn_display},
            {"label": "Kepemilikan", "value": raw["kepemilikan"]},
            {"label": "Kondisi", "value": raw["kondisi"]},
            {"label": "Catatan", "value": catatan_display},
        ],
        "usage_info": [
            {"label": "Status", "value": raw["status"]},
            {"label": "Digunakan Oleh", "value": digunakan_display},
            {"label": "Lokasi", "value": raw["lokasi"]},
            {"label": "Tgl Masuk Gudang", "value": masuk_display},
            {"label": "Tgl Keluar Gudang", "value": keluar_display},
        ],
        "history_info": raw.get(
            "history_info",
            [
                {
                    "event": "Pencatatan Inventaris",
                    "date": masuk_display if masuk_display != "—" else "10 Jan 2026",
                    "note": note_text,
                }
            ],
        ),
    }


def _seed_initial_assets() -> list[dict[str, Any]]:
    """Bangun 42 baris data aset realistis sesuai kategori & lokasi spreadsheet asli."""
    seed_rows: list[dict[str, Any]] = [
        {
            "nama_aset": "Monitor LG 24MK600M 24\"",
            "kategori": "Monitor",
            "sn_pid": "402NTGY8A912",
            "tanggal_masuk_gudang": "2025-11-10",
            "tanggal_keluar_gudang": "2025-11-12",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 14",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Raka Pratama",
            "catatan": "Monitor utama meja kerja operasional.",
        },
        {
            "nama_aset": "PC Rakitan Core i5-12400 H610",
            "kategori": "PC",
            "sn_pid": "PC-XML-B14-01",
            "tanggal_masuk_gudang": "2025-10-04",
            "tanggal_keluar_gudang": "2025-10-06",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 14",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Raka Pratama",
            "catatan": "RAM 16GB, SSD NVMe 512GB.",
        },
        {
            "nama_aset": "Keyboard Logitech K120 USB",
            "kategori": "Keyboard",
            "sn_pid": "2348MR01928",
            "tanggal_masuk_gudang": "2025-11-10",
            "tanggal_keluar_gudang": "2025-11-12",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 14",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Raka Pratama",
            "catatan": "",
        },
        {
            "nama_aset": "Mouse Logitech B100 Optical",
            "kategori": "Mouse",
            "sn_pid": "",
            "tanggal_masuk_gudang": "2025-11-10",
            "tanggal_keluar_gudang": "2025-11-12",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 14",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Raka Pratama",
            "catatan": "Tanpa nomor seri pada bodi.",
        },
        {
            "nama_aset": "Router MikroTik RB450Gx4",
            "kategori": "Router",
            "sn_pid": "HE8092C1145",
            "tanggal_masuk_gudang": "2025-08-15",
            "tanggal_keluar_gudang": "2025-08-16",
            "kepemilikan": "XML",
            "lokasi": "Ruko",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Tim Jaringan Ruko",
            "catatan": "Gateway utama lantai bawah Ruko.",
        },
        {
            "nama_aset": "SSD Samsung 870 EVO 500GB SATA",
            "kategori": "SSD",
            "sn_pid": "S62ANJ0R811204",
            "tanggal_masuk_gudang": "2026-01-18",
            "tanggal_keluar_gudang": "",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 12",
            "kondisi": "Baru",
            "status": "Tidak Digunakan",
            "digunakan_oleh": "",
            "catatan": "Stok cadangan upgrade PC admin.",
        },
        {
            "nama_aset": "RAM Kingston Fury Beast DDR4 8GB 3200MHz",
            "kategori": "RAM",
            "sn_pid": "KF432C16BB-8",
            "tanggal_masuk_gudang": "2026-01-18",
            "tanggal_keluar_gudang": "2026-02-02",
            "kepemilikan": "MBL",
            "lokasi": "Kantor Blok 13",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Nadia Kusuma",
            "catatan": "Dipasang di PC Finance Blok 13.",
        },
        {
            "nama_aset": "Laptop Lenovo ThinkPad L14 Gen 3",
            "kategori": "Laptop",
            "sn_pid": "PF3X991L",
            "tanggal_masuk_gudang": "2025-09-20",
            "tanggal_keluar_gudang": "2025-09-22",
            "kepemilikan": "MBL",
            "lokasi": "Kantor Blok 13",
            "kondisi": "Bekas",
            "status": "Digunakan",
            "digunakan_oleh": "Dimas Saputra",
            "catatan": "Kondisi mulus, baterai sehat 88%.",
        },
        {
            "nama_aset": "HDD Seagate Barracuda 1TB 3.5\"",
            "kategori": "HDD",
            "sn_pid": "Z9A4412P",
            "tanggal_masuk_gudang": "2024-05-12",
            "tanggal_keluar_gudang": "",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 12",
            "kondisi": "Tidak Terpakai / Rusak",
            "status": "Tidak Digunakan",
            "digunakan_oleh": "",
            "catatan": "Health Sentinel 18%, bad sector.",
        },
        {
            "nama_aset": "Server Dell PowerEdge T150 Tower",
            "kategori": "Server",
            "sn_pid": "SVT150-992A",
            "tanggal_masuk_gudang": "2025-06-01",
            "tanggal_keluar_gudang": "2025-06-03",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 14",
            "kondisi": "Baru",
            "status": "Digunakan",
            "digunakan_oleh": "Server Transaksi XML",
            "catatan": "Server database internal.",
        },
        {
            "nama_aset": "PSU Corsair CV550 550W 80+ Bronze",
            "kategori": "Komponen PC",
            "sn_pid": "CP-9020210",
            "tanggal_masuk_gudang": "2026-02-14",
            "tanggal_keluar_gudang": "",
            "kepemilikan": "XML",
            "lokasi": "Kantor Blok 12",
            "kondisi": "Baru",
            "status": "Tidak Digunakan",
            "digunakan_oleh": "",
            "catatan": "Cadangan pengganti PSU PC CS.",
        },
        {
            "nama_aset": "Switch TP-Link TL-SG1016D 16-Port Gigabit",
            "kategori": "Lainnya",
            "sn_pid": "22294810023",
            "tanggal_masuk_gudang": "2025-07-19",
            "tanggal_keluar_gudang": "2025-07-20",
            "kepemilikan": "MBL",
            "lokasi": "Mess Blok 12 Office",
            "kondisi": "Bekas",
            "status": "Digunakan",
            "digunakan_oleh": "Jaringan Mess Office",
            "catatan": "Distribusi LAN ruang kerja mess.",
        },
    ]

    extra_templates = [
        ("Monitor Samsung 22\" S22F350", "Monitor", "SN-SM22-0", "Bekas"),
        ("Keyboard Mechanical VortexSeries", "Keyboard", "VX-KB-0", "Baru"),
        ("Mouse Wireless Logitech M170", "Mouse", "LG-M170-0", "Baru"),
        ("SSD Kingston NV2 500GB PCIe 4.0", "SSD", "KSNV2-500-", "Baru"),
        ("RAM Team Elite Plus DDR4 8GB", "RAM", "TM8G-2666-", "Bekas"),
        ("Laptop ASUS ExpertBook B1400", "Laptop", "ASB14-88", "Bekas"),
        ("Router TP-Link Archer C6 AC1200", "Router", "TPLC6-71", "Bekas"),
        ("HDD WD Blue 1TB SATA", "HDD", "WDB1T-44", "Tidak Terpakai / Rusak"),
        ("PC Rakitan Core i3-10105F Office", "PC", "PC-OFF-0", "Bekas"),
        ("Motherboard ASRock H510M-HDV", "Komponen PC", "ASR-H510-", "Tidak Terpakai / Rusak"),
    ]
    lokasi_cycle = [
        "Kantor Blok 14",
        "Kantor Blok 13",
        "Kantor Blok 12",
        "Ruko",
        "Mess Blok 12 Office",
        "Mess Blok 12",
    ]
    user_samaran = [
        "Fajar Nugraha",
        "Sinta Dewi",
        "Bayu Setiawan",
        "Ayu Lestari",
        "Hendra Wijaya",
        "Putri Maharani",
        "Galih Permana",
        "Rina Oktaviani",
    ]

    for i in range(30):
        tpl = extra_templates[i % len(extra_templates)]
        tpl_name, tpl_kat, tpl_sn_prefix, tpl_kondisi = tpl
        lok = lokasi_cycle[i % len(lokasi_cycle)]
        kep = "XML" if i % 3 != 0 else "MBL"
        if tpl_kondisi == "Tidak Terpakai / Rusak" or i % 4 == 0:
            st = "Tidak Digunakan"
            oleh = ""
            tgl_keluar = ""
        else:
            st = "Digunakan"
            oleh = user_samaran[i % len(user_samaran)]
            tgl_keluar = f"2026-0{(i % 6) + 1}-{(i % 20) + 5:02d}"

        tgl_masuk = f"2026-0{(i % 6) + 1}-{(i % 20) + 1:02d}"
        sn_val = "" if i % 7 == 0 else f"{tpl_sn_prefix}{100 + i}"

        seed_rows.append(
            {
                "nama_aset": f"{tpl_name} #{(i // 10) + 1}",
                "kategori": tpl_kat,
                "sn_pid": sn_val,
                "tanggal_masuk_gudang": tgl_masuk,
                "tanggal_keluar_gudang": tgl_keluar,
                "kepemilikan": kep,
                "lokasi": lok,
                "kondisi": tpl_kondisi,
                "status": st,
                "digunakan_oleh": oleh,
                "catatan": (
                    "Unit teregistrasi dari impor spreadsheet inventaris."
                    if i % 2 == 0
                    else ""
                ),
            }
        )

    records: list[dict[str, Any]] = []
    for idx, row in enumerate(seed_rows, start=1):
        row["id"] = f"AST-{idx:04d}"
        records.append(_format_asset_record(row))
    return records


MOCK_ASSETS_DB: list[dict[str, Any]] = _seed_initial_assets()
_NEXT_SEQ: int = len(MOCK_ASSETS_DB) + 1


def query_mock_assets(
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Filter dan paginasi data aset mock ({items, total, page, page_size})."""
    search = str(filters.get("search", "")).strip().lower()
    kategori = str(filters.get("kategori", "Semua"))
    kepemilikan = str(filters.get("kepemilikan", "Semua"))
    lokasi = str(filters.get("lokasi", "Semua"))
    kondisi = str(filters.get("kondisi", "Semua"))
    status = str(filters.get("status", "Semua"))

    filtered: list[dict[str, Any]] = []
    for item in MOCK_ASSETS_DB:
        if kategori != "Semua" and item["kategori"] != kategori:
            continue
        if kepemilikan != "Semua" and item["kepemilikan"] != kepemilikan:
            continue
        if lokasi != "Semua" and item["lokasi"] != lokasi:
            continue
        if kondisi != "Semua" and item["kondisi"] != kondisi:
            continue
        if status != "Semua" and item["status"] != status:
            continue
        if search:
            haystack = (
                f"{item['nama_aset']} {item['sn_pid_raw']} "
                f"{item['digunakan_oleh_raw']} {item['id']}"
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


def create_mock_assets(payload: dict[str, Any], count: int = 1) -> list[dict[str, Any]]:
    """Buat 1 atau N unit aset fisik baru dengan ID otomatis AST-XXXX."""
    global _NEXT_SEQ
    created: list[dict[str, Any]] = []
    qty = max(1, min(50, int(count)))
    for _ in range(qty):
        new_id = f"AST-{_NEXT_SEQ:04d}"
        _NEXT_SEQ += 1
        raw = {
            "id": new_id,
            "nama_aset": str(payload.get("nama_aset", "")).strip(),
            "kategori": str(payload.get("kategori", "Monitor")),
            "sn_pid": str(payload.get("sn_pid", "")).strip(),
            "tanggal_masuk_gudang": str(payload.get("tanggal_masuk_gudang", "")).strip(),
            "tanggal_keluar_gudang": str(payload.get("tanggal_keluar_gudang", "")).strip(),
            "kepemilikan": str(payload.get("kepemilikan", "XML")),
            "lokasi": str(payload.get("lokasi", "Kantor Blok 14")),
            "kondisi": str(payload.get("kondisi", "Baru")),
            "status": str(payload.get("status", "Digunakan")),
            "digunakan_oleh": str(payload.get("digunakan_oleh", "")).strip(),
            "catatan": str(payload.get("catatan", "")).strip(),
        }
        record = _format_asset_record(raw)
        MOCK_ASSETS_DB.insert(0, record)
        created.append(record)
    return created


def update_mock_asset(asset_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Perbarui data satu aset berdasarkan ID internal."""
    for idx, existing in enumerate(MOCK_ASSETS_DB):
        if existing["id"] == asset_id:
            raw = {
                "id": asset_id,
                "nama_aset": str(payload.get("nama_aset", existing["nama_aset"])).strip(),
                "kategori": str(payload.get("kategori", existing["kategori"])),
                "sn_pid": str(payload.get("sn_pid", existing["sn_pid_raw"])).strip(),
                "tanggal_masuk_gudang": str(
                    payload.get("tanggal_masuk_gudang", existing["tanggal_masuk_iso"])
                ).strip(),
                "tanggal_keluar_gudang": str(
                    payload.get("tanggal_keluar_gudang", existing["tanggal_keluar_iso"])
                ).strip(),
                "kepemilikan": str(payload.get("kepemilikan", existing["kepemilikan"])),
                "lokasi": str(payload.get("lokasi", existing["lokasi"])),
                "kondisi": str(payload.get("kondisi", existing["kondisi"])),
                "status": str(payload.get("status", existing["status"])),
                "digunakan_oleh": str(
                    payload.get("digunakan_oleh", existing["digunakan_oleh_raw"])
                ).strip(),
                "catatan": str(payload.get("catatan", existing["catatan_raw"])).strip(),
                "history_info": [
                    {
                        "event": "Pembaruan Data Aset",
                        "date": "19 Okt 2026",
                        "note": f"Data unit {asset_id} diperbarui oleh Admin IT.",
                    },
                    *existing.get("history_info", []),
                ],
            }
            updated = _format_asset_record(raw)
            MOCK_ASSETS_DB[idx] = updated
            return updated
    return None


def delete_mock_asset(asset_id: str) -> bool:
    """Hapus satu aset dari daftar mock."""
    global MOCK_ASSETS_DB
    before = len(MOCK_ASSETS_DB)
    MOCK_ASSETS_DB = [item for item in MOCK_ASSETS_DB if item["id"] != asset_id]
    return len(MOCK_ASSETS_DB) < before


__all__ = [
    "BULAN_ID",
    "MOCK_ASSETS_DB",
    "create_mock_assets",
    "delete_mock_asset",
    "format_date_id",
    "query_mock_assets",
    "update_mock_asset",
]
