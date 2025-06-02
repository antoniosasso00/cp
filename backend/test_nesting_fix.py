#!/usr/bin/env python3
"""
Test per verificare che gli errori del nesting siano stati risolti
"""
import requests
import json
import time

API_BASE = "http://127.0.0.1:8000/api/v1"

def test_health():
    """Testa l'endpoint di health"""
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_nesting_data():
    """Testa l'endpoint /data che causava l'errore use_secondary_plane"""
    try:
        response = requests.get(f"{API_BASE}/batch_nesting/data")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint /data funziona correttamente")
            print(f"   - ODL in attesa: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"   - Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
            return True
        else:
            print(f"❌ Endpoint /data failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Endpoint /data error: {str(e)}")
        return False

def test_nesting_generation():
    """Testa la generazione nesting"""
    payload = {
        "odl_ids": ["1"],
        "autoclave_ids": ["1"],
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 8
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/batch_nesting/genera",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            message = data.get('message', '')
            
            print(f"✅ Risposta ricevuta:")
            print(f"   - Success: {success}")
            print(f"   - Message: {message}")
            print(f"   - Batch ID: {data.get('batch_id', 'N/A')}")
            
            # Verifica se l'errore use_secondary_plane è ancora presente
            if 'use_secondary_plane' in message:
                print("❌ ERRORE: Il problema use_secondary_plane persiste!")
                return False
            else:
                print("✅ Errore use_secondary_plane NON presente nella risposta")
                return True
        else:
            try:
                error_data = response.json()
                print(f"❌ Errore HTTP: {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ Errore HTTP: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def main():
    """Test principale"""
    print("🧪 TEST VERIFICA FIX ERRORI NESTING")
    print("=" * 50)
    
    # Aspetta che il server sia pronto
    print("⏳ Attesa server...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Endpoint /data", test_nesting_data),
        ("Generazione Nesting", test_nesting_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n📊 RISULTATI FINALI:")
    print("=" * 30)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20s}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 SUCCESS: Tutti i fix funzionano correttamente!")
    else:
        print("\n❌ FAILED: Alcuni problemi persistono")
    
    return all_passed

if __name__ == "__main__":
    main() 