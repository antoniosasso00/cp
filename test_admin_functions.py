#!/usr/bin/env python3
"""
Script per testare le funzioni di amministrazione del database
"""

import requests
import json
import os
import time
from datetime import datetime

# URL base dell'API
BASE_URL = "http://localhost:8000/api/v1/admin"

def test_database_info():
    """Testa l'endpoint di informazioni database"""
    print("🔍 Test informazioni database...")
    
    try:
        response = requests.get(f"{BASE_URL}/database/info")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database info OK: {data['total_tables']} tabelle, {data['total_records']} record")
            return True
        else:
            print(f"❌ Errore: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore: Impossibile connettersi al server. Assicurati che sia in esecuzione su porta 8000")
        return False
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

def test_backup_export():
    """Testa l'endpoint di esportazione database"""
    print("\n🔍 Test esportazione database...")
    
    try:
        response = requests.get(f"{BASE_URL}/backup")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Salva il backup per testare il restore
            content_disposition = response.headers.get('Content-Disposition', '')
            filename = 'test_backup.json'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Backup creato: {filename} ({len(response.content)} bytes)")
            return True, filename
        else:
            print(f"❌ Errore backup: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Errore backup: {str(e)}")
        return False, None

def test_restore(backup_filename):
    """Testa l'endpoint di ripristino database"""
    print(f"\n🔍 Test ripristino database da {backup_filename}...")
    
    try:
        if not os.path.exists(backup_filename):
            print(f"❌ File backup non trovato: {backup_filename}")
            return False
        
        with open(backup_filename, 'rb') as f:
            files = {'backup_file': (backup_filename, f, 'application/json')}
            response = requests.post(f"{BASE_URL}/restore", files=files)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ripristino OK: {data.get('total_tables', 0)} tabelle ripristinate")
            if data.get('errors'):
                print(f"⚠️  Errori: {len(data['errors'])}")
                for error in data['errors'][:3]:  # Mostra solo i primi 3 errori
                    print(f"  - {error}")
            return True
        else:
            print(f"❌ Errore ripristino: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore ripristino: {str(e)}")
        return False

def test_reset():
    """Testa l'endpoint di reset database"""
    print("\n🔍 Test reset database...")
    
    try:
        # Prima tenta senza la parola chiave corretta
        response = requests.post(
            f"{BASE_URL}/database/reset",
            json={"confirmation": "wrong"}
        )
        
        if response.status_code == 400:
            print("✅ Protezione reset funziona (rifiuta parola chiave errata)")
        else:
            print(f"⚠️  Protezione reset non funziona: {response.status_code}")
        
        # Ora testa con la parola chiave corretta
        response = requests.post(
            f"{BASE_URL}/database/reset",
            json={"confirmation": "reset"}
        )
        
        print(f"Status reset: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reset OK: {data.get('total_deleted_records', 0)} record eliminati da {data.get('total_tables_reset', 0)} tabelle")
            if data.get('errors'):
                print(f"⚠️  Errori: {len(data['errors'])}")
                for error in data['errors'][:3]:
                    print(f"  - {error}")
            return True
        else:
            print(f"❌ Errore reset: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore reset: {str(e)}")
        return False

def main():
    """Funzione principale di test"""
    print("🚀 TEST FUNZIONI AMMINISTRATIVE CARBONPILOT")
    print("=" * 55)
    
    # Attendi che il server sia pronto
    print("⏳ Attesa avvio server...")
    time.sleep(3)
    
    results = {}
    
    # Test info database
    results['database_info'] = test_database_info()
    
    # Test backup
    backup_ok, backup_file = test_backup_export()
    results['backup'] = backup_ok
    
    # Test restore (solo se backup è riuscito)
    if backup_ok and backup_file:
        results['restore'] = test_restore(backup_file)
        
        # Cleanup del file di backup
        try:
            os.remove(backup_file)
            print(f"🧹 File backup rimosso: {backup_file}")
        except:
            pass
    else:
        results['restore'] = False
    
    # Test reset
    results['reset'] = test_reset()
    
    # Risultati finali
    print("\n" + "=" * 55)
    print("📋 RISULTATI TEST:")
    print(f"  🔍 Database Info: {'✅ OK' if results['database_info'] else '❌ ERRORE'}")
    print(f"  💾 Backup: {'✅ OK' if results['backup'] else '❌ ERRORE'}")
    print(f"  📥 Restore: {'✅ OK' if results['restore'] else '❌ ERRORE'}")
    print(f"  🗑️  Reset: {'✅ OK' if results['reset'] else '❌ ERRORE'}")
    
    if all(results.values()):
        print("\n🎉 Tutti i test superati! Funzioni amministrative OK!")
    else:
        print("\n⚠️  Alcuni test falliti. Controllare i dettagli sopra.")
        
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"Test falliti: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main() 