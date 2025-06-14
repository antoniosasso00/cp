#!/usr/bin/env python3
"""
Script di test per identificare errori nella generazione nesting
"""

import requests
import json
import sys
import time

def test_nesting_generation():
    """Testa la generazione nesting per identificare il problema specifico"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing CarbonPilot Nesting Generation...")
    print("=" * 60)
    
    # 1. Test backend health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Backend health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Backend non raggiungibile: {e}")
        return
    
    # 2. Test database connection
    try:
        response = requests.get(f"{base_url}/health/detailed", timeout=5)
        print(f"✅ Database health: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Database: {health_data.get('database', 'unknown')}")
    except Exception as e:
        print(f"⚠️ Database health check failed: {e}")
    
    # 3. Test nesting data endpoint
    try:
        response = requests.get(f"{base_url}/api/batch_nesting/data", timeout=10)
        print(f"✅ Nesting data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ODL disponibili: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"   Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
        elif response.status_code == 500:
            print(f"❌ Error 500 in data endpoint: {response.text}")
            return
    except Exception as e:
        print(f"❌ Nesting data endpoint failed: {e}")
        return
    
    # 4. Test nesting generation with minimal data
    try:
        # Payload minimo per test
        payload = {
            "odl_ids": ["5", "6"],  # ODL semplici per test
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 8
            }
        }
        
        print(f"\n🚀 Testing nesting generation...")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/batch_nesting/genera-multi", 
            json=payload,
            timeout=60,  # Timeout lungo per debug
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        print(f"   Duration: {end_time - start_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"   Success: {result.get('success', 'unknown')}")
            print(f"   Message: {result.get('message', 'no message')}")
            print(f"   Batch ID: {result.get('best_batch_id', 'none')}")
        elif response.status_code == 500:
            print(f"❌ ERROR 500:")
            print(f"   Response text: {response.text}")
            
            # Try to parse JSON error
            try:
                error_data = response.json()
                print(f"   Error detail: {error_data.get('detail', 'no detail')}")
            except:
                print("   Could not parse error JSON")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout after 60 seconds")
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed.")

if __name__ == "__main__":
    test_nesting_generation() 