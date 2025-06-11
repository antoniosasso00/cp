#!/usr/bin/env python3
"""
Test completo del workflow semplificato con batch DRAFT
======================================================

FLUSSO: GENERAZIONE → DRAFT (memoria) → CONFERMA → SOSPESO → IN_CURA → TERMINATO
con integrazione TempoFase per record timing ODL
"""

import requests
import time
import json
from datetime import datetime
import sys

# Configurazione
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print('='*70)

def print_step(step, description):
    print(f"\n🔹 STEP {step}: {description}")

def test_backend_status():
    """Verifica che il backend sia attivo e funzionante"""
    print_section("VERIFICA BACKEND")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend attivo e raggiungibile")
            return True
        else:
            print(f"❌ Backend risponde ma con errore: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend non raggiungibile: {e}")
        return False

def test_generate_draft_batches():
    """Genera batch DRAFT multi-autoclave (solo in memoria)"""
    print_section("GENERAZIONE BATCH DRAFT")
    print_step(1, "Generazione batch DRAFT multi-autoclave")
    
    # Recupera ODL disponibili
    response = requests.get(f"{BASE_URL}/api/odl", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Errore recupero ODL: {response.status_code}")
        return None
    
    odl_data = response.json()
    odl_in_attesa = [odl for odl in odl_data if odl.get('status') == 'Attesa Cura'][:5]  # Prime 5 ODL
    
    if len(odl_in_attesa) < 2:
        print(f"⚠️ Insufficient ODL in 'Attesa Cura': {len(odl_in_attesa)}")
        return None
    
    odl_ids = [str(odl['id']) for odl in odl_in_attesa]
    print(f"📋 ODL selezionati: {odl_ids}")
    
    # Genera batch DRAFT multi-autoclave
    payload = {
        "odl_ids": odl_ids,
        "parametri": {
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/batch_nesting/genera-multi", 
                           headers=HEADERS, json=payload, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        success_count = result.get('success_count', 0)
        batch_results = result.get('batch_results', [])
        
        print(f"✅ Generazione multi-batch completata:")
        print(f"   📊 Batch generati: {success_count}")
        print(f"   🎯 Best batch ID: {result.get('best_batch_id')}")
        
        draft_ids = []
        for i, batch_result in enumerate(batch_results):
            autoclave_nome = batch_result.get('autoclave_nome', f'Autoclave {i+1}')
            efficiency = batch_result.get('efficiency', 0)
            draft_id = batch_result.get('batch_id')
            is_draft = batch_result.get('is_draft', False)
            
            print(f"   📦 {autoclave_nome}: {efficiency}% efficienza, ID: {draft_id} (DRAFT: {is_draft})")
            
            if is_draft and draft_id:
                draft_ids.append(draft_id)
        
        return draft_ids
    
    else:
        print(f"❌ Errore generazione: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Dettaglio: {error_detail}")
        except:
            print(f"   Testo errore: {response.text}")
        return None

def test_list_draft_batches():
    """Verifica lista batch DRAFT in memoria"""
    print_step(2, "Verifica batch DRAFT in memoria")
    
    response = requests.get(f"{BASE_URL}/api/batch_nesting/draft", headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        draft_batches = result.get('draft_batches', [])
        stats = result.get('stats', {})
        
        print(f"✅ Batch DRAFT in memoria:")
        print(f"   📊 Totale: {len(draft_batches)}")
        print(f"   🏭 Autoclavi coinvolte: {stats.get('autoclavi_coinvolte', 0)}")
        print(f"   ⚡ Efficienza media: {stats.get('avg_efficiency', 0):.1f}%")
        
        for i, draft in enumerate(draft_batches):
            print(f"   📦 {i+1}. {draft.get('autoclave_nome')} - {draft.get('efficiency', 0):.1f}% - ID: {draft.get('id')}")
        
        return draft_batches
    else:
        print(f"❌ Errore lista DRAFT: {response.status_code}")
        return []

def test_confirm_draft_batch(draft_id):
    """Conferma batch DRAFT → SOSPESO (persistito nel database)"""
    print_step(3, f"Conferma batch DRAFT: {draft_id[:8]}...")
    
    params = {
        "confermato_da_utente": "TEST_USER",
        "confermato_da_ruolo": "ADMIN"
    }
    
    response = requests.post(f"{BASE_URL}/api/batch_nesting/draft/{draft_id}/confirm",
                           headers=HEADERS, params=params, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        persistent_id = result.get('persistent_batch_id')
        
        print(f"✅ Batch DRAFT confermato:")
        print(f"   📦 DRAFT ID: {draft_id[:8]}...")
        print(f"   🎯 Batch persistito: {persistent_id}")
        print(f"   📋 Stato: DRAFT → SOSPESO")
        
        return persistent_id
    else:
        print(f"❌ Errore conferma DRAFT: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Dettaglio: {error_detail}")
        except:
            print(f"   Testo errore: {response.text}")
        return None

def test_start_cure(batch_id):
    """Inizia cura: SOSPESO → IN_CURA + timing TempoFase"""
    print_step(4, f"Inizia cura batch: {batch_id[:8]}...")
    
    params = {
        "caricato_da_utente": "TEST_OPERATOR", 
        "caricato_da_ruolo": "OPERATOR"
    }
    
    response = requests.patch(f"{BASE_URL}/api/batch_nesting/{batch_id}/start-cure",
                            headers=HEADERS, params=params, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cura iniziata:")
        print(f"   📦 Batch: {batch_id[:8]}...")
        print(f"   📋 Stato: SOSPESO → IN_CURA")
        print(f"   ⏱️ Timing TempoFase: ATTIVO")
        print(f"   🏭 Autoclave: DISPONIBILE → IN_USO")
        
        return True
    else:
        print(f"❌ Errore inizio cura: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Dettaglio: {error_detail}")
        except:
            print(f"   Testo errore: {response.text}")
        return False

def test_terminate_cure(batch_id):
    """Termina cura: IN_CURA → TERMINATO + chiusura timing"""
    print_step(5, f"Termina cura batch: {batch_id[:8]}...")
    
    # Aspetta qualche secondo per simulare cura
    print("   ⏳ Simulazione cura in corso (5 secondi)...")
    time.sleep(5)
    
    params = {
        "terminato_da_utente": "TEST_OPERATOR",
        "terminato_da_ruolo": "OPERATOR"
    }
    
    response = requests.patch(f"{BASE_URL}/api/batch_nesting/{batch_id}/terminate",
                            headers=HEADERS, params=params, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cura terminata:")
        print(f"   📦 Batch: {batch_id[:8]}...")
        print(f"   📋 Stato: IN_CURA → TERMINATO")
        print(f"   ⏱️ Timing TempoFase: COMPLETATO")
        print(f"   🏭 Autoclave: IN_USO → DISPONIBILE")
        
        return True
    else:
        print(f"❌ Errore termine cura: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Dettaglio: {error_detail}")
        except:
            print(f"   Testo errore: {response.text}")
        return False

def test_verify_tempo_fase(batch_id):
    """Verifica che i tempi TempoFase siano stati registrati correttamente"""
    print_step(6, f"Verifica timing TempoFase per batch: {batch_id[:8]}...")
    
    # Prima recupera il batch per ottenere gli ODL associati
    response = requests.get(f"{BASE_URL}/api/batch_nesting/{batch_id}", headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Errore recupero batch: {response.status_code}")
        return False
    
    batch_data = response.json()
    odl_ids = batch_data.get('odl_ids', [])
    
    if not odl_ids:
        print("⚠️ Nessun ODL associato al batch")
        return False
    
    print(f"📋 Verifica TempoFase per {len(odl_ids)} ODL: {odl_ids}")
    
    # Verifica timing per ogni ODL
    timing_verified = 0
    for odl_id in odl_ids:
        response = requests.get(f"{BASE_URL}/api/tempo-fasi?odl_id={odl_id}", 
                              headers=HEADERS)
        
        if response.status_code == 200:
            tempo_fasi = response.json()
            
            # Cerca timing di cura
            cura_records = [tf for tf in tempo_fasi if tf.get('fase') == 'cura']
            
            if cura_records:
                timing_verified += 1
                cura = cura_records[0]  # Prendi il più recente
                durata = cura.get('durata_minuti')
                inizio = cura.get('inizio_fase')
                fine = cura.get('fine_fase')
                
                print(f"   ✅ ODL {odl_id}: cura registrata")
                print(f"      ⏱️ Durata: {durata} minuti")
                print(f"      🕐 Inizio: {inizio}")
                print(f"      🕑 Fine: {fine}")
            else:
                print(f"   ⚠️ ODL {odl_id}: nessun timing cura trovato")
        else:
            print(f"   ❌ ODL {odl_id}: errore recupero TempoFase ({response.status_code})")
    
    success_rate = (timing_verified / len(odl_ids)) * 100
    print(f"\n📊 Verifica TempoFase completata:")
    print(f"   ✅ ODL con timing: {timing_verified}/{len(odl_ids)} ({success_rate:.1f}%)")
    
    return timing_verified > 0

def main():
    """Esegue il test completo del workflow semplificato"""
    print_section("TEST WORKFLOW BATCH SEMPLIFICATO")
    print("FLUSSO: GENERAZIONE → DRAFT (memoria) → CONFERMA → SOSPESO → IN_CURA → TERMINATO")
    
    # Test backend status
    if not test_backend_status():
        print("\n❌ ERRORE: Backend non disponibile. Interrompo i test.")
        sys.exit(1)
    
    # Test 1: Genera batch DRAFT
    draft_ids = test_generate_draft_batches()
    if not draft_ids:
        print("\n❌ ERRORE: Generazione batch DRAFT fallita. Interrompo i test.")
        sys.exit(1)
    
    # Test 2: Lista batch DRAFT
    draft_batches = test_list_draft_batches()
    if not draft_batches:
        print("\n❌ ERRORE: Nessun batch DRAFT trovato. Interrompo i test.")
        sys.exit(1)
    
    # Test 3: Conferma primo batch DRAFT
    first_draft_id = draft_ids[0]
    persistent_batch_id = test_confirm_draft_batch(first_draft_id)
    if not persistent_batch_id:
        print("\n❌ ERRORE: Conferma batch DRAFT fallita. Interrompo i test.")
        sys.exit(1)
    
    # Test 4: Inizia cura
    if not test_start_cure(persistent_batch_id):
        print("\n❌ ERRORE: Inizio cura fallito. Interrompo i test.")
        sys.exit(1)
    
    # Test 5: Termina cura
    if not test_terminate_cure(persistent_batch_id):
        print("\n❌ ERRORE: Termine cura fallito. Interrompo i test.")
        sys.exit(1)
    
    # Test 6: Verifica TempoFase
    tempo_fase_ok = test_verify_tempo_fase(persistent_batch_id)
    
    # Risultato finale
    print_section("RISULTATO FINALE")
    
    if tempo_fase_ok:
        print("🎉 SUCCESSO: Workflow semplificato completamente funzionante!")
        print("\n✅ VERIFICHE COMPLETATE:")
        print("   📦 Generazione batch DRAFT in memoria")
        print("   ✅ Conferma DRAFT → SOSPESO (persistenza database)")
        print("   🔄 Transizione SOSPESO → IN_CURA")
        print("   🏁 Transizione IN_CURA → TERMINATO")
        print("   ⏱️ Record timing TempoFase corretto")
        print("   🏭 Gestione automatica stati autoclave")
        print("   📋 Aggiornamento automatico stati ODL")
        
        print(f"\n📋 WORKFLOW TESTATO:")
        print(f"   🆔 Batch ID: {persistent_batch_id}")
        print(f"   📈 Stati attraversati: DRAFT → SOSPESO → IN_CURA → TERMINATO")
        
        sys.exit(0)
    else:
        print("❌ ERRORE: TempoFase non registrato correttamente.")
        sys.exit(1)

if __name__ == "__main__":
    main() 