"""Add efficiency field to batch_nesting table

Revision ID: 20250128_add_efficiency_batch
Revises: 20250127_add_batch_nesting_table
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250128_add_efficiency_batch'
down_revision = '20250127_add_batch_nesting_table'
branch_labels = None
depends_on = None

def upgrade():
    """Add efficiency field to batch_nesting table"""
    
    # Aggiungi il campo efficiency alla tabella batch_nesting
    op.add_column('batch_nesting', sa.Column('efficiency', sa.Float(), nullable=True, default=0.0))
    
    # Aggiorna tutti i record esistenti con efficiency = 0.0
    op.execute("UPDATE batch_nesting SET efficiency = 0.0 WHERE efficiency IS NULL")

def downgrade():
    """Remove efficiency field from batch_nesting table"""
    
    # Rimuovi il campo efficiency dalla tabella batch_nesting
    op.drop_column('batch_nesting', 'efficiency') 