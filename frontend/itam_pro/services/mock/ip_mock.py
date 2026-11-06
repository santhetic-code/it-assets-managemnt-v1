"""
Mock Data & Logika Bisnis untuk Modul IP & Server (VM).
Mendukung klasifikasi berbasis Jenis (Fisik vs VM), deteksi IP bentrok,
VM tanpa host, dan penanda 'Ada kendala' jika field keterangan terisi.
"""

from copy import deepcopy
from typing import Any

from itam_pro.services.mock.seed import MOCK_ASSETS, SEED_IDS


def is_valid_ipv4(ip_str: str) -> bool:
    """Validasi apakah string merupakan alamat IPv4 (a.b.c.d, masing-masing 0..255)."""
    parts = ip_str.strip().split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        if len(part) > 1 and part.startswith("0"):
            return False
        val = int(part)
        if val < 0 or val > 255:
            return False
    return True


def ipv4_sort_tuple(ip_str: str) -> tuple[int, int, int, int]:
    """Konversi IPv4 ke tuple 4 integer untuk pengurutan numerik yang presisi."""
    if not is_valid_ipv4(ip_str):
        return (999, 999, 999, 999)
    p = [int(x) for x in ip_str.strip().split(".")]
    return (p[0], p[1], p[2], p[3])


def derive_subnet_24(ip_str: str) -> str:
    """Turunkan subnet /24 dari alamat IPv4 (contoh: 192.168.10.11 -> 192.168.10.0/24)."""
    if not is_valid_ipv4(ip_str):
        return "—"
    parts = ip_str.strip().split(".")
    return f"{parts[0]}.{parts[1]}.{parts[3 if len(parts) < 3 else 2]}.0/24"


# 26 Entri Mock (Kompatibel penuh dengan seluruh unit test)
MOCK_IP_ENTRIES: list[dict[str, Any]] = [
    {
        "id": "IP-0001",
        "ip_address": "192.168.10.1",
        "nama": "GW-CORE-BLOK14",
        "pengguna": "Admin Jaringan",
        "kategori": "IP Operasional",
        "jenis": "Fisik",
        "asset_id": SEED_IDS["RTR_CORE_01"],
        "host_asset_id": "",
        "grup": "Operasional",
        "fungsi": "Gateway & Firewall Utama",
        "os": "RouterOS v7.15",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0002",
        "ip_address": "192.168.10.2",
        "nama": "SRV-PROXMOX-01",
        "pengguna": "SRV-PROXMOX-01",
        "kategori": "IP Server",
        "jenis": "Fisik",
        "asset_id": SEED_IDS["SRV_PROXMOX_01"],
        "host_asset_id": "",
        "grup": "Operasional",
        "fungsi": "Hypervisor Cluster Node 1",
        "os": "Proxmox VE 8.2",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0003",
        "ip_address": "192.168.10.3",
        "nama": "SRV-ZABBIX-MON",
        "pengguna": "SRV-ZABBIX-MON",
        "kategori": "IP Server",
        "jenis": "Fisik",
        "asset_id": SEED_IDS["SRV_ZABBIX_02"],
        "host_asset_id": "",
        "grup": "Operasional",
        "fungsi": "Monitoring Infrastruktur & SMART Disk",
        "os": "Ubuntu Server 24.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0004",
        "ip_address": "192.168.10.10",
        "nama": "VM-TRX-ENGINE-01",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Core Switching Transaksi Utama",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0005",
        "ip_address": "192.168.10.11",
        "nama": "VM-TRX-ENGINE-02",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Core Switching Transaksi Failover",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0006",
        "ip_address": "192.168.10.12",
        "nama": "VM-DB-PRIMARY",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Database Relasional Produksi",
        "os": "Debian 12 Bookworm",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0007",
        "ip_address": "192.168.10.13",
        "nama": "VM-DB-REPLICA",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Database Read-Replica & Reporting",
        "os": "Debian 12 Bookworm",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0008",
        "ip_address": "192.168.10.14",
        "nama": "VM-REDIS-CACHE",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "In-Memory Cache & Message Broker",
        "os": "Alpine Linux 3.20",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0009",
        "ip_address": "192.168.10.15",
        "nama": "VM-API-GATEWAY",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Reverse Proxy & Rate Limiter",
        "os": "Ubuntu Server 24.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0010",
        "ip_address": "192.168.10.16",
        "nama": "VM-WEB-REPORT",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Portal Laporan Keuangan & CS",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0011",
        "ip_address": "192.168.10.17",
        "nama": "VM-ITAM-PRO",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Aplikasi IT Assets Management Pro",
        "os": "Ubuntu Server 24.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0012",
        "ip_address": "192.168.10.18",
        "nama": "VM-BACKUP-VAULT",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Penyimpanan Snapshot & Dump Harian",
        "os": "Debian 12 Bookworm",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0013",
        "ip_address": "192.168.10.19",
        "nama": "VM-DNS-INTERNAL",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Internal DNS Resolver",
        "os": "Alpine Linux 3.20",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0014",
        "ip_address": "192.168.10.20",
        "nama": "VM-NVR-CCTV",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Aggregator RTSP Multi-Brand CCTV",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    # Pasangan IP Bentrok (192.168.10.25 dipakai di IP-0015 dan IP-0016)
    {
        "id": "IP-0015",
        "ip_address": "192.168.10.25",
        "nama": "VM-BILLER-PLN",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Operasional",
        "fungsi": "Modul Biller PPOB Listrik",
        "os": "Windows Server 2022",
        "status": "Aktif",
        "keterangan": "Konflik IP statis dengan VM-BILLER-PDAM",
    },
    {
        "id": "IP-0016",
        "ip_address": "192.168.10.25",
        "nama": "VM-BILLER-PDAM",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Operasional",
        "fungsi": "Modul Biller Air & Multipayment",
        "os": "Windows Server 2022",
        "status": "Aktif",
        "keterangan": "IP terkonfigurasi ganda saat kloning template",
    },
    # --- 10 ENTRI TAMBAHAN ---
    {
        "id": "IP-0017",
        "ip_address": "192.168.20.11",
        "nama": "VM-ADDON-TG-01",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Addon (VM)",
        "fungsi": "Gateway Bot Transaksi Telegram #1",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0018",
        "ip_address": "192.168.20.12",
        "nama": "VM-ADDON-TG-02",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Addon (VM)",
        "fungsi": "Gateway Bot Transaksi Telegram #2",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0019",
        "ip_address": "192.168.20.13",
        "nama": "VM-ADDON-WA-01",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Addon (VM)",
        "fungsi": "Sender Notifikasi WhatsApp",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0020",
        "ip_address": "192.168.20.14",
        "nama": "VM-ADDON-XMPP",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Addon (VM)",
        "fungsi": "Konektor H2H XMPP / Jabber",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0021",
        "ip_address": "192.168.20.15",
        "nama": "VM-ADDON-DIGIPOS",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0001",
        "grup": "Addon (VM)",
        "fungsi": "Modul Addon Digipos Telkomsel",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0022",
        "ip_address": "192.168.20.16",
        "nama": "VM-ADDON-ISIMPEL",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Addon (VM)",
        "fungsi": "Modul Addon Indosat i-Simpel",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0023",
        "ip_address": "192.168.20.17",
        "nama": "VM-ADDON-SIDOMPUL",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Addon (VM)",
        "fungsi": "Modul Addon XL Sidompul",
        "os": "Windows 10 Pro",
        "status": "Aktif",
        "keterangan": "",
    },
    {
        "id": "IP-0024",
        "ip_address": "192.168.20.18",
        "nama": "VM-ADDON-SANDBOX",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "SRV-0002",
        "grup": "Addon (VM)",
        "fungsi": "Environment QA & Testing Addon",
        "os": "Ubuntu Server 24.04 LTS",
        "status": "Nonaktif",
        "keterangan": "Perlu pengecekan service worker sebelum diaktifkan kembali",
    },
    # 2 VM Tanpa Host (Orphaned VM)
    {
        "id": "IP-0025",
        "ip_address": "192.168.20.91",
        "nama": "VM-LEGACY-SMS",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "",
        "grup": "Addon (VM)",
        "fungsi": "Gateway SMS Modem Pool Lama",
        "os": "Windows 7 Pro",
        "status": "Nonaktif",
        "keterangan": "Host lama sudah dipensiunkan, belum dimigrasi",
    },
    {
        "id": "IP-0026",
        "ip_address": "192.168.20.92",
        "nama": "VM-TEMP-MIGRASI",
        "jenis": "VM",
        "asset_id": "",
        "host_asset_id": "",
        "grup": "Addon (VM)",
        "fungsi": "Staging Migrasi Skema Baru",
        "os": "Ubuntu Server 22.04 LTS",
        "status": "Nonaktif",
        "keterangan": "Menunggu alokasi host server fisik baru",
    },
]

_IP_COUNTER: int = 26


def get_server_assets_map() -> dict[str, str]:
    """Kembalikan pemetaan {id_aset: nama_aset} khusus aset berkategori 'Server'."""
    result: dict[str, str] = {}
    for item in MOCK_ASSETS:
        if item.get("kategori") == "Server":
            aid = str(item.get("id_aset", ""))
            nama = str(item.get("nama_aset", aid))
            if aid:
                result[aid] = nama
    return result


def get_conflict_ip_map() -> dict[str, list[str]]:
    """Kembalikan daftar IP yang dipakai lebih dari 1 entri: {ip_address: [nama1, nama2]}."""
    by_ip: dict[str, list[str]] = {}
    for entry in MOCK_IP_ENTRIES:
        ip = str(entry.get("ip_address", "")).strip()
        if ip:
            by_ip.setdefault(ip, []).append(str(entry.get("nama", entry.get("id", ""))))
    return {ip: names for ip, names in by_ip.items() if len(names) > 1}


def get_ip_conflict_summary() -> dict[str, Any]:
    """Ringkasan konflik IP untuk kartu KPI, banner halaman IP, dan alert Dashboard."""
    conflicts = get_conflict_ip_map()
    conflict_entry_count = sum(len(names) for names in conflicts.values())
    details = [f"{ip} ({', '.join(names)})" for ip, names in conflicts.items()]
    return {
        "conflict_ip_count": len(conflicts),
        "conflict_entry_count": conflict_entry_count,
        "conflict_ips": list(conflicts.keys()),
        "conflict_details": details,
        "banner_message": (
            f"Terdeteksi {conflict_entry_count} entri dengan alamat IP bentrok: "
            + "; ".join(details)
            if details
            else ""
        ),
    }


def find_ip_duplicate_owner(ip_address: str, exclude_id: str = "") -> str | None:
    """Cek apakah IP sudah dipakai oleh entri lain. Kembalikan `nama` jika duplikat."""
    target = ip_address.strip()
    if not target:
        return None
    for entry in MOCK_IP_ENTRIES:
        if entry.get("id") == exclude_id:
            continue
        if str(entry.get("ip_address", "")).strip() == target:
            return str(entry.get("nama", entry.get("id", "")))
    return None


def enrich_ip_entry(
    raw: dict[str, Any],
    server_map: dict[str, str],
    conflict_map: dict[str, list[str]],
) -> dict[str, Any]:
    """Lengkapi field turunan tampilan untuk konsumsi tabel dan drawer."""
    row = deepcopy(raw)
    ip = str(row.get("ip_address", "")).strip()
    jenis = str(row.get("jenis", "Fisik")).strip() or "Fisik"
    asset_id = str(row.get("asset_id", "")).strip()
    host_id = str(row.get("host_asset_id", "")).strip()
    ket_raw = str(row.get("keterangan", "")).strip()
    has_kendala = bool(ket_raw and ket_raw != "—")

    row["subnet"] = derive_subnet_24(ip)
    row["is_conflict"] = ip in conflict_map
    row["has_kendala"] = has_kendala

    if jenis == "Fisik":
        base_sub = f"Aset: {asset_id}" if asset_id else "Server / PC fisik"
        row["host_label"] = "—"
    else:
        if host_id:
            host_name = server_map.get(host_id, "")
            base_sub = f"Host: {host_id}"
            row["host_label"] = host_name if host_name else host_id
        else:
            base_sub = "Tanpa host"
            row["host_label"] = "Tanpa host"

    row["pengguna"] = row.get("pengguna") or row.get("nama") or "—"
    row["kategori"] = row.get("kategori") or "IP Operasional"
    row["sub_label"] = "● Ada kendala (lihat keterangan)" if has_kendala else base_sub
    row["fungsi"] = row.get("fungsi") or "—"
    row["os"] = row.get("os") or "—"
    row["keterangan"] = ket_raw if has_kendala else "—"
    return row


def query_mock_ip_entries(
    grup: str,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Query entri IP dengan kalkulasi KPI, filter Jenis (Fisik/VM), dan pengurutan IPv4 numerik."""
    server_map = get_server_assets_map()
    conflict_map = get_conflict_ip_map()
    all_enriched = [enrich_ip_entry(e, server_map, conflict_map) for e in MOCK_IP_ENTRIES]

    total_all = len(all_enriched)
    count_fisik = sum(1 for x in all_enriched if x.get("jenis") == "Fisik")
    count_vm = sum(1 for x in all_enriched if x.get("jenis") == "VM")
    count_operasional = sum(1 for x in all_enriched if x.get("grup") == "Operasional")
    count_addon = sum(1 for x in all_enriched if x.get("grup") == "Addon (VM)")
    count_conflict = sum(1 for x in all_enriched if x.get("is_conflict"))
    count_orphan_vm = sum(
        1
        for x in all_enriched
        if x.get("jenis") == "VM" and not str(x.get("host_asset_id", "")).strip()
    )

    subnets = sorted(
        {str(x["subnet"]) for x in all_enriched if x.get("subnet") and x["subnet"] != "—"},
        key=lambda s: ipv4_sort_tuple(s.split("/")[0]),
    )
    os_suggestions = sorted({str(x["os"]) for x in all_enriched if x.get("os") and x["os"] != "—"})
    host_options = [f"{aid} ({name})" for aid, name in server_map.items()]

    search = str(filters.get("search", "")).strip().lower()
    f_jenis = str(filters.get("jenis", "")).strip()
    f_host = str(filters.get("host", "")).strip()
    f_kategori = str(filters.get("kategori", "")).strip()
    f_subnet = str(filters.get("subnet", "")).strip()
    f_status = str(filters.get("status", "")).strip()
    only_conflict = bool(filters.get("only_conflict", False))
    only_orphan_vm = bool(filters.get("only_orphan_vm", False))
    sort_by = str(filters.get("sort_by", "ip_address")).strip() or "ip_address"
    sort_dir = str(filters.get("sort_dir", "asc")).strip().lower()

    filtered: list[dict[str, Any]] = []
    for item in all_enriched:
        if grup and grup != "Semua":
            if grup in ("Fisik", "VM"):
                if item.get("jenis") != grup:
                    continue
            elif item.get("grup") != grup:
                continue
        if only_conflict and not item.get("is_conflict"):
            continue
        if only_orphan_vm and not (
            item.get("jenis") == "VM" and not str(item.get("host_asset_id", "")).strip()
        ):
            continue
        if f_jenis and item.get("jenis") != f_jenis:
            continue
        if f_host:
            host_code = f_host.split(" ", 1)[0].strip()
            if host_code == "Tanpa" and str(item.get("host_asset_id", "")).strip():
                continue
            elif host_code != "Tanpa" and str(item.get("host_asset_id", "")) != host_code:
                continue
        if f_kategori and item.get("kategori") != f_kategori:
            continue
        if f_subnet and item.get("subnet") != f_subnet:
            continue
        if f_status and item.get("status") != f_status:
            continue
        if search:
            haystack = " ".join(
                [
                    str(item.get("ip_address", "")),
                    str(item.get("nama", "")),
                    str(item.get("pengguna", "")),
                    str(item.get("kategori", "")),
                    str(item.get("fungsi", "")),
                    str(item.get("os", "")),
                    str(item.get("asset_id", "")),
                    str(item.get("host_asset_id", "")),
                    str(item.get("keterangan", "")),
                ]
            ).lower()
            if search not in haystack:
                continue
        filtered.append(item)

    reverse = sort_dir == "desc"
    if sort_by == "ip_address":
        filtered.sort(key=lambda x: ipv4_sort_tuple(str(x.get("ip_address", ""))), reverse=reverse)
    else:
        filtered.sort(key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)

    total = len(filtered)
    start = max(0, (page - 1) * page_size)
    paginated = filtered[start : start + page_size]

    conflict_info = get_ip_conflict_summary()

    return {
        "items": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "kpi": {
            "total_ip": total_all,
            "fisik": count_fisik,
            "vm": count_vm,
            "operasional": count_operasional,
            "addon": count_addon,
            "bentrok": count_conflict,
            "vm_tanpa_host": count_orphan_vm,
        },
        "conflict_banner": conflict_info["banner_message"],
        "subnet_options": subnets,
        "host_options": [*host_options, "Tanpa host"],
        "server_asset_ids": list(server_map.keys()),
        "os_suggestions": os_suggestions,
    }


def get_vms_on_host(host_asset_id: str) -> list[dict[str, str]]:
    """Ambil daftar VM yang berjalan di atas host server fisik tertentu."""
    target = host_asset_id.strip()
    if not target:
        return []
    vms: list[dict[str, str]] = []
    for entry in MOCK_IP_ENTRIES:
        if entry.get("jenis") == "VM" and str(entry.get("host_asset_id", "")).strip() == target:
            vms.append(
                {
                    "label": f"{entry.get('nama', '')} ({entry.get('ip_address', '')})",
                    "value": f"{entry.get('fungsi', '—')} · {entry.get('status', 'Aktif')}",
                }
            )
    return vms


def create_mock_ip_entry(payload: dict[str, Any]) -> dict[str, Any]:
    """Tambahkan entri IP baru ke dalam MOCK_IP_ENTRIES."""
    global _IP_COUNTER
    _IP_COUNTER += 1
    jenis = str(payload.get("jenis", "Fisik")).strip()
    pengguna_val = str(payload.get("pengguna") or payload.get("nama") or "").strip()
    nama_val = str(payload.get("nama") or pengguna_val).strip()
    record: dict[str, Any] = {
        "id": f"IP-{_IP_COUNTER:04d}",
        "ip_address": str(payload.get("ip_address", "")).strip(),
        "nama": nama_val,
        "pengguna": pengguna_val,
        "kategori": str(payload.get("kategori") or "IP Operasional").strip(),
        "jenis": jenis,
        "asset_id": str(payload.get("asset_id", "")).strip() if jenis == "Fisik" else "",
        "host_asset_id": str(payload.get("host_asset_id", "")).strip() if jenis == "VM" else "",
        "grup": str(
            payload.get("grup") or ("Addon (VM)" if jenis == "VM" else "Operasional")
        ).strip(),
        "fungsi": str(payload.get("fungsi", "")).strip(),
        "os": str(payload.get("os", "")).strip(),
        "status": str(payload.get("status", "Aktif")).strip(),
        "keterangan": str(payload.get("keterangan", "")).strip(),
    }
    MOCK_IP_ENTRIES.append(record)
    return enrich_ip_entry(record, get_server_assets_map(), get_conflict_ip_map())


def update_mock_ip_entry(entry_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Perbarui satu entri IP berdasarkan ID internal."""
    for idx, item in enumerate(MOCK_IP_ENTRIES):
        if item.get("id") == entry_id:
            jenis = str(payload.get("jenis", item.get("jenis", "Fisik"))).strip()
            pengguna_val = str(
                payload.get("pengguna")
                or payload.get("nama")
                or item.get("pengguna")
                or item.get("nama", "")
            ).strip()
            nama_val = str(payload.get("nama") or pengguna_val or item.get("nama", "")).strip()
            updated: dict[str, Any] = {
                **item,
                "ip_address": str(payload.get("ip_address", item["ip_address"])).strip(),
                "nama": nama_val,
                "pengguna": pengguna_val,
                "kategori": str(
                    payload.get("kategori") or item.get("kategori") or "IP Operasional"
                ).strip(),
                "jenis": jenis,
                "asset_id": (str(payload.get("asset_id", "")).strip() if jenis == "Fisik" else ""),
                "host_asset_id": (
                    str(payload.get("host_asset_id", "")).strip() if jenis == "VM" else ""
                ),
                "grup": str(
                    payload.get("grup") or ("Addon (VM)" if jenis == "VM" else "Operasional")
                ).strip(),
                "fungsi": str(payload.get("fungsi", "")).strip(),
                "os": str(payload.get("os", "")).strip(),
                "status": str(payload.get("status", item["status"])).strip(),
                "keterangan": str(payload.get("keterangan", "")).strip(),
            }
            MOCK_IP_ENTRIES[idx] = updated
            return enrich_ip_entry(updated, get_server_assets_map(), get_conflict_ip_map())
    return None


def delete_mock_ip_entry(entry_id: str) -> bool:
    """Hapus satu entri IP berdasarkan ID internal."""
    for idx, item in enumerate(MOCK_IP_ENTRIES):
        if item.get("id") == entry_id:
            MOCK_IP_ENTRIES.pop(idx)
            return True
    return False


__all__ = [
    "MOCK_IP_ENTRIES",
    "create_mock_ip_entry",
    "delete_mock_ip_entry",
    "derive_subnet_24",
    "enrich_ip_entry",
    "find_ip_duplicate_owner",
    "get_conflict_ip_map",
    "get_ip_conflict_summary",
    "get_server_assets_map",
    "get_vms_on_host",
    "ipv4_sort_tuple",
    "is_valid_ipv4",
    "query_mock_ip_entries",
    "update_mock_ip_entry",
]
