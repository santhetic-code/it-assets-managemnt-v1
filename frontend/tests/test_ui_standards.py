import os
import re


def test_no_hardcoded_hex_colors():
    """Memastikan tidak ada nilai hex (mis. #FFFFFF) di luar folder styles/."""
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,6}\b")
    exclude_dirs = ["styles", ".web", "__pycache__", "tests", "docs", "assets"]
    violations = []

    base_dir = os.path.join(os.path.dirname(__file__), "..", "itam_pro")
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        # Pengecualian komentar atau docstring
                        if line.strip().startswith("#"):
                            continue
                        if hex_pattern.search(line):
                            violations.append(f"{file}:{line_no} -> {line.strip()}")

    assert not violations, (
        "Ditemukan hardcoded hex color. Gunakan token dari styles/colors.py:\n"
        + "\n".join(violations)
    )
