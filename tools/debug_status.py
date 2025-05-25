#!/usr/bin/env python3
"""
🔧 CarbonPilot - Diagnostica Locale
Verifica lo stato del sistema e delle API in locale
"""

import sys
import os
import requests
import sqlite3
from datetime import datetime
from pathlib import Path

# Aggiungi il path del backend per importare i moduli
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

# Configurazione
API_BASE_URL = "http://localhost:8000/api/v1"
DB_PATH = backend_path / "carbonpilot.db"

def print_header(title: str):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Stampa una sezione"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_database_connection():
    """Verifica la connessione al database"""
    print_section("Stato Connessione Database")
    
    try:
        if not DB_PATH.exists():
            print("❌ Database non trovato:", DB_PATH)
            return False
            
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Test connessione
        cursor.execute("SELECT 1")
        print("✅ Connessione database: OK")
        
        # Verifica tabelle principali
        tables = ['catalogo', 'parti', 'tools', 'odl', 'autoclavi', 'cicli_cura']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("\n📊 Tabelle presenti:")
        for table in tables:
            if table in existing_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (mancante)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore connessione database: {e}")
        return False

def count_seed_entities():
    """Conta le entità seed nel database"""
    print_section("Totale Entità Seed")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        entities = {
            'Catalogo': 'catalogo',
            'Parti': 'parti', 
            'Tools': 'tools',
            'ODL': 'odl',
            'Autoclavi': 'autoclavi',
            'Cicli Cura': 'cicli_cura',
            'Tempi Fasi': 'tempo_fasi'
        }
        
        for name, table in entities.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📦 {name}: {count} record")
            except sqlite3.OperationalError:
                print(f"  ❌ {name}: tabella non trovata")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore nel conteggio entità: {e}")

def test_api_endpoints():
    """Testa gli endpoint API principali"""
    print_section("Stato API Attive")
    
    endpoints = [
        ("Health Check", "/"),
        ("Catalogo", "/catalogo"),
        ("Parti", "/parti"),
        ("Tools", "/tools"),
        ("Tools con Stato", "/tools/with-status"),
        ("ODL", "/odl"),
        ("Autoclavi", "/autoclavi"),
        ("Cicli Cura", "/cicli-cura"),
        ("Nesting", "/nesting/preview"),
        ("Reports", "/reports/list"),
        ("Tempi Fasi", "/tempo-fasi")
    ]
    
    for name, endpoint in endpoints:
        try:
            url = f"{API_BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                        print(f"  ✅ {name}: {response.status_code} ({count} elementi)")
                    else:
                        print(f"  ✅ {name}: {response.status_code} (OK)")
                except:
                    print(f"  ✅ {name}: {response.status_code} (risposta non JSON)")
            elif response.status_code == 422:
                print(f"  ⚠️  {name}: {response.status_code} (errore validazione)")
            elif response.status_code == 404:
                print(f"  ❌ {name}: {response.status_code} (non trovato)")
            else:
                print(f"  ⚠️  {name}: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"  🔌 {name}: Server non raggiungibile")
        except requests.exceptions.Timeout:
            print(f"  ⏱️  {name}: Timeout")
        except Exception as e:
            print(f"  ❌ {name}: Errore - {e}")

def check_backend_process():
    """Verifica se il processo backend è in esecuzione"""
    print_section("Processo Backend")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=3)
        if response.status_code == 200:
            print("  ✅ Backend FastAPI: In esecuzione")
            print(f"  🌐 URL: {API_BASE_URL}")
        else:
            print(f"  ⚠️  Backend risponde ma con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  ❌ Backend FastAPI: Non raggiungibile")
        print("  💡 Suggerimento: Avvia il backend con:")
        print("     cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"  ❌ Errore verifica backend: {e}")

def check_frontend_process():
    """Verifica se il processo frontend è in esecuzione"""
    print_section("Processo Frontend")
    
    try:
        response = requests.get("http://localhost:3000", timeout=3)
        if response.status_code == 200:
            print("  ✅ Frontend Next.js: In esecuzione")
            print("  🌐 URL: http://localhost:3000")
        else:
            print(f"  ⚠️  Frontend risponde ma con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  ❌ Frontend Next.js: Non raggiungibile")
        print("  💡 Suggerimento: Avvia il frontend con:")
        print("     cd frontend && npm run dev")
    except Exception as e:
        print(f"  ❌ Errore verifica frontend: {e}")

def main():
    """Funzione principale di diagnostica"""
    print_header("CarbonPilot - Diagnostica Sistema Locale")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verifica database
    db_ok = check_database_connection()
    
    if db_ok:
        count_seed_entities()
    
    # Verifica processi
    check_backend_process()
    check_frontend_process()
    
    # Verifica API
    test_api_endpoints()
    
    print_section("Riepilogo")
    print("✅ = OK | ⚠️ = Warning | ❌ = Errore | 🔌 = Connessione | ⏱️ = Timeout")
    print("\n🎯 Per risolvere i problemi:")
    print("   1. Assicurati che il backend sia avviato (porta 8000)")
    print("   2. Assicurati che il frontend sia avviato (porta 3000)")
    print("   3. Verifica che il database SQLite esista e sia accessibile")
    print("   4. Controlla i log del backend per errori specifici")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main() 