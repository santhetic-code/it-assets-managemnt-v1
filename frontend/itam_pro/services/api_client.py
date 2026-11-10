"""
Klien API terpusat untuk State Reflex.
Mendukung mode USE_MOCK=true (Frontend-first) dan USE_MOCK=false (FastAPI Backend),
serta dilengkapi generator & parser Excel (.xlsx) dan PDF A4 Landscape untuk Modul IP.
"""

import asyncio
import csv
import io
import os
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import httpx

from itam_pro.config import USE_MOCK
from itam_pro.services.mock.audit_mock import query_audit_logs, record_audit_event
from itam_pro.services.mock.auth_mock import MOCK_USERS, verify_mock_login
from itam_pro.services.mock.credential_mock import (
    get_filtered_credentials,
    reveal_mock_credential,
)
from itam_pro.services.mock.dashboard_mock import get_mock_dashboard_summary
from itam_pro.services.mock.finance_mock import (
    action_jadikan_aset,
    action_pay_bill,
    query_bills,
    query_invoices,
    query_purchases,
)
from itam_pro.services.mock.ip_mock import (
    create_mock_ip_entry,
    delete_mock_ip_entry,
    find_ip_duplicate_owner,
    get_mock_ip_map,
    get_vms_on_host,
    has_kendala,
    is_ip_in_registered_subnet,
    is_valid_ipv4,
    query_mock_ip_entries,
    update_mock_ip_entry,
)
from itam_pro.services.mock.maintenance_mock import (
    action_buat_jadwal_massal,
    action_tandai_selesai,
    query_maintenance_logs,
    query_maintenance_plans,
)
from itam_pro.services.mock.seed import (
    create_mock_assets,
    delete_mock_asset,
    find_sn_duplicate,
    get_mock_category_counts,
    peek_next_asset_id,
    query_mock_assets,
    update_mock_asset,
)
from itam_pro.services.power_service import (
    query_server_power,
    remove_server_power_entry,
    save_server_power_entry,
)

BACKEND_URL: str = os.getenv("BACKEND_INTERNAL_URL", "http://backend:8001")


class AuthenticationError(Exception):
    """Exception khusus ketika autentikasi gagal."""


class ServiceUnavailableError(Exception):
    """Exception khusus ketika layanan backend tidak dapat dihubungi."""


def _col_letter(col_idx: int) -> str:
    """Konversi indeks kolom 1-based ke huruf kolom Excel (1 -> A, 9 -> I)."""
    result = ""
    while col_idx > 0:
        col_idx, rem = divmod(col_idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def _build_openxml_xlsx(
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[int],
    *,
    is_template: bool = False,
) -> bytes:
    """
    Generator OpenXML (.xlsx) murni (tanpa ketergantungan paket eksternal):
    - Header tebal latar Navy teks putih
    - Freeze header baris pertama (A2)
    - AutoFilter & Auto-Width kolom
    - Baris selang-seling warna putih dan abu terang
    - Kolom IP berformat teks (@)
    - Dropdown DataValidation untuk Jenis ("Fisik,VM") & Status ("Aktif,Nonaktif")
    """
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="IP_Server_VM" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
</Relationships>"""

    # Style indices:
    # 0 = Default, 1 = Header Navy Bold White
    # 2 = Even Row White Text (@), 3 = Odd Row Zebra (#F8FAFC) Text (@)
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="10"/><color rgb="FF0F172A"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
  </fonts>
  <fills count="4">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid">
      <fgColor rgb="FF0F172A"/><bgColor indexed="64"/>
    </patternFill></fill>
    <fill><patternFill patternType="solid">
      <fgColor rgb="FFF8FAFC"/><bgColor indexed="64"/>
    </patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFE2E8F0"/></left>
      <right style="thin"><color rgb="FFE2E8F0"/></right>
      <top style="thin"><color rgb="FFE2E8F0"/></top>
      <bottom style="thin"><color rgb="FFE2E8F0"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="4">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="49" fontId="1" fillId="2" borderId="1" xfId="0"
      applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="49" fontId="0" fillId="0" borderId="1" xfId="0"
      applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="center" wrapText="1"/>
    </xf>
    <xf numFmtId="49" fontId="0" fillId="3" borderId="1" xfId="0"
      applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="center" wrapText="1"/>
    </xf>
  </cellXfs>
</styleSheet>"""

    cols_xml_parts = []
    for idx, w in enumerate(col_widths, start=1):
        cols_xml_parts.append(f'<col min="{idx}" max="{idx}" width="{w}" customWidth="1"/>')
    cols_xml = "<cols>" + "".join(cols_xml_parts) + "</cols>"

    sheet_rows_xml = []
    # Baris 1: Header
    h_cells = []
    for c_idx, h_text in enumerate(headers, start=1):
        ref = f"{_col_letter(c_idx)}1"
        h_cells.append(f'<c r="{ref}" t="inlineStr" s="1"><is><t>{xml_escape(h_text)}</t></is></c>')
    sheet_rows_xml.append(f'<row r="1" ht="26" customHeight="1">{"".join(h_cells)}</row>')

    # Baris Data
    for r_idx, row_vals in enumerate(rows, start=2):
        style_id = "2" if (r_idx % 2 == 0) else "3"
        d_cells = []
        for c_idx, val in enumerate(row_vals, start=1):
            ref = f"{_col_letter(c_idx)}{r_idx}"
            d_cells.append(
                f'<c r="{ref}" t="inlineStr" s="{style_id}"><is><t>{xml_escape(val)}</t></is></c>'
            )
        sheet_rows_xml.append(f'<row r="{r_idx}" ht="21" customHeight="1">{"".join(d_cells)}</row>')

    last_col = _col_letter(len(headers))
    last_row = max(2, len(rows) + 1)
    autofilter_xml = f'<autoFilter ref="A1:{last_col}{last_row}"/>'

    dv_xml = ""
    if is_template:
        # Kolom C = Jenis (Fisik,VM), Kolom E = Status (Aktif,Nonaktif)
        dv_xml = """<dataValidations count="2">
  <dataValidation type="list" allowBlank="0" showInputMessage="1"
    showErrorMessage="1" sqref="C2:C500">
    <formula1>"Fisik,VM"</formula1>
  </dataValidation>
  <dataValidation type="list" allowBlank="0" showInputMessage="1"
    showErrorMessage="1" sqref="E2:E500">
    <formula1>"Aktif,Nonaktif"</formula1>
  </dataValidation>
</dataValidations>"""

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews>
    <sheetView tabSelected="1" workbookViewId="0">
      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>
    </sheetView>
  </sheetViews>
  {cols_xml}
  <sheetData>{"".join(sheet_rows_xml)}</sheetData>
  {autofilter_xml}
  {dv_xml}
</worksheet>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/styles.xml", styles_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()


def _read_xlsx_rows(file_bytes: bytes) -> list[list[str]]:
    """Baca baris-baris dari file .xlsx menggunakan zipfile + ElementTree."""
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in ss_root.findall("main:si", ns):
                texts = [t.text or "" for t in si.findall(".//main:t", ns)]
                shared_strings.append("".join(texts))

        sheet_path = "xl/worksheets/sheet1.xml"
        if sheet_path not in zf.namelist():
            sheet_candidates = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet")]
            if not sheet_candidates:
                return []
            sheet_path = sheet_candidates[0]

        ws_root = ET.fromstring(zf.read(sheet_path))
        extracted_rows: list[list[str]] = []
        for row_el in ws_root.findall(".//main:sheetData/main:row", ns):
            row_map: dict[int, str] = {}
            max_col = 0
            for c_el in row_el.findall("main:c", ns):
                ref = c_el.attrib.get("r", "")
                col_letters = "".join(ch for ch in ref if ch.isalpha())
                col_idx = 0
                for ch in col_letters:
                    col_idx = col_idx * 26 + (ord(ch.upper()) - 64)
                max_col = max(max_col, col_idx)

                c_type = c_el.attrib.get("t", "")
                val_str = ""
                if c_type == "s":
                    v_el = c_el.find("main:v", ns)
                    if v_el is not None and v_el.text and v_el.text.isdigit():
                        idx = int(v_el.text)
                        if 0 <= idx < len(shared_strings):
                            val_str = shared_strings[idx]
                elif c_type == "inlineStr":
                    t_els = c_el.findall(".//main:t", ns)
                    val_str = "".join(t.text or "" for t in t_els)
                else:
                    v_el = c_el.find("main:v", ns)
                    val_str = v_el.text if (v_el is not None and v_el.text) else ""
                if col_idx > 0:
                    row_map[col_idx] = val_str.strip()

            if max_col > 0:
                row_list = [row_map.get(i, "") for i in range(1, max(9, max_col + 1))]
                if any(x != "" for x in row_list):
                    extracted_rows.append(row_list)
        return extracted_rows


def _pdf_escape(text: str) -> str:
    """Escape karakter khusus pada literal string PDF (Latin-1)."""
    clean = (
        text.replace("●", "*")
        .replace("—", "-")
        .replace("–", "-")
        .replace("·", "-")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_a4_landscape_ip_pdf(
    rows: list[dict[str, Any]],
    export_date_label: str,
    exporter_name: str,
    selected_columns: list[str] | None = None,
) -> bytes:
    """
    Generator PDF A4 Landscape (841.89 x 595.28 pt):
    - Judul 'Daftar IP & Server (VM)', tanggal ekspor, jumlah entri,
      nama pengekspor, brand 'ITAM Pro'.
    - Header tabel latar Navy teks putih diulang di setiap halaman.
    - Baris tidak terpotong antar halaman, teks panjang otomatis membungkus (word-wrap).
    - Status berwarna lembut (Aktif hijau, Nonaktif merah).
    - Footer halaman 'Halaman X dari Y'.
    """
    page_w, page_h = 841.89, 595.28
    margin_x = 32.0
    table_w = page_w - 2 * margin_x  # 777.89 pt

    all_specs = [
        ("no", "No", 26.0, 4),
        ("ip_address", "IP Address", 82.0, 14),
        ("pengguna", "Pengguna", 112.0, 19),
        ("jenis", "Jenis", 42.0, 7),
        ("host", "Host", 72.0, 12),
        ("kategori", "Kategori", 78.0, 13),
        ("fungsi", "Fungsi", 122.0, 21),
        ("os", "OS", 96.0, 16),
        ("status", "Status", 54.0, 9),
        ("keterangan", "Keterangan", 93.89, 16),
    ]
    if selected_columns:
        allowed = {c.strip().lower() for c in selected_columns} | {"no"}
        specs = [s for s in all_specs if s[0] in allowed] or all_specs
    else:
        specs = all_specs

    scale = table_w / (sum(s[2] for s in specs) or table_w)
    col_defs = [(s[1], s[2] * scale, max(4, int(s[3] * scale))) for s in specs]
    col_keys = [s[0] for s in specs]
    status_col_idx = col_keys.index("status") if "status" in col_keys else -1

    prepared_rows: list[tuple[list[list[str]], float, str]] = []
    for idx, r in enumerate(rows, start=1):
        ket_val = str(r.get("keterangan") or "—").strip() or "—"
        host_val = str(r.get("host_display") or r.get("host_label") or "—").strip()
        pengguna_val = str(r.get("pengguna") or r.get("nama") or "—")
        row_map = {
            "no": str(idx),
            "ip_address": str(r.get("ip_address", "—")),
            "pengguna": pengguna_val,
            "jenis": str(r.get("jenis", "Fisik")),
            "host": host_val,
            "kategori": str(r.get("kategori", "IP Operasional")),
            "fungsi": str(r.get("fungsi", "—")),
            "os": str(r.get("os", "—")),
            "status": str(r.get("status", "Aktif")),
            "keterangan": ket_val,
        }
        cells_raw = [row_map[k] for k in col_keys]
        wrapped_cells: list[list[str]] = []
        max_lines = 1
        for c_i, raw_txt in enumerate(cells_raw):
            max_chars = col_defs[c_i][2]
            lines = textwrap.wrap(raw_txt, width=max_chars) or ["—"]
            wrapped_cells.append(lines[:3])
            max_lines = max(max_lines, len(lines[:3]))
        row_h = max(24.0, 10.0 + max_lines * 11.5)
        prepared_rows.append((wrapped_cells, row_h, str(r.get("status", "Aktif"))))

    # Bagi baris ke dalam halaman agar tidak ada baris yang terpotong
    pages_data: list[list[tuple[list[list[str]], float, str, int]]] = []
    current_page: list[tuple[list[list[str]], float, str, int]] = []
    y_cursor = page_h - 112.0  # posisi Y setelah header halaman + header tabel
    bottom_limit = 48.0

    for row_idx, (w_cells, r_h, st_val) in enumerate(prepared_rows):
        if y_cursor - r_h < bottom_limit and current_page:
            pages_data.append(current_page)
            current_page = []
            y_cursor = page_h - 112.0
        current_page.append((w_cells, r_h, st_val, row_idx))
        y_cursor -= r_h

    if current_page or not pages_data:
        pages_data.append(current_page)

    total_pages = len(pages_data)
    total_entries = len(rows)

    page_streams: list[bytes] = []
    for p_num, p_rows in enumerate(pages_data, start=1):
        cmds: list[str] = []
        # Header Dokumen
        cmds.append("0.059 0.090 0.165 rg")
        cmds.append(
            f"BT /F2 16 Tf {margin_x:.2f} {page_h - 42:.2f} Td (Daftar IP & Server \\(VM\\)) Tj ET"
        )

        sub_str = f"Diekspor {export_date_label} - {total_entries} entri - {exporter_name}"
        cmds.append("0.392 0.455 0.545 rg")
        cmds.append(
            f"BT /F1 9.5 Tf {margin_x:.2f} {page_h - 58:.2f} Td ({_pdf_escape(sub_str)}) Tj ET"
        )

        # Brand kanan atas 'ITAM Pro'
        cmds.append("0.114 0.306 0.847 rg")
        cmds.append(
            f"BT /F2 11 Tf {page_w - margin_x - 52:.2f} {page_h - 44:.2f} Td (ITAM Pro) Tj ET"
        )

        # Header Tabel Navy (#0F172A)
        th_top = page_h - 74.0
        th_h = 26.0
        cmds.append("0.059 0.090 0.165 rg")
        cmds.append(f"{margin_x:.2f} {th_top - th_h:.2f} {table_w:.2f} {th_h:.2f} re f")

        cmds.append("1 1 1 rg")
        x_pos = margin_x
        for c_title, c_w, _ in col_defs:
            cmds.append(
                f"BT /F2 8.5 Tf {x_pos + 6:.2f} {th_top - 16.5:.2f} Td "
                f"({_pdf_escape(c_title)}) Tj ET"
            )
            x_pos += c_w

        # Baris Tabel
        y_top = th_top - th_h
        for w_cells, r_h, st_val, r_global_idx in p_rows:
            y_bot = y_top - r_h
            # Zebra background
            if r_global_idx % 2 == 1:
                cmds.append("0.973 0.980 0.988 rg")
                cmds.append(f"{margin_x:.2f} {y_bot:.2f} {table_w:.2f} {r_h:.2f} re f")

            # Garis border bawah tipis
            cmds.append("0.886 0.910 0.941 RG 0.5 w")
            cmds.append(f"{margin_x:.2f} {y_bot:.2f} m {margin_x + table_w:.2f} {y_bot:.2f} l S")

            x_pos = margin_x
            for c_i, lines in enumerate(w_cells):
                c_w = col_defs[c_i][1]
                if c_i == status_col_idx:
                    # Kolom Status dengan badge warna lembut
                    is_aktif = st_val.lower() == "aktif"
                    if is_aktif:
                        cmds.append("0.863 0.988 0.906 rg")
                    else:
                        cmds.append("0.996 0.886 0.886 rg")
                    cmds.append(f"{x_pos + 4:.2f} {y_top - 18:.2f} 44 13 re f")
                    if is_aktif:
                        cmds.append("0.082 0.502 0.239 rg")
                    else:
                        cmds.append("0.725 0.110 0.110 rg")
                    cmds.append(
                        f"BT /F2 8 Tf {x_pos + 9:.2f} {y_top - 14:.2f} Td "
                        f"({_pdf_escape(lines[0])}) Tj ET"
                    )
                else:
                    cmds.append("0.059 0.090 0.165 rg")
                    font_ref = "/F2" if c_i in (1, 2) else "/F1"
                    for l_idx, line_str in enumerate(lines):
                        line_y = y_top - 13.0 - (l_idx * 10.5)
                        cmds.append(
                            f"BT {font_ref} 8.2 Tf {x_pos + 6:.2f} {line_y:.2f} Td "
                            f"({_pdf_escape(line_str)}) Tj ET"
                        )
                x_pos += c_w
            y_top = y_bot

        # Footer Halaman
        cmds.append("0.392 0.455 0.545 rg")
        cmds.append(
            f"BT /F1 8.5 Tf {margin_x:.2f} 24.00 Td "
            f"(Header navy tebal, baris selang-seling, kolom diurutkan per IP) Tj ET"
        )
        page_label = f"Halaman {p_num} dari {total_pages}"
        cmds.append(
            f"BT /F1 8.5 Tf {page_w - margin_x - 75:.2f} 24.00 Td ({_pdf_escape(page_label)}) Tj ET"
        )

        page_streams.append("\n".join(cmds).encode("latin-1"))

    # Rakit objek PDF 1.4
    objects: list[bytes] = []
    # Obj 1: Catalog, Obj 2: Pages, Obj 3: Font F1 (Helvetica), Obj 4: Font F2 (Helvetica-Bold)
    page_obj_ids = [5 + i * 2 for i in range(total_pages)]
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode("latin-1"))
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    )

    for i, stream_bytes in enumerate(page_streams):
        content_obj_id = 6 + i * 2
        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w:.2f} {page_h:.2f}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_obj_id} 0 R >>"
        ).encode("latin-1")
        stream_obj = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
            + stream_bytes
            + b"\nendstream"
        )
        objects.append(page_dict)
        objects.append(stream_obj)

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for idx, obj_body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{idx} 0 obj\n".encode("latin-1"))
        out.write(obj_body)
        out.write(b"\nendobj\n")

    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
        ).encode("latin-1")
    )
    return out.getvalue()


class APIClient:
    def __init__(self) -> None:
        self.base_url = BACKEND_URL
        self.timeout = 10.0
        self.token: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Gunakan kembali koneksi HTTP (keep-alive pool) pada event loop yang aktif."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is None or self._client.is_closed or self._client_loop is not current_loop:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=25,
                    max_connections=100,
                    keepalive_expiry=30.0,
                ),
            )
            self._client_loop = current_loop
        return self._client

    def set_token(self, token: str | None) -> None:
        """Simpan token sesi JWT untuk otentikasi otomatis request berikutnya."""
        self.token = token

    def clear_token(self) -> None:
        """Hapus token sesi saat logout."""
        self.token = None

    async def request(
        self,
        method: str,
        endpoint: str,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        headers = {"Accept": "application/json"}
        effective_token = token or self.token
        if effective_token:
            headers["Authorization"] = f"Bearer {effective_token}"

        client = self._get_client()
        try:
            response = await client.request(
                method=method,
                url=endpoint,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail_msg = ""
            try:
                err_json = exc.response.json()
                if isinstance(err_json, dict) and "detail" in err_json:
                    detail_msg = str(err_json["detail"])
            except Exception:
                pass
            if detail_msg:
                raise Exception(detail_msg) from exc
            raise exc
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
            raise ServiceUnavailableError(
                f"Tidak dapat terhubung ke server backend ({self.base_url}). "
                "Pastikan backend aktif atau ubah USE_MOCK=true di file .env."
            ) from exc
        return response.json()

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> dict[str, Any]:
        """Autentikasi pengguna ke Mock Service atau Backend FastAPI."""
        if USE_MOCK:
            result = verify_mock_login(username, password)
            if not result:
                raise AuthenticationError("Username atau password salah")
            return result

        try:
            response = await self.request(
                method="POST",
                endpoint="/api/v1/auth/login",
                json_data={
                    "username": username,
                    "password": password,
                    "remember_me": remember_me,
                },
            )
            return response  # type: ignore[return-value]
        except ServiceUnavailableError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AuthenticationError("Username atau password salah") from exc
            if exc.response.status_code == 403:
                raise AuthenticationError("Akun pengguna tidak aktif") from exc
            if exc.response.status_code == 429:
                raise AuthenticationError(
                    "Terlalu banyak percobaan login gagal. Coba lagi dalam beberapa saat."
                ) from exc
            raise AuthenticationError(
                f"Login gagal (kode HTTP {exc.response.status_code})"
            ) from exc
        except httpx.RequestError as exc:
            raise ServiceUnavailableError(
                f"Gagal terhubung ke layanan backend ({self.base_url}): {exc}"
            ) from exc

    async def get_dashboard_summary(self, token: str | None = None) -> dict[str, Any]:
        """Ambil ringkasan data Dashboard dari Mock Service atau Backend FastAPI."""
        if USE_MOCK:
            return get_mock_dashboard_summary()

        response = await self.request(
            method="GET",
            endpoint="/api/v1/dashboard/summary",
            token=token,
        )
        return response  # type: ignore[return-value]

    async def get_assets(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar aset dengan filter & paginasi untuk Semua Aset atau /assets/c/[slug]."""
        if USE_MOCK:
            return query_mock_assets(filters=filters, page=page, page_size=page_size)

        clean_filters = dict(filters)
        attr_filters = clean_filters.pop("attr_filters", None)
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **{
                k: v
                for k, v in clean_filters.items()
                if v is not None and str(v).strip() != ""
            },
        }
        if isinstance(attr_filters, dict):
            for k, v in attr_filters.items():
                if v and str(v).strip() not in ("", "Semua"):
                    params[f"attr_{k}"] = v

        try:
            response = await self.request(
                method="GET",
                endpoint="/api/v1/assets",
                token=token,
                params=params,
            )
            return response  # type: ignore[return-value]
        except ServiceUnavailableError:
            return query_mock_assets(filters=filters, page=page, page_size=page_size)

    async def create_assets(
        self,
        payload: dict[str, Any],
        duplicate_count: int = 1,
        token: str | None = None,
    ) -> list[dict[str, Any]]:
        """Tambah 1 atau N unit aset fisik baru beserta attributes-nya."""
        if USE_MOCK:
            return create_mock_assets(payload=payload, count=duplicate_count)

        if duplicate_count > 1:
            response = await self.request(
                method="POST",
                endpoint="/api/v1/assets/bulk",
                token=token,
                json_data={"asset": payload, "duplicate_count": duplicate_count},
            )
            if isinstance(response, dict) and "items" in response:
                return list(response["items"])
            return [response] if isinstance(response, dict) else []

        response = await self.request(
            method="POST",
            endpoint="/api/v1/assets",
            token=token,
            json_data=payload,
        )
        return [response] if isinstance(response, dict) else list(response)

    async def update_asset(
        self,
        asset_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any] | None:
        """Perbarui satu aset beserta attributes-nya."""
        if USE_MOCK:
            return update_mock_asset(asset_id=asset_id, payload=payload)

        response = await self.request(
            method="PUT",
            endpoint=f"/api/v1/assets/{asset_id}",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def delete_asset(
        self,
        asset_id: str,
        token: str | None = None,
    ) -> bool:
        """Hapus satu aset."""
        if USE_MOCK:
            return delete_mock_asset(asset_id=asset_id)

        await self.request(
            method="DELETE",
            endpoint=f"/api/v1/assets/{asset_id}",
            token=token,
        )
        return True

    async def get_asset_full_detail(
        self,
        asset_id: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil detail lengkap satu aset beserta relasi lintas modul untuk /assets/[id]."""
        clean_id = asset_id.strip().upper()
        if not USE_MOCK:
            try:
                res = await self.request(
                    method="GET",
                    endpoint=f"/api/v1/assets/{clean_id}/full-detail",
                    token=token,
                )
                if isinstance(res, dict):
                    return res
            except ServiceUnavailableError:
                pass

        from itam_pro.services.mock.seed import MOCK_ASSETS, flatten_asset_row

        raw_item = next(
            (a for a in MOCK_ASSETS if str(a.get("id_aset", "")).upper() == clean_id),
            None,
        )
        if not raw_item:
            return {}
        flat = flatten_asset_row(raw_item)
        child_mons = [
            {
                "id_aset": str(m["id_aset"]),
                "nama_aset": str(m["nama_aset"]),
                "summary": f"{m['id_aset']} — {m['nama_aset']} — 24\" FHD",
            }
            for m in MOCK_ASSETS
            if m.get("parent_asset_id") == clean_id and m.get("kategori") == "Monitor"
        ]
        parent_id = raw_item.get("parent_asset_id")
        parent_obj = (
            next((a for a in MOCK_ASSETS if a.get("id_aset") == parent_id), None)
            if parent_id
            else None
        )
        power_links = [
            {
                "id_aset": str(u["id_aset"]),
                "nama_aset": str(u["nama_aset"]),
                "kategori": str(u["kategori"]),
                "summary": f"{u['id_aset']} — {u['nama_aset']}",
            }
            for u in MOCK_ASSETS
            if (
                u.get("kategori") == "UPS"
                and str(raw_item.get("nama_aset", "")).upper()
                in str(u.get("digunakan_oleh", "")).upper()
                and raw_item.get("kategori") == "Server"
            )
        ]
        ips = [
            {
                "id": 1,
                "ip_address": "192.168.1.31" if clean_id == "PC-003" else "192.168.1.10",
                "nama_perangkat": str(flat.get("nama_aset", "")),
                "is_vm": False,
                "status": "Aktif",
                "summary": (
                    "192.168.1.31 — Aktif" if clean_id == "PC-003" else "192.168.1.10 — Aktif"
                ),
            }
        ]
        creds = (
            [
                {
                    "kode_kredensial": "CRD-001",
                    "nama": str(flat.get("nama_aset")),
                    "jenis": "PC",
                    "username": "user",
                },
                {
                    "kode_kredensial": "CRD-002",
                    "nama": f"Radmin {flat.get('nama_aset')}",
                    "jenis": "Radmin",
                    "username": "admin",
                },
            ]
            if flat.get("kategori") in ("PC", "Server")
            else []
        )
        movements = list(
            raw_item.get("movements")
            or [
                {
                    "id": 1,
                    "jenis": "serah_terima",
                    "dari": "Gudang IT",
                    "ke": f"{flat.get('digunakan_oleh', '—')} ({flat.get('lokasi', '—')})",
                    "alasan": "Penempatan awal",
                    "catatan": str(flat.get("catatan", "")),
                    "tanggal": str(flat.get("tanggal_masuk_gudang") or "2025-03-10"),
                    "oleh": "admin",
                }
            ]
        )

        comp_installed = [
            {
                "id_aset": str(c.get("id_aset")),
                "komponen": str(c.get("kategori")),
                "spesifikasi": (
                    f"{c.get('kategori')} {c.get('attributes', {}).get('tipe', '')} "
                    f"{c.get('attributes', {}).get('kapasitas_gb', '')} GB"
                ).strip(),
                "slot": str(c.get("attributes", {}).get("slot", "—")),
                "dipasang_sejak": str(c.get("attributes", {}).get("dipasang_sejak", "—")),
                "parent_asset_id": str(c.get("parent_asset_id", "")),
                "data_status": str(c.get("attributes", {}).get("data_status", "Kosong")),
            }
            for c in MOCK_ASSETS
            if str(c.get("parent_asset_id", "")).upper() == clean_id
            and str(c.get("kategori", "")).lower() in ("ram", "ssd", "hdd", "vga", "psu")
        ]
        comp_spares = [
            {
                "id_aset": str(c.get("id_aset")),
                "komponen": str(c.get("kategori")),
                "spesifikasi": (
                    f"{c.get('kategori')} {c.get('attributes', {}).get('tipe', '')} "
                    f"{c.get('attributes', {}).get('kapasitas_gb', '')} GB"
                ).strip(),
                "slot": str(c.get("attributes", {}).get("slot", "—")),
                "dipasang_sejak": str(c.get("attributes", {}).get("dipasang_sejak", "—")),
                "parent_asset_id": "",
                "data_status": str(c.get("attributes", {}).get("data_status", "Kosong")),
            }
            for c in MOCK_ASSETS
            if not c.get("parent_asset_id")
            and str(c.get("lokasi", "")).lower() == "gudang"
            and str(c.get("kategori", "")).lower() in ("ram", "ssd", "hdd", "vga", "psu")
        ]
        pc_targets = [
            f"{c.get('id_aset')} — {c.get('nama_aset')}"
            for c in MOCK_ASSETS
            if str(c.get("id_aset", "")).upper() != clean_id
            and str(c.get("kategori", "")).lower() in ("pc", "laptop", "server")
        ]
        total_ram_gb = sum(
            int(c.get("attributes", {}).get("kapasitas_gb") or 0)
            for c in MOCK_ASSETS
            if str(c.get("parent_asset_id", "")).upper() == clean_id
            and str(c.get("kategori", "")).lower() == "ram"
        )
        ram_mods = sum(
            1
            for c in MOCK_ASSETS
            if str(c.get("parent_asset_id", "")).upper() == clean_id
            and str(c.get("kategori", "")).lower() == "ram"
        )
        total_storage_gb = sum(
            int(c.get("attributes", {}).get("kapasitas_gb") or 0)
            for c in MOCK_ASSETS
            if str(c.get("parent_asset_id", "")).upper() == clean_id
            and str(c.get("kategori", "")).lower() in ("ssd", "hdd", "ssd/hdd")
        )
        storage_disks = sum(
            1
            for c in MOCK_ASSETS
            if str(c.get("parent_asset_id", "")).upper() == clean_id
            and str(c.get("kategori", "")).lower() in ("ssd", "hdd", "ssd/hdd")
        )
        is_comp_tracked = len(comp_installed) > 0
        ram_chip = (
            f"RAM total {total_ram_gb} GB · {ram_mods} modul"
            if total_ram_gb > 0
            else f"RAM {flat.get('ram') or '—'}"
        )
        storage_chip = (
            f"Storage total {total_storage_gb} GB · {storage_disks} disk"
            if total_storage_gb > 0
            else f"Storage {flat.get('storage') or '—'}"
        )

        return {
            "asset": flat,
            "relations": {
                "monitors": child_mons,
                "parent_asset": (
                    {
                        "id_aset": str(parent_obj["id_aset"]),
                        "nama_aset": str(parent_obj["nama_aset"]),
                        "kategori": str(parent_obj["kategori"]),
                    }
                    if parent_obj
                    else None
                ),
                "power_links": power_links,
                "ips": ips,
                "credentials": creds,
                "credentials_summary": (
                    "2 entri (PC, Radmin) · sesuai hak akses Anda"
                    if creds
                    else "Belum ada kredensial tertaut"
                ),
                "purchase": (
                    {
                        "kode_pembelian": "PO-001",
                        "nomor_invoice": "INV-PO-001",
                        "nama_item": str(flat.get("nama_aset", "")),
                        "vendor": "Toko Resmi IT",
                        "harga_satuan": 6500000,
                        "tanggal_beli": str(flat.get("tanggal_masuk_gudang") or "2025-03-10"),
                    }
                    if raw_item.get("purchase_item_id")
                    else None
                ),
                "maintenances": [],
            },
            "movements": movements,
            "components": {
                "is_tracked": is_comp_tracked,
                "ram_summary_chip": ram_chip,
                "storage_summary_chip": storage_chip,
                "installed": comp_installed,
                "spares": comp_spares,
                "pc_targets": pc_targets,
            },
        }

    async def handover_asset(
        self,
        asset_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Simpan serah terima atau pindah lokasi aset ke asset_movements."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint=f"/api/v1/assets/{asset_id.strip()}/handover",
                token=token,
                json_data=payload,
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import MOCK_ASSETS

        for item in MOCK_ASSETS:
            if str(item.get("id_aset", "")).upper() == asset_id.strip().upper():
                old_u = item.get("digunakan_oleh") or "—"
                old_l = item.get("lokasi") or "—"
                if payload.get("pengguna_baru"):
                    item["digunakan_oleh"] = payload["pengguna_baru"]
                if payload.get("lokasi_baru"):
                    item["lokasi"] = payload["lokasi_baru"]
                if payload.get("status_baru"):
                    item["status"] = payload["status_baru"]
                mvs = list(item.get("movements") or [])
                mvs.insert(
                    0,
                    {
                        "id": len(mvs) + 1,
                        "jenis": payload.get("jenis", "serah_terima"),
                        "dari": f"{old_u} ({old_l})",
                        "ke": f"{item.get('digunakan_oleh')} ({item.get('lokasi')})",
                        "alasan": payload.get("alasan", "Serah terima"),
                        "catatan": payload.get("catatan", ""),
                        "tanggal": payload.get("tanggal", "2026-11-09"),
                        "oleh": "admin",
                    },
                )
                item["movements"] = mvs
                break
        return {"status": "ok"}

    async def link_asset_relation(
        self,
        asset_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Tautkan atau lepas relasi antar aset (Monitor <-> PC atau UPS <-> Server)."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint=f"/api/v1/assets/{asset_id.strip()}/links",
                token=token,
                json_data=payload,
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import MOCK_ASSETS

        src_id = asset_id.strip().upper()
        tgt_id = str(payload.get("target_asset_id") or "").strip().upper()
        act = str(payload.get("action") or "link").lower()
        for item in MOCK_ASSETS:
            if (
                str(item.get("id_aset", "")).upper() == tgt_id
                and item.get("kategori") == "Monitor"
            ):
                item["parent_asset_id"] = None if act == "unlink" else src_id
                item["digunakan_oleh"] = "—" if act == "unlink" else f"Terpasang di {src_id}"
                item["status"] = "Cadangan" if act == "unlink" else "Digunakan"
        return {"status": "ok"}

    async def preview_component_impact(
        self,
        component_id: str,
        action: str = "pindah",
        target_pc_id: str = "",
        token: str | None = None,
    ) -> dict[str, Any]:
        """Hitung dampak pemindahan/pelepasan komponen pada PC asal & PC tujuan (Artboard 12)."""
        if not USE_MOCK:
            try:
                res = await self.request(
                    method="GET",
                    endpoint=f"/api/v1/assets/{component_id.strip()}/components/preview-impact",
                    token=token,
                    params={"action": action, "target_pc_id": target_pc_id},
                )
                if isinstance(res, dict):
                    return res
            except ServiceUnavailableError:
                pass

        from itam_pro.services.mock.seed import MOCK_ASSETS

        comp = next((a for a in MOCK_ASSETS if a.get("id_aset") == component_id), None)
        if not comp:
            return {"impacts": [], "warning": "", "needs_wipe_confirmation": False}
        attrs = comp.get("attributes") or {}
        cap = int(attrs.get("kapasitas_gb") or 8)
        is_ram = comp.get("kategori") == "RAM"
        metric = "RAM" if is_ram else "Storage"
        src_id = comp.get("parent_asset_id") or "PC-003"
        tgt_clean = target_pc_id.split("—")[0].strip() if target_pc_id else "PC-016"
        impacts = []
        if comp.get("parent_asset_id"):
            before_s = 16 if is_ram else 512
            impacts.append(
                {
                    "label": f"{src_id} {metric}",
                    "change": f"{before_s} GB -> {max(0, before_s - cap)} GB",
                }
            )
        if action in ("pindah", "pasang") and tgt_clean:
            before_t = 8 if is_ram else 256
            impacts.append(
                {
                    "label": f"{tgt_clean} {metric}",
                    "change": f"{before_t} GB -> {before_t + cap} GB",
                }
            )
        return {
            "impacts": impacts,
            "warning": "",
            "needs_wipe_confirmation": str(attrs.get("data_status", "")).lower() == "berisi data",
        }

    async def mutate_component(
        self,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Jalankan mutasi komponen (pasang, lepas, pindah, tandai_rusak) secara atomik."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint="/api/v1/assets/components/mutate",
                token=token,
                json_data=payload,
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import MOCK_ASSETS

        cid = str(payload.get("component_id") or "").strip().upper()
        act = str(payload.get("action") or "pindah").strip().lower()
        raw_tgt = str(payload.get("target_pc_id") or "").strip()
        tgt_id = raw_tgt.split("—")[0].strip().upper() if raw_tgt else ""
        comp = next((a for a in MOCK_ASSETS if str(a.get("id_aset", "")).upper() == cid), None)
        if not comp:
            return {"status": "error"}
        attrs = dict(comp.get("attributes") or {})
        if (
            comp.get("kategori") in ("SSD", "HDD")
            and attrs.get("data_status") == "Berisi data"
            and act in ("pasang", "pindah")
        ):
            if not payload.get("confirm_wipe"):
                raise Exception(
                    f"Disk {cid} berstatus 'Berisi data'. "
                    "Centang konfirmasi wipe sebelum memasang/memindahkan."
                )
            attrs["data_status"] = "Sudah di-wipe"

        if act in ("pasang", "pindah") and tgt_id:
            comp["parent_asset_id"] = tgt_id
            comp["status"] = "Digunakan"
            comp["digunakan_oleh"] = f"Terpasang di {tgt_id}"
            attrs["slot"] = payload.get("slot") or attrs.get("slot") or "DIMM 2"
            attrs["dipasang_sejak"] = "Nov 2026"
        elif act == "lepas":
            comp["parent_asset_id"] = None
            comp["status"] = "Cadangan"
            comp["lokasi"] = payload.get("lokasi") or "Gudang"
            comp["digunakan_oleh"] = "Cadangan — Gudang"
        elif act in ("rusak", "tandai_rusak"):
            comp["parent_asset_id"] = None
            comp["status"] = "Rusak"
            comp["kondisi"] = "Rusak"
            comp["digunakan_oleh"] = "Rusak — Gudang"
        comp["attributes"] = attrs
        return {"status": "ok"}

    async def run_component_wizard(
        self,
        asset_id: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Jalankan Wizard Konversi spesifikasi teks PC/Server menjadi komponen per unit."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint=f"/api/v1/assets/{asset_id.strip()}/components/convert-wizard",
                token=token,
                json_data=payload or {},
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import create_mock_assets

        p_id = asset_id.strip().upper()
        create_mock_assets(
            {
                "nama_aset": "RAM DDR4 8 GB",
                "kategori": "RAM",
                "lokasi": "Head Office",
                "status": "Digunakan",
                "digunakan_oleh": f"Terpasang di {p_id}",
                "parent_asset_id": p_id,
                "attributes": {
                    "tipe": "DDR4",
                    "kapasitas_gb": 8,
                    "slot": "DIMM 1",
                    "dipasang_sejak": "Nov 2026",
                },
            },
            count=2,
        )
        create_mock_assets(
            {
                "nama_aset": "SSD NVMe 512 GB",
                "kategori": "SSD",
                "lokasi": "Head Office",
                "status": "Digunakan",
                "digunakan_oleh": f"Terpasang di {p_id}",
                "parent_asset_id": p_id,
                "attributes": {
                    "tipe": "NVMe",
                    "kapasitas_gb": 512,
                    "slot": "M.2",
                    "dipasang_sejak": "Nov 2026",
                    "data_status": "Berisi data",
                },
            },
            count=1,
        )
        return {"status": "ok"}

    async def get_stock_opname(
        self,
        lokasi: str = "",
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil laporan Stock Opname beserta selisih hasil pindai QR."""
        if not USE_MOCK:
            try:
                res = await self.request(
                    method="GET",
                    endpoint="/api/v1/assets/stock-opname",
                    token=token,
                    params={"lokasi": lokasi} if lokasi else None,
                )
                if isinstance(res, dict):
                    return res
            except ServiceUnavailableError:
                pass

        from itam_pro.services.mock.seed import MOCK_ASSETS

        items = []
        found = 0
        missing = 0
        unscanned = 0
        for a in MOCK_ASSETS:
            st = str(a.get("opname_status") or "Belum dipindai")
            if st == "Ditemukan":
                found += 1
            elif st == "Tidak ditemukan":
                missing += 1
            else:
                unscanned += 1
            items.append(
                {
                    "id_aset": str(a.get("id_aset", "")),
                    "nama_aset": str(a.get("nama_aset", "")),
                    "kategori": str(a.get("kategori", "")),
                    "lokasi": str(a.get("lokasi", "")),
                    "pengguna": str(a.get("digunakan_oleh") or "—"),
                    "opname_status": st,
                    "scanned_at": str(a.get("scanned_at") or "—"),
                    "catatan": str(a.get("opname_note") or ""),
                }
            )
        return {
            "summary": {
                "total_terdaftar": len(MOCK_ASSETS),
                "ditemukan": found,
                "tidak_ditemukan": missing,
                "belum_dipindai": unscanned,
                "selisih": missing + unscanned,
            },
            "items": items,
        }

    async def scan_stock_opname_qr(
        self,
        qr_code: str,
        status: str = "Ditemukan",
        catatan: str = "",
        token: str | None = None,
    ) -> dict[str, Any]:
        """Pindai QR aset untuk menandai Ditemukan atau Tidak ditemukan."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint="/api/v1/assets/stock-opname/scan",
                token=token,
                json_data={"qr_code": qr_code, "status": status, "catatan": catatan},
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import MOCK_ASSETS

        clean = qr_code.strip()
        if "/assets/" in clean:
            clean = clean.split("/assets/", 1)[1].split("?")[0].strip("/")
        clean = clean.upper()
        target = next(
            (a for a in MOCK_ASSETS if str(a.get("id_aset", "")).upper() == clean),
            None,
        )
        if not target:
            raise Exception(f"Aset '{clean}' tidak ditemukan di daftar induk.")
        target["opname_status"] = status
        target["scanned_at"] = "2026-11-10"
        target["opname_note"] = catatan
        return {"status": "ok", "id_aset": clean, "opname_status": status}

    async def preview_assets_import(
        self,
        csv_text: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Validasi baris CSV untuk impor aset lama."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint="/api/v1/assets/import-preview",
                token=token,
                json_data={"csv_text": csv_text},
            )
            return res if isinstance(res, dict) else {}

        lines = [ln.strip() for ln in csv_text.splitlines() if ln.strip()]
        if len(lines) <= 1:
            return {
                "valid_count": 0,
                "error_count": 1,
                "valid_rows": [],
                "errors": [{"row": 1, "nama": "—", "reason": "Data CSV kosong"}],
            }
        valid_rows = []
        errors = []
        delim = ";" if ";" in lines[0] else ","
        for idx, row in enumerate(csv.reader(lines[1:], delimiter=delim), start=2):
            padded = [*row, "", "", "", "", "", "", ""][:7]
            nama_v, kat_v, user_v, lok_v, st_v, kd_v, sn_v = [x.strip() for x in padded]
            if not nama_v or not kat_v:
                errors.append(
                    {"row": idx, "nama": nama_v or "—", "reason": "Nama dan Kategori wajib diisi"}
                )
                continue
            valid_rows.append(
                {
                    "row": idx,
                    "nama_aset": nama_v,
                    "kategori": kat_v,
                    "penanggung_jawab": user_v or "Operasional",
                    "lokasi": lok_v or "Head Office",
                    "status": st_v or "Digunakan",
                    "kondisi": kd_v or "Baik",
                    "serial_number": sn_v,
                }
            )
        return {
            "valid_count": len(valid_rows),
            "error_count": len(errors),
            "valid_rows": valid_rows,
            "errors": errors,
        }

    async def commit_assets_import(
        self,
        valid_rows: list[dict[str, Any]],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Simpan seluruh baris valid hasil import aset lama."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint="/api/v1/assets/import-commit",
                token=token,
                json_data={"valid_rows": valid_rows},
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import create_mock_assets

        for r in valid_rows:
            create_mock_assets(
                {
                    "nama_aset": r.get("nama_aset", "Aset Impor"),
                    "kategori": r.get("kategori", "PC"),
                    "sn_pid": r.get("serial_number", ""),
                    "lokasi": r.get("lokasi", "Head Office"),
                    "status": r.get("status", "Digunakan"),
                    "kondisi": r.get("kondisi", "Baik"),
                    "digunakan_oleh": r.get("penanggung_jawab", "Operasional"),
                },
                count=1,
            )
        return {"status": "ok", "imported_count": len(valid_rows)}

    async def merge_assets(
        self,
        source_id_aset: str,
        target_id_aset: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Gabungkan aset duplikat (source_id_aset) ke aset utama (target_id_aset)."""
        if not USE_MOCK:
            res = await self.request(
                method="POST",
                endpoint="/api/v1/assets/merge",
                token=token,
                json_data={
                    "source_id_aset": source_id_aset,
                    "target_id_aset": target_id_aset,
                },
            )
            return res if isinstance(res, dict) else {}

        from itam_pro.services.mock.seed import MOCK_ASSETS, delete_mock_asset

        src = source_id_aset.strip().upper()
        tgt = target_id_aset.strip().upper()
        if not src or not tgt or src == tgt:
            raise Exception("Pilih ID Aset sumber dan tujuan yang berbeda.")
        for a in MOCK_ASSETS:
            if str(a.get("parent_asset_id", "")).upper() == src:
                a["parent_asset_id"] = tgt
                a["digunakan_oleh"] = f"Terpasang di {tgt}"
        delete_mock_asset(src)
        return {"status": "ok", "merged_from": src, "merged_into": tgt}

    def check_sn_duplicate_sync(self, sn_pid: str, exclude_id: str = "") -> str | None:
        return find_sn_duplicate(sn_pid=sn_pid, exclude_id=exclude_id)

    def peek_next_id_sync(self, kategori: str) -> str:
        return peek_next_asset_id(kategori=kategori)

    def get_category_counts_sync(self) -> dict[str, int]:
        return get_mock_category_counts()

    async def get_ip_entries(
        self,
        grup: str,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar entri IP & Server (VM) dengan filter, sort numerik, & KPI."""
        if self.use_mock:
            return query_mock_ip_entries(
                grup=grup,
                filters=filters,
                page=page,
                page_size=page_size,
            )

        params: dict[str, Any] = {
            "grup": grup,
            "page": page,
            "page_size": page_size,
            **filters,
        }
        try:
            response = await self.request(
                method="GET",
                endpoint="/api/v1/ip-allocations",
                token=token,
                params=params,
            )
            return response  # type: ignore[return-value]
        except ServiceUnavailableError:
            return query_mock_ip_entries(grup=grup, filters=filters, page=page, page_size=page_size)

    async def create_ip_entry(
        self,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        """Tambah satu entri IP baru."""
        if self.use_mock:
            return create_mock_ip_entry(payload=payload)

        response = await self.request(
            method="POST",
            endpoint="/api/v1/ip-allocations",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def update_ip_entry(
        self,
        entry_id: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any] | None:
        """Perbarui satu entri IP."""
        if self.use_mock:
            return update_mock_ip_entry(entry_id=entry_id, payload=payload)

        response = await self.request(
            method="PUT",
            endpoint=f"/api/v1/ip-allocations/{entry_id}",
            token=token,
            json_data=payload,
        )
        return response  # type: ignore[return-value]

    async def delete_ip_entry(
        self,
        entry_id: str,
        token: str | None = None,
    ) -> bool:
        """Hapus satu entri IP."""
        if self.use_mock:
            return delete_mock_ip_entry(entry_id=entry_id)

        await self.request(
            method="DELETE",
            endpoint=f"/api/v1/ip-allocations/{entry_id}",
            token=token,
        )
        return True

    def check_ip_duplicate_sync(self, ip_address: str, exclude_id: str = "") -> str | None:
        return find_ip_duplicate_owner(ip_address=ip_address, exclude_id=exclude_id)

    def validate_ipv4_sync(self, ip_address: str) -> bool:
        return is_valid_ipv4(ip_str=ip_address)

    def get_vms_on_host_sync(self, host_asset_id: str) -> list[dict[str, str]]:
        return get_vms_on_host(host_asset_id=host_asset_id)

    async def get_ip_map(self, subnet: str = "1") -> dict[str, Any]:
        """Ambil peta alokasi IP untuk subnet terdaftar (B4, C1)."""
        if self.use_mock:
            return get_mock_ip_map(subnet="192.168.1.0/24" if subnet == "1" else subnet)
        try:
            res = await self.request("GET", "/api/v1/ip-allocations/map", params={"subnet": subnet})
            return res if isinstance(res, dict) else {}
        except ServiceUnavailableError:
            return get_mock_ip_map(subnet="192.168.1.0/24")

    async def get_ip_print_data(
        self,
        filters: dict[str, Any],
        record_log: bool = True,
    ) -> dict[str, Any]:
        """B2: Ambil SEMUA baris terfilter (maks 5.000) untuk Cetak & catat ke Audit Log."""
        if self.use_mock:
            res = query_mock_ip_entries(grup="Semua", filters=filters, page=1, page_size=5001)
            items = res.get("items", [])
            if record_log:
                record_audit_event(
                    "Administrator IT",
                    "ip.print",
                    "IP-PRINT",
                    f"Cetak data IP ({len(items)} baris)",
                )
            return {
                "title": "Daftar IP & Server (VM)",
                "subnet": "192.168.1.0/24",
                "filter_label": filters.get("jenis") or "Semua Data",
                "total": len(items),
                "items": items,
            }
        params = {**filters, "record_log": record_log}
        res = await self.request("GET", "/api/v1/ip-allocations/print-data", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0}

    async def commit_ip_import(
        self,
        import_id: str = "",
        duplicate_mode: str = "skip",
        valid_rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """A1: Commit hasil import IP ke database (mendukung mode skip dan update)."""
        if self.use_mock:
            rows = valid_rows or []
            imported_cnt = 0
            updated_cnt = 0
            skipped_cnt = 0
            for r in rows:
                ip_addr = str(r.get("ip_address", "")).strip()
                owner = find_ip_duplicate_owner(ip_addr)
                if owner:
                    if duplicate_mode == "update":
                        from itam_pro.services.mock.ip_mock import MOCK_IP_ENTRIES

                        target_id = next(
                            (
                                str(e["id"])
                                for e in MOCK_IP_ENTRIES
                                if str(e.get("ip_address")) == ip_addr
                            ),
                            "",
                        )
                        if target_id:
                            update_mock_ip_entry(target_id, r)
                            updated_cnt += 1
                    else:
                        skipped_cnt += 1
                else:
                    create_mock_ip_entry(r)
                    imported_cnt += 1
            record_audit_event(
                "Administrator IT",
                "ip.import",
                "IP-IMPORT",
                (
                    f"Import data IP: {imported_cnt} baru, "
                    f"{updated_cnt} diperbarui, {skipped_cnt} dilewati"
                ),
            )
            return {
                "success": True,
                "imported_count": imported_cnt,
                "updated_count": updated_cnt,
                "skipped_count": skipped_cnt,
            }
        payload: dict[str, Any] = {
            "import_id": import_id,
            "duplicate_mode": duplicate_mode,
        }
        if valid_rows:
            # A1.2: Jangan kirim ip_int dari client, biarkan server menghitung ulang
            payload["valid_rows"] = [
                {k: v for k, v in row.items() if k != "ip_int"} for row in valid_rows
            ]
        res = await self.request("POST", "/api/v1/ip-allocations/import-commit", json_data=payload)
        return res if isinstance(res, dict) else {}

    async def get_ip_import_template_bytes(self) -> bytes:
        """Buat file template .xlsx standar murni teks (tanpa dropdown)."""
        headers = [
            "IP Address",
            "Pengguna",
            "Jenis",
            "Host",
            "Kategori",
            "Fungsi",
            "OS",
            "Status",
            "Keterangan",
        ]
        sample_row = [
            "192.168.1.30",
            "Nama pengguna / VM",
            "Fisik",
            "",
            "IP Operasional",
            "Fungsi utama",
            "Windows 11",
            "Aktif",
            "",
        ]
        widths = [18, 24, 12, 18, 16, 24, 16, 12, 34]
        return _build_openxml_xlsx(headers, [sample_row], widths, is_template=False)

    async def preview_ip_import_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        valid_hosts: list[str],
    ) -> dict[str, Any]:
        """B1 & B4: Validasi file .xlsx/.csv (maks 5 MB, maks 1.000 baris, validasi subnet)."""
        if len(file_bytes) > 5 * 1024 * 1024:
            return {
                "valid_rows": [],
                "errors": [
                    {
                        "row": 1,
                        "ip_address": "—",
                        "nama": "—",
                        "reason": "Ukuran file melebihi batas maksimum 5 MB",
                    }
                ],
                "total_rows": 1,
            }

        raw_rows: list[list[str]] = []
        try:
            if filename.lower().endswith(".xlsx"):
                raw_rows = _read_xlsx_rows(file_bytes)
            else:
                text_csv = file_bytes.decode("utf-8-sig", errors="replace")
                first_line = text_csv.split("\n")[0] if text_csv else ""
                delim = (
                    ";"
                    if ";" in first_line and first_line.count(";") > first_line.count(",")
                    else ","
                )
                raw_rows = [
                    [c.strip() for c in row]
                    for row in csv.reader(io.StringIO(text_csv), delimiter=delim)
                    if any(row)
                ]
        except Exception:
            return {
                "valid_rows": [],
                "errors": [
                    {
                        "row": 1,
                        "ip_address": "—",
                        "nama": "—",
                        "reason": "File rusak atau format tidak didukung (.xlsx / .csv)",
                    }
                ],
                "total_rows": 1,
            }

        if len(raw_rows) <= 1:
            return {
                "valid_rows": [],
                "errors": [
                    {"row": 1, "ip_address": "—", "nama": "—", "reason": "File tidak berisi data"}
                ],
                "total_rows": 0,
            }

        if len(raw_rows) > 1001:
            raw_rows = raw_rows[:1001]

        seen_in_file: set[str] = set()
        valid_rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        clean_hosts = {
            h.split(" ")[0].strip().upper() for h in valid_hosts if h and h not in ("-", "—")
        }

        for idx, cols in enumerate(raw_rows[1:], start=2):
            padded = [*cols, "", "", "", "", "", "", "", "", ""][:9]
            if len(cols) == 8:
                (
                    ip_val,
                    pengguna_val,
                    jenis_val,
                    host_val,
                    status_val,
                    fungsi_val,
                    os_val,
                    ket_val,
                ) = [x.strip() for x in padded[:8]]
                kat_val = "IP VM" if jenis_val.upper() == "VM" else "IP Operasional"
            else:
                (
                    ip_val,
                    pengguna_val,
                    jenis_val,
                    host_val,
                    kat_val,
                    fungsi_val,
                    os_val,
                    status_val,
                    ket_val,
                ) = [x.strip() for x in padded]

            if not any([ip_val, pengguna_val, jenis_val]):
                continue

            if not ip_val:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": "—",
                        "nama": pengguna_val or "—",
                        "reason": "IP Address kosong",
                    }
                )
                continue
            if not is_valid_ipv4(ip_val):
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val or "—",
                        "reason": "Format IPv4 tidak valid",
                    }
                )
                continue
            if not is_ip_in_registered_subnet(ip_val):
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val or "—",
                        "reason": "IP di luar subnet terdaftar (192.168.1.0/24)",
                    }
                )
                continue
            if ip_val in seen_in_file:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val or "—",
                        "reason": "IP duplikat di dalam file",
                    }
                )
                continue
            if not pengguna_val:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": "—",
                        "reason": "Pengguna / Nama Server kosong",
                    }
                )
                continue

            jenis_norm = (
                "VM"
                if jenis_val.upper() == "VM"
                else ("Fisik" if jenis_val.lower() in ("fisik", "") else "")
            )
            if not jenis_norm:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val,
                        "reason": "Jenis harus Fisik atau VM",
                    }
                )
                continue

            host_clean = host_val.split(" ")[0].strip().upper() if jenis_norm == "VM" else ""
            if jenis_norm == "VM" and not host_clean:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val,
                        "reason": "Host wajib diisi untuk VM",
                    }
                )
                continue
            if jenis_norm == "VM" and clean_hosts and host_clean not in clean_hosts:
                errors.append(
                    {
                        "row": idx,
                        "ip_address": ip_val,
                        "nama": pengguna_val,
                        "reason": f"Host '{host_clean}' tidak terdaftar",
                    }
                )
                continue

            seen_in_file.add(ip_val)
            ket_clean = ket_val if has_kendala(ket_val, fungsi_val) else ""
            valid_rows.append(
                {
                    "row": idx,
                    "ip_address": ip_val,
                    "nama": pengguna_val,
                    "nama_perangkat": pengguna_val,
                    "pengguna": pengguna_val,
                    "jenis": jenis_norm,
                    "tipe": jenis_norm,
                    "is_vm": jenis_norm == "VM",
                    "host_asset_id": host_clean,
                    "id_aset_host": host_clean or None,
                    "kategori": kat_val or ("IP VM" if jenis_norm == "VM" else "IP Operasional"),
                    "status": status_val or "Aktif",
                    "fungsi": fungsi_val,
                    "os": os_val,
                    "keterangan": ket_clean,
                }
            )
        return {
            "valid_rows": valid_rows,
            "errors": errors,
            "total_rows": len(valid_rows) + len(errors),
        }

    async def _collect_filtered_for_export(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        all_rows: list[dict[str, Any]] = []
        p_num = 1
        p_size = 100
        while True:
            res = await self.get_ip_entries(
                grup="Semua", filters=filters, page=p_num, page_size=p_size
            )
            items = res.get("items", [])
            if not items:
                break
            all_rows.extend(items)
            if len(all_rows) >= res.get("total", 0):
                break
            p_num += 1
        return all_rows

    async def generate_ip_excel_bytes(self, rows: list[dict[str, Any]]) -> bytes:
        """Hasilkan file Excel (.xlsx) untuk daftar IP & Server (VM) dengan sanitasi formula."""

        def _clean(val: Any) -> str:
            s = str(val or "")
            if s and s[0] in ("=", "+", "-", "@"):
                return "'" + s
            return s

        headers = [
            "No",
            "IP Address",
            "Pengguna",
            "Jenis",
            "Host",
            "Kategori",
            "Fungsi",
            "OS",
            "Status",
            "Keterangan",
        ]
        data_rows: list[list[str]] = []
        for i, r in enumerate(rows, 1):
            data_rows.append(
                [
                    str(i),
                    str(r.get("ip_address", "")),
                    _clean(r.get("pengguna") or r.get("nama") or ""),
                    _clean(r.get("jenis", "Fisik")),
                    _clean(r.get("host_display", "—")),
                    _clean(r.get("kategori", "IP Operasional")),
                    _clean(r.get("fungsi", "")),
                    _clean(r.get("os", "")),
                    _clean(r.get("status", "Aktif")),
                    _clean(r.get("keterangan", "")),
                ]
            )
        return _build_openxml_xlsx(
            headers,
            data_rows,
            [6, 18, 24, 10, 18, 16, 24, 18, 12, 34],
            is_template=False,
        )

    async def generate_ip_pdf_bytes(
        self,
        rows: list[dict[str, Any]],
        export_date_label: str,
        exporter_name: str,
        selected_columns: list[str] | None = None,
    ) -> bytes:
        """Hasilkan file PDF A4 Landscape untuk daftar IP & Server (VM)."""
        return _build_a4_landscape_ip_pdf(
            rows, export_date_label, exporter_name, selected_columns=selected_columns
        )

    @property
    def use_mock(self) -> bool:
        return USE_MOCK

    async def get_purchases(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_purchases(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "pembelian",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def convert_purchase_to_asset(
        self,
        id_pembelian: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if USE_MOCK:
            codes = action_jadikan_aset(
                id_pembelian,
                str(payload.get("kategori", "PC")),
                str(payload.get("kepemilikan", "XML")),
                str(payload.get("lokasi", "Head Office")),
                jumlah_daftar=int(payload.get("jumlah", 1) or 1),
                bukan_aset=bool(payload.get("bukan_aset", False)),
            )
            return {"created_assets": codes}
        res = await self.request(
            "POST",
            f"/api/v1/purchases/{id_pembelian}/convert-to-asset",
            json_data=payload,
        )
        return res if isinstance(res, dict) else {}

    async def get_invoices(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_invoices(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "invoice",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def get_bills(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_bills(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "tagihan berulang",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/purchases", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def pay_bill(self, bill_id: str, tgl_bayar: str, nominal: int) -> bool:
        if USE_MOCK:
            action_pay_bill(bill_id, tgl_bayar, nominal)
            return True
        await self.request(
            "POST",
            f"/api/v1/purchases/{bill_id}/pay",
            json_data={"tanggal_bayar": tgl_bayar, "advance_cycle": True},
        )
        return True

    async def get_maintenance_plans(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_maintenance_plans(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "jadwal",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/maintenance", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}

    async def get_maintenance_logs(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        if USE_MOCK:
            return query_maintenance_logs(filters, page, page_size)
        params: dict[str, Any] = {
            "tab": "riwayat",
            "page": page,
            "page_size": page_size,
            **filters,
        }
        res = await self.request("GET", "/api/v1/maintenance", params=params)
        return res if isinstance(res, dict) else {"items": [], "total": 0}

    async def mark_maintenance_complete(
        self,
        plan_id: str,
        tgl_selesai: str,
        hasil: str,
        catatan: str,
        pic: str,
    ) -> bool:
        if USE_MOCK:
            action_tandai_selesai(plan_id, tgl_selesai, hasil, catatan, pic)
            return True
        await self.request(
            "POST",
            f"/api/v1/maintenance/{plan_id}/complete",
            json_data={
                "tanggal_selesai": tgl_selesai,
                "hasil": hasil,
                "tindakan": hasil,
                "catatan": catatan,
                "teknisi": pic,
            },
        )
        return True

    async def create_bulk_maintenance(
        self,
        kategori: str,
        kegiatan: str,
        jenis: str,
        frekuensi: str,
        tgl_mulai: str,
        pic: str,
    ) -> bool:
        if USE_MOCK:
            action_buat_jadwal_massal(kategori, kegiatan, jenis, frekuensi, tgl_mulai, pic)
            return True
        await self.request(
            "POST",
            "/api/v1/maintenance/bulk",
            json_data={
                "kategori": kategori,
                "judul": kegiatan,
                "kegiatan": kegiatan,
                "deskripsi": kegiatan,
                "jenis": jenis,
                "frekuensi": frekuensi,
                "tgl_mulai": tgl_mulai,
                "pic": pic,
            },
        )
        return True

    async def get_credentials(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Ambil daftar kredensial berdasarkan permissions token."""

        def _mock_creds() -> dict[str, Any]:
            permissions = {
                "website": "edit",
                "detail_pc": "edit",
                "sql_server": "edit",
                "mikrotik": "edit",
                "internet_kantor": "edit",
                "email": "edit",
                "sosmed": "edit",
                "lainnya": "edit",
            }
            if token == "mock-token-member":
                permissions = {"website": "reveal", "mikrotik": "view"}
            elif token == "mock-token-viewer":
                permissions = {}
            return get_filtered_credentials(permissions, filters, page, page_size)

        if USE_MOCK:
            return _mock_creds()
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        try:
            res = await self.request("GET", "/api/v1/credentials", token=token, params=params)
            return res if isinstance(res, dict) else {"items": [], "total": 0, "tab_counts": {}}
        except ServiceUnavailableError:
            return _mock_creds()

    async def reveal_credential(
        self,
        crd_id: str,
        field_key: str,
        actor: str,
    ) -> dict[str, Any]:
        """Buka rahasia kredensial (dengan audit trail)."""
        if USE_MOCK:
            return await reveal_mock_credential(crd_id, field_key, actor)
        try:
            res = await self.request("POST", f"/api/v1/credentials/{crd_id}/reveal")
            if isinstance(res, dict):
                return {
                    **res,
                    "value": res.get("value") or res.get("password") or res.get("secret") or "",
                    "expires_in": 15,
                }
            return {"value": "", "expires_in": 0}
        except ServiceUnavailableError:
            return await reveal_mock_credential(crd_id, field_key, actor)

    async def get_server_power(
        self,
        filters: dict[str, Any],
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Ambil daftar Rekap Watt Server beserta ringkasan ESTIMASI."""
        if USE_MOCK:
            return query_server_power(filters=filters, page=page, page_size=page_size)
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            **filters,
        }
        try:
            res = await self.request("GET", "/api/v1/watt-server", params=params)
            return res if isinstance(res, dict) else {"items": [], "total": 0, "summary": {}}
        except ServiceUnavailableError:
            return query_server_power(filters=filters, page=page, page_size=page_size)

    async def save_server_power(
        self,
        payload: dict[str, Any],
        asset_id: str = "",
    ) -> dict[str, Any]:
        """Tambah atau perbarui entri Rekap Watt Server secara manual."""
        if USE_MOCK:
            return save_server_power_entry(payload=payload, asset_id=asset_id)
        if asset_id and asset_id.strip():
            res = await self.request(
                "PUT",
                f"/api/v1/watt-server/{asset_id.strip()}",
                json_data=payload,
            )
        else:
            res = await self.request("POST", "/api/v1/watt-server", json_data=payload)
        return res if isinstance(res, dict) else {}

    async def delete_server_power(self, asset_id: str) -> bool:
        """Hapus satu entri server dari Rekap Watt Server."""
        if USE_MOCK:
            return remove_server_power_entry(asset_id=asset_id)
        await self.request("DELETE", f"/api/v1/watt-server/{asset_id.strip()}")
        return True

    async def get_audit_logs(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 15,
    ) -> dict[str, Any]:
        """Ambil daftar Audit Log berhalaman dari Mock atau Backend."""
        if self.use_mock:
            return query_audit_logs(filters or {}, page=page, page_size=page_size)
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        try:
            res = await self.request("GET", "/api/v1/audit-logs", params=params)
            return res if isinstance(res, dict) else {"items": res}
        except ServiceUnavailableError:
            return query_audit_logs(filters or {}, page=page, page_size=page_size)

    async def get_users(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """Ambil daftar pengguna dari Mock atau Backend."""
        if self.use_mock:
            return {"items": list(MOCK_USERS.values()), "total": len(MOCK_USERS)}
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        try:
            res = await self.request("GET", "/api/v1/users", params=params)
            return res if isinstance(res, dict) else {"items": res}
        except ServiceUnavailableError:
            return {"items": list(MOCK_USERS.values()), "total": len(MOCK_USERS)}

    async def change_password(
        self,
        old_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Ubah password akun sendiri yang sedang login (mendukung USE_MOCK)."""

        def _mock_change_pw() -> dict[str, Any]:
            admin_user = MOCK_USERS.get("admin", {})
            expected_pw = admin_user.get("password", "password123")
            if old_password != expected_pw:
                raise Exception("Password saat ini salah.")
            if "admin" in MOCK_USERS:
                MOCK_USERS["admin"]["password"] = new_password
            return {"status": "ok"}

        if self.use_mock:
            return _mock_change_pw()
        try:
            res = await self.request(
                "POST",
                "/api/v1/users/me/password",
                json_data={"old_password": old_password, "new_password": new_password},
            )
            return res if isinstance(res, dict) else {}
        except ServiceUnavailableError:
            return _mock_change_pw()

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Buat akun pengguna baru (Administrator)."""
        res = await self.request("POST", "/api/v1/users", json_data=payload)
        return res if isinstance(res, dict) else {}

    async def update_user(
        self,
        identifier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Perbarui data pengguna (Administrator)."""
        res = await self.request(
            "PATCH",
            f"/api/v1/users/{identifier}",
            json_data=payload,
        )
        return res if isinstance(res, dict) else {}

    async def reset_user_password(
        self,
        identifier: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Reset password akun pengguna oleh Administrator."""
        res = await self.request(
            "POST",
            f"/api/v1/users/{identifier}/reset-password",
            json_data={"new_password": new_password},
        )
        return res if isinstance(res, dict) else {}

    async def delete_user(self, identifier: str) -> dict[str, Any]:
        """Hapus akun pengguna oleh Administrator."""
        res = await self.request("DELETE", f"/api/v1/users/{identifier}")
        return res if isinstance(res, dict) else {}

    async def get_dashboard(self) -> dict[str, Any]:
        """Ambil ringkasan Dashboard real-time dari Mock atau Backend."""
        if self.use_mock:
            return get_mock_dashboard_summary()
        try:
            res = await self.request("GET", "/api/v1/dashboard")
            return res if isinstance(res, dict) else {}
        except ServiceUnavailableError:
            return get_mock_dashboard_summary()


api_client = APIClient()

__all__ = [
    "BACKEND_URL",
    "USE_MOCK",
    "APIClient",
    "AuthenticationError",
    "ServiceUnavailableError",
    "api_client",
]
