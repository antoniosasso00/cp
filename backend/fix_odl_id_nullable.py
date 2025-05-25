#!/usr/bin/env python3
"""
Script per rendere odl_id nullable nella tabella schedule_entries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.db import get_database_url

def fix_odl_id_nullable():
    """Rende odl_id nullable nella tabella schedule_entries."""
    
    print("🔧 CORREZIONE CAMPO ODL_ID")
    print("=" * 50)
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Per SQLite, dobbiamo ricreare la tabella
            print("📊 Backup dati esistenti...")
            
            # 1. Backup dei dati esistenti
            result = conn.execute(text("SELECT * FROM schedule_entries"))
            existing_data = list(result)
            print(f"   Trovati {len(existing_data)} record da preservare")
            
            # 2. Rinomina la tabella esistente
            conn.execute(text("ALTER TABLE schedule_entries RENAME TO schedule_entries_backup"))
            print("   Tabella rinominata in schedule_entries_backup")
            
            # 3. Crea la nuova tabella con odl_id nullable
            conn.execute(text("""
                CREATE TABLE schedule_entries (
                    id INTEGER PRIMARY KEY,
                    schedule_type VARCHAR(50) NOT NULL DEFAULT 'odl_specifico',
                    odl_id INTEGER NULL,
                    autoclave_id INTEGER NOT NULL,
                    categoria VARCHAR(100) NULL,
                    sotto_categoria VARCHAR(100) NULL,
                    start_datetime DATETIME NOT NULL,
                    end_datetime DATETIME NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
                    created_by VARCHAR(100) NULL,
                    priority_override BOOLEAN NOT NULL DEFAULT 0,
                    is_recurring BOOLEAN NOT NULL DEFAULT 0,
                    recurring_frequency VARCHAR(50) NULL,
                    pieces_per_month INTEGER NULL,
                    parent_schedule_id INTEGER NULL,
                    note TEXT NULL,
                    estimated_duration_minutes INTEGER NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (odl_id) REFERENCES odl(id),
                    FOREIGN KEY (autoclave_id) REFERENCES autoclavi(id),
                    FOREIGN KEY (parent_schedule_id) REFERENCES schedule_entries(id)
                )
            """))
            print("   Nuova tabella creata con odl_id nullable")
            
            # 4. Ripristina i dati
            if existing_data:
                print("📝 Ripristino dati esistenti...")
                for row in existing_data:
                    # Prepara i valori per l'inserimento
                    values = list(row)
                    placeholders = ', '.join(['?' for _ in values])
                    columns = [
                        'id', 'schedule_type', 'odl_id', 'autoclave_id', 'categoria', 
                        'sotto_categoria', 'start_datetime', 'end_datetime', 'status',
                        'created_by', 'priority_override', 'is_recurring', 'recurring_frequency',
                        'pieces_per_month', 'parent_schedule_id', 'note', 'estimated_duration_minutes',
                        'created_at', 'updated_at'
                    ]
                    
                    conn.execute(text(f"""
                        INSERT INTO schedule_entries ({', '.join(columns)})
                        VALUES ({placeholders})
                    """), tuple(values))
                
                print(f"   Ripristinati {len(existing_data)} record")
            
            # 5. Elimina la tabella di backup
            conn.execute(text("DROP TABLE schedule_entries_backup"))
            print("   Tabella di backup eliminata")
            
            # Commit delle modifiche
            conn.commit()
            
            # 6. Verifica finale
            result = conn.execute(text("PRAGMA table_info(schedule_entries)"))
            columns = list(result)
            odl_id_column = next((col for col in columns if col[1] == 'odl_id'), None)
            
            if odl_id_column and not odl_id_column[3]:  # not null = False
                print("✅ Campo odl_id ora è nullable!")
            else:
                print("❌ Campo odl_id ancora NOT NULL")
                return False
            
            # Conta i record finali
            result = conn.execute(text("SELECT COUNT(*) FROM schedule_entries"))
            count = result.scalar()
            print(f"📈 Record finali: {count}")
            
            print("\n✅ Correzione completata con successo!")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        return False

def main():
    """Esegue la correzione del campo odl_id."""
    
    print("🚀 AVVIO CORREZIONE ODL_ID")
    print("=" * 40)
    
    if fix_odl_id_nullable():
        print("\n🎉 Correzione completata con successo!")
        print("\n📋 Prossimi passi:")
        print("1. Riavvia il backend: py main.py")
        print("2. Testa la creazione di schedulazioni per categoria")
    else:
        print("\n❌ Correzione fallita")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 