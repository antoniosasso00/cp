#!/usr/bin/env python3
"""
Test semplice per il servizio di monitoraggio ODL
"""

import logging
from models.db import get_db
from models.odl import ODL
from sqlalchemy.orm import joinedload

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_odl_monitoring():
    """Test semplice del servizio di monitoraggio"""
    
    try:
        # Ottieni sessione database
        db = next(get_db())
        
        # Test 1: Conta ODL totali
        total_odl = db.query(ODL).count()
        logger.info(f"📊 ODL totali nel database: {total_odl}")
        
        # Test 2: Ottieni primi 3 ODL con relazioni
        odl_list = db.query(ODL).options(
            joinedload(ODL.parte),
            joinedload(ODL.tool)
        ).limit(3).all()
        
        logger.info(f"📋 Primi 3 ODL trovati:")
        for odl in odl_list:
            logger.info(f"  ODL {odl.id}: {odl.status} - Parte: {odl.parte.descrizione_breve} - Tool: {odl.tool.part_number_tool}")
        
        # Test 3: Prova a ottenere un ODL specifico
        if odl_list:
            first_odl = odl_list[0]
            logger.info(f"🔍 Test ODL specifico {first_odl.id}:")
            logger.info(f"  Status: {first_odl.status}")
            logger.info(f"  Priorità: {first_odl.priorita}")
            logger.info(f"  Parte: {first_odl.parte.descrizione_breve}")
            logger.info(f"  Tool: {first_odl.tool.part_number_tool}")
            logger.info(f"  Created: {first_odl.created_at}")
            logger.info(f"  Updated: {first_odl.updated_at}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il test: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Test servizio monitoraggio ODL...")
    success = test_odl_monitoring()
    
    if success:
        logger.info("✅ Test completato con successo!")
    else:
        logger.error("❌ Test fallito!") 