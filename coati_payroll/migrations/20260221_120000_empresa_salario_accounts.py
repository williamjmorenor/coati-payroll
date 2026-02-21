# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Add company-level accounting accounts for base salary.

Revision ID: 20260221_120000
Revises: 20260125_032900
Create Date: 2026-02-21 12:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260221_120000"
down_revision = "20260125_032900"
branch_labels = None
depends_on = None


def upgrade():
    """Add salary accounting account fields to company table."""
    op.add_column("empresa", sa.Column("codigo_cuenta_debe_salario", sa.String(length=64), nullable=True))
    op.add_column("empresa", sa.Column("descripcion_cuenta_debe_salario", sa.String(length=255), nullable=True))
    op.add_column("empresa", sa.Column("codigo_cuenta_haber_salario", sa.String(length=64), nullable=True))
    op.add_column("empresa", sa.Column("descripcion_cuenta_haber_salario", sa.String(length=255), nullable=True))


def downgrade():
    """Remove salary accounting account fields from company table."""
    op.drop_column("empresa", "descripcion_cuenta_haber_salario")
    op.drop_column("empresa", "codigo_cuenta_haber_salario")
    op.drop_column("empresa", "descripcion_cuenta_debe_salario")
    op.drop_column("empresa", "codigo_cuenta_debe_salario")
