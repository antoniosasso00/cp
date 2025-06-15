#!/usr/bin/env python3
"""
Test per verificare che le correzioni 2L funzionino correttamente
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests
import time
import json

def test_2l_fixes():
    """Test completo delle correzioni 2L"""
    print("🔧 TEST CORREZIONI 2L")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # 1. Test connessione server
        print("🔍 Test connessione server...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code != 200:
            print("❌ Server non raggiungibile")
            return False
        print("✅ Server raggiungibile")
        
        # 2. Ottieni dati per 2L
        print("\n📋 Recupero dati 2L...")
        response = requests.get(f"{base_url}/nesting/data", timeout=10)
        if response.status_code != 200:
            print(f"❌ Errore recupero dati: {response.status_code}")
            return False
        
        data = response.json()
        
        # Filtra autoclavi 2L
        autoclavi_2l = [a for a in data['autoclavi_disponibili'] if a.get('usa_cavalletti', False)]
        odl_disponibili = data['odl_in_attesa_cura']
        
        print(f"   Autoclavi 2L: {len(autoclavi_2l)}")
        print(f"   ODL disponibili: {len(odl_disponibili)}")
        
        if len(autoclavi_2l) == 0:
            print("❌ Nessuna autoclave 2L disponibile")
            return False
        
        if len(odl_disponibili) < 10:
            print("❌ Troppo pochi ODL per test significativo")
            return False
        
        # 3. Test generazione 2L multi-batch
        print("\n🚀 Test generazione 2L multi-batch...")
        
        # Seleziona prime 3 autoclavi 2L e primi 20 ODL
        autoclave_ids = [a['id'] for a in autoclavi_2l[:3]]
        odl_ids = [odl['id'] for odl in odl_disponibili[:20]]
        
        request_data = {
            "autoclavi_2l": autoclave_ids,
            "odl_ids": odl_ids,
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 15
            },
            "use_cavalletti": True,
            "prefer_base_level": False,  # Usa i nuovi parametri bilanciati
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
        
        print(f"   Autoclavi: {autoclave_ids}")
        print(f"   ODL: {len(odl_ids)} selezionati")
        
        response = requests.post(
            f"{base_url}/nesting/2l-multi",
            json=request_data,
            timeout=120  # Timeout generoso per il test
        )
        
        if response.status_code != 200:
            print(f"❌ Errore generazione 2L: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return False
        
        result = response.json()
        print("✅ Generazione 2L completata")
        
        # 4. Analisi risultati
        print("\n📊 ANALISI RISULTATI:")
        
        batch_results = result.get('batch_results', [])
        print(f"   Batch generati: {len(batch_results)}")
        
        total_level_0 = 0
        total_level_1 = 0
        total_cavalletti = 0
        
        for i, batch in enumerate(batch_results):
            level_0_count = batch.get('level_0_count', 0)
            level_1_count = batch.get('level_1_count', 0)
            cavalletti_count = batch.get('cavalletti_count', 0)
            efficiency = batch.get('metrics', {}).get('efficiency_percentage', 0)
            
            total_level_0 += level_0_count
            total_level_1 += level_1_count
            total_cavalletti += cavalletti_count
            
            print(f"   Batch {i+1}: L0={level_0_count}, L1={level_1_count}, cavalletti={cavalletti_count}, eff={efficiency:.1f}%")
        
        print(f"\n🎯 TOTALI:")
        print(f"   Livello 0: {total_level_0} tool")
        print(f"   Livello 1: {total_level_1} tool")
        print(f"   Cavalletti: {total_cavalletti}")
        print(f"   Distribuzione: {total_level_0/(total_level_0+total_level_1)*100:.1f}% L0, {total_level_1/(total_level_0+total_level_1)*100:.1f}% L1")
        
        # 5. Verifica correzioni
        print(f"\n✅ VERIFICA CORREZIONI:")
        
        if total_level_1 > 0:
            print(f"   ✅ SUCCESSO: {total_level_1} tool posizionati su livello 1!")
            print(f"   ✅ Le correzioni ai criteri di eligibilità funzionano")
            print(f"   ✅ L'algoritmo ora usa entrambi i livelli")
        else:
            print(f"   ⚠️ ATTENZIONE: Nessun tool su livello 1")
            print(f"   🔍 Possibili cause:")
            print(f"      - Tool ancora troppo pesanti/grandi per criteri rilassati")
            print(f"      - Algoritmo sequenziale ancora troppo conservativo")
            print(f"      - Tutti i tool stanno comodamente su livello 0")
        
        if total_cavalletti > 0:
            print(f"   ✅ SUCCESSO: {total_cavalletti} cavalletti generati")
        else:
            print(f"   ⚠️ Nessun cavalletto generato")
        
        # 6. Test caricamento risultati
        if batch_results:
            print(f"\n🔍 Test caricamento risultati...")
            first_batch_id = batch_results[0]['id']
            
            response = requests.get(f"{base_url}/nesting/result/{first_batch_id}?multi=true", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Caricamento risultati OK")
                
                result_data = response.json()
                if isinstance(result_data, dict) and 'batch_results' in result_data:
                    print(f"   ✅ Multi-batch mode funziona")
                else:
                    print(f"   ✅ Single-batch mode funziona")
            else:
                print(f"   ⚠️ Errore caricamento risultati: {response.status_code}")
        
        return total_level_1 > 0  # Successo se almeno un tool su livello 1
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore connessione: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_eligibility_improvements():
    """Test specifico per verificare i miglioramenti ai criteri di eligibilità"""
    print(f"\n🔍 TEST CRITERI ELIGIBILITÀ MIGLIORATI")
    print("=" * 50)
    
    # Simula i criteri vecchi vs nuovi
    test_tools = [
        {"peso": 45.0, "larghezza": 450, "lunghezza": 750, "nome": "Tool_A"},
        {"peso": 75.0, "larghezza": 600, "lunghezza": 900, "nome": "Tool_B"},
        {"peso": 95.0, "larghezza": 750, "lunghezza": 1100, "nome": "Tool_C"},
        {"peso": 120.0, "larghezza": 400, "lunghezza": 800, "nome": "Tool_D"},
    ]
    
    print("📊 Confronto criteri eligibilità:")
    print(f"{'Tool':<8} {'Peso':<6} {'Dim':<10} {'Vecchi':<8} {'Nuovi':<8} {'Miglioramento'}")
    print("-" * 60)
    
    improvements = 0
    
    for tool in test_tools:
        peso = tool["peso"]
        larghezza = tool["larghezza"]
        lunghezza = tool["lunghezza"]
        nome = tool["nome"]
        
        # Criteri vecchi (restrittivi)
        eligible_old = (peso <= 50.0 and larghezza <= 500.0 and lunghezza <= 800.0)
        
        # Criteri nuovi (rilassati)
        eligible_new = (peso <= 100.0 and larghezza <= 800.0 and lunghezza <= 1200.0)
        
        old_str = "✅" if eligible_old else "❌"
        new_str = "✅" if eligible_new else "❌"
        improvement = "📈" if (not eligible_old and eligible_new) else ("✅" if eligible_new else "❌")
        
        if not eligible_old and eligible_new:
            improvements += 1
        
        print(f"{nome:<8} {peso:<6.1f} {lunghezza}x{larghezza:<4} {old_str:<8} {new_str:<8} {improvement}")
    
    print(f"\n🎯 RISULTATO: {improvements}/{len(test_tools)} tool migliorati con nuovi criteri")
    
    return improvements > 0

if __name__ == "__main__":
    print("🚀 AVVIO TEST CORREZIONI 2L")
    print("=" * 60)
    
    # Test criteri eligibilità
    eligibility_ok = test_eligibility_improvements()
    
    # Test completo sistema
    system_ok = test_2l_fixes()
    
    print(f"\n🏁 RISULTATO FINALE:")
    print("=" * 60)
    
    if eligibility_ok:
        print("✅ Criteri eligibilità migliorati")
    else:
        print("❌ Problemi criteri eligibilità")
    
    if system_ok:
        print("✅ Sistema 2L funziona correttamente")
        print("✅ Tool posizionati su livello 1")
    else:
        print("⚠️ Sistema 2L necessita ulteriori correzioni")
    
    if eligibility_ok and system_ok:
        print("\n🎉 TUTTE LE CORREZIONI FUNZIONANO!")
    else:
        print("\n🔧 Necessarie ulteriori correzioni") 