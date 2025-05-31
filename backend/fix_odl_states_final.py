#!/usr/bin/env python3
"""
🔧 SCRIPT PER CORREGGERE STATI ODL
==================================

Risolve tutti i problemi di compatibilità degli stati ODL.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import text
from models.db import SessionLocal, engine
from models.odl import ODL
from collections import Counter

def fix_odl_states_final():
    """Corregge definitivamente gli stati ODL"""
    try:
        print("🔧 Correzione definitiva stati ODL...")
        
        db = SessionLocal()
        
        # 1. Controlla stati attuali
        print("\n📊 Stati attuali:")
        odls = db.query(ODL).all()
        states = Counter([odl.status for odl in odls])
        for state, count in states.items():
            print(f"   • {state}: {count}")
        
        # 2. Mapping di correzione stati
        state_mapping = {
            "Terminato": "Finito",
            "terminato": "Finito", 
            "TERMINATO": "Finito",
            "In Cura": "Cura",
            "in_cura": "Cura",
            "Attesa Cura": "Attesa Cura",  # Questo è già corretto
            "attesa_cura": "Attesa Cura",
            "in_attesa_cura": "Attesa Cura"
        }
        
        # 3. Esegui correzioni con SQL diretto
        corrections_made = 0
        for old_state, new_state in state_mapping.items():
            result = db.execute(text(f"""
                UPDATE odl 
                SET status = :new_state 
                WHERE status = :old_state
            """), {"new_state": new_state, "old_state": old_state})
            
            if result.rowcount > 0:
                print(f"   ✅ Aggiornati {result.rowcount} ODL da '{old_state}' a '{new_state}'")
                corrections_made += result.rowcount
        
        db.commit()
        
        # 4. Verifica finale
        print(f"\n✅ Correzioni completate: {corrections_made} ODL aggiornati")
        
        # 5. Mostra stati finali
        print("\n📊 Stati finali:")
        odls = db.query(ODL).all()
        final_states = Counter([odl.status for odl in odls])
        for state, count in final_states.items():
            print(f"   • {state}: {count}")
        
        # 6. Verifica che tutti gli stati siano validi
        valid_states = {"Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"}
        invalid_states = set(final_states.keys()) - valid_states
        
        if invalid_states:
            print(f"\n⚠️ ATTENZIONE: Stati ancora non validi: {invalid_states}")
            
            # Correggi stati rimasti non validi -> Preparazione
            for invalid_state in invalid_states:
                result = db.execute(text("""
                    UPDATE odl 
                    SET status = 'Preparazione' 
                    WHERE status = :invalid_state
                """), {"invalid_state": invalid_state})
                
                if result.rowcount > 0:
                    print(f"   🔧 Portati {result.rowcount} ODL da '{invalid_state}' a 'Preparazione'")
            
            db.commit()
        else:
            print("\n✅ Tutti gli stati sono ora validi!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la correzione: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    fix_odl_states_final() 