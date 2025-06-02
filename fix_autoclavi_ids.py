#!/usr/bin/env python3
"""
🔧 Fix per gli ID NULL delle autoclavi
"""

import sys
import os

# Cambia directory al backend
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append('.')

from sqlalchemy import text
from models.db import SessionLocal

def fix_autoclavi_ids():
    """Corregge gli ID NULL delle autoclavi"""
    
    print("🔧 FIX ID AUTOCLAVI NULL")
    print("="*40)
    
    db = SessionLocal()
    try:
        # 1. Verifica situazione attuale
        result = db.execute(text("SELECT id, nome, codice FROM autoclavi"))
        autoclavi = result.fetchall()
        
        print(f"📊 Autoclavi nel database:")
        for autoclave in autoclavi:
            print(f"   ID: {autoclave[0]} | Nome: {autoclave[1]} | Codice: {autoclave[2]}")
        
        # 2. Conta autoclavi con ID NULL
        null_ids = db.execute(text("SELECT COUNT(*) FROM autoclavi WHERE id IS NULL")).scalar()
        print(f"\n⚠️  Autoclavi con ID NULL: {null_ids}")
        
        if null_ids > 0:
            print(f"\n🔧 Rimozione autoclavi con ID NULL...")
            
            # Elimina autoclavi con ID NULL
            db.execute(text("DELETE FROM autoclavi WHERE id IS NULL"))
            
            # Crea un'autoclave di test con ID valido
            print(f"📝 Creazione autoclave di test...")
            db.execute(text("""
                INSERT INTO autoclavi (
                    nome, codice, lunghezza, larghezza_piano, 
                    temperatura_max, pressione_max, max_load_kg, 
                    num_linee_vuoto, stato, produttore, 
                    anno_produzione, created_at, updated_at
                ) VALUES (
                    'AeroTest-Fixed', 'AERO-FIXED-001', 2000.0, 1200.0,
                    200.0, 8.0, 1000.0, 
                    10, 'DISPONIBILE', 'MantaGroup',
                    2024, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """))
            
            db.commit()
            print(f"✅ Fix completato!")
            
            # Verifica risultato
            result = db.execute(text("SELECT id, nome, codice, stato FROM autoclavi"))
            autoclavi_fixed = result.fetchall()
            
            print(f"\n📊 Autoclavi dopo il fix:")
            for autoclave in autoclavi_fixed:
                print(f"   ID: {autoclave[0]} | Nome: {autoclave[1]} | Codice: {autoclave[2]} | Stato: {autoclave[3]}")
            
            return True
        else:
            print(f"✅ Nessun problema trovato con gli ID")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante il fix: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_autoclavi_ids()
    sys.exit(0 if success else 1) 