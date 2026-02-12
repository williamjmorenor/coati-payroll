# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
    op.add_column("planilla", sa.Column("vacation_policy_id", sa.String(length=26), nullable=True))
    op.create_index("ix_planilla_vacation_policy_id", "planilla", ["vacation_policy_id"], unique=False)
    op.create_foreign_key(
        "fk_planilla_vacation_policy_id",
        "planilla",
        "vacation_policy",
        ["vacation_policy_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_planilla_vacation_policy_id", "planilla", type_="foreignkey")
    op.drop_index("ix_planilla_vacation_policy_id", table_name="planilla")
    op.drop_column("planilla", "vacation_policy_id")
