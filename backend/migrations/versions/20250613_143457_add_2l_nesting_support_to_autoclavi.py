"""Add 2L nesting support to autoclavi

Revision ID: 59e033c7fb6a
Revises: 20250127_simplify_batch_states
Create Date: 2025-06-13 14:34:57.481390

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '59e033c7fb6a'
down_revision = '20250127_simplify_batch_states'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Aggiungi campi per supporto nesting 2L alle autoclavi"""
    
    # Aggiungi usa_cavalletti - flag principale per abilitare 2L
    op.add_column('autoclavi', sa.Column('usa_cavalletti', sa.Boolean(), 
                                        nullable=False, default=False,
                                        doc="Indica se l'autoclave supporta l'utilizzo di cavalletti"))
    
    # Aggiungi altezza_cavalletto_standard - altezza cavalletti in mm
    op.add_column('autoclavi', sa.Column('altezza_cavalletto_standard', sa.Float(), 
                                        nullable=True,
                                        doc="Altezza standard del cavalletto per questa autoclave in mm"))
    
    # Aggiungi max_cavalletti - numero massimo cavalletti supportati
    op.add_column('autoclavi', sa.Column('max_cavalletti', sa.Integer(), 
                                        nullable=True, default=2,
                                        doc="Numero massimo di cavalletti supportati dall'autoclave"))
    
    # Aggiungi clearance_verticale - spazio minimo tra livelli in mm
    op.add_column('autoclavi', sa.Column('clearance_verticale', sa.Float(), 
                                        nullable=True,
                                        doc="Spazio verticale minimo richiesto tra cavalletti in mm"))
    
    # Aggiorna configurazioni iniziali
    # PANINI: Autoclave grande con supporto cavalletti
    op.execute("""
        UPDATE autoclavi 
        SET usa_cavalletti = 1, 
            altezza_cavalletto_standard = 100.0,
            max_cavalletti = 4,
            clearance_verticale = 50.0
        WHERE nome LIKE '%PANINI%'
    """)
    
    # ISMAR: Autoclave media con supporto cavalletti limitato  
    op.execute("""
        UPDATE autoclavi 
        SET usa_cavalletti = 1, 
            altezza_cavalletto_standard = 80.0,
            max_cavalletti = 2,
            clearance_verticale = 40.0
        WHERE nome LIKE '%ISMAR%'
    """)
    
    # MAROSO: Solo piano base (nessun cavalletto)
    op.execute("""
        UPDATE autoclavi 
        SET usa_cavalletti = 0, 
            altezza_cavalletto_standard = NULL,
            max_cavalletti = 0,
            clearance_verticale = NULL
        WHERE nome LIKE '%MAROSO%'
    """)


def downgrade() -> None:
    """Rimuovi campi supporto nesting 2L"""
    op.drop_column('autoclavi', 'clearance_verticale')
    op.drop_column('autoclavi', 'max_cavalletti')
    op.drop_column('autoclavi', 'altezza_cavalletto_standard')
    op.drop_column('autoclavi', 'usa_cavalletti')
