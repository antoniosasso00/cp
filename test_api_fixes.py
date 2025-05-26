#!/usr/bin/env python3
"""
Script di test per verificare le correzioni implementate nell'applicazione CarbonPilot
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"

def test_endpoint(name: str, url: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Testa un endpoint API e restituisce i risultati"""
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, json=data, timeout=10)
        else:
            return {"name": name, "status": "error", "message": f"Metodo {method} non supportato"}
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                return {
                    "name": name,
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "data_length": len(json_data) if isinstance(json_data, list) else 1,
                    "message": f"✅ OK - {len(json_data) if isinstance(json_data, list) else 'Singolo oggetto'} elementi"
                }
            except:
                return {
                    "name": name,
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "message": f"✅ OK - Risposta non JSON"
                }
        else:
            return {
                "name": name,
                "status": "error",
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "message": f"❌ Error {response.status_code}: {response.text[:100]}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "status": "error",
            "message": "💥 Errore di connessione - Server non raggiungibile"
        }
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "status": "error",
            "message": "⏰ Timeout - Server troppo lento"
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "message": f"💥 Errore: {str(e)}"
        }

def main():
    print("🧪 Test delle correzioni API CarbonPilot")
    print("=" * 50)
    
    # Test di base
    tests = [
        ("Health Check", HEALTH_URL),
        ("ODL List", f"{API_BASE_URL}/odl"),
        ("Tools List", f"{API_BASE_URL}/tools"),
        ("Tools with Status", f"{API_BASE_URL}/tools/with-status"),
        ("Nesting Preview", f"{API_BASE_URL}/nesting/preview"),
        ("ODL Pending Nesting", f"{API_BASE_URL}/odl/pending-nesting"),
    ]
    
    results = []
    
    for test_name, url in tests:
        print(f"\n🔍 Testing: {test_name}")
        result = test_endpoint(test_name, url)
        results.append(result)
        
        if result["status"] == "success":
            print(f"   {result['message']} ({result.get('response_time_ms', 0)}ms)")
        else:
            print(f"   {result['message']}")
    
    # Test specifici per le correzioni implementate
    print(f"\n🔧 Test delle correzioni specifiche")
    print("-" * 30)
    
    # Test 1: Verifica che gli endpoint di aggiornamento stato esistano
    odl_status_tests = [
        ("Laminatore Status Endpoint", f"{API_BASE_URL}/odl/1/laminatore-status?new_status=Laminazione", "PATCH"),
        ("Autoclavista Status Endpoint", f"{API_BASE_URL}/odl/1/autoclavista-status?new_status=Cura", "PATCH"),
    ]
    
    for test_name, url, method in odl_status_tests:
        print(f"\n🔍 Testing: {test_name}")
        result = test_endpoint(test_name, url, method)
        results.append(result)
        
        # Per questi test, anche un 404 è accettabile (ODL non esiste)
        if result["status"] == "success" or (result.get("status_code") == 404):
            print(f"   ✅ Endpoint disponibile ({result.get('status_code', 'N/A')})")
        else:
            print(f"   {result['message']}")
    
    # Riepilogo
    print(f"\n📊 Riepilogo Test")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    print(f"✅ Test riusciti: {success_count}/{total_count}")
    print(f"❌ Test falliti: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print(f"\n🎉 Tutti i test sono passati! Le correzioni funzionano correttamente.")
    else:
        print(f"\n⚠️ Alcuni test sono falliti. Verifica i dettagli sopra.")
        
        # Mostra i test falliti
        failed_tests = [r for r in results if r["status"] != "success"]
        if failed_tests:
            print(f"\n❌ Test falliti:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['message']}")
    
    print(f"\n🔗 URL utili:")
    print(f"   - Backend Health: {HEALTH_URL}")
    print(f"   - Frontend (se attivo): http://localhost:3000")
    print(f"   - Debug Page: http://localhost:3000/dashboard/test-debug")

if __name__ == "__main__":
    main() 