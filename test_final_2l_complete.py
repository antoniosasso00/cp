#!/usr/bin/env python3
"""
Test finale completo per identificare e risolvere il problema 2L definitivamente
"""

import requests
import json
import time

def test_complete_comparison():
    """Test completo che confronta endpoint normale vs 2L per identificare il problema"""
    
    print("🔧 === TEST FINALE COMPLETO - NORMALE vs 2L ===")
    print("=" * 70)
    
    backend_url = "http://localhost:8000"
    
    # 1. Ottieni dati reali
    try:
        data_response = requests.get(f"{backend_url}/api/batch_nesting/data", timeout=10)
        if data_response.status_code != 200:
            print(f"❌ Errore recupero dati: {data_response.status_code}")
            return
        
        data = data_response.json()
        odls = data['odl_in_attesa_cura']
        autoclavi = data['autoclavi_disponibili']
        
        if not odls or not autoclavi:
            print("❌ Nessun dato disponibile")
            return
        
        print(f"✅ Dati: {len(odls)} ODL, {len(autoclavi)} autoclavi")
        
        # 2. TEST ENDPOINT NORMALE (che sappiamo funzionare)
        print("\n" + "="*50)
        print("🚀 TEST 1: ENDPOINT NORMALE /genera-multi")
        print("="*50)
        
        payload_normale = {
            "odl_ids": [str(odl['id']) for odl in odls[:5]],
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 15
            }
        }
        
        try:
            start_time = time.time()
            response_normale = requests.post(
                f"{backend_url}/api/batch_nesting/genera-multi",
                json=payload_normale,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            duration_normale = time.time() - start_time
            
            print(f"⏱️ Durata endpoint normale: {duration_normale:.2f}s")
            print(f"📡 Status Code normale: {response_normale.status_code}")
            
            if response_normale.status_code == 200:
                result_normale = response_normale.json()
                print("✅ ENDPOINT NORMALE: SUCCESSO")
                print(f"   Success count: {result_normale.get('success_count', 0)}")
                print(f"   Message: {result_normale.get('message', 'N/A')}")
            else:
                print(f"❌ ENDPOINT NORMALE: FALLITO {response_normale.status_code}")
                try:
                    error = response_normale.json()
                    print(f"   Errore: {error.get('detail', response_normale.text)}")
                except:
                    print(f"   Response: {response_normale.text}")
        
        except Exception as e:
            print(f"❌ Errore endpoint normale: {str(e)}")
        
        # 3. TEST ENDPOINT 2L (che sappiamo fallire)
        print("\n" + "="*50)
        print("🚀 TEST 2: ENDPOINT 2L /2l-multi")
        print("="*50)
        
        autoclavi_2l = [a for a in autoclavi if a.get('usa_cavalletti', False)]
        if not autoclavi_2l:
            print("⚠️ Nessuna autoclave 2L disponibile")
            return
        
        payload_2l = {
            "autoclavi_2l": [auto['id'] for auto in autoclavi_2l],
            "odl_ids": [odl['id'] for odl in odls[:5]],
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 15
            },
            "use_cavalletti": True,
            "prefer_base_level": True
        }
        
        try:
            start_time = time.time()
            response_2l = requests.post(
                f"{backend_url}/api/batch_nesting/2l-multi",
                json=payload_2l,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            duration_2l = time.time() - start_time
            
            print(f"⏱️ Durata endpoint 2L: {duration_2l:.2f}s")
            print(f"📡 Status Code 2L: {response_2l.status_code}")
            
            if response_2l.status_code == 200:
                result_2l = response_2l.json()
                print("✅ ENDPOINT 2L: SUCCESSO!")
                print(f"   Success count: {result_2l.get('success_count', 0)}")
                print(f"   Message: {result_2l.get('message', 'N/A')}")
            else:
                print(f"❌ ENDPOINT 2L: FALLITO {response_2l.status_code}")
                try:
                    error = response_2l.json()
                    print(f"   Errore: {error.get('detail', response_2l.text)}")
                except:
                    print(f"   Response: {response_2l.text}")
        
        except Exception as e:
            print(f"❌ Errore endpoint 2L: {str(e)}")
        
        # 4. TEST ENDPOINT SINGOLO 2L (più semplice)
        print("\n" + "="*50)
        print("🚀 TEST 3: ENDPOINT SINGOLO 2L /2l")
        print("="*50)
        
        payload_2l_single = {
            "autoclave_id": autoclavi_2l[0]['id'],
            "odl_ids": [odl['id'] for odl in odls[:3]],
            "padding_mm": 10.0,
            "min_distance_mm": 15.0,
            "use_cavalletti": True,
            "prefer_base_level": True
        }
        
        try:
            start_time = time.time()
            response_2l_single = requests.post(
                f"{backend_url}/api/batch_nesting/2l",
                json=payload_2l_single,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            duration_2l_single = time.time() - start_time
            
            print(f"⏱️ Durata endpoint 2L singolo: {duration_2l_single:.2f}s")
            print(f"📡 Status Code 2L singolo: {response_2l_single.status_code}")
            
            if response_2l_single.status_code == 200:
                result_2l_single = response_2l_single.json()
                print("✅ ENDPOINT 2L SINGOLO: SUCCESSO!")
                print(f"   Success: {result_2l_single.get('success', False)}")
                print(f"   Message: {result_2l_single.get('message', 'N/A')}")
                print(f"   Positioned tools: {result_2l_single.get('metrics', {}).get('pieces_positioned', 0)}")
            else:
                print(f"❌ ENDPOINT 2L SINGOLO: FALLITO {response_2l_single.status_code}")
                try:
                    error = response_2l_single.json()
                    print(f"   Errore: {error.get('detail', response_2l_single.text)}")
                except:
                    print(f"   Response: {response_2l_single.text}")
        
        except Exception as e:
            print(f"❌ Errore endpoint 2L singolo: {str(e)}")
        
        print("\n" + "="*70)
        print("📊 RIASSUNTO TEST FINALE:")
        print("   1. Endpoint normale: Generalmente funziona")
        print("   2. Endpoint 2L multi: Fallisce sempre")
        print("   3. Endpoint 2L singolo: Da verificare sopra")
        print("   📝 Il problema è nell'implementazione 2L, non nella modalità asincrona")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Errore generale: {str(e)}")

if __name__ == "__main__":
    test_complete_comparison() 