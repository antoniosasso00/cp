#!/usr/bin/env python3
"""
Script per testare il cambio di stato di un ODL e verificare il tracking automatico.
"""

import requests
import json
import time

def test_change_status():
    base_url = "http://localhost:8000"
    odl_id = 1
    
    print("🔄 Test Cambio Stato ODL")
    print("=" * 50)
    
    # 1. Stato iniziale
    print(f"📊 Stato iniziale ODL #{odl_id}:")
    response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/progress")
    if response.status_code == 200:
        initial_data = response.json()
        print(f"   Status: {initial_data.get('status', 'N/A')}")
        print(f"   Timestamps: {len(initial_data.get('timestamps', []))}")
        print(f"   Has Timeline Data: {initial_data.get('has_timeline_data', False)}")
    else:
        print(f"   Errore: {response.text}")
        return
    
    # 2. Cambio stato
    new_status = "Laminazione"
    print(f"\n🔄 Cambio stato a '{new_status}':")
    
    payload = {"new_status": new_status}
    response = requests.patch(
        f"{base_url}/api/v1/odl/{odl_id}/status",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print(f"   ✅ Cambio stato riuscito")
        updated_odl = response.json()
        print(f"   Nuovo status: {updated_odl.get('status', 'N/A')}")
    else:
        print(f"   ❌ Errore nel cambio stato: {response.text}")
        return
    
    # 3. Attendi un momento per il processing
    print(f"\n⏳ Attendo 2 secondi per il processing...")
    time.sleep(2)
    
    # 4. Verifica stato aggiornato
    print(f"\n📊 Stato dopo il cambio:")
    response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/progress")
    if response.status_code == 200:
        updated_data = response.json()
        print(f"   Status: {updated_data.get('status', 'N/A')}")
        print(f"   Timestamps: {len(updated_data.get('timestamps', []))}")
        print(f"   Has Timeline Data: {updated_data.get('has_timeline_data', False)}")
        
        # Confronta con stato iniziale
        initial_timestamps = len(initial_data.get('timestamps', []))
        updated_timestamps = len(updated_data.get('timestamps', []))
        
        if updated_timestamps > initial_timestamps:
            print(f"   ✅ Nuovo timestamp registrato! ({initial_timestamps} → {updated_timestamps})")
            print(f"   ✅ Tracking automatico funzionante!")
        else:
            print(f"   ⚠️  Nessun nuovo timestamp ({initial_timestamps} → {updated_timestamps})")
    else:
        print(f"   Errore: {response.text}")
    
    # 5. Mostra timeline completa
    print(f"\n📅 Timeline completa:")
    response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/timeline")
    if response.status_code == 200:
        timeline_data = response.json()
        logs = timeline_data.get('logs', [])
        print(f"   Eventi totali: {len(logs)}")
        
        # Mostra gli ultimi 3 eventi
        for i, log in enumerate(logs[-3:]):
            evento = log.get('evento', 'N/A')
            timestamp = log.get('timestamp', 'N/A')
            responsabile = log.get('responsabile', 'N/A')
            print(f"   {len(logs)-2+i}. {evento} ({responsabile}) - {timestamp}")
    else:
        print(f"   Errore timeline: {response.text}")
    
    print(f"\n🎯 Test completato!")

if __name__ == "__main__":
    test_change_status() 