"""add cavalletti table

Revision ID: 20250113_add_cavalletti_table
Revises: 20250127_simplify_batch_states
Create Date: 2025-01-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250113_add_cavalletti_table'
down_revision = '20250127_simplify_batch_states'
branch_labels = None
depends_on = None

def upgrade():
    """
    Crea la tabella cavalletti per i supporti utilizzati nelle autoclavi
    """
    # Crea la tabella cavalletti
    op.create_table(
        'cavalletti',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('codice', sa.String(50), nullable=False),
        sa.Column('altezza', sa.Float(), nullable=False),
        sa.Column('larghezza', sa.Float(), nullable=True),
        sa.Column('profondita', sa.Float(), nullable=True),
        sa.Column('peso', sa.Float(), nullable=True),
        sa.Column('portata_max', sa.Float(), nullable=True),
        sa.Column('autoclave_id', sa.Integer(), nullable=True),
        sa.Column('disponibile', sa.Boolean(), nullable=False, default=True),
        sa.Column('in_manutenzione', sa.Boolean(), nullable=False, default=False),
        sa.Column('materiale', sa.String(100), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['autoclave_id'], ['autoclavi.id'], name='fk_cavalletti_autoclave')
    )
    
    # Crea indici
    op.create_index(op.f('ix_cavalletti_id'), 'cavalletti', ['id'], unique=False)
    op.create_index(op.f('ix_cavalletti_nome'), 'cavalletti', ['nome'], unique=False)
    op.create_index(op.f('ix_cavalletti_codice'), 'cavalletti', ['codice'], unique=True)
    op.create_index(op.f('ix_cavalletti_autoclave_id'), 'cavalletti', ['autoclave_id'], unique=False)

def downgrade():
    """
    Rimuove la tabella cavalletti
    """
    # Rimuovi indici
    op.drop_index(op.f('ix_cavalletti_autoclave_id'), table_name='cavalletti')
    op.drop_index(op.f('ix_cavalletti_codice'), table_name='cavalletti')
    op.drop_index(op.f('ix_cavalletti_nome'), table_name='cavalletti')
    op.drop_index(op.f('ix_cavalletti_id'), table_name='cavalletti')
    
    # Rimuovi la tabella cavalletti
    op.drop_table('cavalletti') 