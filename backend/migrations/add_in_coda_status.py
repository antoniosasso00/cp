"""
Migrazione per aggiungere il nuovo stato "In Coda" e il campo motivo_blocco agli ODL
"""

import sqlite3
import os

def migrate_database():
    """Aggiunge il nuovo stato 'In Coda' e il campo motivo_blocco alla tabella ODL"""
    
    # Percorso del database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'carbonpilot.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Inizio migrazione database...")
        
        # 1. Aggiungi il campo motivo_blocco se non esiste
        try:
            cursor.execute("ALTER TABLE odl ADD COLUMN motivo_blocco TEXT")
            print("✅ Campo 'motivo_blocco' aggiunto alla tabella ODL")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  Campo 'motivo_blocco' già presente")
            else:
                raise e
        
        # 2. Per SQLite, non possiamo modificare direttamente l'ENUM
        # Dobbiamo verificare che il nuovo stato sia gestito correttamente dall'applicazione
        # SQLite non ha vincoli ENUM nativi, quindi il controllo avviene a livello applicativo
        
        print("✅ Migrazione completata con successo!")
        
        # Verifica che la migrazione sia andata a buon fine
        cursor.execute("PRAGMA table_info(odl)")
        columns = cursor.fetchall()
        
        motivo_blocco_exists = any(col[1] == 'motivo_blocco' for col in columns)
        
        if motivo_blocco_exists:
            print("✅ Verifica: campo 'motivo_blocco' presente nella tabella")
        else:
            print("❌ Errore: campo 'motivo_blocco' non trovato")
            
        conn.commit()
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 