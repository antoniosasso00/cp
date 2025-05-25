"""
Script per aggiungere la colonna confermato_da_ruolo alla tabella nesting_results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from models.db import SessionLocal, engine

def fix_nesting_schema():
    """Aggiunge la colonna confermato_da_ruolo alla tabella nesting_results"""
    db = SessionLocal()
    
    try:
        print("🔧 Aggiornamento schema tabella nesting_results...")
        
        # Aggiungi la colonna confermato_da_ruolo se non esiste
        sql = "ALTER TABLE nesting_results ADD COLUMN confermato_da_ruolo VARCHAR(50)"
        
        try:
            db.execute(text(sql))
            db.commit()
            print("✅ Colonna 'confermato_da_ruolo' aggiunta con successo!")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⚠️  Colonna 'confermato_da_ruolo' già esistente")
            else:
                print(f"❌ Errore nell'aggiunta della colonna: {e}")
                db.rollback()
                return False
        
        # Verifica che la colonna sia stata aggiunta
        result = db.execute(text("PRAGMA table_info(nesting_results)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'confermato_da_ruolo' in columns:
            print("✅ Verifica completata: colonna 'confermato_da_ruolo' presente")
            return True
        else:
            print("❌ Verifica fallita: colonna 'confermato_da_ruolo' non trovata")
            return False
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento dello schema: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_nesting_schema()
    if success:
        print("\n🎯 Schema aggiornato correttamente! Gli endpoint nesting dovrebbero ora funzionare.")
    else:
        print("\n💥 Aggiornamento fallito. Controlla i log per maggiori dettagli.") 