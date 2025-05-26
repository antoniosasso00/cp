#!/usr/bin/env python3
"""
Script per creare dati di test nel database CarbonPilot
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def create_test_data():
    print("🏗️ Creazione dati di test per CarbonPilot")
    print("=" * 50)
    
    # 1. Crea catalogo
    print("\n📚 Creando catalogo...")
    catalogo_data = {
        "part_number": "TEST001",
        "descrizione": "Parte di test per laminazione",
        "categoria": "Compositi",
        "sotto_categoria": "Carbonio",
        "attivo": True,
        "note": "Parte creata per test"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/catalogo/", json=catalogo_data)
        if response.status_code == 201:
            print("   ✅ Catalogo creato con successo")
        else:
            print(f"   ⚠️ Catalogo già esistente o errore: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Errore creazione catalogo: {e}")
    
    # 2. Crea tool
    print("\n🔧 Creando tool...")
    tool_data = {
        "part_number_tool": "TOOL001",
        "descrizione": "Tool di test per laminazione",
        "lunghezza_piano": 1000,
        "larghezza_piano": 500,
        "peso": 50.0,
        "materiale": "Alluminio",
        "disponibile": True
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/tools", json=tool_data)
        if response.status_code == 201:
            print("   ✅ Tool creato con successo")
            tool_id = response.json()["id"]
        else:
            print(f"   ⚠️ Tool già esistente o errore: {response.status_code}")
            # Prova a recuperare il tool esistente
            tools_response = requests.get(f"{API_BASE_URL}/tools")
            if tools_response.status_code == 200:
                tools = tools_response.json()
                tool_id = tools[0]["id"] if tools else 1
            else:
                tool_id = 1
    except Exception as e:
        print(f"   ❌ Errore creazione tool: {e}")
        tool_id = 1
    
    # 3. Crea parte
    print("\n🧩 Creando parte...")
    parte_data = {
        "part_number": "TEST001",
        "descrizione_breve": "Parte di test",
        "num_valvole_richieste": 4,
        "note_produzione": "Parte per test laminazione",
        "tool_ids": [tool_id]
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/parti/", json=parte_data)
        if response.status_code == 201:
            print("   ✅ Parte creata con successo")
            parte_id = response.json()["id"]
        else:
            print(f"   ⚠️ Parte già esistente o errore: {response.status_code}")
            # Prova a recuperare la parte esistente
            parti_response = requests.get(f"{API_BASE_URL}/parti")
            if parti_response.status_code == 200:
                parti = parti_response.json()
                parte_id = parti[0]["id"] if parti else 1
            else:
                parte_id = 1
    except Exception as e:
        print(f"   ❌ Errore creazione parte: {e}")
        parte_id = 1
    
    # 4. Crea ODL di test
    print("\n📋 Creando ODL di test...")
    
    odl_test_cases = [
        {
            "parte_id": parte_id,
            "tool_id": tool_id,
            "priorita": 5,
            "status": "Preparazione",
            "note": "ODL di test per laminatore"
        },
        {
            "parte_id": parte_id,
            "tool_id": tool_id,
            "priorita": 3,
            "status": "Laminazione",
            "note": "ODL di test in laminazione"
        },
        {
            "parte_id": parte_id,
            "tool_id": tool_id,
            "priorita": 7,
            "status": "Attesa Cura",
            "note": "ODL di test per autoclavista"
        }
    ]
    
    created_odl_ids = []
    
    for i, odl_data in enumerate(odl_test_cases, 1):
        try:
            response = requests.post(f"{API_BASE_URL}/odl", json=odl_data)
            if response.status_code == 201:
                odl_id = response.json()["id"]
                created_odl_ids.append(odl_id)
                print(f"   ✅ ODL {i} creato con successo (ID: {odl_id}, Status: {odl_data['status']})")
            else:
                print(f"   ❌ Errore creazione ODL {i}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Errore creazione ODL {i}: {e}")
    
    print(f"\n📊 Riepilogo creazione dati")
    print("=" * 50)
    print(f"✅ ODL creati: {len(created_odl_ids)}")
    if created_odl_ids:
        print(f"   IDs: {created_odl_ids}")
    
    return created_odl_ids

def test_status_updates(odl_ids):
    """Testa gli aggiornamenti di stato con ODL reali"""
    if not odl_ids:
        print("⚠️ Nessun ODL disponibile per testare gli aggiornamenti di stato")
        return
    
    print(f"\n🔄 Test aggiornamenti stato ODL")
    print("=" * 50)
    
    # Test aggiornamento laminatore
    if len(odl_ids) >= 1:
        odl_id = odl_ids[0]
        print(f"\n🔧 Test aggiornamento stato laminatore (ODL {odl_id})")
        
        try:
            # Prima verifica lo stato attuale
            response = requests.get(f"{API_BASE_URL}/odl/{odl_id}")
            if response.status_code == 200:
                current_status = response.json()["status"]
                print(f"   Stato attuale: {current_status}")
                
                # Determina il prossimo stato valido
                if current_status == "Preparazione":
                    new_status = "Laminazione"
                elif current_status == "Laminazione":
                    new_status = "Attesa Cura"
                else:
                    print(f"   ⚠️ ODL in stato {current_status} non gestibile dal laminatore")
                    new_status = None
                
                if new_status:
                    # Testa l'aggiornamento
                    update_response = requests.patch(
                        f"{API_BASE_URL}/odl/{odl_id}/laminatore-status?new_status={new_status}"
                    )
                    
                    if update_response.status_code == 200:
                        updated_odl = update_response.json()
                        print(f"   ✅ Aggiornamento riuscito: {current_status} → {updated_odl['status']}")
                    else:
                        print(f"   ❌ Errore aggiornamento: {update_response.status_code} - {update_response.text}")
            
        except Exception as e:
            print(f"   ❌ Errore test laminatore: {e}")
    
    # Test aggiornamento autoclavista
    if len(odl_ids) >= 3:
        odl_id = odl_ids[2]  # ODL in "Attesa Cura"
        print(f"\n🔥 Test aggiornamento stato autoclavista (ODL {odl_id})")
        
        try:
            # Prima verifica lo stato attuale
            response = requests.get(f"{API_BASE_URL}/odl/{odl_id}")
            if response.status_code == 200:
                current_status = response.json()["status"]
                print(f"   Stato attuale: {current_status}")
                
                # Determina il prossimo stato valido
                if current_status == "Attesa Cura":
                    new_status = "Cura"
                elif current_status == "Cura":
                    new_status = "Finito"
                else:
                    print(f"   ⚠️ ODL in stato {current_status} non gestibile dall'autoclavista")
                    new_status = None
                
                if new_status:
                    # Testa l'aggiornamento
                    update_response = requests.patch(
                        f"{API_BASE_URL}/odl/{odl_id}/autoclavista-status?new_status={new_status}"
                    )
                    
                    if update_response.status_code == 200:
                        updated_odl = update_response.json()
                        print(f"   ✅ Aggiornamento riuscito: {current_status} → {updated_odl['status']}")
                    else:
                        print(f"   ❌ Errore aggiornamento: {update_response.status_code} - {update_response.text}")
            
        except Exception as e:
            print(f"   ❌ Errore test autoclavista: {e}")

def main():
    # Crea dati di test
    odl_ids = create_test_data()
    
    # Testa gli aggiornamenti di stato
    test_status_updates(odl_ids)
    
    print(f"\n🎯 Test completati!")
    print(f"🔗 Ora puoi testare l'interfaccia web:")
    print(f"   - Frontend: http://localhost:3000")
    print(f"   - Debug Page: http://localhost:3000/dashboard/test-debug")
    print(f"   - Laminatore: http://localhost:3000/dashboard/laminatore/produzione")
    print(f"   - Autoclavista: http://localhost:3000/dashboard/autoclavista/produzione")

if __name__ == "__main__":
    main() 