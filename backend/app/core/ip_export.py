"""
Generator & Parser Dokumen Excel (.xlsx) dan PDF A4 Landscape untuk Modul IP & Server (VM).
Implementasi mandiri (pure Python murni) tanpa ketergantungan library pihak ketiga eksternal.
"""

import io
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from typing import Any
from xml.sax.saxutils import escape as xml_escape


def col_letter(col_idx: int) -> str:
    """Konversi indeks kolom 1-based ke huruf kolom Excel (1 -> A, 9 -> I)."""
    result = ""
    while col_idx > 0:
        col_idx, rem = divmod(col_idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def build_openxml_xlsx(
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[int],
    *,
    is_template: bool = False,
) -> bytes:
    """
    Generator OpenXML (.xlsx) murni:
    - Header tebal latar Navy (#0F172A) teks putih (#FFFFFF)
    - Freeze header baris pertama (A2)
    - AutoFilter & Auto-Width kolom
    - Baris selang-seling (#FFFFFF dan #F8FAFC)
    - Kolom IP berformat teks (@)
    - Dropdown DataValidation untuk Jenis ("Fisik,VM") & Status ("Aktif,Nonaktif")
    """
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
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
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
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
    # Header
    h_cells = []
    for c_idx, h_text in enumerate(headers, start=1):
        ref = f"{col_letter(c_idx)}1"
        h_cells.append(f'<c r="{ref}" t="inlineStr" s="1"><is><t>{xml_escape(h_text)}</t></is></c>')
    sheet_rows_xml.append(f'<row r="1" ht="26" customHeight="1">{"".join(h_cells)}</row>')

    # Data rows
    for r_idx, row_vals in enumerate(rows, start=2):
        style_id = "2" if (r_idx % 2 == 0) else "3"
        d_cells = []
        for c_idx, val in enumerate(row_vals, start=1):
            ref = f"{col_letter(c_idx)}{r_idx}"
            d_cells.append(
                f'<c r="{ref}" t="inlineStr" s="{style_id}"><is><t>{xml_escape(val)}</t></is></c>'
            )
        sheet_rows_xml.append(f'<row r="{r_idx}" ht="21" customHeight="1">{"".join(d_cells)}</row>')

    last_col = col_letter(len(headers))
    last_row = max(2, len(rows) + 1)
    autofilter_xml = f'<autoFilter ref="A1:{last_col}{last_row}"/>'

    dv_xml = ""
    if is_template:
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


def read_xlsx_rows(file_bytes: bytes) -> list[list[str]]:
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


def pdf_escape(text: str) -> str:
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


def build_a4_landscape_ip_pdf(
    rows: list[dict[str, Any]],
    export_date_label: str,
    exporter_name: str,
    selected_columns: list[str] | None = None,
) -> bytes:
    """Generator PDF A4 Landscape dengan dukungan pemilihan kolom dinamis (B2)."""
    page_w, page_h = 841.89, 595.28
    margin_x = 32.0
    table_w = page_w - 2 * margin_x  # 777.89 pt

    all_col_specs = [
        ("no", "No", 30.0, 5),
        ("ip_address", "IP Address", 88.0, 15),
        ("pengguna", "Nama Server / VM", 132.0, 22),
        ("jenis", "Jenis", 48.0, 7),
        ("host", "Host", 78.0, 13),
        ("fungsi", "Fungsi", 145.0, 25),
        ("os", "OS", 102.0, 18),
        ("status", "Status", 58.0, 9),
        ("keterangan", "Keterangan", 96.89, 16),
    ]

    if selected_columns:
        norm_sel = {c.strip().lower() for c in selected_columns}
        norm_sel.add("no")
        filtered_specs = [s for s in all_col_specs if s[0] in norm_sel]
        if not filtered_specs:
            filtered_specs = all_col_specs
    else:
        filtered_specs = all_col_specs

    raw_total_w = sum(s[2] for s in filtered_specs) or table_w
    scale = table_w / raw_total_w
    col_defs = [(s[1], s[2] * scale, max(5, int(s[3] * scale))) for s in filtered_specs]
    col_keys = [s[0] for s in filtered_specs]
    status_col_idx = col_keys.index("status") if "status" in col_keys else -1

    prepared_rows: list[tuple[list[list[str]], float, str]] = []
    for idx, r in enumerate(rows, start=1):
        ket_val = str(r.get("keterangan") or "—").strip() or "—"
        host_val = str(r.get("host_display") or r.get("host_label") or "—").strip()
        val_map = {
            "no": str(idx),
            "ip_address": str(r.get("ip_address") or "—"),
            "pengguna": str(r.get("nama") or r.get("pengguna") or "—"),
            "jenis": str(r.get("jenis") or "Fisik"),
            "host": host_val,
            "fungsi": str(r.get("fungsi") or "—"),
            "os": str(r.get("os") or "—"),
            "status": str(r.get("status") or "Aktif"),
            "keterangan": ket_val,
        }
        cells_raw = [val_map[k] for k in col_keys]
        wrapped_cells: list[list[str]] = []
        max_lines = 1
        for c_i, raw_txt in enumerate(cells_raw):
            max_chars = col_defs[c_i][2]
            lines = textwrap.wrap(raw_txt, width=max_chars) or ["—"]
            wrapped_cells.append(lines[:3])
            max_lines = max(max_lines, len(lines[:3]))
        row_h = max(24.0, 10.0 + max_lines * 11.5)
        prepared_rows.append((wrapped_cells, row_h, str(r.get("status") or "Aktif")))

    pages_data: list[list[tuple[list[list[str]], float, str, int]]] = []
    current_page: list[tuple[list[list[str]], float, str, int]] = []
    y_cursor = page_h - 112.0
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
        cmds.append("0.059 0.090 0.165 rg")
        cmds.append(
            f"BT /F2 16 Tf {margin_x:.2f} {page_h - 42:.2f} Td (Daftar IP & Server \\(VM\\)) Tj ET"
        )

        sub_str = f"Diekspor {export_date_label} - {total_entries} entri - {exporter_name}"
        cmds.append("0.392 0.455 0.545 rg")
        cmds.append(
            f"BT /F1 9.5 Tf {margin_x:.2f} {page_h - 58:.2f} Td ({pdf_escape(sub_str)}) Tj ET"
        )

        cmds.append("0.114 0.306 0.847 rg")
        cmds.append(
            f"BT /F2 11 Tf {page_w - margin_x - 52:.2f} {page_h - 44:.2f} Td (ITAM Pro) Tj ET"
        )

        th_top = page_h - 74.0
        th_h = 26.0
        cmds.append("0.059 0.090 0.165 rg")
        cmds.append(f"{margin_x:.2f} {th_top - th_h:.2f} {table_w:.2f} {th_h:.2f} re f")

        cmds.append("1 1 1 rg")
        x_pos = margin_x
        for c_title, c_w, _ in col_defs:
            cmds.append(
                f"BT /F2 8.5 Tf {x_pos + 6:.2f} {th_top - 16.5:.2f} Td "
                f"({pdf_escape(c_title)}) Tj ET"
            )
            x_pos += c_w

        y_top = th_top - th_h
        for w_cells, r_h, st_val, r_global_idx in p_rows:
            y_bot = y_top - r_h
            if r_global_idx % 2 == 1:
                cmds.append("0.973 0.980 0.988 rg")
                cmds.append(f"{margin_x:.2f} {y_bot:.2f} {table_w:.2f} {r_h:.2f} re f")

            cmds.append("0.886 0.910 0.941 RG 0.5 w")
            cmds.append(f"{margin_x:.2f} {y_bot:.2f} m {margin_x + table_w:.2f} {y_bot:.2f} l S")

            x_pos = margin_x
            for c_i, lines in enumerate(w_cells):
                c_w = col_defs[c_i][1]
                if c_i == status_col_idx:
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
                        f"({pdf_escape(lines[0])}) Tj ET"
                    )
                else:
                    cmds.append("0.059 0.090 0.165 rg")
                    font_ref = "/F2" if c_i in (1, 2) else "/F1"
                    for l_idx, line_str in enumerate(lines):
                        line_y = y_top - 13.0 - (l_idx * 10.5)
                        cmds.append(
                            f"BT {font_ref} 8.2 Tf {x_pos + 6:.2f} {line_y:.2f} Td "
                            f"({pdf_escape(line_str)}) Tj ET"
                        )
                x_pos += c_w
            y_top = y_bot

        cmds.append("0.392 0.455 0.545 rg")
        cmds.append(
            f"BT /F1 8.5 Tf {margin_x:.2f} 24.00 Td "
            "(Header navy tebal, baris selang-seling, kolom diurutkan per IP) Tj ET"
        )
        page_label = f"Halaman {p_num} dari {total_pages}"
        cmds.append(
            f"BT /F1 8.5 Tf {page_w - margin_x - 75:.2f} 24.00 Td ({pdf_escape(page_label)}) Tj ET"
        )

        page_streams.append("\n".join(cmds).encode("latin-1"))

    objects: list[bytes] = []
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
    trailer_str = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    )
    out.write(trailer_str.encode("latin-1"))
    return out.getvalue()
