#!/usr/bin/env python3
"""
Script per creare la tabella BatchNesting nel database SQLite.
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del backend al PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from models.db import engine, Base
from models import *  # Importa tutti i modelli
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_batch_nesting_table():
    """Crea la tabella batch_nesting e aggiorna nesting_results"""
    try:
        logger.info("🔨 Creazione tabelle database...")
        
        # Crea tutte le tabelle definite nei modelli
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tabelle create con successo!")
        logger.info("📊 Tabelle disponibili:")
        
        # Lista le tabelle nel database
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in sorted(tables):
            logger.info(f"  - {table}")
            
        # Verifica che la tabella batch_nesting sia stata creata
        if 'batch_nesting' in tables:
            logger.info("✅ Tabella batch_nesting creata correttamente!")
        else:
            logger.warning("⚠️ Tabella batch_nesting non trovata")
            
        # Verifica che la colonna batch_id sia stata aggiunta a nesting_results
        nesting_columns = inspector.get_columns('nesting_results')
        column_names = [col['name'] for col in nesting_columns]
        
        if 'batch_id' in column_names:
            logger.info("✅ Colonna batch_id aggiunta a nesting_results!")
        else:
            logger.warning("⚠️ Colonna batch_id non trovata in nesting_results")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione delle tabelle: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Creazione tabella BatchNesting...")
    success = create_batch_nesting_table()
    
    if success:
        print("🎉 Script completato con successo!")
        sys.exit(0)
    else:
        print("💥 Script fallito!")
        sys.exit(1) 