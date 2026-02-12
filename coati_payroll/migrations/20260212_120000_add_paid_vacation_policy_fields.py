# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Add paid vacation policy accounting fields.

Revision ID: 20260212_120000
Revises: 20260125_032900
Create Date: 2026-02-12 12:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260212_120000"
down_revision = "20260125_032900"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vacation_policy",
        sa.Column("son_vacaciones_pagadas", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("vacation_policy", sa.Column("cuenta_debito_vacaciones_pagadas", sa.String(length=64), nullable=True))
    op.add_column(
        "vacation_policy",
        sa.Column("descripcion_cuenta_debito_vacaciones_pagadas", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "vacation_policy", sa.Column("cuenta_credito_vacaciones_pagadas", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "vacation_policy",
        sa.Column("descripcion_cuenta_credito_vacaciones_pagadas", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("vacation_policy", "descripcion_cuenta_credito_vacaciones_pagadas")
    op.drop_column("vacation_policy", "cuenta_credito_vacaciones_pagadas")
    op.drop_column("vacation_policy", "descripcion_cuenta_debito_vacaciones_pagadas")
    op.drop_column("vacation_policy", "cuenta_debito_vacaciones_pagadas")
    op.drop_column("vacation_policy", "son_vacaciones_pagadas")
