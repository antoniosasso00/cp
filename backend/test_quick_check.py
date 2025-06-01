#!/usr/bin/env python3
"""
Test rapido per verificare il funzionamento del backend
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

# URL base dell'API
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(url, name):
    """Testa un endpoint specifico"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK (200)")
            return True
        else:
            print(f"⚠️ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connessione fallita (server non in esecuzione?)")
        return False
    except Exception as e:
        print(f"❌ {name}: Errore - {e}")
        return False

def main():
    print("🔍 Controllo Backend CarbonPilot")
    print("=" * 50)
    
    # Lista degli endpoint da testare
    endpoints = [
        (f"{BASE_URL}/odl", "ODL Endpoint"),
        (f"{BASE_URL}/autoclavi", "Autoclavi Endpoint"),
        (f"{BASE_URL}/batch_nesting", "Batch Nesting Endpoint"),
        (f"{BASE_URL}/nesting/result", "Nesting Results Endpoint"),
        (f"{BASE_URL}/admin/info", "Admin Info Endpoint"),
    ]
    
    results = []
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append(result)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Tutti i test passati ({passed}/{total})")
        return 0
    else:
        print(f"⚠️ {passed}/{total} test passati")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 