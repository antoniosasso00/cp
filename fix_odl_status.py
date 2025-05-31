#!/usr/bin/env python3
"""
🔧 SCRIPT PER AGGIORNARE STATI ODL
==================================

Aggiorna gli stati degli ODL per renderli compatibili con l'enum.
"""

import sys
import os

# Aggiungi il path del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import text
from backend.models.db import engine, SessionLocal

def fix_odl_status():
    """Aggiorna gli stati degli ODL per renderli compatibili"""
    try:
        print("🔧 Aggiornamento stati ODL...")
        
        db = SessionLocal()
        
        # Aggiorna stati non validi
        result = db.execute(text("""
            UPDATE odl 
            SET status = 'Preparazione' 
            WHERE status NOT IN ('Preparazione', 'Pronto', 'Laminazione', 'In Coda', 'Caricato', 'Curato', 'Finito')
        """))
        
        updated_count = result.rowcount
        db.commit()
        
        print(f"✅ Aggiornati {updated_count} ODL con stati non validi")
        
        # Verifica risultato
        result = db.execute(text("SELECT id, status FROM odl"))
        odls = result.fetchall()
        
        print("📋 Stati ODL dopo aggiornamento:")
        for odl in odls:
            print(f"   • ODL {odl[0]}: {odl[1]}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    success = fix_odl_status()
    sys.exit(0 if success else 1) 