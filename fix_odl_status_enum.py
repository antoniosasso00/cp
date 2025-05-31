#!/usr/bin/env python3
"""
Script per correggere gli status ODL non validi nel database
"""

import sqlite3
import os
from datetime import datetime

def fix_odl_status():
    """Corregge gli status ODL non validi nel database"""
    
    # Status validi secondo il modello
    valid_statuses = [
        "Preparazione", 
        "Laminazione", 
        "In Coda", 
        "Attesa Cura", 
        "Cura", 
        "Finito"
    ]
    
    # Mapping per correggere status non validi
    status_mapping = {
        "Completato": "Finito",
        "Completed": "Finito",
        "Done": "Finito",
        "Terminato": "Finito",
        "In Attesa": "Attesa Cura",
        "Waiting": "Attesa Cura",
        "Processing": "Cura",
        "In Lavorazione": "Laminazione"
    }
    
    try:
        # Connetti al database
        db_path = os.path.join('backend', 'carbonpilot.db')
        if not os.path.exists(db_path):
            db_path = 'carbonpilot.db'
        
        if not os.path.exists(db_path):
            print("❌ Database non trovato!")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 CORREZIONE STATUS ODL NON VALIDI")
        print("=" * 50)
        
        # Trova tutti gli status unici nel database
        cursor.execute("SELECT DISTINCT status FROM odl ORDER BY status")
        current_statuses = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 STATUS ATTUALI NEL DATABASE:")
        for status in current_statuses:
            cursor.execute("SELECT COUNT(*) FROM odl WHERE status = ?", (status,))
            count = cursor.fetchone()[0]
            is_valid = "✅" if status in valid_statuses else "❌"
            print(f"  {is_valid} {status}: {count} ODL")
        
        # Controlla anche previous_status
        cursor.execute("SELECT DISTINCT previous_status FROM odl WHERE previous_status IS NOT NULL ORDER BY previous_status")
        previous_statuses = [row[0] for row in cursor.fetchall()]
        
        if previous_statuses:
            print(f"\n📊 PREVIOUS_STATUS ATTUALI NEL DATABASE:")
            for status in previous_statuses:
                cursor.execute("SELECT COUNT(*) FROM odl WHERE previous_status = ?", (status,))
                count = cursor.fetchone()[0]
                is_valid = "✅" if status in valid_statuses else "❌"
                print(f"  {is_valid} {status}: {count} ODL")
        
        # Trova status non validi
        invalid_statuses = [s for s in current_statuses if s not in valid_statuses]
        invalid_previous_statuses = [s for s in previous_statuses if s not in valid_statuses]
        
        if not invalid_statuses and not invalid_previous_statuses:
            print("\n✅ Tutti gli status sono validi!")
            conn.close()
            return True
        
        print(f"\n🔧 STATUS DA CORREGGERE:")
        if invalid_statuses:
            print(f"   Status: {invalid_statuses}")
        if invalid_previous_statuses:
            print(f"   Previous Status: {invalid_previous_statuses}")
        
        # Prima correggi i previous_status non validi
        total_fixed = 0
        if invalid_previous_statuses:
            print(f"\n🔄 Correggendo previous_status non validi...")
            for invalid_status in invalid_previous_statuses:
                new_status = status_mapping.get(invalid_status, "Preparazione")
                
                cursor.execute("SELECT COUNT(*) FROM odl WHERE previous_status = ?", (invalid_status,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"   🔄 Correggendo {count} ODL con previous_status '{invalid_status}' -> '{new_status}'...")
                    
                    # Aggiorna previous_status
                    cursor.execute("""
                        UPDATE odl 
                        SET previous_status = ?,
                            updated_at = ?
                        WHERE previous_status = ?
                    """, (new_status, datetime.now().isoformat(), invalid_status))
                    
                    updated_count = cursor.rowcount
                    total_fixed += updated_count
                    print(f"      ✅ Aggiornati {updated_count} ODL")
        
        # Poi correggi gli status principali non validi
        if invalid_statuses:
            print(f"\n🔄 Correggendo status principali non validi...")
            for invalid_status in invalid_statuses:
                new_status = status_mapping.get(invalid_status, "Finito")
                
                cursor.execute("SELECT COUNT(*) FROM odl WHERE status = ?", (invalid_status,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"   🔄 Correggendo {count} ODL da status '{invalid_status}' -> '{new_status}'...")
                    
                    # Aggiorna status (senza toccare previous_status se già corretto)
                    cursor.execute("""
                        UPDATE odl 
                        SET status = ?,
                            updated_at = ?
                        WHERE status = ?
                    """, (new_status, datetime.now().isoformat(), invalid_status))
                    
                    updated_count = cursor.rowcount
                    total_fixed += updated_count
                    print(f"      ✅ Aggiornati {updated_count} ODL")
        
        # Commit delle modifiche
        conn.commit()
        
        print(f"\n🎉 CORREZIONE COMPLETATA!")
        print(f"   📊 Totale ODL corretti: {total_fixed}")
        
        # Verifica finale
        print(f"\n🔍 VERIFICA FINALE:")
        cursor.execute("SELECT DISTINCT status FROM odl ORDER BY status")
        final_statuses = [row[0] for row in cursor.fetchall()]
        
        all_valid = True
        for status in final_statuses:
            cursor.execute("SELECT COUNT(*) FROM odl WHERE status = ?", (status,))
            count = cursor.fetchone()[0]
            is_valid = status in valid_statuses
            if not is_valid:
                all_valid = False
            icon = "✅" if is_valid else "❌"
            print(f"  {icon} {status}: {count} ODL")
        
        # Verifica previous_status
        cursor.execute("SELECT DISTINCT previous_status FROM odl WHERE previous_status IS NOT NULL ORDER BY previous_status")
        final_previous_statuses = [row[0] for row in cursor.fetchall()]
        
        if final_previous_statuses:
            print(f"\n🔍 VERIFICA PREVIOUS_STATUS:")
            for status in final_previous_statuses:
                cursor.execute("SELECT COUNT(*) FROM odl WHERE previous_status = ?", (status,))
                count = cursor.fetchone()[0]
                is_valid = status in valid_statuses
                if not is_valid:
                    all_valid = False
                icon = "✅" if is_valid else "❌"
                print(f"  {icon} {status}: {count} ODL")
        
        conn.close()
        
        if all_valid:
            print(f"\n✅ Tutti gli status sono ora validi!")
            return True
        else:
            print(f"\n⚠️  Ci sono ancora status non validi!")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AVVIO CORREZIONE STATUS ODL")
    print("=" * 50)
    
    success = fix_odl_status()
    
    if success:
        print("\n🎯 Ora puoi testare nuovamente l'API ODL!")
        print("   Comando: python test_api_debug.py")
    else:
        print("\n❌ Correzione fallita. Controlla i log sopra.") 