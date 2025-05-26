#!/usr/bin/env python3
"""
Script di test per il sistema di logging avanzato
Testa tutte le funzionalità principali del sistema di audit trail
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"

def test_system_logs():
    """Testa il sistema di logging"""
    print("🔍 Test Sistema di Logging Avanzato")
    print("=" * 50)
    
    # Test 1: Verifica endpoint statistiche
    print("\n1. Test endpoint statistiche...")
    try:
        response = requests.get(f"{BASE_URL}/system-logs/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiche caricate: {stats.get('total_logs', 0)} log totali")
        else:
            print(f"❌ Errore statistiche: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore connessione statistiche: {e}")
    
    # Test 2: Verifica endpoint lista log
    print("\n2. Test endpoint lista log...")
    try:
        response = requests.get(f"{BASE_URL}/system-logs/", params={"limit": 10})
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Log caricati: {len(logs)} record")
            if logs:
                print(f"   Ultimo log: {logs[0].get('action', 'N/A')}")
        else:
            print(f"❌ Errore lista log: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore connessione lista log: {e}")
    
    # Test 3: Verifica filtri
    print("\n3. Test filtri avanzati...")
    try:
        filters = {
            "event_type": "odl_state_change",
            "level": "info",
            "limit": 5
        }
        response = requests.get(f"{BASE_URL}/system-logs/", params=filters)
        if response.status_code == 200:
            filtered_logs = response.json()
            print(f"✅ Filtri funzionanti: {len(filtered_logs)} log filtrati")
        else:
            print(f"❌ Errore filtri: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore test filtri: {e}")
    
    # Test 4: Verifica errori recenti
    print("\n4. Test errori recenti...")
    try:
        response = requests.get(f"{BASE_URL}/system-logs/recent-errors")
        if response.status_code == 200:
            errors = response.json()
            print(f"✅ Errori recenti: {len(errors)} trovati")
        else:
            print(f"❌ Errore endpoint errori: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore test errori recenti: {e}")
    
    # Test 5: Test export CSV
    print("\n5. Test export CSV...")
    try:
        response = requests.get(f"{BASE_URL}/system-logs/export", params={"limit": 10})
        if response.status_code == 200:
            print(f"✅ Export CSV funzionante: {len(response.content)} bytes")
        else:
            print(f"❌ Errore export: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore test export: {e}")

def test_frontend_access():
    """Testa l'accesso alle pagine frontend"""
    print("\n\n🖥️ Test Accesso Frontend")
    print("=" * 50)
    
    frontend_urls = [
        "http://localhost:3000/dashboard/admin/logs",
        "http://localhost:3000/dashboard/responsabile/logs"
    ]
    
    for url in frontend_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - Accessibile")
            else:
                print(f"❌ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Errore: {e}")

def show_system_info():
    """Mostra informazioni sul sistema"""
    print("\n\n📊 Informazioni Sistema")
    print("=" * 50)
    
    try:
        # Verifica backend
        response = requests.get(f"{BASE_URL}/system-logs/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"📈 Totale log nel sistema: {stats.get('total_logs', 0)}")
            
            # Mostra distribuzione per tipo
            logs_by_type = stats.get('logs_by_type', {})
            if logs_by_type:
                print("\n📋 Distribuzione per tipo evento:")
                for event_type, count in logs_by_type.items():
                    print(f"   • {event_type}: {count}")
            
            # Mostra distribuzione per ruolo
            logs_by_role = stats.get('logs_by_role', {})
            if logs_by_role:
                print("\n👥 Distribuzione per ruolo:")
                for role, count in logs_by_role.items():
                    print(f"   • {role}: {count}")
                    
        else:
            print("❌ Impossibile recuperare statistiche sistema")
            
    except Exception as e:
        print(f"❌ Errore nel recupero informazioni: {e}")

def main():
    """Funzione principale"""
    print("🚀 CarbonPilot - Test Sistema di Logging Avanzato")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Attendi che i servizi siano pronti
    print("\n⏳ Attendo che i servizi siano pronti...")
    time.sleep(3)
    
    # Esegui i test
    test_system_logs()
    test_frontend_access()
    show_system_info()
    
    print("\n\n✨ Test completati!")
    print("\n📝 Per accedere alle dashboard:")
    print("   • Admin: http://localhost:3000/dashboard/admin/logs")
    print("   • Responsabile: http://localhost:3000/dashboard/responsabile/logs")
    print("\n📚 Documentazione API: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 