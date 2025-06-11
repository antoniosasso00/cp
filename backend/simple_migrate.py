#!/usr/bin/env python3
"""
Script semplificato per migrare solo gli stati batch
DRAFT → SOSPESO → IN_CURA → TERMINATO
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_states_only():
    """Mappa solo gli stati senza toccare le colonne"""
    
    print("🚀 MIGRAZIONE SEMPLIFICATA - SOLO STATI")
    print("=" * 50)
    
    SessionLocal = sessionmaker(bind=engine)
    
    try:
        with SessionLocal() as db:
            # Verifica stati esistenti
            logger.info("📊 Stati batch attuali:")
            current_states = db.execute(text("""
                SELECT stato, COUNT(*) as count 
                FROM batch_nesting 
                GROUP BY stato 
                ORDER BY count DESC
            """)).fetchall()
            
            for stato, count in current_states:
                logger.info(f"   {stato}: {count} batch")
            
            # Mappa stati legacy al nuovo sistema
            state_mapping = {
                'confermato': 'sospeso',    # CONFERMATO → SOSPESO
                'loaded': 'in_cura',       # LOADED → IN_CURA
                'cured': 'in_cura',        # CURED → IN_CURA (ancora in cura)
            }
            
            total_updated = 0
            for old_state, new_state in state_mapping.items():
                result = db.execute(text("""
                    UPDATE batch_nesting 
                    SET stato = :new_state 
                    WHERE stato = :old_state
                """), {'old_state': old_state, 'new_state': new_state})
                
                if result.rowcount > 0:
                    logger.info(f"✅ Mappati {result.rowcount} batch: '{old_state}' → '{new_state}'")
                    total_updated += result.rowcount
            
            db.commit()
            
            # Verifica stati finali
            logger.info("\n📊 Stati batch dopo migrazione:")
            final_states = db.execute(text("""
                SELECT stato, COUNT(*) as count 
                FROM batch_nesting 
                GROUP BY stato 
                ORDER BY count DESC
            """)).fetchall()
            
            for stato, count in final_states:
                logger.info(f"   {stato}: {count} batch")
            
            # Verifica che non ci siano stati invalidi
            invalid_states = db.execute(text("""
                SELECT stato, COUNT(*) as count 
                FROM batch_nesting 
                WHERE stato NOT IN ('draft', 'sospeso', 'in_cura', 'terminato')
                GROUP BY stato
            """)).fetchall()
            
            if invalid_states:
                logger.warning("⚠️ Stati non validi trovati:")
                for stato, count in invalid_states:
                    logger.warning(f"   {stato}: {count} batch")
            else:
                logger.info("✅ Tutti gli stati sono validi")
            
            print(f"\n✅ MIGRAZIONE COMPLETATA - {total_updated} batch aggiornati")
            print("🆕 Flusso attivo: DRAFT → SOSPESO → IN_CURA → TERMINATO")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    migrate_states_only() 