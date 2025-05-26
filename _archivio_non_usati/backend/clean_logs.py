#!/usr/bin/env python3
"""
Script per pulire la tabella system_logs
"""

from models.db import engine
from sqlalchemy import text
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_logs():
    """Pulisce la tabella system_logs"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM system_logs"))
            conn.commit()
            logger.info(f"✅ Eliminati {result.rowcount} log dalla tabella")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la pulizia: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧹 Pulizia tabella system_logs...")
    clean_logs() 