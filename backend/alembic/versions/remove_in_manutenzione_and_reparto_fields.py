"""remove_in_manutenzione_and_reparto_fields

Revision ID: remove_in_manutenzione_and_reparto_fields
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_in_manutenzione_and_reparto_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Rimuovi colonna in_manutenzione dalla tabella autoclavi
    op.drop_column('autoclavi', 'in_manutenzione')
    
    # Rimuovi colonne temperatura_max e pressione_max dalla tabella cicli_cura
    op.drop_column('cicli_cura', 'temperatura_max')
    op.drop_column('cicli_cura', 'pressione_max')

def downgrade():
    # Ripristina colonna in_manutenzione nella tabella autoclavi
    op.add_column('autoclavi',
        sa.Column('in_manutenzione', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Ripristina colonne temperatura_max e pressione_max nella tabella cicli_cura
    op.add_column('cicli_cura',
        sa.Column('temperatura_max', sa.Float(), nullable=False)
    )
    op.add_column('cicli_cura',
        sa.Column('pressione_max', sa.Float(), nullable=False)
    ) 