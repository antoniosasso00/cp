#!/usr/bin/env python3
"""
Script di test per verificare la connessione al backend CarbonPilot
"""

import requests
import json
from datetime import datetime

def test_backend_connection():
    """
    Testa la connessione al backend CarbonPilot
    """
    backend_url = "http://localhost:8000"
    
    print("🔍 Test Connessione Backend CarbonPilot")
    print("=" * 50)
    print(f"⏰ Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL Backend: {backend_url}")
    print()
    
    # Test 1: Health check base
    print("📊 Test 1: Health Check Base (/)")
    try:
        response = requests.get(f"{backend_url}/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Risposta: {data}")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
            print(f"   📝 Contenuto: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Errore: Backend non raggiungibile")
        print("   💡 Suggerimento: Verificare che il backend sia avviato")
        return False
    except Exception as e:
        print(f"   ❌ Errore imprevisto: {str(e)}")
        return False
    
    print()
    
    # Test 2: Health check dettagliato
    print("📊 Test 2: Health Check Dettagliato (/health)")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   🗃️ Database Status: {data.get('database', {}).get('status')}")
            print(f"   📊 Tabelle DB: {data.get('database', {}).get('tables_count')}")
            print(f"   🛣️ Route API: {data.get('api', {}).get('routes_count')}")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
            print(f"   📝 Contenuto: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")
    
    print()
    
    # Test 3: API ODL
    print("📊 Test 3: API ODL (/api/odl)")
    try:
        response = requests.get(f"{backend_url}/api/odl", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ ODL trovati: {len(data) if isinstance(data, list) else 'N/A'}")
            if isinstance(data, list) and len(data) > 0:
                print(f"   📋 Primo ODL ID: {data[0].get('id', 'N/A')}")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
            print(f"   📝 Contenuto: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")
    
    print()
    
    # Test 4: Documentazione Swagger
    print("📊 Test 4: Documentazione Swagger (/docs)")
    try:
        response = requests.get(f"{backend_url}/docs", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Documentazione Swagger accessibile")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")
    
    print()
    print("🏁 Test completati!")
    print("💡 Se tutti i test passano, il backend è funzionante")
    print("💡 Se ci sono errori, controllare i log del backend")
    
    return True

if __name__ == "__main__":
    test_backend_connection() 