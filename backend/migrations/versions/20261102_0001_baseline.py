"""baseline

Revision ID: 0001
Revises: 
Create Date: 2026-11-02 03:18:36.867670
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel  # noqa: F401 (dibutuhkan bila migrasi memuat tipe sqlmodel)
from alembic import op


revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

