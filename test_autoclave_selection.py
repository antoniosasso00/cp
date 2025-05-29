#!/usr/bin/env python3
"""
Test rapido per verificare funzionamento selezione autoclave
"""

import requests
import json
import sys
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def test_autoclave_selection():
    """Test della selezione autoclave per nesting manuale"""
    print_header("Test Selezione Autoclave Nesting Manuale")
    print(f"⏰ Avviato alle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    BASE_URL = "http://localhost:8001/api/v1"
    
    try:
        # 1. Controlla se il server è raggiungibile
        print("⏳ Verifica connessione al server...")
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server raggiungibile")
        else:
            print(f"❌ Server risponde ma con errore: {health_response.status_code}")
            return False
            
        # 2. Carica autoclavi disponibili
        print("⏳ Recupero autoclavi disponibili...")
        autoclavi_response = requests.get(f"{BASE_URL}/autoclavi", timeout=10)
        if autoclavi_response.status_code == 200:
            autoclavi = autoclavi_response.json()
            autoclavi_disponibili = [a for a in autoclavi if a.get('stato') == 'DISPONIBILE']
            print(f"✅ Trovate {len(autoclavi_disponibili)} autoclavi disponibili")
            
            if not autoclavi_disponibili:
                print("❌ Nessuna autoclave disponibile per il test")
                return False
                
            autoclave_test = autoclavi_disponibili[0]
            print(f"   Autoclave test: {autoclave_test['nome']} (ID: {autoclave_test['id']})")
        else:
            print(f"❌ Errore nel recupero autoclavi: {autoclavi_response.status_code}")
            return False
            
        # 3. Crea un nesting di test
        print("⏳ Creazione nesting di test...")
        nesting_data = {
            "note": "Test selezione autoclave"
        }
        nesting_response = requests.post(f"{BASE_URL}/nesting/", json=nesting_data, timeout=10)
        if nesting_response.status_code == 200:
            nesting = nesting_response.json()
            nesting_id = int(nesting['id'])
            print(f"✅ Nesting creato con ID: {nesting_id}")
        else:
            print(f"❌ Errore nella creazione nesting: {nesting_response.status_code}")
            print(f"   Risposta: {nesting_response.text}")
            return False
            
        # 4. Test selezione autoclave
        print("⏳ Test selezione autoclave...")
        selection_data = {
            "autoclave_id": autoclave_test['id']
        }
        selection_response = requests.post(
            f"{BASE_URL}/nesting/{nesting_id}/select-autoclave", 
            json=selection_data, 
            timeout=10
        )
        
        if selection_response.status_code == 200:
            result = selection_response.json()
            print("✅ Selezione autoclave riuscita!")
            print(f"   Messaggio: {result.get('message', 'N/A')}")
            print(f"   Autoclave ID: {result.get('autoclave_id', 'N/A')}")
            print(f"   Autoclave Nome: {result.get('autoclave_nome', 'N/A')}")
            return True
        else:
            print(f"❌ Errore nella selezione autoclave: {selection_response.status_code}")
            print(f"   Risposta: {selection_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al server. Assicurati che sia in esecuzione.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout nella richiesta al server.")
        return False
    except Exception as e:
        print(f"❌ Errore imprevisto: {e}")
        return False

if __name__ == "__main__":
    success = test_autoclave_selection()
    sys.exit(0 if success else 1) 