"""redesain_rekap_dan_kalkulator_watt

Revision ID: 20261113_0013
Revises: e4689473699d
Create Date: 2026-11-13 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision: str = "20261113_0013"
down_revision: str | None = "e4689473699d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "power_assumptions" not in existing:
        op.create_table(
            "power_assumptions",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "jam_operasional_per_hari",
                sa.Integer(),
                nullable=False,
                server_default="24",
            ),
            sa.Column("hari_per_bulan", sa.Integer(), nullable=False, server_default="30"),
            sa.Column(
                "faktor_beban_persen",
                sa.Integer(),
                nullable=False,
                server_default="100",
            ),
            sa.Column("tarif_listrik_per_kwh", sa.Float(), nullable=True),
            sa.Column("faktor_daya_ups", sa.Float(), nullable=False, server_default="0.6"),
            sa.Column("batas_waspada_ups", sa.Integer(), nullable=False, server_default="70"),
            sa.Column("batas_kritis_ups", sa.Integer(), nullable=False, server_default="85"),
            sa.Column(
                "updated_by",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=False,
                server_default="system",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_power_assumptions")),
        )

    if "power_catalog" not in existing:
        op.create_table(
            "power_catalog",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "kategori",
                sqlmodel.sql.sqltypes.AutoString(length=40),
                nullable=False,
            ),
            sa.Column(
                "nama",
                sqlmodel.sql.sqltypes.AutoString(length=150),
                nullable=False,
            ),
            sa.Column(
                "merek",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=False,
                server_default="",
            ),
            sa.Column("tdp_w", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("peak_w", sa.Integer(), nullable=True),
            sa.Column(
                "jenis_data",
                sqlmodel.sql.sqltypes.AutoString(length=30),
                nullable=False,
                server_default="resmi",
            ),
            sa.Column(
                "sumber",
                sqlmodel.sql.sqltypes.AutoString(length=255),
                nullable=False,
                server_default="",
            ),
            sa.Column(
                "catatan",
                sqlmodel.sql.sqltypes.AutoString(length=500),
                nullable=False,
                server_default="",
            ),
            sa.Column(
                "diperbarui_oleh",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=False,
                server_default="system",
            ),
            sa.Column("aktif", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_power_catalog")),
        )
        op.create_index(
            op.f("ix_power_catalog_kategori"),
            "power_catalog",
            ["kategori"],
            unique=False,
        )
        op.create_index(op.f("ix_power_catalog_nama"), "power_catalog", ["nama"], unique=False)
        op.create_index(op.f("ix_power_catalog_aktif"), "power_catalog", ["aktif"], unique=False)

    if "watt_scenarios" not in existing:
        op.create_table(
            "watt_scenarios",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "nama",
                sqlmodel.sql.sqltypes.AutoString(length=150),
                nullable=False,
            ),
            sa.Column("asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True),
            sa.Column("komponen", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("hasil", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column(
                "dibuat_oleh",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                nullable=False,
                server_default="system",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_watt_scenarios")),
        )
        op.create_index(op.f("ix_watt_scenarios_nama"), "watt_scenarios", ["nama"], unique=False)
        op.create_index(
            op.f("ix_watt_scenarios_asset_id"),
            "watt_scenarios",
            ["asset_id"],
            unique=False,
        )


def downgrade() -> None:
    if down_revision == "e4689473699d":
        return

    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "watt_scenarios" in existing:
        op.drop_index(op.f("ix_watt_scenarios_asset_id"), table_name="watt_scenarios")
        op.drop_index(op.f("ix_watt_scenarios_nama"), table_name="watt_scenarios")
        op.drop_table("watt_scenarios")

    if "power_catalog" in existing:
        op.drop_index(op.f("ix_power_catalog_aktif"), table_name="power_catalog")
        op.drop_index(op.f("ix_power_catalog_nama"), table_name="power_catalog")
        op.drop_index(op.f("ix_power_catalog_kategori"), table_name="power_catalog")
        op.drop_table("power_catalog")

    if "power_assumptions" in existing:
        op.drop_table("power_assumptions")

