#!/usr/bin/env python3
"""
🔍 SIMULAZIONE FLUSSO FRONTEND MULTI-BATCH
==========================================

Simula esattamente quello che fa il frontend per identificare
dove si rompe la catena del multi-batch.
"""

import requests
import json
import time
from urllib.parse import urlencode

def simulate_frontend_flow():
    """Simula il flusso completo frontend per multi-batch"""
    
    print("🎭 === SIMULAZIONE FLUSSO FRONTEND ===")
    print()
    
    # 1. STEP 1: Carica dati nesting (come fa il frontend)
    print("📡 STEP 1: Caricamento dati nesting...")
    nesting_response = requests.get('http://localhost:8000/api/batch_nesting/data')
    
    if nesting_response.status_code != 200:
        print(f"❌ Errore caricamento dati: {nesting_response.status_code}")
        return False
    
    nesting_data = nesting_response.json()
    autoclavi = nesting_data.get('autoclavi_disponibili', [])
    odl = nesting_data.get('odl_in_attesa_cura', [])
    
    print(f"✅ Dati caricati: {len(autoclavi)} autoclavi, {len(odl)} ODL")
    
    # 2. STEP 2: Simula selezione utente (TUTTE le autoclavi + primi 5 ODL)
    print("\n🎯 STEP 2: Simulazione selezione utente...")
    
    # Simula che l'utente seleziona TUTTE le autoclavi (multi-batch)
    selected_autoclavi = [str(auto['id']) for auto in autoclavi]
    selected_odl = [str(o['id']) for o in odl[:5]]  # Primi 5 ODL
    
    print(f"👤 Utente seleziona:")
    print(f"   - Autoclavi: {selected_autoclavi} ({len(selected_autoclavi)} autoclavi)")
    print(f"   - ODL: {selected_odl} ({len(selected_odl)} ODL)")
    
    # 3. STEP 3: Logica frontend per determinare endpoint
    print("\n🧠 STEP 3: Logica frontend per endpoint...")
    
    is_multi_batch_frontend = len(selected_autoclavi) > 1
    print(f"🔍 Frontend logic: selectedAutoclavi.length > 1 = {is_multi_batch_frontend}")
    
    if is_multi_batch_frontend:
        print("🚀 Frontend sceglie: ENDPOINT MULTI-BATCH")
        endpoint = 'http://localhost:8000/api/batch_nesting/genera-multi'
        payload = {
            "odl_ids": selected_odl,
            "parametri": {
                "padding_mm": 1,
                "min_distance_mm": 1
            }
        }
    else:
        print("🔄 Frontend sceglie: ENDPOINT SINGLE-BATCH")
        endpoint = 'http://localhost:8000/api/batch_nesting/genera'
        payload = {
            "odl_ids": selected_odl,
            "autoclave_ids": selected_autoclavi,
            "parametri": {
                "padding_mm": 1,
                "min_distance_mm": 1
            }
        }
    
    # 4. STEP 4: Chiamata endpoint generazione
    print(f"\n📡 STEP 4: Chiamata endpoint generazione...")
    print(f"URL: {endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(endpoint, json=payload, timeout=120)
        duration = time.time() - start_time
        
        print(f"⚡ Risposta in {duration:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Errore generazione: {response.text}")
            return False
        
        data = response.json()
        
        # 5. STEP 5: Logica frontend per determinare redirect
        print(f"\n🧠 STEP 5: Logica frontend per redirect...")
        
        success = data.get('success', False)
        is_real_multi_batch = data.get('is_real_multi_batch', False)
        best_batch_id = data.get('best_batch_id')
        success_count = data.get('success_count', 0)
        unique_autoclavi_count = data.get('unique_autoclavi_count', 0)
        
        print(f"📊 Risposta backend:")
        print(f"   - success: {success}")
        print(f"   - is_real_multi_batch: {is_real_multi_batch}")
        print(f"   - best_batch_id: {best_batch_id}")
        print(f"   - success_count: {success_count}")
        print(f"   - unique_autoclavi_count: {unique_autoclavi_count}")
        
        if success:
            # Simula la logica frontend per determinare il redirect
            isRealMultiBatch = is_real_multi_batch == True
            
            print(f"\n🔍 DETERMINAZIONE REDIRECT:")
            print(f"   - Backend is_real_multi_batch: {is_real_multi_batch}")
            print(f"   - Frontend isRealMultiBatch: {isRealMultiBatch}")
            
            if isRealMultiBatch and best_batch_id:
                redirect_url = f"/nesting/result/{best_batch_id}?multi=true"
                print(f"🚀 Frontend redirect: MULTI-BATCH")
                print(f"   URL: {redirect_url}")
                
                # 6. STEP 6: Test endpoint result con multi=true
                print(f"\n📡 STEP 6: Test endpoint result...")
                result_url = f'http://localhost:8000/api/batch_nesting/result/{best_batch_id}?multi=true'
                result_response = requests.get(result_url)
                
                print(f"📊 Result status: {result_response.status_code}")
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    batch_results = result_data.get('batch_results', [])
                    
                    print(f"✅ Result endpoint: {len(batch_results)} batch trovati")
                    
                    for i, batch in enumerate(batch_results):
                        autoclave_nome = batch.get('autoclave', {}).get('nome', 'N/A')
                        efficiency = batch.get('metrics', {}).get('efficiency_percentage', 0)
                        print(f"   {i+1}. {autoclave_nome}: {efficiency:.1f}%")
                    
                    if len(batch_results) > 1:
                        print("✅ SUCCESSO: Multi-batch rilevato correttamente!")
                        return True
                    else:
                        print("❌ PROBLEMA: Solo 1 batch nel result endpoint")
                        return False
                else:
                    print(f"❌ Errore result endpoint: {result_response.status_code}")
                    print(f"Response: {result_response.text}")
                    return False
                    
            elif best_batch_id:
                redirect_url = f"/nesting/result/{best_batch_id}"
                print(f"🔄 Frontend redirect: SINGLE-BATCH")
                print(f"   URL: {redirect_url}")
                print("⚠️ Questo spiega perché l'utente vede 'Batch singolo'!")
                return False
            else:
                print("❌ Nessun batch ID nella risposta")
                return False
        else:
            print("❌ Generazione fallita")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante simulazione: {e}")
        return False

if __name__ == "__main__":
    success = simulate_frontend_flow()
    if success:
        print("\n🎯 CONCLUSIONE: Flusso frontend funziona correttamente")
    else:
        print("\n❌ CONCLUSIONE: Problema identificato nel flusso frontend") 