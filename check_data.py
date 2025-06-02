#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.db import SessionLocal
from backend.models.autoclave import Autoclave
from backend.models.odl import ODL

def check_data():
    db = SessionLocal()
    try:
        # Controlla autoclavi
        autoclavi = db.query(Autoclave).all()
        print(f"Autoclavi trovate: {len(autoclavi)}")
        for a in autoclavi:
            print(f"  ID {a.id}: {a.nome}")
        
        # Controlla ODL
        odl_count = db.query(ODL).filter(ODL.status == 'Preparazione').count()
        print(f"ODL in preparazione: {odl_count}")
        
        # Controlla autoclave ID 4
        autoclave_4 = db.query(Autoclave).filter(Autoclave.id == 4).first()
        if autoclave_4:
            print(f"Autoclave 4: {autoclave_4.nome} - {autoclave_4.larghezza_piano}x{autoclave_4.lunghezza}mm")
        else:
            print("Autoclave 4: Non trovata")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_data() 