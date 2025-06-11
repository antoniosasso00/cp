"""simplify batch states to 4 essential states

Revision ID: 20250127_simplify_batch_states
Revises: 20250127_add_batch_nesting_table
Create Date: 2025-01-27 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '20250127_simplify_batch_states'
down_revision = '381101cb6a1c'
branch_labels = None
depends_on = None

def upgrade():
    """
    Semplifica gli stati batch da 6 a 4 stati essenziali:
    - DRAFT: Risultati generati, NON persistiti se non confermati
    - SOSPESO: Confermato dall'operatore, pronto per caricamento  
    - IN_CURA: Autoclave caricata, cura in corso, timing attivo
    - TERMINATO: Cura completata, workflow chiuso
    """
    
    # Connessione database
    conn = op.get_bind()
    
    print("🚀 INIZIO MIGRAZIONE: Semplificazione stati batch")
    
    # === 1. MAPPING STATI LEGACY A NUOVI STATI ===
    
    # Mappa stati legacy ai nuovi stati
    state_mapping = {
        'confermato': 'sospeso',    # confermato → sospeso
        'loaded': 'in_cura',       # loaded → in_cura  
        'cured': 'in_cura'         # cured → in_cura (unificazione)
    }
    
    print("📋 Mappatura stati legacy:")
    for old_state, new_state in state_mapping.items():
        print(f"   {old_state} → {new_state}")
    
    # === 2. AGGIORNA BATCH ESISTENTI ===
    
    # Recupera conteggio stati attuali
    result = conn.execute(text("""
        SELECT stato, COUNT(*) as count 
        FROM batch_nesting 
        GROUP BY stato 
        ORDER BY count DESC
    """)).fetchall()
    
    print(f"📊 Stati batch esistenti:")
    for row in result:
        print(f"   {row[0]}: {row[1]} batch")
    
    # Aggiorna stati uno per uno
    updated_batches = {}
    
    for old_state, new_state in state_mapping.items():
        result = conn.execute(text(f"""
            UPDATE batch_nesting 
            SET stato = :new_state
            WHERE stato = :old_state
        """), {'old_state': old_state, 'new_state': new_state})
        
        if result.rowcount > 0:
            updated_batches[old_state] = result.rowcount
            print(f"✅ {result.rowcount} batch aggiornati: {old_state} → {new_state}")
    
    # === 3. CREA NUOVO ENUM CON 4 STATI ===
    
    # Per SQLite, gli enum sono gestiti come stringhe, nessuna operazione DDL necessaria
    # Ma aggiungiamo un check constraint per validare i nuovi stati
    
    try:
        # Rimuovi constraint vecchio se esiste (ignora errore se non esiste)
        op.drop_constraint('ck_batch_nesting_stato', 'batch_nesting', type_='check')
    except:
        pass  # Constraint potrebbe non esistere
    
    # Aggiungi nuovo constraint per i 4 stati validi
    op.create_check_constraint(
        'ck_batch_nesting_stato_simplified',
        'batch_nesting',
        "stato IN ('draft', 'sospeso', 'in_cura', 'terminato')"
    )
    
    print("✅ Nuovo constraint stati creato: draft, sospeso, in_cura, terminato")
    
    # === 4. VERIFICA FINALE ===
    
    # Conta stati finali
    result = conn.execute(text("""
        SELECT stato, COUNT(*) as count 
        FROM batch_nesting 
        GROUP BY stato 
        ORDER BY count DESC
    """)).fetchall()
    
    print("📊 Stati batch dopo migrazione:")
    total_batches = 0
    for row in result:
        print(f"   {row[0]}: {row[1]} batch")
        total_batches += row[1]
    
    print(f"📊 Totale batch migrati: {total_batches}")
    
    # Verifica che non ci siano stati non validi
    invalid_states = conn.execute(text("""
        SELECT stato, COUNT(*) as count 
        FROM batch_nesting 
        WHERE stato NOT IN ('draft', 'sospeso', 'in_cura', 'terminato')
        GROUP BY stato
    """)).fetchall()
    
    if invalid_states:
        print("⚠️ ATTENZIONE: Stati non validi trovati:")
        for row in invalid_states:
            print(f"   {row[0]}: {row[1]} batch")
        raise Exception("Migrazione fallita: stati non validi presenti")
    
    print("✅ MIGRAZIONE COMPLETATA: Tutti i batch hanno stati validi")
    
    # === 5. RIASSUNTO MIGRAZIONE ===
    
    print(f"\n📋 RIASSUNTO MIGRAZIONE:")
    print(f"   ✅ Stati semplificati: 6 → 4")
    print(f"   ✅ Constraint aggiornato")
    print(f"   ✅ {sum(updated_batches.values())} batch migrati")
    print(f"   ✅ {total_batches} batch totali verificati")
    print(f"   🎯 Nuovi stati: draft, sospeso, in_cura, terminato")

def downgrade():
    """
    Ripristina gli stati precedenti (rollback)
    """
    
    conn = op.get_bind()
    
    print("🔄 ROLLBACK: Ripristino stati batch precedenti")
    
    # Rimuovi constraint semplificato  
    try:
        op.drop_constraint('ck_batch_nesting_stato_simplified', 'batch_nesting', type_='check')
    except:
        pass
    
    # Per il rollback, converte gli stati semplificati in stati legacy
    # Questo è un rollback parziale poiché alcuni dati potrebbero essere persi
    rollback_mapping = {
        'sospeso': 'confermato',  # sospeso → confermato
        'in_cura': 'loaded'       # in_cura → loaded (scegliamo loaded come default)
    }
    
    for new_state, old_state in rollback_mapping.items():
        result = conn.execute(text(f"""
            UPDATE batch_nesting 
            SET stato = :old_state
            WHERE stato = :new_state
        """), {'new_state': new_state, 'old_state': old_state})
        
        if result.rowcount > 0:
            print(f"🔄 {result.rowcount} batch ripristinati: {new_state} → {old_state}")
    
    # Ricrea constraint vecchio
    op.create_check_constraint(
        'ck_batch_nesting_stato',
        'batch_nesting', 
        "stato IN ('sospeso', 'confermato', 'loaded', 'cured', 'terminato')"
    )
    
    print("✅ Rollback completato: stati precedenti ripristinati") 