#!/usr/bin/env python3
"""
Script per verificare i dati nella tabella system_logs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.db import engine
from sqlalchemy import text
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_logs():
    """Verifica i dati nella tabella system_logs"""
    try:
        with engine.connect() as conn:
            # Verifica i tipi di evento
            result = conn.execute(text("SELECT event_type, COUNT(*) FROM system_logs GROUP BY event_type"))
            event_types = list(result)
            logger.info(f"📊 Tipi di evento nel database: {event_types}")
            
            # Verifica tutti i log
            result = conn.execute(text("SELECT id, event_type, user_role, action FROM system_logs LIMIT 10"))
            logs = list(result)
            logger.info(f"📋 Primi 10 log:")
            for log in logs:
                logger.info(f"  ID: {log[0]}, Event: {log[1]}, Role: {log[2]}, Action: {log[3]}")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la verifica: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Verifica dati tabella system_logs...")
    check_logs() 