"""Mesin impor data CSV idempoten untuk data operasional ITAM Pro (B9).

Mengimpor data nyata dari folder docs/data/:
1. rekap_ups_xml.csv -> tabel assets (kategori UPS)
2. rekap_watt_server.csv -> tabel assets (kategori Server)
3. ip_list_xml.csv -> tabel ip_allocations (IP Server, Addon/VM, Operasional)
4. rekap_pembelian.csv -> tabel purchases (Rekap Pembelian Aset/Perangkat)
"""

import csv
import io
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, col, select

from app.core.master_data import (
    CATEGORY_TREE,
    LOCATION_ALIASES,
    LOCATIONS,
    normalize_asset_condition,
    normalize_asset_status,
)
from app.core.security import encrypt_secret
from app.models.asset import Asset, AssetLink, Category
from app.models.credential import Credential
from app.models.finance import Purchase
from app.models.ip_allocation import IPAllocation
from app.models.maintenance import Maintenance
from app.schemas.audit import record_audit_log
from app.schemas.ip_allocation import normalize_keterangan, parse_and_validate_ipv4

logger = logging.getLogger(__name__)


def resolve_data_dir(custom_path: Path | str | None = None) -> Path:
    """Menemukan lokasi folder docs/data baik di lokal maupun container Docker."""
    if custom_path is not None:
        p = Path(custom_path)
        if p.exists():
            return p

    candidates = [
        Path.cwd() / "docs" / "data",
        Path(__file__).resolve().parent.parent.parent.parent / "docs" / "data",
        Path(__file__).resolve().parent.parent.parent / "docs" / "data",
        Path("/app/docs/data"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path.cwd() / "docs" / "data"


def _pick(row: dict[str, str], *keys: str, default: str = "") -> str:
    """Mengambil nilai pertama yang tidak kosong dari beberapa variasi nama kolom CSV."""
    for k in keys:
        for row_k, row_v in row.items():
            if row_k.strip().lower() == k.strip().lower() and row_v.strip():
                return row_v.strip()
    return default


def _read_csv_rows(file_path: Path) -> list[dict[str, str]]:
    """Membaca baris CSV menjadi list dictionary dengan toleransi baris kosong & delimiter."""
    if not file_path.exists():
        logger.warning("File CSV tidak ditemukan: %s", file_path)
        return []

    with file_path.open("r", encoding="utf-8-sig", errors="replace") as f:
        raw_lines = f.readlines()

    header_idx = -1
    for idx, line in enumerate(raw_lines):
        clean = line.strip().replace(",", "").replace(";", "")
        if clean:
            header_idx = idx
            break

    if header_idx == -1:
        return []

    first_line = raw_lines[header_idx]

    # Khusus file ip_list_xml.csv (struktur multi-tabel: SERVER, ADDON, OPERASIONAL)
    if "SERVER" in first_line and "ADDON" in first_line and "OPERASIONAL" in first_line:
        reader = list(csv.reader(io.StringIO("".join(raw_lines[header_idx:]))))
        extracted: list[dict[str, str]] = []
        for row in reader[2:]:
            # 1. Server
            if len(row) > 1 and row[1].strip():
                server_name = row[0].strip()
                os_srv = "Proxmox VE 8.2" if "VM" in server_name.upper() else "Windows Server 2022"
                extracted.append(
                    {
                        "ip": row[1].strip(),
                        "nama_perangkat": server_name if server_name else "Server",
                        "tipe": "Fisik",
                        "grup": "Operasional",
                        "os": os_srv,
                        "fungsi": f"Server Produksi ({server_name})",
                        "keterangan": "",
                        "pengguna": "IT Server",
                        "lokasi": "Head Office (Office Blok 14)",
                        "source_block": "SERVER",
                    }
                )
            # 2. Addon / VM
            if len(row) > 5 and row[5].strip():
                addon_host = row[3].strip()
                rincian = row[4].strip().replace("\n", ", ")
                extracted.append(
                    {
                        "ip": row[5].strip(),
                        "nama_perangkat": f"ADDON {addon_host}".strip() if addon_host else "Addon",
                        "tipe": "VM",
                        "grup": "Addon (VM)",
                        "os": "Windows 10 Pro",
                        "host_name": addon_host,
                        "fungsi": rincian or f"Worker Addon {addon_host}",
                        "keterangan": "",
                        "pengguna": "IT System",
                        "lokasi": "Head Office (Office Blok 14)",
                        "source_block": "ADDON",
                    }
                )
            # 3. Operasional
            if len(row) > 8 and row[8].strip():
                user_name = row[7].strip()
                extracted.append(
                    {
                        "ip": row[8].strip(),
                        "nama_perangkat": f"PC {user_name}".strip() if user_name else "PC User",
                        "tipe": "Fisik",
                        "grup": "Operasional",
                        "os": "Windows 11 Pro",
                        "pengguna": user_name,
                        "fungsi": f"Workstation Operasional ({user_name})",
                        "keterangan": "",
                        "lokasi": "Head Office (Office Blok 14)",
                        "source_block": "OPERASIONAL",
                    }
                )
        return extracted

    # Untuk file CSV tabel biasa:
    content = "".join(raw_lines[header_idx:])
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows: list[dict[str, str]] = []
    for r in reader:
        clean_row = {
            (k.strip() if k else ""): (v.strip() if isinstance(v, str) else "")
            for k, v in r.items()
            if k is not None
        }
        if any(clean_row.values()):
            rows.append(clean_row)
    return rows


def _parse_int(val: Any) -> int:
    """Mengekstrak angka integer dari teks (contoh: '650 VA', '450W', '1.500.000')."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip()
    if not text:
        return 0
    # Ambil bagian sebelum koma desimal jika ada
    if "," in text and "." not in text:
        text = text.split(",")[0]
    digits = re.sub(r"[^\d-]", "", text)
    try:
        return int(digits)
    except ValueError:
        return 0


def _parse_rupiah(val: Any) -> int:
    """Membersihkan format Rupiah ('Rp 1.500.000', 'Rp77.500,00') menjadi angka bulat."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip()
    if not text:
        return 0
    # Hilangkan awalan Rp/IDR
    text = re.sub(r"^(?:Rp|rp|IDR|idr)\.?\s*", "", text)
    # Jika berakhiran ,00 atau desimal, buang bagian desimalnya
    if "," in text:
        parts = text.rsplit(",", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) in (1, 2):
            text = parts[0]
    # Hapus pemisah ribuan titik
    cleaned = text.replace(".", "").replace(" ", "")
    digits = re.sub(r"[^\d-]", "", cleaned)
    try:
        return int(digits)
    except ValueError:
        return 0


def _parse_date(val: Any) -> date | None:
    """Mengonversi teks tanggal berbagai format (DD/MM/YYYY, YYYY-MM-DD, dsb.) ke date."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    text = str(val).strip()
    if not text:
        return None

    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_loc(raw: str | None = None) -> str:
    """Menormalisasi nama lokasi CSV dengan prioritas pencocokan dari yang paling spesifik."""
    cleaned = (raw or "").strip()
    if not cleaned:
        return "Head Office (Office Blok 14)"
    for loc in LOCATIONS:
        if loc.lower() == cleaned.lower():
            return loc

    low = cleaned.lower()
    ordered_rules: list[tuple[tuple[str, ...], str]] = [
        (("437", "office blok 12", "kantor blok 12"), "Office 437 (Office Blok 12)"),
        (("mess", "mess blok 12"), "Mess (Mess Blok 12)"),
        (("konter", "rinjani", "ruko rinjani"), "Konter (Ruko Rinjani)"),
        (("white house", "wh", "blok 13", "office blok 13"), "White House (Office Blok 13)"),
        (("head office", "ho", "blok 14", "office blok 14"), "Head Office (Office Blok 14)"),
    ]
    for keywords, target_location in ordered_rules:
        if any(k in low for k in keywords):
            return target_location

    if low in LOCATION_ALIASES:
        return LOCATION_ALIASES[low]
    return "Head Office (Office Blok 14)"


def import_ups_csv(session: Session, file_path: Path) -> int:
    """Mengimpor data UPS dari rekap_ups_xml.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    for row in rows:
        raw_id = row.get("ID UPS", "").strip()
        if not raw_id:
            continue
        # Format id_aset bersih (misal: 'UPS - 001' -> 'UPS-001')
        id_aset = re.sub(r"\s+", "", raw_id)

        # Cek idempotensi
        existing = session.exec(select(Asset).where(col(Asset.id_aset) == id_aset)).first()
        if existing is not None:
            continue

        merk = row.get("MERK UPS", "").strip()
        kategori_aki = row.get("KATEGORI AKI", "").strip()
        kapasitas_val = _parse_int(row.get("KAPASITAS (VA/WATT)", ""))
        status_ops = row.get("STATUS OPERASIONAL", "").strip().upper()
        id_server = row.get("ID SERVER", "").strip()
        keterangan = row.get("KETERANGAN", "").strip()

        is_digunakan = status_ops == "DIGUNAKAN"
        status_aset = (
            "Digunakan" if is_digunakan else ("Backup" if status_ops == "BACKUP" else "Digunakan")
        )
        beban = id_server if id_server and id_server != "BACKUP" else ""
        jumlah_aki = (
            2 if "DUAL" in kategori_aki.upper() else (1 if "SATU" in kategori_aki.upper() else 0)
        )
        nama_aset = (
            f"UPS {merk} {kapasitas_val}VA ({kategori_aki})"
            if merk and kapasitas_val and kategori_aki
            else (
                f"UPS {merk} {kapasitas_val}VA"
                if merk and kapasitas_val
                else f"UPS {merk or id_aset}"
            )
        )

        asset = Asset(
            id_aset=id_aset,
            nama_aset=nama_aset,
            kategori="UPS",
            merek=merk,
            model=kategori_aki,
            lokasi="Head Office (Office Blok 14)",
            detail_lokasi="Server Room",
            penanggung_jawab=beban or "Cadangan Gudang IT",
            status=status_aset,
            kondisi="Baru",
            tanggal_masuk=date(2025, 6, 15),
            kapasitas_va=kapasitas_val,
            kapasitas_watt=int(kapasitas_val * 0.6) if kapasitas_val else 0,
            baterai=kategori_aki,
            jumlah_baterai=jumlah_aki,
            beban_perangkat=beban,
            catatan=f"Status: {keterangan}. Terhubung: {id_server}".strip(),
            extra_specs={
                "kepemilikan": "XML",
                "tanggal_masuk_gudang": "2025-06-15",
                "tanggal_keluar_gudang": "2025-06-16" if is_digunakan else "",
            },
        )
        session.add(asset)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def import_watt_server_csv(session: Session, file_path: Path) -> int:
    """Mengimpor data Server dari rekap_watt_server.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    # Ambil nomor urut server tertinggi yang sudah ada di database
    existing_srvs = session.exec(
        select(Asset.id_aset).where(col(Asset.id_aset).like("SRV-%"))
    ).all()
    max_num = 0
    for srv_id in existing_srvs:
        m = re.match(r"^SRV-(\d+)$", srv_id)
        if m:
            max_num = max(max_num, int(m.group(1)))

    for row in rows:
        id_server_raw = row.get("ID SERVER", "").strip()
        if not id_server_raw or id_server_raw.upper().startswith("ESTIMASI"):
            continue

        # Cek idempotensi berdasarkan nama aset
        existing = session.exec(select(Asset).where(col(Asset.nama_aset) == id_server_raw)).first()
        if existing is not None:
            continue

        max_num += 1
        new_id_aset = f"SRV-{max_num:03d}"

        cpu = row.get("MODEL PROSESOR (CPU)", "").strip()
        gpu = row.get("KARTU GRAFIS (GPU)", "").strip()
        ram = row.get("KONFIGURASI RAM", "").strip()
        storage = row.get("KONFIGURASI PENYIMPANAN", "").strip()
        watt = _parse_int(row.get("TOTAL TDP (W)", "0"))
        psu_min = _parse_int(row.get("PSU MINIMUM (W)", "0"))
        psu_rek = _parse_int(row.get("PSU REKOMENDASI (W)", "0"))

        is_backup = "BACKUP" in id_server_raw.upper()
        os_val = "Proxmox VE 8.2" if "VM" in id_server_raw.upper() else "Windows Server 2022"
        status_srv = "Backup" if is_backup else "Digunakan"
        pemakai = "Cadangan Server Room" if is_backup else f"Server Produksi ({id_server_raw})"

        asset = Asset(
            id_aset=new_id_aset,
            nama_aset=id_server_raw,
            kategori="Server",
            merek="Rakitan Server",
            model="Rackmount / Desktop Server",
            lokasi="Head Office (Office Blok 14)",
            detail_lokasi="Server Room",
            penanggung_jawab=pemakai,
            status=status_srv,
            kondisi="Baru",
            tanggal_masuk=date(2025, 1, 10),
            processor=cpu,
            motherboard="Server Mainboard",
            gpu=gpu,
            ram=ram,
            storage=storage,
            os=os_val,
            watt=watt,
            extra_specs={
                "jenis": "Backup" if is_backup else "Server",
                "os": os_val,
                "cpu": cpu,
                "vga": gpu,
                "ram": ram,
                "hdd_ssd": storage,
                "mainboard": "Server Mainboard",
                "monitor": "—",
                "keyboard": "—",
                "mouse": "—",
                "tdp_total_w": str(watt),
                "psu_min_w": str(psu_min),
                "psu_rekomendasi_w": str(psu_rek),
                "psu_minimum_watt": psu_min,
                "psu_rekomendasi_watt": psu_rek,
                "kepemilikan": "XML",
                "tanggal_masuk_gudang": "2025-01-10",
                "tanggal_keluar_gudang": "" if is_backup else "2025-01-12",
            },
            catatan=f"Spesifikasi daya: TDP {watt}W (Min PSU {psu_min}W, Rekomendasi {psu_rek}W)",
        )
        session.add(asset)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def _match_server_asset(raw_name: str, server_assets: list[Asset]) -> Asset | None:
    """Mencocokkan nama server / host dari ip_list_xml.csv ke baris Asset kategori Server."""
    cleaned = raw_name.strip().upper()
    if not cleaned:
        return None

    # Normalisasi singkatan umum di ip_list_xml.csv ke nama di rekap_watt_server.csv
    normalized = (
        cleaned.replace("OTOMAX ", "OTO ")
        .replace("MESIN SYSTEM VOUCHER", "MESIN VOUCHER")
        .replace("BACKUP SERVER ", "BACKUP ")
    )
    for srv in server_assets:
        srv_up = srv.nama_aset.strip().upper()
        if (
            srv_up == cleaned
            or srv_up == f"SERVER {cleaned}"
            or srv_up == f"SERVER {normalized}"
            or normalized in srv_up
        ):
            return srv

    # Pencocokan langsung nama grup/brand di kolom SERVER ADDON ip_list_xml.csv
    direct_host_map = {
        "XML MOBILE": "SERVER VM SDP",
        "ALL SERVER RETAIL": "SERVER OTO RETAIL",
        "PULSA HOKI": "SERVER OTO PH",
        "XMLTRONIK H2H": "SERVER OTO H2H",
        "OTOTEPE": "SERVER OTO OTOTEPE",
        "ALL SERVER": "SERVER INDUK SERVER 2",
        "MODUL TRANSAKSI": "SERVER OTO SAMU",
    }
    if cleaned in direct_host_map:
        target_direct = direct_host_map[cleaned]
        for srv in server_assets:
            if srv.nama_aset.strip().upper() == target_direct:
                return srv

    # Pencocokan prefix untuk ADDON (misal 'SDP 1' -> 'SERVER VM SDP', 'H2H 1' -> 'SERVER OTO H2H')
    prefix_token = cleaned.split()[0] if cleaned.split() else ""
    addon_map = {
        "SDP": "SERVER VM SDP",
        "H2H": "SERVER OTO H2H",
        "SAMU": "SERVER OTO SAMU",
        "PH": "SERVER OTO PH",
        "RETAIL": "SERVER OTO RETAIL",
        "GERAI": "SERVER OTO GERAI",
        "OTOTEPE": "SERVER OTO OTOTEPE",
    }
    target_srv_name = addon_map.get(prefix_token)
    if target_srv_name:
        for srv in server_assets:
            if srv.nama_aset.strip().upper() == target_srv_name:
                return srv
    return None


def import_ip_list_csv(session: Session, file_path: Path) -> int:
    """Impor ip_list_xml.csv ke tabel ip_allocations & tautkan otomatis ke Asset bila cocok."""
    rows = _read_csv_rows(file_path)
    all_assets = list(session.exec(select(Asset)).all())
    assets_by_name = {a.nama_aset.strip().lower(): a for a in all_assets}
    server_assets = [a for a in all_assets if a.kategori.lower() == "server"]

    # Hitung nomor urut PC tertinggi untuk membuat aset PC Operasional dari ip_list_xml.csv
    existing_pcs = session.exec(select(Asset.id_aset).where(col(Asset.id_aset).like("PC-%"))).all()
    max_pc_num = 0
    for pc_id in existing_pcs:
        m = re.match(r"^PC-(\d+)$", pc_id)
        if m:
            max_pc_num = max(max_pc_num, int(m.group(1)))

    imported = 0
    for r in rows:
        raw_ip = _pick(r, "ip_address", "ip", "alamat_ip", "address")
        if not raw_ip:
            continue
        try:
            canonical_ip, ip_int = parse_and_validate_ipv4(raw_ip)
        except ValueError:
            continue

        nama = _pick(
            r,
            "nama_perangkat",
            "perangkat",
            "hostname",
            "nama_vm",
            "nama",
            "user",
            "pengguna",
            "keterangan",
            default=f"Device-{canonical_ip}",
        )
        tipe_raw = _pick(r, "tipe", "kategori", "jenis", default="Fisik")
        host_raw = _pick(r, "host_name", "host", "induk", "server_host")
        source_block = r.get("source_block", "")
        is_vm = "vm" in tipe_raw.lower() or "virtual" in tipe_raw.lower() or bool(host_raw)

        lokasi = _normalize_loc(_pick(r, "lokasi", "cabang", "site", "ruangan"))
        fungsi_val = _pick(r, "fungsi", "port_servis", default="Operasional")
        ket_raw = _pick(r, "keterangan", "catatan", "deskripsi")
        ket_norm = normalize_keterangan(ket_raw, fungsi_val)
        pengguna = _pick(r, "pengguna", "user", "pic", "penanggung_jawab")
        os_val = _pick(r, "os", "sistem_operasi")

        # Bila berasal dari blok OPERASIONAL dan belum ada aset PC-nya, buat aset PC Operasional
        if source_block == "OPERASIONAL" and nama.strip().lower() not in assets_by_name:
            max_pc_num += 1
            new_pc_id = f"PC-{max_pc_num:03d}"
            pc_asset = Asset(
                id_aset=new_pc_id,
                nama_aset=nama.strip(),
                kategori="PC",
                merek="Rakitan PC",
                model="Workstation Operasional",
                lokasi=lokasi,
                detail_lokasi="Ruang Operasional",
                penanggung_jawab=pengguna or nama.replace("PC ", "").strip(),
                status="Digunakan",
                kondisi="Baru",
                tanggal_masuk=date(2025, 3, 10),
                processor="Intel Core i5-12400",
                motherboard="ASUS Prime H610M",
                ram="16GB DDR4",
                storage="SSD NVMe 512GB",
                gpu="Intel UHD Graphics 730",
                os=os_val or "Windows 11 Pro",
                watt=0,
                ip_address=canonical_ip,
                catatan=f"Workstation operasional ({pengguna}) - IP {canonical_ip}",
                extra_specs={
                    "jenis": "Operasional",
                    "os": os_val or "Windows 11 Pro",
                    "cpu": "Intel Core i5-12400",
                    "vga": "Intel UHD Graphics 730",
                    "ram": "16GB DDR4",
                    "hdd_ssd": "SSD NVMe 512GB",
                    "mainboard": "ASUS Prime H610M",
                    "monitor": '24" FHD',
                    "keyboard": "Logitech K120",
                    "mouse": "Logitech B100",
                    "kepemilikan": "XML",
                    "tanggal_masuk_gudang": "2025-03-10",
                    "tanggal_keluar_gudang": "2025-03-12",
                },
            )
            session.add(pc_asset)
            session.flush()
            all_assets.append(pc_asset)
            assets_by_name[pc_asset.nama_aset.strip().lower()] = pc_asset

        # Coba cocokkan perangkat fisik atau host VM ke tabel assets
        linked_asset_id: str | None = None
        linked_host_id: str | None = None

        matched_asset = assets_by_name.get(nama.strip().lower())
        if matched_asset is None and not is_vm:
            matched_asset = _match_server_asset(nama, server_assets) or next(
                (
                    a
                    for a in all_assets
                    if a.nama_aset.lower() in nama.lower() or nama.lower() in a.nama_aset.lower()
                ),
                None,
            )

        if not is_vm and matched_asset is not None:
            linked_asset_id = matched_asset.id_aset
            if not matched_asset.ip_address:
                matched_asset.ip_address = canonical_ip
                session.add(matched_asset)
        elif is_vm:
            if host_raw:
                matched_host = (
                    assets_by_name.get(host_raw.strip().lower())
                    or _match_server_asset(host_raw, server_assets)
                    or next(
                        (
                            s
                            for s in server_assets
                            if s.nama_aset.lower() in host_raw.lower()
                            or host_raw.lower() in s.nama_aset.lower()
                        ),
                        None,
                    )
                )
                if matched_host is not None:
                    linked_host_id = matched_host.id_aset
                    host_raw = matched_host.nama_aset
            else:
                host_raw = "Server Host Utama"

        existing = session.exec(
            select(IPAllocation).where(col(IPAllocation.ip_address) == canonical_ip)
        ).first()
        if existing is None:
            row = IPAllocation(
                ip_address=canonical_ip,
                ip_int=ip_int,
                subnet=_pick(r, "subnet", "netmask", default="255.255.255.0")[:45],
                gateway=_pick(r, "gateway", "gw")[:45],
                nama_perangkat=nama[:150],
                hostname=nama[:150],
                tipe="VM" if is_vm else (tipe_raw[:30] or "Fisik"),
                status="Aktif",
                lokasi=lokasi,
                id_aset=linked_asset_id,
                is_vm=is_vm,
                host_name=host_raw[:150] if is_vm else "",
                id_aset_host=linked_host_id,
                os=os_val[:80],
                port_servis=fungsi_val[:120],
                pengguna=pengguna[:100],
                keterangan=ket_norm[:500] if ket_norm else None,
            )
            session.add(row)
            session.flush()
            imported += 1

    if imported > 0:
        session.commit()
    return imported


def _classify_purchase_category(produk: str) -> str:
    """Mengklasifikasikan nama produk pembelian ke salah satu kategori resmi ITAM."""
    p = produk.lower()
    if "monitor" in p:
        return "Monitor"
    if "cctv" in p:
        return "CCTV"
    if any(k in p for k in ("switch", "router", "lan", "rj45", "converter", "media converter")):
        return "Jaringan"
    if any(k in p for k in ("ram", "ssd", "hdd", "vga", "prosesor", "fan", "psu", "thermal")):
        return "Komponen PC"
    if any(
        k in p for k in ("keyboard", "mouse", "logitech", "kabel", "tie", "organizer", "baterai")
    ):
        return "Periferal"
    if "printer" in p or "tinta" in p:
        return "Printer"
    if "synology" in p:
        return "Server"
    if "windows" in p or "lisensi" in p:
        return "Lainnya"
    return "Periferal"


def import_purchases_csv(session: Session, file_path: Path) -> int:
    """Mengimpor rekap pembelian perangkat dari rekap_pembelian.csv secara idempoten."""
    rows = _read_csv_rows(file_path)
    imported_count = 0

    existing_mons = session.exec(
        select(Asset.id_aset).where(col(Asset.id_aset).like("MON-%"))
    ).all()
    max_mon_num = 0
    for mon_id in existing_mons:
        m = re.match(r"^MON-(\d+)$", mon_id)
        if m:
            max_mon_num = max(max_mon_num, int(m.group(1)))

    for row in rows:
        no_str = row.get("NO", "").strip()
        if not no_str or not no_str.isdigit():
            continue

        no_val = int(no_str)
        kode_pembelian = f"PO-{no_val:03d}"

        # Cek idempotensi
        existing = session.exec(
            select(Purchase).where(col(Purchase.kode_pembelian) == kode_pembelian)
        ).first()
        if existing is not None:
            continue

        produk = row.get("PRODUK", "").strip()
        # Header harga di CSV kadang memiliki spasi di depan: ' HARGA' atau 'HARGA'
        raw_harga = row.get(" HARGA") or row.get("HARGA") or ""
        raw_pcs = row.get("PCS", "1")
        raw_total = row.get("Total", "")
        toko = row.get("NAMA TOKO", "").strip()
        link_marketplace = row.get("LINK MARKETPLACE", "").strip()
        dibeli_oleh = row.get("Dibeli Oleh", "").strip()
        raw_tanggal = row.get("TANGGAL", "").strip()

        harga_satuan = _parse_rupiah(raw_harga)
        jumlah = _parse_int(raw_pcs) or 1
        total_harga = _parse_rupiah(raw_total) or (harga_satuan * jumlah)
        tanggal_beli = _parse_date(raw_tanggal) or date(2025, 1, 1)

        kategori = _classify_purchase_category(produk)
        metode = "Marketplace" if link_marketplace else "Transfer"

        # Jika produk adalah Monitor di rekap_pembelian.csv, buat aset Monitor di tabel assets
        linked_asset_code: str | None = None
        if kategori == "Monitor":
            is_samsung = "samsung" in produk.lower()
            merk_mon = "Samsung" if is_samsung else ("LG" if "lg" in produk.lower() else "Lainnya")
            tipe_mon = "S24D330" if is_samsung else "24MR400-B"
            konektivitas = ["HDMI", "VGA"]
            created_mon_codes: list[str] = []
            for unit_idx in range(jumlah):
                max_mon_num += 1
                mon_code = f"MON-{max_mon_num:03d}"
                created_mon_codes.append(mon_code)
                is_backup_mon = unit_idx == (jumlah - 1) and jumlah > 1
                st_mon = "Backup" if is_backup_mon else "Digunakan"
                pemakai_mon = (
                    "Cadangan Gudang IT" if is_backup_mon else (dibeli_oleh or "Operasional Office")
                )
                mon_asset = Asset(
                    id_aset=mon_code,
                    nama_aset=f'{merk_mon} {tipe_mon} 24"',
                    kategori="Monitor",
                    merek=merk_mon,
                    model=tipe_mon,
                    lokasi="Head Office (Office Blok 14)",
                    detail_lokasi="Ruang Operasional",
                    penanggung_jawab=pemakai_mon,
                    status=st_mon,
                    kondisi="Baru",
                    tanggal_masuk=tanggal_beli,
                    ukuran_layar="24",
                    resolusi="1920x1080 (FHD)",
                    panel="IPS",
                    port_display=", ".join(konektivitas),
                    catatan=f"Dibeli dari {toko} ({kode_pembelian})",
                    extra_specs={
                        "merk": merk_mon,
                        "tipe_model": tipe_mon,
                        "ukuran_layar": "24",
                        "resolusi_layar": "1920x1080 (FHD)",
                        "konektivitas": konektivitas,
                        "kepemilikan": "XML",
                        "tanggal_masuk_gudang": tanggal_beli.isoformat(),
                        "tanggal_keluar_gudang": (
                            "" if is_backup_mon else tanggal_beli.isoformat()
                        ),
                    },
                )
                session.add(mon_asset)
            session.flush()
            if created_mon_codes:
                linked_asset_code = created_mon_codes[0]

        purchase = Purchase(
            kode_pembelian=kode_pembelian,
            nomor_invoice=f"INV-PO-{no_val:03d}",
            nama_item=produk,
            kategori=kategori,
            jenis_transaksi="Pembelian",
            vendor=toko,
            lokasi="Head Office (Office Blok 14)",
            jumlah=jumlah,
            satuan="Pcs" if jumlah > 1 else "Unit",
            harga_satuan=harga_satuan,
            total_harga=total_harga,
            tanggal_beli=tanggal_beli,
            tanggal_bayar=tanggal_beli,
            status="Lunas",
            metode_pembayaran=metode,
            is_recurring=False,
            siklus_tagihan="Sekali",
            id_aset=linked_asset_code,
            penanggung_jawab=dibeli_oleh,
            keterangan=link_marketplace[:500],
        )
        session.add(purchase)
        imported_count += 1

    if imported_count > 0:
        session.commit()
    return imported_count


def _seed_initial_operational_records(session: Session) -> None:
    """Mengisi data awal Jadwal Maintenance & Credential Manager secara idempoten bila kosong."""
    if session.exec(select(Maintenance.id)).first() is None:
        sample_maintenances = [
            Maintenance(
                kode_maintenance="MNT-001",
                id_aset="UPS-001",
                nama_aset="UPS PROLINK 1200VA (DUAL AKI)",
                kategori="UPS",
                lokasi="Head Office (Office Blok 14)",
                jenis_maintenance="Penggantian Baterai",
                prioritas="Tinggi",
                judul="Cek voltase aki & kalibrasi beban UPS Server",
                deskripsi="Cek voltase aki & kalibrasi beban UPS Server",
                tindakan="Voltase stabil 13.6V, beban normal",
                teknisi="Ridho",
                tanggal_jadwal=date(2026, 4, 15),
                status="Terjadwal",
                kondisi_setelah="Baik",
                is_recurring=True,
                siklus="Triwulan",
                catatan="Perlu pengecekan berkala 3 bulanan",
            ),
            Maintenance(
                kode_maintenance="MNT-002",
                id_aset="SRV-001",
                nama_aset="SERVER OTO H2H",
                kategori="Server",
                lokasi="Head Office (Office Blok 14)",
                jenis_maintenance="Pembersihan",
                prioritas="Normal",
                judul="Pembersihan debu heatsink & ganti thermal paste",
                deskripsi="Pembersihan debu heatsink & ganti thermal paste",
                tindakan="Suhu turun 8C, kipas normal",
                teknisi="Surya",
                tanggal_jadwal=date(2026, 4, 22),
                status="Terjadwal",
                kondisi_setelah="Baik",
                is_recurring=True,
                siklus="Bulanan",
                catatan="Rutin bulanan server transaksi utama",
            ),
            Maintenance(
                kode_maintenance="MNT-003",
                id_aset="SRV-008",
                nama_aset="SERVER VM SDP",
                kategori="Server",
                lokasi="Head Office (Office Blok 14)",
                jenis_maintenance="Preventif",
                prioritas="Tinggi",
                judul="Snapshot & verifikasi integritas backup VM Proxmox",
                deskripsi="Snapshot & verifikasi integritas backup VM Proxmox",
                tindakan="Semua image VM terverifikasi normal",
                teknisi="Ridho",
                tanggal_jadwal=date(2026, 5, 5),
                status="Terjadwal",
                kondisi_setelah="Baik",
                is_recurring=True,
                siklus="Mingguan",
                catatan="Jadwal rutin mingguan",
            ),
            Maintenance(
                kode_maintenance="MNT-004",
                id_aset="SRV-012",
                nama_aset="SERVER BACKUP REAL TIME",
                kategori="Server",
                lokasi="Head Office (Office Blok 14)",
                jenis_maintenance="Inspeksi",
                prioritas="Normal",
                judul="Uji failover sinkronisasi database real-time",
                deskripsi="Uji failover sinkronisasi database real-time",
                tindakan="Replikasi berjalan lancar tanpa lag",
                teknisi="Surya",
                tanggal_jadwal=date(2026, 3, 20),
                tanggal_selesai=date(2026, 3, 20),
                status="Selesai",
                kondisi_setelah="Baik",
                is_recurring=True,
                siklus="Bulanan",
                catatan="Replikasi berjalan lancar tanpa lag",
            ),
            Maintenance(
                kode_maintenance="MNT-005",
                id_aset="UPS-009",
                nama_aset="UPS APC 1200VA (DUAL AKI)",
                kategori="UPS",
                lokasi="Head Office (Office Blok 14)",
                jenis_maintenance="Penggantian Baterai",
                prioritas="Tinggi",
                judul="Penggantian 2 unit aki kering Yuasa 12V 7Ah",
                deskripsi="Penggantian 2 unit aki kering Yuasa 12V 7Ah",
                tindakan="Komponen diganti dengan aki baru",
                teknisi="Ridho",
                biaya=528000,
                tanggal_jadwal=date(2026, 2, 14),
                tanggal_selesai=date(2026, 2, 14),
                status="Selesai",
                kondisi_setelah="Baik",
                is_recurring=False,
                siklus="Sekali",
                catatan="Aki lama drop, sudah diganti baru",
            ),
        ]
        for m in sample_maintenances:
            session.add(m)
        session.commit()

    if session.exec(select(Credential.id)).first() is None:
        sample_credentials = [
            (
                "CRD-001",
                "SERVER OTO H2H (SQL Server)",
                "Database",
                "192.168.1.6",
                "1433",
                "192.168.1.6:1433",
                "sa",
                "OtomaxSql#2026!Prod",
                "Administrator",
                ["Administrator"],
                "Database utama transaksi Otomax H2H",
            ),
            (
                "CRD-002",
                "SERVER VM SDP (Proxmox VE)",
                "Server",
                "192.168.1.7",
                "8006",
                "https://192.168.1.7:8006",
                "root@pam",
                "PveCluster#Blok14!99",
                "Administrator",
                ["Administrator"],
                "Hypervisor induk seluruh VM Addon SDP",
            ),
            (
                "CRD-003",
                "MikroTik Core Router Blok 14",
                "MikroTik",
                "192.168.1.1",
                "8291",
                "192.168.1.1:8291 (Winbox)",
                "admin_net",
                "MktRouter#Xml2026!",
                "Administrator",
                ["Administrator"],
                "Gateway utama & manajemen bandwidth kantor",
            ),
            (
                "CRD-004",
                "Portal Supplier IRS & Ototepe",
                "Aplikasi",
                "192.168.1.48",
                "443",
                "https://panel.xmltronik.id/admin",
                "admin@xmltronik.id",
                "PanelWeb#XmlTronik88",
                "Member",
                ["Administrator", "Member"],
                "Dashboard monitoring transaksi web & API",
            ),
            (
                "CRD-005",
                "Cloudflare DNS & Domain Manager",
                "Domain / DNS",
                "",
                "443",
                "https://dash.cloudflare.com",
                "infra@xmltronik.id",
                "CfDns#MasterKey2026!",
                "Administrator",
                ["Administrator"],
                "Pengelolaan DNS publik & SSL sertifikat",
            ),
            (
                "CRD-006",
                "CCTV NVR Hikvision Kantor Blok 14",
                "CCTV",
                "192.168.1.250",
                "80",
                "http://192.168.1.250",
                "operator_cctv",
                "CctvMonitor#Blok14",
                "Member",
                ["Administrator", "Member"],
                "Akses pantau kamera keamanan ruang server & kasir",
            ),
        ]
        for (
            code,
            nama,
            jenis,
            ip_addr,
            port,
            url,
            user,
            plain_pw,
            lvl,
            roles,
            note,
        ) in sample_credentials:
            session.add(
                Credential(
                    kode_kredensial=code,
                    nama_layanan=nama,
                    jenis_kredensial=jenis,
                    lokasi="Head Office (Office Blok 14)",
                    ip_address=ip_addr,
                    port=port,
                    url_akses=url,
                    username=user,
                    password_encrypted=encrypt_secret(plain_pw),
                    secret_extra_encrypted="",
                    level_akses=lvl,
                    allowed_roles=roles,
                    status="Aktif",
                    terakhir_diubah_oleh="admin",
                    catatan=note,
                )
            )
        session.commit()


def _sync_master_categories_and_links(session: Session) -> None:
    """Memastikan tabel categories terisi dan 77 aset memiliki category_id & relasi."""
    existing_cats = list(session.exec(select(Category)).all())
    cat_map: dict[str, int] = {c.nama.lower(): c.id for c in existing_cats if c.id is not None}
    cat_map.update({c.kode.lower(): c.id for c in existing_cats if c.id is not None})

    if not cat_map:
        for grp in CATEGORY_TREE:
            parent = Category(
                parent_id=None,
                kode=grp["kode"],
                nama=grp["nama"],
                ikon=grp["ikon"],
                tracking=grp["tracking"],
                spec_schema={},
            )
            session.add(parent)
            session.flush()
            for sub in grp.get("children", []):
                child = Category(
                    parent_id=parent.id,
                    kode=sub["kode"],
                    nama=sub["nama"],
                    ikon=sub["ikon"],
                    tracking=sub["tracking"],
                    spec_schema=sub.get("spec_schema", {}),
                )
                session.add(child)
                session.flush()
                if child.id is not None:
                    cat_map[sub["nama"].lower()] = child.id
                    cat_map[sub["kode"].lower()] = child.id
        session.commit()

    all_assets = list(session.exec(select(Asset)).all())
    servers = [a for a in all_assets if a.kategori.lower() == "server"]
    pcs = [a for a in all_assets if a.kategori.lower() == "pc"]

    # Tautkan Monitor yang Digunakan ke PC (PC-003, PC-016, PC-001) bila belum punya parent_asset_id
    monitors_used = [
        a
        for a in all_assets
        if a.kategori.lower() == "monitor" and normalize_asset_status(a.status) == "Digunakan"
    ]
    preferred_pc_tags = ["PC-003", "PC-016", "PC-001"]
    pc_by_tag = {p.id_aset: p for p in pcs}

    for idx, mon in enumerate(monitors_used):
        if not mon.parent_asset_id:
            target_tag = (
                preferred_pc_tags[idx]
                if idx < len(preferred_pc_tags) and preferred_pc_tags[idx] in pc_by_tag
                else (pcs[idx].id_aset if idx < len(pcs) else None)
            )
            if target_tag:
                mon.parent_asset_id = target_tag
                mon.penanggung_jawab = f"Terpasang di {target_tag}"
                mon.pemakai_text = f"Terpasang di {target_tag}"

    for a in all_assets:
        a.asset_tag = a.id_aset
        a.nama = a.nama_aset
        a.status = normalize_asset_status(a.status)
        a.kondisi = normalize_asset_condition(a.kondisi)
        a.category_id = cat_map.get(a.kategori.lower()) or cat_map.get("ast")
        a.pemakai_text = a.penanggung_jawab
        if not a.tanggal_perolehan and a.tanggal_masuk:
            a.tanggal_perolehan = a.tanggal_masuk
        if not a.peran:
            a.peran = (
                "Server"
                if a.kategori.lower() == "server"
                else ("Backup" if a.status == "Cadangan" else "Operasional")
            )

        # Tautkan UPS ke Server melalui asset_links (Seksi 4.4 & 15.4)
        if a.kategori.lower() == "ups" and a.beban_perangkat:
            matched_srv = _match_server_asset(a.beban_perangkat, servers)
            if matched_srv:
                a.penanggung_jawab = f"Menyuplai {matched_srv.nama_aset}"
                a.pemakai_text = a.penanggung_jawab
                existing_link = session.exec(
                    select(AssetLink).where(
                        col(AssetLink.asset_id) == a.id_aset,
                        col(AssetLink.linked_asset_id) == matched_srv.id_aset,
                    )
                ).first()
                if existing_link is None:
                    session.add(
                        AssetLink(
                            asset_id=a.id_aset,
                            linked_asset_id=matched_srv.id_aset,
                            tipe="menyuplai_daya",
                        )
                    )
        session.add(a)
    session.commit()


def import_all_csv_data(
    session: Session,
    data_dir: Path | str | None = None,
    username: str = "system",
) -> dict[str, Any]:
    """Mengimpor seluruh file CSV operasional ke database secara terintegrasi dan idempoten."""
    folder = resolve_data_dir(data_dir)
    logger.info("Menjalankan impor CSV terpadu dari direktori: %s", folder)

    ups_count = import_ups_csv(session, folder / "rekap_ups_xml.csv")
    server_count = import_watt_server_csv(session, folder / "rekap_watt_server.csv")
    ip_count = import_ip_list_csv(session, folder / "ip_list_xml.csv")
    purchase_count = import_purchases_csv(session, folder / "rekap_pembelian.csv")
    _seed_initial_operational_records(session)
    _sync_master_categories_and_links(session)

    total_imported = ups_count + server_count + ip_count + purchase_count

    if total_imported > 0:
        record_audit_log(
            session,
            username=username,
            nama_pengguna="System Importer" if username == "system" else username,
            role="Administrator",
            aksi="Impor CSV",
            modul="Master Data",
            target_id="CSV-DATA",
            detail=(
                f"Berhasil mengimpor {total_imported} data dari file CSV "
                f"({ups_count} UPS, {server_count} Server, {ip_count} IP, "
                f"{purchase_count} Pembelian)"
            ),
            level_risiko="Sedang",
        )

    return {
        "success": True,
        "message": "Impor data CSV berhasil diselesaikan",
        "data": {
            "ups_imported": ups_count,
            "servers_imported": server_count,
            "ips_imported": ip_count,
            "purchases_imported": purchase_count,
            "total_imported": total_imported,
        },
    }
