#!/usr/bin/env python3
"""
Script per creare la tabella reports nel database esistente
"""

import sys
import os
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, inspect
from models import Base, Report, ReportTypeEnum
from models.db import get_database_url

def create_reports_table():
    """Crea la tabella reports se non esiste già"""
    
    # Ottieni l'URL del database
    database_url = get_database_url()
    print(f"🔗 Connessione al database: {database_url}")
    
    # Crea l'engine
    engine = create_engine(database_url)
    
    # Verifica se la tabella esiste già
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if "reports" in existing_tables:
        print("✅ La tabella 'reports' esiste già nel database")
        
        # Verifica la struttura della tabella
        columns = inspector.get_columns("reports")
        column_names = [col['name'] for col in columns]
        print(f"📋 Colonne esistenti: {column_names}")
        
        # Verifica gli indici
        indexes = inspector.get_indexes("reports")
        index_names = [idx['name'] for idx in indexes]
        print(f"🔍 Indici esistenti: {index_names}")
        
    else:
        print("🔨 Creazione della tabella 'reports'...")
        
        # Crea solo la tabella reports
        Report.__table__.create(engine)
        
        print("✅ Tabella 'reports' creata con successo!")
        
        # Verifica la creazione
        inspector = inspect(engine)
        columns = inspector.get_columns("reports")
        column_names = [col['name'] for col in columns]
        print(f"📋 Colonne create: {column_names}")
        
        # Verifica gli indici
        indexes = inspector.get_indexes("reports")
        index_names = [idx['name'] for idx in indexes]
        print(f"🔍 Indici creati: {index_names}")
    
    print("\n🎯 Tipi di report supportati:")
    for report_type in ReportTypeEnum:
        print(f"   - {report_type.value}")
    
    print("\n✨ Setup completato! Il modulo Reports è pronto per l'uso.")

if __name__ == "__main__":
    try:
        create_reports_table()
    except Exception as e:
        print(f"❌ Errore durante la creazione della tabella: {e}")
        sys.exit(1) 