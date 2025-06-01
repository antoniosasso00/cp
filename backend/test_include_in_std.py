#!/usr/bin/env python3
"""
Test per verificare il funzionamento del campo include_in_std negli ODL
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001/api/v1"

def test_odl_include_in_std():
    """Test del nuovo campo include_in_std"""
    
    print("🧪 Test del campo include_in_std negli ODL")
    print("=" * 50)
    
    # 1. Test GET /odl senza filtri
    print("\n1. Test GET /odl senza filtri...")
    response = requests.get(f"{BASE_URL}/odl?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        odl_list = response.json()
        print(f"ODL trovati: {len(odl_list)}")
        
        if odl_list:
            first_odl = odl_list[0]
            print(f"Primo ODL: ID={first_odl.get('id')}, include_in_std={first_odl.get('include_in_std')}")
            
            # 2. Test GET /odl con filtro include_in_std=true
            print("\n2. Test GET /odl con filtro include_in_std=true...")
            response_filtered = requests.get(f"{BASE_URL}/odl?include_in_std=true&limit=5")
            print(f"Status: {response_filtered.status_code}")
            
            if response_filtered.status_code == 200:
                odl_filtered = response_filtered.json()
                print(f"ODL con include_in_std=true: {len(odl_filtered)}")
            
            # 3. Test PUT per aggiornare include_in_std
            odl_id = first_odl['id']
            current_value = first_odl.get('include_in_std', True)
            new_value = not current_value
            
            print(f"\n3. Test PUT per aggiornare ODL {odl_id}...")
            print(f"Valore attuale: {current_value} -> Nuovo valore: {new_value}")
            
            update_data = {"include_in_std": new_value}
            response_update = requests.put(f"{BASE_URL}/odl/{odl_id}", json=update_data)
            print(f"Status: {response_update.status_code}")
            
            if response_update.status_code == 200:
                updated_odl = response_update.json()
                print(f"Aggiornamento riuscito: include_in_std={updated_odl.get('include_in_std')}")
                
                # 4. Ripristina il valore originale
                print(f"\n4. Ripristino valore originale...")
                restore_data = {"include_in_std": current_value}
                response_restore = requests.put(f"{BASE_URL}/odl/{odl_id}", json=restore_data)
                print(f"Status: {response_restore.status_code}")
                
                if response_restore.status_code == 200:
                    print("✅ Valore ripristinato con successo")
                else:
                    print("❌ Errore nel ripristino")
            else:
                print("❌ Errore nell'aggiornamento")
        else:
            print("⚠️ Nessun ODL trovato nel database")
    else:
        print(f"❌ Errore nella richiesta: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        test_odl_include_in_std()
        print("\n✅ Test completato!")
    except Exception as e:
        print(f"\n❌ Errore durante il test: {e}") 