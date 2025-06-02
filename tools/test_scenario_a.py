#!/usr/bin/env python3
"""
Test specifico per Scenario A - Pezzo Gigante
"""

import sys
import requests
import logging
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from api.database import get_db
from models.odl import ODL

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test dello Scenario A con debug avanzato"""
    logger.info("🧪 TEST SCENARIO A - PEZZO GIGANTE")
    logger.info("=" * 50)
    
    # Trova ODL Scenario A
    db = next(get_db())
    
    odl_a = db.query(ODL).filter(
        ODL.note.like("%Edge case: pezzo gigante%")
    ).first()
    
    if not odl_a:
        logger.error("❌ ODL Scenario A non trovato")
        return
    
    logger.info(f"✅ ODL Scenario A trovato: ID {odl_a.id}")
    
    # Aggiorna stato a "Attesa Cura"
    try:
        response = requests.patch(
            f"http://localhost:8000/api/v1/odl/{odl_a.id}/status",
            json={"new_status": "Attesa Cura"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        logger.info(f"📝 Aggiornamento stato ODL: {response.status_code}")
    except:
        pass
    
    # Test nesting con debug
    request_data = {
        "autoclave_id": 1,  # Autoclave EdgeTest
        "odl_ids": [odl_a.id],
        "padding_mm": 20.0,
        "min_distance_mm": 15.0,
        "vacuum_lines_capacity": 10,
        "allow_heuristic": False,
        "timeout_override": None,
        "heavy_piece_threshold_kg": 50.0
    }
    
    logger.info("🚀 Invio richiesta nesting...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/batch_nesting/solve",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        logger.info(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Successo: {result.get('success')}")
            logger.info(f"📊 Efficienza: {result.get('metrics', {}).get('efficiency_score', 0)}%")
            logger.info(f"🔧 Algoritmo: {result.get('metrics', {}).get('algorithm_status')}")
            logger.info(f"📋 Pezzi posizionati: {result.get('metrics', {}).get('pieces_positioned', 0)}")
            logger.info(f"❌ Pezzi esclusi: {result.get('metrics', {}).get('pieces_excluded', 0)}")
            
            if result.get('excluded_odls'):
                logger.info("🚫 Motivi esclusione:")
                for exc in result['excluded_odls']:
                    logger.info(f"   - {exc.get('reason', 'N/A')}")
        else:
            logger.error(f"❌ Errore HTTP {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"💥 Errore: {str(e)}")
    
    db.close()

if __name__ == "__main__":
    main() 