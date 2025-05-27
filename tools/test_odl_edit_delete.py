#!/usr/bin/env python3
"""
Script di test per verificare le funzionalità di modifica ed eliminazione ODL
anche quando sono in stato "Finito".

Testa:
1. Endpoint DELETE con parametro confirm
2. Endpoint PUT per modifica note
3. Logging delle operazioni
4. Gestione errori appropriata
"""

import requests
import json
import sys
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    """Stampa una sezione del test"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    """Stampa il risultato di un test"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_odl_endpoints():
    """Test principale delle funzionalità ODL"""
    
    print_section("Test Funzionalità Modifica/Eliminazione ODL")
    
    # 1. Verifica esistenza ODL di test
    print("\n1️⃣ Verifica ODL esistenti...")
    try:
        response = requests.get(f"{BASE_URL}/odl", headers=HEADERS)
        if response.status_code == 200:
            odl_list = response.json()
            print_result("Caricamento ODL", True, f"Trovati {len(odl_list)} ODL")
            
            if not odl_list:
                print("⚠️  Nessun ODL trovato. Creando ODL di test...")
                # Crea ODL di test
                test_odl = {
                    "parte_id": 1,  # Assumendo che esista
                    "quantita": 1,
                    "note": "ODL di test per modifica/eliminazione"
                }
                create_response = requests.post(f"{BASE_URL}/odl", 
                                              json=test_odl, headers=HEADERS)
                if create_response.status_code == 201:
                    test_odl_id = create_response.json()["id"]
                    print_result("Creazione ODL test", True, f"ODL {test_odl_id} creato")
                else:
                    print_result("Creazione ODL test", False, "Impossibile creare ODL")
                    return
            else:
                test_odl_id = odl_list[0]["id"]
                
        else:
            print_result("Caricamento ODL", False, f"Status: {response.status_code}")
            return
            
    except Exception as e:
        print_result("Caricamento ODL", False, f"Errore: {str(e)}")
        return

    # 2. Test modifica note ODL
    print("\n2️⃣ Test modifica note ODL...")
    try:
        update_data = {
            "note": f"Note aggiornate - Test {datetime.now().strftime('%H:%M:%S')}"
        }
        response = requests.put(f"{BASE_URL}/odl/{test_odl_id}", 
                               json=update_data, headers=HEADERS)
        
        if response.status_code == 200:
            updated_odl = response.json()
            print_result("Modifica note ODL", True, 
                        f"Note aggiornate: {updated_odl.get('note', 'N/A')}")
        else:
            print_result("Modifica note ODL", False, 
                        f"Status: {response.status_code}")
            
    except Exception as e:
        print_result("Modifica note ODL", False, f"Errore: {str(e)}")

    # 3. Test eliminazione ODL normale (senza confirm)
    print("\n3️⃣ Test eliminazione ODL normale...")
    try:
        response = requests.delete(f"{BASE_URL}/odl/{test_odl_id}", headers=HEADERS)
        
        if response.status_code == 200:
            print_result("Eliminazione ODL normale", True, "ODL eliminato con successo")
        else:
            print_result("Eliminazione ODL normale", False, 
                        f"Status: {response.status_code}")
            
    except Exception as e:
        print_result("Eliminazione ODL normale", False, f"Errore: {str(e)}")

    # 4. Test creazione ODL "Finito" per test eliminazione con confirm
    print("\n4️⃣ Test eliminazione ODL 'Finito'...")
    try:
        # Crea nuovo ODL
        test_odl = {
            "parte_id": 1,
            "quantita": 1,
            "status": "Finito",
            "note": "ODL finito per test eliminazione"
        }
        create_response = requests.post(f"{BASE_URL}/odl", 
                                      json=test_odl, headers=HEADERS)
        
        if create_response.status_code == 201:
            finished_odl_id = create_response.json()["id"]
            print_result("Creazione ODL finito", True, f"ODL {finished_odl_id} creato")
            
            # Test eliminazione senza confirm (dovrebbe fallire)
            response = requests.delete(f"{BASE_URL}/odl/{finished_odl_id}", headers=HEADERS)
            if response.status_code == 400:
                print_result("Eliminazione senza confirm", True, 
                           "Correttamente bloccata per ODL finito")
            else:
                print_result("Eliminazione senza confirm", False, 
                           f"Doveva essere bloccata, status: {response.status_code}")
            
            # Test eliminazione con confirm (dovrebbe funzionare)
            response = requests.delete(f"{BASE_URL}/odl/{finished_odl_id}?confirm=true", 
                                     headers=HEADERS)
            if response.status_code == 200:
                print_result("Eliminazione con confirm", True, 
                           "ODL finito eliminato con conferma")
            else:
                print_result("Eliminazione con confirm", False, 
                           f"Status: {response.status_code}")
                
        else:
            print_result("Creazione ODL finito", False, 
                        f"Status: {create_response.status_code}")
            
    except Exception as e:
        print_result("Test ODL finito", False, f"Errore: {str(e)}")

    # 5. Test verifica logging
    print("\n5️⃣ Verifica logging operazioni...")
    try:
        response = requests.get(f"{BASE_URL}/system-logs", headers=HEADERS)
        
        if response.status_code == 200:
            logs = response.json()
            odl_logs = [log for log in logs if "ODL" in log.get("message", "")]
            print_result("Verifica logging", True, 
                        f"Trovati {len(odl_logs)} log relativi a ODL")
        else:
            print_result("Verifica logging", False, 
                        f"Status: {response.status_code}")
            
    except Exception as e:
        print_result("Verifica logging", False, f"Errore: {str(e)}")

def main():
    """Funzione principale"""
    print("🚀 Avvio test funzionalità modifica/eliminazione ODL")
    print(f"🔗 Base URL: {BASE_URL}")
    
    # Verifica connessione al backend
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=5)
        if response.status_code == 200:
            print("✅ Backend raggiungibile")
        else:
            print("❌ Backend non risponde correttamente")
            return
    except Exception as e:
        print(f"❌ Impossibile raggiungere il backend: {str(e)}")
        print("💡 Assicurati che il backend sia in esecuzione su localhost:8000")
        return
    
    # Esegui i test
    test_odl_endpoints()
    
    print_section("Riepilogo Test Completato")
    print("✅ Test delle funzionalità di modifica/eliminazione ODL completato")
    print("📋 Verifica i risultati sopra per eventuali problemi")
    print("🔍 Controlla i log del backend per dettagli aggiuntivi")

if __name__ == "__main__":
    main() 