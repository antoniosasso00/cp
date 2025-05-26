#!/usr/bin/env python3
"""
Script per controllare le tabelle nel database SQLite
"""

import sqlite3
import os

def check_database():
    """Controlla le tabelle nel database"""
    db_path = "carbonpilot.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} non trovato!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ottieni tutte le tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Database: {db_path}")
        print(f"📋 Tabelle trovate ({len(tables)}):")
        for table in sorted(tables):
            print(f"  ✓ {table}")
        
        # Controlla specificamente la tabella system_logs
        if "system_logs" in tables:
            print(f"\n✅ Tabella 'system_logs' TROVATA!")
            
            # Controlla la struttura
            cursor.execute("PRAGMA table_info(system_logs)")
            columns = cursor.fetchall()
            print(f"📝 Colonne della tabella system_logs ({len(columns)}):")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
                
            # Controlla il numero di record
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            count = cursor.fetchone()[0]
            print(f"📊 Record nella tabella: {count}")
            
        else:
            print(f"\n❌ Tabella 'system_logs' NON TROVATA!")
            print("🔧 Potrebbe essere necessario eseguire la migrazione del database")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore nell'accesso al database: {e}")

if __name__ == "__main__":
    check_database() 