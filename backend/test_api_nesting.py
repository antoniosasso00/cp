#!/usr/bin/env python3
"""
Test finale dell'endpoint API di nesting per verificare che tutto funzioni end-to-end
"""

import sys
sys.path.append('.')

import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL

def test_api_nesting_endpoint():
    """Test dell'endpoint API /nesting/genera"""
    
    print("🌐 TEST ENDPOINT API NESTING")
    print("=" * 40)
    
    # Setup database per ottenere ODL reali
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Ottieni ODL disponibili
        odls = db.query(ODL).all()
        if not odls:
            print("❌ Nessun ODL disponibile per il test!")
            return False
        
        odl_ids = [str(odl.id) for odl in odls[:2]]  # Prendi i primi 2 ODL
        print(f"📋 ODL selezionati per il test: {odl_ids}")
        
        # 2. Prepara payload per l'API
        payload = {
            "odl_ids": odl_ids,
            "autoclave_ids": ["1"],  # Prima autoclave
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 5,
                "priorita_area": False
            }
        }
        
        print(f"📤 Payload:")
        print(json.dumps(payload, indent=2))
        
        # 3. URL dell'endpoint (assumendo che il server sia in running su localhost:8000)
        url = "http://localhost:8000/api/v1/nesting/genera"
        
        print(f"\n🚀 Invocazione API...")
        print(f"URL: {url}")
        
        # 4. Effettua la chiamata POST
        response = requests.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=60  # Timeout di 60 secondi
        )
        
        # 5. Analizza la risposta
        print(f"\n📥 RISPOSTA API:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ SUCCESSO! Risposta JSON:")
                print(json.dumps(data, indent=2))
                
                # Verifica campi essenziali
                required_fields = ['batch_id', 'message', 'positioned_tools', 'excluded_odls', 'efficiency', 'success']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"\n❌ Campi mancanti nella risposta: {missing_fields}")
                    return False
                
                print(f"\n📊 STATISTICHE RISULTATO:")
                print(f"   • Batch ID: {data.get('batch_id')}")
                print(f"   • Successo: {data.get('success')}")
                print(f"   • ODL posizionati: {len(data.get('positioned_tools', []))}")
                print(f"   • ODL esclusi: {len(data.get('excluded_odls', []))}")
                print(f"   • Efficienza: {data.get('efficiency', 0):.1f}%")
                print(f"   • Peso totale: {data.get('total_weight', 0):.1f}kg")
                print(f"   • Status algoritmo: {data.get('algorithm_status')}")
                
                if data.get('positioned_tools'):
                    print(f"\n✅ TOOL POSIZIONATI:")
                    for i, tool in enumerate(data['positioned_tools']):
                        print(f"   {i+1}. ODL {tool.get('odl_id')}: pos({tool.get('x'):.0f},{tool.get('y'):.0f}), dim({tool.get('width'):.0f}x{tool.get('height'):.0f}mm), ruotato={tool.get('rotated', False)}")
                
                if data.get('excluded_odls'):
                    print(f"\n❌ ODL ESCLUSI:")
                    for excl in data['excluded_odls']:
                        print(f"   • ODL {excl.get('odl_id')}: {excl.get('motivo')} - {excl.get('dettagli', '')}")
                
                return data.get('success', False) and len(data.get('positioned_tools', [])) > 0
                
            except json.JSONDecodeError as e:
                print(f"❌ Errore nel parsing JSON: {e}")
                print(f"Raw response: {response.text}")
                return False
                
        elif response.status_code == 422:
            print(f"❌ Errore di validazione (422):")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
            return False
            
        else:
            print(f"❌ Errore HTTP {response.status_code}:")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRORE: Impossibile connettersi al server!")
        print("🔧 Assicurati che il server FastAPI sia in esecuzione su localhost:8000")
        print("   Comando per avviarlo: cd backend && uvicorn main:app --reload")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ ERRORE: Timeout della richiesta")
        return False
        
    except Exception as e:
        print(f"❌ ERRORE IMPREVISTO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def print_instructions():
    """Stampa le istruzioni per avviare il server se necessario"""
    
    print("\n" + "=" * 60)
    print("📖 ISTRUZIONI PER AVVIARE IL SERVER (se non è già attivo):")
    print("=" * 60)
    print("1. Apri un nuovo terminale")
    print("2. Naviga alla directory backend:")
    print("   cd C:/Users/Anton/Documents/CarbonPilot/backend")
    print("3. Attiva l'ambiente virtuale:")
    print("   ../.venv/Scripts/activate")
    print("4. Avvia il server FastAPI:")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("5. Attendi che il server sia pronto (messaggio 'Application startup complete')")
    print("6. Riesegui questo test")
    print()
    print("Il server sarà disponibile su: http://localhost:8000")
    print("Documentazione API: http://localhost:8000/docs")

if __name__ == "__main__":
    print("🚀 AVVIO TEST COMPLETO API NESTING")
    print("=" * 50)
    
    success = test_api_nesting_endpoint()
    
    print("\n" + "=" * 60)
    print("📋 RISULTATO TEST API:")
    print("=" * 60)
    
    if success:
        print("✅ TEST API COMPLETATO CON SUCCESSO!")
        print("🎉 L'endpoint /nesting/genera funziona correttamente!")
        print("✅ Il modulo di nesting è completamente operativo")
        print("✅ Frontend può invocare l'API per generare nesting")
    else:
        print("❌ TEST API FALLITO")
        print("🔧 Verificare i log sopra per identificare il problema")
        print_instructions()
    
    print("\n🔍 TEST API COMPLETATO") 