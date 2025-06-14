#!/usr/bin/env python3
"""
Script di test per verificare il problema con batch result endpoint
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.database import get_db
from models.batch_nesting import BatchNesting
import requests
import time
import json

def test_batch_in_database():
    """Testa se il batch esiste nel database"""
    print("🔍 === TEST DATABASE ===")
    try:
        db = next(get_db())
        batch_id = 'e187ce8d-ed33-4609-a6ab-b03591ab7488'
        batch = db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
        
        if batch:
            print(f"✅ Batch trovato: {batch.nome}")
            print(f"   Efficienza: {batch.efficiency}")
            print(f"   Stato: {batch.stato}")
            print(f"   Autoclave ID: {batch.autoclave_id}")
            print(f"   Peso totale: {batch.peso_totale_kg}")
            print(f"   Numero nesting: {batch.numero_nesting}")
            print(f"   ODL IDs: {batch.odl_ids}")
            print(f"   Configurazione JSON keys: {list(batch.configurazione_json.keys()) if batch.configurazione_json else 'None'}")
            return True
        else:
            print("❌ Batch NON trovato nel database")
            return False
    except Exception as e:
        print(f"❌ Errore database: {e}")
        return False

def test_endpoint():
    """Testa l'endpoint result"""
    print("\n🔍 === TEST ENDPOINT ===")
    try:
        batch_id = 'e187ce8d-ed33-4609-a6ab-b03591ab7488'
        url = f'http://localhost:8000/api/batch_nesting/result/{batch_id}'
        
        print(f"Testing endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Endpoint funziona!")
            print(f"   Batch results: {len(data.get('batch_results', []))}")
            print(f"   Is multi batch: {data.get('is_multi_batch', False)}")
            print(f"   Total batches: {data.get('total_batches', 'N/A')}")
            print(f"   Main batch ID: {data.get('main_batch_id', 'N/A')}")
            
            # 🔍 DEBUG: Analisi batch_results
            batch_results = data.get('batch_results', [])
            if len(batch_results) == 0:
                print("⚠️ WARNING: batch_results è vuoto!")
                print("   Controllare formato_batch_result() per errori")
            else:
                first_batch = batch_results[0]
                print(f"   Primo batch ID: {first_batch.get('id', 'N/A')}")
                print(f"   Primo batch nome: {first_batch.get('nome', 'N/A')}")
                print(f"   Configurazione keys: {list(first_batch.get('configurazione_json', {}).keys())}")
                
        else:
            print(f"❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"❌ Errore endpoint: {e}")

def test_endpoint_simple():
    """Testa l'endpoint /batch_id semplice"""
    print("\n🔍 === TEST ENDPOINT SIMPLE ===")
    try:
        batch_id = 'e187ce8d-ed33-4609-a6ab-b03591ab7488'
        url = f'http://localhost:8000/api/batch_nesting/{batch_id}'
        
        print(f"Testing simple endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Simple endpoint funziona!")
            print(f"   Batch ID: {data.get('id', 'N/A')}")
            print(f"   Batch nome: {data.get('nome', 'N/A')}")
            print(f"   Efficienza: {data.get('efficiency', 'N/A')}")
        else:
            print(f"❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"❌ Errore simple endpoint: {e}")

def wait_for_backend():
    """Aspetta che il backend sia pronto"""
    print("⏳ Aspettando che il backend sia pronto...")
    for i in range(30):  # Max 30 secondi
        try:
            response = requests.get('http://localhost:8000/api/batch_nesting/data', timeout=2)
            if response.status_code == 200:
                print("✅ Backend pronto!")
                return True
        except:
            pass
        print(f"   Tentativo {i+1}/30...")
        time.sleep(1)
    print("❌ Backend non risponde dopo 30 secondi")
    return False

if __name__ == "__main__":
    print("🚀 === TEST BATCH RESULT FIX ===")
    
    # Test database
    db_ok = test_batch_in_database()
    
    # Aspetta backend
    if wait_for_backend():
        # Test endpoints
        test_endpoint_simple()
        test_endpoint()
    
    print(f"\n📊 === RISULTATO ===")
    print(f"Database: {'✅' if db_ok else '❌'}") 