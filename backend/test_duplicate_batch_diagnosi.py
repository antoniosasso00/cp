#!/usr/bin/env python3
"""
Script di diagnosi per il problema batch multipli per stessa autoclave
"""

import requests
import json
import time

def test_multi_batch_duplicates():
    """Test per identificare batch duplicati per stessa autoclave"""
    
    print("🔍 DIAGNOSI PROBLEMA BATCH MULTIPLI")
    print("=" * 60)
    
    url = 'http://localhost:8000/api/batch_nesting/genera-multi'
    payload = {
        'odl_ids': ['1', '2', '3', '4', '5'],
        'parametri': {
            'padding_mm': 1,
            'min_distance_mm': 1
        }
    }
    
    try:
        print("📡 Chiamata endpoint genera-multi...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        elapsed_time = time.time() - start_time
        
        print(f"\n⏱️ Tempo risposta: {elapsed_time:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERRORE HTTP: {response.text}")
            return
        
        data = response.json()
        
        print("\n📈 RISULTATI GENERALI:")
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message')}")
        print(f"   Total autoclavi: {data.get('total_autoclavi')}")
        print(f"   Success count: {data.get('success_count')}")
        print(f"   Error count: {data.get('error_count')}")
        print(f"   Is real multi-batch: {data.get('is_real_multi_batch')}")
        print(f"   Best batch ID: {data.get('best_batch_id')}")
        
        batch_results = data.get('batch_results', [])
        print(f"\n🎯 BATCH RESULTS: {len(batch_results)} totali")
        
        # Analisi dettagliata per autoclave
        autoclave_analysis = {}
        
        for i, batch in enumerate(batch_results):
            autoclave_id = batch.get('autoclave_id')
            autoclave_nome = batch.get('autoclave_nome', 'Unknown')
            batch_id = batch.get('batch_id')
            success = batch.get('success', False)
            efficiency = batch.get('efficiency', 0)
            
            print(f"   #{i+1}: {autoclave_nome} (ID:{autoclave_id}) - "
                  f"{'✅' if success else '❌'} - "
                  f"{efficiency:.1f}% - "
                  f"Batch:{batch_id[:8] if batch_id else 'None'}...")
            
            # Conta per autoclave
            key = f"{autoclave_nome}_{autoclave_id}"
            if key not in autoclave_analysis:
                autoclave_analysis[key] = []
            autoclave_analysis[key].append({
                'batch_id': batch_id,
                'success': success,
                'efficiency': efficiency,
                'batch_data': batch
            })
        
        print(f"\n🔍 ANALISI DUPLICATI:")
        duplicates_found = False
        
        for autoclave_key, batches in autoclave_analysis.items():
            autoclave_name = autoclave_key.split('_')[0]
            batch_count = len(batches)
            
            if batch_count > 1:
                duplicates_found = True
                print(f"🚨 DUPLICATO: {autoclave_name} ha {batch_count} batch:")
                for j, batch_info in enumerate(batches):
                    batch_id = batch_info['batch_id']
                    success = batch_info['success']
                    efficiency = batch_info['efficiency']
                    print(f"     #{j+1}: {batch_id[:8] if batch_id else 'None'}... - "
                          f"{'✅' if success else '❌'} - {efficiency:.1f}%")
            else:
                print(f"✅ OK: {autoclave_name} ha {batch_count} batch")
        
        if not duplicates_found:
            print("\n✅ RISULTATO: Nessun duplicato trovato - Comportamento corretto!")
        else:
            print("\n🚨 PROBLEMA CONFERMATO: Trovati batch duplicati per la stessa autoclave!")
            
            # Verifica se sono davvero duplicati o batch diversi
            print("\n🔧 VERIFICA DETTAGLIATA DUPLICATI:")
            for autoclave_key, batches in autoclave_analysis.items():
                if len(batches) > 1:
                    autoclave_name = autoclave_key.split('_')[0]
                    print(f"\n📋 {autoclave_name}:")
                    
                    for j, batch_info in enumerate(batches):
                        batch_data = batch_info['batch_data']
                        print(f"   Batch #{j+1}:")
                        print(f"     - Batch ID: {batch_data.get('batch_id')}")
                        print(f"     - Success: {batch_data.get('success')}")
                        print(f"     - Efficiency: {batch_data.get('efficiency')}")
                        print(f"     - Total weight: {batch_data.get('total_weight')}")
                        print(f"     - Positioned tools: {batch_data.get('positioned_tools')}")
                        print(f"     - Message: {batch_data.get('message')}")
        
        return duplicates_found
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRORE CONNESSIONE: {e}")
        return None
    except Exception as e:
        print(f"❌ ERRORE GENERALE: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Avvio test duplicati batch...")
    
    result = test_multi_batch_duplicates()
    
    if result is True:
        print("\n🎯 CONCLUSIONE: PROBLEMA CONFERMATO - System genera batch duplicati")
    elif result is False:
        print("\n🎯 CONCLUSIONE: SISTEMA OK - Nessun duplicato trovato")
    else:
        print("\n🎯 CONCLUSIONE: TEST FALLITO - Impossibile verificare") 