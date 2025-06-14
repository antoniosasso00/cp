"""add autoclave cavalletti properties

Revision ID: e7f8a9b1c2d3
Revises: 381101cb6a1c
Create Date: 2025-01-13 17:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7f8a9b1c2d3'
down_revision = '381101cb6a1c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aggiunge i campi relativi ai cavalletti alla tabella autoclavi"""
    
    # Aggiungi campo booleano per indicare se l'autoclave supporta cavalletti
    op.add_column('autoclavi', sa.Column('usa_cavalletti', sa.Boolean(), 
                                        nullable=False, default=False,
                                        doc="Indica se l'autoclave supporta l'utilizzo di cavalletti"))
    
    # Aggiungi altezza standard del cavalletto
    op.add_column('autoclavi', sa.Column('altezza_cavalletto_standard', sa.Float(), 
                                        nullable=True,
                                        doc="Altezza standard del cavalletto per questa autoclave in cm"))
    
    # Aggiungi numero massimo di cavalletti supportati
    op.add_column('autoclavi', sa.Column('max_cavalletti', sa.Integer(), 
                                        nullable=True, default=2,
                                        doc="Numero massimo di cavalletti supportati dall'autoclave"))
    
    # Aggiungi spazio verticale minimo tra cavalletti
    op.add_column('autoclavi', sa.Column('clearance_verticale', sa.Float(), 
                                        nullable=True,
                                        doc="Spazio verticale minimo richiesto tra cavalletti in cm"))


def downgrade() -> None:
    """Rimuove i campi relativi ai cavalletti dalla tabella autoclavi"""
    
    # Rimuovi i campi in ordine inverso
    op.drop_column('autoclavi', 'clearance_verticale')
    op.drop_column('autoclavi', 'max_cavalletti')
    op.drop_column('autoclavi', 'altezza_cavalletto_standard')
    op.drop_column('autoclavi', 'usa_cavalletti') 