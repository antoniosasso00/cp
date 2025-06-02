#!/usr/bin/env python3
"""
Script di test per gli endpoint API di nesting
Identifica e risolve i problemi degli errori mostrati nelle immagini
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def test_data_endpoint():
    """Testa l'endpoint /data per il caricamento dati nesting"""
    print("🔍 Test endpoint /data...")
    
    try:
        response = requests.get(f"{API_BASE}/batch_nesting/data")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dati caricati correttamente:")
            print(f"  - ODL in attesa: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"  - Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
            return True
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def test_genera_endpoint():
    """Testa l'endpoint /genera per la generazione nesting"""
    print("\n🚀 Test endpoint /genera...")
    
    payload = {
        "odl_ids": ["1", "2"],
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
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Nesting generato correttamente:")
            print(f"  - Batch ID: {data.get('batch_id', 'N/A')}")
            print(f"  - Success: {data.get('success', False)}")
            print(f"  - Message: {data.get('message', 'N/A')}")
            print(f"  - Algorithm Status: {data.get('algorithm_status', 'N/A')}")
            return True
        else:
            print(f"❌ Errore: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def test_health_check():
    """Testa lo stato generale del server"""
    print("💓 Test health check...")
    
    try:
        response = requests.get(f"http://localhost:8000/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server attivo:")
            print(f"  - Database: {data.get('database', {}).get('status', 'N/A')}")
            print(f"  - Tabelle: {data.get('database', {}).get('tables_count', 'N/A')}")
            return True
        else:
            print(f"❌ Server non raggiungibile: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server non raggiungibile: {str(e)}")
        return False

def main():
    """Esegue tutti i test"""
    print("🧪 ANALISI PROBLEMI NESTING - Debug degli errori mostrati nelle immagini")
    print("=" * 80)
    
    # Test 1: Health check
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ PROBLEMA CRITICO: Server non raggiungibile")
        print("   Assicurati che il backend sia in esecuzione su localhost:8000")
        return
    
    # Test 2: Data endpoint (problema 404 dell'anteprima)
    data_ok = test_data_endpoint()
    
    # Test 3: Genera endpoint (problema validazione)
    genera_ok = test_genera_endpoint()
    
    # Risultati finali
    print("\n" + "=" * 80)
    print("📊 RISULTATI ANALISI:")
    print(f"  ✅ Health Check: {'OK' if health_ok else 'FAIL'}")
    print(f"  ✅ Data Endpoint: {'OK' if data_ok else 'FAIL'}")
    print(f"  ✅ Genera Endpoint: {'OK' if genera_ok else 'FAIL'}")
    
    if all([health_ok, data_ok, genera_ok]):
        print("\n🎉 TUTTI I TEST SUPERATI - Gli endpoint API funzionano correttamente!")
        print("   Il problema potrebbe essere nel frontend o nella configurazione CORS.")
    else:
        print("\n⚠️ PROBLEMI IDENTIFICATI - Controllare i log sopra per i dettagli.")

if __name__ == "__main__":
    main() 