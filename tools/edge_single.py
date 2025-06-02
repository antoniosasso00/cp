#!/usr/bin/env python3
"""
Edge Single Scenario Test per CarbonPilot
Esegue un singolo test edge case e genera output verbose.
"""

import sys
import os
import json
import time
import logging
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from api.database import get_db
from models.autoclave import Autoclave
from models.odl import ODL

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EdgeSingleTester:
    """Tester per singoli scenari edge case"""
    
    def __init__(self, verbose: bool = False):
        self.base_url = "http://localhost:8000"
        self.verbose = verbose
        self.autoclave_id = None
        
    def setup(self) -> bool:
        """Setup iniziale: trova autoclave di test"""
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            # Trova autoclave di test
            autoclave = db.query(Autoclave).filter(
                Autoclave.nome == "EdgeTest-Autoclave"
            ).first()
            
            if not autoclave:
                logger.error("❌ Autoclave di test non trovata. Esegui prima seed_edge_data.py")
                return False
                
            self.autoclave_id = autoclave.id
            if self.verbose:
                logger.info(f"✅ Autoclave di test trovata: ID {self.autoclave_id}")
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"💥 Errore setup: {str(e)}")
            return False
    
    def get_scenario_odl_ids(self, scenario: str) -> List[int]:
        """Ottiene gli ID degli ODL per uno scenario specifico"""
        try:
            db_gen = get_db()
            db = next(db_gen)
            
            # Mappatura scenari a pattern note
            patterns = {
                "A": "Edge case: pezzo gigante",
                "B": "Edge case B:",
                "C": "Edge case C:",
                "D": "Edge case D:",
                "E": "Edge case E:"
            }
            
            pattern = patterns.get(scenario)
            if not pattern:
                logger.error(f"❌ Scenario sconosciuto: {scenario}")
                return []
            
            odl_list = db.query(ODL).filter(
                ODL.note.like(f"%{pattern}%")
            ).all()
            
            odl_ids = [odl.id for odl in odl_list]
            if self.verbose:
                logger.info(f"📋 Scenario {scenario}: trovati {len(odl_ids)} ODL")
            
            db.close()
            return odl_ids
            
        except Exception as e:
            logger.error(f"💥 Errore recupero ODL scenario {scenario}: {str(e)}")
            return []
    
    def update_odl_status_to_attesa_cura(self, odl_ids: List[int]):
        """Aggiorna lo stato degli ODL a 'Attesa Cura' per renderli disponibili per il nesting"""
        try:
            for odl_id in odl_ids:
                response = requests.patch(
                    f"{self.base_url}/api/v1/odl/{odl_id}/status",
                    json={"new_status": "Attesa Cura"},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                if response.status_code != 200:
                    logger.warning(f"⚠️  Errore aggiornamento ODL {odl_id}: {response.status_code}")
            
            if self.verbose:
                logger.info(f"✅ Aggiornati {len(odl_ids)} ODL a stato 'Attesa Cura'")
                
        except Exception as e:
            logger.error(f"💥 Errore aggiornamento stato ODL: {str(e)}")
    
    def run_nesting_test(self, scenario: str, odl_ids: List[int]) -> Dict[str, Any]:
        """Esegue un singolo test di nesting e ritorna i risultati"""
        
        if self.verbose:
            logger.info(f"🧪 Test scenario {scenario}: {len(odl_ids)} ODL")
        
        # Preparazione richiesta
        request_data = {
            "autoclave_id": self.autoclave_id,
            "odl_ids": odl_ids,
            "padding_mm": 20.0,
            "min_distance_mm": 15.0,
            "vacuum_lines_capacity": 10,
            "allow_heuristic": True,
            "timeout_override": None,
            "heavy_piece_threshold_kg": 50.0
        }
        
        start_time = time.time()
        
        try:
            # Test API nesting
            response = requests.post(
                f"{self.base_url}/api/v1/batch_nesting/solve",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            test_duration = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                result = {
                    "scenario": scenario,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "error_message": response.text if response.text else "Unknown HTTP error",
                    "test_duration_ms": test_duration,
                    "timestamp": datetime.now().isoformat()
                }
                return result
            
            # Parse risposta
            data = response.json()
            metrics = data.get("metrics", {})
            positioned_tools = data.get("positioned_tools", [])
            excluded_reasons = data.get("excluded_reasons", {})
            
            print(f"✅ Test completato:")
            print(f"   📊 Pezzi posizionati: {len(positioned_tools)}")
            print(f"   📊 Pezzi esclusi: {len(excluded_reasons)}")
            print(f"   📊 Efficienza: {metrics.get('efficiency_score', 0):.1f}%")
            print(f"   📊 Area utilizzata: {metrics.get('area_utilization_pct', 0):.1f}%")
            print(f"   📊 Algoritmo: {metrics.get('algorithm_status', 'N/A')}")
            print(f"   📊 Tempo solver: {metrics.get('time_solver_ms', 0):.0f}ms")
            
            if excluded_reasons:
                print(f"   ❌ Motivi esclusione: {excluded_reasons}")
            
            return {
                "success": True,
                "positioned": len(positioned_tools),
                "excluded": len(excluded_reasons),
                "efficiency": metrics.get('efficiency_score', 0),
                "area_pct": metrics.get('area_utilization_pct', 0),
                "algorithm": metrics.get('algorithm_status', 'N/A')
            }
            
        except requests.exceptions.Timeout:
            result = {
                "scenario": scenario,
                "success": False,
                "error": "TIMEOUT",
                "error_message": "Request timeout dopo 30 secondi",
                "test_duration_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
            return result
            
        except Exception as e:
            result = {
                "scenario": scenario,
                "success": False,
                "error": "EXCEPTION",
                "error_message": str(e),
                "test_duration_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
            return result
    
    def test_scenario(self, scenario: str) -> Dict[str, Any]:
        """Testa un singolo scenario"""
        if not self.setup():
            return {
                "scenario": scenario,
                "success": False,
                "error": "SETUP_FAILED",
                "error_message": "Setup fallito - controlla che l'API sia attiva e i dati siano caricati"
            }
        
        # Ottieni ODL per lo scenario
        odl_ids = self.get_scenario_odl_ids(scenario)
        if not odl_ids:
            return {
                "scenario": scenario,
                "success": False,
                "error": "NO_ODL_FOUND",
                "error_message": f"Nessun ODL trovato per scenario {scenario}"
            }
        
        # Aggiorna stato ODL
        self.update_odl_status_to_attesa_cura(odl_ids)
        
        # Esegui test
        result = self.run_nesting_test(scenario, odl_ids)
        
        return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test singolo scenario edge case")
    parser.add_argument("--scenario", "-s", required=True, 
                       choices=["A", "B", "C", "D", "E"],
                       help="Scenario da testare (A-E)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Output verbose")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Crea tester
    tester = EdgeSingleTester(verbose=args.verbose)
    
    # Esegui test
    result = tester.test_scenario(args.scenario)
    
    # Output risultato
    if args.verbose:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Output essenziale
        if result["success"]:
            summary = result.get("summary", {})
            print(f"✅ Scenario {args.scenario}: SUCCESS")
            print(f"   - Positioned: {summary.get('placed', 0)}")
            print(f"   - Excluded: {summary.get('excluded', 0)}")
            print(f"   - Efficiency: {summary.get('efficiency_score', 0):.1f}%")
            print(f"   - Duration: {result.get('test_duration_ms', 0):.0f}ms")
        else:
            print(f"❌ Scenario {args.scenario}: FAILED")
            print(f"   - Error: {result.get('error', 'Unknown')}")
            print(f"   - Message: {result.get('error_message', 'No details')}")
    
    # Exit code
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main() 