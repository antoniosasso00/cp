"""add_standard_times_and_odl_flag

Revision ID: add_standard_times_and_odl_flag
Revises: add_system_logs_table
Create Date: 2024-01-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_standard_times_and_odl_flag'
down_revision: Union[str, None] = 'add_system_logs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea tabella standard_times
    op.create_table(
        'standard_times',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_number', sa.String(50), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('minutes', sa.Float(), nullable=False),
        sa.Column('note', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['part_number'], ['cataloghi.part_number'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crea indici per standard_times
    op.create_index(op.f('ix_standard_times_id'), 'standard_times', ['id'], unique=False)
    op.create_index(op.f('ix_standard_times_part_number'), 'standard_times', ['part_number'], unique=False)
    op.create_index(op.f('ix_standard_times_phase'), 'standard_times', ['phase'], unique=False)
    
    # Aggiungi campo include_in_std alla tabella odl
    op.add_column('odl', sa.Column('include_in_std', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Rimuovi campo include_in_std dalla tabella odl
    op.drop_column('odl', 'include_in_std')
    
    # Rimuovi indici di standard_times
    op.drop_index(op.f('ix_standard_times_phase'), table_name='standard_times')
    op.drop_index(op.f('ix_standard_times_part_number'), table_name='standard_times')
    op.drop_index(op.f('ix_standard_times_id'), table_name='standard_times')
    
    # Rimuovi tabella standard_times
    op.drop_table('standard_times') 