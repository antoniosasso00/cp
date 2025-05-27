#!/usr/bin/env python3
"""
Script di validazione per la pagina Tools
Testa tutti i fix implementati per risolvere i problemi identificati
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configurazione
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10

def print_section(title: str):
    """Stampa una sezione con formattazione"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_success(message: str):
    """Stampa un messaggio di successo"""
    print(f"✅ {message}")

def print_error(message: str):
    """Stampa un messaggio di errore"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Stampa un messaggio di avviso"""
    print(f"⚠️ {message}")

def test_api_connection() -> bool:
    """Testa la connessione all'API"""
    print_section("Test Connessione API")
    
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("Connessione API stabilita")
            health_data = response.json()
            print(f"   Database: {health_data.get('database', {}).get('status', 'N/A')}")
            print(f"   Tabelle: {health_data.get('database', {}).get('tables_count', 'N/A')}")
            return True
        else:
            print_error(f"API non raggiungibile: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Errore di connessione: {e}")
        return False

def test_tools_loading() -> bool:
    """Testa il caricamento dei tools"""
    print_section("Test Caricamento Tools")
    
    try:
        # Test endpoint base tools
        response = requests.get(f"{API_BASE_URL}/tools", timeout=TIMEOUT)
        if response.status_code == 200:
            tools = response.json()
            print_success(f"Tools base caricati: {len(tools)} elementi")
        else:
            print_error(f"Errore caricamento tools base: HTTP {response.status_code}")
            return False
        
        # Test endpoint tools con status
        response = requests.get(f"{API_BASE_URL}/tools/with-status", timeout=TIMEOUT)
        if response.status_code == 200:
            tools_with_status = response.json()
            print_success(f"Tools con status caricati: {len(tools_with_status)} elementi")
            
            # Verifica struttura dati
            if tools_with_status:
                first_tool = tools_with_status[0]
                required_fields = ['id', 'part_number_tool', 'status_display']
                missing_fields = [field for field in required_fields if field not in first_tool]
                
                if missing_fields:
                    print_warning(f"Campi mancanti nel primo tool: {missing_fields}")
                else:
                    print_success("Struttura dati tools corretta")
            
            return True
        else:
            print_error(f"Errore caricamento tools con status: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Errore nella richiesta tools: {e}")
        return False

def test_tool_status_update() -> bool:
    """Testa l'aggiornamento dello stato dei tools"""
    print_section("Test Aggiornamento Stato Tools")
    
    try:
        # Prima ottieni la lista dei tools
        response = requests.get(f"{API_BASE_URL}/tools/with-status", timeout=TIMEOUT)
        if response.status_code != 200:
            print_error("Impossibile ottenere la lista dei tools per il test")
            return False
        
        tools = response.json()
        if not tools:
            print_warning("Nessun tool disponibile per il test di aggiornamento")
            return True
        
        # Prendi il primo tool per il test
        test_tool = tools[0]
        tool_id = test_tool['id']
        original_disponibile = test_tool.get('disponibile', True)
        
        print(f"   Testing con tool ID: {tool_id} (Part Number: {test_tool['part_number_tool']})")
        
        # Test 1: Cambia lo stato di disponibilità
        new_disponibile = not original_disponibile
        update_data = {"disponibile": new_disponibile}
        
        response = requests.put(
            f"{API_BASE_URL}/tools/{tool_id}", 
            json=update_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            print_success(f"Stato tool aggiornato: disponibile = {new_disponibile}")
        else:
            print_error(f"Errore aggiornamento tool: HTTP {response.status_code}")
            if response.text:
                print(f"   Dettagli: {response.text}")
            return False
        
        # Test 2: Ripristina lo stato originale
        restore_data = {"disponibile": original_disponibile}
        response = requests.put(
            f"{API_BASE_URL}/tools/{tool_id}", 
            json=restore_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            print_success(f"Stato tool ripristinato: disponibile = {original_disponibile}")
        else:
            print_warning(f"Errore nel ripristino stato originale: HTTP {response.status_code}")
        
        # Test 3: Sincronizzazione stato da ODL
        response = requests.put(f"{API_BASE_URL}/tools/update-status-from-odl", timeout=TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Sincronizzazione stato completata: {result.get('message', 'OK')}")
        else:
            print_error(f"Errore sincronizzazione stato: HTTP {response.status_code}")
            if response.text:
                print(f"   Dettagli: {response.text}")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Errore nella richiesta di aggiornamento: {e}")
        return False

def test_database_export() -> bool:
    """Testa l'esportazione del database"""
    print_section("Test Esportazione Database")
    
    try:
        # Test endpoint di backup
        response = requests.get(f"{API_BASE_URL}/admin/backup", timeout=30)  # Timeout più lungo per l'export
        
        if response.status_code == 200:
            print_success("Esportazione database completata")
            
            # Verifica headers
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            if 'application/json' in content_type:
                print_success("Content-Type corretto: application/json")
            else:
                print_warning(f"Content-Type inaspettato: {content_type}")
            
            if 'attachment' in content_disposition:
                print_success("Content-Disposition corretto per download")
            else:
                print_warning(f"Content-Disposition: {content_disposition}")
            
            # Verifica dimensione file
            content_length = len(response.content)
            if content_length > 0:
                print_success(f"File esportato: {content_length} bytes")
                
                # Prova a parsare il JSON per verificare la validità
                try:
                    data = response.json()
                    if 'tables' in data and 'export_timestamp' in data:
                        print_success("Struttura JSON del backup valida")
                        tables_count = len(data.get('tables', {}))
                        print(f"   Tabelle esportate: {tables_count}")
                    else:
                        print_warning("Struttura JSON del backup incompleta")
                except json.JSONDecodeError:
                    print_warning("Il file esportato non è un JSON valido")
            else:
                print_error("File esportato vuoto")
                return False
            
            return True
        else:
            print_error(f"Errore esportazione database: HTTP {response.status_code}")
            if response.text:
                print(f"   Dettagli: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Errore nella richiesta di esportazione: {e}")
        return False

def test_refresh_functionality() -> bool:
    """Testa la funzionalità di refresh"""
    print_section("Test Funzionalità Refresh")
    
    try:
        # Test 1: Caricamento iniziale
        start_time = time.time()
        response1 = requests.get(f"{API_BASE_URL}/tools/with-status", timeout=TIMEOUT)
        load_time = time.time() - start_time
        
        if response1.status_code == 200:
            tools1 = response1.json()
            print_success(f"Primo caricamento: {len(tools1)} tools in {load_time:.2f}s")
        else:
            print_error(f"Errore primo caricamento: HTTP {response1.status_code}")
            return False
        
        # Test 2: Refresh immediato
        start_time = time.time()
        response2 = requests.get(f"{API_BASE_URL}/tools/with-status", timeout=TIMEOUT)
        refresh_time = time.time() - start_time
        
        if response2.status_code == 200:
            tools2 = response2.json()
            print_success(f"Refresh: {len(tools2)} tools in {refresh_time:.2f}s")
            
            # Verifica coerenza dati
            if len(tools1) == len(tools2):
                print_success("Numero di tools coerente tra caricamenti")
            else:
                print_warning(f"Numero tools diverso: {len(tools1)} vs {len(tools2)}")
        else:
            print_error(f"Errore refresh: HTTP {response2.status_code}")
            return False
        
        # Test 3: Performance check
        if refresh_time > 5.0:
            print_warning(f"Refresh lento: {refresh_time:.2f}s (soglia: 5s)")
        else:
            print_success(f"Performance refresh accettabile: {refresh_time:.2f}s")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Errore nel test refresh: {e}")
        return False

def run_validation() -> Dict[str, bool]:
    """Esegue tutti i test di validazione"""
    print("🚀 Avvio validazione pagina Tools")
    print(f"   API Base URL: {API_BASE_URL}")
    print(f"   Timeout: {TIMEOUT}s")
    
    results = {}
    
    # Esegui tutti i test
    results['connection'] = test_api_connection()
    results['tools_loading'] = test_tools_loading()
    results['status_update'] = test_tool_status_update()
    results['database_export'] = test_database_export()
    results['refresh'] = test_refresh_functionality()
    
    return results

def print_summary(results: Dict[str, bool]):
    """Stampa il riepilogo dei risultati"""
    print_section("Riepilogo Validazione")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"   {test_display:<25} {status}")
    
    print(f"\n📊 Risultati: {passed_tests}/{total_tests} test superati")
    
    if failed_tests == 0:
        print_success("Tutti i test sono stati superati! 🎉")
        return True
    else:
        print_error(f"{failed_tests} test falliti. Controllare i log sopra per i dettagli.")
        return False

def main():
    """Funzione principale"""
    try:
        results = run_validation()
        success = print_summary(results)
        
        # Exit code per CI/CD
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Validazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print_error(f"Errore inaspettato durante la validazione: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 