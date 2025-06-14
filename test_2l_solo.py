#!/usr/bin/env python3
"""
Test semplice solo per endpoint 2L singolo
"""

import requests
import json
import time

def test_2l_solo():
    """Test solo endpoint 2L singolo con payload fisso"""
    
    print("🔧 TEST SEMPLICE ENDPOINT 2L SINGOLO")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    # Test con parametri fissi invece di dati dinamici
    payload = {
        "autoclave_id": 1,  # Autoclave fissa
        "odl_ids": [1, 2, 3],  # ODL fissi
        "padding_mm": 10.0,
        "min_distance_mm": 15.0,
        "use_cavalletti": True,
        "prefer_base_level": True,
        "allow_heuristic": True,
        "use_multithread": True,
        "heavy_piece_threshold_kg": 50.0
    }
    
    try:
        print("🚀 Test endpoint /api/batch_nesting/2l...")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/api/batch_nesting/2l",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # Timeout più lungo
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Durata: {duration:.2f}s")
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESSO!")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'N/A')}")
            if 'metrics' in result:
                print(f"   Positioned tools: {result['metrics'].get('pieces_positioned', 0)}")
                print(f"   Level 0 count: {result['metrics'].get('level_0_count', 0)}")
                print(f"   Level 1 count: {result['metrics'].get('level_1_count', 0)}")
            return True
        else:
            print(f"❌ ERRORE {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detail: {error_detail.get('detail', response.text)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Il backend potrebbe essere in crash")
        return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_2l_solo()
    if success:
        print("\n✅ TEST SUPERATO: Endpoint 2L singolo funziona!")
    else:
        print("\n❌ TEST FALLITO: Errore nell'endpoint 2L singolo") 