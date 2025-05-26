#!/usr/bin/env python3
"""
Script di test per verificare il sistema di logging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models.db import get_db
from services.system_log_service import SystemLogService
from models.system_log import UserRole, EventType, LogLevel

def test_logging():
    """Test del sistema di logging"""
    print("🧪 Test del sistema di logging...")
    
    # Ottieni una sessione del database
    db = next(get_db())
    
    try:
        # Test 1: Log cambio stato ODL
        print("📝 Test 1: Log cambio stato ODL")
        log1 = SystemLogService.log_odl_state_change(
            db=db,
            odl_id=1,
            old_state="Preparazione",
            new_state="Laminazione",
            user_role=UserRole.LAMINATORE,
            user_id="test_user"
        )
        print(f"✅ Log creato: {log1.id}")
        
        # Test 2: Log conferma nesting
        print("📝 Test 2: Log conferma nesting")
        log2 = SystemLogService.log_nesting_confirm(
            db=db,
            nesting_id=1,
            autoclave_id=1,
            user_role=UserRole.RESPONSABILE,
            user_id="test_responsabile"
        )
        print(f"✅ Log creato: {log2.id}")
        
        # Test 3: Log avvio cura
        print("📝 Test 3: Log avvio cura")
        log3 = SystemLogService.log_cura_start(
            db=db,
            schedule_entry_id=1,
            autoclave_id=1,
            user_role=UserRole.AUTOCLAVISTA,
            user_id="test_autoclavista"
        )
        print(f"✅ Log creato: {log3.id}")
        
        # Test 4: Log modifica tool
        print("📝 Test 4: Log modifica tool")
        log4 = SystemLogService.log_tool_modify(
            db=db,
            tool_id=1,
            modification_details="Aggiornate dimensioni",
            user_role=UserRole.ADMIN,
            old_value="100x50",
            new_value="120x60",
            user_id="test_admin"
        )
        print(f"✅ Log creato: {log4.id}")
        
        # Test 5: Recupero log con filtri
        print("📝 Test 5: Recupero log con filtri")
        from schemas.system_log import SystemLogFilter
        
        filters = SystemLogFilter(
            user_role=UserRole.LAMINATORE,
            limit=10
        )
        
        logs = SystemLogService.get_logs(db, filters)
        print(f"✅ Trovati {len(logs)} log per il laminatore")
        
        # Test 6: Statistiche
        print("📝 Test 6: Statistiche")
        stats = SystemLogService.get_log_stats(db, days=7)
        print(f"✅ Statistiche: {stats.total_logs} log totali")
        print(f"   - Per tipo: {stats.logs_by_type}")
        print(f"   - Per ruolo: {stats.logs_by_role}")
        print(f"   - Per livello: {stats.logs_by_level}")
        
        print("\n🎉 Tutti i test completati con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante i test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_logging() 