#!/usr/bin/env python3
"""
Test rapido per l'endpoint nesting temporaneo
"""

import requests
import json

# URL base del backend
BASE_URL = "http://localhost:8000/api/v1"

def test_nesting_endpoint():
    """Test dell'endpoint POST /nesting/genera"""
    
    print("🧪 Test Endpoint Nesting Temporaneo")
    print("=" * 50)
    
    # Payload di test
    payload = {
        "odl_ids": ["1", "2", "3"],
        "autoclave_ids": ["1"],
        "parametri": {
            "padding_mm": 20,
            "min_distance_mm": 15,
            "priorita_area": True,
            "accorpamento_odl": False
        }
    }
    
    print(f"📤 Invio richiesta a: {BASE_URL}/nesting/genera")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nesting/genera",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📥 Risposta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successo!")
            print(f"📋 Risultato: {json.dumps(result, indent=2)}")
            
            # Verifica che il batch_id sia presente
            if "batch_id" in result:
                print(f"🆔 Batch ID generato: {result['batch_id']}")
                return result["batch_id"]
            else:
                print("❌ Errore: batch_id mancante nella risposta")
                return None
        else:
            print("❌ Errore nella richiesta")
            try:
                error_detail = response.json()
                print(f"📋 Dettaglio errore: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"📋 Risposta raw: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore: Impossibile connettersi al backend")
        print("💡 Assicurati che il backend sia avviato su localhost:8000")
        return None
    except requests.exceptions.Timeout:
        print("❌ Errore: Timeout della richiesta")
        return None
    except Exception as e:
        print(f"❌ Errore imprevisto: {str(e)}")
        return None

def test_batch_retrieval(batch_id):
    """Test del recupero batch nesting"""
    
    if not batch_id:
        print("\n⏭️ Saltando test recupero batch (nessun batch_id)")
        return
    
    print(f"\n🔍 Test Recupero Batch: {batch_id}")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/batch_nesting/{batch_id}",
            timeout=10
        )
        
        print(f"📥 Risposta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch recuperato con successo!")
            print(f"📋 Nome: {result.get('nome', 'N/A')}")
            print(f"📋 Stato: {result.get('stato', 'N/A')}")
            print(f"📋 ODL inclusi: {len(result.get('odl_ids', []))}")
            print(f"📋 Parametri: {result.get('parametri', {})}")
        else:
            print("❌ Errore nel recupero batch")
            try:
                error_detail = response.json()
                print(f"📋 Dettaglio errore: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"📋 Risposta raw: {response.text}")
                
    except Exception as e:
        print(f"❌ Errore nel recupero batch: {str(e)}")

if __name__ == "__main__":
    print("🚀 Avvio test endpoint nesting...")
    
    # Test creazione nesting
    batch_id = test_nesting_endpoint()
    
    # Test recupero batch
    test_batch_retrieval(batch_id)
    
    print("\n�� Test completato!") 