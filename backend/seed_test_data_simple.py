#!/usr/bin/env python3
"""
Script semplice per creare dati di test per ODL in attesa di nesting
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def create_test_odl():
    """Crea ODL di test in stato 'Attesa Cura'"""
    
    # Dati di test per ODL
    test_odl_data = [
        {
            "parte_id": 1,
            "tool_id": 1,
            "priorita": 5,
            "status": "Attesa Cura",
            "note": "ODL di test per nesting manuale - Priorità alta"
        },
        {
            "parte_id": 2,
            "tool_id": 2,
            "priorita": 3,
            "status": "Attesa Cura",
            "note": "ODL di test per nesting manuale - Priorità media"
        },
        {
            "parte_id": 3,
            "tool_id": 3,
            "priorita": 1,
            "status": "Attesa Cura",
            "note": "ODL di test per nesting manuale - Priorità bassa"
        },
        {
            "parte_id": 1,
            "tool_id": 2,
            "priorita": 4,
            "status": "Attesa Cura",
            "note": "ODL di test per nesting manuale - Priorità alta"
        },
        {
            "parte_id": 2,
            "tool_id": 1,
            "priorita": 2,
            "status": "Attesa Cura",
            "note": "ODL di test per nesting manuale - Priorità bassa"
        }
    ]
    
    created_odl = []
    
    for i, odl_data in enumerate(test_odl_data):
        try:
            print(f"🔄 Creazione ODL di test {i+1}/5...")
            
            response = requests.post(f"{BASE_URL}/odl/", json=odl_data, timeout=10)
            
            if response.status_code in [200, 201]:
                odl = response.json()
                created_odl.append(odl)
                print(f"✅ ODL #{odl['id']} creato - Parte: {odl['parte']['part_number']}, Priorità: {odl['priorita']}")
            else:
                print(f"❌ Errore nella creazione ODL {i+1}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Errore nella creazione ODL {i+1}: {e}")
    
    return created_odl

def check_backend():
    """Verifica che il backend sia raggiungibile"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend raggiungibile")
            return True
        else:
            print(f"❌ Backend risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend non raggiungibile: {e}")
        return False

def check_existing_data():
    """Verifica che esistano parti e tool necessari"""
    try:
        # Verifica parti
        response = requests.get(f"{BASE_URL}/parts/", timeout=10)
        if response.status_code == 200:
            parts = response.json()
            print(f"📦 Parti disponibili: {len(parts)}")
            if len(parts) < 3:
                print("⚠️ Servono almeno 3 parti per i test")
                return False
        else:
            print(f"❌ Errore nel recupero parti: {response.status_code}")
            return False
            
        # Verifica tool
        response = requests.get(f"{BASE_URL}/tools/", timeout=10)
        if response.status_code == 200:
            tools = response.json()
            print(f"🔧 Tool disponibili: {len(tools)}")
            if len(tools) < 3:
                print("⚠️ Servono almeno 3 tool per i test")
                return False
        else:
            print(f"❌ Errore nel recupero tool: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Errore nella verifica dati: {e}")
        return False

def check_pending_odl():
    """Verifica ODL in attesa di nesting"""
    try:
        response = requests.get(f"{BASE_URL}/odl/pending-nesting", timeout=10)
        if response.status_code == 200:
            odl_list = response.json()
            print(f"📋 ODL in attesa di nesting: {len(odl_list)}")
            
            if odl_list:
                print("   Primi 3 ODL:")
                for odl in odl_list[:3]:
                    print(f"     #{odl['id']} - {odl['parte']['part_number']} - P{odl['priorita']} - {odl['status']}")
            
            return odl_list
        else:
            print(f"❌ Errore nel recupero ODL pending: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Errore nella verifica ODL pending: {e}")
        return None

def main():
    """Funzione principale"""
    print("🧪 Setup dati di test per Nesting Manuale")
    print("=" * 50)
    
    # Verifica backend
    if not check_backend():
        print("❌ Backend non disponibile. Avvia il backend con: uvicorn main:app --reload")
        sys.exit(1)
    
    print()
    
    # Verifica dati esistenti
    if not check_existing_data():
        print("❌ Dati di base mancanti. Esegui prima il seeding del database.")
        sys.exit(1)
    
    print()
    
    # Verifica ODL esistenti
    existing_odl = check_pending_odl()
    
    print()
    
    # Crea ODL di test se necessario
    if not existing_odl or len(existing_odl) < 3:
        print("🔄 Creazione ODL di test...")
        created_odl = create_test_odl()
        
        if created_odl:
            print(f"\n✅ Creati {len(created_odl)} ODL di test")
        else:
            print("\n❌ Nessun ODL creato")
    else:
        print("✅ ODL di test già presenti")
    
    print()
    
    # Verifica finale
    final_odl = check_pending_odl()
    if final_odl and len(final_odl) >= 3:
        print("🎉 Setup completato! Ora puoi testare l'interfaccia di nesting manuale.")
        print(f"   Vai su: http://localhost:3000/dashboard/nesting")
        print(f"   ODL disponibili per test: {len(final_odl)}")
    else:
        print("❌ Setup non completato correttamente")
        sys.exit(1)

if __name__ == "__main__":
    main() 