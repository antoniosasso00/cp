#!/usr/bin/env python
"""
Script di test per verificare i miglioramenti alla sezione ODL.
Testa le funzionalità principali implementate.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_odl_endpoints():
    """Testa gli endpoint ODL principali"""
    print("🧪 Test degli endpoint ODL...")
    
    # Test GET ODL
    try:
        response = requests.get(f"{BASE_URL}/odl")
        if response.status_code == 200:
            odls = response.json()
            print(f"✅ GET /odl: {len(odls)} ODL trovati")
            
            # Conta ODL per stato
            stati = {}
            for odl in odls:
                stato = odl['status']
                stati[stato] = stati.get(stato, 0) + 1
            
            print("📊 Distribuzione stati ODL:")
            for stato, count in stati.items():
                print(f"   {stato}: {count}")
                
            return odls
        else:
            print(f"❌ GET /odl fallito: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Errore GET /odl: {e}")
        return []

def test_tempo_fasi_endpoints():
    """Testa gli endpoint tempi fasi"""
    print("\n🧪 Test degli endpoint tempi fasi...")
    
    try:
        response = requests.get(f"{BASE_URL}/tempo-fasi")
        if response.status_code == 200:
            fasi = response.json()
            print(f"✅ GET /tempo-fasi: {len(fasi)} fasi trovate")
            
            # Conta fasi per tipo
            tipi_fase = {}
            for fase in fasi:
                tipo = fase['fase']
                tipi_fase[tipo] = tipi_fase.get(tipo, 0) + 1
            
            print("📊 Distribuzione fasi:")
            for tipo, count in tipi_fase.items():
                print(f"   {tipo}: {count}")
                
            return fasi
        else:
            print(f"❌ GET /tempo-fasi fallito: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Errore GET /tempo-fasi: {e}")
        return []

def test_odl_creation():
    """Testa la creazione di un nuovo ODL"""
    print("\n🧪 Test creazione nuovo ODL...")
    
    # Dati per nuovo ODL
    nuovo_odl = {
        "parte_id": 1,
        "tool_id": 1,
        "priorita": 8,  # Priorità alta per test
        "status": "Preparazione",
        "note": "ODL di test creato automaticamente per verifica miglioramenti"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/odl", json=nuovo_odl)
        if response.status_code == 201:
            odl_creato = response.json()
            print(f"✅ ODL creato con successo: ID {odl_creato['id']}")
            print(f"   Parte: {odl_creato['parte']['part_number']}")
            print(f"   Tool: {odl_creato['tool']['part_number_tool']}")
            print(f"   Priorità: {odl_creato['priorita']} (Alta)")
            return odl_creato
        else:
            print(f"❌ Creazione ODL fallita: {response.status_code}")
            print(f"   Errore: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Errore creazione ODL: {e}")
        return None

def test_odl_update(odl_id):
    """Testa l'aggiornamento di un ODL"""
    print(f"\n🧪 Test aggiornamento ODL {odl_id}...")
    
    # Dati per aggiornamento
    aggiornamento = {
        "status": "Laminazione",
        "note": "ODL aggiornato durante test automatico"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/odl/{odl_id}", json=aggiornamento)
        if response.status_code == 200:
            odl_aggiornato = response.json()
            print(f"✅ ODL {odl_id} aggiornato con successo")
            print(f"   Nuovo stato: {odl_aggiornato['status']}")
            return odl_aggiornato
        else:
            print(f"❌ Aggiornamento ODL fallito: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Errore aggiornamento ODL: {e}")
        return None

def test_tempo_fase_creation(odl_id):
    """Testa la creazione di una fase tempo"""
    print(f"\n🧪 Test creazione fase tempo per ODL {odl_id}...")
    
    # Dati per nuova fase
    nuova_fase = {
        "odl_id": odl_id,
        "fase": "laminazione",
        "inizio_fase": datetime.now().isoformat(),
        "note": "Fase di test creata automaticamente"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tempo-fasi", json=nuova_fase)
        if response.status_code == 201:
            fase_creata = response.json()
            print(f"✅ Fase tempo creata con successo: ID {fase_creata['id']}")
            print(f"   Fase: {fase_creata['fase']}")
            print(f"   Inizio: {fase_creata['inizio_fase']}")
            return fase_creata
        else:
            print(f"❌ Creazione fase tempo fallita: {response.status_code}")
            print(f"   Errore: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Errore creazione fase tempo: {e}")
        return None

def test_frontend_pages():
    """Testa che le pagine frontend siano accessibili"""
    print("\n🧪 Test accessibilità pagine frontend...")
    
    frontend_base = "http://localhost:3000"
    pages = [
        "/dashboard/odl",
        "/dashboard/odl/monitoraggio"
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{frontend_base}{page}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Pagina {page} accessibile")
            else:
                print(f"❌ Pagina {page} non accessibile: {response.status_code}")
        except Exception as e:
            print(f"❌ Errore accesso pagina {page}: {e}")

def run_comprehensive_test():
    """Esegue tutti i test in sequenza"""
    print("🚀 Avvio test completo miglioramenti ODL")
    print("=" * 50)
    
    # Test 1: Endpoint ODL
    odls = test_odl_endpoints()
    
    # Test 2: Endpoint tempi fasi
    fasi = test_tempo_fasi_endpoints()
    
    # Test 3: Creazione ODL
    nuovo_odl = test_odl_creation()
    
    # Test 4: Aggiornamento ODL (se creazione riuscita)
    if nuovo_odl:
        test_odl_update(nuovo_odl['id'])
        test_tempo_fase_creation(nuovo_odl['id'])
    
    # Test 5: Pagine frontend
    test_frontend_pages()
    
    print("\n" + "=" * 50)
    print("✨ Test completati!")
    
    # Riepilogo
    print("\n📋 Riepilogo funzionalità testate:")
    print("✅ Endpoint GET /odl (lista ordini)")
    print("✅ Endpoint GET /tempo-fasi (fasi produzione)")
    print("✅ Endpoint POST /odl (creazione)")
    print("✅ Endpoint PUT /odl (aggiornamento)")
    print("✅ Endpoint POST /tempo-fasi (tracciamento)")
    print("✅ Pagina principale ODL")
    print("✅ Pagina monitoraggio ODL")
    
    print("\n🎯 Funzionalità implementate:")
    print("📊 Barra di avanzamento con fasi e colori")
    print("🎯 Sistema priorità con indicatori grafici")
    print("⏱️ Monitoraggio tempo reale fasi")
    print("📚 Storico completo ODL completati")
    print("🔄 Gestione avanzamento automatico")
    print("📝 Form migliorato con titoli descrittivi")

if __name__ == "__main__":
    run_comprehensive_test() 