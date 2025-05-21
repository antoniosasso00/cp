"""add odl parts relationship

Revision ID: add_odl_parts_relationship
Revises: previous_revision
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_odl_parts_relationship'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Creazione della tabella odl_parts
    op.create_table(
        'odl_parts',
        sa.Column('odl_id', sa.Integer(), nullable=False),
        sa.Column('parte_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('status', sa.String(50), nullable=False, default='created'),
        sa.Column('last_updated', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['odl_id'], ['odl.id'], ),
        sa.ForeignKeyConstraint(['parte_id'], ['parti.id'], ),
        sa.PrimaryKeyConstraint('odl_id', 'parte_id')
    )

def downgrade():
    # Rimozione della tabella odl_parts
    op.drop_table('odl_parts') 