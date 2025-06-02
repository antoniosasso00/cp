"""remove second plane columns

Revision ID: remove_second_plane_columns
Revises: add_nesting_improvements
Create Date: 2024-12-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_second_plane_columns'
down_revision = 'add_nesting_improvements'
branch_labels = None
depends_on = None


def upgrade():
    """Rimuovi le colonne relative al secondo piano"""
    # Rimuovi use_secondary_plane dalla tabella autoclavi
    op.drop_column('autoclavi', 'use_secondary_plane')
    
    # Rimuovi area_piano_2 e superficie_piano_2_max dalla tabella nesting_results
    op.drop_column('nesting_results', 'area_piano_2')
    op.drop_column('nesting_results', 'superficie_piano_2_max')


def downgrade():
    """Ripristina le colonne relative al secondo piano"""
    # Ripristina use_secondary_plane nella tabella autoclavi
    op.add_column('autoclavi', sa.Column('use_secondary_plane', sa.Boolean(), 
                                        nullable=False, default=False,
                                        doc="Indica se l'autoclave può utilizzare un piano secondario per aumentare la capacità"))
    
    # Ripristina area_piano_2 e superficie_piano_2_max nella tabella nesting_results
    op.add_column('nesting_results', sa.Column('area_piano_2', sa.Float(), 
                                             default=0.0, doc="Area utilizzata sul piano 2 in cm²"))
    op.add_column('nesting_results', sa.Column('superficie_piano_2_max', sa.Float(), 
                                             nullable=True, doc="Superficie massima configurabile del piano 2 in cm²")) 