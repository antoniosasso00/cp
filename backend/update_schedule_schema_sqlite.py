#!/usr/bin/env python3
"""
Script per aggiornare lo schema del database SQLite con le nuove funzionalità di scheduling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.db import get_database_url
from models import Base
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
from models.tempo_produzione import TempoProduzione

def update_database_schema():
    """Aggiorna lo schema del database SQLite con le nuove funzionalità."""
    
    # Crea il motore del database
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔄 Aggiornamento schema database SQLite per le nuove funzionalità di scheduling...")
    
    try:
        with engine.connect() as conn:
            # Inizia una transazione
            trans = conn.begin()
            
            try:
                # 1. Aggiungi le nuove colonne alla tabella schedule_entries se non esistono
                print("📝 Aggiunta nuove colonne alla tabella schedule_entries...")
                
                new_columns = [
                    ("schedule_type", "VARCHAR(50) DEFAULT 'odl_specifico'"),
                    ("categoria", "VARCHAR(100)"),
                    ("sotto_categoria", "VARCHAR(100)"),
                    ("is_recurring", "BOOLEAN DEFAULT 0"),
                    ("recurring_frequency", "VARCHAR(50)"),
                    ("pieces_per_month", "INTEGER"),
                    ("parent_schedule_id", "INTEGER"),
                    ("note", "TEXT"),
                    ("estimated_duration_minutes", "INTEGER")
                ]
                
                for column_name, column_def in new_columns:
                    try:
                        # Controlla se la colonna esiste già
                        result = conn.execute(text(f"PRAGMA table_info(schedule_entries)"))
                        existing_columns = [row[1] for row in result]
                        
                        if column_name not in existing_columns:
                            conn.execute(text(f"ALTER TABLE schedule_entries ADD COLUMN {column_name} {column_def}"))
                            print(f"  ✅ Aggiunta colonna: {column_name}")
                        else:
                            print(f"  ⚠️  Colonna {column_name} già esistente")
                    except Exception as e:
                        print(f"  ⚠️  Errore nell'aggiunta colonna {column_name}: {e}")
                
                # 2. Modifica le colonne per renderle nullable se necessario
                print("📝 Verifica nullable per colonne esistenti...")
                
                # Per SQLite, non possiamo modificare direttamente le colonne
                # Verifichiamo solo che le colonne esistano
                result = conn.execute(text("PRAGMA table_info(schedule_entries)"))
                columns_info = list(result)
                print(f"  ℹ️  Colonne attuali in schedule_entries: {len(columns_info)}")
                
                # 3. Crea la tabella tempi_produzione se non esiste
                print("📝 Creazione tabella tempi_produzione...")
                
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS tempi_produzione (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_number VARCHAR(100),
                    categoria VARCHAR(100),
                    sotto_categoria VARCHAR(100),
                    tempo_medio_minuti REAL NOT NULL,
                    tempo_minimo_minuti REAL,
                    tempo_massimo_minuti REAL,
                    numero_osservazioni INTEGER DEFAULT 1 NOT NULL,
                    ultima_osservazione TIMESTAMP NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                conn.execute(text(create_table_sql))
                print("  ✅ Tabella tempi_produzione creata/verificata")
                
                # 4. Crea indici per la tabella tempi_produzione
                print("📝 Creazione indici per tempi_produzione...")
                
                tempo_indices = [
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_part_number ON tempi_produzione(part_number)",
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_categoria ON tempi_produzione(categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_sotto_categoria ON tempi_produzione(sotto_categoria)"
                ]
                
                for index in tempo_indices:
                    try:
                        conn.execute(text(index))
                        index_name = index.split('idx_')[1].split(' ')[0]
                        print(f"  ✅ Creato indice: {index_name}")
                    except Exception as e:
                        print(f"  ⚠️  Indice già esistente o errore: {e}")
                
                # 5. Inserisci alcuni dati di esempio per i tempi di produzione
                print("📝 Inserimento dati di esempio per tempi_produzione...")
                
                # Prima controlla se ci sono già dati
                result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
                count = result.scalar()
                
                if count == 0:
                    sample_data = [
                        ("PART001", "Aerospace", "Wing Components", 240, 200, 300, 5),
                        ("PART002", "Automotive", "Engine Parts", 180, 150, 220, 8),
                        (None, "Aerospace", "Fuselage", 360, 300, 420, 3),
                        (None, "Medical", "Implants", 120, 90, 150, 12),
                        (None, "Industrial", "Machinery", 480, 400, 600, 6)
                    ]
                    
                    for part_number, categoria, sotto_categoria, tempo_medio, tempo_min, tempo_max, osservazioni in sample_data:
                        try:
                            conn.execute(text("""
                                INSERT INTO tempi_produzione 
                                (part_number, categoria, sotto_categoria, tempo_medio_minuti, 
                                 tempo_minimo_minuti, tempo_massimo_minuti, numero_osservazioni, 
                                 ultima_osservazione, note)
                                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'Dati di esempio inseriti durante aggiornamento schema')
                            """), (part_number, categoria, sotto_categoria, tempo_medio, tempo_min, tempo_max, osservazioni))
                            print(f"  ✅ Inserito tempo per {categoria}/{sotto_categoria}")
                        except Exception as e:
                            print(f"  ⚠️  Errore nell'inserimento: {e}")
                else:
                    print(f"  ℹ️  Dati già presenti ({count} record), salto l'inserimento")
                
                # 6. Crea indici per le nuove colonne di schedule_entries
                print("📝 Creazione indici per le nuove colonne di schedule_entries...")
                
                schedule_indices = [
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_categoria ON schedule_entries(categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_sotto_categoria ON schedule_entries(sotto_categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_schedule_type ON schedule_entries(schedule_type)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_is_recurring ON schedule_entries(is_recurring)"
                ]
                
                for index in schedule_indices:
                    try:
                        conn.execute(text(index))
                        index_name = index.split('idx_')[1].split(' ')[0]
                        print(f"  ✅ Creato indice: {index_name}")
                    except Exception as e:
                        print(f"  ⚠️  Indice già esistente o errore: {e}")
                
                # Commit della transazione
                trans.commit()
                print("✅ Aggiornamento schema SQLite completato con successo!")
                
            except Exception as e:
                # Rollback in caso di errore
                trans.rollback()
                print(f"❌ Errore durante l'aggiornamento: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Errore di connessione al database: {e}")
        return False
    
    return True

def verify_schema():
    """Verifica che lo schema sia stato aggiornato correttamente."""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("\n🔍 Verifica dello schema aggiornato...")
    
    try:
        with engine.connect() as conn:
            # Verifica le colonne della tabella schedule_entries
            result = conn.execute(text("PRAGMA table_info(schedule_entries)"))
            columns = list(result)
            
            print("\n📋 Colonne tabella schedule_entries:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} (nullable: {not col[3]})")
            
            # Verifica la tabella tempi_produzione
            result = conn.execute(text("PRAGMA table_info(tempi_produzione)"))
            columns = list(result)
            
            print("\n📋 Colonne tabella tempi_produzione:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]} (nullable: {not col[3]})")
            
            # Conta i record di esempio
            result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
            count = result.scalar()
            print(f"\n📊 Record in tempi_produzione: {count}")
            
            # Verifica gli indici
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name IN ('schedule_entries', 'tempi_produzione')"))
            indices = [row[0] for row in result if not row[0].startswith('sqlite_')]
            print(f"\n📊 Indici creati: {len(indices)}")
            for idx in indices:
                print(f"  - {idx}")
            
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Avvio aggiornamento schema database SQLite per CarbonPilot Scheduling...")
    
    if update_database_schema():
        if verify_schema():
            print("\n🎉 Aggiornamento completato con successo!")
            print("\n📝 Nuove funzionalità disponibili:")
            print("  - Schedulazioni per categoria/sotto-categoria")
            print("  - Schedulazioni ricorrenti")
            print("  - Calcolo automatico tempi di fine")
            print("  - Gestione azioni operatore")
            print("  - Tempi di produzione storici")
        else:
            print("\n⚠️  Aggiornamento completato ma verifica fallita")
            sys.exit(1)
    else:
        print("\n❌ Aggiornamento fallito")
        sys.exit(1) 