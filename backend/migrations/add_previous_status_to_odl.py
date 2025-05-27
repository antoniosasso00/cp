"""
Migrazione per aggiungere il campo previous_status alla tabella ODL

Revision ID: add_previous_status_odl
Revises: 
Create Date: 2025-05-27 20:00:00.000000
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def upgrade():
    """Aggiunge il campo previous_status alla tabella odl"""
    try:
        # Percorso del database
        db_path = Path(__file__).parent.parent.parent / "carbonpilot.db"
        
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(odl)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"🔍 Colonne trovate nella tabella odl: {columns}")
        
        if 'previous_status' not in columns:
            # Aggiungi la colonna previous_status
            print("📝 Aggiungendo colonna previous_status...")
            cursor.execute("""
                ALTER TABLE odl 
                ADD COLUMN previous_status TEXT 
                CHECK (previous_status IN ('Preparazione', 'Laminazione', 'In Coda', 'Attesa Cura', 'Cura', 'Finito'))
            """)
            
            logger.info("✅ Campo previous_status aggiunto alla tabella odl")
            print("✅ Campo previous_status aggiunto alla tabella odl")
        else:
            logger.info("ℹ️ Campo previous_status già presente nella tabella odl")
            print("ℹ️ Campo previous_status già presente nella tabella odl")
            
            # Verifica che la colonna sia effettivamente utilizzabile
            try:
                cursor.execute("SELECT previous_status FROM odl LIMIT 1")
                print("✅ Colonna previous_status funzionante")
            except Exception as e:
                print(f"❌ Errore nell'accesso alla colonna previous_status: {e}")
                print("🔧 Tentativo di ricreare la colonna...")
                try:
                    cursor.execute("""
                        ALTER TABLE odl 
                        ADD COLUMN previous_status TEXT 
                        CHECK (previous_status IN ('Preparazione', 'Laminazione', 'In Coda', 'Attesa Cura', 'Cura', 'Finito'))
                    """)
                    print("✅ Colonna previous_status ricreata")
                except Exception as e2:
                    print(f"❌ Impossibile ricreare la colonna: {e2}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Errore durante la migrazione: {e}")
        print(f"❌ Errore durante la migrazione: {e}")
        raise

def downgrade():
    """Rimuove il campo previous_status dalla tabella odl"""
    try:
        # Percorso del database
        db_path = Path(__file__).parent.parent.parent / "carbonpilot.db"
        
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # SQLite non supporta DROP COLUMN direttamente, quindi ricreiamo la tabella
        # Per semplicità, lasciamo il campo (è nullable quindi non causa problemi)
        logger.info("⚠️ Downgrade non implementato - il campo previous_status rimarrà nella tabella")
        print("⚠️ Downgrade non implementato - il campo previous_status rimarrà nella tabella")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Errore durante il downgrade: {e}")
        print(f"❌ Errore durante il downgrade: {e}")
        raise

if __name__ == "__main__":
    upgrade() 