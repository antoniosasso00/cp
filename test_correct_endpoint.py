#!/usr/bin/env python3
"""
Test per verificare l'endpoint ODL corretto
"""

import requests
import json
from datetime import datetime

def test_odl_endpoint():
    """
    Testa l'endpoint ODL con l'URL corretto
    """
    backend_url = "http://localhost:8000"
    
    print("🔍 Test Endpoint ODL Specifico")
    print("=" * 50)
    print(f"⏰ Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL Backend: {backend_url}")
    print()
    
    # Test endpoint corretto
    print("📊 Test: Endpoint ODL (/api/v1/odl)")
    try:
        response = requests.get(f"{backend_url}/api/v1/odl", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ ODL trovati: {len(data) if isinstance(data, list) else 'N/A'}")
            if isinstance(data, list):
                print(f"   📊 Tipologia risposta: Lista con {len(data)} elementi")
                if len(data) > 0:
                    first_odl = data[0]
                    print(f"   📋 Primo ODL:")
                    print(f"      - ID: {first_odl.get('id', 'N/A')}")
                    print(f"      - Status: {first_odl.get('status', 'N/A')}")
                    print(f"      - Parte ID: {first_odl.get('parte_id', 'N/A')}")
                    print(f"      - Tool ID: {first_odl.get('tool_id', 'N/A')}")
                else:
                    print("   📋 Nessun ODL presente nel database")
            else:
                print(f"   📊 Tipologia risposta: {type(data).__name__}")
                print(f"   📝 Contenuto: {data}")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
            print(f"   📝 Contenuto: {response.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Errore: Backend non raggiungibile")
        return False
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")
        return False
    
    print()
    
    # Test altri endpoint correlati
    print("📊 Test: Swagger UI (/docs)")
    try:
        response = requests.get(f"{backend_url}/docs", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Swagger UI accessibile")
            print("   💡 Verifica manualmente: http://localhost:8000/docs")
        else:
            print(f"   ❌ Errore HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Errore: {str(e)}")
    
    print()
    print("🏁 Test endpoint ODL completato!")
    print("📝 Note:")
    print("   - Se l'endpoint restituisce 200 ma lista vuota, il database potrebbe essere vuoto")
    print("   - Se l'endpoint restituisce 404, verifica la configurazione delle rotte")
    print("   - Controlla Swagger UI per vedere tutte le rotte disponibili")
    
    return True

if __name__ == "__main__":
    test_odl_endpoint() 