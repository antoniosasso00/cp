"""
Script per aggiornare manualmente lo schema del database SQLite
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from models.db import SessionLocal, engine

def update_database_schema():
    """Aggiorna lo schema del database aggiungendo le colonne mancanti"""
    db = SessionLocal()
    
    try:
        # Aggiungi colonne al catalogo se non esistono
        catalogo_columns = [
            "ALTER TABLE cataloghi ADD COLUMN lunghezza REAL",
            "ALTER TABLE cataloghi ADD COLUMN larghezza REAL", 
            "ALTER TABLE cataloghi ADD COLUMN altezza REAL"
        ]
        
        for sql in catalogo_columns:
            try:
                db.execute(text(sql))
                print(f"✅ Eseguito: {sql}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️  Colonna già esistente: {sql}")
                else:
                    print(f"❌ Errore: {sql} - {e}")
        
        # Aggiungi colonne al nesting_results se non esistono
        nesting_columns = [
            "ALTER TABLE nesting_results ADD COLUMN odl_esclusi_ids TEXT",
            "ALTER TABLE nesting_results ADD COLUMN motivi_esclusione TEXT",
            "ALTER TABLE nesting_results ADD COLUMN stato TEXT DEFAULT 'In attesa schedulazione'",
            "ALTER TABLE nesting_results ADD COLUMN note TEXT",
            "ALTER TABLE nesting_results ADD COLUMN updated_at DATETIME"
        ]
        
        for sql in nesting_columns:
            try:
                db.execute(text(sql))
                print(f"✅ Eseguito: {sql}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️  Colonna già esistente: {sql}")
                else:
                    print(f"❌ Errore: {sql} - {e}")
        
        db.commit()
        print("✅ Schema del database aggiornato con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento dello schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_database_schema() 