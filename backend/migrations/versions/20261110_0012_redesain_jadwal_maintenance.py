"""redesain_jadwal_maintenance

Revision ID: 20261110_0012
Revises: 20261109_0011
Create Date: 2026-11-10 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision: str = "20261110_0012"
down_revision: str | None = "20261109_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "locations",
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
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_locations")),
    )
    op.create_index(op.f("ix_locations_parent_id"), "locations", ["parent_id"], unique=False)
    op.create_index(op.f("ix_locations_nama"), "locations", ["nama"], unique=False)

    op.create_table(
        "vendors",
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
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column(
            "jenis_layanan",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="AC & Pendingin",
        ),
        sa.Column(
            "kontak",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "catatan",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=False,
            server_default="",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vendors")),
    )
    op.create_index(op.f("ix_vendors_nama"), "vendors", ["nama"], unique=False)

    op.create_table(
        "maintenance_templates",
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
            "nama", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column(
            "kategori_objek",
            sqlmodel.sql.sqltypes.AutoString(length=60),
            nullable=False,
        ),
        sa.Column(
            "kegiatan", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False
        ),
        sa.Column(
            "jenis",
            sqlmodel.sql.sqltypes.AutoString(length=40),
            nullable=False,
            server_default="Preventif",
        ),
        sa.Column(
            "interval_nilai", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "interval_satuan",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="bulan",
        ),
        sa.Column("interval_pemakaian", sa.Integer(), nullable=True),
        sa.Column(
            "satuan_pemakaian",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="jam",
        ),
        sa.Column("checklist", sa.JSON(), nullable=False),
        sa.Column(
            "pelaksana_default",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
            server_default="Internal",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_templates")),
    )
    op.create_index(
        op.f("ix_maintenance_templates_nama"),
        "maintenance_templates",
        ["nama"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_templates_kategori_objek"),
        "maintenance_templates",
        ["kategori_objek"],
        unique=False,
    )

    op.create_table(
        "maintenance_plans",
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
            "kode_rencana", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False
        ),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column(
            "kegiatan", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False
        ),
        sa.Column(
            "jenis",
            sqlmodel.sql.sqltypes.AutoString(length=40),
            nullable=False,
            server_default="Preventif",
        ),
        sa.Column(
            "objek_tipe",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
            server_default="aset",
        ),
        sa.Column(
            "asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True
        ),
        sa.Column(
            "kategori_objek",
            sqlmodel.sql.sqltypes.AutoString(length=60),
            nullable=False,
            server_default="PC",
        ),
        sa.Column(
            "lokasi_nama",
            sqlmodel.sql.sqltypes.AutoString(length=120),
            nullable=False,
            server_default="Kantor Blok 14",
        ),
        sa.Column(
            "ruangan_nama",
            sqlmodel.sql.sqltypes.AutoString(length=120),
            nullable=False,
            server_default="",
        ),
        sa.Column("filter_kelompok", sa.JSON(), nullable=False),
        sa.Column(
            "jumlah_unit_manual", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column(
            "interval_nilai", sa.Integer(), nullable=False, server_default="3"
        ),
        sa.Column(
            "interval_satuan",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="bulan",
        ),
        sa.Column("interval_pemakaian", sa.Integer(), nullable=True),
        sa.Column(
            "hitung_dari",
            sqlmodel.sql.sqltypes.AutoString(length=40),
            nullable=False,
            server_default="tanggal_selesai",
        ),
        sa.Column("last_done_at", sa.Date(), nullable=True),
        sa.Column(
            "last_result",
            sqlmodel.sql.sqltypes.AutoString(length=200),
            nullable=False,
            server_default="—",
        ),
        sa.Column("last_meter", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_meter", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_due_at", sa.Date(), nullable=True),
        sa.Column(
            "pelaksana_tipe",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="Internal",
        ),
        sa.Column("pic_user_id", sa.Integer(), nullable=True),
        sa.Column("vendor_id", sa.Integer(), nullable=True),
        sa.Column(
            "pelaksana_nama",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
            server_default="Ridho",
        ),
        sa.Column("pengingat", sa.JSON(), nullable=False),
        sa.Column("checklist", sa.JSON(), nullable=False),
        sa.Column("aktif", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_by",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="admin",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_plans")),
    )
    op.create_index(
        op.f("ix_maintenance_plans_kode_rencana"),
        "maintenance_plans",
        ["kode_rencana"],
        unique=True,
    )
    op.create_index(
        op.f("ix_maintenance_plans_template_id"),
        "maintenance_plans",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_jenis"),
        "maintenance_plans",
        ["jenis"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_objek_tipe"),
        "maintenance_plans",
        ["objek_tipe"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_asset_id"),
        "maintenance_plans",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_kategori_objek"),
        "maintenance_plans",
        ["kategori_objek"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_lokasi_nama"),
        "maintenance_plans",
        ["lokasi_nama"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_next_due_at"),
        "maintenance_plans",
        ["next_due_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_pelaksana_tipe"),
        "maintenance_plans",
        ["pelaksana_tipe"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_pelaksana_nama"),
        "maintenance_plans",
        ["pelaksana_nama"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_plans_aktif"),
        "maintenance_plans",
        ["aktif"],
        unique=False,
    )

    op.create_table(
        "maintenance_logs",
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
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column(
            "kode_rencana",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True
        ),
        sa.Column(
            "objek_display",
            sqlmodel.sql.sqltypes.AutoString(length=200),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "kegiatan",
            sqlmodel.sql.sqltypes.AutoString(length=150),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "jenis",
            sqlmodel.sql.sqltypes.AutoString(length=40),
            nullable=False,
            server_default="Preventif",
        ),
        sa.Column("dikerjakan_pada", sa.Date(), nullable=False),
        sa.Column("unit_dikerjakan", sa.JSON(), nullable=False),
        sa.Column(
            "pelaksana_tipe",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="Internal",
        ),
        sa.Column(
            "pelaksana",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
            server_default="Ridho",
        ),
        sa.Column(
            "biaya",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "nomor_nota",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "hasil_catatan",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column("checklist_hasil", sa.JSON(), nullable=False),
        sa.Column("meter_reading", sa.Integer(), nullable=True),
        sa.Column("lampiran", sa.JSON(), nullable=False),
        sa.Column(
            "ada_temuan", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("repair_ticket_id", sa.Integer(), nullable=True),
        sa.Column("purchase_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_by",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="admin",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_logs")),
    )
    op.create_index(
        op.f("ix_maintenance_logs_plan_id"),
        "maintenance_logs",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_logs_kode_rencana"),
        "maintenance_logs",
        ["kode_rencana"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_logs_asset_id"),
        "maintenance_logs",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_logs_dikerjakan_pada"),
        "maintenance_logs",
        ["dikerjakan_pada"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_logs_pelaksana"),
        "maintenance_logs",
        ["pelaksana"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_logs_ada_temuan"),
        "maintenance_logs",
        ["ada_temuan"],
        unique=False,
    )

    op.create_table(
        "maintenance_tickets",
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
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column(
            "asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True
        ),
        sa.Column(
            "target_label",
            sqlmodel.sql.sqltypes.AutoString(length=200),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "dilaporkan_oleh",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="admin",
        ),
        sa.Column(
            "masalah",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "status",
            sqlmodel.sql.sqltypes.AutoString(length=30),
            nullable=False,
            server_default="Dilaporkan",
        ),
        sa.Column("tanggal", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_maintenance_tickets")),
    )
    op.create_index(
        op.f("ix_maintenance_tickets_plan_id"),
        "maintenance_tickets",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_tickets_asset_id"),
        "maintenance_tickets",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_tickets_status"),
        "maintenance_tickets",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_tickets_tanggal"),
        "maintenance_tickets",
        ["tanggal"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("maintenance_tickets")
    op.drop_table("maintenance_logs")
    op.drop_table("maintenance_plans")
    op.drop_table("maintenance_templates")
    op.drop_table("vendors")
    op.drop_table("locations")
