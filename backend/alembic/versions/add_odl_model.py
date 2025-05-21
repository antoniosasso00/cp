"""add_odl_model

Revision ID: add_odl_model
Revises: remove_in_manutenzione_and_reparto_fields
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_odl_model'
down_revision = 'remove_in_manutenzione_and_reparto_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Creazione della tabella odl
    op.create_table('odl',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parte_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.Column('priorita', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.Enum('Preparazione', 'Laminazione', 'Attesa Cura', 'Cura', 'Finito', name='odl_status'), nullable=False, server_default='Preparazione'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parte_id'], ['parti.id'], name='fk_odl_parte_id'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], name='fk_odl_tool_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_odl_id'), 'odl', ['id'], unique=False)
    op.create_index(op.f('ix_odl_parte_id'), 'odl', ['parte_id'], unique=False)
    op.create_index(op.f('ix_odl_tool_id'), 'odl', ['tool_id'], unique=False)


def downgrade():
    # Rimozione della tabella odl
    op.drop_index(op.f('ix_odl_tool_id'), table_name='odl')
    op.drop_index(op.f('ix_odl_parte_id'), table_name='odl')
    op.drop_index(op.f('ix_odl_id'), table_name='odl')
    op.drop_table('odl')
    # Rimozione enum
    op.execute('DROP TYPE odl_status;') 