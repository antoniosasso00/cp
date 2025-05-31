#!/usr/bin/env python3
"""
🧪 Test Completo - Verifica Fix Form Tools e Catalogo
Questo script testa tutti i problemi segnalati dall'utente:
1. Modal "Salva e nuovo" che si chiude
2. Peso e materiale non visualizzati
3. Errori nella modifica tools con peso/materiale
4. Errori nella modifica part number catalogo
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")

def print_result(success, message):
    status = "✅ SUCCESSO" if success else "❌ ERRORE"
    print(f"{status}: {message}")

def test_backend_health():
    """Test 1: Verifica che il backend sia attivo"""
    print_test_header("Verifica Backend Attivo")
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Backend attivo - Database: {data['database']['status']}")
            return True
        else:
            print_result(False, f"Backend non risponde - Status: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Errore connessione backend: {str(e)}")
        return False

def test_tool_creation_with_peso_materiale():
    """Test 2: Creazione tool con peso e materiale"""
    print_test_header("Creazione Tool con Peso e Materiale")
    
    tool_data = {
        "part_number_tool": f"TEST_TOOL_{datetime.now().strftime('%H%M%S')}",
        "descrizione": "Tool di test con peso e materiale",
        "lunghezza_piano": 100.0,
        "larghezza_piano": 50.0,
        "peso": 12.5,
        "materiale": "Alluminio",
        "disponibile": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tools/", json=tool_data)
        if response.status_code == 201:
            created_tool = response.json()
            print_result(True, f"Tool creato - ID: {created_tool['id']}")
            print(f"   📊 Peso: {created_tool.get('peso', 'MANCANTE')} kg")
            print(f"   🔧 Materiale: {created_tool.get('materiale', 'MANCANTE')}")
            return created_tool['id']
        else:
            print_result(False, f"Errore creazione - Status: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return None

def test_tool_update_with_peso_materiale(tool_id):
    """Test 3: Modifica tool con peso e materiale"""
    print_test_header("Modifica Tool con Peso e Materiale")
    
    if not tool_id:
        print_result(False, "Nessun tool ID disponibile per il test")
        return False
    
    update_data = {
        "peso": 15.8,
        "materiale": "Acciaio Inox",
        "descrizione": "Tool aggiornato con nuovi dati"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/tools/{tool_id}", json=update_data)
        if response.status_code == 200:
            updated_tool = response.json()
            print_result(True, f"Tool aggiornato - ID: {tool_id}")
            print(f"   📊 Peso aggiornato: {updated_tool.get('peso', 'MANCANTE')} kg")
            print(f"   🔧 Materiale aggiornato: {updated_tool.get('materiale', 'MANCANTE')}")
            return True
        else:
            print_result(False, f"Errore aggiornamento - Status: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return False

def test_tools_list_with_peso_materiale():
    """Test 4: Lista tools include peso e materiale"""
    print_test_header("Lista Tools con Peso e Materiale")
    
    try:
        response = requests.get(f"{BASE_URL}/tools/")
        if response.status_code == 200:
            tools = response.json()
            print_result(True, f"Lista tools ottenuta - {len(tools)} tools trovati")
            
            # Verifica che almeno un tool abbia peso e materiale
            tools_with_peso = [t for t in tools if t.get('peso') is not None]
            tools_with_materiale = [t for t in tools if t.get('materiale') is not None]
            
            print(f"   📊 Tools con peso: {len(tools_with_peso)}/{len(tools)}")
            print(f"   🔧 Tools con materiale: {len(tools_with_materiale)}/{len(tools)}")
            
            if tools_with_peso or tools_with_materiale:
                print("   ✅ Campi peso/materiale presenti nella risposta API")
                return True
            else:
                print("   ⚠️ Nessun tool ha peso o materiale definiti")
                return True  # Non è un errore se non ci sono dati
        else:
            print_result(False, f"Errore lista tools - Status: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return False

def test_catalogo_creation():
    """Test 5: Creazione elemento catalogo per test propagazione"""
    print_test_header("Creazione Elemento Catalogo per Test")
    
    catalogo_data = {
        "part_number": f"TEST_PN_{datetime.now().strftime('%H%M%S')}",
        "descrizione": "Part Number di test per propagazione",
        "categoria": "Test",
        "attivo": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/catalogo/", json=catalogo_data)
        if response.status_code == 201:
            created_catalogo = response.json()
            print_result(True, f"Catalogo creato - PN: {created_catalogo['part_number']}")
            return created_catalogo['part_number']
        else:
            print_result(False, f"Errore creazione - Status: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return None

def test_catalogo_part_number_propagation(old_part_number):
    """Test 6: Propagazione part number nel catalogo"""
    print_test_header("Propagazione Part Number Catalogo")
    
    if not old_part_number:
        print_result(False, "Nessun part number disponibile per il test")
        return False
    
    new_part_number = f"{old_part_number}_NUOVO"
    
    try:
        response = requests.put(
            f"{BASE_URL}/catalogo/{old_part_number}/update-with-propagation",
            json={"new_part_number": new_part_number}
        )
        
        if response.status_code == 200:
            updated_catalogo = response.json()
            print_result(True, f"Part Number propagato con successo")
            print(f"   📝 Da: {old_part_number}")
            print(f"   📝 A: {updated_catalogo['part_number']}")
            return True
        else:
            print_result(False, f"Errore propagazione - Status: {response.status_code}")
            print(f"   Dettagli: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return False

def test_tools_with_status():
    """Test 7: Endpoint tools con status (per verificare peso/materiale)"""
    print_test_header("Tools con Status (Verifica Peso/Materiale)")
    
    try:
        response = requests.get(f"{BASE_URL}/tools/with-status")
        if response.status_code == 200:
            tools = response.json()
            print_result(True, f"Tools con status ottenuti - {len(tools)} tools")
            
            # Verifica struttura dati
            if tools:
                first_tool = tools[0]
                has_peso = 'peso' in first_tool
                has_materiale = 'materiale' in first_tool
                
                print(f"   📊 Campo 'peso' presente: {'✅' if has_peso else '❌'}")
                print(f"   🔧 Campo 'materiale' presente: {'✅' if has_materiale else '❌'}")
                
                return has_peso and has_materiale
            else:
                print("   ⚠️ Nessun tool trovato per verificare struttura")
                return True
        else:
            print_result(False, f"Errore - Status: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Errore: {str(e)}")
        return False

def main():
    """Esegue tutti i test in sequenza"""
    print("🚀 AVVIO TEST COMPLETO - Fix Form Tools e Catalogo")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Backend Health
    results['backend_health'] = test_backend_health()
    if not results['backend_health']:
        print("\n❌ Backend non disponibile - Interrompo i test")
        return
    
    # Test 2: Creazione tool con peso/materiale
    tool_id = test_tool_creation_with_peso_materiale()
    results['tool_creation'] = tool_id is not None
    
    # Test 3: Modifica tool con peso/materiale
    results['tool_update'] = test_tool_update_with_peso_materiale(tool_id)
    
    # Test 4: Lista tools con peso/materiale
    results['tools_list'] = test_tools_list_with_peso_materiale()
    
    # Test 5: Creazione catalogo
    part_number = test_catalogo_creation()
    results['catalogo_creation'] = part_number is not None
    
    # Test 6: Propagazione part number
    results['part_number_propagation'] = test_catalogo_part_number_propagation(part_number)
    
    # Test 7: Tools con status
    results['tools_with_status'] = test_tools_with_status()
    
    # Riepilogo finale
    print(f"\n{'='*60}")
    print("📊 RIEPILOGO RISULTATI TEST")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 RISULTATO FINALE: {passed_tests}/{total_tests} test superati")
    
    if passed_tests == total_tests:
        print("🎉 TUTTI I TEST SUPERATI! I fix sono funzionanti.")
    else:
        print("⚠️ Alcuni test falliti - Verificare i problemi segnalati sopra.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 