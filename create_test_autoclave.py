#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.db import SessionLocal
from backend.models.autoclave import Autoclave, StatoAutoclaveEnum

def create_test_autoclave():
    db = SessionLocal()
    try:
        # Controlla se l'autoclave esiste già
        existing = db.query(Autoclave).filter(Autoclave.nome == "AeroTest-v1.4.12").first()
        if existing:
            print(f"✅ Autoclave già esistente: ID {existing.id}")
            return existing.id
        
        # Crea nuova autoclave
        autoclave = Autoclave(
            nome="AeroTest-v1.4.12",
            codice="AT-V1412",
            lunghezza=2000.0,
            larghezza_piano=1200.0,
            num_linee_vuoto=8,
            temperatura_max=180.0,
            pressione_max=7.0,
            max_load_kg=500.0,
            stato=StatoAutoclaveEnum.DISPONIBILE,
            produttore="AeroTech Systems",
            anno_produzione=2023,
            note="Autoclave per test algoritmo nesting v1.4.12-DEMO"
        )
        
        db.add(autoclave)
        db.commit()
        
        # Recupera l'ID senza refresh
        autoclave_id = autoclave.id
        print(f"✅ Autoclave creata: ID {autoclave_id}")
        return autoclave_id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_autoclave() 