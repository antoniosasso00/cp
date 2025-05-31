#!/usr/bin/env python3
"""
🔧 SCRIPT DI FIX SCHEMA DATABASE
================================

Aggiunge i campi mancanti alla tabella tools nel database
"""

import sys
import os
import logging

# Aggiungi il path del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import text, inspect
from backend.models.db import engine, SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_tools_table():
    """Aggiunge i campi peso e materiale alla tabella tools"""
    try:
        logger.info("🔧 Inizio fix schema tabella tools...")
        
        # Verifica quali colonne esistono
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('tools')]
        
        logger.info(f"📋 Colonne esistenti: {existing_columns}")
        
        with engine.connect() as conn:
            # Aggiungi colonna peso se non esiste
            if 'peso' not in existing_columns:
                logger.info("➕ Aggiunta colonna 'peso' alla tabella tools")
                conn.execute(text("ALTER TABLE tools ADD COLUMN peso FLOAT"))
                conn.commit()
            else:
                logger.info("✅ Colonna 'peso' già presente")
            
            # Aggiungi colonna materiale se non esiste
            if 'materiale' not in existing_columns:
                logger.info("➕ Aggiunta colonna 'materiale' alla tabella tools")
                conn.execute(text("ALTER TABLE tools ADD COLUMN materiale VARCHAR(100)"))
                conn.commit()
            else:
                logger.info("✅ Colonna 'materiale' già presente")
            
            # Verifica le modifiche
            new_columns = [col['name'] for col in inspector.get_columns('tools')]
            logger.info(f"📋 Colonne dopo fix: {new_columns}")
            
        logger.info("✅ Fix schema completato con successo!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore nel fix schema: {e}")
        return False

def verify_tools_data():
    """Verifica e aggiorna i dati dei tools con valori di default"""
    try:
        logger.info("🔍 Verifica dati tools...")
        
        db = SessionLocal()
        
        # Query per tools senza peso
        result = db.execute(text("UPDATE tools SET peso = 50.0 WHERE peso IS NULL"))
        updated_peso = result.rowcount
        
        # Query per tools senza materiale
        result = db.execute(text("UPDATE tools SET materiale = 'Alluminio' WHERE materiale IS NULL"))
        updated_materiale = result.rowcount
        
        db.commit()
        db.close()
        
        logger.info(f"✅ Aggiornati {updated_peso} tools con peso di default")
        logger.info(f"✅ Aggiornati {updated_materiale} tools con materiale di default")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore nell'aggiornamento dati: {e}")
        return False

def fix_autoclave_fields():
    """Aggiunge i campi mancanti alla tabella autoclavi"""
    try:
        logger.info("🔧 Controllo schema tabella autoclavi...")
        
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('autoclavi')]
        
        with engine.connect() as conn:
            # Aggiungi max_load_kg se non esiste
            if 'max_load_kg' not in existing_columns:
                logger.info("➕ Aggiunta colonna 'max_load_kg' alla tabella autoclavi")
                conn.execute(text("ALTER TABLE autoclavi ADD COLUMN max_load_kg FLOAT DEFAULT 1000.0"))
                conn.commit()
            else:
                logger.info("✅ Colonna 'max_load_kg' già presente")
            
            # Aggiungi use_secondary_plane se non esiste
            if 'use_secondary_plane' not in existing_columns:
                logger.info("➕ Aggiunta colonna 'use_secondary_plane' alla tabella autoclavi")
                conn.execute(text("ALTER TABLE autoclavi ADD COLUMN use_secondary_plane BOOLEAN DEFAULT FALSE"))
                conn.commit()
            else:
                logger.info("✅ Colonna 'use_secondary_plane' già presente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore nel fix autoclavi: {e}")
        return False

def main():
    """Funzione principale"""
    try:
        logger.info("🚀 AVVIO FIX SCHEMA DATABASE")
        
        # Fix tabella tools
        if not fix_tools_table():
            logger.error("❌ Fix tabella tools fallito")
            return False
        
        # Fix tabella autoclavi
        if not fix_autoclave_fields():
            logger.error("❌ Fix tabella autoclavi fallito")
            return False
        
        # Aggiorna dati tools
        if not verify_tools_data():
            logger.error("❌ Aggiornamento dati tools fallito")
            return False
        
        logger.info("🎉 TUTTI I FIX SONO STATI APPLICATI CON SUCCESSO!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore fatale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 