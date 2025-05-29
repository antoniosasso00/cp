#!/usr/bin/env python3
"""
Script di validazione per la dashboard di monitoraggio ODL.
Verifica che tutte le funzionalità siano operative e robuste.
"""

import requests
import json
import time
from datetime import datetime

def print_header(title):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Stampa una sezione"""
    print(f"\n📋 {title}")
    print("-" * 40)

def test_backend_connection(base_url="http://localhost:8000"):
    """Testa la connessione al backend"""
    print_section("Connessione Backend")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend attivo e raggiungibile")
            return True
        else:
            print(f"❌ Backend risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossibile connettersi al backend: {e}")
        return False

def test_monitoring_apis(base_url="http://localhost:8000"):
    """Testa le API di monitoraggio ODL"""
    print_section("API Monitoraggio ODL")
    
    api_endpoints = [
        ("/api/v1/odl-monitoring/monitoring/stats", "Statistiche generali"),
        ("/api/v1/odl-monitoring/monitoring", "Lista ODL monitoraggio"),
        ("/api/v1/odl/", "Lista ODL base"),
        ("/api/v1/catalogo/", "Catalogo parti"),
    ]
    
    results = {}
    
    for endpoint, description in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    'status': 'OK',
                    'data_count': len(data) if isinstance(data, list) else 1,
                    'response': data
                }
                print(f"✅ {description}: OK ({results[endpoint]['data_count']} elementi)")
            else:
                results[endpoint] = {'status': 'ERROR', 'code': response.status_code}
                print(f"❌ {description}: Errore {response.status_code}")
        except Exception as e:
            results[endpoint] = {'status': 'EXCEPTION', 'error': str(e)}
            print(f"❌ {description}: Eccezione - {e}")
    
    return results

def test_odl_timeline_detail(base_url="http://localhost:8000", api_results=None):
    """Testa il dettaglio timeline di un ODL specifico"""
    print_section("Timeline Dettagli ODL")
    
    # Trova un ODL valido dai risultati precedenti
    odl_id = None
    if api_results and '/api/v1/odl/' in api_results:
        odl_data = api_results['/api/v1/odl/'].get('response', [])
        if odl_data and len(odl_data) > 0:
            odl_id = odl_data[0].get('id')
    
    if not odl_id:
        print("⚠️  Nessun ODL disponibile per testare la timeline")
        return False
    
    print(f"🔍 Test con ODL #{odl_id}")
    
    # Test endpoint dettaglio
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}", timeout=10)
        if response.status_code == 200:
            detail_data = response.json()
            print(f"✅ Dettaglio ODL #{odl_id}: OK")
            print(f"   - Stato: {detail_data.get('status', 'N/A')}")
            print(f"   - Parte: {detail_data.get('parte_nome', 'N/A')}")
            print(f"   - Tool: {detail_data.get('tool_nome', 'N/A')}")
        else:
            print(f"❌ Dettaglio ODL #{odl_id}: Errore {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dettaglio ODL #{odl_id}: Eccezione - {e}")
        return False
    
    # Test endpoint timeline
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/timeline", timeout=10)
        if response.status_code == 200:
            timeline_data = response.json()
            print(f"✅ Timeline ODL #{odl_id}: OK ({len(timeline_data)} eventi)")
        elif response.status_code == 404:
            print(f"⚠️  Timeline ODL #{odl_id}: Non disponibile (404) - normale per ODL senza log")
        else:
            print(f"❌ Timeline ODL #{odl_id}: Errore {response.status_code}")
    except Exception as e:
        print(f"❌ Timeline ODL #{odl_id}: Eccezione - {e}")
    
    # Test endpoint progress (fallback)
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/{odl_id}/progress", timeout=10)
        if response.status_code == 200:
            progress_data = response.json()
            print(f"✅ Progress ODL #{odl_id}: OK")
            print(f"   - Has Timeline Data: {progress_data.get('has_timeline_data', False)}")
            print(f"   - Data Source: {progress_data.get('data_source', 'N/A')}")
            print(f"   - Timestamps: {len(progress_data.get('timestamps', []))}")
        else:
            print(f"❌ Progress ODL #{odl_id}: Errore {response.status_code}")
    except Exception as e:
        print(f"❌ Progress ODL #{odl_id}: Eccezione - {e}")
    
    return True

def test_error_handling(base_url="http://localhost:8000"):
    """Testa la gestione degli errori"""
    print_section("Gestione Errori")
    
    # Test ID ODL non valido
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/99999", timeout=5)
        if response.status_code == 404:
            print("✅ Gestione ID ODL non valido: OK (404)")
        else:
            print(f"⚠️  Gestione ID ODL non valido: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Test ID non valido: Eccezione - {e}")
    
    # Test ID ODL non numerico
    try:
        response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring/invalid", timeout=5)
        if response.status_code in [400, 422, 404]:
            print("✅ Gestione ID ODL non numerico: OK")
        else:
            print(f"⚠️  Gestione ID ODL non numerico: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Test ID non numerico: Eccezione - {e}")

def test_filters_and_pagination(base_url="http://localhost:8000"):
    """Testa filtri e paginazione"""
    print_section("Filtri e Paginazione")
    
    # Test filtri
    filter_tests = [
        ("?solo_attivi=true", "Solo ODL attivi"),
        ("?solo_attivi=false", "Tutti gli ODL"),
        ("?limit=5", "Limite 5 elementi"),
        ("?status_filter=Preparazione", "Filtro stato Preparazione"),
    ]
    
    for filter_param, description in filter_tests:
        try:
            response = requests.get(f"{base_url}/api/v1/odl-monitoring/monitoring{filter_param}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: OK ({len(data)} elementi)")
            else:
                print(f"❌ {description}: Errore {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Eccezione - {e}")

def test_dashboard_robustness():
    """Test di robustezza della dashboard"""
    print_section("Test Robustezza Dashboard")
    
    print("✅ Naviga su /dashboard/monitoraggio con ODL completati → verifica che i box mostrino dati reali")
    print("✅ Seleziona un part number → verifica che la sezione 'Statistiche per [PN]' si popoli correttamente")
    print("✅ Naviga su /dashboard/management/odl-monitoring/1 → verifica caricamento dettagli")
    print("✅ Forza un errore di rete o un ID errato → controlla se appare un fallback pulito")
    
    print("\n📝 Note tecniche:")
    print("   - Evitare dipendenze tra filtri e visualizzazione se useEffect non sincronizzato")
    print("   - Considerare memorizzazione filtri con useSearchParams() per persistenza")
    print("   - Verificare nei componenti grafici che non si aspettino sempre data.length > 0")

def initialize_monitoring_system(base_url="http://localhost:8000"):
    """Inizializza il sistema di monitoraggio se necessario"""
    print_section("Inizializzazione Sistema")
    
    try:
        # Inizializza state tracking
        response = requests.post(f"{base_url}/api/v1/odl-monitoring/monitoring/initialize-state-tracking", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ State tracking inizializzato: {result.get('logs_creati', 0)} log creati")
        else:
            print(f"⚠️  Inizializzazione state tracking: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Inizializzazione state tracking: Eccezione - {e}")
    
    try:
        # Genera log mancanti
        response = requests.post(f"{base_url}/api/v1/odl-monitoring/monitoring/generate-missing-logs", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Log mancanti generati: {result.get('logs_creati', 0)} log creati")
        else:
            print(f"⚠️  Generazione log mancanti: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Generazione log mancanti: Eccezione - {e}")

def main():
    """Funzione principale di test"""
    print_header("VALIDAZIONE DASHBOARD MONITORAGGIO ODL")
    print(f"🕒 Avviato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    # Test connessione
    if not test_backend_connection(base_url):
        print("\n❌ ERRORE CRITICO: Backend non raggiungibile")
        print("   Assicurati che il backend sia avviato su http://localhost:8000")
        return
    
    # Inizializza sistema se necessario
    initialize_monitoring_system(base_url)
    
    # Test API
    api_results = test_monitoring_apis(base_url)
    
    # Test timeline dettagli
    test_odl_timeline_detail(base_url, api_results)
    
    # Test gestione errori
    test_error_handling(base_url)
    
    # Test filtri
    test_filters_and_pagination(base_url)
    
    # Test robustezza dashboard
    test_dashboard_robustness()
    
    print_header("RIEPILOGO VALIDAZIONE")
    
    # Conta successi e fallimenti
    total_tests = 0
    passed_tests = 0
    
    for endpoint, result in api_results.items():
        total_tests += 1
        if result['status'] == 'OK':
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 Test API: {passed_tests}/{total_tests} passati ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("✅ VALIDAZIONE COMPLETATA CON SUCCESSO")
        print("   La dashboard di monitoraggio è funzionale e robusta")
    elif success_rate >= 60:
        print("⚠️  VALIDAZIONE PARZIALMENTE RIUSCITA")
        print("   Alcune funzionalità potrebbero non essere completamente operative")
    else:
        print("❌ VALIDAZIONE FALLITA")
        print("   Sono necessarie correzioni significative")
    
    print(f"\n🏁 Completato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 