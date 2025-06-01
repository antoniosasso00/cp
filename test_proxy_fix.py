#!/usr/bin/env python3
"""
Test per verificare se il fix del proxy per il nesting funziona correttamente.
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, description):
    """Testa un endpoint e restituisce il risultato"""
    print(f"\n🔍 Test: {description}")
    print(f"📍 URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESSO (200)")
            print(f"📊 Risposta: {json.dumps(data, indent=2, default=str)}")
            return True, data
        else:
            print(f"❌ ERRORE HTTP: {response.status_code}")
            print(f"📄 Contenuto: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRORE CONNESSIONE: {str(e)}")
        return False, None

def main():
    print("🔧 TEST DEL FIX DEL PROXY PER IL NESTING")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Backend diretto
    backend_success, backend_data = test_endpoint(
        "http://localhost:8000/api/v1/nesting/health",
        "Backend diretto - endpoint nesting health"
    )
    
    # Test 2: Proxy frontend
    proxy_success, proxy_data = test_endpoint(
        "http://localhost:3000/api/v1/nesting/health", 
        "Frontend proxy - endpoint nesting health"
    )
    
    # Test 3: Test dell'endpoint principale di generazione
    generate_test_success, _ = test_endpoint(
        "http://localhost:3000/api/v1/nesting/data",
        "Frontend proxy - endpoint nesting data"
    )
    
    # Risultati
    print("\n" + "=" * 50)
    print("📋 RIASSUNTO RISULTATI:")
    print(f"   Backend diretto:     {'✅ OK' if backend_success else '❌ ERRORE'}")
    print(f"   Frontend proxy:      {'✅ OK' if proxy_success else '❌ ERRORE'}")
    print(f"   Endpoint nesting:     {'✅ OK' if generate_test_success else '❌ ERRORE'}")
    
    if backend_success and proxy_success and generate_test_success:
        print("\n🎉 SUCCESSO! Il fix del proxy funziona correttamente!")
        print("   Il problema 'Not Found' dovrebbe essere risolto.")
    elif backend_success and not proxy_success:
        print("\n⚠️  Il backend funziona ma il proxy ha problemi.")
        print("   Possibili cause:")
        print("   - Frontend non ancora riavviato con nuove configurazioni")
        print("   - Problema con next.config.js")
    elif not backend_success:
        print("\n❌ Il backend non risponde.")
        print("   Verifica che il backend sia in esecuzione su porta 8000.")
    else:
        print("\n❌ Problemi rilevati. Verifica logs per dettagli.")

if __name__ == "__main__":
    main() 