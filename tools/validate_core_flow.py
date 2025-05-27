#!/usr/bin/env python3
"""
🧪 Script di Validazione CarbonPilot - Flusso Core
Verifica che tutti i fix implementati funzionino correttamente
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configurazione
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_header(title: str):
    """Stampa un header formattato"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_ok(label: str, condition: bool, details: str = ""):
    """Verifica una condizione e stampa il risultato"""
    status = "✅" if condition else "❌"
    print(f"{status} {label}")
    if details and not condition:
        print(f"   💡 {details}")
    return condition

def test_api_endpoint(endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
    """Testa un endpoint API e ritorna la risposta"""
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        return {
            "success": response.status_code == expected_status,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": str(e)
        }

def validate_core_endpoints():
    """Valida gli endpoint principali del sistema"""
    print_header("VALIDAZIONE ENDPOINT CORE")
    
    endpoints = [
        ("/cicli-cura", "Cicli di Cura"),
        ("/tools", "Tools/Stampi"),
        ("/catalogo", "Catalogo"),
        ("/parti", "Parti"),
        ("/autoclavi", "Autoclavi"),
        ("/odl", "ODL"),
    ]
    
    all_ok = True
    for endpoint, name in endpoints:
        result = test_api_endpoint(endpoint)
        success = check_ok(
            f"{name} accessibili", 
            result["success"],
            f"Status: {result['status_code']}, Error: {result['error']}" if not result["success"] else ""
        )
        all_ok = all_ok and success
    
    return all_ok

def validate_database_export():
    """Valida la funzionalità di export del database"""
    print_header("VALIDAZIONE EXPORT DATABASE")
    
    result = test_api_endpoint("/admin/backup")
    return check_ok(
        "Export DB funzionante", 
        result["success"],
        f"Status: {result['status_code']}, Error: {result['error']}" if not result["success"] else ""
    )

def validate_data_consistency():
    """Valida la consistenza dei dati tra le entità"""
    print_header("VALIDAZIONE CONSISTENZA DATI")
    
    all_ok = True
    
    # Test 1: Verifica che ci siano dati di base
    catalogo_result = test_api_endpoint("/catalogo")
    if catalogo_result["success"] and catalogo_result["data"]:
        catalogo_count = len(catalogo_result["data"])
        all_ok = all_ok and check_ok(f"Catalogo contiene {catalogo_count} elementi", catalogo_count > 0)
    else:
        all_ok = all_ok and check_ok("Catalogo accessibile", False, "Impossibile accedere al catalogo")
    
    # Test 2: Verifica tools
    tools_result = test_api_endpoint("/tools")
    if tools_result["success"] and tools_result["data"]:
        tools_count = len(tools_result["data"])
        all_ok = all_ok and check_ok(f"Tools disponibili: {tools_count}", tools_count >= 0)
    else:
        all_ok = all_ok and check_ok("Tools accessibili", False, "Impossibile accedere ai tools")
    
    # Test 3: Verifica cicli
    cicli_result = test_api_endpoint("/cicli-cura")
    if cicli_result["success"] and cicli_result["data"]:
        cicli_count = len(cicli_result["data"])
        all_ok = all_ok and check_ok(f"Cicli di cura disponibili: {cicli_count}", cicli_count >= 0)
    else:
        all_ok = all_ok and check_ok("Cicli accessibili", False, "Impossibile accedere ai cicli")
    
    # Test 4: Verifica parti
    parti_result = test_api_endpoint("/parti")
    if parti_result["success"]:
        parti_count = len(parti_result["data"]) if parti_result["data"] else 0
        all_ok = all_ok and check_ok(f"Parti disponibili: {parti_count}", True)
    else:
        all_ok = all_ok and check_ok("Parti accessibili", False, "Impossibile accedere alle parti")
    
    return all_ok

def validate_frontend_accessibility():
    """Valida che il frontend sia accessibile"""
    print_header("VALIDAZIONE FRONTEND")
    
    try:
        response = requests.get(BASE_URL, timeout=10)
        return check_ok(
            "Frontend accessibile", 
            response.status_code == 200,
            f"Status code: {response.status_code}" if response.status_code != 200 else ""
        )
    except requests.exceptions.RequestException as e:
        return check_ok("Frontend accessibile", False, f"Errore di connessione: {str(e)}")

def validate_critical_flows():
    """Valida i flussi critici del sistema"""
    print_header("VALIDAZIONE FLUSSI CRITICI")
    
    all_ok = True
    
    # Test 1: Flusso Catalogo → Tools → Cicli → Parti
    print("🔄 Testando flusso: Catalogo → Tools → Cicli → Parti")
    
    # Verifica che ogni step del flusso sia accessibile
    flow_steps = [
        ("/catalogo", "Catalogo"),
        ("/tools", "Tools"),
        ("/cicli-cura", "Cicli"),
        ("/parti", "Parti")
    ]
    
    for endpoint, step_name in flow_steps:
        result = test_api_endpoint(endpoint)
        step_ok = check_ok(f"  {step_name} nel flusso", result["success"])
        all_ok = all_ok and step_ok
    
    # Test 2: Verifica che le autoclavi siano configurate per il nesting
    autoclavi_result = test_api_endpoint("/autoclavi")
    if autoclavi_result["success"] and autoclavi_result["data"]:
        autoclavi_count = len(autoclavi_result["data"])
        all_ok = all_ok and check_ok(f"Autoclavi configurate: {autoclavi_count}", autoclavi_count > 0)
    else:
        all_ok = all_ok and check_ok("Autoclavi configurate", False, "Nessuna autoclave trovata")
    
    return all_ok

def generate_summary_report(results: Dict[str, bool]):
    """Genera un report riassuntivo dei risultati"""
    print_header("REPORT FINALE")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"📊 Risultati Validazione:")
    print(f"   • Test totali: {total_tests}")
    print(f"   • Test superati: {passed_tests} ✅")
    print(f"   • Test falliti: {failed_tests} ❌")
    print(f"   • Percentuale successo: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print(f"\n⚠️  Test falliti:")
        for test_name, result in results.items():
            if not result:
                print(f"   • {test_name}")
    
    overall_status = "✅ TUTTI I TEST SUPERATI" if failed_tests == 0 else f"❌ {failed_tests} TEST FALLITI"
    print(f"\n🎯 Stato generale: {overall_status}")
    
    return failed_tests == 0

def main():
    """Funzione principale di validazione"""
    print("🚀 AVVIO VALIDAZIONE CARBONPILOT")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Esegui tutti i test
    results = {
        "Frontend Accessibile": validate_frontend_accessibility(),
        "Endpoint Core": validate_core_endpoints(),
        "Export Database": validate_database_export(),
        "Consistenza Dati": validate_data_consistency(),
        "Flussi Critici": validate_critical_flows(),
    }
    
    # Genera report finale
    success = generate_summary_report(results)
    
    # Exit code appropriato
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 