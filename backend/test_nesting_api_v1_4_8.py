"""
Test API Endpoint Nesting Solver v1.4.8-DEMO
==============================================

Test per verificare il funzionamento del nuovo endpoint API 
POST /batch_nesting/solve con parametri ottimizzati.
"""

import pytest
import requests
import json
import time
import logging
from typing import Dict, Any

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione API
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/batch_nesting/solve"

def test_api_endpoint_basic():
    """
    Test di base del nuovo endpoint /batch_nesting/solve
    """
    logger.info("🔧 TEST API ENDPOINT BASIC")
    logger.info("=" * 40)
    
    # Dati di test per la richiesta
    request_data = {
        "odl_ids": [1, 2, 3, 4, 5],  # ID di esempio, sostituire con ID reali
        "autoclave_id": 1,           # ID autoclave di esempio
        "padding_mm": 20,
        "min_distance_mm": 15,
        "vacuum_lines_capacity": 8
    }
    
    try:
        # Invio richiesta
        logger.info(f"Invio richiesta a: {API_ENDPOINT}")
        logger.info(f"Dati: {json.dumps(request_data, indent=2)}")
        
        start_time = time.time()
        response = requests.post(API_ENDPOINT, json=request_data, timeout=30)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"⏱️ Tempo risposta: {execution_time:.2f}s")
        
        # Verifica status code
        logger.info(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Parse risposta JSON
            result = response.json()
            
            logger.info("✅ RISPOSTA API RICEVUTA")
            logger.info("-" * 30)
            
            # Verifica struttura risposta
            required_fields = ['layout', 'metrics', 'excluded_odls', 'success', 'algorithm_status']
            for field in required_fields:
                if field in result:
                    logger.info(f"✅ Campo '{field}': presente")
                else:
                    logger.error(f"❌ Campo '{field}': mancante")
                    return False
            
            # Verifica metriche
            metrics = result.get('metrics', {})
            logger.info("")
            logger.info("📊 METRICHE")
            logger.info("-" * 15)
            logger.info(f"Area utilizzata: {metrics.get('area_pct', 0):.1f}%")
            logger.info(f"Linee vuoto: {metrics.get('lines_used', 0)}")
            logger.info(f"Peso totale: {metrics.get('total_weight', 0):.1f}kg")
            logger.info(f"ODL posizionati: {metrics.get('positioned_count', 0)}")
            logger.info(f"ODL esclusi: {metrics.get('excluded_count', 0)}")
            logger.info(f"Efficienza: {metrics.get('efficiency', 0):.1f}%")
            
            # Verifica layout
            layout = result.get('layout', [])
            logger.info("")
            logger.info(f"🗂️ LAYOUT ({len(layout)} elementi)")
            logger.info("-" * 20)
            for item in layout[:3]:  # Mostra primi 3 elementi
                logger.info(f"  ODL {item.get('odl_id')}: pos({item.get('x')},{item.get('y')}) "
                           f"dim({item.get('width')}x{item.get('height')}) "
                           f"ruotato({item.get('rotated')})")
            
            if len(layout) > 3:
                logger.info(f"  ... e altri {len(layout) - 3} elementi")
            
            # Verifica successo
            success = result.get('success', False)
            algorithm = result.get('algorithm_status', 'N/A')
            
            logger.info("")
            logger.info(f"✅ Successo: {success}")
            logger.info(f"🔧 Algoritmo: {algorithm}")
            
            return True
            
        else:
            logger.error(f"❌ Errore API: {response.status_code}")
            logger.error(f"Messaggio: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connessione fallita - Server non raggiungibile")
        logger.error("   Assicurarsi che il server FastAPI sia in esecuzione su localhost:8000")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout richiesta (>30s)")
        return False
    except Exception as e:
        logger.error(f"❌ Errore imprevisto: {str(e)}")
        return False

def test_api_parameters_validation():
    """
    Test di validazione parametri API
    """
    logger.info("")
    logger.info("🔍 TEST VALIDAZIONE PARAMETRI")
    logger.info("=" * 40)
    
    # Test parametri invalidi
    invalid_test_cases = [
        {
            "name": "ODL lista vuota",
            "data": {
                "odl_ids": [],
                "autoclave_id": 1,
                "padding_mm": 20,
                "min_distance_mm": 15,
                "vacuum_lines_capacity": 8
            }
        },
        {
            "name": "Padding troppo piccolo",
            "data": {
                "odl_ids": [1, 2],
                "autoclave_id": 1,
                "padding_mm": 2,  # Sotto il minimo di 5
                "min_distance_mm": 15,
                "vacuum_lines_capacity": 8
            }
        },
        {
            "name": "Capacità linee vuoto zero",
            "data": {
                "odl_ids": [1, 2],
                "autoclave_id": 1,
                "padding_mm": 20,
                "min_distance_mm": 15,
                "vacuum_lines_capacity": 0  # Sotto il minimo di 1
            }
        }
    ]
    
    for test_case in invalid_test_cases:
        logger.info(f"Test: {test_case['name']}")
        
        try:
            response = requests.post(API_ENDPOINT, json=test_case['data'], timeout=10)
            
            if response.status_code == 422:  # Validation Error
                logger.info(f"  ✅ Validazione corretta (422)")
            elif response.status_code == 400:  # Bad Request
                logger.info(f"  ✅ Validazione corretta (400)")
            else:
                logger.warning(f"  ⚠️ Status imprevisto: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            logger.error("  ❌ Server non raggiungibile")
            return False
        except Exception as e:
            logger.error(f"  ❌ Errore: {str(e)}")
            return False
    
    return True

def test_api_performance():
    """
    Test di performance API con diversi carichi
    """
    logger.info("")
    logger.info("⚡ TEST PERFORMANCE API")
    logger.info("=" * 30)
    
    # Test con diverse quantità di ODL
    test_sizes = [2, 5, 8, 12]
    
    for size in test_sizes:
        logger.info(f"Test con {size} ODL")
        
        request_data = {
            "odl_ids": list(range(1, size + 1)),
            "autoclave_id": 1,
            "padding_mm": 20,
            "min_distance_mm": 15,
            "vacuum_lines_capacity": 10
        }
        
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=request_data, timeout=30)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                algorithm = result.get('algorithm_status', 'N/A')
                positioned = result.get('metrics', {}).get('positioned_count', 0)
                
                logger.info(f"  ⏱️ Tempo: {execution_time:.2f}s")
                logger.info(f"  ✅ Successo: {success}")
                logger.info(f"  🔧 Algoritmo: {algorithm}")
                logger.info(f"  📦 Posizionati: {positioned}/{size}")
                
                # Verifica target <10s
                if execution_time < 10.0:
                    logger.info(f"  🎯 Performance OK (<10s)")
                else:
                    logger.warning(f"  ⚠️ Performance lenta (>{execution_time:.1f}s)")
            else:
                logger.error(f"  ❌ Errore: {response.status_code}")
                
        except Exception as e:
            logger.error(f"  ❌ Errore: {str(e)}")
            return False
    
    return True

def run_all_tests():
    """
    Esegue tutti i test API
    """
    logger.info("🚀 AVVIO TEST API NESTING SOLVER v1.4.8-DEMO")
    logger.info("=" * 60)
    
    overall_start = time.time()
    
    tests = [
        ("Basic API Test", test_api_endpoint_basic),
        ("Parameter Validation", test_api_parameters_validation),
        ("Performance Test", test_api_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info("")
        logger.info(f"🧪 ESECUZIONE: {test_name}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASS")
            else:
                logger.info(f"❌ {test_name}: FAIL")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERRORE - {str(e)}")
            results.append((test_name, False))
    
    overall_time = time.time() - overall_start
    
    # Riepilogo finale
    logger.info("")
    logger.info("🏆 RIEPILOGO TEST API")
    logger.info("=" * 30)
    logger.info(f"⏱️ Tempo totale: {overall_time:.2f}s")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"📊 Test passati: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    if passed == total:
        logger.info("")
        logger.info("🎉 TUTTI I TEST API SUPERATI!")
        logger.info("   L'endpoint è pronto per l'uso.")
    else:
        logger.info("")
        logger.info("⚠️ ALCUNI TEST API FALLITI")
        logger.info("   Verificare configurazione server e dati di test.")

if __name__ == "__main__":
    run_all_tests() 