"""Add nesting parameters and state enum

Revision ID: 20250528_add_nesting_parameters
Revises: 20250527_add_use_secondary_plane
Create Date: 2025-05-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250528_add_nesting_parameters'
down_revision = 'add_use_secondary_plane'
branch_labels = None
depends_on = None

def upgrade():
    """
    Aggiunge i nuovi campi per i parametri personalizzabili del nesting
    e aggiorna l'enum degli stati
    """
    
    # 1. Crea il nuovo enum per gli stati del nesting
    statonesting_enum = postgresql.ENUM(
        'bozza', 'in_sospeso', 'confermato', 'annullato', 'completato',
        name='statonesting',
        create_type=True
    )
    statonesting_enum.create(op.get_bind())
    
    # 2. Aggiungi i nuovi campi per i parametri personalizzabili
    op.add_column('nesting_results', sa.Column('padding_mm', sa.Float(), nullable=True, default=10.0))
    op.add_column('nesting_results', sa.Column('borda_mm', sa.Float(), nullable=True, default=20.0))
    op.add_column('nesting_results', sa.Column('max_valvole_per_autoclave', sa.Integer(), nullable=True))
    op.add_column('nesting_results', sa.Column('rotazione_abilitata', sa.Boolean(), nullable=True, default=True))
    
    # 3. Aggiungi il campo per il ruolo che ha confermato
    op.add_column('nesting_results', sa.Column('confermato_da_ruolo', sa.String(50), nullable=True))
    
    # 4. Aggiungi i nuovi campi statistiche
    op.add_column('nesting_results', sa.Column('peso_totale_kg', sa.Float(), nullable=True, default=0.0))
    op.add_column('nesting_results', sa.Column('area_piano_1', sa.Float(), nullable=True, default=0.0))
    op.add_column('nesting_results', sa.Column('area_piano_2', sa.Float(), nullable=True, default=0.0))
    op.add_column('nesting_results', sa.Column('superficie_piano_2_max', sa.Float(), nullable=True))
    
    # 5. Aggiungi il campo per le posizioni 2D dei tool
    op.add_column('nesting_results', sa.Column('posizioni_tool', sa.JSON(), nullable=True))
    
    # 6. Aggiungi il campo note
    op.add_column('nesting_results', sa.Column('note', sa.Text(), nullable=True))
    
    # 7. Modifica la colonna stato per usare il nuovo enum
    # Prima rimuovi la colonna esistente se esiste
    try:
        op.drop_column('nesting_results', 'stato')
    except:
        pass  # La colonna potrebbe non esistere
    
    # Aggiungi la nuova colonna stato con l'enum
    op.add_column('nesting_results', 
        sa.Column('stato', 
            postgresql.ENUM('bozza', 'in_sospeso', 'confermato', 'annullato', 'completato', 
                          name='statonesting', create_type=False),
            nullable=False,
            default='bozza'
        )
    )
    
    # 8. Aggiorna i valori di default per i campi esistenti
    op.execute("UPDATE nesting_results SET padding_mm = 10.0 WHERE padding_mm IS NULL")
    op.execute("UPDATE nesting_results SET borda_mm = 20.0 WHERE borda_mm IS NULL")
    op.execute("UPDATE nesting_results SET rotazione_abilitata = true WHERE rotazione_abilitata IS NULL")
    op.execute("UPDATE nesting_results SET peso_totale_kg = 0.0 WHERE peso_totale_kg IS NULL")
    op.execute("UPDATE nesting_results SET area_piano_1 = 0.0 WHERE area_piano_1 IS NULL")
    op.execute("UPDATE nesting_results SET area_piano_2 = 0.0 WHERE area_piano_2 IS NULL")
    op.execute("UPDATE nesting_results SET posizioni_tool = '[]' WHERE posizioni_tool IS NULL")
    
    # 9. Rendi i campi NOT NULL dopo aver impostato i valori di default
    op.alter_column('nesting_results', 'padding_mm', nullable=False)
    op.alter_column('nesting_results', 'borda_mm', nullable=False)
    op.alter_column('nesting_results', 'rotazione_abilitata', nullable=False)
    op.alter_column('nesting_results', 'peso_totale_kg', nullable=False)
    op.alter_column('nesting_results', 'area_piano_1', nullable=False)
    op.alter_column('nesting_results', 'area_piano_2', nullable=False)
    op.alter_column('nesting_results', 'posizioni_tool', nullable=False)

def downgrade():
    """
    Rimuove i campi aggiunti e ripristina lo stato precedente
    """
    
    # Rimuovi le colonne aggiunte
    op.drop_column('nesting_results', 'note')
    op.drop_column('nesting_results', 'posizioni_tool')
    op.drop_column('nesting_results', 'superficie_piano_2_max')
    op.drop_column('nesting_results', 'area_piano_2')
    op.drop_column('nesting_results', 'area_piano_1')
    op.drop_column('nesting_results', 'peso_totale_kg')
    op.drop_column('nesting_results', 'confermato_da_ruolo')
    op.drop_column('nesting_results', 'rotazione_abilitata')
    op.drop_column('nesting_results', 'max_valvole_per_autoclave')
    op.drop_column('nesting_results', 'borda_mm')
    op.drop_column('nesting_results', 'padding_mm')
    
    # Ripristina la colonna stato come stringa
    op.drop_column('nesting_results', 'stato')
    op.add_column('nesting_results', sa.Column('stato', sa.String(50), nullable=True, default='In sospeso'))
    
    # Rimuovi l'enum
    op.execute('DROP TYPE IF EXISTS statonesting') 