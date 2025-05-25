#!/usr/bin/env python3
"""
Script di debug completo per CarbonPilot
Testa tutti gli endpoint e verifica la connessione al database
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"

def print_header(title):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_success(message):
    """Stampa un messaggio di successo"""
    print(f"✅ {message}")

def print_error(message):
    """Stampa un messaggio di errore"""
    print(f"❌ {message}")

def print_warning(message):
    """Stampa un messaggio di warning"""
    print(f"⚠️ {message}")

def test_endpoint(method, endpoint, data=None, params=None):
    """Testa un endpoint specifico"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        print(f"\n🌐 Testing {method} {endpoint}")
        
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            print_error(f"Metodo HTTP non supportato: {method}")
            return False
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                if isinstance(json_data, list):
                    print(f"   Risposta: Lista con {len(json_data)} elementi")
                    if len(json_data) > 0:
                        print(f"   Primo elemento: {json.dumps(json_data[0], indent=2, default=str)[:200]}...")
                else:
                    print(f"   Risposta: {json.dumps(json_data, indent=2, default=str)[:300]}...")
                print_success(f"Endpoint {endpoint} funziona correttamente")
                return True
            except json.JSONDecodeError:
                print(f"   Risposta (non JSON): {response.text[:200]}...")
                print_success(f"Endpoint {endpoint} risponde (non JSON)")
                return True
        elif response.status_code == 201:
            print_success(f"Endpoint {endpoint} - Risorsa creata")
            return True
        elif response.status_code == 204:
            print_success(f"Endpoint {endpoint} - Operazione completata")
            return True
        elif response.status_code == 404:
            print_warning(f"Endpoint {endpoint} non trovato")
            return False
        elif response.status_code == 422:
            print_error(f"Errore di validazione su {endpoint}")
            try:
                error_data = response.json()
                print(f"   Dettagli errore: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Risposta errore: {response.text}")
            return False
        else:
            print_error(f"Errore {response.status_code} su {endpoint}")
            print(f"   Risposta: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Impossibile connettersi a {url}")
        print_error("Verifica che il backend sia in esecuzione su localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print_error(f"Timeout su {endpoint}")
        return False
    except Exception as e:
        print_error(f"Errore imprevisto su {endpoint}: {str(e)}")
        return False

def test_health_endpoints():
    """Testa gli endpoint di health check"""
    print_header("HEALTH CHECK")
    
    # Test endpoint root
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print_success("Server principale raggiungibile")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
        else:
            print_error(f"Server principale non risponde correttamente: {response.status_code}")
    except Exception as e:
        print_error(f"Server principale non raggiungibile: {str(e)}")
        return False
    
    # Test health endpoint dettagliato
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Health check dettagliato OK")
            data = response.json()
            print(f"   Database status: {data.get('database', {}).get('status')}")
            print(f"   Database tables: {data.get('database', {}).get('tables_count')}")
            print(f"   API routes: {data.get('api', {}).get('routes_count')}")
        else:
            print_error(f"Health check dettagliato fallito: {response.status_code}")
    except Exception as e:
        print_error(f"Health check dettagliato non raggiungibile: {str(e)}")
    
    return True

def test_all_endpoints():
    """Testa tutti gli endpoint principali"""
    print_header("TEST ENDPOINT API")
    
    endpoints_to_test = [
        # Tools
        ("GET", "/tools", None, None),
        ("GET", "/tools/with-status", None, None),
        
        # Parts
        ("GET", "/parti", None, None),
        
        # ODL
        ("GET", "/odl", None, None),
        
        # Catalogo
        ("GET", "/catalogo", None, None),
        
        # Autoclavi
        ("GET", "/autoclavi", None, None),
        
        # Nesting
        ("GET", "/nesting", None, None),
        ("GET", "/nesting/drafts", None, None),
        
        # Schedules
        ("GET", "/schedules", None, None),
        
        # Cicli Cura
        ("GET", "/cicli-cura", None, None),
        
        # Reports
        ("GET", "/reports", None, None),
        
        # Tempo Fasi
        ("GET", "/tempo-fasi", None, None),
    ]
    
    results = []
    for method, endpoint, data, params in endpoints_to_test:
        success = test_endpoint(method, endpoint, data, params)
        results.append((endpoint, success))
    
    # Riepilogo
    print_header("RIEPILOGO TEST ENDPOINT")
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Endpoint testati: {total}")
    print(f"Endpoint funzionanti: {successful}")
    print(f"Endpoint con problemi: {total - successful}")
    
    if successful == total:
        print_success("Tutti gli endpoint funzionano correttamente!")
    else:
        print_warning("Alcuni endpoint hanno problemi:")
        for endpoint, success in results:
            if not success:
                print(f"   ❌ {endpoint}")

def test_database_connection():
    """Testa la connessione al database tramite l'endpoint health"""
    print_header("TEST CONNESSIONE DATABASE")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('database', {}).get('status')
            tables_count = data.get('database', {}).get('tables_count', 0)
            
            if db_status == "connected":
                print_success(f"Database connesso con {tables_count} tabelle")
                return True
            else:
                print_error(f"Database non connesso: {db_status}")
                return False
        else:
            print_error("Impossibile verificare lo stato del database")
            return False
    except Exception as e:
        print_error(f"Errore nel test database: {str(e)}")
        return False

def main():
    """Funzione principale"""
    print_header("DEBUG COMPLETO CARBONPILOT")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base URL: {API_BASE_URL}")
    
    # Test 1: Health check
    if not test_health_endpoints():
        print_error("Health check fallito. Il server potrebbe non essere in esecuzione.")
        sys.exit(1)
    
    # Test 2: Database
    test_database_connection()
    
    # Test 3: Tutti gli endpoint
    test_all_endpoints()
    
    print_header("DEBUG COMPLETATO")
    print("Se ci sono errori 422, controlla i parametri delle richieste.")
    print("Se ci sono errori 500, controlla i log del backend.")
    print("Se ci sono errori di connessione, verifica che il backend sia in esecuzione.")

if __name__ == "__main__":
    main() 