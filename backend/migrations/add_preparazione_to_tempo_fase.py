"""add_preparazione_to_tempo_fase

Revision ID: add_prep_enum
Revises: 20250524_182522_init_clean
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_prep_enum'
down_revision = '20250524_182522_init_clean'
branch_labels = None
depends_on = None

def upgrade():
    """Aggiunge 'preparazione' all'enum tipo_fase"""
    
    # Per PostgreSQL, dobbiamo aggiungere il nuovo valore all'enum esistente
    op.execute("ALTER TYPE tipo_fase ADD VALUE 'preparazione'")

def downgrade():
    """Rimuove 'preparazione' dall'enum tipo_fase"""
    
    # Per PostgreSQL, è più complesso rimuovere un valore da un enum
    # Dovremmo ricreare l'enum, ma per semplicità non implemento il downgrade
    pass 