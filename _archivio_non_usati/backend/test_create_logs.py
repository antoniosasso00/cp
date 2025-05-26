#!/usr/bin/env python3
"""
Script per creare log di test per verificare il sistema di logging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.system_log_service import SystemLogService
from models.system_log import EventType, UserRole, LogLevel
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_logs():
    """Crea alcuni log di test"""
    try:
        from models.db import get_db
        from models.system_log import SystemLog
        from datetime import datetime
        
        db = next(get_db())
        
        logger.info("🔧 Creazione log di test...")
        
        # Creiamo i log direttamente nel database
        logs_to_create = [
            SystemLog(
                level=LogLevel.INFO,
                event_type=EventType.TOOL_MODIFY,
                user_role=UserRole.ADMIN,
                action="Aggiornamento stato tool",
                entity_type="tool",
                entity_id=1,
                old_value="disponibile",
                new_value="in_uso",
                details="Tool aggiornato tramite API"
            ),
            SystemLog(
                level=LogLevel.INFO,
                event_type=EventType.AUTOCLAVE_MODIFY,
                user_role=UserRole.RESPONSABILE,
                action="Modifica parametri autoclave",
                entity_type="autoclave",
                entity_id=1,
                old_value="temperatura: 180°C",
                new_value="temperatura: 200°C",
                details="Aggiornamento parametri per nuovo ciclo"
            ),
            SystemLog(
                level=LogLevel.INFO,
                event_type=EventType.CURA_START,
                user_role=UserRole.AUTOCLAVISTA,
                action="Avvio ciclo di cura",
                entity_type="schedule_entry",
                entity_id=1,
                details="Avvio ciclo di cura automatico"
            ),
            SystemLog(
                level=LogLevel.INFO,
                event_type=EventType.BACKUP_CREATE,
                user_role=UserRole.ADMIN,
                action="Backup creato",
                details="Backup automatico giornaliero - backup_test.json"
            ),
            SystemLog(
                level=LogLevel.INFO,
                event_type=EventType.ODL_STATE_CHANGE,
                user_role=UserRole.LAMINATORE,
                action="Cambio stato ODL",
                entity_type="odl",
                entity_id=1,
                old_value="in_attesa",
                new_value="in_lavorazione",
                details="ODL passato in lavorazione"
            )
        ]
        
        # Aggiungi tutti i log al database
        for log in logs_to_create:
            db.add(log)
        
        db.commit()
        
        logger.info("✅ Log di test creati con successo!")
        
        # Verifica che i log siano stati creati
        count = db.query(SystemLog).count()
        logger.info(f"📊 Totale log nel database: {count}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione dei log di test: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    logger.info("🚀 Avvio creazione log di test...")
    success = create_test_logs()
    
    if success:
        logger.info("🎉 Log di test creati con successo!")
        sys.exit(0)
    else:
        logger.error("💥 Operazione fallita!")
        sys.exit(1) 