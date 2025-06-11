#!/usr/bin/env python3
"""
🔍 TEST FINALE MULTI-BATCH CARBONPILOT
======================================

Test comprensivo per verificare il comportamento del sistema multi-batch
e confermare che il problema dell'utente esiste.
"""

import requests
import json
import time
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title: str):
    """Stampa una sezione del test"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_result(success: bool, message: str, details: Dict = None):
    """Stampa il risultato di un test"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if details:
        print(f"   Details: {json.dumps(details, indent=2)}")

def test_system_status():
    """Verifica che il sistema sia attivo"""
    print_section("VERIFICA SISTEMA")
    
    try:
        # Test backend
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        backend_ok = response.status_code == 200
        print_result(backend_ok, f"Backend Status: {response.status_code}")
        
        # Test endpoint nesting data
        response = requests.get(f"{BASE_URL}/api/batch_nesting/data", timeout=10)
        data_ok = response.status_code == 200
        print_result(data_ok, f"Nesting Data: {response.status_code}")
        
        if data_ok:
            data = response.json()
            odl_count = len(data.get('odl_in_attesa_cura', []))
            autoclave_count = len(data.get('autoclavi_disponibili', []))
            print(f"   📋 ODL disponibili: {odl_count}")
            print(f"   🏭 Autoclavi disponibili: {autoclave_count}")
            
            return data_ok and odl_count >= 3 and autoclave_count >= 3
        
        return False
        
    except Exception as e:
        print_result(False, f"Sistema non raggiungibile: {e}")
        return False

def test_nesting_data():
    """Recupera e analizza i dati disponibili"""
    print_section("ANALISI DATI DISPONIBILI")
    
    try:
        response = requests.get(f"{BASE_URL}/api/batch_nesting/data", headers=HEADERS)
        if response.status_code != 200:
            print_result(False, f"Errore caricamento dati: {response.status_code}")
            return None, None
        
        data = response.json()
        odl_list = data.get('odl_in_attesa_cura', [])
        autoclave_list = data.get('autoclavi_disponibili', [])
        
        print(f"📋 ODL 'Attesa Cura': {len(odl_list)}")
        for i, odl in enumerate(odl_list[:5]):  # Primi 5
            print(f"   {i+1}. ODL {odl['id']} - {odl['parte']['part_number']} - {odl['tool']['larghezza_piano']}×{odl['tool']['lunghezza_piano']}mm")
        
        print(f"\n🏭 Autoclavi disponibili: {len(autoclave_list)}")
        for autoclave in autoclave_list:
            print(f"   - {autoclave['nome']} ({autoclave['codice']}) - {autoclave['lunghezza']}×{autoclave['larghezza_piano']}mm")
        
        return odl_list, autoclave_list
        
    except Exception as e:
        print_result(False, f"Errore nell'analisi dati: {e}")
        return None, None

def test_multi_batch_endpoint(odl_list: List[Dict], autoclave_list: List[Dict]):
    """Testa l'endpoint multi-batch con 13 ODL e 3 autoclavi"""
    print_section("TEST ENDPOINT MULTI-BATCH")
    
    # Usa tutti gli ODL disponibili (fino a 13)
    selected_odl_ids = [str(odl['id']) for odl in odl_list[:13]]
    
    print(f"🎯 Parametri test:")
    print(f"   📋 ODL selezionati: {len(selected_odl_ids)} ({selected_odl_ids})")
    print(f"   🏭 Autoclavi target: {len(autoclave_list)} (tutte disponibili)")
    
    payload = {
        "odl_ids": selected_odl_ids,
        "parametri": {
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        }
    }
    
    print(f"\n📤 Payload inviato:")
    print(json.dumps(payload, indent=2))
    
    try:
        print("\n🚀 Chiamata endpoint /genera-multi...")
        response = requests.post(
            f"{BASE_URL}/api/batch_nesting/genera-multi", 
            headers=HEADERS, 
            json=payload,
            timeout=120  # Timeout esteso per calcoli complessi
        )
        
        print(f"📡 Status Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            success = result.get('success', False)
            success_count = result.get('success_count', 0)
            total_autoclavi = result.get('total_autoclavi', 0)
            is_real_multi_batch = result.get('is_real_multi_batch', False)
            best_batch_id = result.get('best_batch_id')
            batch_results = result.get('batch_results', [])
            
            print(f"\n✅ RISULTATI MULTI-BATCH:")
            print(f"   🎯 Success: {success}")
            print(f"   📊 Success Count: {success_count}")
            print(f"   🏭 Total Autoclavi: {total_autoclavi}")
            print(f"   🚀 Is Real Multi-Batch: {is_real_multi_batch}")
            print(f"   🏆 Best Batch ID: {best_batch_id}")
            
            print(f"\n📋 DETTAGLIO BATCH GENERATI:")
            for i, batch_result in enumerate(batch_results):
                autoclave_nome = batch_result.get('autoclave_nome', f'Autoclave {i+1}')
                efficiency = batch_result.get('efficiency', 0)
                success_single = batch_result.get('success', False)
                batch_id = batch_result.get('batch_id', 'N/A')
                
                status_icon = "✅" if success_single else "❌"
                print(f"   {i+1}. {status_icon} {autoclave_nome}: {efficiency:.2f}% - ID: {batch_id}")
            
            # Verifica il problema dell'utente
            user_problem_detected = False
            if success_count < len(autoclave_list):
                user_problem_detected = True
                print(f"\n🚨 PROBLEMA UTENTE CONFERMATO:")
                print(f"   - Utente seleziona {len(autoclave_list)} autoclavi")
                print(f"   - Sistema genera solo {success_count} batch")
                print(f"   - Autoclavi non utilizzate: {len(autoclave_list) - success_count}")
            
            return {
                'success': success,
                'success_count': success_count,
                'total_autoclavi': total_autoclavi,
                'is_real_multi_batch': is_real_multi_batch,
                'best_batch_id': best_batch_id,
                'batch_results': batch_results,
                'user_problem_detected': user_problem_detected
            }
            
        else:
            error_text = response.text
            print_result(False, f"Errore HTTP {response.status_code}: {error_text}")
            return None
            
    except Exception as e:
        print_result(False, f"Errore nella chiamata multi-batch: {e}")
        return None

def main():
    """Esegue il test completo"""
    print("🧪 TEST FINALE MULTI-BATCH CARBONPILOT")
    print("=" * 60)
    
    # 1. Verifica sistema
    if not test_system_status():
        print("\n❌ Sistema non operativo. Interrompendo i test.")
        return
    
    # 2. Analizza dati
    odl_list, autoclave_list = test_nesting_data()
    if not odl_list or not autoclave_list:
        print("\n❌ Dati insufficienti per i test.")
        return
    
    if len(odl_list) < 3:
        print(f"\n⚠️ ODL insufficienti: {len(odl_list)} (minimo 3 richiesti)")
        return
    
    if len(autoclave_list) < 3:
        print(f"\n⚠️ Autoclavi insufficienti: {len(autoclave_list)} (minimo 3 richieste)")
        return
    
    # 3. Test multi-batch
    result = test_multi_batch_endpoint(odl_list, autoclave_list)
    
    # 4. Conclusioni
    print_section("CONCLUSIONI TEST")
    
    if result:
        if result['user_problem_detected']:
            print("🚨 PROBLEMA CONFERMATO:")
            print("   L'utente seleziona 3 autoclavi ma ottiene risultati solo su alcune.")
            print("   Questo conferma il problema segnalato.")
        else:
            print("✅ SISTEMA FUNZIONANTE:")
            print("   Multi-batch genera correttamente batch per tutte le autoclavi selezionate.")
        
        print(f"\n📊 STATISTICHE FINALI:")
        print(f"   - Autoclavi richieste: {result['total_autoclavi']}")
        print(f"   - Batch generati: {result['success_count']}")
        print(f"   - Successo operazione: {result['success']}")
        print(f"   - Multi-batch reale: {result['is_real_multi_batch']}")
    else:
        print("❌ TEST FALLITO:")
        print("   Impossibile completare il test multi-batch.")
    
    print("\n🏁 Test completato.")

if __name__ == "__main__":
    main() 