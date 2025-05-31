"""add use_secondary_plane to autoclave

Revision ID: add_use_secondary_plane
Revises: 1313c0186228
Create Date: 2025-01-27 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_use_secondary_plane'
down_revision = '1313c0186228'
branch_labels = None
depends_on = None

def upgrade():
    """
    Aggiunge il campo use_secondary_plane alla tabella autoclavi
    """
    # Aggiungi la colonna use_secondary_plane
    op.add_column('autoclavi', sa.Column('use_secondary_plane', sa.Boolean(), nullable=False, default=False))
    
    # Aggiorna i valori esistenti con il default
    op.execute("UPDATE autoclavi SET use_secondary_plane = false WHERE use_secondary_plane IS NULL")

def downgrade():
    """
    Rimuove il campo use_secondary_plane dalla tabella autoclavi
    """
    op.drop_column('autoclavi', 'use_secondary_plane') 