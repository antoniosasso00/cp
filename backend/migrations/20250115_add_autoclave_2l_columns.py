"""add autoclave 2L columns

Revision ID: 20250115_add_autoclave_2l_columns
Revises: 20250113_add_cavalletti_table
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250115_add_autoclave_2l_columns'
down_revision = '20250113_add_cavalletti_table'
branch_labels = None
depends_on = None

def upgrade():
    """
    Aggiunge le colonne per il sistema cavalletti 2L alla tabella autoclavi
    """
    # Aggiungi le colonne per il sistema 2L
    with op.batch_alter_table('autoclavi', schema=None) as batch_op:
        batch_op.add_column(sa.Column('usa_cavalletti', sa.Boolean(), nullable=False, default=False, 
                                     comment="Indica se l'autoclave supporta l'utilizzo di cavalletti"))
        batch_op.add_column(sa.Column('altezza_cavalletto_standard', sa.Float(), nullable=True, 
                                     comment="Altezza standard del cavalletto per questa autoclave in mm"))
        batch_op.add_column(sa.Column('max_cavalletti', sa.Integer(), nullable=True, 
                                     comment="Numero massimo di cavalletti supportati dall'autoclave"))
        batch_op.add_column(sa.Column('clearance_verticale', sa.Float(), nullable=True, 
                                     comment="Spazio verticale minimo richiesto tra cavalletti in mm"))

def downgrade():
    """
    Rimuove le colonne del sistema cavalletti 2L dalla tabella autoclavi
    """
    with op.batch_alter_table('autoclavi', schema=None) as batch_op:
        batch_op.drop_column('clearance_verticale')
        batch_op.drop_column('max_cavalletti')
        batch_op.drop_column('altezza_cavalletto_standard')
        batch_op.drop_column('usa_cavalletti') 