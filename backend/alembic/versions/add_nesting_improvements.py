"""add nesting improvements

Revision ID: add_nesting_improvements
Revises: add_nesting_result_table
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_nesting_improvements'
down_revision = 'add_nesting_result_table'
branch_labels = None
depends_on = None


def upgrade():
    # Aggiungi dimensioni al catalogo
    op.add_column('cataloghi', sa.Column('lunghezza', sa.Float(), nullable=True, doc='Lunghezza del pezzo in mm'))
    op.add_column('cataloghi', sa.Column('larghezza', sa.Float(), nullable=True, doc='Larghezza del pezzo in mm'))
    op.add_column('cataloghi', sa.Column('altezza', sa.Float(), nullable=True, doc='Altezza del pezzo in mm'))
    
    # Aggiungi campi mancanti al nesting_results
    op.add_column('nesting_results', sa.Column('odl_esclusi_ids', sa.JSON(), nullable=True, default=list, doc='Lista degli ID degli ODL esclusi dal nesting'))
    op.add_column('nesting_results', sa.Column('motivi_esclusione', sa.JSON(), nullable=True, default=list, doc='Lista dei motivi per cui gli ODL sono stati esclusi'))
    op.add_column('nesting_results', sa.Column('stato', sa.Enum('Schedulato', 'In attesa schedulazione', 'Completato', 'Annullato', name='nesting_stato'), nullable=False, default='In attesa schedulazione', doc='Stato corrente del nesting'))
    op.add_column('nesting_results', sa.Column('note', sa.Text(), nullable=True, doc='Note aggiuntive sul nesting'))
    op.add_column('nesting_results', sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now(), onupdate=sa.func.now()))


def downgrade():
    # Rimuovi campi dal nesting_results
    op.drop_column('nesting_results', 'updated_at')
    op.drop_column('nesting_results', 'note')
    op.drop_column('nesting_results', 'stato')
    op.drop_column('nesting_results', 'motivi_esclusione')
    op.drop_column('nesting_results', 'odl_esclusi_ids')
    
    # Rimuovi dimensioni dal catalogo
    op.drop_column('cataloghi', 'altezza')
    op.drop_column('cataloghi', 'larghezza')
    op.drop_column('cataloghi', 'lunghezza')
    
    # Rimuovi l'enum se esiste
    op.execute('DROP TYPE IF EXISTS nesting_stato') 