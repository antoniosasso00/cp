#!/usr/bin/env python3
"""
Script per controllare lo schema della tabella batch_nesting
"""
import sqlite3
import sys

def check_batch_nesting_schema():
    try:
        # Connessione al database
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batch_nesting'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ La tabella 'batch_nesting' non esiste!")
            return False
        
        print("✅ La tabella 'batch_nesting' esiste")
        
        # Controlla lo schema della tabella
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns = cursor.fetchall()
        
        print("\n📋 Schema attuale della tabella 'batch_nesting':")
        print("=" * 60)
        
        column_names = []
        for col in columns:
            cid, name, ctype, notnull, default, pk = col
            print(f"  {name:<25} | {ctype:<15} | {'NOT NULL' if notnull else 'NULL':<10} | PK: {bool(pk)}")
            column_names.append(name)
        
        # Verifica se la colonna efficiency esiste
        efficiency_exists = 'efficiency' in column_names
        
        print(f"\n🔍 Colonna 'efficiency' presente: {'✅ SÌ' if efficiency_exists else '❌ NO'}")
        
        if not efficiency_exists:
            print("\n⚠️  La colonna 'efficiency' è mancante!")
            print("📝 Questo spiega l'errore SQLite negli endpoint batch_nesting")
        
        conn.close()
        return efficiency_exists
        
    except Exception as e:
        print(f"❌ Errore durante il controllo dello schema: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Controllo schema tabella batch_nesting...")
    check_batch_nesting_schema() 