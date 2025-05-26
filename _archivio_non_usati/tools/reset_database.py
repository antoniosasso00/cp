#!/usr/bin/env python
"""
Script per il reset completo del database CarbonPilot.
Droppa tutte le tabelle e le ricrea da zero.
Compatibile con SQLite e PostgreSQL.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

# Importa i modelli e la configurazione del database
from backend.models.db import engine, get_database_url, USE_SQLITE
from backend.models import Base

def reset_database():
    """
    Resetta completamente il database:
    1. Droppa tutte le tabelle esistenti
    2. Ricrea tutte le tabelle dai modelli
    """
    try:
        database_url = get_database_url()
        logger.info(f"🔄 Inizio reset database: {database_url}")
        
        # Step 1: Drop tutte le tabelle
        logger.info("⚠️ Eliminazione di tutte le tabelle esistenti...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Tutte le tabelle eliminate con successo")
        
        # Step 2: Ricrea tutte le tabelle
        logger.info("🏗️ Creazione di tutte le tabelle dai modelli...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tutte le tabelle create con successo")
        
        # Verifica che le tabelle siano state create
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"📊 Tabelle create: {len(tables)}")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        logger.info("🎉 Reset database completato con successo!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il reset del database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Funzione principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset del database CarbonPilot")
    parser.add_argument("--force", action="store_true", help="Forza il reset senza chiedere conferma")
    args = parser.parse_args()
    
    logger.info("🗃️ Script di Reset Database CarbonPilot")
    logger.info("=" * 50)
    
    # Mostra configurazione attuale
    database_url = get_database_url()
    db_type = "SQLite" if USE_SQLITE else "PostgreSQL"
    logger.info(f"Tipo database: {db_type}")
    logger.info(f"URL database: {database_url}")
    
    # Chiedi conferma solo se non è forzato
    if not args.force:
        response = input("\n⚠️ ATTENZIONE: Questa operazione eliminerà TUTTI i dati esistenti!\nContinuare? (s/N): ")
        if response.lower() not in ['s', 'si', 'sì', 'y', 'yes']:
            logger.info("❌ Operazione annullata dall'utente")
            return
    else:
        logger.info("\n🔄 Modalità forzata attivata - procedendo con il reset...")
    
    # Esegui il reset
    success = reset_database()
    
    if success:
        logger.info("\n🌱 Suggerimento: Esegui ora 'python tools/seed_test_data.py' per popolare il database con dati di test")
    else:
        logger.error("\n❌ Reset fallito. Controlla i log per i dettagli.")
        sys.exit(1)

if __name__ == "__main__":
    main() 