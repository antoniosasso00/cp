#!/usr/bin/env python3
"""
Test semplice delle funzioni admin
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/admin"

def test_database_info():
    """Test database info"""
    print("🔍 Test database info...")
    try:
        response = requests.get(f"{BASE_URL}/database/info")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OK: {data['total_tables']} tabelle, {data['total_records']} record")
            return True
        else:
            print(f"❌ Errore: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

def test_backup():
    """Test backup"""
    print("\n🔍 Test backup...")
    try:
        response = requests.get(f"{BASE_URL}/backup")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Backup OK: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Errore: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

def test_reset():
    """Test reset"""
    print("\n🔍 Test reset...")
    try:
        # Prima prova con parola chiave sbagliata
        response = requests.post(
            f"{BASE_URL}/database/reset",
            json={"confirmation": "wrong"}
        )
        print(f"Status (wrong): {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Protezione OK")
        
        # Ora prova con parola chiave corretta
        response = requests.post(
            f"{BASE_URL}/database/reset",
            json={"confirmation": "reset"}
        )
        print(f"Status (reset): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reset OK: {data.get('total_deleted_records', 0)} record eliminati")
            return True
        else:
            print(f"❌ Errore: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 TEST FUNZIONI ADMIN")
    print("=" * 30)
    
    info_ok = test_database_info()
    backup_ok = test_backup()
    reset_ok = test_reset()
    
    print("\n" + "=" * 30)
    print("📋 RISULTATI:")
    print(f"  🔍 Database Info: {'✅ OK' if info_ok else '❌ ERRORE'}")
    print(f"  💾 Backup: {'✅ OK' if backup_ok else '❌ ERRORE'}")
    print(f"  🗑️  Reset: {'✅ OK' if reset_ok else '❌ ERRORE'}")
    
    if all([info_ok, backup_ok, reset_ok]):
        print("\n🎉 Tutti i test superati!")
    else:
        print("\n⚠️  Alcuni test falliti.") 