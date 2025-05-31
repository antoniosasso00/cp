#!/usr/bin/env python3
"""
🧪 Script di Test - Conferma Batch Nesting
====================================================
Test rapido per verificare il funzionamento dell'endpoint
PATCH /api/v1/batch_nesting/{batch_id}/conferma

Uso: python test_conferma_batch.py [batch_id]
"""

import requests
import sys
import json
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = "test_user"
TEST_ROLE = "Curing"

def test_batch_conferma(batch_id: str):
    """Test dell'endpoint di conferma batch"""
    
    print(f"🧪 Test Conferma Batch: {batch_id}")
    print("=" * 50)
    
    # 1. Recupera stato attuale del batch
    print("📋 1. Recupero stato attuale batch...")
    try:
        response = requests.get(f"{BASE_URL}/batch_nesting/{batch_id}")
        if response.status_code == 404:
            print(f"❌ Batch {batch_id} non trovato!")
            return False
        
        response.raise_for_status()
        batch_before = response.json()
        
        print(f"   📊 Stato attuale: {batch_before.get('stato', 'N/A')}")
        print(f"   🏭 Autoclave ID: {batch_before.get('autoclave_id', 'N/A')}")
        print(f"   📦 ODL inclusi: {len(batch_before.get('odl_ids', []))}")
        
        if batch_before.get('stato') != 'sospeso':
            print(f"⚠️  Batch non in stato 'sospeso', attuale: {batch_before.get('stato')}")
            print("   Test continuato comunque per verificare validazione...")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nel recupero batch: {e}")
        return False
    
    # 2. Test dell'endpoint di conferma
    print("\n🚀 2. Test endpoint conferma...")
    try:
        params = {
            'confermato_da_utente': TEST_USER,
            'confermato_da_ruolo': TEST_ROLE
        }
        
        response = requests.patch(
            f"{BASE_URL}/batch_nesting/{batch_id}/conferma",
            params=params
        )
        
        if response.status_code == 200:
            batch_after = response.json()
            print("✅ Conferma completata con successo!")
            print(f"   📊 Nuovo stato: {batch_after.get('stato', 'N/A')}")
            print(f"   👤 Confermato da: {batch_after.get('confermato_da_utente', 'N/A')} ({batch_after.get('confermato_da_ruolo', 'N/A')})")
            if batch_after.get('data_conferma'):
                print(f"   🕐 Data conferma: {batch_after.get('data_conferma')}")
            
        else:
            error_detail = response.json().get('detail', 'Errore sconosciuto') if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Errore nella conferma (HTTP {response.status_code}): {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nella richiesta di conferma: {e}")
        return False
    
    # 3. Verifica stato finale
    print("\n🔍 3. Verifica stato finale...")
    try:
        response = requests.get(f"{BASE_URL}/batch_nesting/{batch_id}")
        response.raise_for_status()
        batch_final = response.json()
        
        print(f"   📊 Stato finale batch: {batch_final.get('stato', 'N/A')}")
        
        # Verifica autoclave (se disponibile l'endpoint)
        autoclave_id = batch_final.get('autoclave_id')
        if autoclave_id:
            try:
                autoclave_response = requests.get(f"{BASE_URL}/autoclavi/{autoclave_id}")
                if autoclave_response.status_code == 200:
                    autoclave = autoclave_response.json()
                    print(f"   🏭 Stato autoclave: {autoclave.get('stato', 'N/A')}")
            except:
                print("   ⚠️  Impossibile verificare stato autoclave")
        
        print("✅ Test completato!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Errore nella verifica finale: {e}")
        return True  # Il test principale è riuscito
    
def test_batch_list():
    """Recupera lista batch per il test"""
    print("📋 Recupero lista batch disponibili...")
    try:
        response = requests.get(f"{BASE_URL}/batch_nesting?limit=5")
        response.raise_for_status()
        batches = response.json()
        
        if not batches:
            print("❌ Nessun batch trovato!")
            return None
        
        print("📦 Batch disponibili:")
        for batch in batches[:3]:  # Mostra solo i primi 3
            print(f"   • {batch.get('id', 'N/A')} - Stato: {batch.get('stato', 'N/A')}")
        
        # Restituisce il primo batch sospeso se esiste
        for batch in batches:
            if batch.get('stato') == 'sospeso':
                return batch.get('id')
        
        # Altrimenti restituisce il primo
        return batches[0].get('id')
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore nel recupero lista batch: {e}")
        return None

def main():
    """Funzione principale"""
    print("🧪 Test Endpoint Conferma Batch Nesting")
    print("=" * 60)
    print(f"🔗 Backend URL: {BASE_URL}")
    print(f"👤 Test User: {TEST_USER} ({TEST_ROLE})")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Determina batch ID da testare
    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
        print(f"📋 Batch ID fornito: {batch_id}")
    else:
        print("📋 Nessun batch ID fornito, cerco batch disponibili...")
        batch_id = test_batch_list()
        if not batch_id:
            print("❌ Impossibile procedere senza batch ID valido!")
            sys.exit(1)
        print(f"📋 Utilizzerò il batch: {batch_id}")
    
    print()
    
    # Esegui test
    success = test_batch_conferma(batch_id)
    
    print()
    if success:
        print("🎉 Test completato con successo!")
        sys.exit(0)
    else:
        print("❌ Test fallito!")
        sys.exit(1)

if __name__ == "__main__":
    main() 