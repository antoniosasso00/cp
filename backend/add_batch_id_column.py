#!/usr/bin/env python3
"""
Script per aggiungere la colonna batch_id alla tabella nesting_results.
"""

import sys
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_batch_id_column():
    """Aggiunge la colonna batch_id alla tabella nesting_results"""
    try:
        # Percorso del database
        db_path = Path(__file__).parent / "carbonpilot.db"
        
        logger.info(f"🔗 Connessione al database: {db_path}")
        
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns = [column[1] for column in cursor.fetchall()]
        
        logger.info(f"🔍 Colonne trovate nella tabella nesting_results: {columns}")
        
        if 'batch_id' not in columns:
            # Aggiungi la colonna batch_id
            logger.info("📝 Aggiungendo colonna batch_id...")
            cursor.execute("""
                ALTER TABLE nesting_results 
                ADD COLUMN batch_id TEXT 
                REFERENCES batch_nesting(id)
            """)
            
            logger.info("✅ Colonna batch_id aggiunta alla tabella nesting_results")
        else:
            logger.info("ℹ️ Colonna batch_id già presente nella tabella nesting_results")
        
        # Verifica le tabelle create
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"📊 Tabelle nel database: {[table[0] for table in tables]}")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante l'aggiunta della colonna: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Aggiunta colonna batch_id a nesting_results...")
    success = add_batch_id_column()
    
    if success:
        print("🎉 Script completato con successo!")
        sys.exit(0)
    else:
        print("💥 Script fallito!")
        sys.exit(1) 