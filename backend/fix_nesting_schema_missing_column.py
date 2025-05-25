#!/usr/bin/env python3
"""
Script per aggiungere la colonna mancante 'confermato_da_ruolo' alla tabella nesting_results
"""

import sqlite3
import logging
from pathlib import Path

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_nesting_schema():
    """Aggiunge la colonna confermato_da_ruolo se mancante"""
    
    db_path = Path("carbonpilot.db")
    if not db_path.exists():
        logger.error(f"❌ Database non trovato: {db_path}")
        return False
    
    try:
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'confermato_da_ruolo' in columns:
            logger.info("✅ La colonna 'confermato_da_ruolo' esiste già")
            return True
        
        # Aggiunge la colonna mancante
        logger.info("🔧 Aggiunta colonna 'confermato_da_ruolo' alla tabella nesting_results...")
        cursor.execute("""
            ALTER TABLE nesting_results 
            ADD COLUMN confermato_da_ruolo VARCHAR(50)
        """)
        
        # Commit delle modifiche
        conn.commit()
        logger.info("✅ Colonna 'confermato_da_ruolo' aggiunta con successo!")
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'confermato_da_ruolo' in columns_after:
            logger.info("✅ Verifica completata: colonna presente")
            return True
        else:
            logger.error("❌ Errore: colonna non trovata dopo l'aggiunta")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante l'aggiornamento dello schema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logger.info("🚀 Avvio fix schema nesting_results...")
    success = fix_nesting_schema()
    
    if success:
        logger.info("✅ Fix completato con successo!")
    else:
        logger.error("❌ Fix fallito!")
        exit(1) 