#!/usr/bin/env python3
"""
🚀 TEST FIX DEFINITIVO MULTI-BATCH v3.0
=====================================

Questo script testa il fix definitivo che risolve permanentemente
il problema del multi-batch che mostrava "Batch singolo".

Verifica:
1. Distribuzione ODL garantita tra autoclavi diverse
2. Generazione batch per autoclavi diverse
3. Campo is_real_multi_batch corretto
4. Logging dettagliato funzionante
"""

import requests
import json
import time

def test_multi_batch_fix():
    print("🚀 === TEST FIX DEFINITIVO MULTI-BATCH v3.0 ===")
    print()
    
    # Configurazione test
    url = 'http://localhost:8000/api/batch_nesting/genera-multi'
    test_data = {
        "odl_ids": ["5", "6", "7", "8", "9"],  # 5 ODL per testare distribuzione
        "parametri": {
            "padding_mm": 1,
            "min_distance_mm": 1
        }
    }
    
    print(f"📡 URL: {url}")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        print("⏳ Invio richiesta...")
        start_time = time.time()
        
        response = requests.post(url, json=test_data, timeout=60)
        
        elapsed = time.time() - start_time
        print(f"⚡ Risposta ricevuta in {elapsed:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ === RISPOSTA SUCCESS ===")
            print(f"🎯 Success: {data.get('success')}")
            print(f"📝 Message: {data.get('message')}")
            print(f"🏭 Total autoclavi: {data.get('total_autoclavi')}")
            print(f"✅ Success count: {data.get('success_count')}")
            print(f"❌ Error count: {data.get('error_count')}")
            print(f"🏆 Best batch ID: {data.get('best_batch_id')}")
            print(f"📊 Avg efficiency: {data.get('avg_efficiency')}%")
            print(f"🚀 Is real multi-batch: {data.get('is_real_multi_batch')}")
            print(f"🎯 Unique autoclavi count: {data.get('unique_autoclavi_count')}")
            print()
            
            # Analisi dettagliata batch results
            batch_results = data.get('batch_results', [])
            print(f"📋 === ANALISI {len(batch_results)} BATCH RESULTS ===")
            
            successful_batches = [b for b in batch_results if b.get('success')]
            failed_batches = [b for b in batch_results if not b.get('success')]
            
            print(f"✅ Batch riusciti: {len(successful_batches)}")
            print(f"❌ Batch falliti: {len(failed_batches)}")
            print()
            
            if successful_batches:
                print("✅ BATCH RIUSCITI:")
                unique_autoclavi = set()
                for i, batch in enumerate(successful_batches, 1):
                    autoclave_id = batch.get('autoclave_id')
                    autoclave_nome = batch.get('autoclave_nome')
                    efficiency = batch.get('efficiency', 0)
                    batch_id = batch.get('batch_id', 'N/A')
                    positioned_tools = batch.get('positioned_tools', 0)
                    
                    unique_autoclavi.add(autoclave_id)
                    
                    print(f"  {i}. {autoclave_nome} (ID:{autoclave_id})")
                    print(f"     Batch ID: {batch_id[:8] if batch_id != 'N/A' else 'N/A'}...")
                    print(f"     Efficienza: {efficiency:.1f}%")
                    print(f"     Tool posizionati: {positioned_tools}")
                    print()
                
                print(f"🎯 VERIFICA MULTI-BATCH:")
                print(f"   Autoclavi uniche: {len(unique_autoclavi)} ({unique_autoclavi})")
                print(f"   È realmente multi-batch: {len(unique_autoclavi) > 1}")
                print(f"   Backend dice multi-batch: {data.get('is_real_multi_batch')}")
                
                # Verifica coerenza
                backend_says_multi = data.get('is_real_multi_batch')
                actual_is_multi = len(unique_autoclavi) > 1
                
                if backend_says_multi == actual_is_multi:
                    print(f"   ✅ COERENZA OK: Backend e analisi concordano")
                else:
                    print(f"   ❌ COERENZA FALLITA: Backend dice {backend_says_multi}, analisi dice {actual_is_multi}")
                print()
            
            if failed_batches:
                print("❌ BATCH FALLITI:")
                for i, batch in enumerate(failed_batches, 1):
                    autoclave_nome = batch.get('autoclave_nome')
                    message = batch.get('message')
                    print(f"  {i}. {autoclave_nome}: {message}")
                print()
            
            # Verdetto finale
            print("🏁 === VERDETTO FINALE ===")
            if data.get('is_real_multi_batch') and len(successful_batches) > 1:
                print("🎉 SUCCESS: Fix definitivo FUNZIONA! Multi-batch generato correttamente.")
                print(f"   - {len(successful_batches)} batch generati per autoclavi diverse")
                print(f"   - Backend riconosce correttamente come multi-batch")
                print(f"   - Distribuzione ODL funzionante")
            elif len(successful_batches) == 1:
                print("⚠️  PARTIAL: Solo 1 batch generato (non multi-batch)")
                print("   - Verifica che ci siano più autoclavi disponibili")
                print("   - Controlla log backend per errori di generazione")
            else:
                print("❌ FAILED: Nessun batch generato con successo")
                print("   - Verifica configurazione autoclavi")
                print("   - Controlla log backend per errori")
        
        elif response.status_code == 422:
            print("❌ === VALIDATION ERROR ===")
            try:
                error_data = response.json()
                print(f"Detail: {error_data.get('detail')}")
            except:
                print(f"Raw response: {response.text}")
        
        else:
            print(f"❌ === HTTP ERROR {response.status_code} ===")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: Il backend non ha risposto entro 60 secondi")
        print("   - Verifica che il backend sia attivo su localhost:8000")
        print("   - Controlla che l'algoritmo non sia bloccato")
        
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR: Impossibile connettersi al backend")
        print("   - Verifica che il backend sia attivo: http://localhost:8000")
        print("   - Avvia backend con: cd backend && python -m uvicorn api.main:app --reload --port 8000")
        
    except Exception as e:
        print(f"💥 ERRORE INASPETTATO: {str(e)}")

if __name__ == "__main__":
    test_multi_batch_fix() 