"""add_nesting_result_table

Revision ID: add_nesting_result_table
Revises: add_odl_model
Create Date: 2024-07-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_nesting_result_table'
down_revision: Union[str, None] = 'add_odl_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aggiungi tabella nesting_results
    op.create_table(
        'nesting_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('autoclave_id', sa.Integer(), nullable=True),
        sa.Column('odl_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('area_utilizzata', sa.Float(), nullable=True),
        sa.Column('area_totale', sa.Float(), nullable=True),
        sa.Column('valvole_utilizzate', sa.Integer(), nullable=True),
        sa.Column('valvole_totali', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['autoclave_id'], ['autoclavi.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nesting_results_autoclave_id'), 'nesting_results', ['autoclave_id'], unique=False)
    op.create_index(op.f('ix_nesting_results_id'), 'nesting_results', ['id'], unique=False)
    
    # Aggiungi tabella nesting_result_odl (associazione many-to-many)
    op.create_table(
        'nesting_result_odl',
        sa.Column('nesting_result_id', sa.Integer(), nullable=False),
        sa.Column('odl_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['nesting_result_id'], ['nesting_results.id'], ),
        sa.ForeignKeyConstraint(['odl_id'], ['odl.id'], ),
        sa.PrimaryKeyConstraint('nesting_result_id', 'odl_id')
    )


def downgrade() -> None:
    # Rimuovi tabella nesting_result_odl
    op.drop_table('nesting_result_odl')
    
    # Rimuovi tabella nesting_results
    op.drop_index(op.f('ix_nesting_results_id'), table_name='nesting_results')
    op.drop_index(op.f('ix_nesting_results_autoclave_id'), table_name='nesting_results')
    op.drop_table('nesting_results') 