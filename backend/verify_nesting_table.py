"""
Script per verificare che la tabella nesting_results esista.
"""

import sys
import logging
from sqlalchemy import create_engine, inspect
from models.db import get_database_url

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_table_exists():
    """Verifica che la tabella nesting_results esista nel database."""
    try:
        # Ottieni l'URL del database
        database_url = get_database_url()
        logger.info(f"Connessione al database: {database_url}")
        
        # Crea engine e connettiti al database
        engine = create_engine(database_url)
        
        # Verifica l'esistenza delle tabelle
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"Tabelle esistenti nel database: {existing_tables}")
        
        # Verifica che la tabella nesting_results esista
        if "nesting_results" in existing_tables:
            logger.info("✅ La tabella 'nesting_results' esiste nel database.")
            
            # Verifica anche la tabella di associazione
            if "nesting_result_odl" in existing_tables:
                logger.info("✅ La tabella 'nesting_result_odl' esiste nel database.")
            else:
                logger.error("❌ La tabella 'nesting_result_odl' NON esiste nel database!")
                return False
                
            # Verifica le colonne della tabella
            columns = [col['name'] for col in inspector.get_columns('nesting_results')]
            logger.info(f"Colonne nella tabella 'nesting_results': {columns}")
            
            required_columns = ['id', 'autoclave_id', 'odl_ids', 'area_utilizzata', 
                               'area_totale', 'valvole_utilizzate', 'valvole_totali', 
                               'created_at']
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.error(f"❌ Mancano le seguenti colonne: {missing_columns}")
                return False
                
            return True
        else:
            logger.error("❌ La tabella 'nesting_results' NON esiste nel database!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante la verifica: {str(e)}")
        return False

if __name__ == "__main__":
    result = verify_table_exists()
    sys.exit(0 if result else 1) 