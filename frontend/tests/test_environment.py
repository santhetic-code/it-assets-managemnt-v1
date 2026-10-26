import os
import subprocess
import sys


def test_production_mock_safeguard():
    """Aplikasi harus crash/exit jika berjalan di produksi dengan mock data."""
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["USE_MOCK"] = "true"

    # Jalankan inisialisasi module untuk memicu sys.exit(1)
    python_cmd = sys.executable or "python"
    result = subprocess.run(
        [python_cmd, "-c", "from itam_pro import itam_pro"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "FATAL ERROR: DILARANG" in result.stdout or "FATAL ERROR: DILARANG" in result.stderr
