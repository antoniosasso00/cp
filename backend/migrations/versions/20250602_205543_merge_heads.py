"""merge_heads

Revision ID: 139cc593a2bd
Revises: 20250127_add_missing_batch_columns, 20250128_add_efficiency_batch
Create Date: 2025-06-02 20:55:43.821829

"""
from alembic import op
import sqlalchemy as sa
pass

# revision identifiers, used by Alembic.
revision = '139cc593a2bd'
down_revision = ('20250127_add_missing_batch_columns', '20250128_add_efficiency_batch')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
