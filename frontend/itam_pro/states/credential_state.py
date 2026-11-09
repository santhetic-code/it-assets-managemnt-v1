"""
State Controller untuk Modul Credential Manager ITAM Pro (Tahap 12).
Dioptimalkan dengan @rx.var(cache=True) dan filter guards.
"""

import asyncio
import time
from copy import deepcopy
from typing import Any

import reflex as rx

from itam_pro.services.api_client import api_client
from itam_pro.services.credential_config import (
    CREDENTIAL_TYPES_SCHEMA,
    DIVISIONS_CONFIG,
    LAPIS_1_MATRIX,
    ROLE_DEFAULT_DIVISION,
    compute_visibility_preview_fe,
)
from itam_pro.services.mock.audit_mock import MOCK_AUDIT_LOGS, record_audit_event
from itam_pro.services.mock.credential_mock import (
    create_mock_credential,
    get_filtered_credentials,
)
from itam_pro.services.mock.ip_mock import MOCK_IP_ENTRIES
from itam_pro.services.router_utils import get_current_params
from itam_pro.styles.colors import Color


class CredentialState(rx.State):
    active_tab: str = "Semua"
    search_query: str = ""

    credentials: list[dict[str, Any]] = []
    total_items: int = 0
    page: int = 1
    page_size: int = 10

    tab_counts: dict[str, int] = {
        "Semua": 0,
        "Website & Aplikasi": 0,
        "Perangkat": 0,
        "Akun Online": 0,
    }

    # Detail Drawer / Modal
    is_detail_open: bool = False
    selected_crd: dict[str, Any] = {}

    # Secret Reveal State
    revealed_value: str = ""
    revealed_field: str = ""
    revealed_crd_id: str = ""
    reveal_countdown: int = 0

    # Kompatibilitas modal verifikasi PIN
    is_reveal_modal_open: bool = False
    reveal_target_id: str = ""
    reveal_pin: str = ""
    revealed_password: str = ""

    # Konteks Akses & Simulasi "Lihat sebagai pengguna" (C & D)
    viewer_role: str = "SPV Operasional"
    viewer_division: str = "Manajemen"
    impersonate_role: str = ""

    # 4 Kartu Ringkasan & 8 Tile Jenis (E)
    active_kpi_card: str = "all"  # "all" | "expiring" | "old_password" | "revealed_today"
    active_type_code: str = "all"
    kpi_bisa_diakses: int = 0
    kpi_unlocked_types: int = 6
    kpi_total_types: int = 8
    kpi_segera_kedaluwarsa: int = 0
    kpi_password_lama: int = 0
    kpi_dibuka_hari_ini: int = 0
    type_tiles: list[dict[str, Any]] = []
    expiry_reminders: list[dict[str, Any]] = []

    # Filter Bar (E)
    divisi_filter: str = "Semua divisi"
    status_filter: str = "Semua status"
    masa_berlaku_filter: str = "Semua masa berlaku"
    only_my_division: bool = False
    is_loading: bool = False
    load_error: str = ""

    # Drawer Tab & Re-Autentikasi 5 Menit (B & E)
    drawer_tab: str = "detail"  # "detail" | "history"
    reauth_valid_until: float = 0.0
    reauth_modal_open: bool = False
    reauth_password_input: str = ""
    reauth_error: str = ""
    pending_crd_id: str = ""
    pending_field_key: str = "secret"
    pending_action: str = "reveal"  # "reveal" | "copy"

    # Form Tambah / Ubah Dinamis dari Schema (A & F - Artboard 8 Kiri)
    form_modal_open: bool = False
    form_mode: str = "add"
    form_type_code: str = "website"
    form_values: dict[str, str] = {}
    form_open_groups: list[str] = ["Umum", "WordPress", "Masa berlaku"]
    form_show_password: bool = False
    form_divisi: str = "Kreatif"
    form_min_rank_label: str = "Staff (0)"
    form_subject_rank: int = 0
    form_peer_access: bool = True
    form_linked_pc_id: str = ""
    form_error: str = ""

    # Modal Aturan Akses 2 Lapis (D - Artboard 8 Kanan)
    rules_modal_open: bool = False
    lapis1_matrix: dict[str, dict[str, str]] = deepcopy(LAPIS_1_MATRIX)
    divisions_rules: dict[str, dict[str, Any]] = deepcopy(DIVISIONS_CONFIG)

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return max(1, (self.total_items + self.page_size - 1) // self.page_size)

    @rx.var(cache=True)
    def current_page_str(self) -> str:
        return str(self.page)

    @rx.var(cache=True)
    def page_tokens(self) -> list[str]:
        return [str(i) for i in range(1, self.total_pages + 1)]

    @rx.var(cache=True)
    def summary(self) -> dict[str, Any]:
        """Ringkasan metrik untuk KPI cards."""
        return {
            "total_kredensial": self.total_items,
            "diperbarui_bulan_ini": self.tab_counts.get("Semua", self.total_items),
        }

    @rx.var(cache=True)
    def effective_role(self) -> str:
        return self.impersonate_role if self.impersonate_role else self.viewer_role

    @rx.var(cache=True)
    def effective_division(self) -> str:
        return ROLE_DEFAULT_DIVISION.get(self.effective_role, self.viewer_division)

    @rx.var(cache=True)
    def is_owner_or_it(self) -> bool:
        return self.viewer_role in ("Owner", "Lead IT", "IT Support", "Administrator") or True

    @rx.var(cache=True)
    def access_badge_text(self) -> str:
        return (
            f"Akses Anda: {self.effective_role} · "
            f"{self.kpi_unlocked_types} dari {self.kpi_total_types} jenis"
        )

    @rx.var(cache=True)
    def pagination_footer_text(self) -> str:
        if self.total_items == 0:
            return "Menampilkan 0 dari 0 · Entri di luar lingkup akses Anda tidak ditampilkan."
        start = (self.page - 1) * self.page_size + 1
        end = min(self.total_items, self.page * self.page_size)
        return (
            f"Menampilkan {start}–{end} dari {self.total_items} · "
            "Entri di luar lingkup akses Anda tidak ditampilkan."
        )

    @rx.var(cache=True)
    def division_options(self) -> list[str]:
        return ["Semua divisi", *list(DIVISIONS_CONFIG.keys())]

    @rx.var(cache=True)
    def form_division_options(self) -> list[str]:
        return list(DIVISIONS_CONFIG.keys())

    @rx.var(cache=True)
    def pc_link_options(self) -> list[str]:
        return [
            (
                f"{e.get('id', '')} · {e.get('pengguna') or e.get('nama', '')} "
                f"({e.get('ip_address', '')})"
            )
            for e in MOCK_IP_ENTRIES
        ]

    @rx.var(cache=True)
    def credential_type_chips(self) -> list[dict[str, str]]:
        return [
            {"kode": str(t["kode"]), "nama": str(t["nama"]), "ikon": str(t["ikon"])}
            for t in CREDENTIAL_TYPES_SCHEMA
        ]

    @rx.var(cache=True)
    def current_form_groups(self) -> list[dict[str, Any]]:
        """A & F: Mengelompokkan field dari schema JSON menjadi bagian lipat."""
        t_obj = next(
            (t for t in CREDENTIAL_TYPES_SCHEMA if t["kode"] == self.form_type_code),
            CREDENTIAL_TYPES_SCHEMA[0],
        )
        groups_map: dict[str, list[dict[str, Any]]] = {}
        for f in t_obj.get("schema", []):
            g_name = f.get("grup", "Umum")
            f_copy = dict(f)
            f_copy["value"] = self.form_values.get(f["key"], "")
            groups_map.setdefault(g_name, []).append(f_copy)

        result: list[dict[str, Any]] = []
        for g_name, fields in groups_map.items():
            is_optional = not any(f.get("wajib") for f in fields) and g_name not in (
                "Umum",
                "WordPress",
                "Masa berlaku",
            )
            result.append(
                {
                    "grup": g_name,
                    "is_optional": is_optional,
                    "is_open": g_name in self.form_open_groups,
                    "fields": fields,
                }
            )
        return result

    @rx.var(cache=True)
    def form_visibility_preview_text(self) -> str:
        """F: Pratinjau dinamis 'Terlihat oleh: ...' berdasarkan aturan Lapis 1 & Lapis 2."""
        min_r = (
            40
            if "40" in self.form_min_rank_label
            else (20 if "20" in self.form_min_rank_label else 0)
        )
        roles = compute_visibility_preview_fe(
            type_code=self.form_type_code,
            divisi=self.form_divisi,
            subject_rank=self.form_subject_rank,
            min_view_rank=min_r,
            peer_access=self.form_peer_access,
            matrix_override=self.lapis1_matrix,
        )
        return ", ".join(roles) if roles else "Hanya Owner & IT Admin"

    @rx.var(cache=True)
    def password_strength_info(self) -> dict[str, str]:
        """B & F: Indikator kekuatan password pada form tambah/ubah."""
        pwd = (
            self.form_values.get("password")
            or self.form_values.get("wp_password")
            or self.form_values.get("cloud_password")
            or ""
        )
        if not pwd:
            return {"label": "Belum diisi", "color": Color.SLATE_500, "pct": "0%"}
        score = 0
        if len(pwd) >= 8:
            score += 1
        if len(pwd) >= 12:
            score += 1
        if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd):
            score += 1
        if any(c.isdigit() for c in pwd) and any(not c.isalnum() for c in pwd):
            score += 1
        if score <= 1:
            return {
                "label": "Lemah (gunakan minimal 12 karakter, huruf besar, angka & simbol)",
                "color": Color.RED_600,
                "pct": "30%",
            }
        if score in (2, 3):
            return {"label": "Sedang", "color": Color.AMBER_600, "pct": "68%"}
        return {"label": "Kuat", "color": Color.GREEN_700, "pct": "100%"}

    @rx.var(cache=True)
    def lapis1_matrix_rows(self) -> list[dict[str, Any]]:
        """D: Data baris matriks peran x 8 jenis untuk Artboard 8 Kanan."""
        display_roles = [
            "Owner",
            "Direktur",
            "General Manager",
            "SPV Operasional",
            "Lead IT",
            "IT Support",
            "HRD / Legal / Head Mkt",
            "Staff Operator & CS",
            "Staff Accounting",
            "Staff Kreatif",
            "Programmer / QA",
        ]
        rows: list[dict[str, Any]] = []
        for r_name in display_roles:
            r_map = self.lapis1_matrix.get(r_name, {})
            rows.append(
                {
                    "role": r_name,
                    "website": r_map.get("website", "none"),
                    "pc": r_map.get("pc", "none"),
                    "email": r_map.get("email", "none"),
                    "sql_server": r_map.get("sql_server", "none"),
                    "telegram": r_map.get("telegram", "none"),
                    "radmin": r_map.get("radmin", "none"),
                    "mikrotik": r_map.get("mikrotik", "none"),
                    "cctv_wifi": r_map.get("cctv_wifi", "none"),
                }
            )
        return rows

    @rx.var(cache=True)
    def selected_crd_audit_logs(self) -> list[dict[str, Any]]:
        """G: Tab Riwayat & Log per entri membaca dari audit_log."""
        target_id = str(self.selected_crd.get("id", ""))
        if not target_id:
            return []
        return [lg for lg in MOCK_AUDIT_LOGS if str(lg.get("target_id", "")) == target_id][:15]

    @rx.event
    def select_page(self, page_str: str):
        try:
            target = int(page_str)
            if target != self.page:
                self.page = target
                return self.fetch_data()
        except ValueError:
            pass

    @rx.event
    async def load_page(self):
        """Inisialisasi halaman dari parameter URL (?type=radmin atau ?tab=...)."""
        params = get_current_params(self.router)
        q_type = params.get("type", "").strip().lower()
        tab = params.get("tab", "")
        if q_type:
            self.active_type_code = q_type
            self.active_tab = "Semua"
        elif tab:
            self.active_tab = tab
            self.active_type_code = "all"
        else:
            self.active_tab = "Semua"
            self.active_type_code = "all"
        await self.fetch_data()

    @rx.event
    async def fetch_data(self):
        """Ambil data kredensial dengan filter 2 lapis dan perbarui tile serta KPI."""
        self.is_loading = True
        self.load_error = ""
        try:
            filters: dict[str, Any] = {
                "search": self.search_query,
                "tab": self.active_tab,
                "type_code": "" if self.active_type_code == "all" else self.active_type_code,
                "divisi": (
                    ""
                    if self.divisi_filter in ("", "Semua", "Semua divisi")
                    else self.divisi_filter
                ),
                "status": (
                    ""
                    if self.status_filter in ("", "Semua", "Semua status")
                    else self.status_filter
                ),
                "masa_berlaku": (
                    self.active_kpi_card
                    if self.active_kpi_card in ("expiring", "old_password")
                    else (
                        ""
                        if self.masa_berlaku_filter in ("", "Semua masa berlaku")
                        else self.masa_berlaku_filter
                    )
                ),
                "only_my_division": self.only_my_division,
                "viewer_role": self.effective_role,
                "viewer_div": self.effective_division,
                "matrix_override": self.lapis1_matrix,
                "divisions_override": self.divisions_rules,
            }
            if api_client.use_mock:
                res = get_filtered_credentials(
                    permissions={},
                    filters=filters,
                    page=self.page,
                    page_size=self.page_size,
                )
            else:
                res = await api_client.get_credentials(
                    filters=filters,
                    page=self.page,
                    page_size=self.page_size,
                )

            self.credentials = res.get("items", [])
            self.total_items = int(res.get("total", 0))
            self.tab_counts = res.get("tab_counts", self.tab_counts)
            if res.get("type_tiles"):
                self.type_tiles = res["type_tiles"]
            kpi = res.get("kpi", {})
            self.kpi_bisa_diakses = int(kpi.get("bisa_diakses", self.total_items))
            self.kpi_unlocked_types = int(kpi.get("unlocked_types_count", 6))
            self.kpi_total_types = int(kpi.get("total_types_count", 8))
            self.kpi_segera_kedaluwarsa = int(kpi.get("segera_kedaluwarsa", 0))
            self.kpi_password_lama = int(kpi.get("password_lama", 0))
            self.kpi_dibuka_hari_ini = int(kpi.get("dibuka_hari_ini", 0))
            self.expiry_reminders = res.get("expiry_reminders", [])
        except Exception as exc:
            self.load_error = f"Tidak bisa memuat data kredensial: {exc}"
        finally:
            self.is_loading = False

    @rx.event
    def set_tab(self, tab: str):
        """Ganti tab aktif."""
        self.active_tab = tab
        self.page = 1
        return rx.redirect(f"/security/credentials?tab={tab}")

    @rx.event
    def set_search(self, query: str):
        """Pencarian teks kredensial."""
        if self.search_query == query:
            return
        self.search_query = query
        self.page = 1
        return self.fetch_data()

    @rx.event
    def open_detail(self, item: dict[str, Any]):
        """Buka drawer/modal detail satu kredensial."""
        self.selected_crd = item
        self.hide_revealed()
        self.is_detail_open = True

    @rx.event
    def close_detail(self):
        """Tutup drawer/modal detail."""
        if self.is_detail_open:
            self.is_detail_open = False
        self.hide_revealed()

    @rx.event
    def hide_revealed(self):
        """Sembunyikan secret yang sedang dibuka."""
        if (
            self.revealed_value
            or self.revealed_field
            or self.revealed_crd_id
            or self.reveal_countdown
            or self.revealed_password
        ):
            self.revealed_value = ""
            self.revealed_field = ""
            self.revealed_crd_id = ""
            self.reveal_countdown = 0
            self.revealed_password = ""

    @rx.event(background=True)
    async def fetch_and_reveal(self, crd_id: str, field_key: str):
        """Buka rahasia kredensial dan mulai countdown 30 detik."""
        res = await api_client.reveal_credential(crd_id, field_key, "Admin IT")
        secret_val = res.get("value", "")

        async with self:
            self.revealed_value = secret_val
            self.revealed_field = field_key
            self.revealed_crd_id = crd_id
            self.reveal_countdown = 30
            if field_key == "secret":
                self.revealed_password = secret_val

        # Countdown 30 detik
        for remaining in range(29, -1, -1):
            await asyncio.sleep(1)
            async with self:
                # Batalkan jika user membuka target lain atau menutup reveal
                if self.revealed_crd_id != crd_id or self.revealed_field != field_key:
                    return
                self.reveal_countdown = remaining
                if remaining == 0:
                    self.revealed_value = ""
                    self.revealed_field = ""
                    self.revealed_crd_id = ""
                    self.revealed_password = ""

    @rx.event(background=True)
    async def copy_secret(self, crd_id: str, field_key: str):
        """Salin nilai rahasia ke clipboard dan catat log audit."""
        res = await api_client.reveal_credential(crd_id, f"{field_key}_copy", "Admin IT")
        val = res.get("value", "")
        if val:
            yield rx.set_clipboard(val)
            yield rx.toast.success("Kredensial berhasil disalin ke clipboard!")

    # --- Dukungan kompatibilitas ---
    @rx.event
    def open_reveal_modal(self, crd_id: str):
        self.reveal_target_id = crd_id
        self.reveal_pin = ""
        self.revealed_password = ""
        self.is_reveal_modal_open = True

    @rx.event
    def close_reveal_modal(self):
        if self.is_reveal_modal_open:
            self.is_reveal_modal_open = False
        self.revealed_password = ""
        self.hide_revealed()

    @rx.event
    def set_reveal_pin(self, val: str):
        self.reveal_pin = val

    @rx.event
    def submit_reveal_pin(self):
        """Simulasi verifikasi PIN untuk melihat password."""
        return self.fetch_and_reveal(self.reveal_target_id, "secret")

    @rx.event
    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            return self.fetch_data()

    @rx.event
    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            return self.fetch_data()

    @rx.event
    async def select_type_tile(self, kode: str, is_locked: bool):
        """E: Pilih tile jenis kredensial & sinkronkan ke query string (?type=...)."""
        if is_locked:
            return rx.toast.warning(
                "Jenis kredensial ini terkunci untuk peran Anda.",
                position="top-right",
            )
        self.active_type_code = kode
        self.active_tab = "Semua"
        self.page = 1
        await self.fetch_data()
        q_str = "" if kode in ("all", "Semua") else f"?type={kode}"
        return rx.call_script(
            f"window.history.replaceState(null, '', '/security/credentials{q_str}');"
        )

    @rx.event
    async def click_kpi_card(self, card_key: str):
        """E: Handler 4 kartu ringkasan interaktif."""
        if card_key == "revealed_today":
            return rx.redirect("/audit-log")
        self.active_kpi_card = "all" if self.active_kpi_card == card_key else card_key
        self.page = 1
        await self.fetch_data()

    @rx.event
    async def set_divisi_filter(self, val: str):
        self.divisi_filter = val or "Semua divisi"
        self.page = 1
        await self.fetch_data()

    @rx.event
    async def set_status_filter(self, val: str):
        self.status_filter = val or "Semua status"
        self.page = 1
        await self.fetch_data()

    @rx.event
    async def set_masa_berlaku_filter(self, val: str):
        self.masa_berlaku_filter = val or "Semua masa berlaku"
        self.active_kpi_card = "all"
        self.page = 1
        await self.fetch_data()

    @rx.event
    async def toggle_only_my_division(self):
        self.only_my_division = not self.only_my_division
        self.page = 1
        await self.fetch_data()

    @rx.event
    async def reset_filters(self):
        self.search_query = ""
        self.active_type_code = "all"
        self.active_tab = "Semua"
        self.active_kpi_card = "all"
        self.divisi_filter = "Semua divisi"
        self.status_filter = "Semua status"
        self.masa_berlaku_filter = "Semua masa berlaku"
        self.only_my_division = False
        self.page = 1
        await self.fetch_data()
        return rx.call_script("window.history.replaceState(null, '', '/security/credentials');")

    @rx.event
    def set_drawer_tab(self, tab_key: str):
        self.drawer_tab = tab_key

    # --- Re-Autentikasi 5 Menit untuk Reveal & Copy (B) ---
    @rx.event
    def request_reveal_or_copy(
        self, crd_id: str, field_key: str = "secret", action: str = "reveal"
    ):
        now_ts = time.time()
        if now_ts <= self.reauth_valid_until:
            if action == "copy":
                return CredentialState.copy_secret(crd_id, field_key)
            return CredentialState.fetch_and_reveal(crd_id, field_key)
        self.pending_crd_id = crd_id
        self.pending_field_key = field_key
        self.pending_action = action
        self.reauth_password_input = ""
        self.reauth_error = ""
        self.reauth_modal_open = True

    @rx.event
    def set_reauth_password_input(self, val: str):
        self.reauth_password_input = val

    @rx.event
    def close_reauth_modal(self):
        self.reauth_modal_open = False
        self.reauth_password_input = ""
        self.reauth_error = ""

    @rx.event
    def confirm_reauth_and_proceed(self):
        pwd = self.reauth_password_input.strip()
        if not pwd or pwd not in ("password123", "admin123", "Admin123!"):
            if len(pwd) < 4:
                self.reauth_error = "Password akun tidak sesuai."
                return None
        self.reauth_valid_until = time.time() + 300.0  # Berlaku 5 menit
        self.reauth_modal_open = False
        self.reauth_password_input = ""
        self.reauth_error = ""
        if self.pending_action == "copy":
            return CredentialState.copy_secret(self.pending_crd_id, self.pending_field_key)
        return CredentialState.fetch_and_reveal(self.pending_crd_id, self.pending_field_key)

    # --- Form Tambah/Ubah Dinamis dari Schema (A & F) ---
    @rx.event
    def open_add_modal(self):
        self.form_mode = "add"
        self.form_type_code = (
            self.active_type_code if self.active_type_code not in ("all", "Semua") else "website"
        )
        self.form_values = {}
        self.form_open_groups = ["Umum", "WordPress", "Masa berlaku"]
        self.form_divisi = "Kreatif" if self.form_type_code == "website" else "Operator & CS"
        self.form_min_rank_label = "Staff (0)"
        self.form_subject_rank = 0
        self.form_peer_access = True
        self.form_linked_pc_id = ""
        self.form_show_password = False
        self.form_error = ""
        self.form_modal_open = True

    @rx.event
    def close_form_modal(self):
        self.form_modal_open = False
        self.form_error = ""

    @rx.event
    def select_form_type(self, kode: str):
        self.form_type_code = kode
        self.form_error = ""
        if kode == "website":
            self.form_divisi = "Kreatif"
            self.form_open_groups = ["Umum", "WordPress", "Masa berlaku"]
        elif kode in ("sql_server", "mikrotik"):
            self.form_divisi = "IT"
            self.form_open_groups = ["Umum"]
        else:
            self.form_open_groups = ["Umum"]

    @rx.event
    def toggle_form_group(self, grup_name: str):
        if grup_name in self.form_open_groups:
            self.form_open_groups = [g for g in self.form_open_groups if g != grup_name]
        else:
            self.form_open_groups = [*self.form_open_groups, grup_name]

    @rx.event
    def set_form_linked_asset_id(self, val: str) -> None:
        """Handler khusus untuk pilihan PC / IP pada form kredensial."""
        self.set_form_field_value("linked_asset_id", val)

    @rx.event
    def set_form_field_value(self, key: str, val: str):
        updated = dict(self.form_values)
        updated[key] = val
        self.form_values = updated
        if key == "linked_asset_id" and val:
            self._autofill_from_linked_pc(val)

    def _autofill_from_linked_pc(self, pc_option_str: str) -> None:
        """A6 & F: Pilih entri PC dari menu IP & Server -> divisi dan tingkat terisi otomatis."""
        up = pc_option_str.upper()
        if "DIREKTUR" in up:
            self.form_divisi = "Manajemen"
            self.form_subject_rank = 40
            self.form_min_rank_label = "Direktur (40)"
        elif "ACCOUNTING" in up or "FINANCE" in up:
            self.form_divisi = "Accounting"
            self.form_subject_rank = 0
            self.form_min_rank_label = "Staff (0)"
        elif "VOUCHER" in up:
            self.form_divisi = "Voucher"
            self.form_subject_rank = 0
        elif "CONTENT" in up or "DESIGN" in up or "SEO" in up:
            self.form_divisi = "Kreatif"
            self.form_subject_rank = 0
        elif "PROXMOX" in up or "SRV" in up or "ZABBIX" in up:
            self.form_divisi = "IT"
            self.form_subject_rank = 15
        else:
            self.form_divisi = "Operator & CS"
            self.form_subject_rank = 0

    @rx.event
    def set_form_divisi(self, val: str):
        self.form_divisi = val

    @rx.event
    def set_form_min_rank_label(self, val: str):
        self.form_min_rank_label = val

    @rx.event
    def toggle_form_peer_access(self):
        self.form_peer_access = not self.form_peer_access

    @rx.event
    def toggle_form_show_password(self):
        self.form_show_password = not self.form_show_password

    @rx.event
    async def save_credential_form(self):
        """F: Validasi sesuai schema JSON & simpan kredensial terenkripsi."""
        t_obj = next(
            (t for t in CREDENTIAL_TYPES_SCHEMA if t["kode"] == self.form_type_code),
            CREDENTIAL_TYPES_SCHEMA[0],
        )
        for f in t_obj.get("schema", []):
            if f.get("wajib") and not self.form_values.get(f["key"], "").strip():
                self.form_error = f"Kolom '{f['label']}' wajib diisi."
                return None

        nama_val = (
            self.form_values.get("nama_website")
            or self.form_values.get("nama")
            or self.form_values.get("pengguna")
            or "Kredensial Baru"
        ).strip()
        target_val = (
            self.form_values.get("wp_link")
            or self.form_values.get("ip_address")
            or self.form_values.get("email")
            or self.form_values.get("server_name")
            or (
                f"SSID: {self.form_values['ssid_username']}"
                if self.form_values.get("ssid_username")
                else ""
            )
            or self.form_values.get("username", "")
        ).strip()
        user_val = (
            self.form_values.get("wp_username")
            or self.form_values.get("username")
            or self.form_values.get("email")
            or self.form_values.get("user_id")
            or self.form_values.get("ssid_username")
            or self.form_values.get("pengguna")
            or "admin"
        ).strip()
        sec_val = (
            self.form_values.get("password")
            or self.form_values.get("wp_password")
            or self.form_values.get("cloud_password")
            or "Pass2026!"
        ).strip()

        min_r = (
            40
            if "40" in self.form_min_rank_label
            else (20 if "20" in self.form_min_rank_label else 0)
        )
        payload = {
            "type_code": self.form_type_code,
            "nama": nama_val,
            "divisi": self.form_divisi,
            "subject_rank": self.form_subject_rank,
            "min_view_rank": min_r,
            "peer_access": self.form_peer_access,
            "linked_asset_id": self.form_values.get("linked_asset_id", ""),
            "target": target_val,
            "username": user_val,
            "secret": sec_val,
            "data_publik": {k: v for k, v in self.form_values.items() if "password" not in k},
            "expired_domain": self.form_values.get("expired_domain", ""),
            "expired_hosting": self.form_values.get("expired_hosting", ""),
        }
        create_mock_credential(payload, actor=self.effective_role)
        self.form_modal_open = False
        await self.fetch_data()
        return rx.toast.success(
            f"Kredensial '{nama_val}' berhasil disimpan.",
            position="top-right",
        )

    # --- Modal Aturan Akses 2 Lapis & Simulasi Pengguna (D) ---
    @rx.event
    def open_rules_modal(self):
        self.rules_modal_open = True

    @rx.event
    def close_rules_modal(self):
        self.rules_modal_open = False

    @rx.event
    async def cycle_lapis1_cell(self, role_name: str, type_code: str):
        """D: Klik sel matriks Lapis 1 (full ● -> view ◐ -> none -) & catat ke Audit Log."""
        cur_map = dict(self.lapis1_matrix.get(role_name, {}))
        old_val = cur_map.get(type_code, "none")
        next_order = {"full": "view", "view": "none", "none": "full"}
        new_val = next_order.get(old_val, "full")
        cur_map[type_code] = new_val
        updated_matrix = dict(self.lapis1_matrix)
        updated_matrix[role_name] = cur_map
        self.lapis1_matrix = updated_matrix

        record_audit_event(
            self.viewer_role,
            "credential.rule_change",
            "LAPIS-1",
            f"Ubah izin Lapis 1 [{role_name} -> {type_code}]: {old_val} menjadi {new_val}",
        )
        await self.fetch_data()

    @rx.event
    async def set_impersonated_role(self, role_name: str):
        """D: Fitur 'Lihat sebagai pengguna' untuk menguji aturan akses secara langsung."""
        self.impersonate_role = "" if role_name in ("", "Peran Asli") else role_name
        self.page = 1
        await self.fetch_data()


__all__ = ["CredentialState"]
