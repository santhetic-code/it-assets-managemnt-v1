import os
import subprocess
import sys
from pathlib import Path


def run_config_test(env_vars: dict) -> subprocess.CompletedProcess:
    frontend_dir = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env.update(env_vars)
    env["PYTHONPATH"] = str(frontend_dir)

    return subprocess.run(
        [sys.executable, "-c", "import itam_pro.config"],
        cwd=str(frontend_dir),
        env=env,
        capture_output=True,
        text=True,
    )


def test_production_mock_safeguard():
    """Aplikasi harus crash jika berjalan di produksi dengan mock data."""
    result = run_config_test({"APP_ENV": "production", "USE_MOCK": "true"})
    assert result.returncode != 0
    assert "FATAL ERROR: DILARANG" in result.stderr


def test_invalid_app_env_safeguard():
    """Aplikasi harus crash jika APP_ENV bukan 'dev' atau 'production'."""
    result = run_config_test({"APP_ENV": "prod", "USE_MOCK": "false"})
    assert result.returncode != 0
    assert "Nilai APP_ENV='prod' tidak valid" in result.stderr
