#!/usr/bin/env python3
"""
🧪 Script per creare dati di test per nesting
"""

import requests
import json
from datetime import datetime

# Configurazione API
BASE_URL = "http://localhost:8000/api/v1"
NESTING_API_URL = f"{BASE_URL}/nesting"

def create_test_nesting():
    """Crea un nesting di test tramite API automatica"""
    print("🔧 Creating test nesting...")
    
    try:
        # Usa l'API di nesting automatico
        response = requests.post(
            f"{NESTING_API_URL}/automatic",
            json={
                "parametri": {
                    "tolleranza_peso": 0.05,
                    "padding_mm": 20,
                    "borda_mm": 15,
                    "priorita_minima": 1,
                    "rotazione_abilitata": True
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                nesting_results = result.get('nesting_results', [])
                print(f"   ✅ Creati {len(nesting_results)} nesting automatici")
                
                for nesting in nesting_results:
                    print(f"      • Nesting ID: {nesting['id']}")
                    print(f"        Autoclave: {nesting.get('autoclave_nome', 'N/A')}")
                    print(f"        ODL inclusi: {nesting.get('odl_inclusi', 0)}")
                    print(f"        Efficienza: {nesting.get('efficienza', 0)}%")
                
                return nesting_results
            else:
                print(f"   ⚠️ Nesting non creati: {result.get('message', 'N/A')}")
                return []
        else:
            print(f"   ❌ Errore creazione nesting: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"   ❌ Errore creazione nesting: {e}")
        return []

def update_nesting_status(nesting_id, stato="finito"):
    """Aggiorna lo stato di un nesting per renderlo idoneo per il report"""
    print(f"📝 Updating nesting {nesting_id} status to {stato}...")
    
    try:
        response = requests.put(
            f"{NESTING_API_URL}/{nesting_id}/status",
            json={"nuovo_stato": stato},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ Stato aggiornato a '{stato}'")
            return True
        else:
            print(f"   ❌ Errore aggiornamento stato: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore aggiornamento stato: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 Creazione Nesting di Test")
    print("=" * 40)
    
    # Crea nesting automatici
    nesting_list = create_test_nesting()
    
    if not nesting_list:
        print("⚠️ Nessun nesting creato")
        return
    
    print(f"\n📝 Aggiornamento stati nesting...")
    
    # Aggiorna lo stato dei primi nesting per renderli idonei ai report
    success_count = 0
    for i, nesting in enumerate(nesting_list[:3]):  # Primi 3 nesting
        nesting_id = nesting['id']
        
        # Alterna gli stati per avere varietà
        stati = ["finito", "completato", "confermato"]
        stato = stati[i % len(stati)]
        
        if update_nesting_status(nesting_id, stato):
            success_count += 1
    
    print(f"\n🏆 RISULTATI:")
    print(f"   • Nesting creati: {len(nesting_list)}")
    print(f"   • Stati aggiornati: {success_count}")
    print(f"   • Ready per test report: {success_count}")

if __name__ == "__main__":
    main() 