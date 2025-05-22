"""
Script per testare l'endpoint /api/v1/nesting/.
"""

import logging
import requests
import sys
import json
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"

def test_nesting_endpoint():
    """
    Testa l'endpoint /api/v1/nesting/ per verificare che restituisca i dati corretti.
    """
    try:
        # Costruisci l'URL dell'endpoint
        endpoint_url = urljoin(BASE_URL, "/nesting/")
        logger.info(f"Esecuzione GET su {endpoint_url}")
        
        # Esegui la richiesta GET
        response = requests.get(endpoint_url)
        
        # Verifica che la risposta sia un 200 OK
        if response.status_code == 200:
            logger.info("✅ L'endpoint ha risposto con 200 OK")
            
            # Verifica che la risposta sia in formato JSON
            try:
                data = response.json()
                logger.info(f"Dati ricevuti: {json.dumps(data, indent=2)}")
                
                # Verifica che la risposta sia una lista (anche vuota)
                if isinstance(data, list):
                    logger.info(f"✅ La risposta è una lista con {len(data)} elementi")
                    return True
                else:
                    logger.error("❌ La risposta non è una lista")
                    return False
            except ValueError:
                logger.error("❌ La risposta non è in formato JSON")
                return False
        else:
            logger.error(f"❌ L'endpoint ha risposto con {response.status_code}")
            logger.error(f"Dettagli: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Errore durante il test: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_nesting_endpoint()
    sys.exit(0 if result else 1) 