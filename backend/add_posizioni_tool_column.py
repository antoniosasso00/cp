#!/usr/bin/env python3
"""
Script per aggiungere la colonna posizioni_tool alla tabella nesting_results
"""

import sqlite3
import json
import logging
from pathlib import Path

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_posizioni_tool_column():
    """Aggiunge la colonna posizioni_tool alla tabella nesting_results"""
    
    # Percorso del database
    db_path = Path(__file__).parent / "carbonpilot.db"
    
    if not db_path.exists():
        logger.error(f"Database non trovato: {db_path}")
        return False
    
    try:
        # Connetti al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'posizioni_tool' in columns:
            logger.info("✅ La colonna 'posizioni_tool' esiste già")
            return True
        
        # Aggiungi la colonna
        logger.info("🔧 Aggiunta colonna 'posizioni_tool' alla tabella nesting_results...")
        cursor.execute("""
            ALTER TABLE nesting_results 
            ADD COLUMN posizioni_tool TEXT DEFAULT '[]'
        """)
        
        # Verifica che la colonna sia stata aggiunta
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        if 'posizioni_tool' in columns_after:
            logger.info("✅ Colonna 'posizioni_tool' aggiunta con successo")
            
            # Inizializza tutti i record esistenti con array vuoto
            cursor.execute("UPDATE nesting_results SET posizioni_tool = '[]' WHERE posizioni_tool IS NULL")
            updated_rows = cursor.rowcount
            logger.info(f"📝 Inizializzati {updated_rows} record esistenti con array vuoto")
            
            # Commit delle modifiche
            conn.commit()
            logger.info("💾 Modifiche salvate nel database")
            return True
        else:
            logger.error("❌ Errore: colonna non aggiunta correttamente")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"❌ Errore SQLite: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Errore generico: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verifica che la migrazione sia stata applicata correttamente"""
    
    db_path = Path(__file__).parent / "carbonpilot.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica struttura tabella
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns = cursor.fetchall()
        
        logger.info("📋 Struttura tabella nesting_results:")
        for col in columns:
            logger.info(f"  - {col[1]} ({col[2]})")
        
        # Verifica alcuni record
        cursor.execute("SELECT id, posizioni_tool FROM nesting_results LIMIT 3")
        records = cursor.fetchall()
        
        logger.info("📊 Esempi di record:")
        for record in records:
            logger.info(f"  - ID {record[0]}: posizioni_tool = {record[1]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore nella verifica: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("🚀 Inizio migrazione database per posizioni_tool")
    
    if add_posizioni_tool_column():
        logger.info("✅ Migrazione completata con successo")
        
        logger.info("🔍 Verifica migrazione...")
        if verify_migration():
            logger.info("✅ Verifica completata - tutto OK!")
        else:
            logger.error("❌ Errore nella verifica")
    else:
        logger.error("❌ Migrazione fallita") 