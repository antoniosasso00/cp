#!/usr/bin/env python3
"""
Controlla l'ID dell'autoclave di test
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Imposta variabili d'ambiente per SQLite
os.environ["DATABASE_URL"] = "sqlite:///./carbonpilot.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./carbonpilot.db"

from sqlalchemy.orm import Session
from api.database import get_db
from models.autoclave import Autoclave

def check_autoclave():
    """Controlla l'ID dell'autoclave di test"""
    
    db_gen = get_db()
    db = next(db_gen)
    
    # Trova autoclave di test
    autoclave = db.query(Autoclave).filter(
        Autoclave.nome == "EdgeTest-Autoclave"
    ).first()
    
    if autoclave:
        print(f"✅ Autoclave di test trovata:")
        print(f"   - ID: {autoclave.id}")
        print(f"   - Nome: {autoclave.nome}")
        print(f"   - Codice: {autoclave.codice}")
        print(f"   - Dimensioni: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm")
        print(f"   - Max load: {autoclave.max_load_kg}kg")
    else:
        print("❌ Autoclave di test non trovata")
        
        # Lista tutte le autoclavi
        all_autoclavi = db.query(Autoclave).all()
        print(f"📋 Autoclavi presenti ({len(all_autoclavi)}):")
        for a in all_autoclavi:
            print(f"   - ID {a.id}: {a.nome} ({a.codice})")
    
    db.close()

if __name__ == "__main__":
    check_autoclave() 