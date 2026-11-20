"""tambah kolom user_agent dan changes pada audit_logs

Revision ID: 0014
Revises: 20261113_0013
Create Date: 2026-11-20 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "20261113_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column(
            "user_agent",
            sa.String(length=255),
            nullable=False,
            server_default="tidak diketahui",
        ),
    )
    op.add_column(
        "audit_logs",
        sa.Column("changes", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "changes")
    op.drop_column("audit_logs", "user_agent")
