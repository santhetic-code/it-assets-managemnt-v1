"""restrukturisasi_aset_satu_data_induk

Revision ID: 20261109_0011
Revises: 20261107_0010
Create Date: 2026-11-09 10:00:00.000000
"""

from collections.abc import Sequence
import json

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

from app.core.master_data import (
    CATEGORY_TREE,
    normalize_asset_condition,
    normalize_asset_status,
)

revision: str = "20261109_0011"
down_revision: str | None = "20261107_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
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
        sa.Column("kode", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "ikon",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=False,
            server_default="box",
        ),
        sa.Column(
            "tracking",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=False,
            server_default="unit",
        ),
        sa.Column("spec_schema", sa.JSON(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)
    op.create_index(op.f("ix_categories_kode"), "categories", ["kode"], unique=True)
    op.create_index(op.f("ix_categories_nama"), "categories", ["nama"], unique=False)

    op.create_table(
        "asset_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("linked_asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column(
            "tipe",
            sqlmodel.sql.sqltypes.AutoString(length=40),
            nullable=False,
            server_default="menyuplai_daya",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_links")),
    )
    op.create_index(op.f("ix_asset_links_asset_id"), "asset_links", ["asset_id"], unique=False)
    op.create_index(
        op.f("ix_asset_links_linked_asset_id"),
        "asset_links",
        ["linked_asset_id"],
        unique=False,
    )
    op.create_index(op.f("ix_asset_links_tipe"), "asset_links", ["tipe"], unique=False)

    op.create_table(
        "asset_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("jenis", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column(
            "dari",
            sqlmodel.sql.sqltypes.AutoString(length=150),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "ke",
            sqlmodel.sql.sqltypes.AutoString(length=150),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "alasan",
            sqlmodel.sql.sqltypes.AutoString(length=150),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "catatan",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column("tanggal", sa.Date(), nullable=False),
        sa.Column(
            "oleh",
            sqlmodel.sql.sqltypes.AutoString(length=80),
            nullable=False,
            server_default="admin",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_movements")),
    )
    op.create_index(
        op.f("ix_asset_movements_asset_id"),
        "asset_movements",
        ["asset_id"],
        unique=False,
    )
    op.create_index(op.f("ix_asset_movements_jenis"), "asset_movements", ["jenis"], unique=False)

    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(
            sa.Column("asset_tag", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "nama",
                sqlmodel.sql.sqltypes.AutoString(length=150),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("peran", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=True)
        )
        batch_op.add_column(sa.Column("pengguna_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "pemakai_text",
                sqlmodel.sql.sqltypes.AutoString(length=100),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("lokasi_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "parent_asset_id",
                sqlmodel.sql.sqltypes.AutoString(length=30),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("tanggal_perolehan", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("nilai_perolehan", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "vendor",
                sqlmodel.sql.sqltypes.AutoString(length=150),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("garansi_sampai", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("purchase_item_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("specs", sa.JSON(), server_default="{}", nullable=False))
        batch_op.add_column(
            sa.Column(
                "tracking",
                sqlmodel.sql.sqltypes.AutoString(length=20),
                server_default="unit",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("qty", sa.Integer(), server_default="1", nullable=False))
        batch_op.add_column(
            sa.Column(
                "created_by",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                server_default="system",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

        batch_op.create_index(op.f("ix_assets_asset_tag"), ["asset_tag"], unique=True)
        batch_op.create_index(op.f("ix_assets_category_id"), ["category_id"], unique=False)
        batch_op.create_index(op.f("ix_assets_peran"), ["peran"], unique=False)
        batch_op.create_index(op.f("ix_assets_pengguna_id"), ["pengguna_id"], unique=False)
        batch_op.create_index(op.f("ix_assets_lokasi_id"), ["lokasi_id"], unique=False)
        batch_op.create_index(op.f("ix_assets_parent_asset_id"), ["parent_asset_id"], unique=False)
        batch_op.create_index(op.f("ix_assets_garansi_sampai"), ["garansi_sampai"], unique=False)
        batch_op.create_index(
            op.f("ix_assets_purchase_item_id"), ["purchase_item_id"], unique=False
        )
        batch_op.create_index(op.f("ix_assets_deleted_at"), ["deleted_at"], unique=False)

    # Seed Categories & Migrasi Data Satu Data Induk (Seksi 15)
    bind = op.get_bind()
    cat_name_to_id: dict[str, int] = {}
    for grp in CATEGORY_TREE:
        bind.execute(
            sa.text(
                "INSERT INTO categories (parent_id, kode, nama, ikon, tracking, spec_schema) "
                "VALUES (NULL, :kode, :nama, :ikon, :tracking, :schema)"
            ),
            {
                "kode": grp["kode"],
                "nama": grp["nama"],
                "ikon": grp["ikon"],
                "tracking": grp["tracking"],
                "schema": json.dumps({}),
            },
        )
        parent_id = bind.execute(
            sa.text("SELECT id FROM categories WHERE kode = :k"),
            {"k": grp["kode"]},
        ).scalar()
        for sub in grp.get("children", []):
            bind.execute(
                sa.text(
                    "INSERT INTO categories (parent_id, kode, nama, ikon, tracking, spec_schema) "
                    "VALUES (:pid, :kode, :nama, :ikon, :tracking, :schema)"
                ),
                {
                    "pid": parent_id,
                    "kode": sub["kode"],
                    "nama": sub["nama"],
                    "ikon": sub["ikon"],
                    "tracking": sub["tracking"],
                    "schema": json.dumps(sub.get("spec_schema", {})),
                },
            )
            sub_id = bind.execute(
                sa.text("SELECT id FROM categories WHERE kode = :k"),
                {"k": sub["kode"]},
            ).scalar()
            if sub_id is not None:
                cat_name_to_id[sub["nama"].lower()] = int(sub_id)
                cat_name_to_id[sub["kode"].lower()] = int(sub_id)

    rows = (
        bind.execute(
            sa.text(
                "SELECT id, id_aset, nama_aset, kategori, status, kondisi, penanggung_jawab, "
                "tanggal_masuk, processor, ram, storage, gpu, os, watt, ukuran_layar, resolusi, "
                "port_display, kapasitas_va, baterai, beban_perangkat, extra_specs FROM assets"
            )
        )
        .mappings()
        .all()
    )

    pcs_by_id: list[str] = []
    servers_by_name: dict[str, str] = {}

    for r in rows:
        kat_raw = (r["kategori"] or "Lainnya").strip()
        if kat_raw.startswith("SRV-") or str(r["id_aset"]).startswith("SRV-"):
            kat_raw = "Server"
        cat_id = cat_name_to_id.get(kat_raw.lower(), cat_name_to_id.get("ast"))
        norm_st = normalize_asset_status(r["status"])
        norm_kd = normalize_asset_condition(r["kondisi"])
        peran = (
            "Server"
            if kat_raw == "Server"
            else ("Backup" if norm_st == "Cadangan" else "Operasional")
        )

        extra = r["extra_specs"]
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}
        elif not isinstance(extra, dict):
            extra = {}

        specs = dict(extra)
        if kat_raw in ("PC", "Server"):
            specs.update(
                {
                    "cpu": r["processor"] or extra.get("cpu", ""),
                    "ram": r["ram"] or extra.get("ram", ""),
                    "storage": r["storage"] or extra.get("hdd_ssd", ""),
                    "vga": r["gpu"] or extra.get("vga", ""),
                    "os": r["os"] or extra.get("os", ""),
                }
            )
            if kat_raw == "Server":
                specs["tdp_cpu_w"] = int(r["watt"] or extra.get("tdp_total_w") or 0)
                specs["tdp_gpu_w"] = 0
                servers_by_name[str(r["nama_aset"]).strip().upper()] = str(r["id_aset"])
            else:
                pcs_by_id.append(str(r["id_aset"]))
        elif kat_raw == "Monitor":
            specs.update(
                {
                    "ukuran_layar": r["ukuran_layar"] or extra.get("ukuran_layar", "24"),
                    "resolusi_layar": r["resolusi"]
                    or extra.get("resolusi_layar", "1920x1080 (FHD)"),
                }
            )
        elif kat_raw == "UPS":
            specs.update(
                {
                    "kapasitas_va": int(r["kapasitas_va"] or 0),
                    "jenis_aki": r["baterai"] or "",
                }
            )

        bind.execute(
            sa.text(
                "UPDATE assets SET asset_tag = :tag, nama = :nama, kategori = :kat, "
                "category_id = :cid, status = :st, kondisi = :kd, peran = :peran, "
                "pemakai_text = :pemakai, tanggal_perolehan = :tgl, specs = :specs "
                "WHERE id = :id"
            ),
            {
                "tag": r["id_aset"],
                "nama": r["nama_aset"],
                "kat": kat_raw,
                "cid": cat_id,
                "st": norm_st,
                "kd": norm_kd,
                "peran": peran,
                "pemakai": r["penanggung_jawab"] or "",
                "tgl": r["tanggal_masuk"],
                "specs": json.dumps(specs),
                "id": r["id"],
            },
        )

    # Tautkan Monitor yang digunakan ke PC & UPS ke Server (Seksi 15.4)
    mon_rows = [
        r
        for r in rows
        if (r["kategori"] or "").lower() == "monitor"
        and normalize_asset_status(r["status"]) == "Digunakan"
    ]
    target_pcs = ["PC-003", "PC-016", "PC-001"]
    for idx, m_row in enumerate(mon_rows):
        target_pc = (
            target_pcs[idx]
            if idx < len(target_pcs) and target_pcs[idx] in pcs_by_id
            else (pcs_by_id[idx] if idx < len(pcs_by_id) else None)
        )
        if target_pc:
            bind.execute(
                sa.text(
                    "UPDATE assets SET parent_asset_id = :pid, pemakai_text = :pt, "
                    "penanggung_jawab = :pt WHERE id_aset = :mid"
                ),
                {
                    "pid": target_pc,
                    "pt": f"Terpasang di {target_pc}",
                    "mid": m_row["id_aset"],
                },
            )

    ups_rows = [r for r in rows if (r["kategori"] or "").lower() == "ups"]
    for u_row in ups_rows:
        beban = str(u_row["beban_perangkat"] or "").strip().upper()
        if not beban:
            continue
        matched_srv = servers_by_name.get(beban) or servers_by_name.get(f"SERVER {beban}")
        if not matched_srv:
            for s_name, s_tag in servers_by_name.items():
                if beban in s_name or s_name in beban:
                    matched_srv = s_tag
                    break
        if matched_srv:
            bind.execute(
                sa.text(
                    "INSERT INTO asset_links (asset_id, linked_asset_id, tipe) "
                    "VALUES (:aid, :lid, 'menyuplai_daya')"
                ),
                {"aid": u_row["id_aset"], "lid": matched_srv},
            )


def downgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        for idx_name in (
            "ix_assets_deleted_at",
            "ix_assets_purchase_item_id",
            "ix_assets_garansi_sampai",
            "ix_assets_parent_asset_id",
            "ix_assets_lokasi_id",
            "ix_assets_pengguna_id",
            "ix_assets_peran",
            "ix_assets_category_id",
            "ix_assets_asset_tag",
        ):
            batch_op.drop_index(op.f(idx_name))
        for col_name in (
            "deleted_at",
            "created_by",
            "qty",
            "tracking",
            "specs",
            "purchase_item_id",
            "garansi_sampai",
            "vendor",
            "nilai_perolehan",
            "tanggal_perolehan",
            "parent_asset_id",
            "lokasi_id",
            "pemakai_text",
            "pengguna_id",
            "peran",
            "category_id",
            "nama",
            "asset_tag",
        ):
            batch_op.drop_column(col_name)

    op.drop_table("asset_movements")
    op.drop_table("asset_links")
    op.drop_table("categories")

