from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def alembic_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    db_file = tmp_path / "mig.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    get_settings.cache_clear()
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return cfg


def test_upgrade_head_creates_version_table(alembic_cfg: Config, tmp_path: Path) -> None:
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(f"sqlite:///{tmp_path / 'mig.db'}")
    assert "alembic_version" in inspect(engine).get_table_names()


def test_models_and_migrations_are_in_sync(alembic_cfg: Config) -> None:
    command.upgrade(alembic_cfg, "head")
    command.check(alembic_cfg)  # gagal bila model berbeda dari migrasi


def test_downgrade_base_works(alembic_cfg: Config) -> None:
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")

