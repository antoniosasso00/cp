"""
Migrazione: Semplificazione Stati Batch Nesting 
Data: 23 Dicembre 2024
Obiettivo: Implementa il nuovo flusso semplificato DRAFT → SOSPESO → IN_CURA → TERMINATO

Modifiche Schema:
1. Aggiunge campi timing cura specifici
2. Mappa stati esistenti al nuovo flusso 
3. Pulisce dati legacy
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    """Migrazione al nuovo schema semplificato"""
    
    # ========== STEP 1: AGGIUNGI NUOVI CAMPI ==========
    print("📝 Aggiunta nuovi campi per timing cura...")
    
    # Campi specifici per caricamento autoclave (SOSPESO → IN_CURA)
    op.add_column('batch_nesting', sa.Column('caricato_da_utente', sa.String(100), nullable=True,
                                             comment='ID utente che ha caricato autoclave'))
    op.add_column('batch_nesting', sa.Column('caricato_da_ruolo', sa.String(50), nullable=True,
                                             comment='Ruolo utente che ha caricato autoclave'))
    op.add_column('batch_nesting', sa.Column('data_inizio_cura', sa.DateTime, nullable=True,
                                             comment='Data/ora inizio cura (SOSPESO → IN_CURA)'))
    
    # Campi specifici per terminazione (IN_CURA → TERMINATO)
    op.add_column('batch_nesting', sa.Column('terminato_da_utente', sa.String(100), nullable=True,
                                             comment='ID utente che ha terminato cura'))
    op.add_column('batch_nesting', sa.Column('terminato_da_ruolo', sa.String(50), nullable=True,
                                             comment='Ruolo utente che ha terminato cura'))
    op.add_column('batch_nesting', sa.Column('data_fine_cura', sa.DateTime, nullable=True,
                                             comment='Data/ora fine cura (IN_CURA → TERMINATO)'))
    op.add_column('batch_nesting', sa.Column('durata_cura_effettiva_minuti', sa.Integer, nullable=True,
                                             comment='Durata cura in minuti (calcolata automaticamente)'))
    
    # ========== STEP 2: MAPPA STATI ESISTENTI ==========
    print("🔄 Mappatura stati esistenti al nuovo flusso...")
    
    connection = op.get_bind()
    
    # Mappa stati legacy al nuovo sistema
    state_mapping = {
        'draft': 'draft',           # Rimane uguale
        'sospeso': 'sospeso',       # Rimane uguale  
        'confermato': 'sospeso',    # CONFERMATO → SOSPESO (pronto per caricamento)
        'loaded': 'in_cura',       # LOADED → IN_CURA (caricato e in cura)
        'cured': 'in_cura',        # CURED → IN_CURA (ancora in cura)
        'terminato': 'terminato'    # Rimane uguale
    }
    
    for old_state, new_state in state_mapping.items():
        result = connection.execute(
            sa.text(f"""
                UPDATE batch_nesting 
                SET stato = :new_state 
                WHERE stato = :old_state
            """),
            {'old_state': old_state, 'new_state': new_state}
        )
        if result.rowcount > 0:
            print(f"   ✅ Mappati {result.rowcount} batch da '{old_state}' → '{new_state}'")
    
    # ========== STEP 3: MIGRA DATI TEMPORALI ==========
    print("📅 Migrazione dati temporali...")
    
    # Mappa data_completamento → data_fine_cura per batch terminati
    connection.execute(
        sa.text("""
            UPDATE batch_nesting 
            SET data_fine_cura = data_completamento,
                durata_cura_effettiva_minuti = durata_ciclo_minuti
            WHERE stato = 'terminato' 
            AND data_completamento IS NOT NULL
        """)
    )
    
    # Per batch in_cura, stima data_inizio_cura da dati esistenti
    connection.execute(
        sa.text("""
            UPDATE batch_nesting 
            SET data_inizio_cura = COALESCE(data_avvio_cura, data_caricamento, data_conferma)
            WHERE stato = 'in_cura' 
            AND data_inizio_cura IS NULL
        """)
    )
    
    print("   ✅ Dati temporali migrati")
    
    # ========== STEP 4: CLEANUP STATISTICHE ==========
    print("📊 Aggiornamento statistiche...")
    
    # Conta batch per nuovo stato
    stati_stats = connection.execute(
        sa.text("SELECT stato, COUNT(*) as count FROM batch_nesting GROUP BY stato")
    ).fetchall()
    
    for stato, count in stati_stats:
        print(f"   📈 {stato.upper()}: {count} batch")
    
    print("✅ Migrazione completata - Nuovo flusso semplificato attivo!")

def downgrade():
    """Rollback al sistema precedente (non implementato per sicurezza)"""
    print("⚠️  DOWNGRADE NON SUPPORTATO")
    print("   Il nuovo flusso semplificato non è reversibile")
    print("   Backup del database raccomandato prima della migrazione")
    raise NotImplementedError("Downgrade non supportato per sicurezza dati")

# ========== UTILITÀ PER VERIFICA ==========

def verify_migration():
    """Verifica che la migrazione sia andata a buon fine"""
    connection = op.get_bind()
    
    # Verifica che non ci siano più stati legacy
    legacy_states = connection.execute(
        sa.text("""
            SELECT COUNT(*) as count 
            FROM batch_nesting 
            WHERE stato NOT IN ('draft', 'sospeso', 'in_cura', 'terminato')
        """)
    ).scalar()
    
    if legacy_states > 0:
        print(f"⚠️  ATTENZIONE: {legacy_states} batch con stati non validi!")
        return False
    
    print("✅ Verifica migrazione: SUCCESSO")
    return True

if __name__ == "__main__":
    print("🚀 Migrazione Batch Nesting - Flusso Semplificato")
    print("   Eseguire con: alembic upgrade head")
    print("   Backup raccomandato prima dell'esecuzione") 