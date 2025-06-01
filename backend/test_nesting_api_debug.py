#!/usr/bin/env python3
"""
Script di debug per verificare il funzionamento delle API del nesting
e delle funzioni admin del database
"""
import requests
import json
import sys
from datetime import datetime

def test_api_endpoint(url, method="GET", data=None):
    """Testa un endpoint API e restituisce il risultato"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"🔍 Testing: {method} {url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success: {len(result) if isinstance(result, list) else 'Response received'}")
                return True, result
            except:
                print(f"   ✅ Success: Non-JSON response")
                return True, response.text
        else:
            print(f"   ❌ Error: {response.text}")
            return False, response.text
            
    except requests.exceptions.RequestException as e:
        print(f"   💥 Connection Error: {e}")
        return False, str(e)

def main():
    """Esegue il debug completo del sistema"""
    print("🚀 CARBON PILOT - DEBUG API NESTING")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test di base del backend
    print("\n📡 1. TEST CONNESSIONE BACKEND")
    success, _ = test_api_endpoint(f"{base_url}/docs")
    if not success:
        print("❌ Backend non raggiungibile!")
        return
    
    # Test API principali per il nesting
    print("\n🔄 2. TEST API NESTING")
    endpoints_nesting = [
        f"{base_url}/api/v1/nesting/data",
        f"{base_url}/api/v1/nesting/genera",
        f"{base_url}/api/v1/batch_nesting",
        f"{base_url}/api/v1/odl?limit=100",
        f"{base_url}/api/v1/autoclavi"
    ]
    
    results = {}
    for endpoint in endpoints_nesting:
        success, data = test_api_endpoint(endpoint)
        results[endpoint] = (success, data)
    
    # Test ODL in attesa di cura
    print("\n📋 3. TEST ODL IN ATTESA DI CURA")
    success, odl_data = test_api_endpoint(f"{base_url}/api/v1/odl?status=Attesa Cura&limit=10")
    if success:
        print(f"   ODL in attesa: {len(odl_data) if isinstance(odl_data, list) else 0}")
    
    # Test autoclavi disponibili
    print("\n🏭 4. TEST AUTOCLAVI DISPONIBILI")
    success, autoclave_data = test_api_endpoint(f"{base_url}/api/v1/autoclavi?stato=DISPONIBILE")
    if success:
        print(f"   Autoclavi disponibili: {len(autoclave_data) if isinstance(autoclave_data, list) else 0}")
    
    # Test funzioni admin
    print("\n🔧 5. TEST FUNZIONI ADMIN")
    admin_endpoints = [
        f"{base_url}/api/v1/admin/database/status",
        f"{base_url}/api/v1/admin/database/export-structure",
    ]
    
    for endpoint in admin_endpoints:
        test_api_endpoint(endpoint)
    
    # Riepilogo
    print("\n📊 RIEPILOGO DEBUG")
    print("=" * 30)
    
    total_tests = len(endpoints_nesting) + len(admin_endpoints) + 3
    successful_tests = sum(1 for _, (success, _) in results.items() if success)
    
    print(f"Test completati: {successful_tests}/{total_tests}")
    
    # Identificazione problemi specifici
    print("\n🔍 PROBLEMI IDENTIFICATI:")
    
    nesting_data_success, nesting_data = results.get(f"{base_url}/api/v1/nesting/data", (False, None))
    if not nesting_data_success:
        print("❌ API nesting/data non funziona")
    
    odl_success, odl_data = results.get(f"{base_url}/api/v1/odl?limit=100", (False, None))
    if not odl_success:
        print("❌ API ODL non funziona")
    elif isinstance(odl_data, list) and len(odl_data) == 0:
        print("⚠️  Nessun ODL trovato nel database")
    
    autoclave_success, autoclave_data = results.get(f"{base_url}/api/v1/autoclavi", (False, None))
    if not autoclave_success:
        print("❌ API Autoclavi non funziona")
    elif isinstance(autoclave_data, list) and len(autoclave_data) == 0:
        print("⚠️  Nessuna autoclave trovata nel database")
    
    print(f"\n✅ Debug completato: {datetime.now()}")

if __name__ == "__main__":
    main() 