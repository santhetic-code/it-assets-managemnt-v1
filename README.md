# 📦 IT Assets Management Pro (ITAM Pro)

**ITAM Pro** adalah aplikasi web internal (*on-premise*) untuk mengelola siklus hidup inventaris perangkat keras IT (PC, Server, Monitor, UPS, dan periferal), pemetaan alamat IPv4 & Virtual Machine (VM), pemantauan konsumsi daya server, jadwal pemeliharaan, rekapitulasi finansial, hingga penyimpanan kredensial terenkripsi dan *audit log*.

---

## 📌 Status Pengembangan

- [x] **Frontend:** Python 3.12 + Reflex `0.9.12`, Design System Semantik, Unified Mock Services, Modul Halaman Lengkap (Inventory, Infrastructure, Operations, Finance, Auth), Guard APP_ENV, dan Pytest Unit Tests (51/51 passed).
- [x] **Backend:** B0, B1, B2, B3, B4, B5, B6, B7, B8, & B9 selesai penuh:
  - Fondasi FastAPI, autentikasi JWT, RBAC, dan Data Master.
  - CRUD Aset TI lengkap beserta spesifikasi teknis dan deteksi duplikasi serial number.
  - Alokasi IP numerik, validasi IPv4 canonical, pencegahan konflik, dan manajemen VM.
  - Layanan pemantauan daya (Rekap Watt Server) dan kapasitas baterai UPS.
  - Modul Keuangan (Rekap Pembelian PO, Invoice INV, Tagihan Berulang BIL, serta siklus jatuh tempo).
  - Modul Operasional Maintenance (Jadwal pemeliharaan, riwayat servis, bulk scheduling, auto-regenerasi siklus rutin).
  - Modul Keamanan Credential Manager (Enkripsi simetris Fernet, sanitasi secret, hak akses per tipe kredensial).
  - Modul Audit Log (Pencatatan jejak audit otomatis, sanitasi kredensial, filter level risiko).
  - Modul Manajemen Pengguna & Reset Password Akun (Proteksi anti-hapus diri sendiri & anti-nonaktifkan admin terakhir).
  - Modul Dashboard Agregasi Real-Time (Kalkulasi metrik lintas modul secara dinamis).
  - **B9 - Integrasi Data Nyata CSV, Security Hardening, & Kesiapan Deploy On-Premise**:
    - Mesin impor CSV idempoten (`docs/data/rekap_ups_xml.csv`, `rekap_watt_server.csv`, `ip_list_xml.csv`, `rekap_pembelian.csv`).
    - Endpoint Admin `POST /api/v1/master/import-csv` dan alias `POST /api/v1/users/import-csv`.
    - HTTP Security Headers Middleware (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, `Cache-Control: no-store`).
    - Global Unhandled Exception Handler (HTTP 500 JSON Bahasa Indonesia tanpa leak detail teknis/stack trace).
    - Anti-Brute-Force Rate Limiter pada login (Blokir sementara IP/username setelah 10 kali gagal -> HTTP 429).
    - Generator rahasia produksi (`scripts.generate_secrets`).
    - Konfigurasi deployment produksi on-premise (`docker-compose.prod.yml`).
- [x] **Database & Migrasi:** PostgreSQL 16 Alpine + Alembic migrations 0001 s/d 0008 (head) terpasang dan sinkron 100%.

---

## 🏗️ Arsitektur & Mode `USE_MOCK`

Proyek ini menggunakan arsitektur **Decoupled Containerized Web Application**:
- **Frontend (`itam_frontend`):** Python 3.12 + **Reflex `0.9.12`** (Port `3000` untuk UI, Port `8000` untuk State/WebSocket).
- **Backend (`itam_backend`):** Python 3.12 + **FastAPI + SQLModel + Alembic** (Port internal `8001` di jaringan `itam_net`).
- **Database (`itam_db`):** **PostgreSQL 16 Alpine** (Port internal `5432`).

### Abstraksi `USE_MOCK`
Seluruh komunikasi data dari Reflex State melewati satu pintu di `frontend/itam_pro/services/api_client.py`:
- **`USE_MOCK=true` (Default Fase Frontend-First):** Data disuplai dari *unified mock database* (`services/mock/seed.py` & `ip_mock.py`) dengan kontrak JSON `{items, total, page, page_size}` yang identik dengan respons FastAPI.
- **`USE_MOCK=false` (Mode Produksi / Integrasi Backend):** `api_client.py` meneruskan request HTTP secara *server-to-server* menggunakan `httpx` ke container `http://backend:8001`.

---

## 🚀 Cara Menjalankan Proyek

### Opsi 1: Menjalankan Secara Lokal Pengembangan
```powershell
# 1. Masuk ke direktori proyek dan aktifkan virtual environment Python 3.12
cd it-assets-managemnt-v1
.\.venv\Scripts\Activate.ps1

# 2. Salin konfigurasi environment
Copy-Item .env.example .env

# 3. Jalankan backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload

# 4. Masuk ke folder frontend dan jalankan Reflex
cd frontend
reflex run --loglevel debug
```

### Opsi 2: Menjalankan Menggunakan Docker Compose (Pengembangan)
```bash
docker compose up -d --build
```

### Opsi 3: Deployment Produksi On-Premise
```bash
# 1. Generate rahasia produksi baru (JWT_SECRET_KEY, FERNET_MASTER_KEY, POSTGRES_PASSWORD)
python -m scripts.generate_secrets

# 2. Perbarui file .env produksi dengan rahasia yang dihasilkan di atas

# 3. Jalankan stack produksi (otomatis migrasi Alembic, seed pengguna, dan impor CSV)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 📥 Impor Data Operasional Nyata (CSV)

Sistem menyediakan mesin impor CSV idempoten untuk memuat data nyata dari `docs/data/`:
- `rekap_ups_xml.csv` -> Aset UPS (kapasitas VA/Watt, aki, beban perangkat)
- `rekap_watt_server.csv` -> Aset Server (spesifikasi CPU, GPU, RAM, Storage, TDP Watt)
- `ip_list_xml.csv` -> Alokasi IPv4 (Server fisik, Addon/VM, PC Operasional)
- `rekap_pembelian.csv` -> Rekap Pembelian (PO, nominal Rupiah ternormalisasi, vendor)

### Menjalankan Impor via CLI:
```bash
# Di dalam container backend:
docker compose exec backend python -m scripts.import_csv

# Atau di lingkungan lokal (dengan DB terhubung):
python -m scripts.import_csv
```

### Menjalankan Impor via API (Khusus Administrator):
```http
POST /api/v1/master/import-csv
Authorization: Bearer <ADMIN_JWT_TOKEN>
```

---

## 🧪 Pengujian Unit (Pytest)

### Menjalankan Seluruh Pengujian (112 Tests)
```bash
# Pengujian Backend (61 tests)
pytest backend/tests -v

# Pengujian Frontend (51 tests)
pytest frontend/tests -v
```

---

## 🗄️ Migrasi Database (Alembic)

```bash
# 1. Menjalankan migrasi ke versi terbaru (0008 head)
docker compose exec backend alembic upgrade head

# 2. Memeriksa konsistensi model dan riwayat migrasi
docker compose exec backend alembic check
```
