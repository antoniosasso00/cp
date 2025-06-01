#!/usr/bin/env python3
"""
Verifica e aggiorna lo schema del database per v1.4.5-DEMO
"""
import sqlite3
import sys

def check_and_update_schema():
    """Verifica lo schema del database e aggiunge le colonne mancanti."""
    print("🔍 Verifica Schema Database per v1.4.5-DEMO")
    print("=" * 50)
    
    try:
        # Connessione al database
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica colonne ODL
        print("📋 Colonne attuali tabella ODL:")
        cursor.execute('PRAGMA table_info(odl)')
        odl_columns = cursor.fetchall()
        odl_column_names = [col[1] for col in odl_columns]
        
        for col in odl_columns:
            print(f"  • {col[1]} - {col[2]}")
        
        # Verifica se include_in_std esiste
        if 'include_in_std' not in odl_column_names:
            print("\n❌ Colonna 'include_in_std' mancante!")
            print("➕ Aggiungendo colonna...")
            
            cursor.execute('ALTER TABLE odl ADD COLUMN include_in_std BOOLEAN NOT NULL DEFAULT true')
            print("✅ Colonna 'include_in_std' aggiunta!")
        else:
            print("\n✅ Colonna 'include_in_std' trovata!")
        
        # Verifica tabella standard_times
        print("\n📋 Verifica tabella standard_times:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='standard_times'")
        standard_times_exists = cursor.fetchone() is not None
        
        if standard_times_exists:
            print("✅ Tabella 'standard_times' trovata!")
            cursor.execute('PRAGMA table_info(standard_times)')
            st_columns = cursor.fetchall()
            print("📋 Colonne standard_times:")
            for col in st_columns:
                print(f"  • {col[1]} - {col[2]}")
                
            # Verifica dati di test
            cursor.execute("SELECT COUNT(*) FROM standard_times WHERE part_number = 'TEST-E2E-001'")
            test_data_count = cursor.fetchone()[0]
            print(f"\n📊 Dati di test per TEST-E2E-001: {test_data_count} record")
            
        else:
            print("❌ Tabella 'standard_times' non trovata!")
            print("➕ Creando tabella...")
            
            cursor.execute("""
                CREATE TABLE standard_times (
                    id INTEGER PRIMARY KEY,
                    part_number VARCHAR(50) NOT NULL REFERENCES cataloghi(part_number),
                    phase VARCHAR(50) NOT NULL,
                    minutes FLOAT NOT NULL,
                    note VARCHAR(500),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX ix_standard_times_id ON standard_times(id)")
            cursor.execute("CREATE INDEX ix_standard_times_part_number ON standard_times(part_number)")
            cursor.execute("CREATE INDEX ix_standard_times_phase ON standard_times(phase)")
            
            print("✅ Tabella 'standard_times' creata!")
            
            # Aggiungi dati di test
            test_data = [
                ('TEST-E2E-001', 'laminazione', 45.0, 'Tempo standard per fase di laminazione - dato di test'),
                ('TEST-E2E-001', 'cura', 120.0, 'Tempo standard per fase di cura - dato di test'),
                ('TEST-E2E-001', 'attesa_cura', 30.0, 'Tempo standard per fase di attesa cura - dato di test')
            ]
            
            cursor.executemany(
                "INSERT INTO standard_times (part_number, phase, minutes, note) VALUES (?, ?, ?, ?)",
                test_data
            )
            print("✅ Dati di test inseriti!")
        
        # Commit e chiusura
        conn.commit()
        conn.close()
        
        print("\n🎯 SCHEMA VERIFICATO E AGGIORNATO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRORE: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_and_update_schema()
    sys.exit(0 if success else 1) 