#!/usr/bin/env python3
"""
Test rapido per verificare il fix timeout del solver 2L.
"""

import requests
import time
import json

def test_2l_timeout_fix():
    """Test per verificare che il timeout 2L sia risolto"""
    print("🚀 TEST 2L TIMEOUT FIX")
    print("=" * 40)
    
    # Configurazione test con pochi ODL per ridurre complessità
    test_request = {
        "autoclavi_2l": [1, 2, 3],  # Tutte le autoclavi
        "odl_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Solo 10 ODL (ridotto da 45)
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 8
        },
        "use_cavalletti": True,
        "prefer_base_level": True,
        "cavalletti_config": {
            "min_distance_from_edge": 30.0,
            "max_span_without_support": 300.0,
            "min_distance_between_cavalletti": 200.0,
            "safety_margin_x": 5.0,
            "safety_margin_y": 5.0,
            "prefer_symmetric": True,
            "force_minimum_two": True
        }
    }
    
    # Test endpoint 2L con timeout ridotto
    print("⏰ Chiamata 2L-multi con timeout fix...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/api/batch_nesting/2l-multi",
            json=test_request,
            timeout=30  # 30 secondi timeout client
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Risposta ricevuta in {duration:.2f}s")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Success count: {result.get('success_count', 0)}")
        else:
            print(f"   Error: {response.text}")
            
        # Verifica che il timeout sia ragionevole
        if duration < 60:
            print("✅ TIMEOUT FIX: Successo - Risposta sotto 60 secondi")
        else:
            print("❌ TIMEOUT FIX: Fallimento - Risposta troppo lenta")
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ TIMEOUT CLIENT dopo {duration:.2f}s")
        print("⚠️ Il backend sta ancora processando oltre 30s")
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ ERRORE dopo {duration:.2f}s: {e}")

if __name__ == "__main__":
    test_2l_timeout_fix() 