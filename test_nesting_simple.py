#!/usr/bin/env python3
"""
Test semplificato per debug del modulo Nesting
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_simple_nesting():
    """Test semplificato con parametri più permissivi"""
    
    print("🔧 TEST DEBUG NESTING SEMPLIFICATO")
    print("=" * 50)
    
    # Test con parametri molto permissivi
    nesting_data = {
        "odl_ids": ["1"],  
        "autoclave_ids": ["1"],  
        "parametri": {
            "padding_mm": 5,      # Ridotto da 20 a 5
            "min_distance_mm": 5, # Ridotto da 15 a 5
            "priorita_area": False,  # Massimizza numero ODL invece di area
            "accorpamento_odl": False
        }
    }
    
    print("📋 Parametri test:")
    print(f"   - ODL IDs: {nesting_data['odl_ids']}")
    print(f"   - Autoclave IDs: {nesting_data['autoclave_ids']}")
    print(f"   - Padding: {nesting_data['parametri']['padding_mm']}mm")
    print(f"   - Distanza min: {nesting_data['parametri']['min_distance_mm']}mm")
    print(f"   - Priorità area: {nesting_data['parametri']['priorita_area']}")
    
    try:
        response = requests.post(f"{BASE_URL}/nesting/genera", json=nesting_data)
        
        print(f"\n🔍 Risposta API:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Successo!")
            print(f"   📝 Batch ID: {result.get('batch_id')}")
            print(f"   📝 ODL posizionati: {result.get('odl_count')}")
            print(f"   📝 Efficienza: {result.get('efficiency', 0):.1f}%")
            
            # Verifica dettagli batch
            batch_id = result.get('batch_id')
            if batch_id:
                batch_response = requests.get(f"{BASE_URL}/batch_nesting/{batch_id}/full")
                if batch_response.status_code == 200:
                    batch_details = batch_response.json()
                    print(f"\n📊 Dettagli batch:")
                    print(f"   - Nome: {batch_details.get('nome')}")
                    print(f"   - ODL inclusi: {len(batch_details.get('odl_ids', []))}")
                    print(f"   - Tool positions: {len(batch_details.get('configurazione_json', {}).get('tool_positions', []))}")
                    print(f"   - ODL esclusi: {len(batch_details.get('odl_esclusi', []))}")
                    print(f"   - Note: {batch_details.get('note', 'N/A')}")
                    
                    return True
        else:
            print(f"   ❌ Errore:")
            try:
                error = response.json()
                print(f"   📝 {error}")
            except:
                print(f"   📝 {response.text}")
    
    except Exception as e:
        print(f"   💥 Eccezione: {e}")
    
    return False

if __name__ == "__main__":
    success = test_simple_nesting()
    if success:
        print("\n✅ Test debug completato con successo!")
    else:
        print("\n❌ Test debug fallito!") 