#!/usr/bin/env python3
"""
Script per creare log di test usando il servizio SystemLogService
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_db
from models.system_log import EventType, UserRole, LogLevel
from services.system_log_service import SystemLogService
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_logs():
    """Crea alcuni log di test usando il servizio"""
    try:
        db = next(get_db())
        
        logger.info("🔧 Creazione log di test tramite servizio...")
        
        # Log 1: Cambio stato ODL
        SystemLogService.log_odl_state_change(
            db=db,
            odl_id=1,
            old_state="in_attesa",
            new_state="in_lavorazione",
            user_role=UserRole.LAMINATORE,
            user_id="user123"
        )
        
        # Log 2: Conferma nesting
        SystemLogService.log_nesting_confirm(
            db=db,
            nesting_id=1,
            autoclave_id=1,
            user_role=UserRole.RESPONSABILE,
            user_id="resp456"
        )
        
        # Log 3: Avvio cura
        SystemLogService.log_cura_start(
            db=db,
            schedule_entry_id=1,
            autoclave_id=1,
            user_role=UserRole.AUTOCLAVISTA,
            user_id="auto789"
        )
        
        # Log 4: Backup
        SystemLogService.log_backup_create(
            db=db,
            backup_filename="backup_test_20250526.json",
            tables_count=16,
            user_role=UserRole.ADMIN,
            user_id="admin001"
        )
        
        # Log 5: Modifica tool
        SystemLogService.log_tool_modify(
            db=db,
            tool_id=1,
            modification_details="Aggiornamento stato disponibilità",
            user_role=UserRole.ADMIN,
            old_value="disponibile",
            new_value="in_manutenzione",
            user_id="admin001"
        )
        
        logger.info("✅ Log di test creati con successo!")
        
        # Verifica
        from models.system_log import SystemLog
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
    logger.info("🚀 Avvio creazione log di test tramite servizio...")
    success = create_test_logs()
    
    if success:
        logger.info("🎉 Log di test creati con successo!")
        sys.exit(0)
    else:
        logger.error("💥 Operazione fallita!")
        sys.exit(1) 