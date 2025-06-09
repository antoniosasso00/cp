#!/usr/bin/env python3
"""
🔍 TEST DIAGNOSI PROFONDA MULTI-BATCH
=====================================

Script per testare il nuovo sistema di diagnosi e identificare
perché il multi-batch a volte funziona e a volte no.
"""

import requests
import json
import time
from datetime import datetime

def test_diagnosi_sistema():
    """Testa l'endpoint di diagnosi sistema"""
    print("🔍 === TEST DIAGNOSI SISTEMA ===")
    print()
    
    try:
        # Test diagnosi sistema
        print("📡 Chiamata endpoint diagnosi...")
        response = requests.get('http://localhost:8000/api/batch_nesting/diagnosi-sistema', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ === STATO SISTEMA ===")
            print(f"🕐 Timestamp: {data.get('timestamp')}")
            print(f"🏭 Autoclavi disponibili: {data.get('autoclavi_disponibili')}")
            print(f"📋 ODL in attesa cura: {data.get('odl_attesa_cura')}")
            print(f"📊 Batch sospesi totali: {data.get('total_batch_sospesi')}")
            print(f"🚀 Sistema pronto multi-batch: {data.get('sistema_pronto_multi_batch')}")
            print()
            
            # Dettagli autoclavi
            print("🏭 === DETTAGLI AUTOCLAVI ===")
            autoclavi_info = data.get('autoclavi_info', [])
            for i, autoclave in enumerate(autoclavi_info, 1):
                print(f"{i}. {autoclave['nome']} (ID: {autoclave['id']})")
                print(f"   Dimensioni: {autoclave['dimensioni']}")
                print(f"   Max load: {autoclave['max_load_kg']}kg")
                print(f"   Linee vuoto: {autoclave['num_linee_vuoto']}")
                print(f"   Batch sospesi: {autoclave['batch_sospesi']}")
                print(f"   Stato: {autoclave['stato']}")
                print()
            
            # Problemi identificati
            problemi = data.get('problemi_identificati', [])
            if problemi:
                print("🚨 === PROBLEMI IDENTIFICATI ===")
                for i, problema in enumerate(problemi, 1):
                    livello = problema['livello']
                    icon = "❌" if livello == "CRITICO" else "⚠️"
                    print(f"{icon} {i}. [{livello}] {problema['problema']}")
                    print(f"   Soluzione: {problema['soluzione']}")
                    print()
            else:
                print("✅ Nessun problema identificato!")
                print()
            
            # Raccomandazioni
            raccomandazioni = data.get('raccomandazioni', [])
            if raccomandazioni:
                print("💡 === RACCOMANDAZIONI ===")
                for i, racc in enumerate(raccomandazioni, 1):
                    print(f"{i}. {racc}")
                print()
            
            return data
            
        else:
            print(f"❌ Errore HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("🔌 Errore: Backend non raggiungibile su localhost:8000")
        print("   Avvia backend con: cd backend && python -m uvicorn api.main:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"💥 Errore inaspettato: {str(e)}")
        return None

def test_multi_batch_con_diagnosi():
    """Testa generazione multi-batch con diagnosi integrata"""
    print("\n🚀 === TEST MULTI-BATCH CON DIAGNOSI ===")
    print()
    
    # Prima esegui diagnosi
    diagnosi = test_diagnosi_sistema()
    if not diagnosi:
        print("❌ Impossibile eseguire diagnosi - saltando test multi-batch")
        return
    
    if not diagnosi.get('sistema_pronto_multi_batch'):
        print("⚠️ Sistema non pronto per multi-batch secondo diagnosi")
        print("Problemi identificati:")
        for problema in diagnosi.get('problemi_identificati', []):
            print(f"  - {problema['problema']}")
        print()
        print("🤔 Procedo comunque con il test per vedere cosa succede...")
        print()
    
    # Scegli ODL per il test basandoti sulla diagnosi
    odl_disponibili = min(diagnosi.get('odl_attesa_cura', 0), 5)  # Max 5 ODL per test
    if odl_disponibili < 2:
        print(f"❌ Troppo pochi ODL disponibili ({odl_disponibili}) per test significativo")
        return
    
    # Genera una lista di ODL da testare (usa i primi N disponibili)
    test_odl_ids = [str(i) for i in range(5, 5 + odl_disponibili)]  # ODL 5, 6, 7, etc.
    
    print(f"📋 Test con {len(test_odl_ids)} ODL: {test_odl_ids}")
    print()
    
    try:
        # Test generazione multi-batch
        payload = {
            "odl_ids": test_odl_ids,
            "parametri": {
                "padding_mm": 1,
                "min_distance_mm": 1
            }
        }
        
        print("⏳ Avvio generazione multi-batch...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8000/api/batch_nesting/genera-multi',
            json=payload,
            timeout=60
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⚡ Risposta ricevuta in {duration:.2f}s")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ === RISULTATO MULTI-BATCH ===")
            print(f"🎯 Success: {data.get('success')}")
            print(f"📝 Message: {data.get('message')}")
            print(f"🏭 Total autoclavi: {data.get('total_autoclavi')}")
            print(f"✅ Success count: {data.get('success_count')}")
            print(f"❌ Error count: {data.get('error_count')}")
            print(f"🚀 Is real multi-batch: {data.get('is_real_multi_batch')}")
            print(f"🎯 Unique autoclavi count: {data.get('unique_autoclavi_count')}")
            print()
            
            # Analisi dettagliata risultati
            batch_results = data.get('batch_results', [])
            if batch_results:
                print("📊 === DETTAGLI BATCH GENERATI ===")
                for i, batch in enumerate(batch_results, 1):
                    success_icon = "✅" if batch.get('success') else "❌"
                    autoclave_nome = batch.get('autoclave_nome', 'N/A')
                    efficiency = batch.get('efficiency', 0)
                    batch_id = batch.get('batch_id', 'N/A')
                    message = batch.get('message', 'N/A')
                    
                    print(f"{success_icon} {i}. {autoclave_nome}")
                    print(f"   Efficienza: {efficiency:.1f}%")
                    print(f"   Batch ID: {batch_id[:8] if batch_id != 'N/A' else 'N/A'}...")
                    print(f"   Messaggio: {message}")
                    print()
            
            # Verifica coerenza con diagnosi
            print("🔍 === VERIFICA COERENZA ===")
            predicted_ready = diagnosi.get('sistema_pronto_multi_batch')
            actual_multi_batch = data.get('is_real_multi_batch')
            
            if predicted_ready and actual_multi_batch:
                print("✅ COERENZA OK: Diagnosi prevedeva successo e multi-batch generato")
            elif not predicted_ready and not actual_multi_batch:
                print("✅ COERENZA OK: Diagnosi prevedeva problemi e multi-batch fallito")
            elif predicted_ready and not actual_multi_batch:
                print("❌ INCONSISTENZA: Diagnosi ok ma multi-batch fallito - problema nascosto!")
            else:
                print("🤔 ANOMALIA: Diagnosi negativa ma multi-batch riuscito - falso positivo?")
            
        else:
            print(f"❌ Errore HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: Il backend non ha risposto entro 60 secondi")
    except Exception as e:
        print(f"💥 Errore durante test multi-batch: {str(e)}")

def main():
    """Funzione principale di test"""
    print("🔍 === TEST DIAGNOSI PROFONDA MULTI-BATCH v3.0 ===")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Diagnosi sistema
    test_diagnosi_sistema()
    
    # Test 2: Multi-batch con diagnosi
    test_multi_batch_con_diagnosi()
    
    print("🏁 === TEST COMPLETATO ===")
    print("Controlla i log del backend per dettagli aggiuntivi sulla diagnosi.")

if __name__ == "__main__":
    main() 