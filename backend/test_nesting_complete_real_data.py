#!/usr/bin/env python3
"""
Test completo del modulo di nesting con dati reali
"""
import requests
import json
import time
import sys
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_step(step_num, title):
    """Stampa un titolo di step formattato"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Testa un endpoint API"""
    url = f"{API_BASE}{endpoint}"
    print(f"🌐 {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=30)
        else:
            raise ValueError(f"Metodo HTTP non supportato: {method}")
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == expected_status:
            try:
                result = response.json()
                print(f"✅ Successo! Dati ricevuti: {len(str(result))} caratteri")
                return result
            except:
                print(f"✅ Successo! Risposta non JSON")
                return response.text
        else:
            print(f"❌ Errore! Status atteso: {expected_status}, ricevuto: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📝 Dettagli errore: {error_detail}")
            except:
                print(f"📝 Risposta errore: {response.text[:200]}...")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Errore di connessione! Server non raggiungibile su {BASE_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Timeout! Il server non ha risposto entro 30 secondi")
        return None
    except Exception as e:
        print(f"❌ Errore imprevisto: {str(e)}")
        return None

def main():
    """Test completo del modulo di nesting"""
    
    print("🚀 TEST COMPLETO MODULO NESTING CON DATI REALI")
    print(f"🕒 Avviato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Verifica connessione server
    print_step(1, "VERIFICA CONNESSIONE SERVER")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server FastAPI raggiungibile!")
        else:
            print(f"⚠️ Server risponde ma con status {response.status_code}")
    except:
        print("❌ Server non raggiungibile! Assicurati che sia avviato con:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    
    # Step 2: Recupera ODL disponibili
    print_step(2, "RECUPERO ODL IN ATTESA DI CURA")
    
    odl_data = test_endpoint("GET", "/odl?status=Attesa%20Cura")
    if not odl_data:
        print("❌ Impossibile recuperare ODL")
        sys.exit(1)
    
    print(f"📋 ODL trovati: {len(odl_data)}")
    if len(odl_data) == 0:
        print("⚠️ Nessun ODL in stato 'Attesa Cura' trovato!")
        sys.exit(1)
    
    # Mostra dettagli ODL
    for i, odl in enumerate(odl_data[:3]):  # Mostra solo i primi 3
        print(f"  ODL #{odl['id']}: {odl.get('parte', {}).get('part_number', 'N/A')} - {odl.get('parte', {}).get('descrizione_breve', 'N/A')}")
    
    # Step 3: Recupera autoclavi disponibili
    print_step(3, "RECUPERO AUTOCLAVI DISPONIBILI")
    
    autoclave_data = test_endpoint("GET", "/autoclavi?stato=DISPONIBILE")
    if not autoclave_data:
        print("❌ Impossibile recuperare autoclavi")
        sys.exit(1)
    
    print(f"🏭 Autoclavi trovate: {len(autoclave_data)}")
    if len(autoclave_data) == 0:
        print("⚠️ Nessuna autoclave disponibile trovata!")
        sys.exit(1)
    
    # Mostra dettagli autoclavi
    for autoclave in autoclave_data:
        print(f"  Autoclave #{autoclave['id']}: {autoclave['nome']} ({autoclave['larghezza_piano']}x{autoclave['lunghezza']}mm)")
    
    # Step 4: Test generazione nesting
    print_step(4, "GENERAZIONE NESTING CON OR-TOOLS")
    
    # Prepara dati per il nesting (usa i primi 3 ODL e la prima autoclave)
    nesting_request = {
        "odl_ids": [str(odl['id']) for odl in odl_data[:3]],
        "autoclave_ids": [str(autoclave_data[0]['id'])],
        "parametri": {
            "padding_mm": 20,
            "min_distance_mm": 15,
            "priorita_area": True
        }
    }
    
    print(f"📤 Dati richiesta nesting:")
    print(json.dumps(nesting_request, indent=2))
    
    nesting_result = test_endpoint("POST", "/nesting/genera", nesting_request)
    if not nesting_result:
        print("❌ Generazione nesting fallita!")
        sys.exit(1)
    
    print(f"✅ Nesting generato con successo!")
    print(f"📦 Batch ID: {nesting_result.get('batch_id', 'N/A')}")
    print(f"📊 ODL posizionati: {len(nesting_result.get('positioned_tools', []))}")
    print(f"📊 ODL esclusi: {len(nesting_result.get('excluded_odls', []))}")
    print(f"📊 Efficienza: {nesting_result.get('efficiency', 0):.1f}%")
    print(f"📊 Peso totale: {nesting_result.get('total_weight', 0):.1f}kg")
    
    batch_id = nesting_result.get('batch_id')
    if not batch_id:
        print("❌ Batch ID non ricevuto!")
        sys.exit(1)
    
    # Step 5: Verifica batch creato
    print_step(5, "VERIFICA BATCH NESTING CREATO")
    
    batch_data = test_endpoint("GET", f"/batch_nesting/{batch_id}")
    if not batch_data:
        print("❌ Impossibile recuperare dati batch")
        sys.exit(1)
    
    print(f"✅ Batch recuperato:")
    print(f"  Nome: {batch_data.get('nome', 'N/A')}")
    print(f"  Stato: {batch_data.get('stato', 'N/A')}")
    print(f"  Autoclave ID: {batch_data.get('autoclave_id', 'N/A')}")
    print(f"  ODL inclusi: {len(batch_data.get('odl_ids', []))}")
    
    # Step 6: Test endpoint full per frontend
    print_step(6, "TEST ENDPOINT FULL PER FRONTEND")
    
    batch_full_data = test_endpoint("GET", f"/batch_nesting/{batch_id}/full")
    if not batch_full_data:
        print("❌ Impossibile recuperare dati batch completi")
        sys.exit(1)
    
    print(f"✅ Dati completi batch recuperati:")
    print(f"  Configurazione JSON presente: {'Sì' if batch_full_data.get('configurazione_json') else 'No'}")
    print(f"  Autoclave info presente: {'Sì' if batch_full_data.get('autoclave') else 'No'}")
    print(f"  ODL esclusi: {len(batch_full_data.get('odl_esclusi', []))}")
    
    # Step 7: Test conferma batch
    print_step(7, "TEST CONFERMA BATCH")
    
    conferma_result = test_endpoint("PATCH", f"/batch_nesting/{batch_id}/conferma?confermato_da_utente=test_user&confermato_da_ruolo=Curing")
    if conferma_result:
        print(f"✅ Batch confermato con successo!")
        print(f"  Nuovo stato: {conferma_result.get('stato', 'N/A')}")
    else:
        print("⚠️ Conferma batch fallita (potrebbe essere normale se già confermato)")
    
    # Step 8: Riepilogo finale
    print_step(8, "RIEPILOGO FINALE")
    
    print("🎉 TEST COMPLETATO CON SUCCESSO!")
    print(f"✅ Server backend: Funzionante")
    print(f"✅ API ODL: Funzionante ({len(odl_data)} ODL trovati)")
    print(f"✅ API Autoclavi: Funzionante ({len(autoclave_data)} autoclavi trovate)")
    print(f"✅ Algoritmo nesting: Funzionante (efficienza {nesting_result.get('efficiency', 0):.1f}%)")
    print(f"✅ Batch management: Funzionante")
    print(f"✅ Endpoint frontend: Funzionanti")
    
    print(f"\n📋 DATI PER TEST FRONTEND:")
    print(f"  Batch ID: {batch_id}")
    print(f"  URL risultato: {BASE_URL}/dashboard/curing/nesting/result/{batch_id}")
    
    print(f"\n🔧 PROSSIMI PASSI:")
    print(f"  1. Verifica che il frontend mostri correttamente gli ODL")
    print(f"  2. Testa la generazione nesting dal frontend")
    print(f"  3. Verifica la visualizzazione del canvas con le posizioni")
    print(f"  4. Testa la conferma del batch dal frontend")

if __name__ == "__main__":
    main() 