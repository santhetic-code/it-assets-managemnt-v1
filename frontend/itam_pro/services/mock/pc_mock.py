"""
Data Mock Daftar PC ITAM Pro (~8 PC per tab: Operasional, Server, Backup).
Satu baris = satu PC dengan ID internal otomatis PC-0001.
"""
from typing import Any


def _disp(val: str | None) -> str:
    """Tampilkan '—' bila nilai kosong."""
    if not val or not str(val).strip() or str(val).strip() == "—":
        return "—"
    return str(val).strip()


def _format_pc_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Lengkapi field tampilan tabel ('—') dan 3 grup drawer (Identitas, Perangkat keras, Periferal)."""
    jenis = raw["jenis"]
    nama_pc = raw["nama_pc"].strip()
    user_raw = raw.get("user", "").strip()
    os_raw = raw.get("operasi_system", "").strip()
    ram_raw = raw.get("ram", "").strip()
    vga_raw = raw.get("vga", "").strip()
    cpu_raw = raw.get("cpu", "").strip()
    mb_raw = raw.get("mainboard", "").strip()
    storage_raw = raw.get("hdd_ssd", "").strip()
    mon_raw = raw.get("monitor", "").strip()
    kb_raw = raw.get("keyboard", "").strip()
    mouse_raw = raw.get("mouse", "").strip()
    catatan_raw = raw.get("catatan", "").strip()
    asset_id = raw.get("asset_id")

    user_label = "User / Fungsi" if jenis in ("Server", "Backup") else "User"

    return {
        "id": raw["id"],
        "jenis": jenis,
        "nama_pc": nama_pc,
        "user": _disp(user_raw),
        "user_raw": user_raw,
        "operasi_system": _disp(os_raw),
        "operasi_system_raw": os_raw,
        "ram": _disp(ram_raw),
        "ram_raw": ram_raw,
        "vga": _disp(vga_raw),
        "vga_raw": vga_raw,
        "cpu": _disp(cpu_raw),
        "cpu_raw": cpu_raw,
        "mainboard": _disp(mb_raw),
        "mainboard_raw": mb_raw,
        "hdd_ssd": _disp(storage_raw),
        "hdd_ssd_raw": storage_raw,
        "monitor": _disp(mon_raw),
        "monitor_raw": mon_raw,
        "keyboard": _disp(kb_raw),
        "keyboard_raw": kb_raw,
        "mouse": _disp(mouse_raw),
        "mouse_raw": mouse_raw,
        "catatan": _disp(catatan_raw),
        "catatan_raw": catatan_raw,
        "asset_id": asset_id,
        "identity_info": [
            {"label": "ID Internal", "value": raw["id"]},
            {"label": "Nama PC / Hostname", "value": nama_pc},
            {"label": "Jenis PC", "value": jenis},
            {"label": user_label, "value": _disp(user_raw)},
            {"label": "Catatan", "value": _disp(catatan_raw)},
        ],
        "hardware_info": [
            {"label": "Operasi System", "value": _disp(os_raw)},
            {"label": "CPU / Prosesor", "value": _disp(cpu_raw)},
            {"label": "Mainboard", "value": _disp(mb_raw)},
            {"label": "RAM", "value": _disp(ram_raw)},
            {"label": "VGA / Grafis", "value": _disp(vga_raw)},
            {"label": "HDD / SSD", "value": _disp(storage_raw)},
        ],
        "peripheral_info": [
            {"label": "Monitor", "value": _disp(mon_raw)},
            {"label": "Keyboard", "value": _disp(kb_raw)},
            {"label": "Mouse", "value": _disp(mouse_raw)},
        ],
        "history_info": raw.get(
            "history_info",
            [
                {
                    "event": "Pencatatan Spesifikasi PC",
                    "date": "12 Okt 2026",
                    "note": f"Spesifikasi unit {nama_pc} ({jenis}) telah diverifikasi.",
                }
            ],
        ),
    }


def _seed_initial_pcs() -> list[dict[str, Any]]:
    """Bangun 24 baris PC (8 Operasional, 8 Server, 8 Backup)."""
    rows: list[dict[str, Any]] = [
        # --- 8 PC OPERASIONAL ---
        {
            "jenis": "Operasional",
            "nama_pc": "PC-OPS-B14-01",
            "user": "Raka Pratama",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 3200MHz (2x8GB)",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400 (6C/12T)",
            "mainboard": "ASRock B660M Pro RS",
            "hdd_ssd": "SSD NVMe Samsung 980 500GB",
            "monitor": "LG 24MK600M 24\"",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "PC utama tim operasional Blok 14.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-OPS-B14-02",
            "user": "Fajar Nugraha",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "MSI PRO H610M-E DDR4",
            "hdd_ssd": "SSD Kingston NV2 500GB + HDD 1TB",
            "monitor": "Dual LG 24MK600M 24\"",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech M170 Wireless",
            "catatan": "Setup dual monitor untuk monitoring transaksi.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-FIN-B13-01",
            "user": "Nadia Kusuma",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i5-10400",
            "mainboard": "ASUS Prime H510M-E",
            "hdd_ssd": "SSD Samsung 870 EVO 500GB",
            "monitor": "Samsung 24\" S24R350",
            "keyboard": "Logitech MK270 Combo",
            "mouse": "Logitech MK270 Wireless",
            "catatan": "PC rekap pembelian & akuntansi Blok 13.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-CS-B14-01",
            "user": "Sinta Dewi",
            "operasi_system": "Windows 10 Pro 22H2",
            "ram": "8GB DDR4 2666MHz",
            "vga": "NVIDIA GT 1030 2GB",
            "cpu": "Intel Core i3-10105F",
            "mainboard": "ASRock H510M-HDV/M.2",
            "hdd_ssd": "SSD Crucial BX500 240GB",
            "monitor": "LG 22MK400H 22\"",
            "keyboard": "VortexSeries VX7 Mechanical",
            "mouse": "Logitech B100 Optical",
            "catatan": "Shift pagi & sore Customer Service.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-CS-B14-02",
            "user": "Ayu Lestari",
            "operasi_system": "Windows 10 Pro 22H2",
            "ram": "8GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i3-10100",
            "mainboard": "Gigabyte H410M H V3",
            "hdd_ssd": "SSD WD Green 240GB",
            "monitor": "Samsung 22\" S22F350",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-IT-B12-01",
            "user": "Bayu Setiawan",
            "operasi_system": "Windows 11 Pro + WSL2 Ubuntu",
            "ram": "32GB DDR4 3200MHz (2x16GB)",
            "vga": "NVIDIA GeForce GTX 1650 4GB",
            "cpu": "Intel Core i7-12700",
            "mainboard": "MSI MAG B660M Mortar DDR4",
            "hdd_ssd": "SSD Samsung 980 Pro 1TB NVMe",
            "monitor": "Dell UltraSharp U2422H 24\"",
            "keyboard": "Keychron K2 Wireless",
            "mouse": "Logitech G304 Lightspeed",
            "catatan": "Workstation tim IT Support & QA.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-RUKO-01",
            "user": "Hendra Wijaya",
            "operasi_system": "Windows 10 Pro 64-bit",
            "ram": "8GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 610",
            "cpu": "Intel Pentium Gold G6400",
            "mainboard": "ASRock H410M-HVS",
            "hdd_ssd": "SSD Kingston A400 240GB",
            "monitor": "AOC 22B2HM 21.5\"",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "Meja admin lantai bawah Ruko.",
        },
        {
            "jenis": "Operasional",
            "nama_pc": "PC-MESS-OFF-01",
            "user": "Galih Permana",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 3200MHz",
            "vga": "AMD Radeon Vega 7 Integrated",
            "cpu": "AMD Ryzen 5 5600G",
            "mainboard": "ASRock B550M Pro4",
            "hdd_ssd": "SSD Team MP33 512GB NVMe",
            "monitor": "LG 24MP400 24\" IPS",
            "keyboard": "Logitech MK220 Wireless",
            "mouse": "Logitech MK220 Wireless",
            "catatan": "Operasional Mess Blok 12 Office.",
        },
        # --- 8 PC SERVER ---
        {
            "jenis": "Server",
            "nama_pc": "SRV-DB-MAIN-01",
            "user": "Server Database Utama",
            "operasi_system": "Ubuntu Server 24.04 LTS",
            "ram": "64GB DDR4 ECC 3200MHz",
            "vga": "Onboard Matrox G200eW3",
            "cpu": "Intel Xeon E-2336 (6C/12T)",
            "mainboard": "Supermicro X12STL-F",
            "hdd_ssd": "2x 1TB NVMe Enterprise RAID-1",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Diakses via SSH & IPMI (Kantor Blok 14).",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-TRX-XML-01",
            "user": "Server Engine Transaksi XML",
            "operasi_system": "Windows Server 2022 Standard",
            "ram": "32GB DDR4 3200MHz (2x16GB)",
            "vga": "Intel UHD Graphics 770",
            "cpu": "Intel Core i7-13700",
            "mainboard": "ASUS Prime B760M-A D4",
            "hdd_ssd": "2x SSD Samsung 980 Pro 1TB",
            "monitor": "LG 19M38A 18.5\" (KVM Switch)",
            "keyboard": "Logitech K120 (KVM Switch)",
            "mouse": "Logitech B100 (KVM Switch)",
            "catatan": "Node utama engine pulsa & PPOB.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-TRX-XML-02",
            "user": "Server Addon & Center",
            "operasi_system": "Windows 10 Pro LTSC",
            "ram": "32GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "ASRock B660M Pro RS",
            "hdd_ssd": "SSD Samsung 870 EVO 1TB",
            "monitor": "LG 19M38A 18.5\" (KVM Switch)",
            "keyboard": "Logitech K120 (KVM Switch)",
            "mouse": "Logitech B100 (KVM Switch)",
            "catatan": "Menangani koneksi modul supplier & webhook.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-TRX-MBL-01",
            "user": "Server Transaksi MBL",
            "operasi_system": "Windows Server 2019 Standard",
            "ram": "32GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i7-10700",
            "mainboard": "Gigabyte B460M DS3H",
            "hdd_ssd": "SSD Samsung 870 EVO 500GB + HDD 2TB",
            "monitor": "AOC 19\" E970SWNL",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "Server produksi khusus entitas MBL.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-MON-ZABBIX",
            "user": "Server Monitoring Zabbix & Grafana",
            "operasi_system": "Ubuntu Server 24.04 LTS",
            "ram": "16GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "MSI PRO B660M-A DDR4",
            "hdd_ssd": "SSD WD Black SN770 500GB",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Menjalankan Docker Zabbix, Grafana, dan ITAM Pro.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-PROXMOX-01",
            "user": "Host Virtualisasi VM Internal",
            "operasi_system": "Proxmox VE 8.2",
            "ram": "64GB DDR4 3200MHz (4x16GB)",
            "vga": "NVIDIA GT 710 1GB",
            "cpu": "AMD Ryzen 9 5900X (12C/24T)",
            "mainboard": "ASUS TUF Gaming B550M-Plus",
            "hdd_ssd": "2x 1TB NVMe + 2x 4TB HDD IronWolf",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Host untuk 6 VM layanan internal.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-CCTV-NVR-B14",
            "user": "Server Rekaman CCTV Multi-Site",
            "operasi_system": "Windows 10 Pro 64-bit",
            "ram": "16GB DDR4 2666MHz",
            "vga": "NVIDIA GTX 1050 Ti 4GB",
            "cpu": "Intel Core i5-10400F",
            "mainboard": "ASRock B460M Steel Legend",
            "hdd_ssd": "SSD 256GB OS + 2x 6TB WD Purple",
            "monitor": "Samsung 32\" Smart TV Monitor",
            "keyboard": "Logitech K400 Plus Wireless",
            "mouse": "Touchpad Terintegrasi",
            "catatan": "Streaming Hikvision, Dahua, dan Ezviz.",
        },
        {
            "jenis": "Server",
            "nama_pc": "SRV-FILE-NAS-01",
            "user": "Server File Sharing & Dokumen",
            "operasi_system": "TrueNAS SCALE 24.04",
            "ram": "32GB DDR4 ECC",
            "vga": "Integrated Graphics",
            "cpu": "Intel Core i3-12100",
            "mainboard": "ASRock H670M-ITX/ax",
            "hdd_ssd": "4x 4TB Seagate IronWolf RAID-Z1",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Penyimpanan invoice, SOP, dan arsip gudang.",
        },
        # --- 8 PC BACKUP ---
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-DB-01",
            "user": "Replica Database Standby",
            "operasi_system": "Ubuntu Server 24.04 LTS",
            "ram": "32GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "ASRock B660M Pro RS",
            "hdd_ssd": "2x SSD Samsung 870 EVO 1TB",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Auto-sync harian pukul 02:00 WIB dari SRV-DB-MAIN-01.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-TRX-01",
            "user": "Failover Engine Transaksi XML",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "32GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "MSI PRO B660M-A DDR4",
            "hdd_ssd": "SSD Samsung 980 1TB NVMe",
            "monitor": "LG 19M38A 18.5\"",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "Siap switch-over kurang dari 5 menit bila server utama gangguan.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-MBL-01",
            "user": "Backup Server MBL",
            "operasi_system": "Windows 10 Pro 64-bit",
            "ram": "16GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i5-10400",
            "mainboard": "ASUS Prime H510M-E",
            "hdd_ssd": "SSD 500GB + HDD WD Blue 2TB",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Cold-standby di Kantor Blok 13.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-OPS-01",
            "user": "Cadangan PC Operasional #1",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 3200MHz",
            "vga": "Intel UHD Graphics 730",
            "cpu": "Intel Core i5-12400",
            "mainboard": "ASRock H610M-HDV/M.2",
            "hdd_ssd": "SSD Kingston NV2 500GB",
            "monitor": "LG 24MK600M 24\"",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "Unit siap pakai di Kantor Blok 12 untuk pengganti darurat.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-OPS-02",
            "user": "Cadangan PC Operasional #2",
            "operasi_system": "Windows 10 Pro 64-bit",
            "ram": "8GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i3-10100",
            "mainboard": "ASRock H410M-HDV",
            "hdd_ssd": "SSD Crucial BX500 240GB",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Unit CPU saja di ruang IT Blok 12.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-FIN-01",
            "user": "Cadangan PC Finance & Kasir",
            "operasi_system": "Windows 11 Pro 64-bit",
            "ram": "16GB DDR4 2666MHz",
            "vga": "Intel UHD Graphics 630",
            "cpu": "Intel Core i5-10400",
            "mainboard": "Gigabyte H410M S2 V3",
            "hdd_ssd": "SSD Samsung 870 EVO 500GB",
            "monitor": "Samsung 22\" S22F350",
            "keyboard": "Logitech K120 USB",
            "mouse": "Logitech B100 Optical",
            "catatan": "Sudah terinstal aplikasi pajak & e-Faktur backup.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-RUKO-01",
            "user": "Cadangan Operasional Ruko",
            "operasi_system": "Windows 10 Pro 64-bit",
            "ram": "8GB DDR4 2666MHz",
            "vga": "Intel HD Graphics 630",
            "cpu": "Intel Core i3-9100",
            "mainboard": "ASUS Prime H310M-D",
            "hdd_ssd": "SSD WD Green 240GB",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Disimpan di lemari perangkat Ruko.",
        },
        {
            "jenis": "Backup",
            "nama_pc": "PC-BKP-ARCHIVE-01",
            "user": "Cold Backup Snapshot Tahunan",
            "operasi_system": "Ubuntu Server 22.04 LTS",
            "ram": "16GB DDR4 2666MHz",
            "vga": "Integrated Graphics",
            "cpu": "Intel Core i3-10100",
            "mainboard": "ASRock H510M-HVS",
            "hdd_ssd": "2x 4TB Seagate Barracuda Mirror",
            "monitor": "—",
            "keyboard": "—",
            "mouse": "—",
            "catatan": "Dinyalakan setiap akhir pekan untuk sinkronisasi arsip.",
        },
    ]

    records: list[dict[str, Any]] = []
    for idx, r in enumerate(rows, start=1):
        r["id"] = f"PC-{idx:04d}"
        r["asset_id"] = None
        records.append(_format_pc_record(r))
    return records


MOCK_PCS_DB: list[dict[str, Any]] = _seed_initial_pcs()
_NEXT_PC_SEQ: int = len(MOCK_PCS_DB) + 1


def _count_by_jenis() -> dict[str, int]:
    counts: dict[str, int] = {"Operasional": 0, "Server": 0, "Backup": 0}
    for item in MOCK_PCS_DB:
        j = str(item.get("jenis", "Operasional"))
        counts[j] = counts.get(j, 0) + 1
    return counts


def query_mock_pcs(
    jenis: str,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Filter data PC berdasarkan tab jenis dan pencarian (hostname, user, CPU, mainboard)."""
    search = str(filters.get("search", "")).strip().lower()

    filtered: list[dict[str, Any]] = []
    for item in MOCK_PCS_DB:
        if item["jenis"] != jenis:
            continue
        if search:
            haystack = (
                f"{item['nama_pc']} {item['user_raw']} "
                f"{item['cpu_raw']} {item['mainboard_raw']} {item['id']}"
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
        "counts_by_jenis": _count_by_jenis(),
    }


def create_mock_pc(payload: dict[str, Any]) -> dict[str, Any]:
    """Tambah satu baris PC baru dengan ID otomatis PC-XXXX."""
    global _NEXT_PC_SEQ
    new_id = f"PC-{_NEXT_PC_SEQ:04d}"
    _NEXT_PC_SEQ += 1
    raw = {
        "id": new_id,
        "jenis": str(payload.get("jenis", "Operasional")),
        "nama_pc": str(payload.get("nama_pc", "")).strip(),
        "user": str(payload.get("user", "")).strip(),
        "operasi_system": str(payload.get("operasi_system", "")).strip(),
        "ram": str(payload.get("ram", "")).strip(),
        "vga": str(payload.get("vga", "")).strip(),
        "cpu": str(payload.get("cpu", "")).strip(),
        "mainboard": str(payload.get("mainboard", "")).strip(),
        "hdd_ssd": str(payload.get("hdd_ssd", "")).strip(),
        "monitor": str(payload.get("monitor", "")).strip(),
        "keyboard": str(payload.get("keyboard", "")).strip(),
        "mouse": str(payload.get("mouse", "")).strip(),
        "catatan": str(payload.get("catatan", "")).strip(),
        "asset_id": payload.get("asset_id"),
    }
    record = _format_pc_record(raw)
    MOCK_PCS_DB.insert(0, record)
    return record


def update_mock_pc(pc_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Perbarui spesifikasi satu PC berdasarkan ID internal."""
    for idx, existing in enumerate(MOCK_PCS_DB):
        if existing["id"] == pc_id:
            raw = {
                "id": pc_id,
                "jenis": str(payload.get("jenis", existing["jenis"])),
                "nama_pc": str(payload.get("nama_pc", existing["nama_pc"])).strip(),
                "user": str(payload.get("user", existing["user_raw"])).strip(),
                "operasi_system": str(
                    payload.get("operasi_system", existing["operasi_system_raw"])
                ).strip(),
                "ram": str(payload.get("ram", existing["ram_raw"])).strip(),
                "vga": str(payload.get("vga", existing["vga_raw"])).strip(),
                "cpu": str(payload.get("cpu", existing["cpu_raw"])).strip(),
                "mainboard": str(payload.get("mainboard", existing["mainboard_raw"])).strip(),
                "hdd_ssd": str(payload.get("hdd_ssd", existing["hdd_ssd_raw"])).strip(),
                "monitor": str(payload.get("monitor", existing["monitor_raw"])).strip(),
                "keyboard": str(payload.get("keyboard", existing["keyboard_raw"])).strip(),
                "mouse": str(payload.get("mouse", existing["mouse_raw"])).strip(),
                "catatan": str(payload.get("catatan", existing["catatan_raw"])).strip(),
                "asset_id": existing.get("asset_id"),
                "history_info": [
                    {
                        "event": "Pembaruan Spesifikasi PC",
                        "date": "19 Okt 2026",
                        "note": f"Spesifikasi {pc_id} diperbarui oleh Admin IT.",
                    },
                    *existing.get("history_info", []),
                ],
            }
            updated = _format_pc_record(raw)
            MOCK_PCS_DB[idx] = updated
            return updated
    return None


def delete_mock_pc(pc_id: str) -> bool:
    """Hapus satu PC dari daftar mock."""
    global MOCK_PCS_DB
    before = len(MOCK_PCS_DB)
    MOCK_PCS_DB = [item for item in MOCK_PCS_DB if item["id"] != pc_id]
    return len(MOCK_PCS_DB) < before


__all__ = [
    "MOCK_PCS_DB",
    "create_mock_pc",
    "delete_mock_pc",
    "query_mock_pcs",
    "update_mock_pc",
]
