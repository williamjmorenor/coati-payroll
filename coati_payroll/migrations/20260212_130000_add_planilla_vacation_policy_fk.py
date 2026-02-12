# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
# pylint: disable=no-member
"""Add planilla.vacation_policy_id foreign key.

Revision ID: 20260212_130000
Revises: 20260212_120000
Create Date: 2026-02-12 13:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260212_130000"
down_revision = "20260212_120000"
branch_labels = None
depends_on = None


def upgrade():
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("planilla", schema=None) as batch_op:
        batch_op.add_column(sa.Column("vacation_policy_id", sa.String(length=26), nullable=True))
        batch_op.create_index("ix_planilla_vacation_policy_id", ["vacation_policy_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_planilla_vacation_policy_id",
            "vacation_policy",
            ["vacation_policy_id"],
            ["id"],
        )


def downgrade():
    # In SQLite with batch mode, dropping the column automatically removes the FK constraint
    # because Alembic recreates the table without the column and its constraints
    with op.batch_alter_table("planilla", schema=None) as batch_op:
        batch_op.drop_index("ix_planilla_vacation_policy_id")
        batch_op.drop_column("vacation_policy_id")
