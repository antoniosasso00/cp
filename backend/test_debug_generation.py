#!/usr/bin/env python3
"""
Debug test per generazione batch DRAFT
"""

import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_simple_generation():
    """Test semplice di generazione con 2 ODL"""
    print("🧪 Test generazione batch DRAFT")
    
    payload = {
        "odl_ids": ["1", "2"],
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 15
        }
    }
    
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/batch_nesting/genera-multi",
        headers=HEADERS,
        json=payload,  # Usa json= invece di data=
        timeout=60
    )
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Risposta: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Errore: {response.text}")

if __name__ == "__main__":
    test_simple_generation() 