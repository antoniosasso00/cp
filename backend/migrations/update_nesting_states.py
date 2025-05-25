#!/usr/bin/env python3
"""
Script di migrazione per aggiornare gli stati del nesting
e aggiungere il campo confermato_da_ruolo

Questo script:
1. Aggiunge la colonna confermato_da_ruolo alla tabella nesting_results
2. Aggiorna gli stati esistenti dal vecchio formato al nuovo formato:
   - "In attesa schedulazione" -> "In sospeso"
   - "Schedulato" -> "Confermato"
   - "Completato" -> "Completato" (rimane uguale)
   - "Annullato" -> "Annullato" (rimane uguale)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models.db import get_database_url
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_nesting_states():
    """Esegue la migrazione degli stati del nesting"""
    
    # Connessione al database
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Inizia una transazione
            trans = conn.begin()
            
            try:
                logger.info("🔄 Inizio migrazione stati nesting...")
                
                # 1. Aggiungi la colonna confermato_da_ruolo se non esiste
                logger.info("📝 Aggiunta colonna confermato_da_ruolo...")
                try:
                    conn.execute(text("""
                        ALTER TABLE nesting_results 
                        ADD COLUMN confermato_da_ruolo VARCHAR(50)
                    """))
                    logger.info("✅ Colonna confermato_da_ruolo aggiunta")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        logger.info("ℹ️ Colonna confermato_da_ruolo già esistente")
                    else:
                        raise e
                
                # 2. Aggiorna gli stati esistenti
                logger.info("🔄 Aggiornamento stati esistenti...")
                
                # Mappa degli stati vecchi -> nuovi
                state_mapping = {
                    "In attesa schedulazione": "In sospeso",
                    "Schedulato": "Confermato",
                    "Completato": "Completato",
                    "Annullato": "Annullato"
                }
                
                for old_state, new_state in state_mapping.items():
                    result = conn.execute(text("""
                        UPDATE nesting_results 
                        SET stato = :new_state 
                        WHERE stato = :old_state
                    """), {"old_state": old_state, "new_state": new_state})
                    
                    if result.rowcount > 0:
                        logger.info(f"✅ Aggiornati {result.rowcount} record da '{old_state}' a '{new_state}'")
                
                # 3. Verifica i risultati
                result = conn.execute(text("SELECT stato, COUNT(*) as count FROM nesting_results GROUP BY stato"))
                logger.info("📊 Stati attuali nel database:")
                for row in result:
                    logger.info(f"   - {row.stato}: {row.count} record")
                
                # Commit della transazione
                trans.commit()
                logger.info("✅ Migrazione completata con successo!")
                
            except Exception as e:
                # Rollback in caso di errore
                trans.rollback()
                logger.error(f"❌ Errore durante la migrazione: {e}")
                raise e
                
    except Exception as e:
        logger.error(f"❌ Errore di connessione al database: {e}")
        raise e

if __name__ == "__main__":
    migrate_nesting_states() 