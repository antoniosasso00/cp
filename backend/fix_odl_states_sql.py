#!/usr/bin/env python3
"""
🔧 SCRIPT PER CORREGGERE STATI ODL CON SQL DIRETTO
=================================================

Corregge gli stati ODL usando SQL diretto per evitare problemi con enum.
"""

import sqlite3
import os

def fix_odl_states_sql():
    """Corregge gli stati ODL usando SQL diretto"""
    try:
        print("🔧 Correzione stati ODL con SQL diretto...")
        
        # Connessione diretta al database SQLite
        db_path = os.path.join(os.path.dirname(__file__), 'carbonpilot.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Controlla stati attuali
        print("\n📊 Stati attuali:")
        cursor.execute("SELECT status, COUNT(*) FROM odl GROUP BY status")
        current_states = cursor.fetchall()
        for state, count in current_states:
            print(f"   • {state}: {count}")
        
        # 2. Mapping di correzione stati
        state_corrections = [
            ("Terminato", "Finito"),
            ("terminato", "Finito"), 
            ("TERMINATO", "Finito"),
            ("In Cura", "Cura"),
            ("in_cura", "Cura"),
            ("attesa_cura", "Attesa Cura"),
            ("in_attesa_cura", "Attesa Cura"),
            ("cura", "Cura"),
            ("laminazione", "Laminazione"),
            ("preparazione", "Preparazione"),
            ("finito", "Finito")
        ]
        
        # 3. Esegui correzioni
        total_corrections = 0
        for old_state, new_state in state_corrections:
            cursor.execute("UPDATE odl SET status = ? WHERE status = ?", (new_state, old_state))
            corrections = cursor.rowcount
            if corrections > 0:
                print(f"   ✅ Aggiornati {corrections} ODL da '{old_state}' a '{new_state}'")
                total_corrections += corrections
        
        # 4. Verifica che tutti gli stati siano validi
        valid_states = {"Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"}
        cursor.execute("SELECT DISTINCT status FROM odl")
        current_states_after = {row[0] for row in cursor.fetchall()}
        invalid_states = current_states_after - valid_states
        
        if invalid_states:
            print(f"\n⚠️ ATTENZIONE: Stati ancora non validi: {invalid_states}")
            
            # Correggi stati rimasti non validi -> Preparazione
            for invalid_state in invalid_states:
                cursor.execute("UPDATE odl SET status = 'Preparazione' WHERE status = ?", (invalid_state,))
                corrections = cursor.rowcount
                if corrections > 0:
                    print(f"   🔧 Portati {corrections} ODL da '{invalid_state}' a 'Preparazione'")
                    total_corrections += corrections
        
        # 5. Commit delle modifiche
        conn.commit()
        
        # 6. Verifica finale
        print(f"\n✅ Correzioni completate: {total_corrections} ODL aggiornati")
        
        print("\n📊 Stati finali:")
        cursor.execute("SELECT status, COUNT(*) FROM odl GROUP BY status")
        final_states = cursor.fetchall()
        for state, count in final_states:
            print(f"   • {state}: {count}")
        
        # 7. Verifica che tutti gli stati siano ora validi
        cursor.execute("SELECT DISTINCT status FROM odl")
        final_states_set = {row[0] for row in cursor.fetchall()}
        remaining_invalid = final_states_set - valid_states
        
        if remaining_invalid:
            print(f"\n❌ ERRORE: Stati ancora non validi: {remaining_invalid}")
            return False
        else:
            print("\n✅ Tutti gli stati sono ora validi!")
            return True
        
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = fix_odl_states_sql()
    if success:
        print("\n🎉 Correzione completata con successo!")
    else:
        print("\n💥 Correzione fallita!") 