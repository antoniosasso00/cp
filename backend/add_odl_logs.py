import sqlite3
import os

def add_odl_logs_table():
    """Aggiunge la tabella odl_logs al database"""
    
    db_path = "carbonpilot.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} non trovato")
        return
    
    # SQL per creare la tabella odl_logs
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS odl_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        odl_id INTEGER NOT NULL,
        evento VARCHAR(100) NOT NULL,
        stato_precedente VARCHAR(50),
        stato_nuovo VARCHAR(50) NOT NULL,
        descrizione TEXT,
        responsabile VARCHAR(100),
        nesting_id INTEGER,
        autoclave_id INTEGER,
        schedule_entry_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (odl_id) REFERENCES odl(id),
        FOREIGN KEY (nesting_id) REFERENCES nesting_results(id),
        FOREIGN KEY (autoclave_id) REFERENCES autoclavi(id),
        FOREIGN KEY (schedule_entry_id) REFERENCES schedule_entries(id)
    );
    """
    
    # Indici per migliorare le performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_odl_id ON odl_logs(odl_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_timestamp ON odl_logs(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_nesting_id ON odl_logs(nesting_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_autoclave_id ON odl_logs(autoclave_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_schedule_entry_id ON odl_logs(schedule_entry_id);"
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crea la tabella
        cursor.execute(create_table_sql)
        print("✅ Tabella odl_logs creata")
        
        # Crea gli indici
        for index_sql in create_indexes_sql:
            cursor.execute(index_sql)
        print("✅ Indici creati")
        
        # Verifica che la tabella sia stata creata
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='odl_logs'")
        if cursor.fetchone():
            print("✅ Verifica completata: tabella odl_logs presente")
            
            # Mostra la struttura
            cursor.execute("PRAGMA table_info(odl_logs)")
            columns = cursor.fetchall()
            print("📋 Struttura tabella odl_logs:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Errore: tabella non trovata")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Creazione tabella odl_logs...")
    add_odl_logs_table()
    print("✅ Completato!") 