#!/usr/bin/env python3
"""
🔧 SCRIPT PER VERIFICARE E CREARE TABELLE
==========================================

Verifica l'esistenza delle tabelle e le crea se necessario.
"""

import sys
import os

# Aggiungi il path del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import text, inspect
from backend.models.db import engine, Base
from backend.models import *

def check_and_create_tables():
    """Verifica e crea tutte le tabelle necessarie"""
    try:
        print("🔍 Verifica tabelle esistenti...")
        
        # Verifica tabelle esistenti
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result]
            
        print(f"📋 Tabelle esistenti: {sorted(existing_tables)}")
        
        # Crea tutte le tabelle
        print("🔧 Creazione tabelle mancanti...")
        Base.metadata.create_all(engine)
        
        # Verifica dopo la creazione
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            final_tables = [row[0] for row in result]
            
        print(f"✅ Tabelle finali: {sorted(final_tables)}")
        print(f"📊 Totale tabelle: {len(final_tables)}")
        
        # Verifica specificamente batch_nesting
        if 'batch_nesting' in final_tables:
            print("✅ Tabella batch_nesting presente")
        else:
            print("❌ Tabella batch_nesting mancante")
            
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    success = check_and_create_tables()
    sys.exit(0 if success else 1) 