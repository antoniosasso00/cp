#!/usr/bin/env python3
"""
Script per creare manualmente la tabella standard_times e aggiungere il campo include_in_std alla tabella odl.
"""

import sys
import os
from sqlalchemy import create_engine, text
from models.db import get_database_url

def create_tables():
    """
    Crea la tabella standard_times e aggiunge il campo include_in_std alla tabella odl.
    """
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Crea la tabella standard_times
            print("🔨 Creazione tabella standard_times...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS standard_times (
                    id INTEGER PRIMARY KEY,
                    part_number VARCHAR(50) NOT NULL,
                    phase VARCHAR(50) NOT NULL,
                    minutes FLOAT NOT NULL,
                    note VARCHAR(500),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (part_number) REFERENCES cataloghi(part_number)
                )
            """))
            
            # Crea gli indici
            print("📊 Creazione indici per standard_times...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_standard_times_id ON standard_times(id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_standard_times_part_number ON standard_times(part_number)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_standard_times_phase ON standard_times(phase)"))
            
            # Verifica se il campo include_in_std esiste già nella tabella odl
            print("🔍 Verifica campo include_in_std nella tabella odl...")
            result = conn.execute(text("PRAGMA table_info(odl)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'include_in_std' not in columns:
                print("➕ Aggiunta campo include_in_std alla tabella odl...")
                conn.execute(text("ALTER TABLE odl ADD COLUMN include_in_std BOOLEAN NOT NULL DEFAULT 1"))
            else:
                print("✅ Campo include_in_std già presente nella tabella odl")
            
            # Commit delle modifiche
            conn.commit()
            
            print("✅ Tabelle create/aggiornate con successo!")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante la creazione delle tabelle: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 Avvio script di creazione tabelle...")
    print("=" * 50)
    
    success = create_tables()
    
    print("=" * 50)
    if success:
        print("✅ Script completato con successo!")
    else:
        print("❌ Script completato con errori!")
        sys.exit(1)

if __name__ == "__main__":
    main() 