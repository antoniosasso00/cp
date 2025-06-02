#!/usr/bin/env python3
"""
Test per verificare il fix dell'attributo use_secondary_plane
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def test_server_health():
    """Testa se il server è attivo"""
    try:
        response = requests.get(f"http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server attivo - Database: {data.get('database', {}).get('status', 'N/A')}")
            return True
        return False
    except Exception as e:
        print(f"❌ Server non raggiungibile: {str(e)}")
        return False

def test_data_load():
    """Testa il caricamento dati"""
    try:
        response = requests.get(f"{API_BASE}/batch_nesting/data")
        if response.status_code == 200:
            data = response.json()
            odl_count = len(data.get('odl_in_attesa_cura', []))
            autoclave_count = len(data.get('autoclavi_disponibili', []))
            print(f"✅ Dati caricati: {odl_count} ODL, {autoclave_count} autoclavi")
            return odl_count > 0 and autoclave_count > 0
        return False
    except Exception as e:
        print(f"❌ Errore caricamento dati: {str(e)}")
        return False

def test_nesting_generation():
    """Testa la generazione nesting"""
    payload = {
        "odl_ids": ["1"],
        "autoclave_ids": ["1"],
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 8
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/batch_nesting/genera",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            message = data.get('message', '')
            
            print(f"✅ Risposta ricevuta:")
            print(f"   - Success: {success}")
            print(f"   - Message: {message}")
            print(f"   - Batch ID: {data.get('batch_id', 'N/A')}")
            
            # Verifica se l'errore use_secondary_plane è ancora presente
            if 'use_secondary_plane' in message:
                print("❌ ERRORE: Il problema use_secondary_plane persiste!")
                return False
            else:
                print("✅ Errore use_secondary_plane NON presente nella risposta")
                return True
        else:
            try:
                error_data = response.json()
                print(f"❌ Errore HTTP: {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ Errore HTTP: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def main():
    """Test principale"""
    print("🧪 TEST VERIFICA FIX use_secondary_plane")
    print("=" * 50)
    
    # Test 1: Server attivo
    if not test_server_health():
        print("❌ FALLITO: Server non raggiungibile")
        return
    
    # Test 2: Dati disponibili
    if not test_data_load():
        print("❌ FALLITO: Dati non disponibili")
        return
    
    # Test 3: Generazione nesting (il test principale)
    print("\n🔧 Test generazione nesting...")
    result = test_nesting_generation()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 SUCCESS: Il fix use_secondary_plane funziona correttamente!")
    else:
        print("❌ FAILED: Il problema use_secondary_plane persiste")

if __name__ == "__main__":
    main() 