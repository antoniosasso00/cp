#!/usr/bin/env python3
"""
🚀 TEST RAPIDO TIMEOUT FIX
=========================

Test veloce per verificare se il fix timeout ha risolto il problema 2L multi-batch.
"""

import requests
import json
import time

def test_timeout_fix_quick():
    """Test rapido con dataset piccolo per verificare timeout fix"""
    print("🚀 === TEST RAPIDO TIMEOUT FIX ===\n")
    
    # Test con dataset piccolo (3 ODL, 3 autoclavi)
    url = 'http://localhost:8000/api/batch_nesting/2l-multi'
    data = {
        'autoclavi_2l': [1, 2, 3],
        'odl_ids': [4, 13, 14],  # Solo 3 ODL per test rapido
        'parametri': {
            'padding_mm': 5.0,
            'min_distance_mm': 10.0
        },
        'use_cavalletti': True,
        'prefer_base_level': True
    }
    
    print("📋 Test Configuration:")
    print(f"   Autoclavi: {len(data['autoclavi_2l'])}")
    print(f"   ODL: {len(data['odl_ids'])}")
    print(f"   Cavalletti: {data['use_cavalletti']}")
    
    try:
        print(f"\n🚀 Chiamata endpoint con timeout 5 minuti...")
        start_time = time.time()
        
        response = requests.post(url, json=data, timeout=300)  # 5 minuti timeout
        
        duration = time.time() - start_time
        
        print(f"✅ Risposta ricevuta in {duration:.1f} secondi")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            success_count = result.get('success_count', 0)
            total_count = result.get('total_autoclavi', 0)
            best_batch_id = result.get('best_batch_id')
            
            print(f"\n📊 RISULTATO FINALE:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Batch generati: {success_count}/{total_count}")
            print(f"   Best Batch ID: {best_batch_id}")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            # Dettagli per ogni batch
            batch_results = result.get('batch_results', [])
            print(f"\n📋 DETTAGLI BATCH ({len(batch_results)} risultati):")
            
            for i, batch in enumerate(batch_results):
                success = batch.get('success', False)
                autoclave_nome = batch.get('autoclave_nome', 'N/A')
                positioned_tools = batch.get('positioned_tools', 0)
                efficiency = batch.get('efficiency', 0)
                message = batch.get('message', 'N/A')
                
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} Autoclave {autoclave_nome}:")
                print(f"      Tools posizionati: {positioned_tools}")
                print(f"      Efficienza: {efficiency:.1f}%")
                print(f"      Messaggio: {message}")
            
            # Verifica risultato atteso
            if success_count >= 2:  # Almeno 2/3 batch dovrebbero riuscire
                print(f"\n🎯 RISULTATO: TIMEOUT FIX SEMBRA FUNZIONARE!")
                print(f"   Generati {success_count} batch su {total_count} (atteso: >=2)")
                return True
            else:
                print(f"\n⚠️ RISULTATO: TIMEOUT FIX PARZIALE")
                print(f"   Solo {success_count} batch generati, potrebbero servire altri aggiustamenti")
                return False
                
        else:
            print(f"❌ Errore HTTP {response.status_code}:")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.Timeout:
        print("❌ TIMEOUT: Il problema persiste anche dopo il fix")
        return False
    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        return False

if __name__ == "__main__":
    success = test_timeout_fix_quick()
    if success:
        print("\n🎯 PROSSIMO PASSO: Test con dataset completo (tutti gli ODL)")
    else:
        print("\n🔧 PROSSIMO PASSO: Ulteriori debugging timeout") 