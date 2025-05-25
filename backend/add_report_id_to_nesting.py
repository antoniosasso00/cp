"""
Script per aggiungere la colonna report_id alla tabella nesting_results
per collegare i nesting ai report PDF generati automaticamente.
"""

import sqlite3
import os
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_report_id_column():
    """Aggiunge la colonna report_id alla tabella nesting_results"""
    
    # Percorso del database
    db_path = "carbonpilot.db"
    
    if not os.path.exists(db_path):
        logger.error(f"Database non trovato: {db_path}")
        return False
    
    try:
        # Connessione al database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'report_id' in columns:
            logger.info("La colonna report_id esiste già nella tabella nesting_results")
            return True
        
        # Aggiunge la colonna report_id
        logger.info("Aggiunta della colonna report_id alla tabella nesting_results...")
        cursor.execute("""
            ALTER TABLE nesting_results 
            ADD COLUMN report_id INTEGER REFERENCES reports(id)
        """)
        
        # Crea l'indice per performance
        logger.info("Creazione dell'indice per report_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nesting_results_report_id 
            ON nesting_results(report_id)
        """)
        
        # Commit delle modifiche
        conn.commit()
        logger.info("✅ Colonna report_id aggiunta con successo!")
        
        # Verifica che la colonna sia stata aggiunta
        cursor.execute("PRAGMA table_info(nesting_results)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        if 'report_id' in columns_after:
            logger.info("✅ Verifica completata: colonna report_id presente")
            return True
        else:
            logger.error("❌ Errore: colonna report_id non trovata dopo l'aggiunta")
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

if __name__ == "__main__":
    logger.info("🚀 Avvio migrazione: aggiunta colonna report_id a nesting_results")
    success = add_report_id_column()
    
    if success:
        logger.info("🎉 Migrazione completata con successo!")
    else:
        logger.error("💥 Migrazione fallita!")
        exit(1) 