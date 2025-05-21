"""aggiunta tabelle nesting

Revision ID: b99248a67c2a5
Revises: a99248a67c2a4
Create Date: 2025-05-21 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'b99248a67c2a5'
down_revision = 'a99248a67c2a4'
branch_labels = None
depends_on = None


def upgrade():
    # Tabella nesting_params
    op.create_table(
        'nesting_params',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('peso_valvole', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('peso_area', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('peso_priorita', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('spazio_minimo_mm', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('attivo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('descrizione', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    
    op.create_index('ix_nesting_params_id', 'nesting_params', ['id'], unique=False)
    
    # Tabella nesting_results
    op.create_table(
        'nesting_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codice', sa.String(length=50), nullable=False),
        sa.Column('autoclave_id', sa.Integer(), nullable=False),
        sa.Column('confermato', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_conferma', sa.DateTime(timezone=True), nullable=True),
        sa.Column('area_totale_mm2', sa.Float(), nullable=False),
        sa.Column('area_utilizzata_mm2', sa.Float(), nullable=False),
        sa.Column('efficienza_area', sa.Float(), nullable=False),
        sa.Column('valvole_totali', sa.Integer(), nullable=False),
        sa.Column('valvole_utilizzate', sa.Integer(), nullable=False),
        sa.Column('layout', JSONB(), nullable=False),
        sa.Column('odl_ids', JSONB(), nullable=False),
        sa.Column('generato_manualmente', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['autoclave_id'], ['autoclavi.id'], name='fk_autoclave'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codice')
    )
    
    op.create_index('ix_nesting_results_id', 'nesting_results', ['id'], unique=False)
    
    # Inserisci un set di parametri default
    op.execute("""
        INSERT INTO nesting_params (nome, peso_valvole, peso_area, peso_priorita, spazio_minimo_mm, attivo, descrizione)
        VALUES ('Configurazione Default', 2.0, 3.0, 5.0, 30.0, TRUE, 'Configurazione predefinita del sistema')
        ON CONFLICT (nome) DO NOTHING
    """)


def downgrade():
    op.drop_index('ix_nesting_results_id', table_name='nesting_results')
    op.drop_table('nesting_results')
    op.drop_index('ix_nesting_params_id', table_name='nesting_params')
    op.drop_table('nesting_params') 