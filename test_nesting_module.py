#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento completo del modulo Nesting
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configurazione
API_BASE_URL = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")

def test_endpoint(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Testa un endpoint API e ritorna la risposta"""
    url = f"{API_BASE_URL}{endpoint}"
    print_info(f"Testing {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, json=data, headers=HEADERS)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=HEADERS)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        else:
            raise ValueError(f"Metodo non supportato: {method}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print_success(f"{method} {endpoint} - Status: {response.status_code}")
            return response.json()
        else:
            print_error(f"{method} {endpoint} - Status: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"{method} {endpoint} - Error: {str(e)}")
        return None

def main():
    print("\n=== TEST MODULO NESTING ===\n")
    
    # 1. Test GET /nesting/
    print("\n1. Test lista nesting:")
    nesting_list = test_endpoint("GET", "/nesting/")
    
    # 2. Test GET /odl/
    print("\n2. Test lista ODL:")
    odl_list = test_endpoint("GET", "/odl/")
    
    # 3. Test GET /autoclavi/
    print("\n3. Test lista autoclavi:")
    autoclave_list = test_endpoint("GET", "/autoclavi/")
    
    # 4. Test nesting automatico
    print("\n4. Test generazione automatica nesting:")
    auto_nesting_data = {
        "force_regenerate": True,
        "parameters": {
            "distanza_minima_tool_cm": 2.0,
            "padding_bordo_autoclave_cm": 1.5,
            "margine_sicurezza_peso_percent": 10.0,
            "priorita_minima": 1,
            "efficienza_minima_percent": 60.0
        }
    }
    auto_result = test_endpoint("POST", "/nesting/automatic", auto_nesting_data)
    
    # 5. Test preview nesting
    print("\n5. Test preview nesting:")
    preview_result = test_endpoint("GET", "/nesting/preview")
    
    # 6. Test active nesting
    print("\n6. Test nesting attivi:")
    active_result = test_endpoint("GET", "/nesting/active")
    
    # 7. Se abbiamo almeno un nesting, testa i dettagli
    if nesting_list and len(nesting_list) > 0:
        first_nesting_id = nesting_list[0].get('id')
        if first_nesting_id:
            print(f"\n7. Test dettagli nesting #{first_nesting_id}:")
            details = test_endpoint("GET", f"/nesting/{first_nesting_id}")
            
            # 8. Test layout
            print(f"\n8. Test layout nesting #{first_nesting_id}:")
            layout = test_endpoint("GET", f"/nesting/{first_nesting_id}/layout")
            
            # 9. Test tools
            print(f"\n9. Test tools nesting #{first_nesting_id}:")
            tools = test_endpoint("GET", f"/nesting/{first_nesting_id}/tools")
    
    # 10. Test parametri
    print("\n10. Test parametri nesting:")
    params = test_endpoint("GET", "/nesting/parameters")
    
    # 11. Test report API
    print("\n11. Test API reports:")
    reports_list = test_endpoint("GET", "/reports/")
    
    # Riepilogo
    print("\n=== RIEPILOGO TEST ===")
    print_info("Test completato. Verifica i risultati sopra per identificare eventuali problemi.")

if __name__ == "__main__":
    main() 