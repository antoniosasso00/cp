#!/usr/bin/env python3
"""
Script per ricreare la tabella reports con l'enum corretto
"""

import sys
import os
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from models.db import get_database_url
from models.report import Report

def recreate_reports_table():
    """Ricrea la tabella reports con l'enum corretto"""
    
    # Ottieni l'URL del database
    database_url = get_database_url()
    print(f"🔗 Connessione al database: {database_url}")
    
    # Crea l'engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Backup dei dati esistenti
            print("📋 Backup dei dati esistenti...")
            result = conn.execute(text("SELECT * FROM reports"))
            existing_reports = result.fetchall()
            
            print(f"   Trovati {len(existing_reports)} report da preservare")
            
            # Elimina la tabella esistente
            print("🗑️ Eliminazione tabella reports esistente...")
            conn.execute(text("DROP TABLE IF EXISTS reports"))
            
            # Commit della cancellazione
            conn.commit()
            
        # Ricrea la tabella con la nuova definizione
        print("🔨 Creazione nuova tabella reports...")
        Report.__table__.create(engine)
        
        # Ripristina i dati con i valori corretti
        if existing_reports:
            print("📥 Ripristino dei dati con valori enum corretti...")
            
            with engine.connect() as conn:
                for report_data in existing_reports:
                    # Mappa i valori enum
                    old_type = report_data[3]  # report_type è la 4a colonna (indice 3)
                    new_type = old_type.lower() if old_type else 'nesting'
                    
                    # Inserisci il record con il nuovo valore enum
                    conn.execute(text("""
                        INSERT INTO reports (
                            id, filename, file_path, report_type, generated_for_user_id,
                            period_start, period_end, include_sections, file_size_bytes,
                            created_at, updated_at
                        ) VALUES (:id, :filename, :file_path, :report_type, :generated_for_user_id,
                                 :period_start, :period_end, :include_sections, :file_size_bytes,
                                 :created_at, :updated_at)
                    """), {
                        'id': report_data[0],
                        'filename': report_data[1],
                        'file_path': report_data[2],
                        'report_type': new_type,
                        'generated_for_user_id': report_data[4],
                        'period_start': report_data[5],
                        'period_end': report_data[6],
                        'include_sections': report_data[7],
                        'file_size_bytes': report_data[8],
                        'created_at': report_data[9],
                        'updated_at': report_data[10]
                    })
                
                conn.commit()
                print(f"   Ripristinati {len(existing_reports)} report")
        
        print("✅ Tabella reports ricreata con successo!")
        
        # Verifica finale
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, filename, report_type FROM reports"))
            final_reports = result.fetchall()
            
            print("\n📋 Report finali:")
            for report in final_reports:
                print(f"   ID: {report[0]}, File: {report[1]}, Tipo: {report[2]}")
                
    except Exception as e:
        print(f"❌ Errore durante la ricreazione della tabella: {e}")
        raise

if __name__ == "__main__":
    try:
        recreate_reports_table()
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1) 