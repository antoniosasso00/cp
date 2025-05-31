#!/usr/bin/env python3
"""
Script per aggiungere le colonne mancanti alla tabella batch_nesting
"""
import sqlite3
import os

def fix_batch_nesting_schema():
    """Aggiunge le colonne mancanti alla tabella batch_nesting"""
    
    # Path del database
    db_path = "backend/carbonpilot.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return False
    
    try:
        # Connessione al database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se le colonne esistono già
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 Colonne attuali in batch_nesting: {columns}")
        
        # Aggiungi data_completamento se non esiste
        if 'data_completamento' not in columns:
            print("➕ Aggiungendo colonna data_completamento...")
            cursor.execute("ALTER TABLE batch_nesting ADD COLUMN data_completamento DATETIME")
            print("✅ Colonna data_completamento aggiunta")
        else:
            print("✅ Colonna data_completamento già presente")
        
        # Aggiungi durata_ciclo_minuti se non esiste
        if 'durata_ciclo_minuti' not in columns:
            print("➕ Aggiungendo colonna durata_ciclo_minuti...")
            cursor.execute("ALTER TABLE batch_nesting ADD COLUMN durata_ciclo_minuti INTEGER")
            print("✅ Colonna durata_ciclo_minuti aggiunta")
        else:
            print("✅ Colonna durata_ciclo_minuti già presente")
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colonne finali in batch_nesting: {columns_after}")
        
        conn.close()
        print("✅ Schema batch_nesting aggiornato con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento dello schema: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Aggiornamento schema batch_nesting...")
    success = fix_batch_nesting_schema()
    if success:
        print("🎉 Operazione completata con successo!")
    else:
        print("💥 Operazione fallita!") 