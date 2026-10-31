import os
import subprocess
import sys
from pathlib import Path


def run_startup_test(env_vars: dict) -> subprocess.CompletedProcess:
    frontend_dir = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env.update(env_vars)
    env["PYTHONPATH"] = str(frontend_dir)

    return subprocess.run(
        [sys.executable, "-c", "import itam_pro.itam_pro"],
        cwd=str(frontend_dir),
        env=env,
        capture_output=True,
        text=True,
    )


def test_production_mock_safeguard():
    """Aplikasi harus crash jika berjalan di produksi dengan mock data (0.9)."""
    result = run_startup_test({"APP_ENV": "production", "USE_MOCK": "true"})
    assert result.returncode != 0
    assert (
        "DILARANG menjalankan aplikasi di lingkungan production dengan USE_MOCK=true"
        in result.stderr
    )


def test_production_weak_secret_safeguard():
    """Aplikasi harus crash di produksi jika kunci rahasia masih bawaan (0.9)."""
    result = run_startup_test(
        {
            "APP_ENV": "production",
            "USE_MOCK": "false",
            "JWT_SECRET_KEY": "rahasia_ganti_di_produksi",
        }
    )
    assert result.returncode != 0
    assert "JWT_SECRET_KEY kosong, masih bawaan" in result.stderr
