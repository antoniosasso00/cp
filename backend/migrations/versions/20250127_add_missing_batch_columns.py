"""add missing batch_nesting columns

Revision ID: 20250127_add_missing_batch_columns
Revises: 20250127_add_batch_nesting_table
Create Date: 2025-01-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250127_add_missing_batch_columns'
down_revision = '20250127_add_batch_nesting_table'
branch_labels = None
depends_on = None

def upgrade():
    """
    Aggiunge le colonne mancanti alla tabella batch_nesting
    """
    # Aggiungi data_completamento
    op.add_column('batch_nesting', sa.Column('data_completamento', sa.DateTime(), nullable=True))
    
    # Aggiungi durata_ciclo_minuti
    op.add_column('batch_nesting', sa.Column('durata_ciclo_minuti', sa.Integer(), nullable=True))

def downgrade():
    """
    Rimuove le colonne aggiunte
    """
    op.drop_column('batch_nesting', 'durata_ciclo_minuti')
    op.drop_column('batch_nesting', 'data_completamento') 