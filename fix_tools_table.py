#!/usr/bin/env python3
"""
Script per aggiungere le colonne mancanti alla tabella tools
"""

import sqlite3
from pathlib import Path

def main():
    # Percorso del database
    db_path = Path("backend/carbonpilot.db")
    
    print(f"🔍 Connessione al database: {db_path}")
    
    try:
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la tabella tools esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tools'")
        if not cursor.fetchone():
            print("❌ Tabella 'tools' non trovata!")
            return
        
        print("✅ Tabella 'tools' trovata")
        
        # Verifica struttura tabella
        cursor.execute("PRAGMA table_info(tools)")
        columns = cursor.fetchall()
        
        print(f"📋 Colonne nella tabella tools:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        column_names = [col[1] for col in columns]
        
        # Aggiungi colonne mancanti
        columns_to_add = [
            ("peso", "REAL"),
            ("materiale", "TEXT"),
            ("note", "TEXT")
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in column_names:
                print(f"\n📝 Aggiungendo colonna {col_name}...")
                cursor.execute(f"ALTER TABLE tools ADD COLUMN {col_name} {col_type}")
                print(f"✅ Colonna {col_name} aggiunta!")
            else:
                print(f"\nℹ️ Colonna {col_name} già presente")
        
        # Salva le modifiche
        conn.commit()
        
        # Test finale
        print("\n🧪 Test finale...")
        cursor.execute("SELECT COUNT(*) FROM tools")
        count = cursor.fetchone()[0]
        print(f"📊 Totale tools nel database: {count}")
        
        cursor.execute("PRAGMA table_info(tools)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Colonne finali nella tabella tools:")
        for col in final_columns:
            print(f"   - {col}")
        
        conn.close()
        
        print("\n🎉 Operazione completata!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    main() 