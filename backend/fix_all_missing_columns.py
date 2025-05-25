#!/usr/bin/env python3
"""
Script per aggiungere tutte le colonne mancanti alla tabella nesting_results
"""

import sqlite3
import logging
from pathlib import Path

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_all_missing_columns():
    """Aggiunge tutte le colonne mancanti alla tabella nesting_results"""
    
    db_path = Path("carbonpilot.db")
    if not db_path.exists():
        logger.error(f"❌ Database non trovato: {db_path}")
        return False
    
    # Colonne che dovrebbero esistere
    required_columns = {
        'confermato_da_ruolo': 'VARCHAR(50)',
        'posizioni_tool': 'JSON',
        'report_id': 'INTEGER'
    }
    
    try:
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica colonne esistenti
        cursor.execute("PRAGMA table_info(nesting_results)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"📋 Colonne esistenti: {existing_columns}")
        
        # Aggiunge colonne mancanti
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                logger.info(f"🔧 Aggiunta colonna '{column_name}' ({column_type})...")
                
                # Per SQLite, JSON viene trattato come TEXT
                if column_type == 'JSON':
                    column_type = 'TEXT'
                
                cursor.execute(f"""
                    ALTER TABLE nesting_results 
                    ADD COLUMN {column_name} {column_type}
                """)
                logger.info(f"✅ Colonna '{column_name}' aggiunta!")
            else:
                logger.info(f"✅ Colonna '{column_name}' già presente")
        
        # Commit delle modifiche
        conn.commit()
        logger.info("✅ Tutte le modifiche salvate!")
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(nesting_results)")
        final_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"📋 Colonne finali: {final_columns}")
        
        # Controlla che tutte le colonne richieste siano presenti
        missing = [col for col in required_columns.keys() if col not in final_columns]
        if missing:
            logger.error(f"❌ Colonne ancora mancanti: {missing}")
            return False
        else:
            logger.info("✅ Tutte le colonne richieste sono presenti!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore durante l'aggiornamento dello schema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logger.info("🚀 Avvio fix completo schema nesting_results...")
    success = fix_all_missing_columns()
    
    if success:
        logger.info("✅ Fix completato con successo!")
    else:
        logger.error("❌ Fix fallito!")
        exit(1) 