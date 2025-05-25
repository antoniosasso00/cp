#!/usr/bin/env python3
"""
Script per aggiornare lo schema del database con le nuove funzionalità di scheduling.
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
    """Aggiorna lo schema del database con le nuove funzionalità."""
    
    # Crea il motore del database
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print("🔄 Aggiornamento schema database per le nuove funzionalità di scheduling...")
    
    try:
        with engine.connect() as conn:
            # Inizia una transazione
            trans = conn.begin()
            
            try:
                # 1. Crea i nuovi enum se non esistono
                print("📝 Creazione nuovi enum...")
                
                # Enum per ScheduleEntryType
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE schedule_entry_type AS ENUM (
                            'odl_specifico', 'categoria', 'sotto_categoria', 'ricorrente'
                        );
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Aggiorna l'enum ScheduleEntryStatus con i nuovi valori
                conn.execute(text("""
                    DO $$ BEGIN
                        ALTER TYPE schedule_entry_status ADD VALUE IF NOT EXISTS 'previsionale';
                        ALTER TYPE schedule_entry_status ADD VALUE IF NOT EXISTS 'in_attesa';
                        ALTER TYPE schedule_entry_status ADD VALUE IF NOT EXISTS 'in_corso';
                        ALTER TYPE schedule_entry_status ADD VALUE IF NOT EXISTS 'posticipato';
                    EXCEPTION
                        WHEN others THEN null;
                    END $$;
                """))
                
                # 2. Aggiungi le nuove colonne alla tabella schedule_entries
                print("📝 Aggiunta nuove colonne alla tabella schedule_entries...")
                
                new_columns = [
                    "ADD COLUMN IF NOT EXISTS schedule_type schedule_entry_type DEFAULT 'odl_specifico'",
                    "ADD COLUMN IF NOT EXISTS categoria VARCHAR(100)",
                    "ADD COLUMN IF NOT EXISTS sotto_categoria VARCHAR(100)",
                    "ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN DEFAULT FALSE",
                    "ADD COLUMN IF NOT EXISTS recurring_frequency VARCHAR(50)",
                    "ADD COLUMN IF NOT EXISTS pieces_per_month INTEGER",
                    "ADD COLUMN IF NOT EXISTS parent_schedule_id INTEGER REFERENCES schedule_entries(id)",
                    "ADD COLUMN IF NOT EXISTS note TEXT",
                    "ADD COLUMN IF NOT EXISTS estimated_duration_minutes INTEGER"
                ]
                
                for column in new_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE schedule_entries {column}"))
                        print(f"  ✅ Aggiunta colonna: {column.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]}")
                    except Exception as e:
                        print(f"  ⚠️  Colonna già esistente o errore: {e}")
                
                # 3. Modifica la colonna odl_id per renderla nullable
                print("📝 Modifica colonna odl_id per renderla nullable...")
                try:
                    conn.execute(text("ALTER TABLE schedule_entries ALTER COLUMN odl_id DROP NOT NULL"))
                    print("  ✅ Colonna odl_id ora nullable")
                except Exception as e:
                    print(f"  ⚠️  Errore nella modifica di odl_id: {e}")
                
                # 4. Modifica la colonna end_datetime per renderla nullable
                print("📝 Modifica colonna end_datetime per renderla nullable...")
                try:
                    conn.execute(text("ALTER TABLE schedule_entries ALTER COLUMN end_datetime DROP NOT NULL"))
                    print("  ✅ Colonna end_datetime ora nullable")
                except Exception as e:
                    print(f"  ⚠️  Errore nella modifica di end_datetime: {e}")
                
                # 5. Crea indici per le nuove colonne
                print("📝 Creazione indici per le nuove colonne...")
                
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_categoria ON schedule_entries(categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_sotto_categoria ON schedule_entries(sotto_categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_schedule_type ON schedule_entries(schedule_type)",
                    "CREATE INDEX IF NOT EXISTS idx_schedule_entries_is_recurring ON schedule_entries(is_recurring)"
                ]
                
                for index in indices:
                    try:
                        conn.execute(text(index))
                        print(f"  ✅ Creato indice: {index.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        print(f"  ⚠️  Indice già esistente o errore: {e}")
                
                # 6. Crea la tabella tempi_produzione
                print("📝 Creazione tabella tempi_produzione...")
                
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS tempi_produzione (
                    id SERIAL PRIMARY KEY,
                    part_number VARCHAR(100),
                    categoria VARCHAR(100),
                    sotto_categoria VARCHAR(100),
                    tempo_medio_minuti FLOAT NOT NULL,
                    tempo_minimo_minuti FLOAT,
                    tempo_massimo_minuti FLOAT,
                    numero_osservazioni INTEGER DEFAULT 1 NOT NULL,
                    ultima_osservazione TIMESTAMP NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                conn.execute(text(create_table_sql))
                print("  ✅ Tabella tempi_produzione creata")
                
                # 7. Crea indici per la tabella tempi_produzione
                print("📝 Creazione indici per tempi_produzione...")
                
                tempo_indices = [
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_part_number ON tempi_produzione(part_number)",
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_categoria ON tempi_produzione(categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_tempi_produzione_sotto_categoria ON tempi_produzione(sotto_categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_part_number_categoria ON tempi_produzione(part_number, categoria)",
                    "CREATE INDEX IF NOT EXISTS idx_categoria_sotto_categoria ON tempi_produzione(categoria, sotto_categoria)"
                ]
                
                for index in tempo_indices:
                    try:
                        conn.execute(text(index))
                        print(f"  ✅ Creato indice: {index.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        print(f"  ⚠️  Indice già esistente o errore: {e}")
                
                # 8. Inserisci alcuni dati di esempio per i tempi di produzione
                print("📝 Inserimento dati di esempio per tempi_produzione...")
                
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
                            VALUES (:part_number, :categoria, :sotto_categoria, :tempo_medio, 
                                    :tempo_min, :tempo_max, :osservazioni, CURRENT_TIMESTAMP, 
                                    'Dati di esempio inseriti durante l''aggiornamento schema')
                            ON CONFLICT DO NOTHING
                        """), {
                            'part_number': part_number,
                            'categoria': categoria,
                            'sotto_categoria': sotto_categoria,
                            'tempo_medio': tempo_medio,
                            'tempo_min': tempo_min,
                            'tempo_max': tempo_max,
                            'osservazioni': osservazioni
                        })
                        print(f"  ✅ Inserito tempo per {categoria}/{sotto_categoria}")
                    except Exception as e:
                        print(f"  ⚠️  Errore nell'inserimento: {e}")
                
                # Commit della transazione
                trans.commit()
                print("✅ Aggiornamento schema completato con successo!")
                
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
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_entries'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Colonne tabella schedule_entries:")
            for row in result:
                print(f"  - {row.column_name}: {row.data_type} (nullable: {row.is_nullable})")
            
            # Verifica la tabella tempi_produzione
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'tempi_produzione'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Colonne tabella tempi_produzione:")
            for row in result:
                print(f"  - {row.column_name}: {row.data_type} (nullable: {row.is_nullable})")
            
            # Conta i record di esempio
            result = conn.execute(text("SELECT COUNT(*) FROM tempi_produzione"))
            count = result.scalar()
            print(f"\n📊 Record in tempi_produzione: {count}")
            
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Avvio aggiornamento schema database per CarbonPilot Scheduling...")
    
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