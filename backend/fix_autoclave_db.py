#!/usr/bin/env python3
"""
Script per aggiornare il database del backend aggiungendo il campo superficie_piano_2_max
"""

from models.db import engine, get_db
from models.autoclave import Autoclave
from sqlalchemy import text

def fix_autoclave_schema():
    """Aggiorna lo schema delle autoclavi nel database del backend"""
    try:
        with engine.connect() as conn:
            # Verifica se il campo esiste già
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            columns = [col[1] for col in result]
            
            print("🔍 Colonne attuali:")
            for col in result:
                print(f"   {col[1]} ({col[2]})")
            
            if 'superficie_piano_2_max' not in columns:
                print("\n🔧 Aggiunta campo superficie_piano_2_max...")
                conn.execute(text("ALTER TABLE autoclavi ADD COLUMN superficie_piano_2_max FLOAT"))
                conn.commit()
                print("✅ Campo superficie_piano_2_max aggiunto!")
            else:
                print("\nℹ️ Campo superficie_piano_2_max già presente")
                return True
            
            # Aggiorna i valori di default per le autoclavi esistenti
            print("🔧 Aggiornamento valori di default...")
            db = next(get_db())
            autoclavi = db.query(Autoclave).all()
            
            for autoclave in autoclavi:
                if autoclave.superficie_piano_2_max is None:
                    # Imposta superficie piano 2 come 80% del piano principale
                    area_piano = autoclave.area_piano if autoclave.area_piano else 10000.0
                    autoclave.superficie_piano_2_max = area_piano * 0.8
                    print(f"   ✅ {autoclave.nome}: superficie_piano_2_max = {autoclave.superficie_piano_2_max:.1f} cm²")
            
            db.commit()
            print("✅ Aggiornamento completato!")
            
            # Verifica finale
            result = conn.execute(text("PRAGMA table_info(autoclavi)")).fetchall()
            columns = [col[1] for col in result]
            if 'superficie_piano_2_max' in columns:
                print("🎯 Verifica: Campo superficie_piano_2_max presente!")
                return True
            else:
                print("❌ Verifica: Campo superficie_piano_2_max NON presente!")
                return False
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fix Schema Autoclave Database Backend")
    print("=" * 60)
    
    success = fix_autoclave_schema()
    
    if success:
        print("\n🎯 Schema aggiornato con successo!")
    else:
        print("\n❌ Aggiornamento fallito!") 