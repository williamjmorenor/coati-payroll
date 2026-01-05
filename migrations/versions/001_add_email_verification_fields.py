"""Add email verification and restricted access configuration fields

Revision ID: 001_email_verification
Revises: 
Create Date: 2026-01-05 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_email_verification'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add email verification fields to usuario table and configuration to configuracion_global table."""
    # Add email verification fields to usuario table
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_verificado', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('fecha_verificacion_email', sa.DateTime(), nullable=True))
    
    # Add restricted access configuration to configuracion_global table
    with op.batch_alter_table('configuracion_global', schema=None) as batch_op:
        batch_op.add_column(sa.Column('permitir_acceso_email_no_verificado', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    """Remove email verification fields from usuario table and configuration from configuracion_global table."""
    # Remove fields from configuracion_global table
    with op.batch_alter_table('configuracion_global', schema=None) as batch_op:
        batch_op.drop_column('permitir_acceso_email_no_verificado')
    
    # Remove fields from usuario table
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_column('fecha_verificacion_email')
        batch_op.drop_column('email_verificado')
