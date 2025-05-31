#!/usr/bin/env python3
"""Script per controllare gli stati ODL nel database"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from models.db import SessionLocal
from models.odl import ODL
from collections import Counter

def check_odl_states():
    """Controlla gli stati ODL presenti nel database"""
    try:
        print("🔍 Controllo stati ODL nel database...")
        
        db = SessionLocal()
        odls = db.query(ODL).all()
        
        print(f"📋 Totale ODL: {len(odls)}")
        
        # Conta stati
        states = Counter([odl.status for odl in odls])
        
        print("\n📊 Stati ODL presenti:")
        for state, count in states.items():
            print(f"   • {state}: {count}")
        
        # Mostra alcuni ODL di esempio
        print("\n🔍 Esempi ODL (primi 5):")
        for odl in odls[:5]:
            print(f"   • ODL {odl.id}: {odl.status} (Parte: {odl.parte_id})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    check_odl_states() 