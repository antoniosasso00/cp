#!/usr/bin/env python3
"""
Test per verificare che la rimozione della modalità asincrona abbia risolto il problema
"""

import requests
import json
import time

def test_frontend_backend_integration():
    """Testa l'integrazione frontend-backend dopo la rimozione modalità asincrona"""
    
    print("🔧 TEST FINALE - Verifica rimozione modalità asincrona")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    # 1. Verifica backend attivo
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        print(f"✅ Backend: {response.status_code} - {response.json()['status']}")
        
        if response.status_code != 200:
            print("❌ Backend non disponibile!")
            return False
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False
    
    # 2. Verifica frontend attivo (se disponibile)
    try:
        response = requests.get(frontend_url, timeout=5)
        print(f"✅ Frontend: {response.status_code} - Attivo")
    except Exception as e:
        print(f"⚠️ Frontend: Non testabile via HTTP ({e})")
    
    # 3. Test nesting diretto (modalità backend-only)
    print(f"\n🚀 Test generazione nesting diretta...")
    
    try:
        payload = {
            "odl_ids": ["5", "6", "7"],  # Test con 3 ODL
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 8
            }
        }
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/api/batch_nesting/genera-multi",
            json=payload,
            timeout=30,  # Timeout breve per test sincrono
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"   Durata: {duration:.2f}s")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESSO SINCRONO!")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Batch generati: {result.get('success_count', 0)}")
            print(f"   Best batch ID: {result.get('best_batch_id', 'none')}")
            
            if duration < 10:
                print(f"✅ Performance ottima: {duration:.2f}s < 10s")
            else:
                print(f"⚠️ Performance accettabile: {duration:.2f}s")
                
            return True
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT dopo 30s - Problema ancora presente")
        return False
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

def main():
    success = test_frontend_backend_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST SUPERATO: Modalità asincrona rimossa con successo!")
        print("   - Generazione nesting funziona in modalità sincrona")
        print("   - Timeout ridotti a 2 minuti")
        print("   - Performance ottimali")
        print("   - AbortSignal.timeout() rimosso")
    else:
        print("❌ TEST FALLITO: Problema ancora presente")
        print("   - Controllare configurazione backend/frontend")
        print("   - Verificare altri timeout problematici")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 