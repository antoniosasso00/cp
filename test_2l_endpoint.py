#!/usr/bin/env python3
"""
Test specifico per l'endpoint 2L-multi che sta causando HTTP 500
"""

import requests
import json
import time

def test_2l_endpoint():
    """Testa specificamente l'endpoint 2L-multi che sta fallendo"""
    
    print("🔍 TEST ENDPOINT 2L-MULTI - Debug HTTP 500")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    
    # 1. Test endpoint 2L-multi che sta fallendo nel frontend
    print(f"🚀 Test endpoint /api/batch_nesting/2l-multi...")
    
    try:
        # Payload simile a quello che invia il frontend
        payload = {
            "autoclavi_2l": [1, 2, 3],  # Le 3 autoclavi con 2L abilitato
            "odl_ids": [5, 6, 7, 8, 9],  # Solo alcuni ODL per test
            "parametri": {
                "padding_mm": 5,
                "min_distance_mm": 10
            },
            "use_cavalletti": True,
            "prefer_base_level": True,
            "cavalletti_config": {
                "min_distance_from_edge": 30.0,
                "max_span_without_support": 400.0,
                "min_distance_between_cavalletti": 200.0,
                "safety_margin_x": 5.0,
                "safety_margin_y": 5.0,
                "prefer_symmetric": True,
                "force_minimum_two": True
            }
        }
        
        print(f"📦 Payload:")
        print(json.dumps(payload, indent=2))
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/api/batch_nesting/2l-multi",
            json=payload,
            timeout=60,  # Timeout per debug
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n⏱️ Durata: {duration:.2f}s")
        print(f"📡 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESSO 2L!")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message', 'no message')}")
            print(f"   Batch count: {len(result.get('batch_results', []))}")
            return True
            
        elif response.status_code == 500:
            print(f"❌ ERRORE 500 - DETTAGLI:")
            print(f"📄 Response text: {response.text}")
            
            try:
                error_data = response.json()
                print(f"🔍 Error detail: {error_data.get('detail', 'no detail')}")
                if 'traceback' in error_data:
                    print(f"🐛 Traceback: {error_data['traceback']}")
            except:
                print("❌ Impossibile parsare JSON di errore")
            
            return False
        else:
            print(f"❌ Status inaspettato: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT dopo 60s")
        return False
    except Exception as e:
        print(f"❌ Errore richiesta: {e}")
        return False

def test_simple_2l():
    """Test con payload ultra-semplificato per 2L"""
    
    print(f"\n🔧 TEST SEMPLIFICATO 2L...")
    
    backend_url = "http://localhost:8000"
    
    # Payload minimo
    payload = {
        "autoclavi_2l": [1],  # Solo una autoclave
        "odl_ids": [5, 6],    # Solo 2 ODL
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 8
        },
        "use_cavalletti": True,
        "prefer_base_level": True
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/batch_nesting/2l-multi",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ PAYLOAD SEMPLIFICATO FUNZIONA!")
            return True
        else:
            print(f"❌ Errore anche con payload semplificato: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Errore payload semplificato: {e}")
        return False

def main():
    """Test completo dell'endpoint 2L"""
    
    print("🔍 DIAGNOSI COMPLETA ENDPOINT 2L-MULTI")
    print("=" * 60)
    
    # Test 1: Endpoint 2L complesso (come frontend)
    success_complex = test_2l_endpoint()
    
    # Test 2: Endpoint 2L semplificato
    success_simple = test_simple_2l()
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI:")
    
    if success_complex:
        print("✅ Endpoint 2L-multi: FUNZIONANTE")
        print("   Il problema non è nell'endpoint 2L")
    elif success_simple:
        print("⚠️ Endpoint 2L-multi: PROBLEMI CON PAYLOAD COMPLESSO")
        print("   Il problema è nei parametri o nella complessità")
    else:
        print("❌ Endpoint 2L-multi: COMPLETAMENTE NON FUNZIONANTE")
        print("   Il problema è nell'implementazione 2L del backend")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 