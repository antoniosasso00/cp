#!/usr/bin/env python3
"""
Test per verificare se il proxy del frontend funziona correttamente
"""

import requests
import json

def test_frontend_proxy():
    """Testa il proxy del frontend"""
    print("🔍 Test Proxy Frontend CarbonPilot")
    print("=" * 50)
    
    # Test endpoint tramite proxy frontend
    frontend_endpoints = [
        ("http://localhost:3000/api/odl", "ODL via Frontend"),
        ("http://localhost:3000/api/autoclavi", "Autoclavi via Frontend"),
        ("http://localhost:3000/api/batch_nesting", "Batch Nesting via Frontend"),
    ]
    
    # Test endpoint diretti backend
    backend_endpoints = [
        ("http://localhost:8000/api/v1/odl", "ODL Diretto Backend"),
        ("http://localhost:8000/api/v1/autoclavi", "Autoclavi Diretto Backend"),
        ("http://localhost:8000/api/v1/batch_nesting", "Batch Nesting Diretto Backend"),
    ]
    
    all_results = []
    
    print("\n📡 Test Proxy Frontend:")
    for url, name in frontend_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                all_results.append(True)
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
                all_results.append(False)
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connessione fallita")
            all_results.append(False)
        except Exception as e:
            print(f"❌ {name}: Errore - {e}")
            all_results.append(False)
    
    print("\n🔗 Test Backend Diretto:")
    for url, name in backend_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                all_results.append(True)
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
                all_results.append(False)
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connessione fallita")
            all_results.append(False)
        except Exception as e:
            print(f"❌ {name}: Errore - {e}")
            all_results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(all_results)
    total = len(all_results)
    
    if passed == total:
        print(f"🎉 Tutti i test passati ({passed}/{total})")
        print("✅ Il proxy del frontend funziona correttamente!")
        return 0
    else:
        print(f"⚠️ {passed}/{total} test passati")
        if passed >= 3:  # Se almeno il backend funziona
            print("✅ Backend funzionante, possibili problemi di proxy frontend")
        return 1

if __name__ == "__main__":
    exit(test_frontend_proxy()) 