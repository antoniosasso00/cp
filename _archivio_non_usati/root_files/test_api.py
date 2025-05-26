#!/usr/bin/env python3
"""
Script di test per verificare le API del backend
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_database_info():
    """Test dell'endpoint per ottenere informazioni sul database"""
    print("🔍 Test: Informazioni Database...")
    try:
        response = requests.get(f"{BASE_URL}/admin/database/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database info: {data['total_tables']} tabelle, {data['total_records']} record totali")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return False

def test_backup():
    """Test dell'endpoint per il backup del database"""
    print("💾 Test: Backup Database...")
    try:
        response = requests.get(f"{BASE_URL}/admin/backup")
        if response.status_code == 200:
            # Salva il file di backup
            with open("test_backup.json", "wb") as f:
                f.write(response.content)
            print("✅ Backup creato con successo: test_backup.json")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return False

def test_reset():
    """Test dell'endpoint per il reset del database"""
    print("🗑️ Test: Reset Database...")
    try:
        # Test con conferma sbagliata
        response = requests.post(
            f"{BASE_URL}/admin/database/reset",
            json={"confirmation": "wrong"}
        )
        if response.status_code == 400:
            print("✅ Conferma sbagliata correttamente rifiutata")
        else:
            print(f"❌ Errore: doveva rifiutare la conferma sbagliata")
            return False
        
        # Test con conferma corretta
        response = requests.post(
            f"{BASE_URL}/admin/database/reset",
            json={"confirmation": "reset"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reset completato: {data['total_deleted_records']} record eliminati")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🚀 Avvio test delle API del backend...\n")
    
    tests = [
        ("Informazioni Database", test_database_info),
        ("Backup Database", test_backup),
        ("Reset Database", test_reset),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'='*50}")
    
    print(f"\n🏁 Risultati finali:")
    print("-" * 30)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotale: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 Tutti i test sono passati!")
        sys.exit(0)
    else:
        print("⚠️ Alcuni test sono falliti")
        sys.exit(1)

if __name__ == "__main__":
    main() 