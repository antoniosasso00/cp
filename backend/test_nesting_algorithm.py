#!/usr/bin/env python3
"""
Script di test per l'algoritmo di nesting 2D con OR-Tools
"""

import requests
import json
import sys
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
NESTING_ENDPOINT = f"{BASE_URL}/api/v1/nesting/genera"

def test_nesting_algorithm():
    """
    Testa l'algoritmo di nesting inviando una richiesta di test
    """
    print("🧠 Test Algoritmo di Nesting OR-Tools")
    print("=" * 50)
    
    # Parametri di test
    test_request = {
        "odl_ids": ["1", "2", "3"],  # ODL di esempio
        "autoclave_ids": ["1"],       # Prima autoclave disponibile
        "parametri": {
            "padding_mm": 20,
            "min_distance_mm": 15,
            "priorita_area": False,  # Massimizza numero ODL invece dell'area
            "accorpamento_odl": False
        }
    }
    
    print(f"📤 Invio richiesta di nesting:")
    print(f"   ODL: {test_request['odl_ids']}")
    print(f"   Autoclave: {test_request['autoclave_ids'][0]}")
    print(f"   Parametri: padding={test_request['parametri']['padding_mm']}mm, distanza={test_request['parametri']['min_distance_mm']}mm")
    print(f"   Priorità area: {test_request['parametri']['priorita_area']}")
    print()
    
    try:
        # Invia la richiesta
        print("🚀 Invio richiesta al server...")
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={'Content-Type': 'application/json'},
            timeout=60  # Timeout di 60 secondi
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Nesting completato con successo!")
            print()
            print("📊 Risultati:")
            print(f"   Batch ID: {result['batch_id']}")
            print(f"   Messaggio: {result['message']}")
            print(f"   ODL posizionati: {len(result['positioned_tools'])}")
            print(f"   ODL esclusi: {len(result['excluded_odls'])}")
            print(f"   Efficienza: {result['efficiency']:.1f}%")
            print(f"   Peso totale: {result['total_weight']:.1f} kg")
            print(f"   Status algoritmo: {result['algorithm_status']}")
            print(f"   Successo: {result['success']}")
            print()
            
            # Dettagli tool posizionati
            if result['positioned_tools']:
                print("🔧 Tool posizionati:")
                for i, tool in enumerate(result['positioned_tools'], 1):
                    rotation_info = " (🔄 RUOTATO)" if tool.get('rotated', False) else " (➡️ NORMALE)"
                    print(f"   {i}. ODL {tool['odl_id']}: posizione ({tool['x']:.1f}, {tool['y']:.1f}), dimensioni {tool['width']:.1f}x{tool['height']:.1f}mm, peso {tool['peso']:.1f}kg{rotation_info}")
            
            # Dettagli esclusioni
            if result['excluded_odls']:
                print()
                print("❌ ODL esclusi:")
                for i, excluded in enumerate(result['excluded_odls'], 1):
                    print(f"   {i}. ODL {excluded['odl_id']}: {excluded['motivo']} - {excluded['dettagli']}")
            
            print()
            print("✅ Test completato con successo!")
            return True
            
        else:
            print(f"❌ Errore nella richiesta: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Dettaglio: {error_detail.get('detail', 'Errore sconosciuto')}")
            except:
                print(f"   Risposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione al server!")
        print("   Assicurati che il server FastAPI sia in esecuzione su http://localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout nella richiesta!")
        print("   L'algoritmo potrebbe aver impiegato troppo tempo")
        return False
    except Exception as e:
        print(f"❌ Errore imprevisto: {str(e)}")
        return False

def check_server_status():
    """
    Verifica se il server è attivo
    """
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server FastAPI attivo e raggiungibile")
            return True
        else:
            print(f"⚠️ Server risponde ma con status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server FastAPI non raggiungibile")
        print("   Avvia il server con: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Errore nella verifica server: {str(e)}")
        return False

def main():
    """
    Funzione principale
    """
    print(f"🕐 Avvio test alle {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Verifica server
    print("🔍 Verifica stato del server...")
    if not check_server_status():
        sys.exit(1)
    
    print()
    
    # Esegui test nesting
    success = test_nesting_algorithm()
    
    print()
    if success:
        print("🎉 Tutti i test sono stati completati con successo!")
        sys.exit(0)
    else:
        print("💥 Alcuni test sono falliti!")
        sys.exit(1)

if __name__ == "__main__":
    main() 