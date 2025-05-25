#!/usr/bin/env python3
"""
Script per controllare gli ID degli ODL nel database
"""

import sqlite3
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_odl_ids():
    """Controlla gli ID degli ODL nel database"""
    
    try:
        # Connessione al database
        conn = sqlite3.connect("carbonpilot.db")
        cursor = conn.cursor()
        
        # Ottieni tutti gli ODL
        cursor.execute("SELECT id, status, priorita FROM odl ORDER BY id")
        odl_list = cursor.fetchall()
        
        logger.info(f"📊 Trovati {len(odl_list)} ODL nel database:")
        for odl_id, status, priorita in odl_list:
            logger.info(f"  ODL {odl_id}: {status} - Priorità: {priorita}")
        
        # Controlla anche le parti e i tool
        cursor.execute("SELECT COUNT(*) FROM parti")
        parti_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tools")
        tools_count = cursor.fetchone()[0]
        
        logger.info(f"📋 Parti nel database: {parti_count}")
        logger.info(f"🔧 Tools nel database: {tools_count}")
        
        conn.close()
        return odl_list
        
    except Exception as e:
        logger.error(f"❌ Errore durante il controllo: {e}")
        return []

if __name__ == "__main__":
    logger.info("🚀 Controllo ID ODL nel database...")
    odl_list = check_odl_ids()
    
    if odl_list:
        logger.info("✅ Controllo completato!")
    else:
        logger.error("❌ Nessun ODL trovato!") 