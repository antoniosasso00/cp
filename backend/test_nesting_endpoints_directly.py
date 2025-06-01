#!/usr/bin/env python3
"""
Test diretto degli endpoint del nesting attraverso FastAPI TestClient
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
import json

def test_nesting_endpoints():
    """Testa tutti gli endpoint del nesting"""
    print("🚀 TEST ENDPOINT NESTING - CARBON PILOT")
    print("=" * 50)
    
    client = TestClient(app)
    
    # 1. Test endpoint health check nesting
    print("\n🔍 1. TEST HEALTH CHECK NESTING")
    print("-" * 35)
    
    try:
        response = client.get("/v1/nesting/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Status: {data.get('status', 'N/A')}")
            print(f"   ODL Statistiche: {data.get('statistics', {})}")
            if data.get('issues'):
                print(f"   Problemi: {len(data['issues'])}")
                for issue in data['issues']:
                    print(f"     - {issue}")
        else:
            print(f"❌ Errore: {response.text}")
    except Exception as e:
        print(f"❌ Eccezione: {e}")
    
    # 2. Test endpoint dati nesting
    print("\n📊 2. TEST ENDPOINT DATI NESTING")
    print("-" * 35)
    
    try:
        response = client.get("/v1/nesting/data")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status Sistema: {data.get('status', 'N/A')}")
            print(f"   ODL in attesa cura: {len(data.get('odl_in_attesa_cura', []))}")
            print(f"   Autoclavi disponibili: {len(data.get('autoclavi_disponibili', []))}")
            print(f"   Statistiche: {data.get('statistiche', {})}")
            
            # Mostra primo ODL
            if data.get('odl_in_attesa_cura'):
                odl = data['odl_in_attesa_cura'][0]
                print(f"   Primo ODL: #{odl['id']} - {odl.get('parte', {}).get('descrizione_breve', 'N/A')}")
                
            # Mostra prima autoclave
            if data.get('autoclavi_disponibili'):
                autoclave = data['autoclavi_disponibili'][0]
                print(f"   Prima Autoclave: {autoclave['nome']} ({autoclave['codice']})")
        else:
            print(f"❌ Errore: {response.text}")
    except Exception as e:
        print(f"❌ Eccezione: {e}")
    
    # 3. Test endpoint ODL base
    print("\n📋 3. TEST ENDPOINT ODL BASE")
    print("-" * 30)
    
    try:
        response = client.get("/v1/odl?limit=5")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ODL totali (primi 5): {len(data)}")
            
            odl_attesa_cura = [odl for odl in data if odl.get('status') == 'Attesa Cura']
            print(f"   ODL in 'Attesa Cura': {len(odl_attesa_cura)}")
        else:
            print(f"❌ Errore: {response.text}")
    except Exception as e:
        print(f"❌ Eccezione: {e}")
    
    # 4. Test endpoint autoclavi base
    print("\n🏭 4. TEST ENDPOINT AUTOCLAVI BASE")
    print("-" * 35)
    
    try:
        response = client.get("/v1/autoclavi")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Autoclavi totali: {len(data)}")
            
            autoclavi_disponibili = [ac for ac in data if ac.get('stato') == 'DISPONIBILE']
            print(f"   Autoclavi DISPONIBILI: {len(autoclavi_disponibili)}")
        else:
            print(f"❌ Errore: {response.text}")
    except Exception as e:
        print(f"❌ Eccezione: {e}")
    
    # 5. Test generazione nesting con dati reali
    print("\n🔄 5. TEST GENERAZIONE NESTING")
    print("-" * 32)
    
    try:
        # Primo ottieni ODL e autoclavi
        odl_response = client.get("/v1/odl")
        autoclave_response = client.get("/v1/autoclavi")
        
        if odl_response.status_code == 200 and autoclave_response.status_code == 200:
            odl_data = odl_response.json()
            autoclave_data = autoclave_response.json()
            
            # Filtra ODL in attesa cura
            odl_attesa = [odl for odl in odl_data if odl.get('status') == 'Attesa Cura']
            autoclavi_disp = [ac for ac in autoclave_data if ac.get('stato') == 'DISPONIBILE']
            
            if odl_attesa and autoclavi_disp:
                # Prepara payload
                payload = {
                    "odl_ids": [str(odl['id']) for odl in odl_attesa[:3]],  # Primi 3 ODL
                    "autoclave_ids": [str(ac['id']) for ac in autoclavi_disp[:1]],  # Prima autoclave
                    "parametri": {
                        "padding_mm": 10,
                        "min_distance_mm": 8,
                        "priorita_area": True
                    }
                }
                
                print(f"   Payload: {len(payload['odl_ids'])} ODL, {len(payload['autoclave_ids'])} autoclavi")
                
                response = client.post("/v1/nesting/genera", json=payload)
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Nesting generato!")
                    print(f"   Batch ID: {result.get('batch_id', 'N/A')}")
                    print(f"   Success: {result.get('success', False)}")
                    print(f"   Message: {result.get('message', 'N/A')}")
                    print(f"   Tool posizionati: {len(result.get('positioned_tools', []))}")
                    print(f"   ODL esclusi: {len(result.get('excluded_odls', []))}")
                else:
                    print(f"❌ Errore generazione: {response.text}")
            else:
                print("⚠️ Dati insufficienti per test generazione")
                print(f"   ODL in attesa: {len(odl_attesa)}")
                print(f"   Autoclavi disponibili: {len(autoclavi_disp)}")
        else:
            print("❌ Impossibile ottenere dati per test generazione")
    except Exception as e:
        print(f"❌ Eccezione: {e}")
    
    # 6. Test funzioni admin database
    print("\n🔧 6. TEST FUNZIONI ADMIN DATABASE")
    print("-" * 38)
    
    try:
        # Test status database
        response = client.get("/v1/admin/database/status")
        print(f"Database Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database Status: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Database Status Error: {response.text}")
    except Exception as e:
        print(f"❌ Admin Test Exception: {e}")
    
    print(f"\n✅ Test endpoint completato!")

if __name__ == "__main__":
    test_nesting_endpoints() 