#!/usr/bin/env python3
"""
Script di test per verificare le correzioni apportate:
1. Connessione al database locale
2. Funzionalità dei cicli di cura
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi il backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test della connessione al database"""
    try:
        from models.db import DATABASE_URL, engine
        from sqlalchemy import text
        
        logger.info(f"Testing database connection...")
        logger.info(f"Database URL: {DATABASE_URL}")
        
        # Test connessione
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Connessione al database riuscita!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Errore connessione database: {e}")
        return False

def test_cicli_cura_model():
    """Test del modello CicloCura"""
    try:
        from models.ciclo_cura import CicloCura
        from models.db import SessionLocal
        
        logger.info("Testing CicloCura model...")
        
        # Test creazione sessione
        db = SessionLocal()
        
        # Test query
        cicli = db.query(CicloCura).limit(5).all()
        logger.info(f"✅ Trovati {len(cicli)} cicli di cura nel database")
        
        for ciclo in cicli:
            logger.info(f"  - {ciclo.nome}: Stasi1({ciclo.temperatura_stasi1}°C, {ciclo.pressione_stasi1}bar, {ciclo.durata_stasi1}min)")
            if ciclo.attiva_stasi2:
                logger.info(f"    Stasi2({ciclo.temperatura_stasi2}°C, {ciclo.pressione_stasi2}bar, {ciclo.durata_stasi2}min)")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test CicloCura: {e}")
        return False

def main():
    """Esegue tutti i test"""
    logger.info("🚀 Avvio test delle correzioni...")
    
    # Test 1: Connessione database
    db_ok = test_database_connection()
    
    # Test 2: Modello CicloCura
    cicli_ok = test_cicli_cura_model()
    
    # Risultati
    logger.info("\n📊 Risultati test:")
    logger.info(f"  Database connection: {'✅' if db_ok else '❌'}")
    logger.info(f"  CicloCura model: {'✅' if cicli_ok else '❌'}")
    
    if db_ok and cicli_ok:
        logger.info("🎉 Tutti i test sono passati!")
        return 0
    else:
        logger.error("💥 Alcuni test sono falliti!")
        return 1

if __name__ == "__main__":
    exit(main()) 