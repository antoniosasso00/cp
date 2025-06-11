#!/usr/bin/env python3
"""
Test del nuovo flusso semplificato batch
DRAFT → SOSPESO → IN_CURA → TERMINATO
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_batch_workflow():
    """Test completo del workflow batch"""
    
    print("🧪 TEST NUOVO FLUSSO BATCH SEMPLIFICATO")
    print("=" * 60)
    
    # Step 1: Genera un nuovo batch (dovrebbe essere in stato DRAFT)
    print("1️⃣ Generazione nuovo batch...")
    
    generate_data = {
        "odl_ids": [5, 6],
        "autoclave_id": "PANINI",
        "parameters": {
            "padding_mm": 10.0,
            "min_distance_mm": 50.0
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/batch_nesting/genera", 
                               json=generate_data, timeout=30)
        if response.status_code == 200:
            batch_data = response.json()
            batch_id = batch_data['id']
            print(f"   ✅ Batch generato: {batch_id}")
            print(f"   📊 Stato iniziale: {batch_data.get('stato', 'N/A')}")
        else:
            print(f"   ❌ Errore generazione: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    # Step 2: Conferma batch (DRAFT → SOSPESO)
    print("\n2️⃣ Conferma batch (DRAFT → SOSPESO)...")
    
    try:
        response = requests.patch(
            f"{BASE_URL}/api/batch_nesting/{batch_id}/confirm",
            params={
                "confermato_da_utente": "TEST_USER",
                "confermato_da_ruolo": "ADMIN"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            print(f"   ✅ Batch confermato")
            print(f"   📊 Nuovo stato: {batch_data.get('stato', 'N/A')}")
            print(f"   👤 Confermato da: {batch_data.get('confermato_da_utente', 'N/A')}")
        else:
            print(f"   ❌ Errore conferma: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    # Step 3: Inizia cura (SOSPESO → IN_CURA)
    print("\n3️⃣ Inizio cura (SOSPESO → IN_CURA)...")
    
    try:
        response = requests.patch(
            f"{BASE_URL}/api/batch_nesting/{batch_id}/start-cure",
            params={
                "caricato_da_utente": "AUTOCLAVISTA_01",
                "caricato_da_ruolo": "AUTOCLAVISTA"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            print(f"   ✅ Cura iniziata")
            print(f"   📊 Nuovo stato: {batch_data.get('stato', 'N/A')}")
            print(f"   👤 Caricato da: {batch_data.get('caricato_da_utente', 'N/A')}")
            print(f"   🔥 Inizio cura: {batch_data.get('data_inizio_cura', 'N/A')}")
        else:
            print(f"   ❌ Errore inizio cura: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    # Pausa simbolica per simulare cura
    print("\n⏱️ Simulazione cura in corso... (2 secondi)")
    time.sleep(2)
    
    # Step 4: Termina cura (IN_CURA → TERMINATO)
    print("\n4️⃣ Terminazione cura (IN_CURA → TERMINATO)...")
    
    try:
        response = requests.patch(
            f"{BASE_URL}/api/batch_nesting/{batch_id}/terminate",
            params={
                "terminato_da_utente": "AUTOCLAVISTA_01",
                "terminato_da_ruolo": "AUTOCLAVISTA"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            print(f"   ✅ Cura terminata")
            print(f"   📊 Stato finale: {batch_data.get('stato', 'N/A')}")
            print(f"   👤 Terminato da: {batch_data.get('terminato_da_utente', 'N/A')}")
            print(f"   🏁 Fine cura: {batch_data.get('data_fine_cura', 'N/A')}")
            print(f"   ⏰ Durata: {batch_data.get('durata_cura_effettiva_minuti', 'N/A')} minuti")
        else:
            print(f"   ❌ Errore terminazione: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    # Step 5: Verifica stato finale
    print("\n5️⃣ Verifica stato finale...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/batch_nesting/{batch_id}", timeout=10)
        if response.status_code == 200:
            batch_data = response.json()
            print(f"   📊 Stato: {batch_data.get('stato', 'N/A')}")
            print(f"   ✅ Workflow completato con successo!")
        else:
            print(f"   ❌ Errore verifica: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TEST WORKFLOW COMPLETATO")
    print("✅ Flusso semplificato funzionante:")
    print("   DRAFT → SOSPESO → IN_CURA → TERMINATO")
    print("=" * 60)
    
    return True

def test_backend_health():
    """Verifica che il backend sia attivo"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🏥 Controllo salute backend...")
    if not test_backend_health():
        print("❌ Backend non disponibile su localhost:8000")
        print("   Avviare prima: python -m uvicorn main:app --port 8000 --reload")
        exit(1)
    
    print("✅ Backend attivo\n")
    
    # Esegui test completo
    success = test_batch_workflow()
    exit(0 if success else 1) 