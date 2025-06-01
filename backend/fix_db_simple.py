#!/usr/bin/env python3
"""
Script semplice per correggere gli stati ODL non validi
"""

import sqlite3

def fix_database():
    print("🔧 Correzione database ODL...")
    
    # Connessione al database
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    try:
        # Mostra stati attuali
        cursor.execute('SELECT DISTINCT status FROM odl')
        stati = cursor.fetchall()
        print("Stati attuali:")
        for stato in stati:
            print(f"  - {stato[0]}")
        
        # Correggi "Terminato" -> "Finito"
        cursor.execute('UPDATE odl SET status = "Finito" WHERE status = "Terminato"')
        changes = cursor.rowcount
        print(f"\n✅ Aggiornati {changes} record da 'Terminato' a 'Finito'")
        
        # Commit
        conn.commit()
        
        # Verifica finale
        cursor.execute('SELECT DISTINCT status FROM odl')
        stati_finali = cursor.fetchall()
        print("\nStati dopo correzione:")
        for stato in stati_finali:
            print(f"  - {stato[0]}")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database() 