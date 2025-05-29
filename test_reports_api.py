#!/usr/bin/env python3
"""
🧪 Test API Report e Nesting
Verifica che le API per i report funzionino correttamente
"""

import requests
import json
import time
from datetime import datetime

# Configurazione API
BASE_URL = "http://localhost:8001/api/v1"
NESTING_API_URL = f"{BASE_URL}/nesting"
REPORTS_API_URL = f"{BASE_URL}/reports"

def test_nesting_list():
    """Testa il recupero della lista dei nesting"""
    print("📋 Testing nesting list...")
    
    try:
        response = requests.get(NESTING_API_URL, timeout=10)
        if response.status_code == 200:
            nesting_list = response.json()
            print(f"   ✅ Trovati {len(nesting_list)} nesting")
            return nesting_list
        else:
            print(f"   ❌ Errore API: {response.status_code}")
            return []
    except Exception as e:
        print(f"   ❌ Errore connessione: {e}")
        return []

def test_nesting_report_generation(nesting_id):
    """Testa la generazione di report per un nesting specifico"""
    print(f"📊 Testing report generation for nesting {nesting_id}...")
    
    try:
        # Genera il report
        response = requests.post(
            f"{NESTING_API_URL}/{nesting_id}/generate-report",
            params={'force_regenerate': True},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Report generato: {data.get('filename', 'N/A')}")
                print(f"      • Report ID: {data.get('report_id')}")
                print(f"      • File path: {data.get('file_path')}")
                print(f"      • Size: {data.get('file_size_bytes', 0)} bytes")
                return data
            else:
                print(f"   ⚠️ Report non generato: {data.get('message', 'N/A')}")
                return None
        else:
            print(f"   ❌ Errore generazione: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Errore generazione report: {e}")
        return None

def test_nesting_report_download(nesting_id):
    """Testa il download di un report PDF per un nesting"""
    print(f"⬇️ Testing report download for nesting {nesting_id}...")
    
    try:
        response = requests.get(
            f"{REPORTS_API_URL}/nesting/{nesting_id}/download",
            timeout=15
        )
        
        if response.status_code == 200:
            if response.headers.get('content-type') == 'application/pdf':
                content_length = len(response.content)
                print(f"   ✅ Report PDF scaricato ({content_length} bytes)")
                return True
            else:
                print(f"   ⚠️ Contenuto non PDF: {response.headers.get('content-type')}")
                return False
        else:
            print(f"   ❌ Errore download: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore download report: {e}")
        return False

def test_reports_general_api():
    """Testa le API generali dei report"""
    print("📄 Testing general reports API...")
    
    try:
        # Test lista report
        response = requests.get(REPORTS_API_URL, timeout=10)
        if response.status_code == 200:
            reports = response.json()
            print(f"   ✅ Reports disponibili: {len(reports.get('reports', []))}")
        else:
            print(f"   ❌ Errore lista report: {response.status_code}")
        
        # Test statistiche efficienza nesting
        response = requests.get(f"{REPORTS_API_URL}/nesting-efficiency", timeout=10)
        if response.status_code == 200:
            efficiency_data = response.json()
            print(f"   ✅ Statistiche efficienza:")
            print(f"      • Total nesting: {efficiency_data.get('total_nestings', 0)}")
            print(f"      • Efficienza area media: {efficiency_data.get('average_area_efficiency', 0)}%")
            print(f"      • Efficienza valvole media: {efficiency_data.get('average_valve_efficiency', 0)}%")
        else:
            print(f"   ❌ Errore statistiche efficienza: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Errore API generale: {e}")

def test_export_apis():
    """Testa le API di export (CSV, Excel, PDF) - Mock check"""
    print("📤 Testing export APIs...")
    
    export_endpoints = [
        f"{NESTING_API_URL}/reports/export.csv",
        f"{NESTING_API_URL}/reports/export.xlsx", 
        f"{NESTING_API_URL}/reports/export.pdf"
    ]
    
    for endpoint in export_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            format_name = endpoint.split('.')[-1].upper()
            
            if response.status_code == 200:
                print(f"   ✅ Export {format_name} disponibile")
            elif response.status_code == 404:
                print(f"   🔧 Export {format_name} non implementato (404)")
            else:
                print(f"   ⚠️ Export {format_name} stato: {response.status_code}")
                
        except Exception as e:
            format_name = endpoint.split('.')[-1].upper()
            print(f"   🔧 Export {format_name} non raggiungibile (da implementare)")

def main():
    """Funzione principale del test"""
    print("🚀 Test API Report e Nesting - CarbonPilot")
    print("=" * 50)
    
    # Test lista nesting
    nesting_list = test_nesting_list()
    
    if not nesting_list:
        print("⚠️ Nessun nesting trovato, non posso testare i report")
        return
    
    print(f"\n🎯 Testing con i primi 2 nesting...")
    
    # Test report generation e download per i primi 2 nesting
    test_count = min(2, len(nesting_list))
    successful_reports = 0
    
    for i in range(test_count):
        nesting = nesting_list[i]
        nesting_id = nesting['id']
        
        print(f"\n--- Test Nesting {nesting_id} ---")
        print(f"Stato: {nesting.get('stato', 'N/A')}")
        print(f"Autoclave: {nesting.get('autoclave_nome', 'N/A')}")
        
        # Genera report
        report_info = test_nesting_report_generation(nesting_id)
        
        if report_info:
            # Prova download
            if test_nesting_report_download(nesting_id):
                successful_reports += 1
            time.sleep(1)  # Pausa tra i test
    
    print(f"\n📊 Test API Generali")
    test_reports_general_api()
    
    print(f"\n📤 Test Export")
    test_export_apis()
    
    print(f"\n🏆 RISULTATI FINALI:")
    print(f"   • Report generati e scaricati: {successful_reports}/{test_count}")
    print(f"   • Nesting testati: {test_count}")
    
    if successful_reports > 0:
        print("   ✅ API Report funzionanti!")
    else:
        print("   ⚠️ Verificare implementazione API Report")

if __name__ == "__main__":
    main() 