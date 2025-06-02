#!/usr/bin/env python3
"""
Script per verificare le colonne della tabella autoclavi
"""
import sqlite3
import os

def check_autoclavi_columns():
    """Controlla le colonne della tabella autoclavi"""
    
    # Trova il database
    db_paths = ['carbonpilot.db', '../carbonpilot.db', './carbonpilot.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database non trovato")
        return
    
    print(f"🔍 Connessione a: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica tabella autoclavi
        cursor.execute("PRAGMA table_info(autoclavi)")
        columns_info = cursor.fetchall()
        
        print(f"\n📋 Tabella 'autoclavi' - {len(columns_info)} colonne:")
        print("=" * 60)
        
        columns_names = []
        for col_info in columns_info:
            col_id, name, type_name, not_null, default, pk = col_info
            columns_names.append(name)
            print(f"  {col_id:2d}. {name:20s} {type_name:15s} {'NOT NULL' if not_null else 'NULL':8s} PK={pk}")
        
        print(f"\n🔍 Verifica presenza colonne chiave:")
        critical_columns = [
            'use_secondary_plane', 
            'area_piano_2', 
            'superficie_piano_2_max',
            'max_load_kg',
            'num_linee_vuoto'
        ]
        
        for col in critical_columns:
            status = "✅ PRESENTE" if col in columns_names else "❌ MANCANTE"
            print(f"  {col:25s}: {status}")
        
        # Verifica se ci sono problemi
        problems = []
        if 'use_secondary_plane' in columns_names:
            problems.append("La colonna 'use_secondary_plane' esiste ancora nel database")
        
        if not 'max_load_kg' in columns_names:
            problems.append("La colonna 'max_load_kg' è mancante")
        
        if not 'num_linee_vuoto' in columns_names:
            problems.append("La colonna 'num_linee_vuoto' è mancante")
        
        print(f"\n🚨 PROBLEMI IDENTIFICATI:")
        if problems:
            for i, problem in enumerate(problems, 1):
                print(f"  {i}. {problem}")
        else:
            print("  ✅ Nessun problema rilevato")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    check_autoclavi_columns() 