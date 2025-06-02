#!/usr/bin/env python3
"""
Script per testare gli endpoint nesting problematici
"""
import requests
import json

def test_nesting_endpoints():
    """Testa gli endpoint nesting che causano errori nel frontend"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🔍 TEST ENDPOINT NESTING")
    print("=" * 50)
    
    # Test 1: Endpoint /data che causava errore
    print("\n📋 1. Test endpoint /batch_nesting/data:")
    try:
        response = requests.get(f"{base_url}/batch_nesting/data", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Successo!")
            print(f"   📊 ODL in attesa: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"   📊 Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
            print(f"   📊 Status: {data.get('status')}")
        else:
            print(f"   ❌ Errore: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Eccezione: {str(e)}")
    
    # Test 2: Lista batch nesting
    print("\n📋 2. Test endpoint /batch_nesting/ (lista):")
    try:
        response = requests.get(f"{base_url}/batch_nesting/", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Successo!")
            print(f"   📊 Batch trovati: {len(data)}")
        else:
            print(f"   ❌ Errore: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Eccezione: {str(e)}")
    
    # Test 3: Health check backend
    print("\n📋 3. Test health check:")
    try:
        response = requests.get(f"http://localhost:8000/health", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend healthy!")
            print(f"   📊 Database: {data.get('database', {}).get('status')}")
            print(f"   📊 Tables: {data.get('database', {}).get('tables_count')}")
        else:
            print(f"   ❌ Errore: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Eccezione: {str(e)}")
    
    # Test 4: Endpoint dashboard che dovrebbero funzionare
    print("\n📋 4. Test endpoint dashboard:")
    dashboard_endpoints = [
        "dashboard/odl-count",
        "dashboard/autoclave-load", 
        "dashboard/nesting-active"
    ]
    
    for endpoint in dashboard_endpoints:
        try:
            response = requests.get(f"{base_url}/{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
            
        except Exception as e:
            print(f"   {endpoint}: ❌ Eccezione: {str(e)}")

if __name__ == "__main__":
    test_nesting_endpoints() 