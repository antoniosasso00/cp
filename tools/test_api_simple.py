#!/usr/bin/env python3
"""
Script semplice per testare le API del monitoraggio ODL.
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Test API CarbonPilot")
    print("=" * 50)
    
    # Test 1: Verifica che il backend sia attivo
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend attivo")
        else:
            print(f"❌ Backend non risponde: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Impossibile connettersi al backend: {e}")
        return
    
    # Test 2: Lista ODL
    try:
        response = requests.get(f"{base_url}/api/v1/odl/", timeout=5)
        print(f"\n📋 Lista ODL:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            odl_list = response.json()
            print(f"   ODL trovati: {len(odl_list)}")
            if odl_list:
                for odl in odl_list[:3]:  # Mostra solo i primi 3
                    print(f"   - ODL #{odl.get('id', 'N/A')}: {odl.get('status', 'N/A')}")
            else:
                print("   Nessun ODL nel database")
        else:
            print(f"   Errore: {response.text}")
    except Exception as e:
        print(f"❌ Errore nel recupero ODL: {e}")
    
    # Test 3: Statistiche monitoraggio
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/stats", timeout=5)
        print(f"\n📊 Statistiche Monitoraggio:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Totale ODL: {stats.get('totale_odl', 0)}")
            print(f"   Per stato: {stats.get('per_stato', {})}")
        else:
            print(f"   Errore: {response.text}")
    except Exception as e:
        print(f"❌ Errore nelle statistiche: {e}")
    
    # Test 4: Inizializzazione tracking (se endpoint esiste)
    try:
        response = requests.post(f"{base_url}/api/v1/odl-monitoring/monitoring/initialize-state-tracking", timeout=10)
        print(f"\n🔧 Inizializzazione Tracking:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Log creati: {result.get('logs_creati', 0)}")
            print(f"   ODL processati: {result.get('odl_processati', [])}")
        else:
            print(f"   Errore: {response.text}")
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione: {e}")
    
    # Test 5: Test progresso ODL (se ci sono ODL)
    try:
        # Prima ottieni la lista ODL per trovare un ID valido
        response = requests.get(f"{base_url}/api/v1/odl/", timeout=5)
        if response.status_code == 200:
            odl_list = response.json()
            if odl_list:
                test_odl_id = odl_list[0]['id']
                
                # Test endpoint progress
                response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{test_odl_id}/progress", timeout=5)
                print(f"\n📈 Test Progresso ODL #{test_odl_id}:")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    progress = response.json()
                    print(f"   Status ODL: {progress.get('status', 'N/A')}")
                    print(f"   Timestamps: {len(progress.get('timestamps', []))}")
                    print(f"   Has Timeline Data: {progress.get('has_timeline_data', False)}")
                    
                    if progress.get('has_timeline_data'):
                        print("   ✅ Dati timeline disponibili!")
                    else:
                        print("   ⚠️  Usando dati stimati (fallback)")
                else:
                    print(f"   Errore: {response.text}")
            else:
                print(f"\n📈 Test Progresso: Nessun ODL disponibile per il test")
    except Exception as e:
        print(f"❌ Errore nel test progresso: {e}")
    
    print(f"\n🎯 Test completato!")

if __name__ == "__main__":
    test_api() 