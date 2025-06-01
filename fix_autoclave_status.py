#!/usr/bin/env python3
"""
🔧 SCRIPT PER AGGIORNARE STATO AUTOCLAVI
=========================================

Questo script aggiorna lo stato delle autoclavi per renderle disponibili
per il nesting e risolve il problema di "Nessuna autoclave disponibile".
"""

import sqlite3
from datetime import datetime

def fix_autoclave_status():
    """Aggiorna lo stato delle autoclavi a 'Disponibile'"""
    
    print("🔧 AGGIORNAMENTO STATO AUTOCLAVI")
    print("=" * 40)
    
    try:
        # Connessione al database
        conn = sqlite3.connect('carbonpilot.db')
        cursor = conn.cursor()
        
        # Verifica stato attuale
        cursor.execute("""
            SELECT id, nome, stato 
            FROM autoclavi 
            ORDER BY id
        """)
        autoclavi = cursor.fetchall()
        
        print(f"📊 Stato attuale autoclavi:")
        for autoclave in autoclavi:
            print(f"  Autoclave {autoclave[0]}: {autoclave[1]} - {autoclave[2]}")
        
        # Aggiorna tutte le autoclavi a 'Disponibile' (eccetto quelle guaste)
        cursor.execute("""
            UPDATE autoclavi 
            SET stato = 'Disponibile',
                updated_at = ?
            WHERE stato != 'Guasto'
        """, (datetime.now().isoformat(),))
        
        rows_updated = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ {rows_updated} autoclavi aggiornate a 'Disponibile'")
        
        # Verifica risultato
        cursor.execute("""
            SELECT stato, COUNT(*) 
            FROM autoclavi 
            GROUP BY stato
        """)
        status_counts = dict(cursor.fetchall())
        
        print(f"📊 Nuova distribuzione stati:")
        for stato, count in status_counts.items():
            print(f"  {stato}: {count}")
        
        conn.close()
        
        if status_counts.get('Disponibile', 0) > 0:
            print(f"\n🎉 Problema risolto! {status_counts['Disponibile']} autoclavi ora disponibili")
            return True
        else:
            print(f"\n❌ Problema non risolto - nessuna autoclave disponibile")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {str(e)}")
        return False

if __name__ == "__main__":
    fix_autoclave_status() 