#!/usr/bin/env python3
"""
Test per verificare le correzioni al solver del nesting
Verifica che non ci siano più errori di conversione float to integer
"""

import sys
import os
import requests
import json
import time

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_nesting_api():
    """Test dell'API di nesting per verificare le correzioni"""
    
    print("🧪 Test API Nesting - Verifica Correzioni Float to Integer")
    print("=" * 60)
    
    # URL dell'API
    base_url = "http://localhost:8000"
    
    # 1. Test caricamento dati
    print("\n1️⃣ Test caricamento dati...")
    try:
        response = requests.get(f"{base_url}/api/v1/batch_nesting/data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dati caricati: {len(data.get('odl_in_attesa_cura', []))} ODL, {len(data.get('autoclavi_disponibili', []))} autoclavi")
            
            # Prendi i primi ODL e la prima autoclave per il test
            odl_list = data.get('odl_in_attesa_cura', [])
            autoclavi_list = data.get('autoclavi_disponibili', [])
            
            if not odl_list or not autoclavi_list:
                print("❌ Nessun ODL o autoclave disponibile per il test")
                return False
                
        else:
            print(f"❌ Errore caricamento dati: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore connessione API: {e}")
        return False
    
    # 2. Test solve nesting con parametri che potrebbero causare errori float
    print("\n2️⃣ Test solve nesting...")
    try:
        # Prendi i primi 3 ODL per il test
        test_odl_ids = [odl['id'] for odl in odl_list[:3]]
        test_autoclave_id = autoclavi_list[0]['id']
        
        payload = {
            "odl_ids": test_odl_ids,
            "autoclave_id": test_autoclave_id,
            "padding_mm": 20,
            "min_distance_mm": 15,
            "vacuum_lines_capacity": 10,
            "allow_heuristic": False,
            "timeout_override": 30,
            "heavy_piece_threshold_kg": 50.0
        }
        
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v1/batch_nesting/solve",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        print(f"⏱️ Tempo risposta: {(end_time - start_time)*1000:.0f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Nesting completato con successo!")
            
            # Verifica risultati
            metrics = result.get('metrics', {})
            positioned_tools = result.get('positioned_tools', [])
            excluded_odls = result.get('excluded_odls', [])
            
            print(f"📊 Risultati:")
            print(f"   • ODL posizionati: {len(positioned_tools)}")
            print(f"   • ODL esclusi: {len(excluded_odls)}")
            print(f"   • Efficienza: {metrics.get('efficiency_score', 0):.1f}%")
            print(f"   • Area utilizzata: {metrics.get('area_utilization_pct', 0):.1f}%")
            print(f"   • Peso totale: {metrics.get('total_weight_kg', 0):.1f}kg")
            print(f"   • Algoritmo: {metrics.get('algorithm_status', 'N/A')}")
            print(f"   • Fallback usato: {metrics.get('fallback_used', False)}")
            print(f"   • Tempo solver: {metrics.get('time_solver_ms', 0):.0f}ms")
            
            # Verifica che non ci siano errori di tipo float
            if result.get('success', False):
                print("✅ Test superato: nessun errore di conversione float to integer")
                return True
            else:
                print(f"⚠️ Nesting non riuscito: {result.get('message', 'Motivo sconosciuto')}")
                return False
                
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Errore API: {response.status_code}")
            print(f"   Dettagli: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante test solve: {e}")
        return False
    
    # 3. Test con parametri edge case
    print("\n3️⃣ Test parametri edge case...")
    try:
        edge_payload = {
            "odl_ids": test_odl_ids[:2],  # Meno ODL
            "autoclave_id": test_autoclave_id,
            "padding_mm": 5,  # Valore minimo
            "min_distance_mm": 5,  # Valore minimo
            "vacuum_lines_capacity": 5,
            "allow_heuristic": True,  # Abilita heuristica
            "timeout_override": 15,  # Timeout breve
            "heavy_piece_threshold_kg": 25.0
        }
        
        response = requests.post(
            f"{base_url}/api/v1/batch_nesting/solve",
            json=edge_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test edge case completato")
            print(f"   • Successo: {result.get('success', False)}")
            print(f"   • Algoritmo: {result.get('metrics', {}).get('algorithm_status', 'N/A')}")
            return True
        else:
            print(f"⚠️ Test edge case fallito: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore test edge case: {e}")
        return False

def main():
    """Funzione principale del test"""
    
    print("🚀 Avvio test correzioni nesting solver")
    print("Verifica che le modifiche abbiano risolto l'errore 'float object cannot be interpreted as an integer'")
    
    # Attendi che i servizi siano pronti
    print("\n⏳ Attesa avvio servizi...")
    time.sleep(3)
    
    # Esegui test
    success = test_nesting_api()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("✅ Le correzioni al solver del nesting funzionano correttamente")
        print("✅ Nessun errore di conversione float to integer rilevato")
    else:
        print("❌ ALCUNI TEST FALLITI")
        print("⚠️ Potrebbero esserci ancora problemi nel solver")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 