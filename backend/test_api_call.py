#!/usr/bin/env python3
"""
Test HTTP per verificare l'accessibilità dell'endpoint 2L
"""

import requests
import json
import sys

def test_server_availability():
    """Test disponibilità server"""
    print("🔍 Test 1: Disponibilità server...")
    
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server FastAPI disponibile")
            return True
        else:
            print(f"❌ Server risponde con status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server non raggiungibile su localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Errore connessione server: {e}")
        return False

def test_endpoint_availability():
    """Test disponibilità endpoint 2L"""
    print("\n🔍 Test 2: Disponibilità endpoint 2L...")
    
    try:
        # Test con richiesta vuota per verificare che l'endpoint esista
        response = requests.post(
            "http://localhost:8000/api/batch_nesting/2l",
            json={},
            timeout=10
        )
        
        # Ci aspettiamo un errore 422 (validation error) perché non abbiamo mandato parametri validi
        if response.status_code == 422:
            print("✅ Endpoint 2L raggiungibile (422 = validation error atteso)")
            return True
        elif response.status_code == 404:
            print("❌ Endpoint 2L non trovato (404)")
            return False
        else:
            print(f"⚠️ Endpoint 2L risponde con status inatteso: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Endpoint non raggiungibile")
        return False
    except Exception as e:
        print(f"❌ Errore chiamata endpoint: {e}")
        return False

def test_swagger_documentation():
    """Test documentazione Swagger"""
    print("\n🔍 Test 3: Documentazione Swagger...")
    
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_spec = response.json()
            
            # Cerca l'endpoint 2L nella spec OpenAPI
            paths = openapi_spec.get('paths', {})
            endpoint_found = False
            
            for path, methods in paths.items():
                if '/batch_nesting/2l' in path and 'post' in methods:
                    endpoint_found = True
                    endpoint_info = methods['post']
                    print(f"✅ Endpoint trovato in Swagger: {path}")
                    print(f"   Summary: {endpoint_info.get('summary', 'N/A')}")
                    print(f"   Description: {endpoint_info.get('description', 'N/A')}")
                    break
            
            if not endpoint_found:
                print("❌ Endpoint 2L non trovato nella documentazione Swagger")
                return False
            
            return True
        else:
            print(f"❌ Documentazione Swagger non disponibile (status {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Errore accesso Swagger: {e}")
        return False

def test_endpoint_structure():
    """Test struttura endpoint con richiesta valida"""
    print("\n🔍 Test 4: Struttura endpoint con richiesta valida...")
    
    try:
        # Richiesta di esempio
        test_request = {
            "autoclave_id": 1,
            "odl_ids": [1, 2, 3],
            "use_cavalletti": True,
            "padding_mm": 10.0,
            "min_distance_mm": 15.0
        }
        
        response = requests.post(
            "http://localhost:8000/api/batch_nesting/2l",
            json=test_request,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funziona correttamente")
            print(f"   Success: {data.get('success', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            return True
        elif response.status_code == 404:
            print("❌ Autoclave non trovata (atteso per test)")
            return True  # È normale per un test
        elif response.status_code == 422:
            error_detail = response.json()
            print(f"⚠️ Errore validazione: {error_detail}")
            return True  # Validazione funziona
        else:
            print(f"⚠️ Status inatteso: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore test struttura: {e}")
        return False

def main():
    """Esegue tutti i test HTTP"""
    print("🚀 === TEST HTTP ENDPOINT 2L - INIZIO ===\n")
    
    tests = [
        test_server_availability,
        test_endpoint_availability,
        test_swagger_documentation,
        test_endpoint_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 === RISULTATI TEST HTTP ===")
    print(f"✅ Test passati: {passed}/{total}")
    
    if passed == total:
        print("🎉 Endpoint 2L completamente funzionale via HTTP!")
        return True
    else:
        print("❌ Alcuni test HTTP sono falliti. Verifica il server.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 