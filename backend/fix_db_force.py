#!/usr/bin/env python3
"""
Script per forzare la correzione degli stati ODL
"""

import sqlite3
import os

def fix_database():
    print("🔧 Correzione forzata database ODL...")
    
    # Trova il file database
    db_files = ['carbonpilot.db', '../carbonpilot.db', './carbonpilot.db']
    db_path = None
    
    for path in db_files:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ File database non trovato!")
        return
    
    print(f"📁 Usando database: {db_path}")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Mostra tutti gli ODL con i loro stati
        cursor.execute('SELECT id, status FROM odl ORDER BY id')
        odl_list = cursor.fetchall()
        print(f"\n📊 Trovati {len(odl_list)} ODL nel database:")
        
        stati_count = {}
        for odl_id, status in odl_list:
            print(f"  ODL {odl_id}: {status}")
            stati_count[status] = stati_count.get(status, 0) + 1
        
        print(f"\n📈 Conteggio stati:")
        for stato, count in stati_count.items():
            print(f"  {stato}: {count}")
        
        # Correggi tutti gli stati non validi
        corrections = {
            'Terminato': 'Finito',
            'terminato': 'Finito',
            'TERMINATO': 'Finito',
            'In Cura': 'Cura',
            'in_cura': 'Cura',
            'IN_CURA': 'Cura'
        }
        
        total_changes = 0
        for old_status, new_status in corrections.items():
            cursor.execute('UPDATE odl SET status = ? WHERE status = ?', (new_status, old_status))
            changes = cursor.rowcount
            if changes > 0:
                print(f"✅ Aggiornati {changes} record da '{old_status}' a '{new_status}'")
                total_changes += changes
        
        # Commit
        conn.commit()
        print(f"\n🎉 Totale modifiche: {total_changes}")
        
        # Verifica finale
        cursor.execute('SELECT DISTINCT status FROM odl')
        stati_finali = cursor.fetchall()
        print("\n📋 Stati finali nel database:")
        for stato in stati_finali:
            print(f"  - {stato[0]}")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database() 