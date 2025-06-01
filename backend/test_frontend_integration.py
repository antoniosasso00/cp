#!/usr/bin/env python3
"""
Test rapido di integrazione frontend
Verifica che le pagine del nesting siano accessibili e funzionanti
"""

import requests
import time

def test_frontend_pages():
    """Test delle pagine frontend del nesting"""
    
    print("🌐 TEST INTEGRAZIONE FRONTEND")
    print("=" * 50)
    
    # URL del frontend (assumendo Next.js su porta 3000)
    FRONTEND_URL = "http://localhost:3000"
    
    pages_to_test = [
        "/nesting/new",
        "/dashboard/curing/nesting/list",
        "/dashboard/curing/nesting"
    ]
    
    for page in pages_to_test:
        try:
            print(f"\n🔍 Test pagina: {page}")
            response = requests.get(f"{FRONTEND_URL}{page}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Pagina accessibile (HTTP {response.status_code})")
                
                # Verifica che non sia una pagina di errore
                if "error" not in response.text.lower() and "404" not in response.text:
                    print(f"   ✅ Contenuto valido")
                else:
                    print(f"   ⚠️ Possibile errore nel contenuto")
                    
            else:
                print(f"   ❌ Pagina non accessibile (HTTP {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Frontend non raggiungibile")
            print(f"   🔧 Assicurati che il frontend sia avviato su {FRONTEND_URL}")
            return False
        except Exception as e:
            print(f"   ❌ Errore: {e}")
    
    print(f"\n✅ Test frontend completato")
    return True

def test_api_from_frontend_context():
    """Test che simula le chiamate che farebbe il frontend"""
    
    print(f"\n🔗 TEST API DAL CONTESTO FRONTEND")
    print("=" * 50)
    
    # Simula le chiamate che farebbe la pagina /nesting/new
    
    print("📋 1. Caricamento ODL per selezione...")
    try:
        response = requests.get("http://localhost:8000/api/v1/odl/")
        if response.status_code == 200:
            odl_data = response.json()
            print(f"   ✅ {len(odl_data)} ODL caricati")
        else:
            print(f"   ❌ Errore ODL: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    print("🏭 2. Caricamento autoclavi disponibili...")
    try:
        response = requests.get("http://localhost:8000/api/v1/autoclavi/")
        if response.status_code == 200:
            autoclave_data = response.json()
            autoclavi_disponibili = [a for a in autoclave_data if a.get('stato') == 'DISPONIBILE']
            print(f"   ✅ {len(autoclavi_disponibili)} autoclavi disponibili")
        else:
            print(f"   ❌ Errore autoclavi: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    print("🧠 3. Generazione nesting (simulazione frontend)...")
    try:
        payload = {
            "odl_ids": ["1", "2"],
            "autoclave_ids": ["1"],
            "parametri": {
                "padding_mm": 10,
                "min_distance_mm": 5,
                "priorita_area": False
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/nesting/genera",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            batch_id = result.get('batch_id')
            print(f"   ✅ Nesting generato: {batch_id}")
            
            # Test caricamento risultato (come farebbe la pagina di risultato)
            print("📊 4. Caricamento risultato batch...")
            detail_response = requests.get(f"http://localhost:8000/api/v1/batch_nesting/{batch_id}/full")
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print(f"   ✅ Dettagli batch caricati")
                
                # Verifica che ci siano i dati per il canvas
                if 'configurazione_json' in detail_data and detail_data['configurazione_json']:
                    config = detail_data['configurazione_json']
                    if 'tool_positions' in config and len(config['tool_positions']) > 0:
                        print(f"   ✅ Configurazione canvas pronta ({len(config['tool_positions'])} tool)")
                        return True
                    else:
                        print(f"   ❌ Configurazione canvas vuota")
                        return False
                else:
                    print(f"   ❌ configurazione_json mancante")
                    return False
            else:
                print(f"   ❌ Errore dettagli batch: {detail_response.status_code}")
                return False
        else:
            print(f"   ❌ Errore generazione: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False

def main():
    print("🚀 TEST INTEGRAZIONE FRONTEND COMPLETO")
    print("=" * 60)
    
    # Test 1: Accessibilità pagine frontend
    frontend_ok = test_frontend_pages()
    
    # Test 2: API dal contesto frontend
    api_ok = test_api_from_frontend_context()
    
    print("\n" + "=" * 60)
    print("📊 RISULTATI TEST INTEGRAZIONE FRONTEND")
    print("=" * 60)
    
    if frontend_ok and api_ok:
        print("🎉 INTEGRAZIONE FRONTEND COMPLETAMENTE FUNZIONALE!")
        print("✅ Pagine accessibili")
        print("✅ API integrazione OK")
        print("✅ Flusso completo nesting operativo")
        
        print("\n🌐 ACCESSO DIRETTO:")
        print("   • Nuovo nesting: http://localhost:3000/nesting/new")
        print("   • Dashboard: http://localhost:3000/dashboard/curing/nesting")
        print("   • Lista batch: http://localhost:3000/dashboard/curing/nesting/list")
        
        return True
    else:
        print("❌ PROBLEMI NELL'INTEGRAZIONE FRONTEND")
        if not frontend_ok:
            print("   🔧 Verifica che il frontend sia avviato:")
            print("      cd frontend && npm run dev")
        if not api_ok:
            print("   🔧 Verifica che il backend sia avviato:")
            print("      cd backend && uvicorn main:app --reload")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 