#!/usr/bin/env python3
"""
Script per aggiungere manualmente il campo efficiency alla tabella batch_nesting
"""
import sqlite3
import sys

def add_efficiency_field():
    """Aggiunge il campo efficiency alla tabella batch_nesting"""
    try:
        # Connessione al database
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        print("🔧 Aggiunta del campo efficiency alla tabella batch_nesting...")
        
        # Verifica se il campo esiste già
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'efficiency' in column_names:
            print("✅ Il campo 'efficiency' esiste già!")
            return True
        
        # Aggiunge il campo efficiency
        cursor.execute("ALTER TABLE batch_nesting ADD COLUMN efficiency REAL DEFAULT 0.0")
        print("✅ Campo 'efficiency' aggiunto con successo!")
        
        # Aggiorna tutti i record esistenti
        cursor.execute("UPDATE batch_nesting SET efficiency = 0.0 WHERE efficiency IS NULL")
        print("✅ Record esistenti aggiornati con efficiency = 0.0")
        
        # Verifica il numero di record aggiornati
        cursor.execute("SELECT COUNT(*) FROM batch_nesting")
        count = cursor.fetchone()[0]
        print(f"📊 Totale batch nel database: {count}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Operazione completata con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiunta del campo: {str(e)}")
        return False

def verify_field_added():
    """Verifica che il campo sia stato aggiunto correttamente"""
    try:
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        print("\n🔍 Verifica finale dello schema...")
        
        # Controlla lo schema aggiornato
        cursor.execute("PRAGMA table_info(batch_nesting)")
        columns = cursor.fetchall()
        
        efficiency_found = False
        for col in columns:
            if col[1] == 'efficiency':
                efficiency_found = True
                print(f"✅ Campo 'efficiency' trovato: {col[1]} ({col[2]}) | DEFAULT: {col[4]}")
                break
        
        if not efficiency_found:
            print("❌ Campo 'efficiency' non trovato!")
            return False
        
        # Verifica i valori dei record esistenti
        cursor.execute("SELECT COUNT(*) FROM batch_nesting WHERE efficiency IS NOT NULL")
        count_not_null = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM batch_nesting")
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Record con efficiency NOT NULL: {count_not_null}/{total_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Avvio aggiunta campo efficiency...")
    
    if add_efficiency_field():
        verify_field_added()
    else:
        sys.exit(1) 