#!/usr/bin/env python3
"""
🚀 TEST SEMPLICE PARAMETRI OTTIMIZZATI
======================================

Test semplice per verificare che i parametri default ottimizzati funzionino.
"""

import requests
import json

def test_simple():
    """Test semplice dei parametri ottimizzati"""
    base_url = "http://localhost:8000"
    
    print("🚀 TEST PARAMETRI OTTIMIZZATI")
    print("=" * 40)
    
    # Test con parametri di default (ottimizzati)
    payload = {
        "autoclave_id": 3  # Autoclave Compact
    }
    
    try:
        print("📋 Chiamata API con parametri default ottimizzati...")
        response = requests.post(
            f"{base_url}/api/batch_nesting/solve",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Aumentato timeout a 60 secondi
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            metrics = result.get('metrics', {})
            efficiency = metrics.get('area_utilization_pct', 0)
            positioned = metrics.get('pieces_positioned', 0)
            excluded = metrics.get('pieces_excluded', 0)
            algorithm = metrics.get('algorithm_status', 'UNKNOWN')
            
            print(f"✅ SUCCESSO!")
            print(f"   📊 Efficienza: {efficiency:.1f}%")
            print(f"   🔧 Tool posizionati: {positioned}")
            print(f"   ❌ Tool esclusi: {excluded}")
            print(f"   ⚙️ Algoritmo: {algorithm}")
            
            if efficiency > 30:
                print(f"   🎯 OTTIMO! Efficienza > 30%")
            elif efficiency > 15:
                print(f"   ✅ BUONO! Efficienza > 15%")
            else:
                print(f"   ⚠️ Migliorabile: efficienza < 15%")
                
        else:
            print(f"❌ ERRORE HTTP: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Dettaglio: {error_detail.get('detail', 'N/A')}")
            except:
                print(f"   Testo: {response.text[:200]}...")
                
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: La richiesta ha impiegato troppo tempo")
    except requests.exceptions.ConnectionError:
        print("❌ CONNESSIONE: Impossibile connettersi al server")
    except Exception as e:
        print(f"❌ ERRORE: {e}")
    
    print("\n🎯 PARAMETRI DEFAULT OTTIMIZZATI:")
    print("   • padding_mm = 1")
    print("   • min_distance_mm = 1")
    print("   • vacuum_lines_capacity = 20")
    print("   • allow_heuristic = True")

if __name__ == "__main__":
    test_simple() 