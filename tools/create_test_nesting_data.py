#!/usr/bin/env python3
"""
Script per creare dati di test per il sistema nesting
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_test_data():
    """Crea dati di test per il sistema nesting"""
    
    print("🔧 Creazione dati di test per il sistema nesting...")
    
    # 1. Crea un'autoclave di test
    print("\n1. Creazione autoclave di test...")
    autoclave_data = {
        "nome": "Autoclave Test 1",
        "codice": "AC-TEST-001",
        "lunghezza": 2000,
        "larghezza_piano": 1000,
        "num_linee_vuoto": 8,
        "stato": "DISPONIBILE",
        "temperatura_max": 180,
        "pressione_max": 8,
        "produttore": "Test Manufacturer",
        "anno_produzione": 2023,
        "note": "Autoclave per test del sistema nesting"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/autoclavi/", json=autoclave_data)
        if response.status_code == 201:
            autoclave = response.json()
            print(f"✅ Autoclave creata: {autoclave['nome']} (ID: {autoclave['id']})")
        else:
            print(f"❌ Errore creazione autoclave: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return
    
    # 2. Crea un ciclo di cura di test
    print("\n2. Creazione ciclo di cura di test...")
    ciclo_data = {
        "nome": "Ciclo Test Standard",
        "temperatura_stasi1": 120,
        "pressione_stasi1": 6,
        "durata_stasi1": 60,
        "attiva_stasi2": True,
        "temperatura_stasi2": 140,
        "pressione_stasi2": 8,
        "durata_stasi2": 30
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cicli-cura/", json=ciclo_data)
        if response.status_code == 201:
            ciclo = response.json()
            print(f"✅ Ciclo di cura creato: {ciclo['nome']} (ID: {ciclo['id']})")
        else:
            print(f"❌ Errore creazione ciclo: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return
    
    print(f"\n🎉 Dati di base creati con successo!")
    print(f"📊 Riepilogo:")
    print(f"   - 1 Autoclave: {autoclave['nome']}")
    print(f"   - 1 Ciclo di cura: {ciclo['nome']}")
    print(f"\n🔗 Ora puoi testare il nesting su: http://localhost:3000/dashboard/curing/nesting")

if __name__ == "__main__":
    create_test_data() 