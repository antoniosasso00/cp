"""add_cavalletto_dimensions_to_autoclavi

Revision ID: add_cavalletto_dims
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cavalletto_dims'
down_revision = '20250613_143457_add_2l_nesting_support_to_autoclavi'  # Basato sulla migrazione precedente
branch_labels = None
depends_on = None

def upgrade():
    """Aggiunge le dimensioni fisiche dei cavalletti alla tabella autoclavi"""
    # Aggiunge colonna cavalletto_width (larghezza fisica in mm)
    op.add_column('autoclavi', sa.Column('cavalletto_width', sa.Float(), nullable=True, default=80.0))
    
    # Aggiunge colonna cavalletto_height (altezza fisica in mm) 
    op.add_column('autoclavi', sa.Column('cavalletto_height', sa.Float(), nullable=True, default=60.0))
    
    # Aggiorna le autoclavi esistenti con valori di default
    op.execute("UPDATE autoclavi SET cavalletto_width = 80.0 WHERE cavalletto_width IS NULL")
    op.execute("UPDATE autoclavi SET cavalletto_height = 60.0 WHERE cavalletto_height IS NULL")

def downgrade():
    """Rimuove le dimensioni fisiche dei cavalletti dalla tabella autoclavi"""
    op.drop_column('autoclavi', 'cavalletto_height')
    op.drop_column('autoclavi', 'cavalletto_width') 