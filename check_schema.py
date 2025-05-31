#!/usr/bin/env python3
"""
Script per verificare lo schema del database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import engine
from sqlalchemy import text

def check_schema():
    """Verifica lo schema del database"""
    try:
        with engine.connect() as conn:
            # Verifica colonne autoclavi
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            print("🔍 Colonne tabella autoclavi:")
            for col in result:
                print(f"   {col[1]} ({col[2]})")
            
            # Verifica se superficie_piano_2_max esiste
            columns = [col[1] for col in result]
            if 'superficie_piano_2_max' in columns:
                print("✅ Campo superficie_piano_2_max presente")
            else:
                print("❌ Campo superficie_piano_2_max mancante")
                
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    print("🔍 Verifica Schema Database")
    print("=" * 40)
    check_schema() 