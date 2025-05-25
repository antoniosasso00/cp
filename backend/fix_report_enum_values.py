#!/usr/bin/env python3
"""
Script per correggere i valori enum nella tabella reports
"""

import sys
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from models.db import get_database_url

def fix_report_enum_values():
    """Corregge i valori enum nella tabella reports"""
    
    # Ottieni l'URL del database
    database_url = get_database_url()
    print(f"🔗 Connessione al database: {database_url}")
    
    # Crea l'engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Verifica i valori attuali
            result = conn.execute(text("SELECT id, filename, report_type FROM reports"))
            reports = result.fetchall()
            
            print(f"📋 Trovati {len(reports)} report nel database")
            
            if not reports:
                print("✅ Nessun report da aggiornare")
                return
            
            # Mostra i valori attuali
            for report in reports:
                print(f"   ID: {report[0]}, File: {report[1]}, Tipo: {report[2]}")
            
            # Mappa di conversione da maiuscolo a minuscolo
            conversion_map = {
                'PRODUZIONE': 'produzione',
                'QUALITA': 'qualita', 
                'TEMPI': 'tempi',
                'COMPLETO': 'completo',
                'NESTING': 'nesting'
            }
            
            # Aggiorna i valori
            updated_count = 0
            for old_value, new_value in conversion_map.items():
                result = conn.execute(
                    text("UPDATE reports SET report_type = :new_value WHERE report_type = :old_value"),
                    {"new_value": new_value, "old_value": old_value}
                )
                if result.rowcount > 0:
                    print(f"🔄 Aggiornati {result.rowcount} record da '{old_value}' a '{new_value}'")
                    updated_count += result.rowcount
            
            # Commit delle modifiche
            conn.commit()
            
            print(f"✅ Aggiornamento completato! {updated_count} record modificati")
            
            # Verifica i valori finali
            result = conn.execute(text("SELECT id, filename, report_type FROM reports"))
            reports = result.fetchall()
            
            print("\n📋 Valori finali:")
            for report in reports:
                print(f"   ID: {report[0]}, File: {report[1]}, Tipo: {report[2]}")
                
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        raise

if __name__ == "__main__":
    try:
        fix_report_enum_values()
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1) 