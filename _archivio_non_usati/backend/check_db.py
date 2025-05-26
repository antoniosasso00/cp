#!/usr/bin/env python3
"""
Script per controllare lo stato del database e aggiornare i record esistenti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_db
from models.nesting_result import NestingResult
from sqlalchemy import text

def main():
    db = next(get_db())
    
    try:
        # Controlla se la colonna stato esiste (SQLite)
        result = db.execute(text("PRAGMA table_info(nesting_results)"))
        columns = [row[1] for row in result.fetchall()]
        stato_exists = 'stato' in columns
        
        print(f"Colonne esistenti: {columns}")
        print(f"Colonna 'stato' esiste: {stato_exists}")
        
        # Controlla i record esistenti
        try:
            results = db.query(NestingResult).all()
            print(f"Numero di nesting results: {len(results)}")
            
            if results:
                for r in results[:5]:
                    print(f"ID: {r.id}, created_at: {r.created_at}")
        except Exception as e:
            print(f"Errore nel query dei nesting results: {e}")
                
        # Se la colonna stato non esiste, possiamo procedere con la migrazione
        if not stato_exists:
            print("La colonna stato non esiste ancora. La migrazione può procedere.")
        else:
            print("La colonna stato esiste già. Controlliamo i valori...")
            # Controlla valori null
            null_count = db.execute(text("SELECT COUNT(*) FROM nesting_results WHERE stato IS NULL")).fetchone()[0]
            print(f"Record con stato NULL: {null_count}")
            
            if null_count > 0:
                print("Aggiornamento dei record con stato NULL...")
                db.execute(text("UPDATE nesting_results SET stato = 'In sospeso' WHERE stato IS NULL"))
                db.commit()
                print("Record aggiornati con successo!")
        
    except Exception as e:
        print(f"Errore: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 