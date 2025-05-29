#!/usr/bin/env python3
"""
Script per verificare lo schema del database SQLite
e identificare problemi con la tabella schedule_entries
"""

from sqlalchemy import create_engine, text, inspect
import os

def main():
    print("🔍 Verifica Schema Database SQLite")
    print("=" * 50)
    
    # Path del database
    db_path = "./carbonpilot.db"
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    # Connessione al database
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    
    # Verifica tabelle esistenti
    tables = inspector.get_table_names()
    print(f"📋 Tabelle nel database: {len(tables)}")
    for table in sorted(tables):
        print(f"  - {table}")
    
    print()
    
    # Verifica specifica della tabella schedule_entries
    if 'schedule_entries' in tables:
        print("🔍 Schema tabella schedule_entries:")
        columns = inspector.get_columns('schedule_entries')
        for col in columns:
            print(f"  - {col['name']}: {col['type']} {'(NULL)' if col['nullable'] else '(NOT NULL)'}")
        
        print()
        
        # Verifica se manca la colonna schedule_type
        column_names = [col['name'] for col in columns]
        if 'schedule_type' not in column_names:
            print("❌ PROBLEMA IDENTIFICATO:")
            print("   La colonna 'schedule_type' NON esiste nella tabella!")
            print("   Il modello SQLAlchemy la richiede ma la migrazione non l'ha creata.")
            print()
            print("🔧 Soluzioni possibili:")
            print("   1. Applicare migrazione mancante")
            print("   2. Aggiungere colonna manualmente")
            print("   3. Ricreare il database")
            
            # Controlla anche altre colonne mancanti
            required_columns = [
                'schedule_type', 'categoria', 'sotto_categoria', 
                'is_recurring', 'recurring_frequency', 'pieces_per_month',
                'parent_schedule_id', 'note', 'estimated_duration_minutes'
            ]
            
            missing_columns = [col for col in required_columns if col not in column_names]
            if missing_columns:
                print(f"   🔍 Altre colonne mancanti: {', '.join(missing_columns)}")
        else:
            print("✅ La colonna 'schedule_type' esiste correttamente")
    else:
        print("❌ Tabella 'schedule_entries' non trovata!")
    
    print()
    
    # Verifica con query diretta
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM schedule_entries"))
            count = result.scalar()
            print(f"📊 Numero di record in schedule_entries: {count}")
            
            # Prova a accedere alla colonna schedule_type
            try:
                result = conn.execute(text("SELECT schedule_type FROM schedule_entries LIMIT 1"))
                print("✅ Colonna schedule_type accessibile")
            except Exception as e:
                print(f"❌ Errore accesso schedule_type: {e}")
                
    except Exception as e:
        print(f"❌ Errore connessione database: {e}")
        
    print()
    print("🔧 Se ci sono colonne mancanti, esegui questo comando SQL:")
    print("   ALTER TABLE schedule_entries ADD COLUMN schedule_type VARCHAR(50) DEFAULT 'odl_specifico';")

if __name__ == "__main__":
    main() 