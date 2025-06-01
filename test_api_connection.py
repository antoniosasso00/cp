#!/usr/bin/env python3
"""
🔍 Test di connessione API Dashboard
===================================

Script per testare tutti gli endpoint del dashboard e identificare problemi di connessione.
"""

import requests
import json
import sys
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "health": f"{BASE_URL}/health",
    "odl_count": f"{BASE_URL}/api/v1/dashboard/odl-count",
    "autoclave_load": f"{BASE_URL}/api/v1/dashboard/autoclave-load", 
    "nesting_active": f"{BASE_URL}/api/v1/dashboard/nesting-active",
    "kpi_summary": f"{BASE_URL}/api/v1/dashboard/kpi-summary"
}

def test_endpoint(name: str, url: str) -> dict:
    """Testa un singolo endpoint e ritorna i risultati"""
    print(f"\n🔍 Testing {name}: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        result = {
            "name": name,
            "url": url,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get("content-type", ""),
            "error": None,
            "data": None
        }
        
        if response.status_code == 200:
            try:
                result["data"] = response.json()
                print(f"✅ SUCCESS - Status: {response.status_code}, Time: {result['response_time']:.3f}s")
            except json.JSONDecodeError as e:
                result["error"] = f"JSON decode error: {str(e)}"
                result["success"] = False
                print(f"❌ JSON ERROR - {result['error']}")
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ HTTP ERROR - {result['error']}")
            
    except requests.exceptions.ConnectionError:
        result = {
            "name": name,
            "url": url,
            "status_code": None,
            "success": False,
            "response_time": None,
            "content_type": None,
            "error": "Connection refused - Backend non raggiungibile",
            "data": None
        }
        print(f"❌ CONNECTION ERROR - Backend non raggiungibile")
        
    except requests.exceptions.Timeout:
        result = {
            "name": name,
            "url": url,
            "status_code": None,
            "success": False,
            "response_time": None,
            "content_type": None,
            "error": "Request timeout",
            "data": None
        }
        print(f"❌ TIMEOUT ERROR - Richiesta scaduta")
        
    except Exception as e:
        result = {
            "name": name,
            "url": url,
            "status_code": None,
            "success": False,
            "response_time": None,
            "content_type": None,
            "error": f"Unexpected error: {str(e)}",
            "data": None
        }
        print(f"❌ UNEXPECTED ERROR - {str(e)}")
    
    return result

def main():
    """Esegue tutti i test e genera un report"""
    print("🚀 CARBON PILOT - Test Connessione API Dashboard")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    results = []
    
    # Testa tutti gli endpoint
    for name, url in ENDPOINTS.items():
        result = test_endpoint(name, url)
        results.append(result)
    
    # Genera report finale
    print("\n" + "=" * 60)
    print("📊 REPORT FINALE")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Endpoint funzionanti: {successful}/{total}")
    print(f"❌ Endpoint con errori: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 TUTTI GLI ENDPOINT FUNZIONANO CORRETTAMENTE!")
        exit_code = 0
    else:
        print("\n⚠️ ALCUNI ENDPOINT HANNO PROBLEMI:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['name']}: {result['error']}")
        exit_code = 1
    
    # Salva report dettagliato
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "summary": {
            "total_endpoints": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round((successful / total) * 100, 1)
        },
        "results": results
    }
    
    with open("api_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report dettagliato salvato in: api_test_report.json")
    
    # Mostra dati di esempio se disponibili
    for result in results:
        if result["success"] and result["data"] and result["name"] != "health":
            print(f"\n📋 Dati di esempio da {result['name']}:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False)[:500] + "...")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 