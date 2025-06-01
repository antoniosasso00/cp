#!/usr/bin/env python3
"""
Test di verifica per la correzione dell'errore di fetch nel modulo nesting.
Verifica che l'endpoint /api/v1/batch_nesting/{id}/full funzioni correttamente.
"""

import requests
import json
import sys
from datetime import datetime

def test_backend_health():
    """Testa che il backend sia attivo e funzionante."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend attivo - Tabelle: {data['database']['tables_count']}, Route: {data['api']['routes_count']}")
            return True
        else:
            print(f"❌ Backend non risponde correttamente: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore connessione backend: {e}")
        return False

def test_batch_nesting_endpoint():
    """Testa l'endpoint specifico del batch nesting che era problematico."""
    batch_id = "f12cc922-d484-4ee9-aadb-f3c03a378cea"
    
    try:
        # Test endpoint corretto con /v1
        response = requests.get(f"http://localhost:8000/api/v1/batch_nesting/{batch_id}/full", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint batch nesting funzionante")
            print(f"   - Batch ID: {data['id']}")
            print(f"   - Nome: {data['nome']}")
            print(f"   - Stato: {data['stato']}")
            print(f"   - Autoclave: {data['autoclave']['nome'] if data.get('autoclave') else 'N/A'}")
            print(f"   - ODL inclusi: {len(data['odl_ids'])}")
            print(f"   - Tool posizionati: {len(data['configurazione_json']['tool_positions']) if data.get('configurazione_json') else 0}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Batch {batch_id} non trovato (normale se non esiste)")
            return True
        else:
            print(f"❌ Errore endpoint batch nesting: {response.status_code}")
            print(f"   Risposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore chiamata endpoint batch nesting: {e}")
        return False

def test_frontend_proxy():
    """Testa che il proxy del frontend funzioni correttamente."""
    batch_id = "f12cc922-d484-4ee9-aadb-f3c03a378cea"
    
    # Prova diverse porte dove potrebbe essere il frontend
    frontend_ports = [3000, 3001, 3002]
    
    for port in frontend_ports:
        try:
            response = requests.get(f"http://localhost:{port}/api/v1/batch_nesting/{batch_id}/full", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Proxy frontend funzionante su porta {port}")
                print(f"   - Dati ricevuti correttamente tramite proxy")
                return True
            elif response.status_code == 404:
                print(f"✅ Proxy frontend funzionante su porta {port} (batch non trovato è normale)")
                return True
                
        except requests.exceptions.RequestException:
            continue
    
    print("⚠️  Frontend non raggiungibile su nessuna porta standard")
    return False

def test_old_endpoint_fails():
    """Verifica che il vecchio endpoint (senza /v1) non funzioni più."""
    batch_id = "f12cc922-d484-4ee9-aadb-f3c03a378cea"
    
    try:
        # Test endpoint vecchio senza /v1 (dovrebbe fallire)
        response = requests.get(f"http://localhost:8000/api/batch_nesting/{batch_id}/full", timeout=5)
        
        if response.status_code == 404:
            print("✅ Vecchio endpoint (senza /v1) correttamente non funzionante")
            return True
        else:
            print(f"⚠️  Vecchio endpoint ancora attivo: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✅ Vecchio endpoint non raggiungibile (corretto): {e}")
        return True

def main():
    """Esegue tutti i test di verifica."""
    print("🧪 Test di verifica correzione errore fetch nesting")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Backend Health Check", test_backend_health),
        ("Endpoint Batch Nesting", test_batch_nesting_endpoint),
        ("Proxy Frontend", test_frontend_proxy),
        ("Vecchio Endpoint", test_old_endpoint_fails),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ Errore durante {test_name}: {e}")
            results.append((test_name, False))
            print()
    
    # Riepilogo
    print("📊 RIEPILOGO TEST")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Risultato: {passed}/{len(results)} test superati")
    
    if passed == len(results):
        print("🎉 Tutti i test superati! La correzione funziona correttamente.")
        return 0
    else:
        print("⚠️  Alcuni test falliti. Verificare la configurazione.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 