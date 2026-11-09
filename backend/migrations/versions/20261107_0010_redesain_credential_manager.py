"""redesain_credential_manager

Revision ID: 20261107_0010
Revises: 20261107_0009
Create Date: 2026-11-07 15:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "20261107_0010"
down_revision: str | None = "20261107_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credential_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kode", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("ikon", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("urutan", sa.Integer(), nullable=False),
        sa.Column("schema", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_credential_types_kode"), "credential_types", ["kode"], unique=True)
    op.create_index(
        op.f("ix_credential_types_urutan"), "credential_types", ["urutan"], unique=False
    )

    op.create_table(
        "divisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nama", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("peer_access", sa.Boolean(), nullable=False),
        sa.Column("upward_min_rank", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_divisions_nama"), "divisions", ["nama"], unique=True)

    op.create_table(
        "role_type_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("can_view", sa.Boolean(), nullable=False),
        sa.Column("can_reveal", sa.Boolean(), nullable=False),
        sa.Column("can_edit", sa.Boolean(), nullable=False),
        sa.Column("can_delete", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_role_type_permissions_role_id"),
        "role_type_permissions",
        ["role_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_type_permissions_type_id"),
        "role_type_permissions",
        ["type_id"],
        unique=False,
    )

    op.create_table(
        "division_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("viewer_role_id", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=True),
        sa.Column("viewer_division_id", sa.Integer(), nullable=True),
        sa.Column("target_division_id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_division_grants_target_division_id"),
        "division_grants",
        ["target_division_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_division_grants_type_id"),
        "division_grants",
        ["type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_division_grants_viewer_division_id"),
        "division_grants",
        ["viewer_division_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_division_grants_viewer_role_id"),
        "division_grants",
        ["viewer_role_id"],
        unique=False,
    )

    op.create_table(
        "credential_acl",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("principal", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("principal_id", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("effect", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_credential_acl_credential_id"),
        "credential_acl",
        ["credential_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credential_acl_principal_id"),
        "credential_acl",
        ["principal_id"],
        unique=False,
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "jabatan",
                sqlmodel.sql.sqltypes.AutoString(length=60),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("rank", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("division_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("is_it_admin", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.create_index(op.f("ix_users_jabatan"), ["jabatan"], unique=False)
        batch_op.create_index(op.f("ix_users_rank"), ["rank"], unique=False)
        batch_op.create_index(op.f("ix_users_division_id"), ["division_id"], unique=False)
        batch_op.create_index(op.f("ix_users_is_it_admin"), ["is_it_admin"], unique=False)

    with op.batch_alter_table("credentials") as batch_op:
        batch_op.add_column(sa.Column("type_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "nama",
                sqlmodel.sql.sqltypes.AutoString(length=150),
                server_default="",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("divisi_pemilik_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("subject_rank", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column("min_view_rank", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "linked_asset_id",
                sqlmodel.sql.sqltypes.AutoString(length=50),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("data_publik", sa.JSON(), server_default="{}", nullable=False)
        )
        batch_op.add_column(sa.Column("data_rahasia", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(
            sa.Column("key_version", sa.Integer(), server_default="1", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "last_rotated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("expired_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_by",
                sqlmodel.sql.sqltypes.AutoString(length=80),
                server_default="admin",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index(op.f("ix_credentials_type_id"), ["type_id"], unique=False)
        batch_op.create_index(op.f("ix_credentials_nama"), ["nama"], unique=False)
        batch_op.create_index(
            op.f("ix_credentials_divisi_pemilik_id"), ["divisi_pemilik_id"], unique=False
        )
        batch_op.create_index(op.f("ix_credentials_subject_rank"), ["subject_rank"], unique=False)
        batch_op.create_index(
            op.f("ix_credentials_linked_asset_id"), ["linked_asset_id"], unique=False
        )
        batch_op.create_index(
            op.f("ix_credentials_last_rotated_at"), ["last_rotated_at"], unique=False
        )
        batch_op.create_index(op.f("ix_credentials_expired_at"), ["expired_at"], unique=False)
        batch_op.create_index(op.f("ix_credentials_deleted_at"), ["deleted_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("credentials") as batch_op:
        batch_op.drop_index(op.f("ix_credentials_deleted_at"))
        batch_op.drop_index(op.f("ix_credentials_expired_at"))
        batch_op.drop_index(op.f("ix_credentials_last_rotated_at"))
        batch_op.drop_index(op.f("ix_credentials_linked_asset_id"))
        batch_op.drop_index(op.f("ix_credentials_subject_rank"))
        batch_op.drop_index(op.f("ix_credentials_divisi_pemilik_id"))
        batch_op.drop_index(op.f("ix_credentials_nama"))
        batch_op.drop_index(op.f("ix_credentials_type_id"))
        for col_name in (
            "deleted_at",
            "created_by",
            "expired_at",
            "last_rotated_at",
            "key_version",
            "data_rahasia",
            "data_publik",
            "linked_asset_id",
            "min_view_rank",
            "subject_rank",
            "divisi_pemilik_id",
            "nama",
            "type_id",
        ):
            batch_op.drop_column(col_name)

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(op.f("ix_users_is_it_admin"))
        batch_op.drop_index(op.f("ix_users_division_id"))
        batch_op.drop_index(op.f("ix_users_rank"))
        batch_op.drop_index(op.f("ix_users_jabatan"))
        for col_name in ("is_it_admin", "division_id", "rank", "jabatan"):
            batch_op.drop_column(col_name)

    op.drop_table("credential_acl")
    op.drop_table("division_grants")
    op.drop_table("role_type_permissions")
    op.drop_table("divisions")
    op.drop_table("credential_types")
