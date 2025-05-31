#!/usr/bin/env python3
"""
Script per aggiornare lo schema del database aggiungendo il campo superficie_piano_2_max
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import engine, get_db
from models.autoclave import Autoclave
from sqlalchemy import text

def update_autoclave_schema():
    """Aggiorna lo schema delle autoclavi aggiungendo il campo superficie_piano_2_max"""
    try:
        with engine.connect() as conn:
            # Verifica se il campo esiste già
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            columns = [col[1] for col in result]
            
            if 'superficie_piano_2_max' not in columns:
                print("🔧 Aggiunta campo superficie_piano_2_max...")
                conn.execute(text("ALTER TABLE autoclavi ADD COLUMN superficie_piano_2_max FLOAT"))
                conn.commit()
                print("✅ Campo superficie_piano_2_max aggiunto con successo!")
            else:
                print("ℹ️ Campo superficie_piano_2_max già presente")
            
            # Aggiorna i valori di default per le autoclavi esistenti
            print("🔧 Aggiornamento valori di default...")
            db = next(get_db())
            autoclavi = db.query(Autoclave).all()
            
            for autoclave in autoclavi:
                if autoclave.superficie_piano_2_max is None:
                    # Imposta superficie piano 2 come 80% del piano principale
                    autoclave.superficie_piano_2_max = autoclave.area_piano * 0.8
                    print(f"   ✅ {autoclave.nome}: superficie_piano_2_max = {autoclave.superficie_piano_2_max:.1f} cm²")
            
            db.commit()
            print("✅ Aggiornamento completato!")
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Aggiornamento Schema Autoclave")
    print("=" * 50)
    
    success = update_autoclave_schema()
    
    if success:
        print("\n🎯 Schema aggiornato con successo!")
    else:
        print("\n❌ Aggiornamento fallito!")
        sys.exit(1) 