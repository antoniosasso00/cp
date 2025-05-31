"""add batch_nesting table

Revision ID: 20250127_add_batch_nesting_table
Revises: add_use_secondary_plane
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250127_add_batch_nesting_table'
down_revision = 'add_use_secondary_plane'
branch_labels = None
depends_on = None

def upgrade():
    """
    Crea la tabella batch_nesting per raggruppare i nesting con parametri salvati
    """
    # Crea l'enum per lo stato del batch nesting
    stato_batch_enum = postgresql.ENUM('sospeso', 'confermato', 'terminato', name='statobatchnestingenum')
    stato_batch_enum.create(op.get_bind())
    
    # Crea la tabella batch_nesting
    op.create_table(
        'batch_nesting',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('nome', sa.String(255), nullable=True),
        sa.Column('stato', stato_batch_enum, nullable=False, default='sospeso'),
        sa.Column('autoclave_id', sa.Integer(), nullable=False),
        sa.Column('odl_ids', sa.JSON(), nullable=True, default=[]),
        sa.Column('configurazione_json', sa.JSON(), nullable=True),
        sa.Column('parametri', sa.JSON(), nullable=True, default={}),
        sa.Column('numero_nesting', sa.Integer(), nullable=True, default=0),
        sa.Column('peso_totale_kg', sa.Integer(), nullable=True, default=0),
        sa.Column('area_totale_utilizzata', sa.Integer(), nullable=True, default=0),
        sa.Column('valvole_totali_utilizzate', sa.Integer(), nullable=True, default=0),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('creato_da_utente', sa.String(100), nullable=True),
        sa.Column('creato_da_ruolo', sa.String(50), nullable=True),
        sa.Column('confermato_da_utente', sa.String(100), nullable=True),
        sa.Column('confermato_da_ruolo', sa.String(50), nullable=True),
        sa.Column('data_conferma', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['autoclave_id'], ['autoclavi.id'], name='fk_batch_nesting_autoclave')
    )
    
    # Crea indici
    op.create_index(op.f('ix_batch_nesting_id'), 'batch_nesting', ['id'], unique=False)
    op.create_index(op.f('ix_batch_nesting_autoclave_id'), 'batch_nesting', ['autoclave_id'], unique=False)
    op.create_index(op.f('ix_batch_nesting_stato'), 'batch_nesting', ['stato'], unique=False)
    op.create_index(op.f('ix_batch_nesting_created_at'), 'batch_nesting', ['created_at'], unique=False)
    
    # Aggiungi la colonna batch_id alla tabella nesting_results per il collegamento
    op.add_column('nesting_results', sa.Column('batch_id', sa.String(36), nullable=True))
    op.create_index(op.f('ix_nesting_results_batch_id'), 'nesting_results', ['batch_id'], unique=False)
    op.create_foreign_key('fk_nesting_results_batch', 'nesting_results', 'batch_nesting', ['batch_id'], ['id'])

def downgrade():
    """
    Rimuove la tabella batch_nesting e le relative relazioni
    """
    # Rimuovi la foreign key e la colonna dalla tabella nesting_results
    op.drop_constraint('fk_nesting_results_batch', 'nesting_results', type_='foreignkey')
    op.drop_index(op.f('ix_nesting_results_batch_id'), table_name='nesting_results')
    op.drop_column('nesting_results', 'batch_id')
    
    # Rimuovi indici della tabella batch_nesting
    op.drop_index(op.f('ix_batch_nesting_created_at'), table_name='batch_nesting')
    op.drop_index(op.f('ix_batch_nesting_stato'), table_name='batch_nesting')
    op.drop_index(op.f('ix_batch_nesting_autoclave_id'), table_name='batch_nesting')
    op.drop_index(op.f('ix_batch_nesting_id'), table_name='batch_nesting')
    
    # Rimuovi la tabella batch_nesting
    op.drop_table('batch_nesting')
    
    # Rimuovi l'enum type
    stato_batch_enum = postgresql.ENUM('sospeso', 'confermato', 'terminato', name='statobatchnestingenum')
    stato_batch_enum.drop(op.get_bind()) 