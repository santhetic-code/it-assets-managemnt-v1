import os
import subprocess
import sys
from pathlib import Path


def test_production_mock_safeguard():
    """Aplikasi harus crash jika berjalan di produksi dengan mock data."""
    frontend_dir = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["USE_MOCK"] = "true"
    env["PYTHONPATH"] = str(frontend_dir)

    result = subprocess.run(
        [sys.executable, "-c", "import itam_pro.config"],
        cwd=str(frontend_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "FATAL ERROR: DILARANG" in result.stdout or "FATAL ERROR: DILARANG" in result.stderr
