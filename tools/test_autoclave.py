import urllib.request
import urllib.error
import json
import sys

# Configurazione endpoint
BASE_URL = "http://localhost:8000/api/v1"
AUTOCLAVE_ENDPOINT = f"{BASE_URL}/autoclavi"

# Dati di test
test_autoclave_data = {
    "nome": "Test Autoclave",
    "codice": "AC-TEST-01",
    "lunghezza": 2000,
    "larghezza_piano": 1000,
    "num_linee_vuoto": 4,
    "temperatura_max": 180.5,
    "pressione_max": 10.0,
    "stato": "disponibile",
    "in_manutenzione": False,
    "produttore": "Test Manufacturer",
    "anno_produzione": 2023,
    "note": "Test note"
}

def test_create_autoclave():
    try:
        print(f"🔄 Creazione autoclave con dati: {json.dumps(test_autoclave_data, indent=2)}")
        
        # Preparazione dei dati e della richiesta
        data = json.dumps(test_autoclave_data).encode('utf-8')
        req = urllib.request.Request(AUTOCLAVE_ENDPOINT, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        # Invio della richiesta
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.status
                response_data = json.loads(response.read().decode('utf-8'))
                print(f"Risposta: {status_code}")
                print(f"✅ Creazione riuscita: {json.dumps(response_data, indent=2)}")
                return response_data["id"]
        except urllib.error.HTTPError as e:
            print(f"Risposta: {e.code}")
            print(f"🚫 Errore: {e.read().decode('utf-8')}")
            return None
            
    except Exception as e:
        print(f"❌ Eccezione durante il test: {str(e)}")
        return None

def test_get_autoclave(autoclave_id):
    try:
        # Preparazione della richiesta
        req = urllib.request.Request(f"{AUTOCLAVE_ENDPOINT}/{autoclave_id}", method='GET')
        
        # Invio della richiesta
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.status
                response_data = json.loads(response.read().decode('utf-8'))
                print(f"Risposta GET: {status_code}")
                print(f"✅ GET riuscito: {json.dumps(response_data, indent=2)}")
        except urllib.error.HTTPError as e:
            print(f"Risposta GET: {e.code}")
            print(f"🚫 Errore: {e.read().decode('utf-8')}")
            
    except Exception as e:
        print(f"❌ Eccezione durante il test: {str(e)}")

if __name__ == "__main__":
    print("🔄 Test API Autoclave...")
    autoclave_id = test_create_autoclave()
    if autoclave_id:
        test_get_autoclave(autoclave_id) 