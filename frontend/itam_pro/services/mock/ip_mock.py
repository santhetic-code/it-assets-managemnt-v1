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


REGISTERED_SUBNET_CIDR = "192.168.1.0/24"


def has_kendala(entry_or_ket: Any, fungsi: str = "") -> bool:
    """A2: True hanya jika keterangan.trim() tidak kosong dan tidak sama persis dengan Fungsi."""
    if isinstance(entry_or_ket, dict):
        ket_raw = str(entry_or_ket.get("keterangan") or "").strip()
        fn_raw = str(fungsi or entry_or_ket.get("fungsi") or "").strip()
    else:
        ket_raw = str(entry_or_ket or "").strip()
        fn_raw = str(fungsi or "").strip()
    if not ket_raw or ket_raw in ("—", "-"):
        return False
    if fn_raw and ket_raw.lower() == fn_raw.lower():
        return False
    return True


hasKendala = has_kendala


def is_ip_in_registered_subnet(
    ip_str: str,
    subnet_cidr: str = REGISTERED_SUBNET_CIDR,
) -> bool:
    """B4: Cek apakah IP berada di dalam subnet terdaftar (default 192.168.1.0/24)."""
    if not is_valid_ipv4(ip_str):
        return False
    prefix = ".".join(subnet_cidr.split("/")[0].split(".")[:3])
    return ip_str.strip().startswith(f"{prefix}.")


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
    """Lengkapi field turunan tampilan untuk konsumsi tabel dan drawer (A2, B4)."""
    row = deepcopy(raw)
    ip = str(row.get("ip_address", "")).strip()
    jenis = str(row.get("jenis", "Fisik")).strip() or "Fisik"
    asset_id = str(row.get("asset_id", "")).strip()
    host_id = str(row.get("host_asset_id", "")).strip()
    fungsi_val = str(row.get("fungsi") or "").strip()
    ket_raw = str(row.get("keterangan") or "").strip()
    kendala = has_kendala(ket_raw, fungsi_val)
    outside_subnet = bool(ip and not is_ip_in_registered_subnet(ip))

    row["subnet"] = derive_subnet_24(ip)
    row["is_conflict"] = ip in conflict_map
    row["has_kendala"] = kendala
    row["is_outside_subnet"] = outside_subnet

    if jenis == "Fisik":
        base_sub = f"Aset: {asset_id}" if asset_id else "Server / PC fisik"
        row["host_label"] = "—"
    else:
        if host_id:
            host_name = server_map.get(host_id, "")
            base_sub = f"Host: {host_id}"
            row["host_label"] = f"{host_id} ({host_name})" if host_name else host_id
        else:
            base_sub = "Tanpa host"
            row["host_label"] = "Tanpa host"

    if kendala:
        sub_lbl = "● Ada kendala (lihat keterangan)"
    elif outside_subnet:
        sub_lbl = f"{base_sub} · Di luar subnet"
    else:
        sub_lbl = base_sub

    row["pengguna"] = row.get("pengguna") or row.get("nama") or "—"
    row["kategori"] = row.get("kategori") or ("IP VM" if jenis == "VM" else "IP Operasional")
    row["sub_label"] = sub_lbl
    row["fungsi"] = fungsi_val or "—"
    row["os"] = row.get("os") or "—"
    row["keterangan"] = ket_raw if kendala else ""
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

    os_suggestions = sorted({str(x["os"]) for x in all_enriched if x.get("os") and x["os"] != "—"})

    # A3: Dropdown "Semua host" hanya berisi host yang punya VM terhubung + jumlah VM
    vm_counts_by_host: dict[str, int] = {}
    for x in all_enriched:
        if x.get("jenis") == "VM":
            hid = str(x.get("host_asset_id", "")).strip()
            if hid:
                vm_counts_by_host[hid] = vm_counts_by_host.get(hid, 0) + 1

    connected_host_options = [
        f"{hid} ({server_map.get(hid, hid)}) · {cnt} VM"
        if server_map.get(hid)
        else f"{hid} · {cnt} VM"
        for hid, cnt in sorted(vm_counts_by_host.items())
        if cnt > 0
    ]
    host_server_options = [f"{aid} ({name})" for aid, name in sorted(server_map.items())]

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
        if f_host and f_host not in ("Semua", "Semua host"):
            clean_h = f_host.split("·", 1)[0].strip()
            host_code = clean_h.split(" ", 1)[0].strip()
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
    used_in_main_subnet = sum(
        1
        for x in all_enriched
        if str(x.get("ip_address", "")).startswith("192.168.1.")
        and str(x.get("ip_address", "")) not in ("192.168.1.0", "192.168.1.255")
    )
    kosong_main = max(0, 254 - used_in_main_subnet)

    return {
        "items": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "kpi": {
            "total_ip": total_all,
            "fisik": count_fisik,
            "vm": count_vm,
            "kosong": kosong_main,
            "operasional": count_operasional,
            "addon": count_addon,
            "bentrok": count_conflict,
            "vm_tanpa_host": count_orphan_vm,
        },
        "conflict_banner": conflict_info["banner_message"],
        "subnet_options": [REGISTERED_SUBNET_CIDR],
        "subnets": [{"id": 1, "cidr": REGISTERED_SUBNET_CIDR, "nama": "Subnet Utama LAN"}],
        "host_options": connected_host_options,
        "host_server_options": host_server_options,
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


def get_mock_ip_map(subnet: str = "192.168.1.0/24") -> dict[str, Any]:
    """Menghasilkan representasi 256 sel peta IP untuk mode mock."""
    clean_subnet = subnet.strip()
    base_ip = clean_subnet.split("/")[0] if "/" in clean_subnet else clean_subnet
    parts = base_ip.split(".")
    prefix = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else "192.168.1"
    normalized_subnet = f"{prefix}.0/24"

    alloc_map: dict[int, dict[str, Any]] = {}
    for item in MOCK_IP_ENTRIES:
        ip = str(item.get("ip_address", "")).strip()
        if ip.startswith(f"{prefix}."):
            try:
                oct_val = int(ip.split(".")[3])
                alloc_map[oct_val] = item
            except (IndexError, ValueError):
                continue

    cells: list[dict[str, Any]] = []
    terpakai = 0
    fisik_count = 0
    vm_count = 0
    nonaktif_count = 0

    for octet in range(256):
        ip_str = f"{prefix}.{octet}"
        if octet == 0:
            cells.append(
                {
                    "octet": octet,
                    "ip_address": ip_str,
                    "status": "network",
                    "label": "Network ID",
                    "is_reserved": True,
                    "is_occupied": False,
                }
            )
        elif octet == 255:
            cells.append(
                {
                    "octet": octet,
                    "ip_address": ip_str,
                    "status": "broadcast",
                    "label": "Broadcast",
                    "is_reserved": True,
                    "is_occupied": False,
                }
            )
        else:
            alloc = alloc_map.get(octet)
            if alloc:
                terpakai += 1
                is_nonaktif = str(alloc.get("status", "")).lower() == "nonaktif"
                is_vm = str(alloc.get("jenis", "")).upper() == "VM"
                if is_nonaktif:
                    cell_status = "nonaktif"
                    nonaktif_count += 1
                elif is_vm:
                    cell_status = "vm"
                    vm_count += 1
                else:
                    cell_status = "fisik"
                    fisik_count += 1

                cells.append(
                    {
                        "octet": octet,
                        "ip_address": ip_str,
                        "status": cell_status,
                        "is_reserved": False,
                        "is_occupied": True,
                        "entry_id": alloc.get("id"),
                        "nama": alloc.get("nama") or alloc.get("pengguna", ""),
                        "pengguna": alloc.get("pengguna") or alloc.get("nama", ""),
                        "jenis": "VM" if is_vm else "Fisik",
                        "host": alloc.get("host_asset_id") or ("—" if not is_vm else "Tanpa host"),
                        "os": alloc.get("os", "—"),
                        "fungsi": alloc.get("fungsi", "—"),
                    }
                )
            else:
                cells.append(
                    {
                        "octet": octet,
                        "ip_address": ip_str,
                        "status": "kosong",
                        "is_reserved": False,
                        "is_occupied": False,
                        "label": "Tersedia",
                    }
                )

    kosong = 254 - terpakai

    empty_octets = [
        c["octet"] for c in cells if not c.get("is_reserved") and not c.get("is_occupied")
    ]
    suggested_octets = [o for o in empty_octets if o > 1][:5]
    if len(suggested_octets) < 5:
        suggested_octets = empty_octets[:5]
    suggested_ips = [f"{prefix}.{o}" for o in suggested_octets]

    largest_start = None
    largest_end = None
    largest_len = 0
    cur_start = None
    cur_len = 0

    for octet in range(1, 255):
        if octet not in alloc_map:
            if cur_start is None:
                cur_start = octet
                cur_len = 1
            else:
                cur_len += 1
            if cur_len > largest_len:
                largest_len = cur_len
                largest_start = cur_start
                largest_end = octet
        else:
            cur_start = None
            cur_len = 0

    if largest_start is not None and largest_end is not None and largest_len > 0:
        largest_empty_range = (
            f"{prefix}.{largest_start} - {prefix}.{largest_end} ({largest_len} IP)"
        )
    else:
        largest_empty_range = "Tidak ada rentang kosong"

    conflict_map = get_conflict_ip_map()
    bentrok_count = sum(
        1 for oct_v, it in alloc_map.items() if str(it.get("ip_address", "")) in conflict_map
    )
    stats = {
        "total_allocatable": 254,
        "terpakai": terpakai,
        "kosong": kosong,
        "fisik": fisik_count,
        "vm": vm_count,
        "nonaktif": nonaktif_count,
        "bentrok": bentrok_count,
        "konflik": bentrok_count,
        "fisik_percent": round((fisik_count / 254) * 100, 1),
        "vm_percent": round((vm_count / 254) * 100, 1),
        "bentrok_percent": round((bentrok_count / 254) * 100, 1),
        "kosong_percent": round((kosong / 254) * 100, 1),
    }

    return {
        "subnet_id": 1,
        "subnet": normalized_subnet,
        "subnets": [{"id": 1, "cidr": REGISTERED_SUBNET_CIDR, "nama": "Subnet Utama LAN"}],
        "prefix": prefix,
        "cells": cells,
        "stats": stats,
        "suggested_ips": suggested_ips,
        "largest_empty_range": largest_empty_range,
    }


__all__ = [
    "MOCK_IP_ENTRIES",
    "REGISTERED_SUBNET_CIDR",
    "create_mock_ip_entry",
    "delete_mock_ip_entry",
    "derive_subnet_24",
    "enrich_ip_entry",
    "find_ip_duplicate_owner",
    "get_conflict_ip_map",
    "get_ip_conflict_summary",
    "get_mock_ip_map",
    "get_server_assets_map",
    "get_vms_on_host",
    "hasKendala",
    "has_kendala",
    "ipv4_sort_tuple",
    "is_ip_in_registered_subnet",
    "is_valid_ipv4",
    "query_mock_ip_entries",
    "update_mock_ip_entry",
]
