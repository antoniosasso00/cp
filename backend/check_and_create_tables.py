#!/usr/bin/env python3
"""
Script per verificare e creare le tabelle necessarie.
"""

import sqlite3
import os

def main():
    # Connetti al database
    db_path = 'carbonpilot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica tabelle esistenti
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelle esistenti: {tables}")
        
        # Verifica se standard_times esiste
        if 'standard_times' not in tables:
            print("🔨 Creazione tabella standard_times...")
            cursor.execute("""
                CREATE TABLE standard_times (
                    id INTEGER PRIMARY KEY,
                    part_number VARCHAR(50) NOT NULL,
                    phase VARCHAR(50) NOT NULL,
                    minutes FLOAT NOT NULL,
                    note VARCHAR(500),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (part_number) REFERENCES cataloghi(part_number)
                )
            """)
            
            # Crea indici
            cursor.execute("CREATE INDEX ix_standard_times_id ON standard_times(id)")
            cursor.execute("CREATE INDEX ix_standard_times_part_number ON standard_times(part_number)")
            cursor.execute("CREATE INDEX ix_standard_times_phase ON standard_times(phase)")
            print("✅ Tabella standard_times creata!")
        else:
            print("✅ Tabella standard_times già esistente")
        
        # Verifica campo include_in_std in odl
        cursor.execute("PRAGMA table_info(odl)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'include_in_std' not in columns:
            print("➕ Aggiunta campo include_in_std alla tabella odl...")
            cursor.execute("ALTER TABLE odl ADD COLUMN include_in_std BOOLEAN NOT NULL DEFAULT 1")
            print("✅ Campo include_in_std aggiunto!")
        else:
            print("✅ Campo include_in_std già presente")
        
        # Commit e chiudi
        conn.commit()
        print("🎯 Operazioni completate con successo!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 