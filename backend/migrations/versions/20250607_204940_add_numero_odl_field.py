"""add_numero_odl_field

Revision ID: 381101cb6a1c
Revises: 139cc593a2bd
Create Date: 2025-06-07 20:49:40.556763

"""
from alembic import op
import sqlalchemy as sa
pass

# revision identifiers, used by Alembic.
revision = '381101cb6a1c'
down_revision = '139cc593a2bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Aggiungi la colonna numero_odl alla tabella odl
    op.add_column('odl', sa.Column('numero_odl', sa.String(length=50), nullable=True))
    
    # Popola i valori esistenti con un numero progressivo basato sull'ID
    # Questo è necessario perché il campo deve essere unique e not null
    op.execute("""
        UPDATE odl 
        SET numero_odl = 'ODL' || LPAD(CAST(id AS TEXT), 6, '0')
        WHERE numero_odl IS NULL
    """)
    
    # Ora rendi la colonna NOT NULL e UNIQUE
    op.alter_column('odl', 'numero_odl', nullable=False)
    op.create_unique_constraint('uq_odl_numero_odl', 'odl', ['numero_odl'])
    op.create_index('ix_odl_numero_odl', 'odl', ['numero_odl'])


def downgrade() -> None:
    # Rimuovi indice e constraint
    op.drop_index('ix_odl_numero_odl', 'odl')
    op.drop_constraint('uq_odl_numero_odl', 'odl', type_='unique')
    
    # Rimuovi la colonna
    op.drop_column('odl', 'numero_odl')
