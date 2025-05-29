#!/usr/bin/env python3
"""
Script di test per verificare il reset del modulo nesting.
Verifica che la pulizia sia stata completata correttamente e che i nuovi endpoint funzionino.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configurazione
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_endpoints():
    """
    Testa gli endpoint backend essenziali del nesting.
    """
    print("🔧 Test Backend Endpoints")
    print("=" * 50)
    
    # Test 1: GET /api/nesting/ - Lista nesting
    try:
        response = requests.get(f"{BACKEND_URL}/api/nesting/")
        if response.status_code == 200:
            nesting_list = response.json()
            print(f"✅ GET /api/nesting/ - OK ({len(nesting_list)} nesting trovati)")
        else:
            print(f"❌ GET /api/nesting/ - Errore {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/nesting/ - Errore connessione: {e}")
    
    # Test 2: POST /api/nesting/generate - Genera nesting
    try:
        payload = {
            "autoclave_id": None,
            "priorita_minima": 1,
            "include_bozze": False
        }
        response = requests.post(f"{BACKEND_URL}/api/nesting/generate", json=payload)
        if response.status_code in [200, 201]:
            nesting_data = response.json()
            print(f"✅ POST /api/nesting/generate - OK (ID: {nesting_data.get('id', 'N/A')})")
            return nesting_data.get('id')
        elif response.status_code == 400:
            print(f"⚠️ POST /api/nesting/generate - Nessun ODL disponibile (normale se DB vuoto)")
        else:
            print(f"❌ POST /api/nesting/generate - Errore {response.status_code}")
    except Exception as e:
        print(f"❌ POST /api/nesting/generate - Errore connessione: {e}")
    
    return None

def test_frontend_page():
    """
    Testa che la pagina frontend sia accessibile.
    """
    print("\n🌐 Test Frontend Page")
    print("=" * 50)
    
    try:
        response = requests.get(f"{FRONTEND_URL}/dashboard/management/nesting")
        if response.status_code == 200:
            print("✅ Pagina /dashboard/management/nesting - Accessibile")
        else:
            print(f"❌ Pagina /dashboard/management/nesting - Errore {response.status_code}")
    except Exception as e:
        print(f"❌ Pagina frontend - Errore connessione: {e}")

def check_removed_components():
    """
    Verifica che i componenti obsoleti siano stati rimossi.
    """
    print("\n🧹 Verifica Rimozione Componenti Obsoleti")
    print("=" * 50)
    
    # Percorsi che dovrebbero essere stati rimossi
    removed_paths = [
        "frontend/src/components/nesting/",
        "frontend/src/app/dashboard/nesting-preview/",
    ]
    
    for path in removed_paths:
        if os.path.exists(path):
            print(f"❌ {path} - Ancora presente (dovrebbe essere rimosso)")
        else:
            print(f"✅ {path} - Rimosso correttamente")
    
    # Verifica che la nuova pagina esista
    new_page = "frontend/src/app/dashboard/management/nesting/page.tsx"
    if os.path.exists(new_page):
        print(f"✅ {new_page} - Creato correttamente")
    else:
        print(f"❌ {new_page} - Non trovato")

def test_nesting_workflow(nesting_id):
    """
    Testa il workflow completo di un nesting se disponibile.
    """
    if not nesting_id:
        print("\n⚠️ Nessun nesting disponibile per testare il workflow")
        return
    
    print(f"\n🔄 Test Workflow Nesting (ID: {nesting_id})")
    print("=" * 50)
    
    # Test 3: GET /api/nesting/{id} - Dettagli nesting
    try:
        response = requests.get(f"{BACKEND_URL}/api/nesting/{nesting_id}")
        if response.status_code == 200:
            nesting_detail = response.json()
            print(f"✅ GET /api/nesting/{nesting_id} - OK")
            print(f"   Stato: {nesting_detail.get('stato', 'N/A')}")
            print(f"   ODL: {len(nesting_detail.get('odl_ids', []))}")
        else:
            print(f"❌ GET /api/nesting/{nesting_id} - Errore {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/nesting/{nesting_id} - Errore: {e}")
    
    # Test 4: POST /api/nesting/{id}/confirm - Conferma nesting (solo se in BOZZA)
    try:
        response = requests.post(f"{BACKEND_URL}/api/nesting/{nesting_id}/confirm")
        if response.status_code == 200:
            print(f"✅ POST /api/nesting/{nesting_id}/confirm - OK")
        elif response.status_code == 400:
            print(f"⚠️ POST /api/nesting/{nesting_id}/confirm - Nesting non in stato BOZZA")
        else:
            print(f"❌ POST /api/nesting/{nesting_id}/confirm - Errore {response.status_code}")
    except Exception as e:
        print(f"❌ POST /api/nesting/{nesting_id}/confirm - Errore: {e}")

def main():
    """
    Esegue tutti i test di verifica del reset nesting.
    """
    print("🧪 TEST NESTING RESET - CarbonPilot")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verifica rimozione componenti
    check_removed_components()
    
    # Test backend
    nesting_id = test_backend_endpoints()
    
    # Test workflow se disponibile
    test_nesting_workflow(nesting_id)
    
    # Test frontend
    test_frontend_page()
    
    print("\n" + "=" * 60)
    print("✅ Test completati!")
    print()
    print("📋 CHECKLIST MANUALE:")
    print("✅ Naviga in /dashboard/management/nesting")
    print("✅ Verifica che non ci siano più componenti obsoleti")
    print("✅ Genera un nesting → deve apparire in tabella")
    print("✅ Testa i bottoni Conferma, Dettagli, Cancella")
    print()

if __name__ == "__main__":
    main() 