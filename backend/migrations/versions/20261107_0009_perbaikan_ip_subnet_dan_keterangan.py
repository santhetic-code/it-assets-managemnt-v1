"""perbaikan_ip_subnet_dan_keterangan

Revision ID: 20261107_0009
Revises: 4e6fdb2d3d0c
Create Date: 2026-11-07 09:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "20261107_0009"
down_revision: str | None = "4e6fdb2d3d0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Buat tabel ip_subnets & isi 1 baris awal 192.168.1.0/24 (B4)
    op.create_table(
        "ip_subnets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cidr", sqlmodel.sql.sqltypes.AutoString(length=45), nullable=False),
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("dibuat_oleh", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("dibuat_pada", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ip_subnets_cidr"), "ip_subnets", ["cidr"], unique=True)

    op.execute(
        sa.text(
            "INSERT INTO ip_subnets (cidr, nama, dibuat_oleh, dibuat_pada) "
            "VALUES ('192.168.1.0/24', 'Subnet Utama LAN', 'system', CURRENT_TIMESTAMP)"
        )
    )

    # 2. Ubah kolom keterangan menjadi nullable (A2)
    with op.batch_alter_table("ip_allocations") as batch_op:
        batch_op.alter_column(
            "keterangan",
            existing_type=sa.VARCHAR(length=500),
            nullable=True,
        )
        batch_op.create_index(
            op.f("ix_ip_allocations_hostname"), ["hostname"], unique=False
        )
        batch_op.create_index(
            op.f("ix_ip_allocations_host_name"), ["host_name"], unique=False
        )
        batch_op.create_index(op.f("ix_ip_allocations_os"), ["os"], unique=False)
        batch_op.create_index(
            op.f("ix_ip_allocations_pengguna"), ["pengguna"], unique=False
        )

    # 3. Migrasi data lama: salin keterangan ke port_servis (Fungsi) bila port_servis masih kosong,
    #    lalu UPDATE keterangan = NULL untuk nilai kosong/spasi atau identik dengan Fungsi (A2).
    op.execute(
        sa.text(
            "UPDATE ip_allocations SET port_servis = SUBSTR(TRIM(keterangan), 1, 120) "
            "WHERE (port_servis IS NULL OR TRIM(port_servis) = '') "
            "AND keterangan IS NOT NULL AND TRIM(keterangan) NOT IN ('', '-', '—')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE ip_allocations SET keterangan = NULL "
            "WHERE keterangan IS NOT NULL AND ("
            "  TRIM(keterangan) IN ('', '-', '—') "
            "  OR LOWER(TRIM(keterangan)) = LOWER(TRIM(port_servis)) "
            "  OR keterangan LIKE 'Server Produksi (%' "
            "  OR keterangan LIKE 'Workstation Operasional (%' "
            "  OR keterangan LIKE 'Worker Addon %'"
            ")"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE ip_allocations SET keterangan = '' WHERE keterangan IS NULL")
    )
    with op.batch_alter_table("ip_allocations") as batch_op:
        batch_op.drop_index(op.f("ix_ip_allocations_pengguna"))
        batch_op.drop_index(op.f("ix_ip_allocations_os"))
        batch_op.drop_index(op.f("ix_ip_allocations_host_name"))
        batch_op.drop_index(op.f("ix_ip_allocations_hostname"))
        batch_op.alter_column(
            "keterangan",
            existing_type=sa.VARCHAR(length=500),
            nullable=False,
        )
    op.drop_index(op.f("ix_ip_subnets_cidr"), table_name="ip_subnets")
    op.drop_table("ip_subnets")

