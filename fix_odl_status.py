#!/usr/bin/env python3
"""
Script per correggere gli stati degli ODL nel database.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import engine
from sqlalchemy import text

def fix_odl_status():
    """Corregge gli stati degli ODL nel database."""
    print("🔧 Correzione stati ODL...")
    
    with engine.connect() as conn:
        # Prima vediamo gli stati attuali
        result = conn.execute(text("SELECT id, status FROM odl"))
        odl_list = result.fetchall()
        
        print(f"📋 Stati ODL attuali:")
        for odl in odl_list:
            print(f"  - ODL {odl[0]}: {odl[1]}")
        
        # Aggiorna tutti gli ODL allo stato "Attesa Cura"
        result = conn.execute(text("UPDATE odl SET status = 'Attesa Cura'"))
        print(f"✅ Aggiornati {result.rowcount} ODL allo stato 'Attesa Cura'")
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        result = conn.execute(text("SELECT id, status FROM odl"))
        odl_list = result.fetchall()
        
        print(f"📋 Stati ODL dopo correzione:")
        for odl in odl_list:
            print(f"  - ODL {odl[0]}: {odl[1]}")

if __name__ == "__main__":
    fix_odl_status()
    print("🎉 Correzione completata!") 