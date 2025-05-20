"""remove unused fields from Tool and Parte

Revision ID: 20250522_164500
Revises: 983c24c9692a
Create Date: 2025-05-22 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


# revision identifiers, used by Alembic.
revision = '20250522_164500'
down_revision = '983c24c9692a'
branch_labels = None
depends_on = None


def safe_drop_column(table, column):
    """Drop column if exists, silently ignore if doesn't exist"""
    try:
        op.drop_column(table, column)
        print(f"✅ Colonna '{column}' rimossa dalla tabella '{table}'")
    except OperationalError:
        print(f"⚠️ Colonna '{column}' non trovata nella tabella '{table}' o errore nella rimozione")


def upgrade() -> None:
    # Rimuovi campi da Tool
    safe_drop_column('tools', 'data_ultima_manutenzione')
    safe_drop_column('tools', 'max_temperatura')
    safe_drop_column('tools', 'max_pressione')
    safe_drop_column('tools', 'cicli_completati')
    
    # Rimuovi campi da Parte
    safe_drop_column('parti', 'peso')
    safe_drop_column('parti', 'spessore')
    safe_drop_column('parti', 'cliente')


def downgrade() -> None:
    # Ripristina campi in Parte
    op.add_column('parti', sa.Column('cliente', sa.String(length=100), nullable=True))
    op.add_column('parti', sa.Column('spessore', sa.Float(), nullable=True))
    op.add_column('parti', sa.Column('peso', sa.Float(), nullable=True))
    
    # Ripristina campi in Tool
    op.add_column('tools', sa.Column('cicli_completati', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tools', sa.Column('max_pressione', sa.Float(), nullable=True))
    op.add_column('tools', sa.Column('max_temperatura', sa.Float(), nullable=True))
    op.add_column('tools', sa.Column('data_ultima_manutenzione', sa.DateTime(), nullable=True)) 