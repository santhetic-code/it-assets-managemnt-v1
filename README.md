# 📦 IT Assets Management Pro (ITAM Pro)

**ITAM Pro** adalah aplikasi web internal (*on-premise*) untuk mengelola siklus hidup inventaris perangkat keras IT (PC, Server, Monitor, UPS, dan periferal), pemetaan alamat IPv4 & Virtual Machine (VM), pemantauan konsumsi daya server, jadwal pemeliharaan, rekapitulasi finansial, hingga penyimpanan kredensial terenkripsi dan *audit log*.

---

## 📌 Status Pengembangan

- [x] **Frontend:** Python 3.12 + Reflex `0.9.12`, Design System Semantik, Unified Mock Services, Modul Halaman Lengkap (Inventory, Infrastructure, Operations, Finance, Auth), Guard APP_ENV, dan Pytest Unit Tests.
- [x] **Backend:** B0, B1, & B2 selesai: fondasi FastAPI, autentikasi JWT, RBAC, Data Master, CRUD Aset TI, auto-generate ID aset, dan pengujian unit.
- [x] **Database & Migrasi:** PostgreSQL 16 Alpine + Alembic migrations 0001 (baseline), 0002 (users), dan 0003 (assets) terpasang.

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

### Opsi 1: Menjalankan Secara Lokal (`reflex run`)
```powershell
# 1. Masuk ke direktori proyek dan aktifkan virtual environment Python 3.12
cd it-assets-managemnt-v1
.\.venv\Scripts\Activate.ps1

# 2. Salin konfigurasi environment
Copy-Item .env.example .env

# 3. Masuk ke folder frontend dan jalankan server Reflex
cd frontend
reflex run --loglevel debug
```

### Opsi 2: Menjalankan Menggunakan Docker Compose
```bash
docker compose up -d --build
```

---

## 🧪 Pengujian Unit (Pytest)

### Menjalankan Pengujian Frontend
```bash
cd frontend
pytest -v
cd ..
```

### Menjalankan Pengujian Backend
```bash
pytest backend/tests -v
```

---

## 🗄️ Migrasi Database (Alembic)

Saat mengembangkan model data baru atau mengubah skema database backend:

```bash
# 1. Membuat migrasi baru (selalu cantumkan rev-id berurutan)
docker compose exec backend alembic revision --autogenerate --rev-id 0002 -m "pesan migrasi"

# 2. Menjalankan migrasi ke versi terbaru
docker compose exec backend alembic upgrade head

# 3. Memeriksa konsistensi model dan riwayat migrasi
docker compose exec backend alembic check
```
