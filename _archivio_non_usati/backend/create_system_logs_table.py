#!/usr/bin/env python3
"""
Script per creare la tabella system_logs nel database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import engine, Base
from models.system_log import SystemLog
from sqlalchemy import inspect
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_system_logs_table():
    """Crea la tabella system_logs se non esiste"""
    try:
        # Verifica se la tabella esiste già
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'system_logs' in tables:
            logger.info("✅ La tabella 'system_logs' esiste già")
            return True
        
        logger.info("🔧 Creazione tabella 'system_logs'...")
        
        # Crea solo la tabella SystemLog
        SystemLog.__table__.create(engine)
        
        logger.info("✅ Tabella 'system_logs' creata con successo!")
        
        # Verifica che sia stata creata
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'system_logs' in tables:
            logger.info("✅ Verifica completata: tabella 'system_logs' presente nel database")
            return True
        else:
            logger.error("❌ Errore: tabella 'system_logs' non trovata dopo la creazione")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione della tabella: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Avvio creazione tabella system_logs...")
    success = create_system_logs_table()
    
    if success:
        logger.info("🎉 Operazione completata con successo!")
        sys.exit(0)
    else:
        logger.error("💥 Operazione fallita!")
        sys.exit(1) 