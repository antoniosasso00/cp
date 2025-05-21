"""remove tool in_manutenzione

Revision ID: a99248a67c2a4
Revises: 99248a67c2a3
Create Date: 2025-05-20 22:05:28.497769

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a99248a67c2a4'
down_revision = '99248a67c2a3'
branch_labels = None
depends_on = None


def upgrade():
    # Rimuovi la colonna in_manutenzione dalla tabella tools
    op.drop_column('tools', 'in_manutenzione')


def downgrade():
    # Aggiungi nuovamente la colonna in_manutenzione alla tabella tools
    op.add_column('tools', sa.Column('in_manutenzione', sa.Boolean(), nullable=False, server_default=sa.text('false'))) 