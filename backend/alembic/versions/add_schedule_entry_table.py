"""add_schedule_entry_table

Revision ID: add_schedule_entry_table
Revises: add_nesting_result_table
Create Date: 2024-07-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_schedule_entry_table'
down_revision: Union[str, None] = 'add_nesting_result_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea tipo enum per status
    schedule_entry_status = postgresql.ENUM('scheduled', 'manual', 'done', name='schedule_entry_status')
    schedule_entry_status.create(op.get_bind())
    
    # Aggiungi tabella schedule_entries
    op.create_table(
        'schedule_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('odl_id', sa.Integer(), nullable=False),
        sa.Column('autoclave_id', sa.Integer(), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('status', schedule_entry_status, nullable=False, default='scheduled'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('priority_override', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['odl_id'], ['odl.id'], ),
        sa.ForeignKeyConstraint(['autoclave_id'], ['autoclavi.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_entries_id'), 'schedule_entries', ['id'], unique=False)
    op.create_index(op.f('ix_schedule_entries_odl_id'), 'schedule_entries', ['odl_id'], unique=False)
    op.create_index(op.f('ix_schedule_entries_autoclave_id'), 'schedule_entries', ['autoclave_id'], unique=False)


def downgrade() -> None:
    # Rimuovi tabella schedule_entries
    op.drop_index(op.f('ix_schedule_entries_autoclave_id'), table_name='schedule_entries')
    op.drop_index(op.f('ix_schedule_entries_odl_id'), table_name='schedule_entries')
    op.drop_index(op.f('ix_schedule_entries_id'), table_name='schedule_entries')
    op.drop_table('schedule_entries')
    
    # Rimuovi tipo enum
    schedule_entry_status = postgresql.ENUM('scheduled', 'manual', 'done', name='schedule_entry_status')
    schedule_entry_status.drop(op.get_bind()) 