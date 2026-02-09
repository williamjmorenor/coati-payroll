# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Initial migration - mark existing database schema

Revision ID: 20260125_032900
Revises:
Create Date: 2026-01-25 03:29:00

This is the initial migration that marks the existing database schema as the base.
This migration doesn't create or modify any tables - it assumes that the database
was already initialized using db.create_all() before implementing flask-alembic.

For new databases, the schema will be created by db.create_all() in the
ensure_database_initialized() function, and then this migration will be stamped
as 'head' to mark the database as up to date.

For existing databases, this migration should be stamped as 'head' without running
any actual migrations, as the database already contains all the tables.
"""

# revision identifiers, used by Alembic.
revision = "20260125_032900"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade to this revision.

    This is a no-op migration because we assume the database schema was already
    created by db.create_all(). This migration simply marks the schema version.
    """
    return None


def downgrade():
    """Downgrade from this revision.

    This is a no-op migration. Downgrading from the initial migration would
    require dropping all tables, which should be done with db.drop_all() instead.
    """
    return None
