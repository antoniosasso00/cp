#!/usr/bin/env python3
"""
🔧 TEST SOLUZIONE ROBUSTA TIMEOUT 2L MULTI-AUTOCLAVE
Verifica che la nuova implementazione con timeout estesi e modalità asincrona funzioni
"""

import requests
import time
import json
from typing import Dict, Any

# Configurazione test
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"

def test_backend_connectivity():
    """Test connettività backend"""
    print("🔍 Test connettività backend...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/batch_nesting/data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend attivo: {len(data.get('autoclavi', []))} autoclavi, {len(data.get('odl', []))} ODL")
            return True
        else:
            print(f"❌ Backend error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend non raggiungibile: {e}")
        return False

def test_frontend_api_routes():
    """Test API routes frontend"""
    print("\n🔍 Test API routes frontend...")
    
    # Test dataset semplice (dovrebbe usare modalità sincrona)
    simple_payload = {
        "autoclavi_2l": [1, 2],  # 2 autoclavi
        "odl_ids": [1, 2, 3],    # 3 ODL (semplice)
        "parametri": {
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        },
        "use_cavalletti": True
    }
    
    print("📋 Test dataset SEMPLICE (modalità sincrona)...")
    print(f"   - Autoclavi: {len(simple_payload['autoclavi_2l'])}")
    print(f"   - ODL: {len(simple_payload['odl_ids'])}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{FRONTEND_URL}/api/batch_nesting/2l-multi",
            json=simple_payload,
            timeout=180  # 3 minuti timeout client
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Durata richiesta: {duration:.1f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('mode') == 'async':
                print("🔄 Modalità asincrona attivata (inaspettato per dataset semplice)")
                return test_async_polling(data.get('job_id'))
            else:
                print("✅ Modalità sincrona - Successo!")
                print(f"   - Success: {data.get('success')}")
                print(f"   - Batch count: {len(data.get('batch_results', []))}")
                return True
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout richiesta (3 minuti) - Questo indica un problema")
        return False
    except Exception as e:
        print(f"❌ Errore richiesta: {e}")
        return False

def test_complex_dataset():
    """Test dataset complesso (dovrebbe attivare modalità asincrona)"""
    print("\n🔍 Test dataset COMPLESSO (modalità asincrona)...")
    
    # Dataset complesso che dovrebbe attivare modalità asincrona
    complex_payload = {
        "autoclavi_2l": [1, 2, 3],  # 3 autoclavi
        "odl_ids": list(range(1, 16)),  # 15 ODL (complesso)
        "parametri": {
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        },
        "use_cavalletti": True
    }
    
    print(f"📋 Dataset complesso:")
    print(f"   - Autoclavi: {len(complex_payload['autoclavi_2l'])}")
    print(f"   - ODL: {len(complex_payload['odl_ids'])}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{FRONTEND_URL}/api/batch_nesting/2l-multi",
            json=complex_payload,
            timeout=30  # Timeout breve per forzare modalità asincrona
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Durata richiesta: {duration:.1f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('mode') == 'async':
                print("🔄 Modalità asincrona attivata correttamente!")
                print(f"   - Job ID: {data.get('job_id')}")
                print(f"   - Durata stimata: {data.get('estimated_duration_minutes')} minuti")
                return test_async_polling(data.get('job_id'))
            else:
                print("✅ Modalità sincrona completata velocemente")
                return True
        else:
            print(f"❌ Errore: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout richiesta - Modalità asincrona dovrebbe essere attivata")
        return False
    except Exception as e:
        print(f"❌ Errore richiesta: {e}")
        return False

def test_async_polling(job_id: str) -> bool:
    """Test polling asincrono"""
    print(f"\n🔄 Test polling asincrono per job: {job_id}")
    
    max_polls = 20  # Max 20 polling (100 secondi)
    poll_interval = 5  # 5 secondi tra polling
    
    for i in range(max_polls):
        try:
            print(f"   Polling {i+1}/{max_polls}...")
            response = requests.get(f"{FRONTEND_URL}/api/batch_nesting/status/{job_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                if status.get('status') == 'completed':
                    print("✅ Job completato!")
                    result = status.get('result', {})
                    if result.get('success'):
                        print(f"   - Success: {result.get('success')}")
                        print(f"   - Batch count: {len(result.get('data', {}).get('batch_results', []))}")
                        return True
                    else:
                        print(f"   - Errore: {result.get('error')}")
                        return False
                        
                elif status.get('status') == 'processing':
                    print(f"   - Ancora in elaborazione...")
                    time.sleep(poll_interval)
                    continue
                else:
                    print(f"   - Status sconosciuto: {status.get('status')}")
                    return False
            else:
                print(f"   - Errore polling: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   - Errore polling: {e}")
            return False
    
    print("⏰ Timeout polling - Job non completato in tempo")
    return False

def main():
    """Test principale"""
    print("🚀 TEST SOLUZIONE ROBUSTA TIMEOUT 2L MULTI-AUTOCLAVE")
    print("=" * 60)
    
    # Test connettività
    if not test_backend_connectivity():
        print("\n❌ FALLIMENTO: Backend non disponibile")
        return
    
    # Test API routes frontend
    print("\n" + "=" * 60)
    success_simple = test_frontend_api_routes()
    
    print("\n" + "=" * 60)
    success_complex = test_complex_dataset()
    
    # Risultati finali
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI:")
    print(f"   - Dataset semplice: {'✅ SUCCESSO' if success_simple else '❌ FALLIMENTO'}")
    print(f"   - Dataset complesso: {'✅ SUCCESSO' if success_complex else '❌ FALLIMENTO'}")
    
    if success_simple and success_complex:
        print("\n🎉 SOLUZIONE ROBUSTA FUNZIONANTE!")
        print("   - Timeout estesi implementati correttamente")
        print("   - Modalità asincrona per dataset complessi")
        print("   - Polling funzionante")
    else:
        print("\n⚠️ PROBLEMI RILEVATI - Ulteriori fix necessari")

if __name__ == "__main__":
    main() 