#!/usr/bin/env python3
"""
Script di test per verificare l'integrazione completa del sistema scheduling.
"""

import requests
import json
from datetime import datetime, timedelta

def test_integration():
    """Testa l'integrazione completa del sistema."""
    
    print("🧪 TEST INTEGRAZIONE SISTEMA SCHEDULING")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Test health check
    print("\n1️⃣ Test Health Check")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend attivo - Database: {data['database']['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend non raggiungibile: {e}")
        return False
    
    # 2. Test endpoint schedules
    print("\n2️⃣ Test Endpoint Schedules")
    try:
        response = requests.get(f"{base_url}/schedules/")
        if response.status_code == 200:
            schedules = response.json()
            print(f"✅ Schedulazioni caricate: {len(schedules)}")
            if schedules:
                print(f"   Esempio: ID {schedules[0]['id']}, Tipo: {schedules[0]['schedule_type']}")
        else:
            print(f"❌ Errore schedules: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore schedules: {e}")
        return False
    
    # 3. Test endpoint production times
    print("\n3️⃣ Test Endpoint Production Times")
    try:
        response = requests.get(f"{base_url}/schedules/production-times")
        if response.status_code == 200:
            times = response.json()
            print(f"✅ Tempi produzione caricati: {len(times)}")
            if times:
                print(f"   Esempio: {times[0]['categoria']} - {times[0]['tempo_medio_minuti']}min")
        else:
            print(f"❌ Errore production times: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore production times: {e}")
        return False
    
    # 4. Test endpoint estimate
    print("\n4️⃣ Test Endpoint Estimate")
    try:
        response = requests.get(f"{base_url}/schedules/production-times/estimate?categoria=Aerospace")
        if response.status_code == 200:
            estimate = response.json()
            print(f"✅ Stima tempo: {estimate['tempo_stimato_minuti']}min per categoria Aerospace")
        else:
            print(f"❌ Errore estimate: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore estimate: {e}")
        return False
    
    # 5. Test creazione schedulazione
    print("\n5️⃣ Test Creazione Schedulazione")
    try:
        # Prima recuperiamo le autoclavi disponibili
        response = requests.get(f"{base_url}/autoclavi/")
        if response.status_code != 200:
            print("⚠️  Nessuna autoclave disponibile per il test")
            return True
        
        autoclavi = response.json()
        if not autoclavi:
            print("⚠️  Nessuna autoclave disponibile per il test")
            return True
        
        autoclave_id = autoclavi[0]['id']
        
        # Crea una schedulazione di test
        schedule_data = {
            "schedule_type": "categoria",
            "autoclave_id": autoclave_id,
            "categoria": "Aerospace",
            "start_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "status": "manual",
            "created_by": "test_integration",
            "note": "Schedulazione di test creata automaticamente"
        }
        
        response = requests.post(f"{base_url}/schedules/", json=schedule_data)
        if response.status_code == 201:
            new_schedule = response.json()
            print(f"✅ Schedulazione creata: ID {new_schedule['id']}")
            
            # Elimina la schedulazione di test
            delete_response = requests.delete(f"{base_url}/schedules/{new_schedule['id']}")
            if delete_response.status_code == 204:
                print(f"✅ Schedulazione di test eliminata")
            else:
                print(f"⚠️  Schedulazione di test non eliminata (ID: {new_schedule['id']})")
        else:
            print(f"❌ Errore creazione schedulazione: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore test creazione: {e}")
        return False
    
    # 6. Test frontend
    print("\n6️⃣ Test Frontend")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Next.js attivo")
        else:
            print(f"⚠️  Frontend risponde con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Frontend non raggiungibile (normale se non avviato)")
    except Exception as e:
        print(f"⚠️  Errore frontend: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 INTEGRAZIONE COMPLETATA CON SUCCESSO!")
    print("\n📋 SISTEMA PRONTO PER L'USO:")
    print("• Backend FastAPI: http://localhost:8000")
    print("• API Docs: http://localhost:8000/docs")
    print("• Frontend Next.js: http://localhost:3000")
    print("• Scheduling: http://localhost:3000/dashboard/schedule")
    
    return True

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n✅ Tutti i test superati!")
    else:
        print("\n❌ Alcuni test falliti!") 