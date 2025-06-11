#!/usr/bin/env python3
"""
Script per la migrazione degli stati batch al nuovo flusso semplificato
Esegue la migrazione manualmente senza Alembic

DRAFT → SOSPESO → IN_CURA → TERMINATO
"""

import sys
import os
from datetime import datetime
import logging

# Aggiungi il backend al path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.db import engine  # Usa engine direttamente da models.db
from models.batch_nesting import BatchNesting

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_batch_states():
    """Esegue la migrazione degli stati batch"""
    
    print("🚀 MIGRAZIONE STATI BATCH - FLUSSO SEMPLIFICATO")
    print("=" * 60)
    
    # Usa l'engine esistente
    SessionLocal = sessionmaker(bind=engine)
    
    try:
        with SessionLocal() as db:
            # STEP 1: Aggiungi colonne se non esistono
            logger.info("📝 Controllo schema database...")
            
            try:
                # Verifica se le colonne esistono già
                result = db.execute(text("""
                    SELECT COUNT(*) 
                    FROM pragma_table_info('batch_nesting') 
                    WHERE name IN ('caricato_da_utente', 'data_inizio_cura', 'durata_cura_effettiva_minuti')
                """)).scalar()
                
                if result < 3:
                    logger.info("🔧 Aggiunta nuove colonne...")
                    
                    # Aggiungi colonne per timing cura
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN caricato_da_utente TEXT
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN caricato_da_ruolo TEXT
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN data_inizio_cura DATETIME
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN terminato_da_utente TEXT
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN terminato_da_ruolo TEXT
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN data_fine_cura DATETIME
                    """))
                    
                    db.execute(text("""
                        ALTER TABLE batch_nesting 
                        ADD COLUMN durata_cura_effettiva_minuti INTEGER
                    """))
                    
                    db.commit()
                    logger.info("✅ Colonne aggiunte con successo")
                else:
                    logger.info("✅ Colonne già presenti")
                    
            except Exception as e:
                logger.warning(f"⚠️ Errore aggiunta colonne (potrebbero già esistere): {e}")
            
            # STEP 2: Mappa stati esistenti
            logger.info("🔄 Mappatura stati esistenti...")
            
            state_mapping = {
                'draft': 'draft',           # Rimane uguale
                'sospeso': 'sospeso',       # Rimane uguale  
                'confermato': 'sospeso',    # CONFERMATO → SOSPESO (pronto per caricamento)
                'loaded': 'in_cura',       # LOADED → IN_CURA (caricato e in cura)
                'cured': 'in_cura',        # CURED → IN_CURA (ancora in cura)
                'terminato': 'terminato'    # Rimane uguale
            }
            
            total_updated = 0
            for old_state, new_state in state_mapping.items():
                result = db.execute(text("""
                    UPDATE batch_nesting 
                    SET stato = :new_state 
                    WHERE stato = :old_state
                """), {'old_state': old_state, 'new_state': new_state})
                
                if result.rowcount > 0:
                    logger.info(f"   ✅ Mappati {result.rowcount} batch da '{old_state}' → '{new_state}'")
                    total_updated += result.rowcount
            
            db.commit()
            logger.info(f"📊 Totale batch aggiornati: {total_updated}")
            
            # STEP 3: Migra dati temporali
            logger.info("📅 Migrazione dati temporali...")
            
            # Mappa data_completamento → data_fine_cura per batch terminati
            result1 = db.execute(text("""
                UPDATE batch_nesting 
                SET data_fine_cura = data_completamento,
                    durata_cura_effettiva_minuti = durata_ciclo_minuti
                WHERE stato = 'terminato' 
                AND data_completamento IS NOT NULL
                AND data_fine_cura IS NULL
            """))
            
            if result1.rowcount > 0:
                logger.info(f"   📅 Aggiornati {result1.rowcount} batch terminati con timing")
            
            # Per batch in_cura, stima data_inizio_cura da dati esistenti
            result2 = db.execute(text("""
                UPDATE batch_nesting 
                SET data_inizio_cura = COALESCE(data_avvio_cura, data_caricamento, data_conferma)
                WHERE stato = 'in_cura' 
                AND data_inizio_cura IS NULL
            """))
            
            if result2.rowcount > 0:
                logger.info(f"   🔥 Stimato inizio cura per {result2.rowcount} batch attivi")
            
            db.commit()
            
            # STEP 4: Statistiche finali
            logger.info("📊 Statistiche migrazione...")
            
            stati_stats = db.execute(text("""
                SELECT stato, COUNT(*) as count 
                FROM batch_nesting 
                GROUP BY stato 
                ORDER BY count DESC
            """)).fetchall()
            
            for stato, count in stati_stats:
                logger.info(f"   📈 {stato.upper()}: {count} batch")
            
            # Verifica che non ci siano stati invalidi
            invalid_states = db.execute(text("""
                SELECT COUNT(*) as count 
                FROM batch_nesting 
                WHERE stato NOT IN ('draft', 'sospeso', 'in_cura', 'terminato')
            """)).scalar()
            
            if invalid_states > 0:
                logger.error(f"❌ ATTENZIONE: {invalid_states} batch con stati non validi!")
                return False
            
            print("\n" + "=" * 60)
            print("✅ MIGRAZIONE COMPLETATA CON SUCCESSO!")
            print("🆕 Nuovo flusso semplificato attivo:")
            print("   DRAFT → SOSPESO → IN_CURA → TERMINATO")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore durante la migrazione: {e}")
        return False

def rollback_migration():
    """Rollback della migrazione (limitato)"""
    print("⚠️ ROLLBACK MIGRAZIONE")
    print("Il rollback completo non è supportato per sicurezza dati")
    print("Ripristinare dal backup se necessario")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrazione stati batch')
    parser.add_argument('--rollback', action='store_true', help='Esegui rollback (limitato)')
    parser.add_argument('--force', action='store_true', help='Forza esecuzione senza conferma')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
        sys.exit(0)
    
    if not args.force:
        print("🚨 ATTENZIONE: Questa migrazione modificherà la struttura del database")
        print("📋 Operazioni previste:")
        print("   1. Aggiunta colonne per timing cura")
        print("   2. Mappatura stati legacy → nuovo flusso")
        print("   3. Migrazione dati temporali")
        print("   4. Verifica integrità")
        
        confirm = input("\nContinuare? (s/N): ").lower().strip()
        if confirm not in ['s', 'si', 'sì', 'y', 'yes']:
            print("❌ Migrazione annullata")
            sys.exit(1)
    
    # Esegui migrazione
    success = migrate_batch_states()
    sys.exit(0 if success else 1) 