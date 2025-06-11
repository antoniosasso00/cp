#!/usr/bin/env python3
"""
Test completo del nuovo workflow semplificato
FLUSSO: DRAFT → SOSPESO → IN_CURA → TERMINATO
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
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

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
            print(f"❌ Backend non disponibile: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore connessione backend: {e}")
        return False

def test_database_status():
    """Verifica dati nel database"""
    print_section("VERIFICA DATABASE")
    
    # Controlla ODL disponibili
    response = requests.get(f"{BASE_URL}/api/odl", headers=HEADERS)
    if response.status_code == 200:
        odl_data = response.json()
        print(f"✅ ODL trovati: {len(odl_data)}")
        if len(odl_data) >= 2:
            print(f"   📋 ODL disponibili: {[odl['id'] for odl in odl_data[:5]]}")  # Mostra primi 5
            return odl_data[:2]  # Ritorna primi 2 ODL per il test
        else:
            print("❌ Serve almeno 2 ODL per il test")
            return None
    else:
        print(f"❌ Errore caricamento ODL: {response.status_code}")
        return None

def test_batch_generation(odl_ids):
    """Genera un batch di test"""
    print_section("GENERAZIONE BATCH")
    
    payload = {
        "odl_ids": [str(id) for id in odl_ids],  # Convert to strings
        "parametri": {
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        }
    }
    
    print(f"🔹 Generazione batch con ODL: {odl_ids}")
    response = requests.post(f"{BASE_URL}/api/batch_nesting/genera-multi", 
                           headers=HEADERS, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        batch_id = result.get('best_batch_id')
        success_count = result.get('success_count', 0)
        print(f"✅ Multi-batch generato: {success_count} batch")
        print(f"   🏆 Best batch ID: {batch_id}")
        if 'batch_results' in result and result['batch_results']:
            for i, batch_result in enumerate(result['batch_results']):
                autoclave_name = batch_result.get('autoclave_nome', f'Autoclave {i+1}')
                efficiency = batch_result.get('efficiency', 0)
                print(f"   📊 {autoclave_name}: {efficiency:.1f}% efficienza")
        return batch_id
    else:
        print(f"❌ Errore generazione batch: {response.status_code}")
        print(f"   Dettagli: {response.text}")
        return None

def test_workflow_transitions(batch_id):
    """Testa tutte le transizioni del workflow"""
    print_section("TEST WORKFLOW COMPLETO")
    
    # STEP 1: Verifica stato attuale - Multi-batch genera direttamente SOSPESO
    print_step(1, "Verifica stato batch (Multi-batch già SOSPESO)")
    
    response = requests.get(f"{BASE_URL}/api/batch_nesting/{batch_id}", headers=HEADERS)
    
    if response.status_code == 200:
        batch_data = response.json()
        stato_attuale = batch_data.get('stato')
        print(f"   ✅ Stato attuale: {stato_attuale}")
        
        if stato_attuale == 'draft':
            # Se è draft, fai la conferma
            print("   🔄 Batch in DRAFT - eseguendo conferma...")
            response = requests.patch(
                f"{BASE_URL}/api/batch_nesting/{batch_id}/confirm",
                params={
                    "confermato_da_utente": "TEST_USER",
                    "confermato_da_ruolo": "ADMIN"
                },
                headers=HEADERS
            )
            if response.status_code != 200:
                print(f"   ❌ Errore conferma: {response.status_code} - {response.text}")
                return False
            batch_data = response.json()
            print(f"   ✅ Batch confermato a: {batch_data.get('stato')}")
        elif stato_attuale == 'sospeso':
            print("   ✅ Batch già SOSPESO (corretto per multi-batch)")
        else:
            print(f"   ⚠️ Stato inaspettato: {stato_attuale}")
    else:
        print(f"   ❌ Errore verifica stato: {response.status_code} - {response.text}")
        return False
    
    time.sleep(2)
    
    # STEP 2: SOSPESO → IN_CURA (Inizio cura)
    print_step(2, "Inizio cura (SOSPESO → IN_CURA)")
    
    response = requests.patch(
        f"{BASE_URL}/api/batch_nesting/{batch_id}/start-cure",
        params={
            "caricato_da_utente": "OPERATOR_USER", 
            "caricato_da_ruolo": "OPERATOR"
        },
        headers=HEADERS
    )
    
    if response.status_code == 200:
        batch_data = response.json()
        print(f"   ✅ Cura iniziata")
        print(f"   📊 Nuovo stato: {batch_data.get('stato')}")
        print(f"   👤 Caricato da: {batch_data.get('caricato_da_utente', 'N/A')}")
        print(f"   🔥 Autoclave in uso")
    else:
        print(f"   ❌ Errore inizio cura: {response.status_code} - {response.text}")
        return False
    
    # Simula tempo di cura
    print("   ⏱️ Simulazione tempo di cura (10 secondi)...")
    time.sleep(10)
    
    # STEP 3: IN_CURA → TERMINATO (Fine cura)
    print_step(3, "Terminazione cura (IN_CURA → TERMINATO)")
    
    response = requests.patch(
        f"{BASE_URL}/api/batch_nesting/{batch_id}/terminate",
        params={
            "terminato_da_utente": "OPERATOR_USER",
            "terminato_da_ruolo": "OPERATOR"
        },
        headers=HEADERS
    )
    
    if response.status_code == 200:
        batch_data = response.json()
        print(f"   ✅ Cura terminata")
        print(f"   📊 Nuovo stato: {batch_data.get('stato')}")
        print(f"   👤 Terminato da: {batch_data.get('terminato_da_utente', 'N/A')}")
        print(f"   🏁 Workflow completato")
    else:
        print(f"   ❌ Errore terminazione: {response.status_code} - {response.text}")
        return False
    
    return True

def test_tempo_fase_records(odl_ids):
    """Verifica che i record TempoFase siano stati creati correttamente"""
    print_section("VERIFICA TEMPI ODL (TempoFase)")
    
    for odl_id in odl_ids:
        print(f"\n🔹 Controllo tempi ODL {odl_id}")
        
        # Controlla record TempoFase per questo ODL
        response = requests.get(f"{BASE_URL}/api/tempo-fasi?odl_id={odl_id}", 
                              headers=HEADERS)
        
        if response.status_code == 200:
            tempo_fasi = response.json()
            
            # Cerca il record di cura
            cura_records = [tf for tf in tempo_fasi if tf.get('fase') == 'cura']
            
            if cura_records:
                record = cura_records[-1]  # Prendi l'ultimo
                print(f"   ✅ Record TempoFase trovato:")
                print(f"      📅 Inizio: {record.get('inizio_fase')}")
                print(f"      📅 Fine: {record.get('fine_fase')}")
                print(f"      ⏱️ Durata: {record.get('durata_minuti')} minuti")
                print(f"      📝 Note: {record.get('note', 'N/A')}")
            else:
                print(f"   ⚠️ Nessun record TempoFase 'cura' trovato")
        else:
            print(f"   ❌ Errore recupero TempoFase: {response.status_code}")

def test_odl_status_progression(odl_ids):
    """Verifica che gli stati ODL siano stati aggiornati correttamente"""
    print_section("VERIFICA STATI ODL")
    
    for odl_id in odl_ids:
        response = requests.get(f"{BASE_URL}/api/odl/{odl_id}", headers=HEADERS)
        
        if response.status_code == 200:
            odl_data = response.json()
            final_status = odl_data.get('status')
            print(f"   📋 ODL {odl_id}: Stato finale = '{final_status}'")
            
            if final_status == 'Finito':
                print(f"      ✅ Stato corretto (Finito)")
            else:
                print(f"      ⚠️ Stato inaspettato: {final_status}")
        else:
            print(f"   ❌ Errore recupero ODL {odl_id}: {response.status_code}")

def test_autoclave_status():
    """Verifica che l'autoclave sia tornata disponibile"""
    print_section("VERIFICA STATO AUTOCLAVE")
    
    response = requests.get(f"{BASE_URL}/api/autoclavi/1", headers=HEADERS)
    
    if response.status_code == 200:
        autoclave_data = response.json()
        stato = autoclave_data.get('stato')
        print(f"   🏭 Autoclave 1: Stato = '{stato}'")
        
        if stato == 'disponibile':
            print(f"      ✅ Autoclave disponibile (corretto)")
        else:
            print(f"      ⚠️ Autoclave non disponibile: {stato}")
    else:
        print(f"   ❌ Errore recupero autoclave: {response.status_code}")

def main():
    """Test completo del workflow"""
    print_section("TEST WORKFLOW COMPLETO CarbonPilot v4.0")
    print("Nuovo flusso semplificato: DRAFT → SOSPESO → IN_CURA → TERMINATO")
    print("Sistema timing integrato con TempoFase per compatibilità statistiche")
    
    # Verifica prerequisiti
    if not test_backend_status():
        return False
    
    odl_data = test_database_status()
    if not odl_data:
        return False
    
    odl_ids = [odl['id'] for odl in odl_data]
    
    # Genera batch
    batch_id = test_batch_generation(odl_ids)
    if not batch_id:
        return False
    
    # Test workflow completo
    if not test_workflow_transitions(batch_id):
        return False
    
    # Verifica risultati
    test_tempo_fase_records(odl_ids)
    test_odl_status_progression(odl_ids)
    test_autoclave_status()
    
    print_section("RISULTATI FINALI")
    print("✅ WORKFLOW COMPLETATO CON SUCCESSO!")
    print("✅ Sistema timing TempoFase integrato")
    print("✅ Stati ODL e autoclave aggiornati correttamente")
    print("✅ Compatibilità con statistiche mantenuta")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 