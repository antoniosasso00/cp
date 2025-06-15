#!/usr/bin/env python3
"""
🚀 TEST 2L MULTI-BATCH DEBUG
============================

Script per diagnosticare perché vengono generati solo 1/3 batch nel sistema 2L multi.
"""

import requests
import json
import time

def test_2l_multi_batch():
    """Test dell'endpoint 2L multi-batch"""
    print("🚀 === TEST 2L MULTI-BATCH DEBUG ===\n")
    
    # 1. Test autoclavi disponibili
    try:
        print("📋 1. Verificando autoclavi disponibili...")
        url_autoclavi = 'http://localhost:8000/api/autoclavi/'
        response = requests.get(url_autoclavi, timeout=10)
        autoclavi = response.json()
        
        print(f"   Totale autoclavi: {len(autoclavi)}")
        autoclavi_2l = []
        for a in autoclavi:
            usa_cavalletti = a.get('usa_cavalletti', False)
            print(f"   - ID: {a.get('id')}, Nome: {a.get('nome')}, Supporta 2L: {usa_cavalletti}")
            if usa_cavalletti:
                autoclavi_2l.append(a.get('id'))
        
        print(f"   Autoclavi 2L disponibili: {autoclavi_2l}")
        
        if len(autoclavi_2l) < 3:
            print(f"   ⚠️ PROBLEMA: Solo {len(autoclavi_2l)} autoclavi supportano 2L, ma ne servono 3!")
            return
            
    except Exception as e:
        print(f"   ❌ Errore recupero autoclavi: {e}")
        return
    
    # 2. Test ODL disponibili
    try:
        print("\n📋 2. Verificando ODL disponibili...")
        url_odl = 'http://localhost:8000/api/odl/'
        response = requests.get(url_odl, timeout=10)
        odls = response.json()
        
        odl_attesa_cura = [odl for odl in odls if odl.get('status') == 'Attesa Cura']
        print(f"   Totale ODL: {len(odls)}")
        print(f"   ODL in 'Attesa Cura': {len(odl_attesa_cura)}")
        
        if len(odl_attesa_cura) < 4:
            print(f"   ⚠️ PROBLEMA: Solo {len(odl_attesa_cura)} ODL in 'Attesa Cura', potrebbero non essere sufficienti!")
        
        # Mostra primi ODL disponibili
        for i, odl in enumerate(odl_attesa_cura[:8]):
            print(f"   - ODL {odl.get('id')}: {odl.get('numero_odl')} - {odl.get('status')}")
            
    except Exception as e:
        print(f"   ❌ Errore recupero ODL: {e}")
        return
    
    # 3. Test endpoint 2L multi-batch
    try:
        print("\n🚀 3. Testando endpoint 2L multi-batch...")
        url_2l = 'http://localhost:8000/api/batch_nesting/2l-multi'
        
        # Usa le prime 3 autoclavi 2L e primi ODL disponibili
        test_autoclavi = autoclavi_2l[:3] if len(autoclavi_2l) >= 3 else autoclavi_2l
        test_odl_ids = [odl.get('id') for odl in odl_attesa_cura[:6]]
        
        data = {
            'autoclavi_2l': test_autoclavi,
            'odl_ids': test_odl_ids,
            'parametri': {
                'padding_mm': 5.0,
                'min_distance_mm': 10.0
            },
            'use_cavalletti': True,
            'prefer_base_level': True
        }
        
        print(f"   Request data: {json.dumps(data, indent=4)}")
        print("   Sending request... (timeout 60s)")
        
        start_time = time.time()
        response = requests.post(url_2l, json=data, timeout=60)
        duration = time.time() - start_time
        
        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ⏱️ Duration: {duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Response Summary:")
            print(f"      Success: {result.get('success')}")
            print(f"      Message: {result.get('message')}")
            print(f"      Success Count: {result.get('success_count')}")
            print(f"      Error Count: {result.get('error_count')}")
            print(f"      Best Batch ID: {result.get('best_batch_id')}")
            
            batch_results = result.get('batch_results', [])
            print(f"      Batch Results: {len(batch_results)}")
            
            for i, batch in enumerate(batch_results):
                success = batch.get('success', False)
                autoclave_nome = batch.get('autoclave_nome', 'N/A')
                positioned_tools = batch.get('positioned_tools', 0)
                efficiency = batch.get('efficiency', 0)
                message = batch.get('message', 'N/A')
                
                status_icon = "✅" if success else "❌"
                print(f"        {status_icon} Batch {i+1}: {autoclave_nome}")
                print(f"            Tools posizionati: {positioned_tools}")
                print(f"            Efficienza: {efficiency:.1f}%")
                print(f"            Messaggio: {message}")
            
        else:
            print(f"   ❌ Error Response: {response.text}")
            
    except requests.Timeout:
        print("   ❌ TIMEOUT: L'endpoint ha superato i 60 secondi")
    except Exception as e:
        print(f"   ❌ Errore chiamata 2L multi: {e}")

if __name__ == "__main__":
    test_2l_multi_batch() 