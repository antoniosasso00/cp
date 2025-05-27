#!/usr/bin/env python3
"""
Script robusto per aggiungere la colonna previous_status alla tabella ODL
"""

import sqlite3
from pathlib import Path

def main():
    # Percorso del database
    db_path = Path("carbonpilot.db")
    
    print(f"🔍 Connessione al database: {db_path}")
    
    try:
        # Connessione al database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verifica se la tabella odl esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='odl'")
        if not cursor.fetchone():
            print("❌ Tabella 'odl' non trovata!")
            return
        
        print("✅ Tabella 'odl' trovata")
        
        # Verifica struttura tabella
        cursor.execute("PRAGMA table_info(odl)")
        columns = cursor.fetchall()
        
        print(f"📋 Colonne nella tabella odl:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        column_names = [col[1] for col in columns]
        
        if 'previous_status' not in column_names:
            print("\n📝 Aggiungendo colonna previous_status...")
            
            # Aggiungi la colonna
            cursor.execute("ALTER TABLE odl ADD COLUMN previous_status TEXT")
            
            print("✅ Colonna previous_status aggiunta!")
            
        else:
            print("\nℹ️ Colonna previous_status già presente")
        
        # Verifica che la colonna sia accessibile
        try:
            cursor.execute("SELECT id, status, previous_status FROM odl LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"✅ Test accesso riuscito: ODL {result[0]}, status='{result[1]}', previous_status='{result[2]}'")
            else:
                print("ℹ️ Nessun ODL presente nella tabella")
        except Exception as e:
            print(f"❌ Errore nell'accesso alla colonna: {e}")
            
            # Prova a ricreare la colonna
            print("🔧 Tentativo di ricreare la colonna...")
            try:
                cursor.execute("ALTER TABLE odl DROP COLUMN previous_status")
            except:
                pass  # Ignora errori se la colonna non esiste
            
            cursor.execute("ALTER TABLE odl ADD COLUMN previous_status TEXT")
            print("✅ Colonna previous_status ricreata")
        
        # Salva le modifiche
        conn.commit()
        
        # Test finale
        print("\n🧪 Test finale...")
        cursor.execute("SELECT COUNT(*) FROM odl")
        count = cursor.fetchone()[0]
        print(f"📊 Totale ODL nel database: {count}")
        
        cursor.execute("PRAGMA table_info(odl)")
        final_columns = [col[1] for col in cursor.fetchall()]
        if 'previous_status' in final_columns:
            print("✅ Colonna previous_status confermata nel database")
        else:
            print("❌ Colonna previous_status NON trovata nel database")
        
        conn.close()
        
        print("\n🎉 Operazione completata!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    main() 