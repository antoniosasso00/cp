#!/usr/bin/env python3
"""
🧪 Test generazione automatica nesting con debug
"""

import requests
import json

def test_automatic_generation():
    """Testa la generazione automatica con parametri diversi"""
    
    print("🤖 Test Generazione Automatica Nesting...")
    
    # Test 1: Parametri base
    print("\n1️⃣ Test con parametri base...")
    payload1 = {
        "force_regenerate": True,
        "parameters": {
            "distanza_minima_tool_cm": 1.0,  # Ridotto per essere meno restrittivo
            "padding_bordo_autoclave_cm": 1.0,  # Ridotto
            "margine_sicurezza_peso_percent": 5.0,  # Ridotto
            "priorita_minima": 1,
            "efficienza_minima_percent": 30.0  # Ridotto per essere meno restrittivo
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/nesting/automatic', 
            json=payload1, 
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('success'):
                nesting_results = data.get('nesting_results', [])
                summary = data.get('summary', {})
                
                print(f"   ✅ Nesting creati: {len(nesting_results)}")
                print(f"   ✅ ODL processati: {summary.get('total_odl_processed', 0)}")
                print(f"   ✅ ODL esclusi: {summary.get('total_odl_excluded', 0)}")
                print(f"   ✅ Autoclavi utilizzate: {summary.get('autoclavi_utilizzate', 0)}")
                
                # Dettagli nesting
                for i, nesting in enumerate(nesting_results):
                    print(f"      Nesting {i+1}:")
                    print(f"         ID: {nesting.get('id')}")
                    print(f"         Autoclave: {nesting.get('autoclave_nome')}")
                    print(f"         Ciclo: {nesting.get('ciclo_cura')}")
                    print(f"         Efficienza: {nesting.get('efficienza')}%")
                    print(f"         ODL inclusi: {nesting.get('odl_inclusi')}")
            else:
                print(f"   ⚠️ Fallimento: {data.get('message')}")
                
        else:
            print(f"   ❌ Errore HTTP: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 2: Parametri molto permissivi
    print("\n2️⃣ Test con parametri molto permissivi...")
    payload2 = {
        "force_regenerate": True,
        "parameters": {
            "distanza_minima_tool_cm": 0.5,
            "padding_bordo_autoclave_cm": 0.5,
            "margine_sicurezza_peso_percent": 1.0,
            "priorita_minima": 1,
            "efficienza_minima_percent": 10.0  # Molto basso
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/nesting/automatic', 
            json=payload2, 
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('success'):
                nesting_results = data.get('nesting_results', [])
                summary = data.get('summary', {})
                
                print(f"   ✅ Nesting creati: {len(nesting_results)}")
                print(f"   ✅ ODL processati: {summary.get('total_odl_processed', 0)}")
                print(f"   ✅ ODL esclusi: {summary.get('total_odl_excluded', 0)}")
                
            else:
                print(f"   ⚠️ Fallimento: {data.get('message')}")
                
        else:
            print(f"   ❌ Errore HTTP: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 3: Senza parametri (default)
    print("\n3️⃣ Test senza parametri (default)...")
    payload3 = {
        "force_regenerate": True
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/nesting/automatic', 
            json=payload3, 
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('success'):
                nesting_results = data.get('nesting_results', [])
                summary = data.get('summary', {})
                
                print(f"   ✅ Nesting creati: {len(nesting_results)}")
                print(f"   ✅ ODL processati: {summary.get('total_odl_processed', 0)}")
                print(f"   ✅ ODL esclusi: {summary.get('total_odl_excluded', 0)}")
                
            else:
                print(f"   ⚠️ Fallimento: {data.get('message')}")
                
        else:
            print(f"   ❌ Errore HTTP: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")

if __name__ == "__main__":
    test_automatic_generation() 