#!/usr/bin/env python3
"""
Test script per verificare il nuovo endpoint multi-2L
"""

import requests
import json

def test_2l_multi_endpoint():
    url = "http://localhost:8000/api/batch_nesting/2l-multi"
    
    # Payload di test (simulando la richiesta del frontend)
    payload = {
        "autoclavi_2l": [1, 2, 3],  # ID autoclavi con supporto 2L
        "odl_ids": [1, 2, 3, 4, 5],  # ODL di test
        "parametri": {
            "padding_mm": 5,
            "min_distance_mm": 10
        },
        "use_cavalletti": True,
        "cavalletto_height_mm": 100.0,
        "max_weight_per_level_kg": 200.0,
        "prefer_base_level": True
    }
    
    try:
        print("🧪 Testing new 2L multi endpoint...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ ERROR - Status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Backend not running?")
        return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    test_2l_multi_endpoint() 