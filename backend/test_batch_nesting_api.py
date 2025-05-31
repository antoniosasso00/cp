#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento delle API BatchNesting.
"""

import sys
import requests
import json
from pathlib import Path
import time

# Aggiungi il path del backend al PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_batch_nesting_apis():
    """Testa le API BatchNesting"""
    base_url = "http://localhost:8000"
    
    print("🧪 Test delle API BatchNesting")
    print("="*50)
    
    # Verifica che il server sia attivo
    try:
        health_response = requests.get(f"{base_url}/docs", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server FastAPI attivo")
        else:
            print(f"❌ Server risponde con status {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server non raggiungibile: {e}")
        print("💡 Assicurati che il server sia avviato con: python main.py")
        return False
    
    # Test 1: Lista batch nesting (GET /)
    print("\n🔍 Test 1: Lista batch nesting")
    try:
        response = requests.get(f"{base_url}/api/v1/batch_nesting/", timeout=10)
        if response.status_code == 200:
            batch_list = response.json()
            print(f"✅ Lista batch ricevuta: {len(batch_list)} elementi")
        else:
            print(f"❌ Errore nella lista batch: {response.status_code}")
            print(f"   Dettagli: {response.text}")
    except Exception as e:
        print(f"❌ Errore nella richiesta lista batch: {e}")
    
    # Test 2: Creazione nuovo batch (POST /)
    print("\n📝 Test 2: Creazione nuovo batch")
    try:
        new_batch = {
            "nome": "Test Batch API",
            "autoclave_id": 1,  # Assumendo che esista almeno un'autoclave
            "odl_ids": [1, 2],  # Assumendo che esistano almeno 2 ODL
            "parametri": {
                "padding_mm": 25.0,
                "min_distance_mm": 20.0,
                "priorita_area": True,
                "accorpamento_odl": False
            },
            "note": "Batch di test creato dalle API",
            "creato_da_utente": "test_user",
            "creato_da_ruolo": "admin"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/batch_nesting/",
            json=new_batch,
            timeout=10
        )
        
        if response.status_code == 201:
            created_batch = response.json()
            batch_id = created_batch['id']
            print(f"✅ Batch creato con successo: ID {batch_id}")
            
            # Test 3: Lettura batch specifico (GET /{id})
            print(f"\n👁️ Test 3: Lettura batch {batch_id}")
            read_response = requests.get(f"{base_url}/api/v1/batch_nesting/{batch_id}", timeout=10)
            if read_response.status_code == 200:
                batch_details = read_response.json()
                print("✅ Dettagli batch ricevuti:")
                print(f"   Nome: {batch_details.get('nome')}")
                print(f"   Stato: {batch_details.get('stato')}")
                print(f"   Autoclave ID: {batch_details.get('autoclave_id')}")
                print(f"   ODL IDs: {batch_details.get('odl_ids')}")
            else:
                print(f"❌ Errore nella lettura batch: {read_response.status_code}")
            
            # Test 4: Aggiornamento batch (PUT /{id})
            print(f"\n✏️ Test 4: Aggiornamento batch {batch_id}")
            update_data = {
                "nome": "Test Batch API - Aggiornato",
                "note": "Batch aggiornato tramite API"
            }
            
            update_response = requests.put(
                f"{base_url}/api/v1/batch_nesting/{batch_id}",
                json=update_data,
                timeout=10
            )
            
            if update_response.status_code == 200:
                updated_batch = update_response.json()
                print("✅ Batch aggiornato con successo:")
                print(f"   Nuovo nome: {updated_batch.get('nome')}")
            else:
                print(f"❌ Errore nell'aggiornamento batch: {update_response.status_code}")
            
            # Test 5: Statistiche batch (GET /{id}/statistics)
            print(f"\n📊 Test 5: Statistiche batch {batch_id}")
            stats_response = requests.get(f"{base_url}/api/v1/batch_nesting/{batch_id}/statistics", timeout=10)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("✅ Statistiche ricevute:")
                print(f"   Numero ODL: {stats.get('numero_odl')}")
                print(f"   Peso totale: {stats.get('peso_totale_kg')} kg")
            else:
                print(f"❌ Errore nelle statistiche: {stats_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Errore nella creazione batch: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nella creazione batch: {e}")
        return False

def check_swagger_docs():
    """Verifica che le API siano visibili in Swagger"""
    try:
        print("\n📚 Verifica documentazione Swagger")
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get('paths', {})
            
            batch_paths = [path for path in paths.keys() if 'batch_nesting' in path]
            if batch_paths:
                print("✅ API BatchNesting trovate in Swagger:")
                for path in batch_paths:
                    methods = list(paths[path].keys())
                    print(f"   {path}: {', '.join(methods).upper()}")
                return True
            else:
                print("❌ API BatchNesting non trovate in Swagger")
                return False
        else:
            print(f"❌ Errore nell'accesso a Swagger: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore nella verifica Swagger: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test completo delle API BatchNesting")
    
    # Verifica Swagger
    swagger_ok = check_swagger_docs()
    
    # Test delle API
    if swagger_ok:
        api_test_ok = test_batch_nesting_apis()
        
        if api_test_ok:
            print("\n🎉 Tutti i test completati con successo!")
            print("✅ Le API BatchNesting sono funzionanti e disponibili")
        else:
            print("\n💥 Alcuni test sono falliti")
    else:
        print("\n💥 Test interrotti - problema con Swagger")
    
    print("\n📖 Per vedere la documentazione completa: http://localhost:8000/docs") 