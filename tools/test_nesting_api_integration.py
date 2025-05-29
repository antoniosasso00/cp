#!/usr/bin/env python3
"""
Test di integrazione per le API del layout nesting.
Verifica che tutti gli endpoint backend funzionino correttamente.
"""

import sys
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any

# ✅ AGGIORNATO: URL corretto con prefisso v1
API_BASE_URL = "http://localhost:8000/api/v1"
NESTING_API_URL = f"{API_BASE_URL}/nesting"

def print_header():
    """Stampa l'header del test"""
    print("🧪 TEST INTEGRAZIONE API NESTING LAYOUT")
    print("=" * 60)
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")

def test_api_connection() -> bool:
    """Test connessione API base"""
    print("🔗 Test: Connessione API base")
    try:
        response = requests.get(f"http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Connessione API riuscita")
            return True
        else:
            print(f"❌ Connessione API fallita: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connessione API fallita: {e}")
        return False

def test_nesting_list() -> Dict[str, Any]:
    """Test endpoint lista nesting"""
    print("\n📋 Test: Endpoint lista nesting")
    try:
        response = requests.get(f"{NESTING_API_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Lista nesting recuperata: {len(data)} elementi")
            return {"success": True, "data": data}
        else:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"❌ Errore recupero lista: {response.status_code}")
            if error_detail:
                print(f"   Dettaglio: {error_detail}")
            return {"success": False, "data": []}
    except Exception as e:
        print(f"❌ Errore recupero lista: {e}")
        return {"success": False, "data": []}

def test_multi_canvas_layout() -> bool:
    """Test endpoint multi-canvas layout"""
    print("\n🖼️  Test: Endpoint multi-canvas layout")
    try:
        params = {
            "limit": 5,
            "padding_mm": 10.0,
            "borda_mm": 20.0,
            "rotazione_abilitata": True
        }
        response = requests.get(f"{NESTING_API_URL}/layout/multi", params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            nesting_count = len(data.get("nesting_list", []))
            print(f"✅ Multi-canvas layout recuperato: {nesting_count} nesting")
            return True
        else:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"❌ Errore multi-layout: {response.status_code}")
            if error_detail:
                print(f"   Dettaglio: {error_detail}")
            return False
    except Exception as e:
        print(f"❌ Errore multi-layout: {e}")
        return False

def test_single_nesting_layout(nesting_list: list) -> bool:
    """Test endpoint layout singolo nesting"""
    print("\n🎯 Test: Endpoint layout singolo nesting")
    
    if not nesting_list:
        print("⚠️  Nessun nesting disponibile per test layout singolo")
        return False
    
    try:
        nesting_id = nesting_list[0]["id"]
        params = {
            "padding_mm": 15.0,
            "borda_mm": 25.0,
            "rotazione_abilitata": True
        }
        response = requests.get(f"{NESTING_API_URL}/{nesting_id}/layout", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tool_count = len(data.get("posizioni_tool", []))
            print(f"✅ Layout singolo recuperato per nesting #{nesting_id}: {tool_count} tool")
            return True
        else:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"❌ Errore layout singolo: {response.status_code}")
            if error_detail:
                print(f"   Dettaglio: {error_detail}")
            return False
    except Exception as e:
        print(f"❌ Errore layout singolo: {e}")
        return False

def test_orientation_calculation() -> bool:
    """Test endpoint calcolo orientamento"""
    print("\n🔄 Test: Endpoint calcolo orientamento")
    try:
        payload = {
            "tool_lunghezza": 150.0,
            "tool_larghezza": 100.0,
            "autoclave_lunghezza": 800.0,
            "autoclave_larghezza": 600.0
        }
        response = requests.post(f"{NESTING_API_URL}/calculate-orientation", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            should_rotate = data.get("should_rotate", False)
            improvement = data.get("improvement_percentage", 0)
            print(f"✅ Calcolo orientamento riuscito: rotazione={should_rotate}, miglioramento={improvement}%")
            return True
        else:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"❌ Errore calcolo orientamento: {response.status_code}")
            if error_detail:
                print(f"   Dettaglio: {error_detail}")
            return False
    except Exception as e:
        print(f"❌ Errore calcolo orientamento: {e}")
        return False

def test_layout_statistics() -> bool:
    """Test endpoint statistiche layout"""
    print("\n📊 Test: Endpoint statistiche layout")
    try:
        params = {"giorni_precedenti": 30}
        response = requests.get(f"{NESTING_API_URL}/layout/statistics", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats = data.get("statistiche", {})
            print(f"✅ Statistiche layout recuperate: {len(stats)} metriche")
            return True
        else:
            error_detail = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"❌ Errore statistiche: {response.status_code}")
            if error_detail:
                print(f"   Dettaglio: {error_detail}")
            return False
    except Exception as e:
        print(f"❌ Errore statistiche: {e}")
        return False

def main():
    """Esegue tutti i test di integrazione"""
    print_header()
    
    # Contatori risultati
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Connessione API
    if test_api_connection():
        tests_passed += 1
    
    # Test 2: Lista nesting
    nesting_result = test_nesting_list()
    if nesting_result["success"]:
        tests_passed += 1
    
    # Test 3: Multi-canvas layout
    if test_multi_canvas_layout():
        tests_passed += 1
    
    # Test 4: Layout singolo (dipende dalla lista nesting)
    if test_single_nesting_layout(nesting_result["data"]):
        tests_passed += 1
    
    # Test 5: Calcolo orientamento
    if test_orientation_calculation():
        tests_passed += 1
    
    # Test 6: Statistiche layout
    if test_layout_statistics():
        tests_passed += 1
    
    # Risultati finali
    print("\n" + "=" * 60)
    print("📊 RISULTATI FINALI:")
    print(f"1. Connessione API: {'✅ PASS' if tests_passed >= 1 else '❌ FAIL'}")
    print(f"2. Lista Nesting: {'✅ PASS' if nesting_result['success'] else '❌ FAIL'}")
    print(f"3. Multi-Canvas Layout: {'✅ PASS' if tests_passed >= 3 else '❌ FAIL'}")
    print(f"4. Layout Singolo: {'✅ PASS' if tests_passed >= 4 else '❌ FAIL'}")
    print(f"5. Calcolo Orientamento: {'✅ PASS' if tests_passed >= 5 else '❌ FAIL'}")
    print(f"6. Statistiche Layout: {'✅ PASS' if tests_passed >= 6 else '❌ FAIL'}")
    
    print(f"\n🎯 Test superati: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Tutti i test sono passati! L'integrazione API è funzionante.")
    else:
        print("⚠️  Alcuni test hanno fallito - verificare la configurazione API")
        print("💡 Suggerimenti:")
        print("   - Verificare che il backend FastAPI sia in esecuzione")
        print("   - Controllare l'URL dell'API e la porta")
        print("   - Verificare che il database contenga dati di test")

if __name__ == "__main__":
    main() 