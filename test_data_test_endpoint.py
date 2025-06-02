#!/usr/bin/env python3
"""
Test endpoint data-test
"""
import requests
import json

def test_data_test_endpoint():
    """Testa l'endpoint data-test"""
    
    print("🧪 TEST ENDPOINT /batch_nesting/data-test")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/v1/batch_nesting/data-test", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successo!")
            print(f"📊 ODL recuperati: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"📊 Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
            print(f"📊 Status: {data.get('status')}")
            
            # Mostra dettagli primo ODL se presente
            odl_list = data.get('odl_in_attesa_cura', [])
            if odl_list:
                first_odl = odl_list[0]
                print(f"\n📋 Primo ODL:")
                print(f"   ID: {first_odl.get('id')}")
                print(f"   Status: {first_odl.get('status')}")
                print(f"   Parte: {first_odl.get('parte', {}).get('part_number', 'None')}")
                print(f"   Tool: {first_odl.get('tool', {}).get('part_number_tool', 'None')}")
        else:
            print(f"❌ Errore: {response.text}")
            
    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")

if __name__ == "__main__":
    test_data_test_endpoint() 