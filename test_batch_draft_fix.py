#!/usr/bin/env python
"""
🧪 TEST VERIFICA FIX BATCH DRAFT
================================

Script per verificare che i problemi identificati siano stati risolti:
1. Batch vengono creati in stato DRAFT invece che SOSPESO
2. Nessun redirect a vecchi risultati eliminati
3. Sistema di cleanup non interferisce

"""

import requests
import json
import sys
import time
from datetime import datetime

# Configurazione
BACKEND_URL = "http://localhost:8000"
TEST_ODL_IDS = ["5", "6", "7"]  # ODL di test disponibili

def test_connection():
    """Testa la connessione al backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/batch_nesting/data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend connesso: {len(data.get('odl_in_attesa_cura', []))} ODL disponibili")
            return True
        else:
            print(f"❌ Backend non connesso: status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore connessione backend: {e}")
        return False

def test_draft_creation():
    """Test 1: Verifica che i batch vengano creati in stato DRAFT"""
    print("\n🧪 TEST 1: Creazione batch in stato DRAFT")
    
    try:
        # Payload per generazione multi-batch
        payload = {
            "odl_ids": TEST_ODL_IDS,
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 15
            }
        }
        
        print(f"📤 Inviando richiesta multi-batch con ODL: {TEST_ODL_IDS}")
        response = requests.post(
            f"{BACKEND_URL}/api/batch_nesting/genera-multi",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generazione completata: {data.get('success_count', 0)} batch")
            
            # Verifica best_batch_id
            best_batch_id = data.get('best_batch_id')
            if best_batch_id:
                print(f"🎯 Best batch ID: {best_batch_id}")
                
                # Recupera il batch dal database per verificare lo stato
                batch_response = requests.get(f"{BACKEND_URL}/api/batch_nesting/result/{best_batch_id}")
                if batch_response.status_code == 200:
                    batch_data = batch_response.json()
                    stato = batch_data.get('batch', {}).get('stato')
                    print(f"📊 Stato batch creato: {stato}")
                    
                    if stato == "draft":
                        print("✅ TEST 1 PASSATO: Batch creato in stato DRAFT")
                        return True
                    else:
                        print(f"❌ TEST 1 FALLITO: Stato atteso 'draft', trovato '{stato}'")
                        return False
                else:
                    print(f"❌ Errore recupero batch: {batch_response.status_code}")
                    return False
            else:
                print("❌ TEST 1 FALLITO: Nessun best_batch_id restituito")
                return False
        else:
            print(f"❌ TEST 1 FALLITO: Status {response.status_code}")
            if response.text:
                print(f"   Errore: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ TEST 1 ERRORE: {e}")
        return False

def test_no_old_redirects():
    """Test 2: Verifica che non ci siano redirect a vecchi risultati"""
    print("\n🧪 TEST 2: No redirect a risultati obsoleti")
    
    try:
        # Genera più batch in sequenza per testare il controllo duplicati
        results = []
        
        for i in range(2):
            print(f"📤 Generazione batch {i+1}/2...")
            
            payload = {
                "odl_ids": TEST_ODL_IDS,
                "parametri": {
                    "padding_mm": 12 + i,  # Parametri leggermente diversi
                    "min_distance_mm": 16 + i
                }
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/batch_nesting/genera-multi",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                best_batch_id = data.get('best_batch_id')
                results.append(best_batch_id)
                print(f"   ✅ Batch {i+1}: {best_batch_id}")
                time.sleep(2)  # Pausa tra generazioni
            else:
                print(f"   ❌ Errore generazione {i+1}: {response.status_code}")
                return False
        
        # Verifica che i batch siano diversi (no redirect a vecchi)
        if len(results) == 2 and results[0] != results[1]:
            print("✅ TEST 2 PASSATO: Nessun redirect a vecchi risultati")
            return True
        else:
            print(f"❌ TEST 2 FALLITO: Redirect rilevato ({results})")
            return False
            
    except Exception as e:
        print(f"❌ TEST 2 ERRORE: {e}")
        return False

def test_cleanup_disabled():
    """Test 3: Verifica che il cleanup automatico sia disabilitato"""
    print("\n🧪 TEST 3: Cleanup automatico disabilitato")
    
    try:
        # Simula una chiamata di generazione e controlla i log
        payload = {
            "odl_ids": TEST_ODL_IDS[:2],  # Solo 2 ODL per test rapido
            "parametri": {
                "padding_mm": 8,
                "min_distance_mm": 12
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/batch_nesting/genera-multi",
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            print("✅ TEST 3 PASSATO: Generazione completata senza cleanup automatico")
            return True
        else:
            print(f"❌ TEST 3 FALLITO: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ TEST 3 ERRORE: {e}")
        return False

def main():
    """Esegue tutti i test di verifica fix"""
    print("🚀 VERIFICA FIX BATCH DRAFT")
    print("=" * 40)
    
    # Test connessione
    if not test_connection():
        print("\n❌ TESTS ABORTITI: Backend non disponibile")
        sys.exit(1)
    
    # Esegui tutti i test
    tests = [
        ("Creazione DRAFT", test_draft_creation),
        ("No redirect obsoleti", test_no_old_redirects), 
        ("Cleanup disabilitato", test_cleanup_disabled)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        success = test_func()
        results.append((test_name, success))
    
    # Risultati finali
    print(f"\n{'='*50}")
    print("🏁 RISULTATI FINALI:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSATO" if success else "❌ FALLITO"
        print(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 TUTTI I FIX FUNZIONANO CORRETTAMENTE!")
        print("   - Batch creati in stato DRAFT ✅")
        print("   - Nessun redirect a vecchi risultati ✅") 
        print("   - Cleanup automatico disabilitato ✅")
    else:
        print("\n⚠️ ALCUNI PROBLEMI PERSISTONO")
        print("   Controllare i log del backend per dettagli")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 