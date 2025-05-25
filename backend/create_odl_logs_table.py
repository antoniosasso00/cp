#!/usr/bin/env python3
"""
Script per creare la tabella odl_logs nel database esistente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from models.base import Base
from models.odl_log import ODLLog
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_odl_logs_table():
    """Crea la tabella odl_logs nel database"""
    
    # Connessione al database SQLite
    DATABASE_URL = "sqlite:///./carbonpilot.db"
    engine = create_engine(DATABASE_URL, echo=True)
    
    try:
        # Crea solo la tabella ODLLog se non esiste
        ODLLog.__table__.create(engine, checkfirst=True)
        logger.info("✅ Tabella odl_logs creata con successo!")
        
        # Verifica che la tabella sia stata creata
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='odl_logs'"))
            if result.fetchone():
                logger.info("✅ Verifica completata: tabella odl_logs presente nel database")
                
                # Mostra la struttura della tabella
                result = conn.execute(text("PRAGMA table_info(odl_logs)"))
                columns = result.fetchall()
                logger.info("📋 Struttura tabella odl_logs:")
                for col in columns:
                    logger.info(f"  - {col[1]} ({col[2]})")
            else:
                logger.error("❌ Errore: tabella odl_logs non trovata dopo la creazione")
                
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione della tabella: {str(e)}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    logger.info("🚀 Avvio creazione tabella odl_logs...")
    create_odl_logs_table()
    logger.info("✅ Processo completato!") 