"""add_system_logs_table

Revision ID: add_system_logs_table
Revises: add_schedule_entry_table
Create Date: 2024-12-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_system_logs_table'
down_revision: Union[str, None] = 'add_schedule_entry_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea enum per log level
    log_level_enum = postgresql.ENUM('info', 'warning', 'error', 'critical', name='loglevel')
    log_level_enum.create(op.get_bind())
    
    # Crea enum per event type
    event_type_enum = postgresql.ENUM(
        'odl_state_change', 'nesting_confirm', 'nesting_modify', 'cura_start', 'cura_complete',
        'tool_modify', 'autoclave_modify', 'ciclo_modify', 'backup_create', 'backup_restore',
        'user_login', 'user_logout', 'system_error', name='eventtype'
    )
    event_type_enum.create(op.get_bind())
    
    # Crea enum per user role
    user_role_enum = postgresql.ENUM(
        'admin', 'responsabile', 'autoclavista', 'laminatore', 'sistema', name='userrole'
    )
    user_role_enum.create(op.get_bind())
    
    # Crea tabella system_logs
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('level', log_level_enum, nullable=False, default='info'),
        sa.Column('event_type', event_type_enum, nullable=False),
        sa.Column('user_role', user_role_enum, nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crea indici
    op.create_index(op.f('ix_system_logs_id'), 'system_logs', ['id'], unique=False)
    op.create_index(op.f('ix_system_logs_timestamp'), 'system_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_system_logs_event_type'), 'system_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_system_logs_user_role'), 'system_logs', ['user_role'], unique=False)
    op.create_index(op.f('ix_system_logs_entity_id'), 'system_logs', ['entity_id'], unique=False)


def downgrade() -> None:
    # Rimuovi indici
    op.drop_index(op.f('ix_system_logs_entity_id'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_user_role'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_event_type'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_timestamp'), table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_id'), table_name='system_logs')
    
    # Rimuovi tabella
    op.drop_table('system_logs')
    
    # Rimuovi enum types
    user_role_enum = postgresql.ENUM('admin', 'responsabile', 'autoclavista', 'laminatore', 'sistema', name='userrole')
    user_role_enum.drop(op.get_bind())
    
    event_type_enum = postgresql.ENUM(
        'odl_state_change', 'nesting_confirm', 'nesting_modify', 'cura_start', 'cura_complete',
        'tool_modify', 'autoclave_modify', 'ciclo_modify', 'backup_create', 'backup_restore',
        'user_login', 'user_logout', 'system_error', name='eventtype'
    )
    event_type_enum.drop(op.get_bind())
    
    log_level_enum = postgresql.ENUM('info', 'warning', 'error', 'critical', name='loglevel')
    log_level_enum.drop(op.get_bind()) 