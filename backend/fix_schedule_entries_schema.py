#!/usr/bin/env python3
"""
Script per aggiungere le colonne mancanti alla tabella schedule_entries
"""

from sqlalchemy import create_engine, text
import os

def main():
    print("🔧 Fix Schema tabella schedule_entries")
    print("=" * 50)
    
    # Path del database
    db_path = "./carbonpilot.db"
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    # Connessione al database
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Colonne da aggiungere con i loro tipi e valori default
    columns_to_add = [
        ("schedule_type", "VARCHAR(50)", "'odl_specifico'"),
        ("categoria", "VARCHAR(100)", "NULL"),
        ("sotto_categoria", "VARCHAR(100)", "NULL"),
        ("is_recurring", "BOOLEAN", "FALSE"),
        ("recurring_frequency", "VARCHAR(50)", "NULL"),
        ("pieces_per_month", "INTEGER", "NULL"),
        ("parent_schedule_id", "INTEGER", "NULL"),
        ("note", "TEXT", "NULL"),
        ("estimated_duration_minutes", "INTEGER", "NULL"),
        ("updated_at", "DATETIME", "CURRENT_TIMESTAMP")
    ]
    
    try:
        with engine.connect() as conn:
            # Backup di sicurezza prima delle modifiche
            print("📋 Creazione backup della tabella...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schedule_entries_backup AS 
                SELECT * FROM schedule_entries
            """))
            conn.commit()
            print("✅ Backup creato: schedule_entries_backup")
            
            # Aggiunge ogni colonna mancante
            for column_name, column_type, default_value in columns_to_add:
                print(f"🔧 Aggiunta colonna: {column_name}")
                try:
                    alter_sql = f"ALTER TABLE schedule_entries ADD COLUMN {column_name} {column_type}"
                    if default_value != "NULL":
                        alter_sql += f" DEFAULT {default_value}"
                    
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"✅ Colonna {column_name} aggiunta con successo")
                    
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  Colonna {column_name} già esiste")
                    else:
                        print(f"❌ Errore aggiunta {column_name}: {e}")
            
            # Aggiorna odl_id per permettere valori NULL (per schedulazioni per categoria)
            print("🔧 Aggiornamento vincolo odl_id...")
            try:
                # Crea una nuova tabella con la struttura corretta
                conn.execute(text("""
                    CREATE TABLE schedule_entries_new (
                        id INTEGER PRIMARY KEY,
                        schedule_type VARCHAR(50) DEFAULT 'odl_specifico',
                        odl_id INTEGER NULL,
                        autoclave_id INTEGER NOT NULL,
                        categoria VARCHAR(100) NULL,
                        sotto_categoria VARCHAR(100) NULL,
                        start_datetime DATETIME NOT NULL,
                        end_datetime DATETIME,
                        status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
                        created_by VARCHAR(100),
                        priority_override BOOLEAN NOT NULL DEFAULT FALSE,
                        is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
                        recurring_frequency VARCHAR(50),
                        pieces_per_month INTEGER,
                        parent_schedule_id INTEGER,
                        note TEXT,
                        estimated_duration_minutes INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (odl_id) REFERENCES odl(id),
                        FOREIGN KEY (autoclave_id) REFERENCES autoclavi(id),
                        FOREIGN KEY (parent_schedule_id) REFERENCES schedule_entries(id)
                    )
                """))
                
                # Copia i dati esistenti
                conn.execute(text("""
                    INSERT INTO schedule_entries_new 
                    (id, schedule_type, odl_id, autoclave_id, categoria, sotto_categoria,
                     start_datetime, end_datetime, status, created_by, priority_override,
                     is_recurring, recurring_frequency, pieces_per_month, parent_schedule_id,
                     note, estimated_duration_minutes, created_at, updated_at)
                    SELECT 
                        id, 
                        COALESCE(schedule_type, 'odl_specifico'),
                        odl_id,
                        autoclave_id,
                        categoria,
                        sotto_categoria,
                        start_datetime,
                        end_datetime,
                        status,
                        created_by,
                        priority_override,
                        COALESCE(is_recurring, FALSE),
                        recurring_frequency,
                        pieces_per_month,
                        parent_schedule_id,
                        note,
                        estimated_duration_minutes,
                        created_at,
                        COALESCE(updated_at, CURRENT_TIMESTAMP)
                    FROM schedule_entries
                """))
                
                # Rinomina le tabelle
                conn.execute(text("DROP TABLE schedule_entries"))
                conn.execute(text("ALTER TABLE schedule_entries_new RENAME TO schedule_entries"))
                
                conn.commit()
                print("✅ Struttura tabella aggiornata con successo")
                
            except Exception as e:
                print(f"❌ Errore aggiornamento struttura: {e}")
            
            # Verifica finale
            print("\n📊 Verifica finale:")
            result = conn.execute(text("SELECT COUNT(*) FROM schedule_entries"))
            count = result.scalar()
            print(f"✅ Record in schedule_entries: {count}")
            
            # Test colonna schedule_type
            try:
                result = conn.execute(text("SELECT schedule_type FROM schedule_entries LIMIT 1"))
                print("✅ Colonna schedule_type accessibile")
            except Exception as e:
                print(f"❌ Errore accesso schedule_type: {e}")
                
    except Exception as e:
        print(f"❌ Errore generale: {e}")
    
    print("\n🎉 Fix completato!")
    print("💡 Ora riavvia il backend per verificare che non ci siano più errori SQLAlchemy")

if __name__ == "__main__":
    main() 